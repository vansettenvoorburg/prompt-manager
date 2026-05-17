"""
Backend-tests voor story 06: Aantal runs en temperature per run.

AC gedekt:
- Prompt wordt precies `runs` keer verstuurd naar de API
- Modus 'alle': elke run gebruikt dezelfde temperature
- Modus 'per_run': elke run gebruikt de overeenkomende temperature
- Response bevat alle run-resultaten op volgorde met run_nummer en temperature
- Validatie: runs < 1 → 400
- Validatie: temperature buiten 0.0–2.0 → 400
- Validatie: modus 'per_run' met mismatch temperatures/runs → 400
- Elke run wordt als apart logbestand opgeslagen
- Logbestandsnaam bevat run-nummer en temperature
- Logbestand bevat velden 'run_nummer' (int) en 'temperature' (float)
- Bij 1 run wordt suffix _run1_t{temperature} altijd toegevoegd
- Mislukte run: geen logbestand, foutmelding in response, uitvoering gaat door
- Sessie opslaan bevat velden 'runs', 'temperature_modus' en 'temperatures'
- Sessie laden geeft deze velden terug
- Bestaande sessies zonder deze velden worden geladen zonder fout
"""
import json
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio

BASE_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "mijn-sessie",
    "provider": "ollama",
}

SESSIE_MET_RUNS = {
    "name": "test-runs",
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "provider": "ollama",
    "runs": 3,
    "temperature_modus": "per_run",
    "temperatures": [0.3, 0.7, 1.0],
}


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Uitvoering: aantal runs
# ---------------------------------------------------------------------------

