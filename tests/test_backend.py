"""
Backend-tests voor story 01: prompt invoeren en resultaat ontvangen via Ollama.

AC gedekt:
- AC 5: leeg verplicht veld → 400 met uitleg
- AC 6: Ollama niet bereikbaar → 503 met foutmelding
- AC 3: geldige invoer → 200 met antwoord van Ollama

Story 02 heeft het API-formaat gewijzigd van {"prompt": "..."} naar acht afzonderlijke
velden. Tests zijn bijgewerkt naar het nieuwe formaat (2026-05-10).
"""
import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio

VERPLICHT = {"rol": "Python developer", "taak": "een API bouwen", "doel": "data te verwerken"}


async def test_endpoint_exists(client):
    """POST /api/prompt bestaat en geeft geen 404."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        response = await client.post("/api/prompt", json=VERPLICHT)
    assert response.status_code != 404


async def test_leeg_verplicht_veld_geeft_400(client):
    """AC 5 — leeg verplicht veld retourneert 400 met een duidelijke melding."""
    response = await client.post("/api/prompt", json={**VERPLICHT, "rol": ""})
    assert response.status_code == 400
    body = response.json()
    assert "rol" in body["detail"].lower()


async def test_geldige_invoer_retourneert_ollama_antwoord(client):
    """AC 3 — geldige invoer stuurt naar Ollama en retourneert het antwoord."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Dit is het antwoord"):
        response = await client.post("/api/prompt", json=VERPLICHT)
    assert response.status_code == 200
    assert response.json()["response"] == "Dit is het antwoord"


async def test_ollama_onbereikbaar_geeft_503(client):
    """AC 6 — als Ollama niet bereikbaar is, retourneert de API 503 met uitleg."""
    with patch(
        "app.call_ollama",
        new_callable=AsyncMock,
        side_effect=ConnectionError("Ollama niet bereikbaar"),
    ):
        response = await client.post("/api/prompt", json=VERPLICHT)
    assert response.status_code == 503
    body = response.json()
    assert body.get("detail"), "Foutmelding mag niet leeg zijn"
