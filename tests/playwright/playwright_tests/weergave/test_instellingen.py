"""
Weergave-tests voor de instellingen-tab (rate limiting).

Bron: documentatie/acceptatiecriteria/instellingen.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
instellingen.weergave.01 — bewust een ander formaat dan de AC-codes (INSTELLINGEN-W-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
from tests.playwright.mocks import stub_lege_sessies, stub_settings
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    stub_settings(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# INSTELLINGEN-W-01 — tab aanwezig en opent paneel
# ---------------------------------------------------------------------------

def test_instellingen_tab_is_aanwezig(app: PromptPage):
    """Testcode: instellingen.weergave.01
    Dekt: INSTELLINGEN-W-01 — er is een 'Instellingen'-tab in de navigatie.
    """
    expect(app.tab_instellingen).to_be_visible()


def test_instellingen_tab_opent_paneel(app: PromptPage):
    """Testcode: instellingen.weergave.02
    Dekt: INSTELLINGEN-W-01 — na klikken op de Instellingen-tab is het instellingenpaneel zichtbaar.
    """
    app.open_tab_instellingen()
    app.instellingen.expect_zichtbaar()


# ---------------------------------------------------------------------------
# INSTELLINGEN-W-02 — RPM-velden per provider
# ---------------------------------------------------------------------------

def test_groq_rpm_veld_is_aanwezig(app: PromptPage):
    """Testcode: instellingen.weergave.03
    Dekt: INSTELLINGEN-W-02 — het Groq RPM-invoerveld is aanwezig in de Instellingen-tab.
    """
    app.open_tab_instellingen()
    app.instellingen.expect_groq_rpm_veld_zichtbaar()


def test_google_rpm_veld_is_aanwezig(app: PromptPage):
    """Testcode: instellingen.weergave.04
    Dekt: INSTELLINGEN-W-02 — het Google RPM-invoerveld is aanwezig in de Instellingen-tab.
    """
    app.open_tab_instellingen()
    app.instellingen.expect_google_rpm_veld_zichtbaar()


def test_ollama_rpm_veld_is_niet_aanwezig(app: PromptPage):
    """Testcode: instellingen.weergave.05
    Dekt: INSTELLINGEN-W-02 — er is geen Ollama RPM-veld in de Instellingen-tab.
    """
    app.open_tab_instellingen()
    app.instellingen.expect_ollama_rpm_veld_niet_aanwezig()


# ---------------------------------------------------------------------------
# INSTELLINGEN-W-03 — velden tonen de opgehaalde waarde
# ---------------------------------------------------------------------------

def test_groq_rpm_toont_geladen_waarde(app: PromptPage):
    """Testcode: instellingen.weergave.06
    Dekt: INSTELLINGEN-W-03 — het Groq RPM-veld toont de waarde die via GET /api/settings is opgehaald.
    """
    app.open_tab_instellingen()
    app.instellingen.expect_groq_rpm_waarde("30")


def test_google_rpm_toont_geladen_waarde(app: PromptPage):
    """Testcode: instellingen.weergave.07
    Dekt: INSTELLINGEN-W-03 — het Google RPM-veld toont de waarde die via GET /api/settings is opgehaald.
    """
    app.open_tab_instellingen()
    app.instellingen.expect_google_rpm_waarde("15")