async def test_drie_runs_roept_api_drie_keer_aan(client, logs_dir):
    """Bij runs=3 wordt de API precies 3 keer aangeroepen."""
    payload = {**BASE_PAYLOAD, "runs": 3, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord") as mock:
        await client.post("/api/prompt", json=payload)
    assert mock.call_count == 3


async def test_een_run_roept_api_een_keer_aan(client, logs_dir):
    """Bij runs=1 (standaard) wordt de API precies 1 keer aangeroepen."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord") as mock:
        await client.post("/api/prompt", json=payload)
    assert mock.call_count == 1


# ---------------------------------------------------------------------------
# Uitvoering: temperature doorgegeven aan API
# ---------------------------------------------------------------------------

async def test_modus_alle_geeft_zelfde_temperature_aan_elke_run(client, logs_dir):
    """In modus 'alle' ontvangt elke run-aanroep dezelfde temperature."""
    payload = {**BASE_PAYLOAD, "runs": 3, "temperature_modus": "alle", "temperatures": [0.5]}
    ontvangen = []

    async def registreer(prompt, temperature):
        ontvangen.append(temperature)
        return "antwoord"

    with patch("app.call_ollama", side_effect=registreer):
        await client.post("/api/prompt", json=payload)

    assert ontvangen == [0.5, 0.5, 0.5]


async def test_modus_per_run_geeft_juiste_temperature_per_run(client, logs_dir):
    """In modus 'per_run' ontvangt elke run-aanroep de bijbehorende temperature."""
    payload = {**BASE_PAYLOAD, "runs": 3, "temperature_modus": "per_run", "temperatures": [0.3, 0.7, 1.0]}
    ontvangen = []

    async def registreer(prompt, temperature):
        ontvangen.append(temperature)
        return "antwoord"

    with patch("app.call_ollama", side_effect=registreer):
        await client.post("/api/prompt", json=payload)

    assert ontvangen == [0.3, 0.7, 1.0]


# ---------------------------------------------------------------------------
# Uitvoering: response-formaat
# ---------------------------------------------------------------------------

async def test_response_bevat_runs_lijst(client, logs_dir):
    """De response bevat een 'runs'-lijst met een resultaat per run."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, side_effect=["antwoord 1", "antwoord 2"]):
        response = await client.post("/api/prompt", json=payload)
    data = response.json()
    assert "runs" in data
    assert len(data["runs"]) == 2


async def test_response_runs_bevat_antwoorden_op_volgorde(client, logs_dir):
    """De 'runs'-lijst bevat de antwoorden op volgorde van uitvoering."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, side_effect=["eerste antwoord", "tweede antwoord"]):
        response = await client.post("/api/prompt", json=payload)
    data = response.json()
    assert data["runs"][0]["response"] == "eerste antwoord"
    assert data["runs"][1]["response"] == "tweede antwoord"


async def test_response_runs_bevatten_run_nummer(client, logs_dir):
    """Elk run-resultaat in de response bevat het juiste 'run_nummer'."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=payload)
    data = response.json()
    assert data["runs"][0]["run_nummer"] == 1
    assert data["runs"][1]["run_nummer"] == 2


async def test_response_runs_bevatten_gebruikte_temperature(client, logs_dir):
    """Elk run-resultaat in de response bevat de gebruikte 'temperature'."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "per_run", "temperatures": [0.3, 0.9]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=payload)
    data = response.json()
    assert data["runs"][0]["temperature"] == pytest.approx(0.3)
    assert data["runs"][1]["temperature"] == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# Validatie
# ---------------------------------------------------------------------------

async def test_runs_nul_geeft_400(client):
    """Bij runs=0 retourneert de backend HTTP 400."""
    payload = {**BASE_PAYLOAD, "runs": 0, "temperature_modus": "alle", "temperatures": [0.7]}
    response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 400


async def test_runs_negatief_geeft_400(client):
    """Bij een negatief getal voor runs retourneert de backend HTTP 400."""
    payload = {**BASE_PAYLOAD, "runs": -1, "temperature_modus": "alle", "temperatures": [0.7]}
    response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 400


async def test_temperature_boven_2_geeft_400(client):
    """Bij een temperature boven 2.0 retourneert de backend HTTP 400."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [2.1]}
    response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 400


async def test_temperature_onder_0_geeft_400(client):
    """Bij een temperature onder 0.0 retourneert de backend HTTP 400."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [-0.1]}
    response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 400


async def test_temperature_exact_2_punt_0_is_geldig(client, logs_dir):
    """Een temperature van precies 2.0 is geldig en geeft HTTP 200."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [2.0]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 200


async def test_temperature_exact_0_punt_0_is_geldig(client, logs_dir):
    """Een temperature van precies 0.0 is geldig en geeft HTTP 200."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [0.0]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 200


async def test_per_run_mismatch_geeft_400(client):
    """In modus 'per_run' met 3 runs maar 2 temperatures retourneert de backend HTTP 400."""
    payload = {**BASE_PAYLOAD, "runs": 3, "temperature_modus": "per_run", "temperatures": [0.3, 0.7]}
    response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 400


async def test_per_run_mismatch_foutmelding_vermeldt_verwacht_aantal(client):
    """De foutmelding bij een per_run-mismatch vermeldt het verwachte aantal temperatures."""
    payload = {**BASE_PAYLOAD, "runs": 3, "temperature_modus": "per_run", "temperatures": [0.3, 0.7]}
    response = await client.post("/api/prompt", json=payload)
    detail = response.json()["detail"]
    assert "3" in detail


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

async def test_drie_runs_maakt_drie_logbestanden(client, logs_dir):
    """Bij 3 runs worden er precies 3 afzonderlijke logbestanden aangemaakt."""
    payload = {**BASE_PAYLOAD, "runs": 3, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=payload)
    assert len(list(logs_dir.iterdir())) == 3


async def test_logbestandsnaam_bevat_run_nummers(client, logs_dir):
    """De logbestandsnamen bevatten het run-nummer (run1, run2)."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=payload)
    namen = [f.name for f in logs_dir.iterdir()]
    assert any("run1" in naam for naam in namen), f"'run1' ontbreekt in namen: {namen}"
    assert any("run2" in naam for naam in namen), f"'run2' ontbreekt in namen: {namen}"


async def test_logbestandsnaam_bevat_temperature(client, logs_dir):
    """De logbestandsnaam bevat de gebruikte temperature (bijv. t0.7)."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=payload)
    namen = [f.name for f in logs_dir.iterdir()]
    assert any("t0.7" in naam for naam in namen), f"'t0.7' ontbreekt in namen: {namen}"


async def test_een_run_heeft_altijd_run_suffix(client, logs_dir):
    """Bij 1 run bevat de bestandsnaam altijd _run1_t{temperature}."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [0.8]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=payload)
    namen = [f.name for f in logs_dir.iterdir()]
    assert any("run1" in naam for naam in namen), f"'run1' ontbreekt bij 1 run: {namen}"


async def test_logbestand_bevat_run_nummer_veld(client, logs_dir):
    """Het logbestand bevat het veld 'run_nummer' als integer."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=payload)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert "run_nummer" in data
    assert isinstance(data["run_nummer"], int)
    assert data["run_nummer"] == 1


async def test_logbestand_bevat_temperature_veld(client, logs_dir):
    """Het logbestand bevat het veld 'temperature' als float."""
    payload = {**BASE_PAYLOAD, "runs": 1, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=payload)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert "temperature" in data
    assert isinstance(data["temperature"], float)
    assert data["temperature"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Foutafhandeling per run
# ---------------------------------------------------------------------------

async def test_mislukte_run_maakt_geen_logbestand(client, logs_dir):
    """Als een run mislukt, wordt er geen logbestand voor die run aangemaakt."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=[ConnectionError("Ollama niet bereikbaar"), "antwoord run 2"]):
        await client.post("/api/prompt", json=payload)
    assert len(list(logs_dir.iterdir())) == 1


async def test_uitvoering_gaat_door_na_mislukte_run(client, logs_dir):
    """Als run 1 mislukt, wordt run 2 toch uitgevoerd."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=[ConnectionError("Ollama niet bereikbaar"), "antwoord run 2"]):
        response = await client.post("/api/prompt", json=payload)
    data = response.json()
    assert len(data["runs"]) == 2
    assert data["runs"][1]["response"] == "antwoord run 2"


async def test_mislukte_run_bevat_foutmelding_in_response(client, logs_dir):
    """Als een run mislukt, bevat het run-resultaat in de response een foutindicatie."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=[ConnectionError("Ollama niet bereikbaar"), "antwoord run 2"]):
        response = await client.post("/api/prompt", json=payload)
    data = response.json()
    run1 = data["runs"][0]
    assert "fout" in run1 or "error" in run1, f"Geen foutindicatie in mislukte run: {run1}"


async def test_geslaagde_run_na_mislukte_run_heeft_log(client, logs_dir):
    """De geslaagde run na een mislukte run wordt wél gelogd."""
    payload = {**BASE_PAYLOAD, "runs": 2, "temperature_modus": "alle", "temperatures": [0.7]}
    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=[ConnectionError("Ollama niet bereikbaar"), "antwoord run 2"]):
        await client.post("/api/prompt", json=payload)
    bestanden = list(logs_dir.iterdir())
    assert len(bestanden) == 1
    data = json.loads(bestanden[0].read_text(encoding="utf-8"))
    assert data["run_nummer"] == 2


