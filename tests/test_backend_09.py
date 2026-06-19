"""
Backend-tests voor story 09: Rate limiting — API-quota's respecteren.

AC gedekt:
- GET /api/settings geeft standaardwaarden terug (Groq=30, Google=15) als settings.json ontbreekt
- GET /api/settings geeft opgeslagen waarden terug als settings.json bestaat
- PUT /api/settings slaat instellingen op in settings.json
- PUT /api/settings met negatieve RPM geeft 422
- RPM=0 is toegestaan (rate limiting uitgeschakeld)
- Na PUT geeft GET de nieuwe waarden terug
- Bij 429 met Retry-After header: wacht de opgegeven tijd en herstart
- Bij 429 zonder Retry-After header: exponential backoff (5s)
- Na maximaal 3 pogingen: stap bevat 'fout'-veld met 'pogingen' in de melding
- Na 3 mislukte pogingen bevat de stap ook 'rate_limit_retries' = 3
- Succesvolle retry: stap bevat 'rate_limit_retries' >= 1
- Geen 'rate_limit_retries' in resultaat als er geen retry nodig was
- Logbestand bevat 'rate_limit_retries' na succesvolle retry
- Logbestand bevat 'retry_after_seconden' als Retry-After header aanwezig was
- Vóór het eerste request wordt geen delay-sleep uitgevoerd
- Bij 2 runs wordt sleep 1 keer aangeroepen, met duur 60/RPM seconden
- Bij Ollama wordt geen delay-sleep uitgevoerd
- Als RPM=0 wordt geen delay-sleep uitgevoerd
"""
import asyncio
import json
import httpx
import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio

GROQ_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "rate-test",
    "provider": "groq",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}

GROQ_PAYLOAD_2_RUNS = {
    **GROQ_PAYLOAD,
    "runs": 2,
    "temperatures": [0.7, 0.7],
    "temperature_modus": "per_run",
}


def _maak_429_error(retry_after=None):
    """Maakt een httpx.HTTPStatusError voor een 429-response."""
    headers = {"retry-after": str(retry_after)} if retry_after is not None else {}
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(429, headers=headers, request=request)
    return httpx.HTTPStatusError("Rate limited", request=request, response=response)


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    monkeypatch.setattr("app.SETTINGS_FILE", pad)
    return pad


# ---------------------------------------------------------------------------
# Instellingen ophalen
# ---------------------------------------------------------------------------

async def test_get_settings_geeft_standaardwaarden_als_settings_ontbreekt(client, settings_file):
    """GET /api/settings geeft standaardwaarden als settings.json niet bestaat."""
    response = await client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["groq_rpm"] == 30
    assert data["google_rpm"] == 15


async def test_get_settings_geeft_opgeslagen_waarden_terug(client, settings_file):
    """GET /api/settings geeft de opgeslagen waarden terug als settings.json bestaat."""
    settings_file.write_text(json.dumps({"groq_rpm": 20, "google_rpm": 10}), encoding="utf-8")
    response = await client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["groq_rpm"] == 20
    assert data["google_rpm"] == 10


# ---------------------------------------------------------------------------
# Instellingen opslaan
# ---------------------------------------------------------------------------

async def test_put_settings_slaat_waarden_op_in_settings_json(client, settings_file):
    """PUT /api/settings schrijft de nieuwe waarden naar settings.json."""
    response = await client.put("/api/settings", json={"groq_rpm": 20, "google_rpm": 10})
    assert response.status_code == 200
    opgeslagen = json.loads(settings_file.read_text(encoding="utf-8"))
    assert opgeslagen["groq_rpm"] == 20
    assert opgeslagen["google_rpm"] == 10


async def test_put_settings_met_negatieve_rpm_geeft_422(client, settings_file):
    """PUT /api/settings met negatieve RPM geeft 422."""
    response = await client.put("/api/settings", json={"groq_rpm": -1, "google_rpm": 15})
    assert response.status_code == 422, (
        f"Verwacht 422 voor negatieve RPM, kreeg {response.status_code}"
    )


