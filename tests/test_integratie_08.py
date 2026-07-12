"""
Integratietests voor story 08: Review pipeline — iteratief verbeteren.

Deze tests draaien via een echte HTTP-verbinding tegen de draaiende server
(zie BASE_URL in conftest.py). Ze controleren of verzoeken met reviewers de handler
bereiken en niet worden afgewezen door FastAPI-routing of Pydantic-validatie.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.
Worden overgeslagen als de server niet bereikbaar is.
"""
import pytest

pytestmark = pytest.mark.asyncio

BASE_PAYLOAD = {
    "rol": "tester",
    "taak": "een API testen",
    "doel": "kwaliteit bewaken",
    "provider": "groq",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.8],
    "sessie": "integratie-test-08",
}


# ---------------------------------------------------------------------------
# Routing — verzoeken bereiken de handler
# ---------------------------------------------------------------------------

async def test_prompt_met_reviewers_geeft_geen_422(live_client):
    """Een JSON-verzoek met reviewers geeft nooit 422 (FastAPI mag het niet afwijzen)."""
    payload = {
        **BASE_PAYLOAD,
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    response = await live_client.post("/api/prompt", json=payload)
    assert response.status_code != 422, (
        f"Verzoek met reviewers gaf onverwacht 422: {response.text}"
    )
    assert response.status_code in (200, 400, 503), (
        f"Onverwachte statuscode {response.status_code}: {response.text}"
    )


async def test_prompt_zonder_reviewers_werkt_nog_via_http(live_client):
    """Een JSON-verzoek zonder reviewers werkt nog steeds via echte HTTP."""
    response = await live_client.post("/api/prompt", json=BASE_PAYLOAD)
    assert response.status_code != 422, (
        f"Verzoek zonder reviewers gaf onverwacht 422: {response.text}"
    )
    assert response.status_code in (200, 400, 503), (
        f"Onverwachte statuscode {response.status_code}: {response.text}"
    )


async def test_sessie_met_reviewers_opslaan_via_http(live_client):
    """Een sessie met reviewers kan worden opgeslagen via echte HTTP."""
    payload = {
        "name": "integratie-test-reviewers-08",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit",
        "provider": "groq",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
        "force": True,
    }
    response = await live_client.post("/api/sessions", json=payload)
    assert response.status_code == 200, (
        f"Sessie met reviewers opslaan mislukt: {response.status_code}: {response.text}"
    )


async def test_sessie_met_reviewers_laden_via_http(live_client):
    """Een opgeslagen sessie met reviewers kan worden geladen via echte HTTP."""
    payload = {
        "name": "integratie-test-reviewers-08",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit",
        "provider": "groq",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
        "force": True,
    }
    await live_client.post("/api/sessions", json=payload)

    response = await live_client.get("/api/sessions/integratie-test-reviewers-08")
    assert response.status_code == 200, (
        f"Sessie laden mislukt: {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "reviewers" in data, f"'reviewers' ontbreekt in geladen sessie: {list(data.keys())}"
    assert "review_modus" in data, f"'review_modus' ontbreekt in geladen sessie: {list(data.keys())}"


async def test_sessie_met_omschrijving_bevat_omschrijving_na_laden(live_client):
    """Een opgeslagen sessie met reviewers behoudt de omschrijving na opslaan en laden."""
    payload = {
        "name": "integratie-test-omschrijving-08",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit",
        "provider": "groq",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
        "force": True,
    }
    save_response = await live_client.post("/api/sessions", json=payload)
    assert save_response.status_code == 200, (
        f"Sessie opslaan mislukt: {save_response.status_code}: {save_response.text}"
    )

    response = await live_client.get("/api/sessions/integratie-test-omschrijving-08")
    assert response.status_code == 200
    data = response.json()
    reviewer = data["reviewers"][0]
    assert "omschrijving" in reviewer, (
        f"'omschrijving' ontbreekt na laden: {list(reviewer.keys())}"
    )
    assert reviewer["omschrijving"] == "Controleer op volledigheid."
