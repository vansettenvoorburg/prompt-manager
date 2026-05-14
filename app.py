import json
import os
import re
import httpx
import uvicorn
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
SESSIONS_DIR = Path("sessions")
LOGS_DIR = Path.home() / "Documents" / "PromptSessieManager" / "logs"


class SessionRequest(BaseModel):
    name: str
    rol: str = ""
    taak: str = ""
    doel: str = ""
    formaat: str = ""
    stijl: str = ""
    scope: str = ""
    eisen: str = ""
    voorbeelden: str = ""
    force: bool = False


class PromptRequest(BaseModel):
    rol: str
    taak: str
    doel: str
    formaat: str = ""
    stijl: str = ""
    scope: str = ""
    eisen: str = ""
    voorbeelden: str = ""
    sessie: str = ""


_OPTIONELE_LABELS = [
    ("formaat", "Formaat"),
    ("stijl", "Stijl"),
    ("scope", "Scope"),
    ("eisen", "Extra eisen"),
    ("voorbeelden", "Voorbeelden"),
]


def bouw_prompt(body: PromptRequest) -> str:
    regels = [f"Als {body.rol} wil ik {body.taak} zodat {body.doel}."]
    for attribuut, label in _OPTIONELE_LABELS:
        if waarde := getattr(body, attribuut):
            regels.append(f"{label}: {waarde}")
    return "\n".join(regels)


def _schrijf_log(body: PromptRequest, prompt_tekst: str, antwoord: str, start: datetime, duur: float):
    sessie = body.sessie.strip() or "geen-sessie"
    timestamp = start.strftime("%Y-%m-%dT%H:%M:%S")
    datum_tijd = start.strftime("%Y-%m-%d_%H-%M-%S")
    bestandsnaam = f"{datum_tijd}_ollama_{sessie}.json"
    log_data = {
        "timestamp": timestamp,
        "provider": "ollama",
        "model": OLLAMA_MODEL,
        "sessie": sessie,
        "prompt": {
            "rol": body.rol,
            "taak": body.taak,
            "doel": body.doel,
            "formaat": body.formaat,
            "stijl": body.stijl,
            "scope": body.scope,
            "eisen": body.eisen,
            "voorbeelden": body.voorbeelden,
        },
        "request": prompt_tekst,
        "response": antwoord,
        "duur_seconden": round(duur, 3),
    }
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return f"Logmap aanmaken mislukt: {exc}"
    try:
        (LOGS_DIR / bestandsnaam).write_text(
            json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        return f"Logbestand schrijven mislukt: {exc}"
    return None


async def call_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json()["response"]
        except httpx.HTTPError as exc:
            raise ConnectionError("Ollama niet bereikbaar") from exc


@app.post("/api/prompt")
async def handle_prompt(body: PromptRequest):
    ontbrekend = [v for v in ("rol", "taak", "doel") if not getattr(body, v).strip()]
    if ontbrekend:
        raise HTTPException(
            status_code=400,
            detail=f"Verplicht veld ontbreekt: {', '.join(ontbrekend)}",
        )
    prompt = bouw_prompt(body)
    start = datetime.now()
    try:
        result = await call_ollama(prompt)
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    duur = (datetime.now() - start).total_seconds()
    log_warning = _schrijf_log(body, prompt, result, start, duur)
    response: dict = {"response": result}
    if log_warning:
        response["log_warning"] = log_warning
    else:
        response["log_status"] = "ok"
    return response


def _valideer_sessienaam(name: str) -> None:
    if not name.strip():
        raise HTTPException(status_code=400, detail="Veld 'name' mag niet leeg zijn")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
        raise HTTPException(status_code=400, detail="Veld 'name' mag alleen letters, cijfers, - en _ bevatten")


@app.post("/api/sessions")
async def save_session(body: SessionRequest):
    _valideer_sessienaam(body.name)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{body.name}.json"
    if path.exists() and not body.force:
        raise HTTPException(status_code=409, detail="Sessie bestaat al")
    data = {
        "name": body.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": "ollama",
        "model": OLLAMA_MODEL,
        "rol": body.rol,
        "taak": body.taak,
        "doel": body.doel,
        "formaat": body.formaat,
        "stijl": body.stijl,
        "scope": body.scope,
        "eisen": body.eisen,
        "voorbeelden": body.voorbeelden,
    }
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "ok"}


@app.get("/api/sessions")
async def list_sessions():
    if not SESSIONS_DIR.exists():
        return {"sessions": []}
    return {"sessions": [p.stem for p in SESSIONS_DIR.glob("*.json")]}


@app.get("/api/sessions/{name}")
async def get_session(name: str):
    _valideer_sessienaam(name)
    path = SESSIONS_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sessie niet gevonden")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return data


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
