"""
Validatie-tests voor sessiebeheer.

Bron: documentatie/acceptatiecriteria/sessiebeheer.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
sessiebeheer.validatie.01 — bewust een ander formaat dan de AC-codes (SESSIE-V-01).
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.mocks import SESSIONS_ROUTE, stub_sessies_met_doorgang
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
# SESSIE-V-01 — lege sessienaam
# ---------------------------------------------------------------------------

def test_lege_sessienaam_toont_validatiemelding(app: PromptPage):
    """Testcode: sessiebeheer.validatie.01
    Dekt: SESSIE-V-01 — opslaan met lege sessienaam toont een validatiemelding; er wordt geen API-call gedaan.
    """
    calls = []
    app.page.route(SESSIONS_ROUTE, lambda route: (
        calls.append(route) or route.abort()
        if route.request.method == "POST"
        else route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')
    ))

    app.vul_verplichte_velden()
    app.sidebar.opslaan()

    app.sidebar.expect_validatie_naam_zichtbaar()
    assert len(calls) == 0, "Er mag geen POST zijn gedaan bij een lege sessienaam"


# ---------------------------------------------------------------------------
# SESSIE-V-02 — bestaande naam: overschrijf-bevestiging
# ---------------------------------------------------------------------------

def test_bestaande_naam_toont_bevestigingsdialoog(app: PromptPage):
    """Testcode: sessiebeheer.validatie.02
    Dekt: SESSIE-V-02 — als de sessienaam al bestaat (409), verschijnt een bevestigingsdialoog.
    """
    app.page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=409, content_type="application/json",
        body='{"detail": "Sessie bestaat al"}',
    ) if route.request.method == "POST" else route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))

    _vul_formulier(app, naam="bestaand")
    app.sidebar.opslaan()

    app.sidebar.expect_overschrijf_dialoog_zichtbaar()


def test_annuleren_bij_overschrijven_doet_niets(app: PromptPage):
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

    app.page.route(SESSIONS_ROUTE, handle_route)

    _vul_formulier(app, naam="bestaand")
    app.sidebar.opslaan()

    app.sidebar.expect_overschrijf_dialoog_zichtbaar()
    app.sidebar.annuleer_overschrijven()

    app.sidebar.expect_overschrijf_dialoog_niet_zichtbaar()
    force_calls = [c for c in post_calls if c and '"force": true' in c]
    assert len(force_calls) == 0, "Na annuleren mag geen force-opslaan zijn gedaan"


# ---------------------------------------------------------------------------
# SESSIE-V-03 — opslaan mislukt
# ---------------------------------------------------------------------------

def test_opslaan_mislukt_toont_foutmelding(app: PromptPage):
    """Testcode: sessiebeheer.validatie.04
    Dekt: SESSIE-V-03 — als opslaan mislukt (500), verschijnt een foutmelding.
    """
    app.page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=500, content_type="application/json",
        body='{"detail": "Schrijffout"}',
    ) if route.request.method == "POST" else route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))

    _vul_formulier(app, naam="test")
    app.sidebar.opslaan()

    app.sidebar.expect_opslaan_fout_zichtbaar()


# ---------------------------------------------------------------------------
# SESSIE-V-04 — laden mislukt
# ---------------------------------------------------------------------------

def test_laden_mislukt_toont_foutmelding(app: PromptPage):
    """Testcode: sessiebeheer.validatie.05
    Dekt: SESSIE-V-04 — als laden mislukt (500), verschijnt een foutmelding.
    """
    stub_sessies_met_doorgang(app.page, ["kapot"])
    app.page.route("**/api/sessions/kapot", lambda route: route.fulfill(
        status=500, content_type="application/json",
        body='{"detail": "Ongeldig JSON"}',
    ))
    app.reload()

    app.sidebar.selecteer_via_lijst("kapot")

    app.sidebar.expect_laadfout_zichtbaar()
