import asyncio
import contextvars
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
from pydantic import BaseModel, Field, ValidationError
from typing import Annotated

load_dotenv()

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
GROQ_MODELS_BESCHIKBAAR = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "moonshotai/kimi-k2-instruct",
    "qwen3-32b",
]
SESSIONS_DIR = Path("sessions")
LOGS_DIR = Path.home() / "Documents" / "PromptSessieManager" / "logs"
SETTINGS_FILE = Path("settings.json")

_GROQ_RPM_DEFAULT = 30
_GOOGLE_RPM_DEFAULT = 15
_BACKOFF_SECONDEN = [5, 10, 20]
_MAX_RETRIES = 3

_TEKST_EXTENSIES = {".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json"}
_ONDERSTEUNDE_EXTENSIES = _TEKST_EXTENSIES | {".pdf", ".docx"}

_laatst_bevestigd_groq_model: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "laatst_bevestigd_groq_model", default=None
)


def _saneer_voor_bestandsnaam(waarde: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "-", waarde)


def extract_pdf_text(content: bytes) -> str:
    import fitz
    doc = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_docx_text(content: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs)


def _laad_rpm(provider: str) -> int:
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    if provider == "groq":
        return int(data.get("groq_rpm", _GROQ_RPM_DEFAULT))
    if provider == "google":
        return int(data.get("google_rpm", _GOOGLE_RPM_DEFAULT))
    return 0


class RateLimitError(Exception):
    def __init__(self, retries: int):
        self.retries = retries
        super().__init__(f"API-limiet bereikt na {retries} pogingen — probeer later opnieuw")


class SettingsModel(BaseModel):
    groq_rpm: int = Field(ge=0, default=_GROQ_RPM_DEFAULT)
    google_rpm: int = Field(ge=0, default=_GOOGLE_RPM_DEFAULT)


class ReviewerConfig(BaseModel):
    rol: str
    omschrijving: str
    runs: int = 1
    temperatures: list[float] = []


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
    reviewers: list[ReviewerConfig] = []
    review_modus: str = "iteratief"
    groq_model: str | None = None


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
    reviewers: list[ReviewerConfig] = []
    review_modus: str = "iteratief"
    model: str | None = None


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


def bouw_reviewer_prompt(
    reviewer_rol: str,
    reviewer_omschrijving: str,
    body: PromptRequest,
    vorige_output: str,
    review_modus: str,
    bijlage_tekst: str | None = None,
) -> str:
    header_regels = [
        f"Je bent {reviewer_rol}.",
        f"Reviewfocus: {reviewer_omschrijving}",
    ]
    if review_modus == "iteratief":
        header_regels.append(
            "TAAK: Herschrijf de volledige tekst hieronder zodat deze verbeterd is op basis van je reviewfocus.\n"
            "REGELS:\n"
            "- Geef ALLEEN de verbeterde en complete versie terug — niets anders.\n"
            "- Begin direct met de inhoud, zonder inleiding of afsluiting.\n"
            "- Voeg geen commentaar, feedback, uitleg of wijzigingsmarkering toe.\n"
            "- Laat ongewijzigde delen intact in de output."
        )

    context_regels = []
    for attribuut, label in _OPTIONELE_LABELS:
        if waarde := getattr(body, attribuut):
            context_regels.append(f"{label}: {waarde}")
    if bijlage_tekst:
        context_regels.append(f"Bijlage:\n{bijlage_tekst}")

    delen = ["\n".join(header_regels)]
    if context_regels:
        delen.append("Originele eisen:\n" + "\n".join(context_regels))
    delen.append(f"Te verbeteren tekst:\n{vorige_output}")
    if review_modus == "iteratief":
        delen.append("Verbeterde tekst:")
    return "\n\n".join(delen)


