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
from tests.playwright.mocks import stub_lege_sessies, stub_prompt_response
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# RESULTAAT-I-01 — kopieerknop kopieert en toont tijdelijk 'Gekopieerd!'
# ---------------------------------------------------------------------------

def test_kopieerknop_tekst_verandert_naar_gekopieerd(app: PromptPage):
    """Testcode: resultaten_en_kopieren.interactie.01
    Dekt: RESULTAAT-I-01 — na klikken op de kopieerknop verandert de tekst tijdelijk naar 'Gekopieerd!'.

    Bevestigt het knop-mechanisme; verifieert niet apart dat de gekopieerde tekst vrij is
    van markdown-opmaaktekens.
    """
    stub_prompt_response(app.page, runs=[{"run_nummer": 1, "temperature": 0.8, "response": "dit is de uitvoer", "log_status": "ok"}])
    app.vul_verplichte_velden()
    app.verstuur()
    app.mock_clipboard_succesvol()

    knop = app.eerste_kopieer_knop()
    knop.click()

    expect(knop).to_have_text("Gekopieerd!")


def test_kopieerknop_tekst_keert_terug_na_2_seconden(app: PromptPage):
    """Testcode: resultaten_en_kopieren.interactie.02
    Dekt: RESULTAAT-I-01 — na 2 seconden keert de knoptekst terug naar de originele tekst.
    """
    stub_prompt_response(app.page, runs=[{"run_nummer": 1, "temperature": 0.8, "response": "dit is de uitvoer", "log_status": "ok"}])
    app.vul_verplichte_velden()
    app.verstuur()
    app.mock_clipboard_succesvol()

    knop = app.eerste_kopieer_knop()
    originele_tekst = knop.inner_text()
    knop.click()

    expect(knop).to_have_text(originele_tekst, timeout=3000)
