"""
Weergave-tests voor sessiebeheer.

Bron: documentatie/acceptatiecriteria/sessiebeheer.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
sessiebeheer.weergave.01 — bewust een ander formaat dan de AC-codes (SESSIE-W-01).
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.mocks import stub_sessies_met_doorgang
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_sessies_met_doorgang(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# SESSIE-W-01 — invoerveld sessienaam en opslaan-knop
# ---------------------------------------------------------------------------

def test_sessienaam_invoerveld_is_zichtbaar(app: PromptPage):
    """Testcode: sessiebeheer.weergave.01
    Dekt: SESSIE-W-01 — het invoerveld voor de sessienaam is zichtbaar.
    """
    app.sidebar.expect_naam_invoerveld_zichtbaar()


def test_opslaan_knop_is_zichtbaar(app: PromptPage):
    """Testcode: sessiebeheer.weergave.02
    Dekt: SESSIE-W-01 — de opslaan-knop is zichtbaar.
    """
    app.sidebar.expect_opslaan_knop_zichtbaar()


# ---------------------------------------------------------------------------
# SESSIE-W-02 — sessieslijst, inclusief lege-staat
# ---------------------------------------------------------------------------

def test_sessieslijst_is_zichtbaar(app: PromptPage):
    """Testcode: sessiebeheer.weergave.03
    Dekt: SESSIE-W-02 — de sessieslijst is zichtbaar op de pagina.
    """
    app.sidebar.expect_zichtbaar()


def test_lege_sessieslijst_toont_melding(app: PromptPage):
    """Testcode: sessiebeheer.weergave.04
    Dekt: SESSIE-W-02 — als er geen sessies zijn, is er een lege-staat melding zichtbaar.
    """
    app.sidebar.expect_lege_lijst_melding_zichtbaar()


def test_sessie_in_lijst_is_zichtbaar_na_ophalen(app: PromptPage):
    """Testcode: sessiebeheer.weergave.05
    Dekt: SESSIE-W-02 — opgeslagen sessies zijn zichtbaar als klikbare items in de lijst.
    """
    stub_sessies_met_doorgang(app.page, ["mijn-sessie"])
    app.reload()

    app.sidebar.expect_lijst_bevat("mijn-sessie")