async def test_put_settings_rpm_nul_is_toegestaan(client, settings_file):
    """PUT /api/settings met RPM=0 is geldig (rate limiting uitgeschakeld)."""
    response = await client.put("/api/settings", json={"groq_rpm": 0, "google_rpm": 0})
    assert response.status_code == 200


async def test_get_settings_na_put_geeft_nieuwe_waarden_terug(client, settings_file):
    """Na PUT geeft GET de nieuwe waarden terug."""
    await client.put("/api/settings", json={"groq_rpm": 25, "google_rpm": 12})
    response = await client.get("/api/settings")
    data = response.json()
    assert data["groq_rpm"] == 25
    assert data["google_rpm"] == 12


# ---------------------------------------------------------------------------
# Retry na 429 — succesvolle herstart
# ---------------------------------------------------------------------------

async def test_429_met_retry_after_header_wacht_opgegeven_tijd(
    client, logs_dir, settings_file, monkeypatch
):
    """Bij 429 met Retry-After header wacht de app de opgegeven tijd."""
    slaaptijden = []

    async def fake_sleep(t):
        slaaptijden.append(t)

    aanroep = [0]

    async def call_met_429(*args, **kwargs):
        aanroep[0] += 1
        if aanroep[0] == 1:
            raise _maak_429_error(retry_after=3)
        return "antwoord"

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", side_effect=call_met_429), \
         patch("app.GROQ_API_KEY", "test-key"):
        response = await client.post("/api/prompt", json=GROQ_PAYLOAD)

    assert response.status_code == 200
    assert 3.0 in slaaptijden, (
        f"Verwacht sleep(3.0) voor Retry-After=3, maar slaaptijden waren: {slaaptijden}"
    )


async def test_429_zonder_retry_after_gebruikt_backoff(
    client, logs_dir, settings_file, monkeypatch
):
    """Bij 429 zonder Retry-After header gebruikt de app exponential backoff (eerste stap: 5s)."""
    slaaptijden = []

    async def fake_sleep(t):
        slaaptijden.append(t)

    aanroep = [0]

    async def call_met_429(*args, **kwargs):
        aanroep[0] += 1
        if aanroep[0] == 1:
            raise _maak_429_error()
        return "antwoord"

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", side_effect=call_met_429), \
         patch("app.GROQ_API_KEY", "test-key"):
        response = await client.post("/api/prompt", json=GROQ_PAYLOAD)

    assert response.status_code == 200
    backoff_tijden = [t for t in slaaptijden if t >= 5]
    assert len(backoff_tijden) >= 1, (
        f"Verwacht ten minste één backoff sleep (≥5s), maar slaaptijden waren: {slaaptijden}"
    )


async def test_succesvolle_retry_geeft_rate_limit_retries_terug(
    client, logs_dir, settings_file, monkeypatch
):
    """Na een succesvolle retry bevat het resultaat 'rate_limit_retries' >= 1."""
    async def fake_sleep(t):
        pass

    aanroep = [0]

    async def call_met_429(*args, **kwargs):
        aanroep[0] += 1
        if aanroep[0] == 1:
            raise _maak_429_error(retry_after=0)
        return "antwoord"

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", side_effect=call_met_429), \
         patch("app.GROQ_API_KEY", "test-key"):
        response = await client.post("/api/prompt", json=GROQ_PAYLOAD)

    data = response.json()
    assert data["runs"][0].get("rate_limit_retries", 0) >= 1, (
        f"'rate_limit_retries' ontbreekt of is 0 na retry: {data['runs'][0]}"
    )


