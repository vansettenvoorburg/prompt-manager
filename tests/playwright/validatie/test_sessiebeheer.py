"""
Validatie-tests voor sessiebeheer.

Bron: documentatie/acceptatiecriteria/sessiebeheer.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
sessiebeheer.validatie.01 — bewust een ander formaat dan de AC-codes (SESSIE-V-01).
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


def _vul_formulier(page: Page, naam: str = "mijn-sessie"):
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")
    page.locator("[name=session-name]").fill(naam)


# ---------------------------------------------------------------------------
# SESSIE-V-01 — lege sessienaam
# ---------------------------------------------------------------------------

def test_lege_sessienaam_toont_validatiemelding(page: Page):
    """Testcode: sessiebeheer.validatie.01
    Dekt: SESSIE-V-01 — opslaan met lege sessienaam toont een validatiemelding; er wordt geen API-call gedaan.
    """
    calls = []
    page.route(SESSIONS_ROUTE, lambda route: (
        calls.append(route) or route.abort()
        if route.request.method == "POST"
        else route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')
    ))

    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")
    page.get_by_role("button", name="Opslaan").click()

    expect(page.locator("[data-testid=validation-session-name]")).to_be_visible()
    assert len(calls) == 0, "Er mag geen POST zijn gedaan bij een lege sessienaam"


# ---------------------------------------------------------------------------
# SESSIE-V-02 — bestaande naam: overschrijf-bevestiging
# ---------------------------------------------------------------------------

def test_bestaande_naam_toont_bevestigingsdialoog(page: Page):
    """Testcode: sessiebeheer.validatie.02
    Dekt: SESSIE-V-02 — als de sessienaam al bestaat (409), verschijnt een bevestigingsdialoog.
    """
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=409, content_type="application/json",
        body='{"detail": "Sessie bestaat al"}',
    ) if route.request.method == "POST" else route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))

    _vul_formulier(page, naam="bestaand")
    page.get_by_role("button", name="Opslaan").click()

    expect(page.locator("[data-testid=overwrite-dialog]")).to_be_visible()


def test_annuleren_bij_overschrijven_doet_niets(page: Page):
    """Testcode: sessiebeheer.validatie.03
    Dekt: SESSIE-V-02 — annuleren in de bevestigingsdialoog doet niets; de sessie wordt niet overschreven.
    """
    post_calls = []

    def handle_route(route):
        if route.request.method == "POST":
            post_calls.append(route.request.post_data)
            route.fulfill(
                status=409, content_type="application/json",
                body='{"detail": "Sessie bestaat al"}',
            )
        else:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')

    page.route(SESSIONS_ROUTE, handle_route)

    _vul_formulier(page, naam="bestaand")
    page.get_by_role("button", name="Opslaan").click()

    expect(page.locator("[data-testid=overwrite-dialog]")).to_be_visible()
    page.get_by_role("button", name="Annuleren").click()

    expect(page.locator("[data-testid=overwrite-dialog]")).not_to_be_visible()
    force_calls = [c for c in post_calls if c and '"force": true' in c]
    assert len(force_calls) == 0, "Na annuleren mag geen force-opslaan zijn gedaan"


# ---------------------------------------------------------------------------
# SESSIE-V-03 — opslaan mislukt
# ---------------------------------------------------------------------------

def test_opslaan_mislukt_toont_foutmelding(page: Page):
    """Testcode: sessiebeheer.validatie.04
    Dekt: SESSIE-V-03 — als opslaan mislukt (500), verschijnt een foutmelding.
    """
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=500, content_type="application/json",
        body='{"detail": "Schrijffout"}',
    ) if route.request.method == "POST" else route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))

    _vul_formulier(page, naam="test")
    page.get_by_role("button", name="Opslaan").click()

    expect(page.locator("[data-testid=save-error]")).to_be_visible()


# ---------------------------------------------------------------------------
# SESSIE-V-04 — laden mislukt
# ---------------------------------------------------------------------------

def test_laden_mislukt_toont_foutmelding(page: Page):
    """Testcode: sessiebeheer.validatie.05
    Dekt: SESSIE-V-04 — als laden mislukt (500), verschijnt een foutmelding.
    """
    page.unroute(SESSIONS_ROUTE)
    page.route("**/api/sessions", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"sessions": ["kapot"]}',
    ) if not route.request.url.endswith("/kapot") else route.continue_())
    page.route("**/api/sessions/kapot", lambda route: route.fulfill(
        status=500, content_type="application/json",
        body='{"detail": "Ongeldig JSON"}',
    ))
    page.reload()

    page.locator("[data-testid=sessions-list]").get_by_text("kapot").click()

    expect(page.locator("[data-testid=load-error]")).to_be_visible()
