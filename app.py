import io
import json
import os
import re
import httpx
import uvicorn
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Annotated

load_dotenv()

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
SESSIONS_DIR = Path("sessions")
LOGS_DIR = Path.home() / "Documents" / "PromptSessieManager" / "logs"


_TEKST_EXTENSIES = {".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json"}
_ONDERSTEUNDE_EXTENSIES = _TEKST_EXTENSIES | {".pdf", ".docx"}


def extract_pdf_text(content: bytes) -> str:
    import fitz
    doc = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_docx_text(content: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs)


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
    runs: int = 1
    temperature_modus: str = "alle"
    temperatures: list[float] = []
    bijlage_bestandsnaam: str | None = None


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
    runs: int = 1
    temperature_modus: str = "alle"
    temperatures: list[float] = []


_OPTIONELE_LABELS = [
    ("formaat", "Formaat"),
    ("stijl", "Stijl"),
    ("scope", "Scope"),
    ("eisen", "Extra eisen"),
    ("voorbeelden", "Voorbeelden"),
]


def bouw_prompt(body: PromptRequest, bijlage_tekst: str | None = None) -> str:
    regels = [f"Als {body.rol} wil ik {body.taak} zodat {body.doel}."]
    for attribuut, label in _OPTIONELE_LABELS:
        if waarde := getattr(body, attribuut):
            regels.append(f"{label}: {waarde}")
    if bijlage_tekst:
        regels.append(f"Bijlage:\n{bijlage_tekst}")
    return "\n".join(regels)


def _schrijf_log(body: PromptRequest, prompt_tekst: str, antwoord: str, start: datetime, duur: float, model: str, run_nummer: int, temperature: float, bijlage_bestandsnaam: str | None = None, bijlage_tekst: str | None = None):
    provider = body.provider.lower()
    sessie = body.sessie.strip() or "geen-sessie"
    timestamp = start.strftime("%Y-%m-%dT%H:%M:%S")
    datum_tijd = start.strftime("%Y-%m-%d_%H-%M-%S")
    bestandsnaam = f"{datum_tijd}_{provider}_{sessie}_run{run_nummer}_t{temperature:g}.json"
    log_data = {
        "timestamp": timestamp,
        "provider": provider,
        "model": model,
        "sessie": sessie,
        "run_nummer": run_nummer,
        "temperature": temperature,
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
        "bijlage_bestandsnaam": bijlage_bestandsnaam,
        "bijlage_tekst": bijlage_tekst,
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


async def call_ollama(prompt: str, temperature: float) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
            response.raise_for_status()
            return response.json()["response"]
        except httpx.HTTPError as exc:
            raise ConnectionError("Ollama niet bereikbaar") from exc


async def call_groq(prompt: str, temperature: float) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            raise ConnectionError("Groq niet bereikbaar") from exc


async def _voer_prompt_uit(
    body: PromptRequest,
    bijlage_bestandsnaam: str | None = None,
    bijlage_tekst: str | None = None,
):
    ontbrekend = [v for v in ("rol", "taak", "doel") if not getattr(body, v).strip()]
    if ontbrekend:
        raise HTTPException(
            status_code=400,
            detail=f"Verplicht veld ontbreekt: {', '.join(ontbrekend)}",
        )

    if body.runs < 1:
        raise HTTPException(status_code=400, detail="'runs' moet minimaal 1 zijn")

    if not body.temperatures:
        raise HTTPException(status_code=400, detail="Temperature is verplicht")

    for t in body.temperatures:
        if not (0.0 <= t <= 2.0):
            raise HTTPException(status_code=400, detail="Temperature moet tussen 0 en 2 liggen")

    if body.temperature_modus == "per_run" and len(body.temperatures) != body.runs:
        raise HTTPException(
            status_code=400,
            detail=f"Vul {body.runs} temperatures in, of kies 'één voor alle runs'",
        )

    provider = body.provider.lower()
    if provider == "groq" and not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Groq API key ontbreekt — stel GROQ_API_KEY in via .env",
        )

    prompt = bouw_prompt(body, bijlage_tekst)
    resultaten = []

    for i in range(1, body.runs + 1):
        temperature = body.temperatures[i - 1] if body.temperature_modus == "per_run" else body.temperatures[0]
        start = datetime.now()

        try:
            if provider == "groq":
                result = await call_groq(prompt, temperature)
                model = GROQ_MODEL
            else:
                result = await call_ollama(prompt, temperature)
                model = OLLAMA_MODEL

            duur = (datetime.now() - start).total_seconds()
            log_pad, log_warning = _schrijf_log(body, prompt, result, start, duur, model, i, temperature, bijlage_bestandsnaam, bijlage_tekst)

            run_result: dict = {"run_nummer": i, "temperature": temperature, "response": result}
            if log_warning:
                run_result["log_warning"] = log_warning
            else:
                run_result["log_status"] = "ok"
                run_result["log_path"] = str(log_pad)
            resultaten.append(run_result)

        except ConnectionError as exc:
            resultaten.append({"run_nummer": i, "fout": str(exc)})

    return {"runs": resultaten}


