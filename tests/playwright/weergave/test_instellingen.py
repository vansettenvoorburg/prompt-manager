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

SESSIONS_ROUTE = "**/api/sessions"
SETTINGS_ROUTE = "**/api/settings"

_STUB_SETTINGS = '{"groq_rpm": 30, "google_rpm": 15}'


def _stub_settings(route):
    if route.request.method == "GET":
        route.fulfill(status=200, content_type="application/json", body=_STUB_SETTINGS)
    else:
        route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))
    page.route(SETTINGS_ROUTE, _stub_settings)
    page.goto(BASE_URL)


# ---------------------------------------------------------------------------
# INSTELLINGEN-W-01 — tab aanwezig en opent paneel
# ---------------------------------------------------------------------------

def test_instellingen_tab_is_aanwezig(page: Page):
    """Testcode: instellingen.weergave.01
    Dekt: INSTELLINGEN-W-01 — er is een 'Instellingen'-tab in de navigatie.
    """
    expect(page.locator("[data-testid=tab-instellingen]")).to_be_visible()


def test_instellingen_tab_opent_paneel(page: Page):
    """Testcode: instellingen.weergave.02
    Dekt: INSTELLINGEN-W-01 — na klikken op de Instellingen-tab is het instellingenpaneel zichtbaar.
    """
    page.locator("[data-testid=tab-instellingen]").click()
    expect(page.locator("[data-testid=instellingen-paneel]")).to_be_visible()


# ---------------------------------------------------------------------------
# INSTELLINGEN-W-02 — RPM-velden per provider
# ---------------------------------------------------------------------------

def test_groq_rpm_veld_is_aanwezig(page: Page):
    """Testcode: instellingen.weergave.03
    Dekt: INSTELLINGEN-W-02 — het Groq RPM-invoerveld is aanwezig in de Instellingen-tab.
    """
    page.locator("[data-testid=tab-instellingen]").click()
    expect(page.locator("[data-testid=groq-rpm-input]")).to_be_visible()


def test_google_rpm_veld_is_aanwezig(page: Page):
    """Testcode: instellingen.weergave.04
    Dekt: INSTELLINGEN-W-02 — het Google RPM-invoerveld is aanwezig in de Instellingen-tab.
    """
    page.locator("[data-testid=tab-instellingen]").click()
    expect(page.locator("[data-testid=google-rpm-input]")).to_be_visible()


def test_ollama_rpm_veld_is_niet_aanwezig(page: Page):
    """Testcode: instellingen.weergave.05
    Dekt: INSTELLINGEN-W-02 — er is geen Ollama RPM-veld in de Instellingen-tab.
    """
    page.locator("[data-testid=tab-instellingen]").click()
    expect(page.locator("[data-testid=ollama-rpm-input]")).not_to_be_attached()


# ---------------------------------------------------------------------------
# INSTELLINGEN-W-03 — velden tonen de opgehaalde waarde
# ---------------------------------------------------------------------------

def test_groq_rpm_toont_geladen_waarde(page: Page):
    """Testcode: instellingen.weergave.06
    Dekt: INSTELLINGEN-W-03 — het Groq RPM-veld toont de waarde die via GET /api/settings is opgehaald.
    """
    page.locator("[data-testid=tab-instellingen]").click()
    waarde = page.locator("[data-testid=groq-rpm-input]").input_value()
    assert waarde == "30", f"Verwacht '30' als Groq RPM, maar kreeg {waarde!r}"


def test_google_rpm_toont_geladen_waarde(page: Page):
    """Testcode: instellingen.weergave.07
    Dekt: INSTELLINGEN-W-03 — het Google RPM-veld toont de waarde die via GET /api/settings is opgehaald.
    """
    page.locator("[data-testid=tab-instellingen]").click()
    waarde = page.locator("[data-testid=google-rpm-input]").input_value()
    assert waarde == "15", f"Verwacht '15' als Google RPM, maar kreeg {waarde!r}"
