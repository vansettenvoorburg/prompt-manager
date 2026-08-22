"""
Backend-tests voor story 04: logging.

AC gedekt:
- Na voltooide aanvraag wordt automatisch een logbestand aangemaakt in LOGS_DIR
- Één logbestand per aanvraag
- logs-map wordt automatisch aangemaakt als die nog niet bestaat
- Bestandsnaam: [datum]_[tijd]_[provider]_[sessienaam].json (bijv. 2026-05-10_14-32-01_ollama_sessie-tests.json)
- Datum: JJJJ-MM-DD, tijd: UU-MM-SS
- Zonder sessie in payload → 'geen-sessie' als sessienaam
- Loginhoud: verplichte velden timestamp, provider, model, sessie, prompt, request, response, duur_seconden
- prompt bevat de acht promptvelden als subobject
- request bevat de samengestelde prompt als string
- response bevat de ruwe modeloutput
- timestamp formaat: JJJJ-MM-DDTHH:MM:SS
- duur_seconden is een decimaal getal >= 0
- Schrijffout bij log → aanvraag slaagt toch (200), response bevat log_warning
- logs-map aanmaken mislukt → aanvraag slaagt toch (200), response bevat log_warning
"""
import json
import re
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio

PROMPT = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "formaat": "JSON",
    "stijl": "technisch",
    "scope": "backend only",
    "eisen": "",
    "voorbeelden": "",
    "sessie": "mijn-sessie",
    "temperatures": [0.8],
}

PROMPT_ZONDER_SESSIE = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "formaat": "",
    "stijl": "",
    "scope": "",
    "eisen": "",
    "voorbeelden": "",
    "temperatures": [0.8],
}


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Automatisch opslaan
# ---------------------------------------------------------------------------

async def test_logbestand_aangemaakt_na_prompt(client, logs_dir):
    """Na een voltooide aanvraag bestaat er een logbestand in LOGS_DIR."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    assert len(list(logs_dir.iterdir())) == 1


async def test_een_logbestand_per_aanvraag(client, logs_dir):
    """Twee aanvragen produceren twee afzonderlijke logbestanden."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json={**PROMPT, "sessie": "sessie-a"})
        await client.post("/api/prompt", json={**PROMPT, "sessie": "sessie-b"})
    assert len(list(logs_dir.iterdir())) == 2


# ---------------------------------------------------------------------------
# Locatie
# ---------------------------------------------------------------------------

async def test_logs_map_wordt_automatisch_aangemaakt(client, tmp_path, monkeypatch):
    """Backend maakt de logs-map automatisch aan als die nog niet bestaat."""
    nieuw = tmp_path / "logs-nieuw"
    assert not nieuw.exists()
    monkeypatch.setattr("app.LOGS_DIR", nieuw)
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    assert nieuw.exists()


# ---------------------------------------------------------------------------
# Bestandsnaam
# ---------------------------------------------------------------------------

async def test_bestandsnaam_formaat(client, logs_dir):
    """Bestandsnaam volgt het formaat [datum]_[tijd]_[provider]_[sessienaam].json."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    namen = [f.name for f in logs_dir.iterdir()]
    patroon = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[a-z]+_.+\.json$")
    assert any(patroon.match(naam) for naam in namen), f"Geen geldige bestandsnaam in: {namen}"


async def test_bestandsnaam_bevat_provider(client, logs_dir):
    """De bestandsnaam bevat de providernaam (ollama)."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    namen = [f.name for f in logs_dir.iterdir()]
    assert any("ollama" in naam for naam in namen), f"Provider ontbreekt in bestandsnaam: {namen}"


async def test_bestandsnaam_bevat_sessienaam(client, logs_dir):
    """De bestandsnaam bevat de sessienaam."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    namen = [f.name for f in logs_dir.iterdir()]
    assert any("mijn-sessie" in naam for naam in namen), f"Sessienaam ontbreekt in bestandsnaam: {namen}"


async def test_bestandsnaam_zonder_sessie_gebruikt_geen_sessie(client, logs_dir):
    """Zonder sessie in de payload wordt 'geen-sessie' als sessienaam in de bestandsnaam gebruikt."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT_ZONDER_SESSIE)
    namen = [f.name for f in logs_dir.iterdir()]
    assert any("geen-sessie" in naam for naam in namen), f"'geen-sessie' ontbreekt in bestandsnaam: {namen}"


# ---------------------------------------------------------------------------
# Inhoud logbestand
# ---------------------------------------------------------------------------

