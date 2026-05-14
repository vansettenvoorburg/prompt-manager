"""
Frontend-tests voor story 04: logging.

Vereist: de app draait op http://localhost:3000 (python app.py).

AC gedekt:
- Na succesvolle aanvraag toont de UI een melding 'Log opgeslagen'
- Als logging mislukt (log_warning in response), toont de UI een waarschuwing
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"
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
        body='{"response": "Antwoord van model", "log_status": "ok", "log_path": "/logs/2026-05-14_ollama_test.json"}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=log-status]")).to_be_visible()
    expect(page.locator("[data-testid=log-status]")).to_contain_text("Log opgeslagen")
    expect(page.locator("[data-testid=log-status]")).to_contain_text("2026-05-14_ollama_test.json")


# ---------------------------------------------------------------------------
# Waarschuwing bij logfout
# ---------------------------------------------------------------------------

def test_log_mislukt_toont_waarschuwing(page: Page):
    """Als logging mislukt (log_warning in response), toont de UI een waarschuwing."""
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"response": "Antwoord van model", "log_warning": "Logging mislukt"}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=log-warning]")).to_be_visible()


def test_log_mislukt_toont_antwoord_toch(page: Page):
    """Bij een logfout wordt het modelantwoord nog steeds getoond."""
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"response": "Antwoord ondanks logfout", "log_warning": "Logging mislukt"}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=response]")).to_contain_text("Antwoord ondanks logfout")
