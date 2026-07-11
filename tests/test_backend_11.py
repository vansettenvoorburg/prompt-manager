"""
Backend-tests voor story 11: Groq-modelkeuze uitbreiden.

Aannames over de API-vorm (niet expliciet vastgelegd in de AC, dus hier
gedocumenteerd zodat ze bij de implementatiesessie bevestigd kunnen worden):
- PromptRequest krijgt een optioneel veld `model` (string, default None).
  None/ontbrekend => fallback op GROQ_MODEL. Lege string => validatiefout.
- SessionRequest krijgt een optioneel veld `groq_model` (string, default None),
  dat 1-op-1 wordt opgeslagen in het sessiebestand.
- GET /api/settings krijgt er een veld `groq_model` bij met de huidige
  env-waarde, zodat de frontend de dropdown kan vullen/default kan zetten.
- call_groq(prompt, temperature, model) krijgt een derde parameter `model`
  in plaats van intern altijd GROQ_MODEL te gebruiken.

AC gedekt:
- GET /api/settings bevat het veld 'groq_model' met de env-waarde
- Backend gebruikt het geselecteerde model voor de Groq-aanroep
- Geen model meegestuurd => fallback op GROQ_MODEL
- Model-veld heeft geen effect bij provider 'ollama'
- Elk van de vier nieuwe modellen kan een aanvraag uitvoeren
- Lege of onbekende modelwaarde bij provider 'groq' => HTTP 400
- Bekende modelwaarden (env-default + vier nieuwe) worden geaccepteerd
- Logveld 'model' bevat het daadwerkelijk gebruikte model
- Logbestandsnaam bevat provider én modelnaam
- Ongeldige tekens (zoals '/') in modelnaam worden vervangen in de bestandsnaam
- Sessie opslaan bevat veld 'groq_model'
- Sessie laden geeft veld 'groq_model' terug
- Oude sessies zonder 'groq_model' laden nog steeds correct
"""
import json
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio

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
    "sessie": "model-test",
    "provider": "groq",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}

OLLAMA_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "model-test",
    "provider": "ollama",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}

SESSIE_GROQ_BASE = {
    "name": "model-sessie",
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "provider": "groq",
}


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    monkeypatch.setattr("app.SETTINGS_FILE", pad)
    return pad


@pytest.fixture
def sessions_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def groq_key(monkeypatch):
    monkeypatch.setattr("app.GROQ_API_KEY", "test-api-key")


async def _vang_groq_model(prompt, temperature, model):
    """side_effect voor app.call_groq die het gebruikte model vastlegt."""
    _vang_groq_model.laatste_model = model
    return "antwoord"


# ---------------------------------------------------------------------------
# GET /api/settings bevat groq_model
# ---------------------------------------------------------------------------

async def test_settings_bevat_groq_model_veld(client, settings_file, monkeypatch):
    """GET /api/settings bevat het veld 'groq_model'."""
    monkeypatch.setattr("app.GROQ_MODEL", "llama3-8b-8192")
    response = await client.get("/api/settings")
    assert response.status_code == 200
    assert "groq_model" in response.json()


async def test_settings_groq_model_volgt_env_waarde(client, settings_file, monkeypatch):
    """Het veld 'groq_model' in /api/settings weerspiegelt de huidige GROQ_MODEL-waarde."""
    monkeypatch.setattr("app.GROQ_MODEL", "custom-env-model")
    response = await client.get("/api/settings")
    assert response.json()["groq_model"] == "custom-env-model"


# ---------------------------------------------------------------------------
# API-aanroep: geselecteerd model wordt gebruikt
# ---------------------------------------------------------------------------

async def test_geselecteerd_model_wordt_gebruikt_voor_groq_aanroep(client, groq_key, logs_dir):
    """De backend gebruikt het door de gebruiker gekozen model voor de Groq-aanroep."""
    captured = {}

    async def vang_op(prompt, temperature, model):
        captured["model"] = model
        return "antwoord"

    with patch("app.call_groq", side_effect=vang_op):
        payload = {**GROQ_PAYLOAD, "model": "qwen3-32b"}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200
    assert captured.get("model") == "qwen3-32b"


async def test_geen_model_meegestuurd_valt_terug_op_groq_model(client, groq_key, logs_dir, monkeypatch):
    """Als er geen model is meegestuurd, valt de backend terug op GROQ_MODEL."""
    monkeypatch.setattr("app.GROQ_MODEL", "llama3-8b-8192")
    captured = {}

    async def vang_op(prompt, temperature, model):
        captured["model"] = model
        return "antwoord"

    with patch("app.call_groq", side_effect=vang_op):
        response = await client.post("/api/prompt", json=GROQ_PAYLOAD)

    assert response.status_code == 200
    assert captured.get("model") == "llama3-8b-8192"


async def test_model_veld_heeft_geen_effect_bij_ollama(client, logs_dir, monkeypatch):
    """Bij provider 'ollama' heeft het model-veld geen effect — OLLAMA_MODEL blijft leidend."""
    monkeypatch.setattr("app.OLLAMA_MODEL", "llama3.2")

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        payload = {**OLLAMA_PAYLOAD, "model": "openai/gpt-oss-120b"}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data["model"] == "llama3.2"


# ---------------------------------------------------------------------------
# Elk van de vier nieuwe modellen kan een aanvraag uitvoeren
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model", GROQ_MODELS_NIEUW)
async def test_elk_nieuw_model_voert_aanvraag_uit(client, groq_key, logs_dir, model):
    """Elk van de vier nieuwe modellen kan via de bestaande Groq-integratie een aanvraag uitvoeren."""
    captured = {}

    async def vang_op(prompt, temperature, model):
        captured["model"] = model
        return "antwoord"

    with patch("app.call_groq", side_effect=vang_op):
        payload = {**GROQ_PAYLOAD, "model": model}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200, f"Model {model} gaf status {response.status_code}: {response.text}"
    assert captured.get("model") == model


