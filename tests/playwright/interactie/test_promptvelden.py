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

PROMPT_ROUTE = "**/api/prompt"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.goto(BASE_URL)


def _vul_verplichte_velden(page: Page):
    waarden = {"rol": "senior developer", "taak": "een API ontwerpen", "doel": "data op te slaan"}
    for veld, waarde in waarden.items():
        page.locator(f"[name={veld}]").fill(waarde)


# ---------------------------------------------------------------------------
# PROMPTVELDEN-I-01 — velden bereiken de backend-aanvraag
# ---------------------------------------------------------------------------

def test_optionele_velden_worden_meegestuurd_in_api_call(page: Page):
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

    page.route(PROMPT_ROUTE, inspect_route)
    _vul_verplichte_velden(page)
    page.locator("[name=formaat]").fill("markdown")
    page.get_by_role("button", name="Verstuur").click()

    page.wait_for_selector("[data-testid=run-results]")
    assert captured_body.get("formaat") == "markdown"


# ---------------------------------------------------------------------------
# PROMPTVELDEN-I-03 — newlines worden geaccepteerd
# ---------------------------------------------------------------------------

def test_taak_accepteert_newlines(page: Page):
    """Testcode: promptvelden.interactie.02
    Dekt: PROMPTVELDEN-I-03 — het `taak`-veld accepteert newlines (Enter-toets).
    """
    page.locator("[name=taak]").fill("regel 1\nregel 2")
    waarde = page.locator("[name=taak]").input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'taak': {waarde!r}"


def test_doel_accepteert_newlines(page: Page):
    """Testcode: promptvelden.interactie.03
    Dekt: PROMPTVELDEN-I-03 — het `doel`-veld accepteert newlines (Enter-toets).
    """
    page.locator("[name=doel]").fill("doel A\ndoel B")
    waarde = page.locator("[name=doel]").input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'doel': {waarde!r}"


def test_formaat_accepteert_newlines(page: Page):
    """Testcode: promptvelden.interactie.04
    Dekt: PROMPTVELDEN-I-03 — het `formaat`-veld accepteert newlines (Enter-toets).
    """
    page.locator("[name=formaat]").fill("JSON\nmarkdown")
    waarde = page.locator("[name=formaat]").input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'formaat': {waarde!r}"
