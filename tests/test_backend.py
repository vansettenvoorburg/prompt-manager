"""
Backend-tests voor story 01: prompt invoeren en resultaat ontvangen via Ollama.

AC gedekt:
- AC 5: lege prompt → 400 met uitleg
- AC 6: Ollama niet bereikbaar → 503 met foutmelding
- AC 3: geldige prompt → 200 met antwoord van Ollama
"""
import pytest
from unittest.mock import AsyncMock, patch


pytestmark = pytest.mark.asyncio


async def test_endpoint_exists(client):
    """POST /api/prompt bestaat en geeft geen 404."""
    response = await client.post("/api/prompt", json={"prompt": "Hallo"})
    assert response.status_code != 404


async def test_lege_prompt_geeft_400(client):
    """AC 5 — lege prompt retourneert 400 met een duidelijke melding."""
    response = await client.post("/api/prompt", json={"prompt": ""})
    assert response.status_code == 400
    body = response.json()
    assert "prompt" in body["detail"].lower()


async def test_geldige_prompt_retourneert_ollama_antwoord(client):
    """AC 3 — geldige prompt stuurt naar Ollama en retourneert het antwoord."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Dit is het antwoord"):
        response = await client.post("/api/prompt", json={"prompt": "Hallo"})
    assert response.status_code == 200
    assert response.json()["response"] == "Dit is het antwoord"


async def test_ollama_onbereikbaar_geeft_503(client):
    """AC 6 — als Ollama niet bereikbaar is, retourneert de API 503 met uitleg."""
    with patch(
        "app.call_ollama",
        new_callable=AsyncMock,
        side_effect=ConnectionError("Ollama niet bereikbaar"),
    ):
        response = await client.post("/api/prompt", json={"prompt": "Hallo"})
    assert response.status_code == 503
    body = response.json()
    assert body.get("detail"), "Foutmelding mag niet leeg zijn"
