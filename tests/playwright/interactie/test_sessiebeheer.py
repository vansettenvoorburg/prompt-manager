"""
Interactie-tests voor sessiebeheer.

Bron: documentatie/acceptatiecriteria/sessiebeheer.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
sessiebeheer.interactie.01 — bewust een ander formaat dan de AC-codes (SESSIE-I-01).
"""
import json
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


def _vul_formulier(page: Page, naam: str = "mijn-sessie"):
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")
    page.locator("[name=session-name]").fill(naam)


# ---------------------------------------------------------------------------
# SESSIE-I-01 — bevestiging na opslaan
# ---------------------------------------------------------------------------

def test_opslaan_toont_bevestiging(page: Page):
    """Testcode: sessiebeheer.interactie.01
    Dekt: SESSIE-I-01 — na opslaan verschijnt een bevestiging met de naam van de sessie.
    """
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"status": "ok"}',
    ))
    _vul_formulier(page, naam="mijn-sessie")
    page.get_by_role("button", name="Opslaan").click()

    bevestiging = page.locator("[data-testid=save-confirmation]")
    expect(bevestiging).to_be_visible()
    expect(bevestiging).to_contain_text("mijn-sessie")


# ---------------------------------------------------------------------------
# SESSIE-I-02 — sessie selecteren herstelt formulier
# ---------------------------------------------------------------------------

def test_sessie_selecteren_herstelt_formulier(page: Page):
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

    page.unroute(SESSIONS_ROUTE)
    page.route("**/api/sessions", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"sessions": ["mijn-sessie"]}',
    ) if not route.request.url.endswith("/mijn-sessie") else route.continue_())
    page.route("**/api/sessions/mijn-sessie", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps(sessie_data),
    ))
    page.reload()

    page.locator("[data-testid=sessions-list]").get_by_text("mijn-sessie").click()

    expect(page.locator("[name=rol]")).to_have_value("senior developer")
    expect(page.locator("[name=taak]")).to_have_value("een API ontwerpen")
    expect(page.locator("[name=doel]")).to_have_value("data op te slaan")