def _schrijf_log(
    body: PromptRequest,
    prompt_tekst: str,
    antwoord: str,
    start: datetime,
    duur: float,
    model: str,
    run_nummer: int,
    temperature: float,
    bijlage_bestandsnaam: str | None = None,
    bijlage_tekst: str | None = None,
    rate_limit_retries: int | None = None,
    retry_after_seconden: float | None = None,
    model_bevestigd: str | None = None,
):
    provider = body.provider.lower()
    sessie = body.sessie.strip() or "geen-sessie"
    timestamp = start.strftime("%Y-%m-%dT%H:%M:%S")
    datum_tijd = start.strftime("%Y-%m-%d_%H-%M-%S")
    model_gesaneerd = _saneer_voor_bestandsnaam(model)
    bestandsnaam = f"{datum_tijd}_{provider}_{model_gesaneerd}_{sessie}_run{run_nummer}_t{temperature:g}.json"
    log_data = {
        "timestamp": timestamp,
        "provider": provider,
        "model": model,
        "model_bevestigd_door_groq": model_bevestigd,
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
    if rate_limit_retries is not None:
        log_data["rate_limit_retries"] = rate_limit_retries
    if retry_after_seconden is not None:
        log_data["retry_after_seconden"] = retry_after_seconden
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


def _schrijf_reviewer_log(
    body: PromptRequest,
    reviewer_nr: int,
    reviewer_rol: str,
    reviewer_omschrijving: str,
    run_nummer: int,
    temperature: float,
    prompt_tekst: str,
    antwoord: str,
    start: datetime,
    duur: float,
    model: str,
    rate_limit_retries: int | None = None,
    retry_after_seconden: float | None = None,
):
    provider = body.provider.lower()
    sessie = body.sessie.strip() or "geen-sessie"
    timestamp = start.strftime("%Y-%m-%dT%H:%M:%S")
    datum_tijd = start.strftime("%Y-%m-%d_%H-%M-%S-%f")
    model_gesaneerd = _saneer_voor_bestandsnaam(model)
    bestandsnaam = f"{datum_tijd}_{provider}_{model_gesaneerd}_{sessie}_reviewer{reviewer_nr}_run{run_nummer}_t{temperature:g}.json"
    log_data = {
        "timestamp": timestamp,
        "provider": provider,
        "model": model,
        "sessie": sessie,
        "reviewer_nr": reviewer_nr,
        "reviewer_rol": reviewer_rol,
        "reviewer_omschrijving": reviewer_omschrijving,
        "run_nummer": run_nummer,
        "temperature": temperature,
        "request": prompt_tekst,
        "response": antwoord,
        "duur_seconden": round(duur, 3),
    }
    if rate_limit_retries is not None:
        log_data["rate_limit_retries"] = rate_limit_retries
    if retry_after_seconden is not None:
        log_data["retry_after_seconden"] = retry_after_seconden
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


async def call_groq(prompt: str, temperature: float, model: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            _laatst_bevestigd_groq_model.set(data.get("model"))
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError:
            raise
        except httpx.HTTPError as exc:
            raise ConnectionError("Groq niet bereikbaar") from exc


async def _roep_groq_aan_met_retry(
    prompt: str, temperature: float, model: str
) -> tuple[str, int, float | None]:
    retries = 0
    retry_after_seconden: float | None = None

    while True:
        try:
            _laatst_bevestigd_groq_model.set(None)
            result = await call_groq(prompt, temperature, model)
            return result, retries, retry_after_seconden
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429:
                raise ConnectionError("Groq niet bereikbaar") from exc
            if retries >= _MAX_RETRIES:
                raise RateLimitError(_MAX_RETRIES) from exc
            retries += 1
            header = exc.response.headers.get("retry-after")
            if header is not None:
                wacht = float(header)
                retry_after_seconden = wacht
            else:
                wacht = _BACKOFF_SECONDEN[retries - 1]
            await asyncio.sleep(wacht)


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

    groq_model_gebruikt = GROQ_MODEL
    if provider == "groq" and body.model is not None:
        geldige_modellen = {GROQ_MODEL, *GROQ_MODELS_BESCHIKBAAR}
        if body.model not in geldige_modellen:
            raise HTTPException(
                status_code=400,
                detail=f"Onbekend of leeg model: '{body.model}'",
            )
        groq_model_gebruikt = body.model

    rpm = _laad_rpm(provider)
    delay = (60.0 / rpm) if rpm > 0 else 0.0

    prompt = bouw_prompt(body, bijlage_tekst)
    resultaten = []
    is_eerste_request = True

    for i in range(1, body.runs + 1):
        temperature = body.temperatures[i - 1] if body.temperature_modus == "per_run" else body.temperatures[0]

        if not is_eerste_request and delay > 0:
            await asyncio.sleep(delay)
        is_eerste_request = False

        start = datetime.now()

        try:
            model_bevestigd = None
            if provider == "groq":
                result, retries, retry_after_sec = await _roep_groq_aan_met_retry(
                    prompt, temperature, groq_model_gebruikt
                )
                model = groq_model_gebruikt
                model_bevestigd = _laatst_bevestigd_groq_model.get()
            else:
                result = await call_ollama(prompt, temperature)
                retries, retry_after_sec = 0, None
                model = OLLAMA_MODEL

            duur = (datetime.now() - start).total_seconds()
            log_pad, log_warning = _schrijf_log(
                body, prompt, result, start, duur, model, i, temperature,
                bijlage_bestandsnaam, bijlage_tekst,
                rate_limit_retries=retries if retries > 0 else None,
                retry_after_seconden=retry_after_sec,
                model_bevestigd=model_bevestigd,
            )

            run_result: dict = {"run_nummer": i, "temperature": temperature, "response": result}
            if retries > 0:
                run_result["rate_limit_retries"] = retries
            if model_bevestigd is not None and model_bevestigd != model:
                run_result["model_mismatch_warning"] = (
                    f"Aangevraagd model '{model}' wijkt af van door Groq bevestigd model '{model_bevestigd}'"
                )
            if log_warning:
                run_result["log_warning"] = log_warning
            else:
                run_result["log_status"] = "ok"
                run_result["log_path"] = str(log_pad)
            resultaten.append(run_result)

        except RateLimitError as exc:
            resultaten.append({
                "run_nummer": i,
                "fout": str(exc),
                "rate_limit_retries": exc.retries,
            })
        except ConnectionError as exc:
            resultaten.append({"run_nummer": i, "fout": str(exc)})

    if not body.reviewers:
        return {"runs": resultaten}

    reviewer_stappen = []
    eindoutput = ""

    for hoofdrun in resultaten:
        if "response" not in hoofdrun:
            continue
        hoofdrun_nummer = hoofdrun["run_nummer"]
        vorige_output = hoofdrun["response"]

        for reviewer_nr, reviewer in enumerate(body.reviewers, start=1):
            for run_nummer in range(1, reviewer.runs + 1):
                if reviewer.temperatures:
                    temperature = reviewer.temperatures[run_nummer - 1] if run_nummer <= len(reviewer.temperatures) else reviewer.temperatures[0]
                else:
                    temperature = 0.7
                reviewer_prompt = bouw_reviewer_prompt(
                    reviewer.rol, reviewer.omschrijving, body, vorige_output,
                    body.review_modus, bijlage_tekst,
                )

                if not is_eerste_request and delay > 0:
                    await asyncio.sleep(delay)
                is_eerste_request = False

                start = datetime.now()
                try:
                    if provider == "groq":
                        result, retries, retry_after_sec = await _roep_groq_aan_met_retry(
                            reviewer_prompt, temperature, groq_model_gebruikt
                        )
                        model = groq_model_gebruikt
                    else:
                        result = await call_ollama(reviewer_prompt, temperature)
                        retries, retry_after_sec = 0, None
                        model = OLLAMA_MODEL

                    duur = (datetime.now() - start).total_seconds()
                    log_pad, log_warning = _schrijf_reviewer_log(
                        body, reviewer_nr, reviewer.rol, reviewer.omschrijving, run_nummer, temperature,
                        reviewer_prompt, result, start, duur, model,
                        rate_limit_retries=retries if retries > 0 else None,
                        retry_after_seconden=retry_after_sec,
                    )

                    stap: dict = {
                        "hoofdrun_nummer": hoofdrun_nummer,
                        "reviewer_nr": reviewer_nr,
                        "reviewer_rol": reviewer.rol,
                        "run_nummer": run_nummer,
                        "temperature": temperature,
                        "response": result,
                    }
                    if retries > 0:
                        stap["rate_limit_retries"] = retries
                    if log_warning:
                        stap["log_warning"] = log_warning
                    else:
                        stap["log_status"] = "ok"
                        stap["log_path"] = str(log_pad)
                    reviewer_stappen.append(stap)
                    vorige_output = result

                except RateLimitError as exc:
                    reviewer_stappen.append({
                        "hoofdrun_nummer": hoofdrun_nummer,
                        "reviewer_nr": reviewer_nr,
                        "reviewer_rol": reviewer.rol,
                        "run_nummer": run_nummer,
                        "fout": str(exc),
                        "rate_limit_retries": exc.retries,
                    })
                except ConnectionError as exc:
                    reviewer_stappen.append({
                        "hoofdrun_nummer": hoofdrun_nummer,
                        "reviewer_nr": reviewer_nr,
                        "reviewer_rol": reviewer.rol,
                        "run_nummer": run_nummer,
                        "fout": str(exc),
                    })

        eindoutput = vorige_output

    return {"runs": resultaten, "reviewer_stappen": reviewer_stappen, "eindoutput": eindoutput}


@app.get("/api/settings")
async def get_settings():
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    return {
        "groq_rpm": int(data.get("groq_rpm", _GROQ_RPM_DEFAULT)),
        "google_rpm": int(data.get("google_rpm", _GOOGLE_RPM_DEFAULT)),
        "groq_model": GROQ_MODEL,
    }


@app.put("/api/settings")
async def put_settings(body: SettingsModel):
    data = body.model_dump()
    try:
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "ok"}


@app.post("/api/prompt")
async def handle_prompt(request: Request):
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form_data = await request.form()
        bijlage = form_data.get("bijlage")
        bijlage_bestandsnaam = None
        bijlage_tekst = None

        if bijlage is not None and hasattr(bijlage, "filename"):
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
            runs_int = int(form_data.get("runs", "1"))
        except (ValueError, TypeError):
            runs_int = 1
        temperatures_str = form_data.get("temperatures", "[]")
        try:
            temps_parsed = json.loads(temperatures_str)
            temperatures_list = temps_parsed if isinstance(temps_parsed, list) else [float(temps_parsed)]
        except (json.JSONDecodeError, TypeError, ValueError):
            temperatures_list = []

        reviewers_str = form_data.get("reviewers", "[]")
        try:
            reviewers_data = json.loads(reviewers_str)
            reviewers_list = [ReviewerConfig(**r) for r in reviewers_data] if isinstance(reviewers_data, list) else []
        except (json.JSONDecodeError, TypeError, ValueError):
            reviewers_list = []

        body = PromptRequest(
            rol=form_data.get("rol", ""),
            taak=form_data.get("taak", ""),
            doel=form_data.get("doel", ""),
            formaat=form_data.get("formaat", ""),
            stijl=form_data.get("stijl", ""),
            scope=form_data.get("scope", ""),
            eisen=form_data.get("eisen", ""),
            voorbeelden=form_data.get("voorbeelden", ""),
            sessie=form_data.get("sessie", ""),
            provider=form_data.get("provider", "ollama"),
            runs=runs_int,
            temperature_modus=form_data.get("temperature_modus", "alle"),
            temperatures=temperatures_list,
            reviewers=reviewers_list,
            review_modus=form_data.get("review_modus", "iteratief"),
            model=form_data.get("model"),
        )
        return await _voer_prompt_uit(body, bijlage_bestandsnaam, bijlage_tekst)

    body_data = await request.json()
    try:
        body = PromptRequest(**body_data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
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
    reviewers: Annotated[str, Form()] = "[]",
    review_modus: Annotated[str, Form()] = "iteratief",
    model: Annotated[str | None, Form()] = None,
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

    try:
        reviewers_data = json.loads(reviewers)
        reviewers_list = [ReviewerConfig(**r) for r in reviewers_data] if isinstance(reviewers_data, list) else []
    except (json.JSONDecodeError, TypeError, ValueError):
        reviewers_list = []

    prompt_body = PromptRequest(
        rol=rol, taak=taak, doel=doel,
        formaat=formaat, stijl=stijl, scope=scope,
        eisen=eisen, voorbeelden=voorbeelden,
        sessie=sessie, provider=provider,
        runs=runs_int,
        temperature_modus=temperature_modus,
        temperatures=temperatures_list,
        reviewers=reviewers_list,
        review_modus=review_modus,
        model=model,
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
        "reviewers": [r.model_dump() for r in body.reviewers],
        "review_modus": body.review_modus,
        "groq_model": body.groq_model,
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