# ---------------------------------------------------------------------------
# Validatie
# ---------------------------------------------------------------------------

async def test_lege_modelwaarde_geeft_400(client, groq_key):
    """Een lege modelwaarde bij provider 'groq' retourneert HTTP 400."""
    payload = {**GROQ_PAYLOAD, "model": ""}
    response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 400
    assert "model" in response.json()["detail"].lower()


async def test_onbekende_modelwaarde_geeft_400(client, groq_key):
    """Een onbekende modelwaarde bij provider 'groq' retourneert HTTP 400."""
    payload = {**GROQ_PAYLOAD, "model": "onbekend-model-x"}
    response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 400
    assert "model" in response.json()["detail"].lower()


async def test_ingestelde_groq_model_env_waarde_wordt_geaccepteerd(client, groq_key, logs_dir, monkeypatch):
    """De ingestelde GROQ_MODEL-waarde zelf is altijd een geldige modelwaarde."""
    monkeypatch.setattr("app.GROQ_MODEL", "custom-env-model")
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"):
        payload = {**GROQ_PAYLOAD, "model": "custom-env-model"}
        response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 200


@pytest.mark.parametrize("model", GROQ_MODELS_NIEUW)
async def test_nieuwe_modelwaarden_worden_geaccepteerd(client, groq_key, logs_dir, model):
    """Elk van de vier nieuwe modelwaarden wordt door de validatie geaccepteerd."""
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"):
        payload = {**GROQ_PAYLOAD, "model": model}
        response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 200, f"Model {model} gaf status {response.status_code}: {response.text}"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

async def test_log_model_veld_bevat_daadwerkelijk_gebruikte_model(client, groq_key, logs_dir):
    """Het veld 'model' in het logbestand bevat het daadwerkelijk gebruikte model."""
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"):
        payload = {**GROQ_PAYLOAD, "model": "qwen3-32b"}
        await client.post("/api/prompt", json=payload)

    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data["model"] == "qwen3-32b"


async def test_logbestandsnaam_bevat_provider_en_model(client, groq_key, logs_dir):
    """De bestandsnaam van het logbestand bevat zowel 'groq' als de gebruikte modelnaam."""
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"):
        payload = {**GROQ_PAYLOAD, "model": "openai/gpt-oss-120b"}
        await client.post("/api/prompt", json=payload)

    namen = [f.name for f in logs_dir.iterdir()]
    assert any("groq" in naam and "openai-gpt-oss-120b" in naam for naam in namen), (
        f"Provider en/of model ontbreken in bestandsnaam: {namen}"
    )


async def test_ongeldige_tekens_in_modelnaam_vervangen_in_bestandsnaam(client, groq_key, logs_dir):
    """Tekens die ongeldig zijn voor bestandsnamen (zoals '/') worden vervangen door '-'."""
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"):
        payload = {**GROQ_PAYLOAD, "model": "moonshotai/kimi-k2-instruct"}
        await client.post("/api/prompt", json=payload)

    namen = [f.name for f in logs_dir.iterdir()]
    assert len(namen) == 1, f"Verwacht precies 1 logbestand, kreeg: {namen}"
    assert "/" not in namen[0], f"Bestandsnaam bevat nog een '/': {namen[0]!r}"
    assert "moonshotai-kimi-k2-instruct" in namen[0], (
        f"Gesaneerde modelnaam ontbreekt in bestandsnaam: {namen[0]!r}"
    )


# ---------------------------------------------------------------------------
# Sessie opslaan en laden
# ---------------------------------------------------------------------------

async def test_sessie_opslaan_bevat_groq_model_veld(client, sessions_dir):
    """Het opgeslagen sessiebestand bevat het veld 'groq_model' met de gekozen waarde."""
    payload = {**SESSIE_GROQ_BASE, "groq_model": "qwen3-32b"}
    await client.post("/api/sessions", json=payload)

    data = json.loads((sessions_dir / "model-sessie.json").read_text(encoding="utf-8"))
    assert data.get("groq_model") == "qwen3-32b"


async def test_sessie_laden_geeft_groq_model_terug(client, sessions_dir):
    """GET /api/sessions/{name} retourneert het opgeslagen 'groq_model'."""
    sessie_data = {
        "name": "model-sessie",
        "provider": "groq",
        "groq_model": "openai/gpt-oss-20b",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "formaat": "",
        "stijl": "",
        "scope": "",
        "eisen": "",
        "voorbeelden": "",
    }
    (sessions_dir / "model-sessie.json").write_text(
        json.dumps(sessie_data, ensure_ascii=False), encoding="utf-8"
    )

    response = await client.get("/api/sessions/model-sessie")
    assert response.status_code == 200
    assert response.json()["groq_model"] == "openai/gpt-oss-20b"


async def test_oude_sessie_zonder_groq_model_laadt_nog_steeds(client, sessions_dir):
    """Een sessie opgeslagen vóór deze wijziging (zonder 'groq_model') laadt nog steeds correct."""
    oude_sessie_data = {
        "name": "oude-sessie",
        "provider": "groq",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "formaat": "",
        "stijl": "",
        "scope": "",
        "eisen": "",
        "voorbeelden": "",
    }
    (sessions_dir / "oude-sessie.json").write_text(
        json.dumps(oude_sessie_data, ensure_ascii=False), encoding="utf-8"
    )

    response = await client.get("/api/sessions/oude-sessie")
    assert response.status_code == 200
    assert response.json()["rol"] == "tester"
