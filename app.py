import json
import os
import re
import httpx
import uvicorn
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
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
    provider: str = "ollama"
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
    provider: str = "ollama"


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


def _schrijf_log(body: PromptRequest, prompt_tekst: str, antwoord: str, start: datetime, duur: float, provider: str, model: str):
    sessie = body.sessie.strip() or "geen-sessie"
    timestamp = start.strftime("%Y-%m-%dT%H:%M:%S")
    datum_tijd = start.strftime("%Y-%m-%d_%H-%M-%S")
    bestandsnaam = f"{datum_tijd}_{provider}_{sessie}.json"
    log_data = {
        "timestamp": timestamp,
        "provider": provider,
        "model": model,
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
        return None, f"Logmap aanmaken mislukt: {exc}"
    pad = LOGS_DIR / bestandsnaam
    try:
        pad.write_text(
            json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        return None, f"Logbestand schrijven mislukt: {exc}"
    return pad, None


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


async def call_groq(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            raise ConnectionError("Groq niet bereikbaar") from exc


@app.post("/api/prompt")
async def handle_prompt(body: PromptRequest):
    ontbrekend = [v for v in ("rol", "taak", "doel") if not getattr(body, v).strip()]
    if ontbrekend:
        raise HTTPException(
            status_code=400,
            detail=f"Verplicht veld ontbreekt: {', '.join(ontbrekend)}",
        )
    provider = body.provider.lower()
    if provider == "groq" and not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Groq API key ontbreekt — stel GROQ_API_KEY in via .env",
        )
    prompt = bouw_prompt(body)
    start = datetime.now()
    try:
        if provider == "groq":
            result = await call_groq(prompt)
            model = GROQ_MODEL
        else:
            result = await call_ollama(prompt)
            model = OLLAMA_MODEL
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    duur = (datetime.now() - start).total_seconds()
    log_pad, log_warning = _schrijf_log(body, prompt, result, start, duur, provider, model)
    response: dict = {"response": result}
    if log_warning:
        response["log_warning"] = log_warning
    else:
        response["log_status"] = "ok"
        response["log_path"] = str(log_pad)
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
    model = GROQ_MODEL if body.provider == "groq" else OLLAMA_MODEL
    data = {
        "name": body.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": body.provider,
        "model": model,
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