async def test_geen_rate_limit_retries_als_geen_retry_nodig(client, logs_dir, settings_file):
    """Zonder 429 bevat het resultaat geen 'rate_limit_retries' veld."""
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"), \
         patch("app.GROQ_API_KEY", "test-key"):
        response = await client.post("/api/prompt", json=GROQ_PAYLOAD)

    data = response.json()
    assert "rate_limit_retries" not in data["runs"][0], (
        f"'rate_limit_retries' staat onterecht in resultaat: {data['runs'][0]}"
    )


# ---------------------------------------------------------------------------
# Retry na 429 — maximale pogingen bereikt
# ---------------------------------------------------------------------------

async def test_na_drie_mislukte_pogingen_geeft_fout_terug(
    client, logs_dir, settings_file, monkeypatch
):
    """Na 3 mislukte 429-pogingen bevat de stap een 'fout'-veld."""
    async def fake_sleep(t):
        pass

    async def altijd_429(*args, **kwargs):
        raise _maak_429_error(retry_after=0)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", side_effect=altijd_429), \
         patch("app.GROQ_API_KEY", "test-key"):
        response = await client.post("/api/prompt", json=GROQ_PAYLOAD)

    assert response.status_code == 200
    stap = response.json()["runs"][0]
    assert "fout" in stap, f"'fout'-veld ontbreekt na max retries: {stap}"
    assert "pogingen" in stap["fout"], (
        f"Foutmelding noemt geen pogingen: {stap['fout']!r}"
    )


async def test_fout_na_max_retries_bevat_rate_limit_retries(
    client, logs_dir, settings_file, monkeypatch
):
    """Na 3 mislukte pogingen bevat de stap ook 'rate_limit_retries' = 3."""
    async def fake_sleep(t):
        pass

    async def altijd_429(*args, **kwargs):
        raise _maak_429_error(retry_after=0)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", side_effect=altijd_429), \
         patch("app.GROQ_API_KEY", "test-key"):
        response = await client.post("/api/prompt", json=GROQ_PAYLOAD)

    stap = response.json()["runs"][0]
    assert stap.get("rate_limit_retries") == 3, (
        f"Verwacht rate_limit_retries=3, maar stap bevat: {stap}"
    )


# ---------------------------------------------------------------------------
# Retry logging
# ---------------------------------------------------------------------------

async def test_log_bevat_rate_limit_retries_na_succesvolle_retry(
    client, logs_dir, settings_file, monkeypatch
):
    """Het logbestand bevat 'rate_limit_retries' als het request na retry slaagde."""
    async def fake_sleep(t):
        pass

    aanroep = [0]

    async def call_met_429(*args, **kwargs):
        aanroep[0] += 1
        if aanroep[0] == 1:
            raise _maak_429_error(retry_after=0)
        return "antwoord"

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", side_effect=call_met_429), \
         patch("app.GROQ_API_KEY", "test-key"):
        await client.post("/api/prompt", json=GROQ_PAYLOAD)

    logbestanden = list(logs_dir.iterdir())
    assert len(logbestanden) == 1
    log_data = json.loads(logbestanden[0].read_text(encoding="utf-8"))
    assert "rate_limit_retries" in log_data, (
        f"'rate_limit_retries' ontbreekt in logbestand: {list(log_data.keys())}"
    )
    assert log_data["rate_limit_retries"] >= 1


async def test_log_bevat_retry_after_seconden_als_header_aanwezig(
    client, logs_dir, settings_file, monkeypatch
):
    """Het logbestand bevat 'retry_after_seconden' als de Retry-After header aanwezig was."""
    async def fake_sleep(t):
        pass

    aanroep = [0]

    async def call_met_429(*args, **kwargs):
        aanroep[0] += 1
        if aanroep[0] == 1:
            raise _maak_429_error(retry_after=5)
        return "antwoord"

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", side_effect=call_met_429), \
         patch("app.GROQ_API_KEY", "test-key"):
        await client.post("/api/prompt", json=GROQ_PAYLOAD)

    logbestanden = list(logs_dir.iterdir())
    log_data = json.loads(logbestanden[0].read_text(encoding="utf-8"))
    assert "retry_after_seconden" in log_data, (
        f"'retry_after_seconden' ontbreekt in logbestand: {list(log_data.keys())}"
    )
    assert log_data["retry_after_seconden"] == 5.0


