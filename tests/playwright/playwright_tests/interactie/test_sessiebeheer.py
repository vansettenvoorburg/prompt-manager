"""
Interactie-tests voor sessiebeheer.

Bron: documentatie/acceptatiecriteria/sessiebeheer.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
sessiebeheer.interactie.01 — bewust een ander formaat dan de AC-codes (SESSIE-I-01).
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.mocks import SESSIONS_ROUTE, stub_sessie_item, stub_sessies_met_doorgang
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_sessies_met_doorgang(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


def _vul_formulier(app: PromptPage, naam: str = "mijn-sessie") -> None:
    app.vul_verplichte_velden()
    app.sidebar.fill_naam(naam)


# ---------------------------------------------------------------------------
# SESSIE-I-01 — bevestiging na opslaan
# ---------------------------------------------------------------------------

def test_opslaan_toont_bevestiging(app: PromptPage):
    """Testcode: sessiebeheer.interactie.01
    Dekt: SESSIE-I-01 — na opslaan verschijnt een bevestiging met de naam van de sessie.
    """
    app.page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"status": "ok"}',
    ))
    _vul_formulier(app, naam="mijn-sessie")
    app.sidebar.opslaan()

    app.sidebar.expect_bevestiging_zichtbaar(bevat="mijn-sessie")


# ---------------------------------------------------------------------------
# SESSIE-I-02 — sessie selecteren herstelt formulier
# ---------------------------------------------------------------------------

def test_sessie_selecteren_herstelt_formulier(app: PromptPage):
    """Testcode: sessiebeheer.interactie.02
    Dekt: SESSIE-I-02 — een sessie aanklikken herstelt de acht velden in het formulier.
    """
    sessie_data = {
        "name": "mijn-sessie",
        "rol": "senior developer",
        "taak": "een API ontwerpen",
        "doel": "data op te slaan",
        "formaat": "JSON",
        "stijl": "technisch",
        "scope": "",
        "eisen": "",
        "voorbeelden": "",
        "provider": "ollama",
        "model": "llama3.2",
        "created_at": "2026-05-10T12:00:00",
    }
    stub_sessies_met_doorgang(app.page, ["mijn-sessie"])
    stub_sessie_item(app.page, "mijn-sessie", sessie_data)
    app.reload()

    app.sidebar.selecteer_via_lijst("mijn-sessie")

    app.expect_veld_waarde("rol", "senior developer")
    app.expect_veld_waarde("taak", "een API ontwerpen")
    app.expect_veld_waarde("doel", "data op te slaan")
