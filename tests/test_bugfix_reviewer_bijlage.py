"""
Regressietest voor bug: reviewer-configuratie wordt genegeerd bij een aanvraag met bijlage.

Gemeld gedrag: de gebruiker voegt een reviewer toe en configureert een bijlage.
Bij versturen wordt de reviewer-stap niet uitgevoerd. Oorzaak: de frontend stuurt
bijlage-aanvragen naar /api/prompt/upload, en dat endpoint leest de velden
'reviewers' en 'review_modus' niet uit de form-data — ze worden stilzwijgend
genegeerd, ook al stuurt de frontend ze wel mee.
"""
import json
from unittest.mock import patch, AsyncMock
import pytest

pytestmark = pytest.mark.asyncio


async def test_reviewer_wordt_uitgevoerd_bij_aanvraag_met_bijlage(client, tmp_path, monkeypatch):
    """Een aanvraag met bijlage én een geconfigureerde reviewer voert de reviewstap nog uit."""
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)

    reviewers = json.dumps([
        {"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}
    ])
    form = {
        "rol": "tester",
        "taak": "een API testen",
        "doel": "kwaliteit bewaken",
        "provider": "ollama",
        "runs": "1",
        "temperature_modus": "alle",
        "temperatures": "[0.8]",
        "reviewers": reviewers,
        "review_modus": "iteratief",
    }

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post(
            "/api/prompt/upload",
            data=form,
            files={"bijlage": ("notities.txt", b"inhoud van de bijlage", "text/plain")},
        )

    assert response.status_code == 200, f"Onverwachte statuscode: {response.status_code}: {response.text}"
    data = response.json()
    assert "reviewer_stappen" in data and len(data["reviewer_stappen"]) > 0, (
        f"De reviewer-stap werd niet uitgevoerd bij een aanvraag met bijlage: {data}"
    )