# ---------------------------------------------------------------------------
# Vertraging tussen requests op basis van RPM
# ---------------------------------------------------------------------------

async def test_geen_delay_sleep_voor_eerste_request(client, logs_dir, settings_file, monkeypatch):
    """Vóór het eerste request wordt geen delay-sleep uitgevoerd."""
    slaaptijden = []

    async def fake_sleep(t):
        slaaptijden.append(t)

    settings_file.write_text(json.dumps({"groq_rpm": 30, "google_rpm": 15}), encoding="utf-8")
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"), \
         patch("app.GROQ_API_KEY", "test-key"):
        await client.post("/api/prompt", json=GROQ_PAYLOAD)

    # Met 1 run is er geen "tussen"-request, dus geen delay
    delay_sleeps = [t for t in slaaptijden if t > 0]
    assert len(delay_sleeps) == 0, (
        f"Verwacht geen delay bij 1 run, maar sleep werd aangeroepen met: {delay_sleeps}"
    )


async def test_sleep_tussen_requests_op_basis_van_rpm(client, logs_dir, settings_file, monkeypatch):
    """Bij 2 runs wordt sleep 1 keer aangeroepen met duur 60/RPM seconden."""
    slaaptijden = []

    async def fake_sleep(t):
        slaaptijden.append(t)

    settings_file.write_text(json.dumps({"groq_rpm": 30, "google_rpm": 15}), encoding="utf-8")
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"), \
         patch("app.GROQ_API_KEY", "test-key"):
        await client.post("/api/prompt", json=GROQ_PAYLOAD_2_RUNS)

    delay_sleeps = [t for t in slaaptijden if t > 0]
    assert len(delay_sleeps) == 1, (
        f"Verwacht 1 delay-sleep tussen 2 requests, maar slaaptijden waren: {slaaptijden}"
    )
    verwacht = 60 / 30
    assert abs(delay_sleeps[0] - verwacht) < 0.1, (
        f"Verwachte delay {verwacht}s (60/30), maar sleep was {delay_sleeps[0]}s"
    )


async def test_geen_delay_sleep_bij_ollama(client, logs_dir, settings_file, monkeypatch):
    """Bij Ollama wordt geen delay-sleep uitgevoerd, ook bij meerdere runs."""
    slaaptijden = []

    async def fake_sleep(t):
        slaaptijden.append(t)

    settings_file.write_text(json.dumps({"groq_rpm": 30, "google_rpm": 15}), encoding="utf-8")
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    ollama_payload = {**GROQ_PAYLOAD_2_RUNS, "provider": "ollama"}
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=ollama_payload)

    delay_sleeps = [t for t in slaaptijden if t > 0]
    assert len(delay_sleeps) == 0, (
        f"Verwacht geen delay bij Ollama, maar slaaptijden waren: {delay_sleeps}"
    )


async def test_geen_delay_sleep_als_rpm_nul_is(client, logs_dir, settings_file, monkeypatch):
    """Als RPM=0 is ingesteld, wordt geen delay-sleep uitgevoerd."""
    slaaptijden = []

    async def fake_sleep(t):
        slaaptijden.append(t)

    settings_file.write_text(json.dumps({"groq_rpm": 0, "google_rpm": 0}), encoding="utf-8")
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    with patch("app.call_groq", new_callable=AsyncMock, return_value="antwoord"), \
         patch("app.GROQ_API_KEY", "test-key"):
        await client.post("/api/prompt", json=GROQ_PAYLOAD_2_RUNS)

    delay_sleeps = [t for t in slaaptijden if t > 0]
    assert len(delay_sleeps) == 0, (
        f"Verwacht geen delay bij RPM=0, maar slaaptijden waren: {delay_sleeps}"
    )
