"""
Integratietests voor story 09: Rate limiting — API-quota's respecteren.

Deze tests draaien via een echte HTTP-verbinding tegen de draaiende server
(http://localhost:3000). Ze controleren of /api/settings bereikbaar is,
de juiste velden retourneert en schrijfoperaties correct verwerkt.

Vereist: python app.py draait op http://localhost:3000.
"""
import pytest

pytestmark = pytest.mark.asyncio


async def test_get_settings_geeft_200(live_client):
    """GET /api/settings is bereikbaar en geeft HTTP 200 terug."""
    response = await live_client.get("/api/settings")
    assert response.status_code == 200, (
        f"GET /api/settings gaf {response.status_code}: {response.text}"
    )


async def test_get_settings_bevat_groq_rpm(live_client):
    """GET /api/settings geeft het veld 'groq_rpm' terug."""
    response = await live_client.get("/api/settings")
    data = response.json()
    assert "groq_rpm" in data, (
        f"'groq_rpm' ontbreekt in GET /api/settings respons: {list(data.keys())}"
    )


async def test_get_settings_bevat_google_rpm(live_client):
    """GET /api/settings geeft het veld 'google_rpm' terug."""
    response = await live_client.get("/api/settings")
    data = response.json()
    assert "google_rpm" in data, (
        f"'google_rpm' ontbreekt in GET /api/settings respons: {list(data.keys())}"
    )


async def test_get_settings_groq_rpm_is_getal(live_client):
    """GET /api/settings geeft een numerieke waarde voor 'groq_rpm'."""
    response = await live_client.get("/api/settings")
    data = response.json()
    assert isinstance(data["groq_rpm"], (int, float)), (
        f"'groq_rpm' is geen getal: {data['groq_rpm']!r}"
    )


async def test_put_settings_geeft_200(live_client):
    """PUT /api/settings met geldige waarden geeft HTTP 200 terug."""
    original = (await live_client.get("/api/settings")).json()
    try:
        response = await live_client.put("/api/settings", json={"groq_rpm": 25, "google_rpm": 12})
        assert response.status_code == 200, (
            f"PUT /api/settings gaf {response.status_code}: {response.text}"
        )
    finally:
        await live_client.put("/api/settings", json=original)


async def test_put_settings_waarden_terug_te_lezen(live_client):
    """Na PUT /api/settings geeft GET de nieuwe waarden terug."""
    original = (await live_client.get("/api/settings")).json()
    try:
        await live_client.put("/api/settings", json={"groq_rpm": 25, "google_rpm": 12})
        response = await live_client.get("/api/settings")
        data = response.json()
        assert data["groq_rpm"] == 25, f"Verwacht groq_rpm=25, maar kreeg {data['groq_rpm']}"
        assert data["google_rpm"] == 12, f"Verwacht google_rpm=12, maar kreeg {data['google_rpm']}"
    finally:
        await live_client.put("/api/settings", json=original)


async def test_put_settings_met_negatieve_rpm_geeft_422(live_client):
    """PUT /api/settings met negatieve RPM geeft 422 terug."""
    response = await live_client.put("/api/settings", json={"groq_rpm": -1, "google_rpm": 15})
    assert response.status_code == 422, (
        f"Verwacht 422 voor negatieve RPM, maar kreeg {response.status_code}: {response.text}"
    )


async def test_put_settings_rpm_nul_is_toegestaan(live_client):
    """PUT /api/settings met RPM=0 is geldig."""
    original = (await live_client.get("/api/settings")).json()
    try:
        response = await live_client.put("/api/settings", json={"groq_rpm": 0, "google_rpm": 0})
        assert response.status_code == 200, (
            f"Verwacht 200 voor RPM=0, maar kreeg {response.status_code}: {response.text}"
        )
    finally:
        await live_client.put("/api/settings", json=original)
