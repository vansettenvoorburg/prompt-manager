"""
Frontend-tests voor story 04: logging.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.

AC gedekt:
- Na succesvolle aanvraag toont de UI een melding 'Log opgeslagen'
- Als logging mislukt (log_warning in response), toont de UI een waarschuwing
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
PROMPT_ROUTE = "**/api/prompt"
SESSIONS_ROUTE = "**/api/sessions"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))
    page.goto(BASE_URL)


def _vul_verplichte_velden(page: Page):
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")


# ---------------------------------------------------------------------------
# Log opgeslagen melding
# ---------------------------------------------------------------------------

def test_log_opgeslagen_melding_zichtbaar_na_aanvraag(page: Page):
    """Na een succesvolle aanvraag toont de UI 'Log opgeslagen' met het bestandspad."""
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord van model", "log_status": "ok", "log_path": "/logs/2026-05-14_ollama_test.json"}]}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_contain_text("Log opgeslagen")
    expect(page.locator("[data-testid=run-results]")).to_contain_text("2026-05-14_ollama_test.json")


# ---------------------------------------------------------------------------
# Waarschuwing bij logfout
# ---------------------------------------------------------------------------

def test_log_mislukt_toont_waarschuwing(page: Page):
    """Als logging mislukt (log_warning in response), toont de UI een waarschuwing."""
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord van model", "log_warning": "Logging mislukt"}]}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_contain_text("Logging mislukt")


def test_log_mislukt_toont_antwoord_toch(page: Page):
    """Bij een logfout wordt het modelantwoord nog steeds getoond."""
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord ondanks logfout", "log_warning": "Logging mislukt"}]}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_contain_text("Antwoord ondanks logfout")
    expect(page.locator("[data-testid=run-results]")).to_contain_text("Logging mislukt")
