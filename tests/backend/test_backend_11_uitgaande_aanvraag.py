"""
Integratietests voor story 11: Groq-modelkeuze uitbreiden.

Deze tests controleren de samenwerking tussen de promptroute, de
modelresolutie/-validatie en de daadwerkelijke Groq-aanroep (call_groq).
In tegenstelling tot tests/backend/test_backend_11.py — waar app.call_groq zelf
gemockt wordt — laten deze tests call_groq ongemoeid en mocken alleen de
netwerklaag (httpx.AsyncClient.post). Zo wordt gecontroleerd of het
geselecteerde model daadwerkelijk in de uitgaande aanvraag naar de Groq API
terechtkomt, en niet alleen dat call_groq met de juiste parameter wordt
aangeroepen — dat is een gat dat de gemockte unit-tests niet dekken.

Gebruikt de in-process ASGI-testclient (fixture `client`) in plaats van de
draaiende server, omdat httpx.AsyncClient.post binnen hetzelfde proces
gemockt moet worden. Er wordt geen echte netwerkaanvraag gedaan.

AC gedekt:
- De backend gebruikt het geselecteerde model in de daadwerkelijke JSON-body
  naar de Groq API, in plaats van altijd GROQ_MODEL
- Zonder meegestuurd model bevat de uitgaande aanvraag de GROQ_MODEL-waarde
- Elk van de vier nieuwe modellen komt terecht in de uitgaande aanvraag
- De aanvraag blijft naar dezelfde OpenAI-compatibele endpoint gaan, ongeacht het model
- Bij provider 'ollama' wordt de Groq-endpoint niet aangeroepen, model-veld heeft geen effect
- Het logbestand bevat 'model_bevestigd_door_groq' met het model uit de Groq-respons
- Bij een mismatch tussen aangevraagd en bevestigd model bevat het run-resultaat een waarschuwing
- Bij een gelijk model verschijnt er geen mismatch-waarschuwing
- Ontbreekt het 'model'-veld in de Groq-respons, dan wordt dit niet als mismatch behandeld
"""
import json
import httpx
import pytest
from unittest.mock import patch

pytestmark = pytest.mark.asyncio

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

GROQ_MODELS_NIEUW = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "moonshotai/kimi-k2-instruct",
    "qwen3-32b",
]

GROQ_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "integratie-model-test",
    "provider": "groq",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}

OLLAMA_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "integratie-model-test",
    "provider": "ollama",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}


@pytest.fixture
def groq_key(monkeypatch):
    monkeypatch.setattr("app.GROQ_API_KEY", "test-api-key")


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


_ECHTE_EXTERNE_PREFIXES = ("https://api.groq.com", "http://localhost:11434")
_ORIGINELE_ASYNC_CLIENT_POST = httpx.AsyncClient.post


def _stub_httpx_post(captured, groq_model_in_respons=None):
    """Vervangt httpx.AsyncClient.post: onderschept alleen aanvragen naar de
    echte Groq/Ollama-endpoints (legt ze vast en geeft een nepresponse terug,
    zonder een echte netwerkaanvraag). Alle andere aanvragen — met name de
    eigen ASGI-testclient-aanroep naar '/api/prompt', die ook via
    httpx.AsyncClient loopt — worden ongewijzigd doorgegeven aan de
    originele implementatie, anders wordt de aanvraag nooit door de app
    zelf afgehandeld.

    Met `groq_model_in_respons` wordt het top-level 'model'-veld gesimuleerd
    dat de echte Groq API in haar respons teruggeeft."""
    async def fake_post(self, url, **kwargs):
        url_str = str(url)
        if not url_str.startswith(_ECHTE_EXTERNE_PREFIXES):
            return await _ORIGINELE_ASYNC_CLIENT_POST(self, url, **kwargs)

        captured.append({"url": url_str, "json": kwargs.get("json"), "headers": kwargs.get("headers")})
        respons_data = {
            "response": "antwoord",
            "choices": [{"message": {"content": "antwoord"}}],
        }
        if groq_model_in_respons is not None:
            respons_data["model"] = groq_model_in_respons
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json=respons_data,
        )
    return fake_post


# ---------------------------------------------------------------------------
# Geselecteerd model komt terecht in de uitgaande Groq-aanvraag
# ---------------------------------------------------------------------------

async def test_geselecteerd_model_zit_in_uitgaande_groq_aanvraag(client, groq_key, logs_dir):
    """Het geselecteerde model staat in de JSON-body van de echte aanroep naar de Groq API."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured)):
        payload = {**GROQ_PAYLOAD, "model": "qwen3-32b"}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200, f"Onverwachte statuscode: {response.status_code}: {response.text}"
    assert len(captured) == 1, f"Verwacht 1 uitgaande aanvraag, kreeg {len(captured)}: {captured}"
    assert captured[0]["json"]["model"] == "qwen3-32b", (
        f"Verwacht model='qwen3-32b' in uitgaande aanvraag, kreeg: {captured[0]['json']}"
    )


@pytest.mark.parametrize("model", GROQ_MODELS_NIEUW)
async def test_elk_nieuw_model_komt_terecht_in_uitgaande_aanvraag(client, groq_key, logs_dir, model):
    """Elk van de vier nieuwe modellen komt terecht in de JSON-body van de echte Groq-aanroep."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured)):
        payload = {**GROQ_PAYLOAD, "model": model}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200, f"Model {model} gaf status {response.status_code}: {response.text}"
    assert captured[0]["json"]["model"] == model, (
        f"Verwacht model={model!r} in uitgaande aanvraag, kreeg: {captured[0]['json']}"
    )


