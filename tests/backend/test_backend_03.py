"""
Backend-tests voor story 03: sessie opslaan en laden.

AC gedekt:
- Geldige sessie opslaan → 200, bestand aangemaakt
- Lege sessienaam → 400
- Bestaande naam → 409; met force=true → 200 (overschrijven)
- sessions/-map wordt automatisch aangemaakt
- JSON bevat alle verplichte velden incl. provider="ollama" en model
- GET /api/sessions → lijst van namen
- GET /api/sessions/{name} → sessiedata
- Onbekende naam → 404
- Corrupt JSON → 500
"""
import json
import pytest
from unittest.mock import patch

pytestmark = pytest.mark.asyncio


@pytest.fixture
def sessions_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    return tmp_path


SESSIE = {
    "name": "mijn-sessie",
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "formaat": "JSON",
    "stijl": "technisch",
    "scope": "backend only",
    "eisen": "",
    "voorbeelden": "",
}


async def test_sessie_opslaan_geeft_200(client, sessions_dir):
    """Geldige sessie opslaan retourneert 200."""
    response = await client.post("/api/sessions", json=SESSIE)
    assert response.status_code == 200


async def test_sessie_opslaan_maakt_bestand_aan(client, sessions_dir):
    """Na opslaan bestaat het JSON-bestand in de sessions-map."""
    await client.post("/api/sessions", json=SESSIE)
    assert (sessions_dir / "mijn-sessie.json").exists()


async def test_sessie_json_bevat_verplichte_velden(client, sessions_dir):
    """Het JSON-bestand bevat name, created_at, provider, model en de acht promptvelden."""
    await client.post("/api/sessions", json=SESSIE)
    data = json.loads((sessions_dir / "mijn-sessie.json").read_text(encoding="utf-8"))
    for veld in ("name", "created_at", "provider", "model",
                 "rol", "taak", "doel", "formaat", "stijl", "scope", "eisen", "voorbeelden"):
        assert veld in data, f"Veld '{veld}' ontbreekt in opgeslagen JSON"


async def test_sessie_json_provider_is_ollama(client, sessions_dir):
    """Provider wordt als vaste waarde 'ollama' opgeslagen."""
    await client.post("/api/sessions", json=SESSIE)
    data = json.loads((sessions_dir / "mijn-sessie.json").read_text(encoding="utf-8"))
    assert data["provider"] == "ollama"


async def test_lege_sessienaam_geeft_400(client, sessions_dir):
    """Lege sessienaam retourneert 400 met uitleg."""
    response = await client.post("/api/sessions", json={**SESSIE, "name": ""})
    assert response.status_code == 400
    assert "name" in response.json()["detail"].lower()


async def test_bestaande_naam_geeft_409(client, sessions_dir):
    """Opslaan met een naam die al bestaat retourneert 409."""
    await client.post("/api/sessions", json=SESSIE)
    response = await client.post("/api/sessions", json=SESSIE)
    assert response.status_code == 409


async def test_overschrijven_met_force_geeft_200(client, sessions_dir):
    """Opslaan met bestaande naam en force=true retourneert 200."""
    await client.post("/api/sessions", json=SESSIE)
    response = await client.post("/api/sessions", json={**SESSIE, "force": True})
    assert response.status_code == 200


async def test_sessions_map_wordt_automatisch_aangemaakt(client, tmp_path, monkeypatch):
    """Backend maakt de sessions-map automatisch aan als die nog niet bestaat."""
    nieuw = tmp_path / "nieuw"
    assert not nieuw.exists()
    monkeypatch.setattr("app.SESSIONS_DIR", nieuw)
    await client.post("/api/sessions", json=SESSIE)
    assert nieuw.exists()


async def test_sessies_ophalen_geeft_lijst(client, sessions_dir):
    """GET /api/sessions retourneert een lijst met opgeslagen sessienamen."""
    await client.post("/api/sessions", json=SESSIE)
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    assert "mijn-sessie" in response.json()["sessions"]


async def test_sessies_ophalen_leeg(client, sessions_dir):
    """GET /api/sessions retourneert een lege lijst als er geen sessies zijn."""
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    assert response.json()["sessions"] == []


async def test_sessie_laden(client, sessions_dir):
    """GET /api/sessions/{name} retourneert de opgeslagen sessiedata."""
    await client.post("/api/sessions", json=SESSIE)
    response = await client.get("/api/sessions/mijn-sessie")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "mijn-sessie"
    assert data["rol"] == "Python developer"


async def test_onbekende_sessie_geeft_404(client, sessions_dir):
    """GET /api/sessions/{name} retourneert 404 als de sessie niet bestaat."""
    response = await client.get("/api/sessions/bestaat-niet")
    assert response.status_code == 404


async def test_corrupt_sessie_geeft_500(client, sessions_dir):
    """GET /api/sessions/{name} retourneert 500 als het JSON-bestand ongeldig is."""
    (sessions_dir / "kapot.json").write_text("dit is geen json", encoding="utf-8")
    response = await client.get("/api/sessions/kapot")
    assert response.status_code == 500
