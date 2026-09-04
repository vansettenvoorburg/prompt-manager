"""
Backend-tests voor story 15: Eigen eindoutput per hoofdrun.

Bron: documentatie/acceptatiecriteria/review-pipeline.md
AC gedekt: REVIEW-I-05, REVIEW-V-03.

Bij meerdere hoofdruns met reviewers overschrijft de backend momenteel het
eindresultaat van elke hoofdrun in de loop, waardoor alleen het eindresultaat
van de láátste hoofdrun in de response overblijft (zie stories/15-eindoutput-per-hoofdrun.md).
Deze tests verwachten in plaats daarvan een 'eindoutputs'-lijst met één
item per hoofdrun, gekoppeld via 'hoofdrun_nummer'.
"""
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio

BASE_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "provider": "ollama",
    "temperature_modus": "alle",
    "temperatures": [0.7],
}


def _payload_twee_hoofdruns_met_reviewer() -> dict:
    return {
        **BASE_PAYLOAD,
        "runs": 2,
        "reviewers": [
            {"rol": "QA engineer", "omschrijving": "Controleer volledigheid.", "runs": 1, "temperatures": [0.5]},
        ],
        "review_modus": "iteratief",
    }


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# REVIEW-I-05 — eindresultaat per hoofdrun, gekoppeld aan het hoofdrun-nummer
# ---------------------------------------------------------------------------

async def test_response_bevat_eindoutputs_lijst_bij_meerdere_hoofdruns(client, logs_dir):
    """Bij 2 hoofdruns met reviewer bevat de response een 'eindoutputs'-lijst met 2 items."""
    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=["hoofdrun1 antwoord", "hoofdrun2 antwoord",
                            "hoofdrun1 review", "hoofdrun2 review"]):
        response = await client.post("/api/prompt", json=_payload_twee_hoofdruns_met_reviewer())

    assert response.status_code == 200, response.text
    data = response.json()
    assert "eindoutputs" in data, f"'eindoutputs' ontbreekt in response: {data.keys()}"
    assert len(data["eindoutputs"]) == 2, (
        f"Verwacht 2 items in 'eindoutputs' (1 per hoofdrun), kreeg {len(data['eindoutputs'])}"
    )


async def test_eindoutputs_items_zijn_gekoppeld_aan_hun_eigen_hoofdrun_nummer(client, logs_dir):
    """Elk item in 'eindoutputs' vermeldt het hoofdrun-nummer waar het bij hoort."""
    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=["hoofdrun1 antwoord", "hoofdrun2 antwoord",
                            "hoofdrun1 review", "hoofdrun2 review"]):
        response = await client.post("/api/prompt", json=_payload_twee_hoofdruns_met_reviewer())

    data = response.json()
    hoofdrun_nummers = sorted(item["hoofdrun_nummer"] for item in data["eindoutputs"])
    assert hoofdrun_nummers == [1, 2], (
        f"Verwachte hoofdrun-nummers [1, 2] in 'eindoutputs', kreeg: {hoofdrun_nummers}"
    )


async def test_eindoutput_per_hoofdrun_is_niet_samengevoegd_met_andere_hoofdrun(client, logs_dir):
    """Regressie: het eindresultaat van hoofdrun 1 mag niet overschreven zijn door hoofdrun 2
    (de bug uit stories/15-eindoutput-per-hoofdrun.md: alleen de láátste hoofdrun bleef over)."""
    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=["hoofdrun1 antwoord", "hoofdrun2 antwoord",
                            "hoofdrun1 review", "hoofdrun2 review"]):
        response = await client.post("/api/prompt", json=_payload_twee_hoofdruns_met_reviewer())

    data = response.json()
    per_hoofdrun = {item["hoofdrun_nummer"]: item.get("eindoutput") for item in data["eindoutputs"]}
    assert per_hoofdrun.get(1) == "hoofdrun1 review", (
        f"Eindoutput van hoofdrun 1 is niet zijn eigen resultaat: {per_hoofdrun}"
    )
    assert per_hoofdrun.get(2) == "hoofdrun2 review", (
        f"Eindoutput van hoofdrun 2 is niet zijn eigen resultaat: {per_hoofdrun}"
    )


# ---------------------------------------------------------------------------
# REVIEW-V-03 — reviewketen van één hoofdrun faalt op de laatste stap
# ---------------------------------------------------------------------------

async def test_falende_reviewketen_van_een_hoofdrun_geeft_foutmelding_in_eindoutputs(client, logs_dir):
    """Faalt de laatste reviewstap van hoofdrun 1 (bv. API-limiet), dan bevat het
    'eindoutputs'-item van hoofdrun 1 een foutmelding in plaats van een eindoutput."""
    from app import RateLimitError

    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=["hoofdrun1 antwoord", "hoofdrun2 antwoord",
                            RateLimitError(3), "hoofdrun2 review"]):
        response = await client.post("/api/prompt", json=_payload_twee_hoofdruns_met_reviewer())

    assert response.status_code == 200, response.text
    data = response.json()
    item_hoofdrun_1 = next(item for item in data["eindoutputs"] if item["hoofdrun_nummer"] == 1)
    assert "fout" in item_hoofdrun_1, (
        f"Geen foutindicatie in eindoutputs-item van de gefaalde hoofdrun: {item_hoofdrun_1}"
    )


async def test_falende_reviewketen_van_een_hoofdrun_laat_andere_hoofdruns_onaangetast(client, logs_dir):
    """Faalt de reviewketen van hoofdrun 1, dan blijft het eindoutputs-item van hoofdrun 2
    zijn eigen, correcte resultaat tonen."""
    from app import RateLimitError

    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=["hoofdrun1 antwoord", "hoofdrun2 antwoord",
                            RateLimitError(3), "hoofdrun2 review"]):
        response = await client.post("/api/prompt", json=_payload_twee_hoofdruns_met_reviewer())

    data = response.json()
    item_hoofdrun_2 = next(item for item in data["eindoutputs"] if item["hoofdrun_nummer"] == 2)
    assert item_hoofdrun_2.get("eindoutput") == "hoofdrun2 review", (
        f"Eindoutput van hoofdrun 2 is aangetast door de gefaalde hoofdrun 1: {item_hoofdrun_2}"
    )
    assert "fout" not in item_hoofdrun_2, (
        f"Hoofdrun 2 toont onterecht een foutindicatie: {item_hoofdrun_2}"
    )


# ---------------------------------------------------------------------------
# REVIEW-W-06 — bij precies één hoofdrun blijft het bestaande 'eindoutput'-veld werken
# ---------------------------------------------------------------------------

async def test_een_hoofdrun_geeft_geen_eindoutputs_lijst(client, logs_dir):
    """Bij precies 1 hoofdrun blijft het gedrag ongewijzigd: geen 'eindoutputs'-lijst,
    alleen het bestaande 'eindoutput'-veld (zie test_backend_08.test_eindoutput_is_output_van_laatste_stap)."""
    payload = {
        **BASE_PAYLOAD,
        "runs": 1,
        "reviewers": [
            {"rol": "QA engineer", "omschrijving": "Controleer volledigheid.", "runs": 1, "temperatures": [0.5]},
        ],
        "review_modus": "iteratief",
    }
    with patch("app.call_ollama", new_callable=AsyncMock,
               side_effect=["hoofdrun antwoord", "review"]):
        response = await client.post("/api/prompt", json=payload)

    data = response.json()
    assert "eindoutputs" not in data, (
        f"'eindoutputs' zou niet aanwezig moeten zijn bij precies 1 hoofdrun: {data.keys()}"
    )
