"""
Backend-tests voor story 05: Groq als tweede provider.

AC gedekt:
- Bij provider 'groq' roept de backend call_groq aan, niet call_ollama
- Bij provider 'ollama' (standaard) roept de backend call_ollama aan
- GROQ_MODEL is instelbaar via omgevingsvariabele (standaard: llama3-8b-8192)
- GROQ_API_KEY ontbreekt of is leeg → HTTP 503 met passende melding
- Groq-aanvraag: bestandsnaam bevat 'groq' als provider
- Groq-aanvraag: veld 'provider' in logbestand is 'groq'
- Groq-aanvraag: veld 'model' in logbestand bevat het gebruikte Groq-model
- Bij Groq-fout wordt geen logbestand aangemaakt
- Prompt wordt identiek opgebouwd als bij Ollama — alleen de API-aanroep verschilt
- Sessie opslaan bevat veld 'provider'
- Sessie laden geeft veld 'provider' terug
"""
import importlib
import json
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio

PROMPT_GROQ = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "mijn-sessie",
    "provider": "groq",
    "temperatures": [0.8],
}

PROMPT_OLLAMA = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "mijn-sessie",
    "provider": "ollama",
    "temperatures": [0.8],
}

SESSIE_GROQ = {
    "name": "test-groq",
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
def groq_key(monkeypatch):
    monkeypatch.setattr("app.GROQ_API_KEY", "test-api-key")


# ---------------------------------------------------------------------------
# Providerselectie: juiste call-functie
# ---------------------------------------------------------------------------

async def test_groq_provider_roept_call_groq_aan(client, groq_key):
    """Bij provider='groq' wordt call_groq aangeroepen."""
    with patch("app.call_groq", new_callable=AsyncMock, return_value="Groq antwoord") as mock_groq, \
         patch("app.call_ollama", new_callable=AsyncMock, return_value="Ollama antwoord") as mock_ollama:
        await client.post("/api/prompt", json=PROMPT_GROQ)
    mock_groq.assert_called_once()
    mock_ollama.assert_not_called()


async def test_ollama_provider_roept_call_ollama_aan(client):
    """Bij provider='ollama' wordt call_ollama aangeroepen, niet call_groq."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Ollama antwoord") as mock_ollama, \
         patch("app.call_groq", new_callable=AsyncMock, return_value="Groq antwoord") as mock_groq:
        await client.post("/api/prompt", json=PROMPT_OLLAMA)
    mock_ollama.assert_called_once()
    mock_groq.assert_not_called()


async def test_standaard_provider_is_ollama(client):
    """Zonder provider-veld in de payload wordt call_ollama gebruikt."""
    payload = {k: v for k, v in PROMPT_OLLAMA.items() if k != "provider"}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Ollama antwoord") as mock_ollama, \
         patch("app.call_groq", new_callable=AsyncMock) as mock_groq:
        await client.post("/api/prompt", json=payload)
    mock_ollama.assert_called_once()
    mock_groq.assert_not_called()


# ---------------------------------------------------------------------------
# Groq model
# ---------------------------------------------------------------------------

async def test_groq_model_standaard_is_llama3(monkeypatch):
    """Als GROQ_MODEL niet is ingesteld, is de standaardwaarde 'llama3-8b-8192'."""
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    with patch("dotenv.load_dotenv"):
        import app as app_module
        importlib.reload(app_module)
    assert app_module.GROQ_MODEL == "llama3-8b-8192"


async def test_groq_model_instelbaar_via_env(monkeypatch):
    """GROQ_MODEL is instelbaar via monkeypatch op het module-attribuut."""
    monkeypatch.setattr("app.GROQ_MODEL", "custom-model-v2")
    import app as app_module
    assert app_module.GROQ_MODEL == "custom-model-v2"


# ---------------------------------------------------------------------------
# GROQ_API_KEY ontbreekt of leeg
# ---------------------------------------------------------------------------

async def test_groq_key_ontbreekt_geeft_503(client, monkeypatch):
    """Als GROQ_API_KEY leeg is en provider='groq', retourneert de backend HTTP 503."""
    monkeypatch.setattr("app.GROQ_API_KEY", "")
    response = await client.post("/api/prompt", json=PROMPT_GROQ)
    assert response.status_code == 503


async def test_groq_key_ontbreekt_foutmelding(client, monkeypatch):
    """Foutmelding bij ontbrekende GROQ_API_KEY legt duidelijk uit wat er moet worden ingesteld."""
    monkeypatch.setattr("app.GROQ_API_KEY", "")
    response = await client.post("/api/prompt", json=PROMPT_GROQ)
    assert "GROQ_API_KEY" in response.json()["detail"]


async def test_groq_key_ontbreekt_geen_logbestand(client, monkeypatch, logs_dir):
    """Bij ontbrekende GROQ_API_KEY wordt geen logbestand aangemaakt."""
    monkeypatch.setattr("app.GROQ_API_KEY", "")
    await client.post("/api/prompt", json=PROMPT_GROQ)
    assert len(list(logs_dir.iterdir())) == 0


# ---------------------------------------------------------------------------
# Logging bij Groq
# ---------------------------------------------------------------------------

async def test_groq_logbestandsnaam_bevat_groq(client, groq_key, logs_dir):
    """Bestandsnaam van het logbestand bevat 'groq' als provider."""
    with patch("app.call_groq", new_callable=AsyncMock, return_value="Groq antwoord"):
        await client.post("/api/prompt", json=PROMPT_GROQ)
    namen = [f.name for f in logs_dir.iterdir()]
    assert any("groq" in naam for naam in namen), f"'groq' ontbreekt in bestandsnaam: {namen}"


async def test_groq_logveld_provider_is_groq(client, groq_key, logs_dir):
    """Het veld 'provider' in het logbestand bevat 'groq'."""
    with patch("app.call_groq", new_callable=AsyncMock, return_value="Groq antwoord"):
        await client.post("/api/prompt", json=PROMPT_GROQ)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data["provider"] == "groq"


async def test_groq_logveld_model_bevat_groq_model(client, groq_key, logs_dir, monkeypatch):
    """Het veld 'model' in het logbestand bevat het gebruikte Groq-model."""
    monkeypatch.setattr("app.GROQ_MODEL", "llama3-8b-8192")
    with patch("app.call_groq", new_callable=AsyncMock, return_value="Groq antwoord"):
        await client.post("/api/prompt", json=PROMPT_GROQ)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data["model"] == "llama3-8b-8192"


async def test_groq_fout_geen_logbestand(client, groq_key, logs_dir):
    """Als de Groq API een fout retourneert, wordt er geen logbestand aangemaakt."""
    with patch("app.call_groq", new_callable=AsyncMock, side_effect=ConnectionError("Groq niet bereikbaar")):
        await client.post("/api/prompt", json=PROMPT_GROQ)
    assert len(list(logs_dir.iterdir())) == 0


async def test_groq_fout_geeft_fout_in_run(client, groq_key):
    """Als de Groq API niet bereikbaar is, bevat de run een fout-veld (aanvraag geeft 200)."""
    with patch("app.call_groq", new_callable=AsyncMock, side_effect=ConnectionError("Groq niet bereikbaar")):
        response = await client.post("/api/prompt", json=PROMPT_GROQ)
    assert response.status_code == 200
    assert "fout" in response.json()["runs"][0]


# ---------------------------------------------------------------------------
# Prompt identiek opgebouwd
# ---------------------------------------------------------------------------

async def test_prompt_identiek_opgebouwd_bij_groq_en_ollama(client, groq_key):
    """De samengestelde prompt is voor Groq identiek aan die voor Ollama bij dezelfde invoer."""
    vastgelegde_prompts = []

    async def vang_op(prompt, temperature):
        vastgelegde_prompts.append(prompt)
        return "antwoord"

    payload_basis = {
        "rol": "Python developer",
        "taak": "een API bouwen",
        "doel": "data te verwerken",
        "formaat": "JSON",
        "sessie": "test",
        "temperatures": [0.8],
    }

    with patch("app.call_ollama", side_effect=vang_op):
        await client.post("/api/prompt", json={**payload_basis, "provider": "ollama"})

    with patch("app.call_groq", side_effect=vang_op):
        await client.post("/api/prompt", json={**payload_basis, "provider": "groq"})

    assert len(vastgelegde_prompts) == 2
    assert vastgelegde_prompts[0] == vastgelegde_prompts[1], (
        "Prompt voor Groq wijkt af van Ollama:\n"
        f"Ollama: {vastgelegde_prompts[0]!r}\n"
        f"Groq:   {vastgelegde_prompts[1]!r}"
    )


# ---------------------------------------------------------------------------
# Sessie opslaan en laden met provider
# ---------------------------------------------------------------------------

async def test_sessie_opslaan_bevat_provider(client, tmp_path, monkeypatch):
    """Opgeslagen sessie bevat het veld 'provider'."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_GROQ)
    pad = tmp_path / "test-groq.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    assert "provider" in data


async def test_sessie_opslaan_slaat_groq_provider_op(client, tmp_path, monkeypatch):
    """Sessie opgeslagen met provider='groq' bevat provider='groq' in het bestand."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_GROQ)
    pad = tmp_path / "test-groq.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    assert data["provider"] == "groq"


async def test_sessie_laden_geeft_provider_terug(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie wordt het veld 'provider' meegeleverd."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    sessie_data = {
        "name": "test-groq",
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
    (tmp_path / "test-groq.json").write_text(
        json.dumps(sessie_data, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/test-groq")
    assert response.status_code == 200
    assert response.json()["provider"] == "groq"
