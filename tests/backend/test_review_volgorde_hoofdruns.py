"""
Test voor AC in documentatie/acceptatiecriteria/08-review-iteratief.md (Uitvoervolgorde bij meerdere hoofdruns):
elke hoofdrun doorloopt eerst zijn volledige reviewketen voordat de volgende hoofdrun start.
"""
from unittest.mock import patch, AsyncMock
import pytest

pytestmark = pytest.mark.asyncio


async def test_volgorde_is_per_hoofdrun_volledige_reviewketen_voor_volgende_hoofdrun(client, tmp_path, monkeypatch):
    """Bij 2 hoofdruns en 2 reviewers is de volgorde: hoofdrun1-rev1, hoofdrun1-rev2, hoofdrun2-rev1, hoofdrun2-rev2."""
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    payload = {
        "rol": "Python developer",
        "taak": "een API bouwen",
        "doel": "data te verwerken",
        "provider": "ollama",
        "runs": 2,
        "temperature_modus": "alle",
        "temperatures": [0.7],
        "reviewers": [
            {"rol": "Reviewer 1", "omschrijving": "Controleer stijl.", "runs": 1, "temperatures": [0.5]},
            {"rol": "Reviewer 2", "omschrijving": "Controleer inhoud.", "runs": 1, "temperatures": [0.5]},
        ],
        "review_modus": "iteratief",
    }

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()

    volgorde = [(s["hoofdrun_nummer"], s["reviewer_nr"]) for s in data["reviewer_stappen"]]
    assert volgorde == [(1, 1), (1, 2), (2, 1), (2, 2)], (
        f"Verwachte volgorde: elke hoofdrun volledig doorlopen vóór de volgende. Kreeg: {volgorde}"
    )