@app.post("/api/prompt")
async def handle_prompt(body: PromptRequest):
    return await _voer_prompt_uit(body)


@app.post("/api/prompt/upload")
async def handle_prompt_upload(
    bijlage: Annotated[UploadFile, File()],
    rol: Annotated[str, Form()] = "",
    taak: Annotated[str, Form()] = "",
    doel: Annotated[str, Form()] = "",
    formaat: Annotated[str, Form()] = "",
    stijl: Annotated[str, Form()] = "",
    scope: Annotated[str, Form()] = "",
    eisen: Annotated[str, Form()] = "",
    voorbeelden: Annotated[str, Form()] = "",
    sessie: Annotated[str, Form()] = "",
    provider: Annotated[str, Form()] = "ollama",
    runs: Annotated[str, Form()] = "1",
    temperature_modus: Annotated[str, Form()] = "alle",
    temperatures: Annotated[str, Form()] = "[]",
):
    bijlage_bestandsnaam = bijlage.filename
    extensie = Path(bijlage_bestandsnaam).suffix.lower() if bijlage_bestandsnaam else ""

    if extensie not in _ONDERSTEUNDE_EXTENSIES:
        raise HTTPException(
            status_code=400,
            detail=f"Niet-ondersteund bestandstype: {extensie} — gebruik .txt, .md, .py, .js, .ts, .html, .css, .json, .pdf of .docx",
        )

    inhoud = await bijlage.read()

    if not inhoud:
        raise HTTPException(
            status_code=400,
            detail="Bijlage is leeg — upload een bestand met inhoud",
        )

    if extensie == ".pdf":
        try:
            bijlage_tekst = extract_pdf_text(inhoud)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Bijlage kon niet worden gelezen: {exc}")
    elif extensie == ".docx":
        try:
            bijlage_tekst = extract_docx_text(inhoud)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Bijlage kon niet worden gelezen: {exc}")
    else:
        bijlage_tekst = inhoud.decode("utf-8", errors="replace")

    try:
        runs_int = int(runs)
    except (ValueError, TypeError):
        runs_int = 1
    try:
        temps_parsed = json.loads(temperatures)
        temperatures_list = temps_parsed if isinstance(temps_parsed, list) else [float(temps_parsed)]
    except (json.JSONDecodeError, TypeError, ValueError):
        temperatures_list = []

    prompt_body = PromptRequest(
        rol=rol, taak=taak, doel=doel,
        formaat=formaat, stijl=stijl, scope=scope,
        eisen=eisen, voorbeelden=voorbeelden,
        sessie=sessie, provider=provider,
        runs=runs_int,
        temperature_modus=temperature_modus,
        temperatures=temperatures_list,
    )

    return await _voer_prompt_uit(prompt_body, bijlage_bestandsnaam, bijlage_tekst)


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
        "runs": body.runs,
        "temperature_modus": body.temperature_modus,
        "temperatures": body.temperatures,
        "bijlage_bestandsnaam": body.bijlage_bestandsnaam,
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
