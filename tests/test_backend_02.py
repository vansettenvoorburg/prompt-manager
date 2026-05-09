"""
Backend-tests voor story 02: prompt samenstellen via acht velden.

AC gedekt:
- Endpoint accepteert acht velden; samengestelde prompt gaat naar Ollama
- rol, taak en doel zijn verplicht; leeg veld → 400 met veldnaam in melding
- Optionele velden die leeg zijn worden weggelaten uit de samengestelde prompt
- Vaste template-structuur wordt correct opgebouwd
- Geen Ollama-call als een verplicht veld ontbreekt (achterwaartse compat: 503 blijft werken)
"""
import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio

VERPLICHT = {"rol": "Python developer", "taak": "een API bouwen", "doel": "data te verwerken"}
ALLE_VELDEN = {
    **VERPLICHT,
    "formaat": "JSON",
    "stijl": "technisch",
    "scope": "backend only",
    "eisen": "geen externe afhankelijkheden",
    "voorbeelden": "zie bijlage",
}


async def test_endpoint_accepteert_acht_velden(client):
    """Endpoint /api/prompt accepteert de acht nieuwe velden en geeft 200 terug."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="Antwoord"):
        response = await client.post("/api/prompt", json=ALLE_VELDEN)
    assert response.status_code == 200


async def test_prompt_template_vaste_structuur(client):
    """De samengestelde prompt volgt de vaste template met correcte labels."""
    captured = {}

    async def mock_ollama(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Antwoord"

    with patch("app.call_ollama", side_effect=mock_ollama):
        await client.post("/api/prompt", json=ALLE_VELDEN)

    p = captured["prompt"]
    assert p.startswith("Als Python developer wil ik een API bouwen zodat data te verwerken.")
    assert "Formaat: JSON" in p
    assert "Stijl: technisch" in p
    assert "Scope: backend only" in p
    assert "Extra eisen: geen externe afhankelijkheden" in p
    assert "Voorbeelden: zie bijlage" in p


async def test_lege_optionele_velden_worden_weggelaten(client):
    """Optionele velden met lege waarde verschijnen niet als regel in de samengestelde prompt."""
    captured = {}

    async def mock_ollama(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Antwoord"

    payload = {**VERPLICHT, "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": ""}
    with patch("app.call_ollama", side_effect=mock_ollama):
        await client.post("/api/prompt", json=payload)

    p = captured["prompt"]
    assert "Formaat:" not in p
    assert "Stijl:" not in p
    assert "Scope:" not in p
    assert "Extra eisen:" not in p
    assert "Voorbeelden:" not in p


async def test_gedeeltelijk_optioneel_ingevuld(client):
    """Alleen ingevulde optionele velden verschijnen in de prompt; lege worden overgeslagen."""
    captured = {}

    async def mock_ollama(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Antwoord"

    payload = {**VERPLICHT, "formaat": "markdown", "stijl": "", "scope": "", "eisen": "", "voorbeelden": ""}
    with patch("app.call_ollama", side_effect=mock_ollama):
        await client.post("/api/prompt", json=payload)

    p = captured["prompt"]
    assert "Formaat: markdown" in p
    assert "Stijl:" not in p


async def test_lege_rol_geeft_400(client):
    """Verplicht veld rol leeg → 400 met 'rol' in de foutmelding."""
    response = await client.post("/api/prompt", json={**ALLE_VELDEN, "rol": ""})
    assert response.status_code == 400
    assert "rol" in response.json()["detail"].lower()


async def test_lege_taak_geeft_400(client):
    """Verplicht veld taak leeg → 400 met 'taak' in de foutmelding."""
    response = await client.post("/api/prompt", json={**ALLE_VELDEN, "taak": ""})
    assert response.status_code == 400
    assert "taak" in response.json()["detail"].lower()


async def test_leeg_doel_geeft_400(client):
    """Verplicht veld doel leeg → 400 met 'doel' in de foutmelding."""
    response = await client.post("/api/prompt", json={**ALLE_VELDEN, "doel": ""})
    assert response.status_code == 400
    assert "doel" in response.json()["detail"].lower()


async def test_geen_ollama_call_bij_leeg_verplicht_veld(client):
    """Er wordt geen Ollama-call gedaan zolang een verplicht veld leeg is."""
    with patch("app.call_ollama", new_callable=AsyncMock) as mock_ollama:
        await client.post("/api/prompt", json={**ALLE_VELDEN, "rol": ""})
    mock_ollama.assert_not_called()


async def test_ollama_onbereikbaar_geeft_503(client):
    """Achterwaartse compat story 01: Ollama niet bereikbaar → 503."""
    with patch(
        "app.call_ollama",
        new_callable=AsyncMock,
        side_effect=ConnectionError("Ollama niet bereikbaar"),
    ):
        response = await client.post("/api/prompt", json=ALLE_VELDEN)
    assert response.status_code == 503
    assert response.json().get("detail")
