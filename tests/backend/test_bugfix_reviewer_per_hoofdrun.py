"""
Regressietest voor bug: het aantal reviews houdt geen rekening met meerdere hoofdruns.

Gemeld gedrag: bij 'Aantal runs' (hoofdprompt) = 3 en 1 reviewer met 3 runs
verwacht de gebruiker dat elke hoofdrun zijn eigen reviewketen krijgt
(3 hoofdruns x 3 reviewer-runs = 9 reviewer-stappen). In werkelijkheid werd
alleen de output van de láátste hoofdrun gereviewd (3 reviewer-stappen in
totaal), waardoor het aantal reviews niet overeenkwam met de configuratie.
"""
import json
from unittest.mock import patch, AsyncMock
import pytest

pytestmark = pytest.mark.asyncio


async def test_elke_hoofdrun_krijgt_eigen_reviewketen(client, tmp_path, monkeypatch):
    """3 hoofdruns + 1 reviewer met 3 runs geeft 9 reviewer-stappen, 3 per hoofdrun."""
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    payload = {
        "rol": "Python developer",
        "taak": "een API bouwen",
        "doel": "data te verwerken",
        "provider": "ollama",
        "runs": 3,
        "temperature_modus": "alle",
        "temperatures": [0.7],
        "reviewers": [
            {"rol": "QA engineer", "omschrijving": "Controleer volledigheid.", "runs": 3, "temperatures": [0.5, 0.6, 0.7]},
        ],
        "review_modus": "iteratief",
    }

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()

    assert len(data["runs"]) == 3, f"Verwacht 3 hoofdruns, kreeg {len(data['runs'])}"
    assert len(data["reviewer_stappen"]) == 9, (
        f"Verwacht 9 reviewer-stappen (3 hoofdruns x 3 reviewer-runs), "
        f"kreeg {len(data['reviewer_stappen'])}: {data['reviewer_stappen']}"
    )

    for hoofdrun_nummer in (1, 2, 3):
        stappen_voor_run = [s for s in data["reviewer_stappen"] if s.get("hoofdrun_nummer") == hoofdrun_nummer]
        assert len(stappen_voor_run) == 3, (
            f"Hoofdrun {hoofdrun_nummer} heeft {len(stappen_voor_run)} reviewer-stappen, verwacht 3"
        )
