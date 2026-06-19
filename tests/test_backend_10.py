"""
Backend-tests voor story 10: Kopieerknop en formulieropmaak.

AC gedekt:
- Newlines in `taak` worden als \\n bewaard in de sessie-JSON
- Newlines in `doel` worden als \\n bewaard in de sessie-JSON
- Newlines in `formaat` worden als \\n bewaard in de sessie-JSON
- Newlines worden bij laden hersteld via GET /api/sessions/{name}
- Validatie op `taak` werkt na omzetting: alleen newlines is ongeldig
- Validatie op `doel` werkt na omzetting: alleen newlines is ongeldig
- Validatie op `rol` werkt ongewijzigd: alleen newlines is ongeldig
"""
import json
import pytest

pytestmark = pytest.mark.asyncio

_BASIS_SESSIE = {
    "name": "test-sessie",
    "provider": "ollama",
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "formaat": "",
}

_BASIS_PROMPT = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "provider": "ollama",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}


@pytest.fixture
def sessions_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Newlines opslaan in sessie-JSON
# ---------------------------------------------------------------------------

async def test_newlines_in_taak_worden_opgeslagen(client, sessions_dir):
    """Newlines in `taak` worden als \\n bewaard in de sessie-JSON."""
    body = {**_BASIS_SESSIE, "taak": "stap 1\nstap 2"}
    response = await client.post("/api/sessions", json=body)
    assert response.status_code == 200

    pad = sessions_dir / "test-sessie.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    assert data["taak"] == "stap 1\nstap 2", (
        f"Newline in 'taak' werd niet bewaard: {data['taak']!r}"
    )


async def test_newlines_in_doel_worden_opgeslagen(client, sessions_dir):
    """Newlines in `doel` worden als \\n bewaard in de sessie-JSON."""
    body = {**_BASIS_SESSIE, "doel": "doel A\ndoel B"}
    response = await client.post("/api/sessions", json=body)
    assert response.status_code == 200

    pad = sessions_dir / "test-sessie.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    assert data["doel"] == "doel A\ndoel B", (
        f"Newline in 'doel' werd niet bewaard: {data['doel']!r}"
    )


async def test_newlines_in_formaat_worden_opgeslagen(client, sessions_dir):
    """Newlines in `formaat` worden als \\n bewaard in de sessie-JSON."""
    body = {**_BASIS_SESSIE, "formaat": "JSON\nmarkdown"}
    response = await client.post("/api/sessions", json=body)
    assert response.status_code == 200

    pad = sessions_dir / "test-sessie.json"
    data = json.loads(pad.read_text(encoding="utf-8"))
    assert data["formaat"] == "JSON\nmarkdown", (
        f"Newline in 'formaat' werd niet bewaard: {data['formaat']!r}"
    )


# ---------------------------------------------------------------------------
# Newlines herstellen via GET
# ---------------------------------------------------------------------------

async def test_newlines_worden_hersteld_bij_laden(client, sessions_dir):
    """Via GET /api/sessions/{name} komen de newlines ongewijzigd terug."""
    body = {**_BASIS_SESSIE, "taak": "stap 1\nstap 2", "formaat": "JSON\nmarkdown"}
    await client.post("/api/sessions", json=body)

    response = await client.get("/api/sessions/test-sessie")
    assert response.status_code == 200
    data = response.json()
    assert data["taak"] == "stap 1\nstap 2", (
        f"Newline in 'taak' niet hersteld: {data['taak']!r}"
    )
    assert data["formaat"] == "JSON\nmarkdown", (
        f"Newline in 'formaat' niet hersteld: {data['formaat']!r}"
    )


# ---------------------------------------------------------------------------
# Validatie — werkt ongewijzigd na omzetting naar textarea
# ---------------------------------------------------------------------------

async def test_validatie_taak_met_alleen_newlines_geeft_400(client):
    """`taak` met alleen newlines (leeg na strip) wordt geweigerd door POST /api/prompt."""
    body = {**_BASIS_PROMPT, "taak": "\n\n"}
    response = await client.post("/api/prompt", json=body)
    assert response.status_code == 400, (
        f"Verwacht 400 voor lege 'taak', maar kreeg {response.status_code}: {response.text}"
    )


async def test_validatie_doel_met_alleen_newlines_geeft_400(client):
    """`doel` met alleen newlines (leeg na strip) wordt geweigerd door POST /api/prompt."""
    body = {**_BASIS_PROMPT, "doel": "\n\n"}
    response = await client.post("/api/prompt", json=body)
    assert response.status_code == 400, (
        f"Verwacht 400 voor leeg 'doel', maar kreeg {response.status_code}: {response.text}"
    )


async def test_validatie_rol_met_alleen_newlines_geeft_400(client):
    """`rol` met alleen newlines (leeg na strip) wordt geweigerd door POST /api/prompt."""
    body = {**_BASIS_PROMPT, "rol": "\n"}
    response = await client.post("/api/prompt", json=body)
    assert response.status_code == 400, (
        f"Verwacht 400 voor lege 'rol', maar kreeg {response.status_code}: {response.text}"
    )
