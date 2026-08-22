"""
Interactie-tests voor resultaten weergeven en kopiëren.

Bron: documentatie/acceptatiecriteria/resultaten-en-kopieren.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
resultaten_en_kopieren.interactie.01 — bewust een ander formaat dan de AC-codes
(RESULTAAT-I-01).
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


def _mock_clipboard_succesvol(page: Page):
    page.evaluate("navigator.clipboard = { writeText: (t) => Promise.resolve() }")


# ---------------------------------------------------------------------------
# RESULTAAT-I-01 — kopieerknop kopieert en toont tijdelijk 'Gekopieerd!'
# ---------------------------------------------------------------------------

def test_kopieerknop_tekst_verandert_naar_gekopieerd(page: Page):
    """Testcode: resultaten_en_kopieren.interactie.01
    Dekt: RESULTAAT-I-01 — na klikken op de kopieerknop verandert de tekst tijdelijk naar 'Gekopieerd!'.

    Bevestigt het knop-mechanisme; verifieert niet apart dat de gekopieerde tekst vrij is
    van markdown-opmaaktekens.
    """
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    _mock_clipboard_succesvol(page)

    knop = page.locator("[data-testid=run-results] [data-testid=kopieer-knop]").first
    knop.click()

    expect(knop).to_have_text("Gekopieerd!")


def test_kopieerknop_tekst_keert_terug_na_2_seconden(page: Page):
    """Testcode: resultaten_en_kopieren.interactie.02
    Dekt: RESULTAAT-I-01 — na 2 seconden keert de knoptekst terug naar de originele tekst.
    """
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    _mock_clipboard_succesvol(page)

    knop = page.locator("[data-testid=run-results] [data-testid=kopieer-knop]").first
    originele_tekst = knop.inner_text()
    knop.click()

    page.wait_for_timeout(2200)
    expect(knop).to_have_text(originele_tekst)