async def test_loginhoud_bevat_verplichte_velden(client, logs_dir):
    """Logbestand is geldig JSON met alle verplichte velden."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Model output"):
        await client.post("/api/prompt", json=PROMPT)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    for veld in ("timestamp", "provider", "model", "sessie", "prompt", "request", "response", "duur_seconden"):
        assert veld in data, f"Verplicht veld '{veld}' ontbreekt in logbestand"


async def test_loginhoud_prompt_heeft_acht_velden(client, logs_dir):
    """Het prompt-subobject bevat de acht promptvelden."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    for veld in ("rol", "taak", "doel", "formaat", "stijl", "scope", "eisen", "voorbeelden"):
        assert veld in data["prompt"], f"Promptveld '{veld}' ontbreekt in log.prompt"


async def test_loginhoud_response_is_modeloutput(client, logs_dir):
    """Het veld response bevat de ruwe output van het model."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Exacte model output"):
        await client.post("/api/prompt", json=PROMPT)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data["response"] == "Exacte model output"


async def test_loginhoud_request_is_samengestelde_prompt(client, logs_dir):
    """Het veld request bevat de samengestelde prompt als niet-lege string."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert isinstance(data["request"], str)
    assert len(data["request"]) > 0


async def test_loginhoud_timestamp_formaat(client, logs_dir):
    """timestamp heeft het formaat JJJJ-MM-DDTHH:MM:SS."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    patroon = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
    assert patroon.match(data["timestamp"]), f"Ongeldig timestamp-formaat: {data['timestamp']}"


async def test_loginhoud_duur_seconden_is_decimaal(client, logs_dir):
    """duur_seconden is een decimaal getal >= 0."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert isinstance(data["duur_seconden"], (int, float))
    assert data["duur_seconden"] >= 0


async def test_loginhoud_sessie_klopt(client, logs_dir):
    """Het veld sessie bevat de naam van de actieve sessie uit de payload."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data["sessie"] == "mijn-sessie"


async def test_loginhoud_sessie_is_geen_sessie_zonder_sessie(client, logs_dir):
    """Zonder sessie in de payload bevat het veld sessie 'geen-sessie'."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        await client.post("/api/prompt", json=PROMPT_ZONDER_SESSIE)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert data["sessie"] == "geen-sessie"


# ---------------------------------------------------------------------------
# Foutafhandeling
# ---------------------------------------------------------------------------

async def test_schrijffout_voltooit_aanvraag_toch(client, tmp_path, monkeypatch):
    """Als aanmaken van het logbestand mislukt, wordt de aanvraag toch voltooid (200)."""
    blokkeer = tmp_path / "blokkeer"
    blokkeer.write_text("dit is een bestand, geen map")
    monkeypatch.setattr("app.LOGS_DIR", blokkeer)
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        response = await client.post("/api/prompt", json=PROMPT)
    assert response.status_code == 200
    assert response.json()["runs"][0]["response"] == "Antwoord"


async def test_schrijffout_retourneert_log_warning(client, tmp_path, monkeypatch):
    """Als logging mislukt, bevat de response een log_warning."""
    blokkeer = tmp_path / "blokkeer"
    blokkeer.write_text("dit is een bestand, geen map")
    monkeypatch.setattr("app.LOGS_DIR", blokkeer)
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        response = await client.post("/api/prompt", json=PROMPT)
    assert "log_warning" in response.json()["runs"][0], "log_warning ontbreekt in response bij logfout"


async def test_logs_map_aanmaken_mislukt_voltooit_aanvraag(client, tmp_path, monkeypatch):
    """Als de logs-map niet aangemaakt kan worden, wordt de aanvraag toch uitgevoerd (200)."""
    geblokkeerd = tmp_path / "geblokkeerd"
    geblokkeerd.write_text("dit is een bestand")
    monkeypatch.setattr("app.LOGS_DIR", geblokkeerd / "logs")
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        response = await client.post("/api/prompt", json=PROMPT)
    assert response.status_code == 200


async def test_logs_map_aanmaken_mislukt_retourneert_log_warning(client, tmp_path, monkeypatch):
    """Als de logs-map niet aangemaakt kan worden, bevat de response een log_warning."""
    geblokkeerd = tmp_path / "geblokkeerd"
    geblokkeerd.write_text("dit is een bestand")
    monkeypatch.setattr("app.LOGS_DIR", geblokkeerd / "logs")
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        response = await client.post("/api/prompt", json=PROMPT)
    assert "log_warning" in response.json()["runs"][0], "log_warning ontbreekt in response bij aanmakingsfout"
