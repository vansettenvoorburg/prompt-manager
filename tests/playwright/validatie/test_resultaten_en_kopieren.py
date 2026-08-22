"""
Validatie-tests voor resultaten weergeven en kopiëren.

Bron: documentatie/acceptatiecriteria/resultaten-en-kopieren.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
resultaten_en_kopieren.validatie.01 — bewust een ander formaat dan de AC-codes
(RESULTAAT-V-01).

RESULTAAT-V-03 (API-limiet na 3 pogingen) wordt gedekt door de backend/integratietests
(tests/backend/test_backend_09.py) — geen aparte Playwright-test nodig.
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


def _stub_prompt_response(page: Page):
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "dit is de uitvoer", "log_status": "ok"}]}',
    ))


def _mock_clipboard_mislukt(page: Page):
    page.evaluate(
        "navigator.clipboard = { writeText: (t) => Promise.reject(new Error('geen toestemming')) }"
    )


# ---------------------------------------------------------------------------
# RESULTAAT-V-01 — klembord niet beschikbaar
# ---------------------------------------------------------------------------

def test_kopieerknop_toont_mislukt_bij_geen_klembord_toegang(page: Page):
    """Testcode: resultaten_en_kopieren.validatie.01
    Dekt: RESULTAAT-V-01 — als het klembord niet beschikbaar is, toont de knop kort 'Mislukt'.
    """
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    _mock_clipboard_mislukt(page)

    knop = page.locator("[data-testid=run-results] [data-testid=kopieer-knop]").first
    knop.click()

    expect(knop).to_have_text("Mislukt")


# ---------------------------------------------------------------------------
# RESULTAAT-V-02 — logfout toont waarschuwing, antwoord blijft zichtbaar
# ---------------------------------------------------------------------------

def test_log_mislukt_toont_waarschuwing(page: Page):
    """Testcode: resultaten_en_kopieren.validatie.02
    Dekt: RESULTAAT-V-02 — als logging mislukt (log_warning in response), toont de UI een waarschuwing.
    """
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord van model", "log_warning": "Logging mislukt"}]}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_contain_text("Logging mislukt")


def test_log_mislukt_toont_antwoord_toch(page: Page):
    """Testcode: resultaten_en_kopieren.validatie.03
    Dekt: RESULTAAT-V-02 — bij een logfout wordt het modelantwoord nog steeds getoond.
    """
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord ondanks logfout", "log_warning": "Logging mislukt"}]}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_contain_text("Antwoord ondanks logfout")
    expect(page.locator("[data-testid=run-results]")).to_contain_text("Logging mislukt")
