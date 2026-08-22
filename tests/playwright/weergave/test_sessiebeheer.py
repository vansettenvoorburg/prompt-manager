"""
Weergave-tests voor sessiebeheer.

Bron: documentatie/acceptatiecriteria/sessiebeheer.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
sessiebeheer.weergave.01 — bewust een ander formaat dan de AC-codes (SESSIE-W-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

SESSIONS_ROUTE = "**/api/sessions"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    def handle_sessions_lijst(route):
        is_lijst = route.request.method == "GET" and "/api/sessions/" not in route.request.url
        if is_lijst:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')
        else:
            route.continue_()

    page.route(SESSIONS_ROUTE, handle_sessions_lijst)
    page.goto(BASE_URL)


# ---------------------------------------------------------------------------
# SESSIE-W-01 — invoerveld sessienaam en opslaan-knop
# ---------------------------------------------------------------------------

def test_sessienaam_invoerveld_is_zichtbaar(page: Page):
    """Testcode: sessiebeheer.weergave.01
    Dekt: SESSIE-W-01 — het invoerveld voor de sessienaam is zichtbaar.
    """
    expect(page.locator("[name=session-name]")).to_be_visible()


def test_opslaan_knop_is_zichtbaar(page: Page):
    """Testcode: sessiebeheer.weergave.02
    Dekt: SESSIE-W-01 — de opslaan-knop is zichtbaar.
    """
    expect(page.get_by_role("button", name="Opslaan")).to_be_visible()


# ---------------------------------------------------------------------------
# SESSIE-W-02 — sessieslijst, inclusief lege-staat
# ---------------------------------------------------------------------------

def test_sessieslijst_is_zichtbaar(page: Page):
    """Testcode: sessiebeheer.weergave.03
    Dekt: SESSIE-W-02 — de sessieslijst is zichtbaar op de pagina.
    """
    expect(page.locator("[data-testid=sessions-list]")).to_be_visible()


def test_lege_sessieslijst_toont_melding(page: Page):
    """Testcode: sessiebeheer.weergave.04
    Dekt: SESSIE-W-02 — als er geen sessies zijn, is er een lege-staat melding zichtbaar.
    """
    expect(page.locator("[data-testid=sessions-empty]")).to_be_visible()


def test_sessie_in_lijst_is_zichtbaar_na_ophalen(page: Page):
    """Testcode: sessiebeheer.weergave.05
    Dekt: SESSIE-W-02 — opgeslagen sessies zijn zichtbaar als klikbare items in de lijst.
    """
    page.unroute(SESSIONS_ROUTE)
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"sessions": ["mijn-sessie"]}',
    ))
    page.reload()

    expect(page.locator("[data-testid=sessions-list]")).to_contain_text("mijn-sessie")