async def test_geen_model_meegestuurd_gebruikt_groq_model_env_in_aanvraag(client, groq_key, logs_dir, monkeypatch):
    """Zonder meegestuurd model bevat de uitgaande aanvraag de GROQ_MODEL-waarde."""
    monkeypatch.setattr("app.GROQ_MODEL", "llama3-8b-8192")
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured)):
        response = await client.post("/api/prompt", json=GROQ_PAYLOAD)

    assert response.status_code == 200
    assert captured[0]["json"]["model"] == "llama3-8b-8192", (
        f"Verwacht fallback naar GROQ_MODEL, kreeg: {captured[0]['json']}"
    )


async def test_groq_aanvraag_blijft_naar_dezelfde_endpoint_gaan(client, groq_key, logs_dir):
    """Ongeacht het gekozen model blijft de aanvraag naar dezelfde OpenAI-compatibele Groq-endpoint gaan."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured)):
        payload = {**GROQ_PAYLOAD, "model": "moonshotai/kimi-k2-instruct"}
        await client.post("/api/prompt", json=payload)

    assert len(captured) == 1
    assert captured[0]["url"] == GROQ_ENDPOINT, (
        f"Verwacht endpoint {GROQ_ENDPOINT}, kreeg {captured[0]['url']}"
    )


# ---------------------------------------------------------------------------
# Ollama blijft onaangeroerd
# ---------------------------------------------------------------------------

async def test_ollama_roept_groq_endpoint_niet_aan_ondanks_model_veld(client, logs_dir):
    """Bij provider 'ollama' wordt de Groq-endpoint nooit aangeroepen, ook niet met een model-veld."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured)):
        payload = {**OLLAMA_PAYLOAD, "model": "openai/gpt-oss-120b"}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200
    groq_aanroepen = [c for c in captured if c["url"] == GROQ_ENDPOINT]
    assert groq_aanroepen == [], f"De Groq-endpoint werd onterecht aangeroepen: {groq_aanroepen}"


# ---------------------------------------------------------------------------
# Modelbevestiging — model uit de Groq-respons vergelijken met het aangevraagde model
# ---------------------------------------------------------------------------

async def test_bevestigd_model_wordt_gelogd(client, groq_key, logs_dir):
    """Het logbestand bevat 'model_bevestigd_door_groq' met het model uit de Groq-respons."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured, groq_model_in_respons="qwen3-32b")):
        payload = {**GROQ_PAYLOAD, "model": "qwen3-32b"}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data.get("model_bevestigd_door_groq") == "qwen3-32b", (
        f"'model_bevestigd_door_groq' ontbreekt of is onjuist: {data}"
    )


async def test_geen_mismatch_waarschuwing_bij_gelijk_model(client, groq_key, logs_dir):
    """Als aangevraagd en bevestigd model overeenkomen, bevat het run-resultaat geen mismatch-waarschuwing."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured, groq_model_in_respons="qwen3-32b")):
        payload = {**GROQ_PAYLOAD, "model": "qwen3-32b"}
        response = await client.post("/api/prompt", json=payload)

    stap = response.json()["runs"][0]
    assert "model_mismatch_warning" not in stap, (
        f"Onterechte mismatch-waarschuwing bij gelijk model: {stap}"
    )


@pytest.mark.parametrize("model", GROQ_MODELS_NIEUW)
async def test_elk_nieuw_model_wordt_bevestigd_zonder_mismatch(client, groq_key, logs_dir, model):
    """Voor elk van de vier nieuwe modellen: bevestigt Groq hetzelfde model, dan wordt dit
    correct gelogd in 'model_bevestigd_door_groq' en verschijnt er geen mismatch-waarschuwing.
    Dit borgt dat elk model individueel nog steeds correct wordt herkend door de Groq-respons,
    ook als een van de modellen ooit door Groq wordt uitgefaseerd of hernoemd."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured, groq_model_in_respons=model)):
        payload = {**GROQ_PAYLOAD, "model": model}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200, f"Model {model} gaf status {response.status_code}: {response.text}"
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data.get("model_bevestigd_door_groq") == model, (
        f"Model {model!r}: 'model_bevestigd_door_groq' ontbreekt of is onjuist: {data}"
    )

    stap = response.json()["runs"][0]
    assert "model_mismatch_warning" not in stap, (
        f"Model {model!r}: onterechte mismatch-waarschuwing: {stap}"
    )


async def test_mismatch_tussen_aangevraagd_en_bevestigd_model_geeft_waarschuwing(client, groq_key, logs_dir):
    """Als het bevestigde model afwijkt van het aangevraagde model, bevat het run-resultaat een waarschuwing."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured, groq_model_in_respons="llama3-8b-8192")):
        payload = {**GROQ_PAYLOAD, "model": "qwen3-32b"}
        response = await client.post("/api/prompt", json=payload)

    stap = response.json()["runs"][0]
    assert "model_mismatch_warning" in stap, f"Verwachte mismatch-waarschuwing ontbreekt: {stap}"
    melding = str(stap["model_mismatch_warning"])
    assert "qwen3-32b" in melding and "llama3-8b-8192" in melding, (
        f"Waarschuwing noemt niet beide modellen: {melding!r}"
    )


async def test_ontbrekend_model_veld_in_respons_geeft_geen_waarschuwing(client, groq_key, logs_dir):
    """Als de Groq-respons geen 'model'-veld bevat, wordt dit niet als mismatch behandeld."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured, groq_model_in_respons=None)):
        payload = {**GROQ_PAYLOAD, "model": "qwen3-32b"}
        response = await client.post("/api/prompt", json=payload)

    stap = response.json()["runs"][0]
    assert "model_mismatch_warning" not in stap, (
        f"Onterechte mismatch-waarschuwing zonder 'model'-veld in respons: {stap}"
    )
