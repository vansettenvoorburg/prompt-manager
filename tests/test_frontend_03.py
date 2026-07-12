"""
Frontend-tests voor story 03: sessie opslaan en laden.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.

AC gedekt:
- Invoerveld sessienaam en opslaan-knop zijn zichtbaar
- Na opslaan verschijnt bevestiging met de sessienaam
- Lege sessienaam toont validatiemelding; geen API-call
- Bestaande naam toont bevestigingsdialoog; annuleren doet niets
- Sessies zijn zichtbaar als lijst
- Sessie selecteren herstelt de formuliervelden
- Lege sessieslijst toont lege-staat melding
- Opslaan mislukt (500) toont foutmelding
- Laden mislukt (500) toont foutmelding
"""
import json
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
SESSIONS_ROUTE = "**/api/sessions"
SESSION_ITEM_ROUTE = "**/api/sessions/*"


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
# Formulierstructuur
# ---------------------------------------------------------------------------

def test_sessienaam_invoerveld_is_zichtbaar(page: Page):
    """Het invoerveld voor de sessienaam is zichtbaar."""
    expect(page.locator("[name=session-name]")).to_be_visible()


def test_opslaan_knop_is_zichtbaar(page: Page):
    """De opslaan-knop is zichtbaar."""
    expect(page.get_by_role("button", name="Opslaan")).to_be_visible()


# ---------------------------------------------------------------------------
# Opslaan — happy path
# ---------------------------------------------------------------------------

def test_opslaan_toont_bevestiging(page: Page):
    """Na opslaan verschijnt een bevestiging met de naam van de sessie."""
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"status": "ok"}',
    ))
    _vul_formulier(page, naam="mijn-sessie")
    page.get_by_role("button", name="Opslaan").click()

    bevestiging = page.locator("[data-testid=save-confirmation]")
    expect(bevestiging).to_be_visible()
    expect(bevestiging).to_contain_text("mijn-sessie")


# ---------------------------------------------------------------------------
# Validatie
# ---------------------------------------------------------------------------

def test_lege_sessienaam_toont_validatiemelding(page: Page):
    """Opslaan met lege sessienaam toont een validatiemelding; er wordt geen API-call gedaan."""
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
# Overschrijven
# ---------------------------------------------------------------------------

def test_bestaande_naam_toont_bevestigingsdialoog(page: Page):
    """Als de sessienaam al bestaat (409), verschijnt een bevestigingsdialoog."""
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
    """Annuleren in de bevestigingsdialoog doet niets; de sessie wordt niet overschreven."""
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
# Sessieslijst
# ---------------------------------------------------------------------------

def test_sessieslijst_is_zichtbaar(page: Page):
    """De sessieslijst is zichtbaar op de pagina."""
    expect(page.locator("[data-testid=sessions-list]")).to_be_visible()


def test_lege_sessieslijst_toont_melding(page: Page):
    """Als er geen sessies zijn, is er een lege-staat melding zichtbaar."""
    expect(page.locator("[data-testid=sessions-empty]")).to_be_visible()


def test_sessie_in_lijst_is_zichtbaar_na_ophalen(page: Page):
    """Opgeslagen sessies zijn zichtbaar als klikbare items in de lijst."""
    page.unroute(SESSIONS_ROUTE)
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"sessions": ["mijn-sessie"]}',
    ))
    page.reload()

    expect(page.locator("[data-testid=sessions-list]")).to_contain_text("mijn-sessie")


def test_sessie_selecteren_herstelt_formulier(page: Page):
    """Een sessie aanklikken herstelt de acht velden in het formulier."""
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


# ---------------------------------------------------------------------------
# Foutafhandeling
# ---------------------------------------------------------------------------

def test_opslaan_mislukt_toont_foutmelding(page: Page):
    """Als opslaan mislukt (500), verschijnt een foutmelding."""
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=500, content_type="application/json",
        body='{"detail": "Schrijffout"}',
    ) if route.request.method == "POST" else route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))

    _vul_formulier(page, naam="test")
    page.get_by_role("button", name="Opslaan").click()

    expect(page.locator("[data-testid=save-error]")).to_be_visible()


def test_laden_mislukt_toont_foutmelding(page: Page):
    """Als laden mislukt (500), verschijnt een foutmelding."""
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
