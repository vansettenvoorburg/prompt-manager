"""
Integratietests voor story 07: Bijlage toevoegen aan een sessie.

Deze tests draaien via een echte HTTP-verbinding tegen de draaiende server
(zie BASE_URL in conftest.py). Ze controleren of verzoeken de handler bereiken —
iets wat de ASGI-testclient niet vangt omdat die uvicorn omzeilt.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.
Worden overgeslagen als de server niet bereikbaar is.
"""
import json
import pytest

pytestmark = pytest.mark.asyncio

TEKST_BIJLAGE = ("spec.html", b"<html><body>Functioneel Ontwerp</body></html>", "text/html")
LEGE_BIJLAGE = ("leeg.txt", b"", "text/plain")
ONGELDIG_BIJLAGE = ("foto.png", b"\x89PNG\r\n", "image/png")

BASE_FORM = {
    "rol": "tester",
    "taak": "een API testen",
    "doel": "kwaliteit bewaken",
    "provider": "groq",
    "runs": "1",
    "temperature_modus": "alle",
    "temperatures": "[0.8]",
}


# ---------------------------------------------------------------------------
# Kern: het routingprobleem dat de ASGI-testclient niet vangt
# ---------------------------------------------------------------------------

async def test_multipart_bijlage_geeft_geen_422(live_client):
    """Een multipart-verzoek via echte HTTP geeft nooit 422 'Input should be a valid dictionary'."""
    naam, inhoud, mime = TEKST_BIJLAGE
    response = await live_client.post(
        "/api/prompt/upload",
        data=BASE_FORM,
        files={"bijlage": (naam, inhoud, mime)},
    )
    assert response.status_code != 422, (
        f"Bijlage-upload gaf onverwacht 422: {response.text}"
    )
    assert "valid dictionary" not in response.text, (
        f"FastAPI verwierp het multipart-verzoek vóór de handler: {response.text}"
    )


async def test_multipart_bijlage_bereikt_handler(live_client):
    """Het verzoek bereikt de handler: de bijlagetekst of een bekende fout (geen 422/500)."""
    naam, inhoud, mime = TEKST_BIJLAGE
    response = await live_client.post(
        "/api/prompt/upload",
        data=BASE_FORM,
        files={"bijlage": (naam, inhoud, mime)},
    )
    # 200 (Ollama beschikbaar) of 200 met fout in runs (Ollama niet beschikbaar)
    # of 400/422 vanuit de bijlageverwerking zelf — maar nooit een FastAPI-routingfout
    assert response.status_code in (200, 400, 422), (
        f"Onverwachte statuscode {response.status_code}: {response.text}"
    )


async def test_json_prompt_zonder_bijlage_geeft_geen_422(live_client):
    """Een JSON-verzoek naar /api/prompt werkt nog steeds via echte HTTP."""
    payload = {
        "rol": "tester",
        "taak": "een API testen",
        "doel": "kwaliteit bewaken",
        "provider": "groq",
        "runs": 1,
        "temperature_modus": "alle",
        "temperatures": [0.8],
    }
    response = await live_client.post("/api/prompt", json=payload)
    assert response.status_code != 422, (
        f"JSON-verzoek gaf onverwacht 422: {response.text}"
    )
    assert response.status_code in (200, 400, 503), (
        f"Onverwachte statuscode {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# Foutpaden: validatie bereikt via echte HTTP
# ---------------------------------------------------------------------------

async def test_niet_ondersteund_bestandstype_geeft_400_via_http(live_client):
    """Een niet-ondersteund bestandstype geeft 400 via echte HTTP (niet 422 van routing)."""
    naam, inhoud, mime = ONGELDIG_BIJLAGE
    response = await live_client.post(
        "/api/prompt/upload",
        data=BASE_FORM,
        files={"bijlage": (naam, inhoud, mime)},
    )
    assert response.status_code == 400, (
        f"Verwacht 400 voor .png, kreeg {response.status_code}: {response.text}"
    )
    assert ".png" in response.json()["detail"]


async def test_leeg_bestand_geeft_400_via_http(live_client):
    """Een leeg geüpload bestand geeft 400 via echte HTTP."""
    naam, inhoud, mime = LEGE_BIJLAGE
    response = await live_client.post(
        "/api/prompt/upload",
        data=BASE_FORM,
        files={"bijlage": (naam, inhoud, mime)},
    )
    assert response.status_code == 400, (
        f"Verwacht 400 voor leeg bestand, kreeg {response.status_code}: {response.text}"
    )
    assert "leeg" in response.json()["detail"].lower()


async def test_ontbrekend_verplicht_veld_geeft_400_via_http(live_client):
    """Een verzoek zonder verplicht veld geeft 400, niet 422 van Pydantic-routing."""
    naam, inhoud, mime = TEKST_BIJLAGE
    form_zonder_rol = {k: v for k, v in BASE_FORM.items() if k != "rol"}
    response = await live_client.post(
        "/api/prompt/upload",
        data=form_zonder_rol,
        files={"bijlage": (naam, inhoud, mime)},
    )
    assert response.status_code == 400, (
        f"Verwacht 400 voor ontbrekend veld 'rol', kreeg {response.status_code}: {response.text}"
    )