# ---------------------------------------------------------------------------
# Sessie opslaan en laden
# ---------------------------------------------------------------------------

async def test_sessie_opslaan_bevat_runs(client, tmp_path, monkeypatch):
    """Opgeslagen sessie bevat het veld 'runs'."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_MET_RUNS)
    data = json.loads((tmp_path / "test-runs.json").read_text(encoding="utf-8"))
    assert "runs" in data
    assert data["runs"] == 3


async def test_sessie_opslaan_bevat_temperature_modus(client, tmp_path, monkeypatch):
    """Opgeslagen sessie bevat het veld 'temperature_modus'."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_MET_RUNS)
    data = json.loads((tmp_path / "test-runs.json").read_text(encoding="utf-8"))
    assert "temperature_modus" in data
    assert data["temperature_modus"] == "per_run"


async def test_sessie_opslaan_bevat_temperatures(client, tmp_path, monkeypatch):
    """Opgeslagen sessie bevat het veld 'temperatures' als array van floats."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_MET_RUNS)
    data = json.loads((tmp_path / "test-runs.json").read_text(encoding="utf-8"))
    assert "temperatures" in data
    assert data["temperatures"] == [0.3, 0.7, 1.0]


async def test_sessie_laden_geeft_runs_terug(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie wordt het veld 'runs' meegeleverd."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "test-runs.json").write_text(
        json.dumps(SESSIE_MET_RUNS, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/test-runs")
    assert response.status_code == 200
    assert response.json()["runs"] == 3


async def test_sessie_laden_geeft_temperature_modus_terug(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie wordt het veld 'temperature_modus' meegeleverd."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "test-runs.json").write_text(
        json.dumps(SESSIE_MET_RUNS, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/test-runs")
    assert response.json()["temperature_modus"] == "per_run"


async def test_sessie_laden_geeft_temperatures_terug(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie wordt het veld 'temperatures' meegeleverd."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "test-runs.json").write_text(
        json.dumps(SESSIE_MET_RUNS, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/test-runs")
    assert response.json()["temperatures"] == [0.3, 0.7, 1.0]


async def test_bestaande_sessie_zonder_runs_velden_laadt_zonder_fout(client, tmp_path, monkeypatch):
    """Bestaande sessiebestanden zonder runs/temperature-velden worden geladen zonder fout."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    oud = {"name": "oud-sessie", "provider": "ollama", "rol": "tester", "taak": "testen", "doel": "kwaliteit"}
    (tmp_path / "oud-sessie.json").write_text(json.dumps(oud, ensure_ascii=False), encoding="utf-8")
    response = await client.get("/api/sessions/oud-sessie")
    assert response.status_code == 200
