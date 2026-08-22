"""
Interactie-tests voor promptvelden.

Bron: documentatie/acceptatiecriteria/promptvelden.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
promptvelden.interactie.01 — bewust een ander formaat dan de AC-codes (PROMPTVELDEN-I-01).

PROMPTVELDEN-I-01 (vaste template) en PROMPTVELDEN-I-02 (lege optionele velden
weggelaten) worden gedekt door de backend/integratietests (tests/backend/) die de
samengestelde promptstring rechtstreeks verifiëren — geen aparte Playwright-test nodig.
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# PROMPTVELDEN-I-01 — velden bereiken de backend-aanvraag
# ---------------------------------------------------------------------------

def test_optionele_velden_worden_meegestuurd_in_api_call(app: PromptPage):
    """Testcode: promptvelden.interactie.01
    Dekt: PROMPTVELDEN-I-01 — een ingevuld optioneel veld staat in het verstuurde JSON-body.
    """
    captured_body = {}

    def inspect_route(route):
        captured_body.update(route.request.post_data_json)
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "ok"}]}',
        )

    app.page.route("**/api/prompt", inspect_route)
    app.vul_verplichte_velden()
    app.fill_veld("formaat", "markdown")
    app.verstuur()

    app.page.wait_for_selector("[data-testid=run-results]")
    assert captured_body.get("formaat") == "markdown"


# ---------------------------------------------------------------------------
# PROMPTVELDEN-I-03 — newlines worden geaccepteerd
# ---------------------------------------------------------------------------

def test_taak_accepteert_newlines(app: PromptPage):
    """Testcode: promptvelden.interactie.02
    Dekt: PROMPTVELDEN-I-03 — het `taak`-veld accepteert newlines (Enter-toets).
    """
    app.fill_veld("taak", "regel 1\nregel 2")
    waarde = app.taak_input.input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'taak': {waarde!r}"


def test_doel_accepteert_newlines(app: PromptPage):
    """Testcode: promptvelden.interactie.03
    Dekt: PROMPTVELDEN-I-03 — het `doel`-veld accepteert newlines (Enter-toets).
    """
    app.fill_veld("doel", "doel A\ndoel B")
    waarde = app.doel_input.input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'doel': {waarde!r}"


def test_formaat_accepteert_newlines(app: PromptPage):
    """Testcode: promptvelden.interactie.04
    Dekt: PROMPTVELDEN-I-03 — het `formaat`-veld accepteert newlines (Enter-toets).
    """
    app.fill_veld("formaat", "JSON\nmarkdown")
    waarde = app.formaat_input.input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'formaat': {waarde!r}"
