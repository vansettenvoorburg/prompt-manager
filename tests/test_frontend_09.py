"""
Frontend-tests voor story 09: Rate limiting — API-quota's respecteren.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.

AC gedekt:
- Er is een 'Instellingen'-tab in de navigatie
- Na klikken op de Instellingen-tab is het instellingenpaneel zichtbaar
- Het Groq RPM-invoerveld is aanwezig in de Instellingen-tab
- Het Google RPM-invoerveld is aanwezig in de Instellingen-tab
- Er is geen Ollama RPM-veld in de Instellingen-tab
- Het Groq RPM-veld toont de waarde uit GET /api/settings
- Het Google RPM-veld toont de waarde uit GET /api/settings
- Bij het opslaan wordt PUT /api/settings verstuurd
- De ingevoerde Groq RPM-waarde wordt meegestuurd bij het opslaan
- De ingevoerde Google RPM-waarde wordt meegestuurd bij het opslaan
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
SESSIONS_ROUTE = "**/api/sessions"
SETTINGS_ROUTE = "**/api/settings"

_STUB_SETTINGS = '{"groq_rpm": 30, "google_rpm": 15}'


def _stub_settings(route):
    if route.request.method == "GET":
        route.fulfill(
            status=200,
            content_type="application/json",
            body=_STUB_SETTINGS,
        )
    else:
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"status": "ok"}',
        )


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))
    page.route(SETTINGS_ROUTE, _stub_settings)
    page.goto(BASE_URL)


# ---------------------------------------------------------------------------
# UI structuur — Instellingen tab
# ---------------------------------------------------------------------------

def test_instellingen_tab_is_aanwezig(page: Page):
    """Er is een 'Instellingen'-tab in de navigatie."""
    expect(page.locator("[data-testid=tab-instellingen]")).to_be_visible()


def test_instellingen_tab_opent_paneel(page: Page):
    """Na klikken op de Instellingen-tab is het instellingenpaneel zichtbaar."""
    page.locator("[data-testid=tab-instellingen]").click()
    expect(page.locator("[data-testid=instellingen-paneel]")).to_be_visible()


def test_groq_rpm_veld_is_aanwezig(page: Page):
    """Het Groq RPM-invoerveld is aanwezig in de Instellingen-tab."""
    page.locator("[data-testid=tab-instellingen]").click()
    expect(page.locator("[data-testid=groq-rpm-input]")).to_be_visible()


def test_google_rpm_veld_is_aanwezig(page: Page):
    """Het Google RPM-invoerveld is aanwezig in de Instellingen-tab."""
    page.locator("[data-testid=tab-instellingen]").click()
    expect(page.locator("[data-testid=google-rpm-input]")).to_be_visible()


def test_ollama_rpm_veld_is_niet_aanwezig(page: Page):
    """Er is geen Ollama RPM-veld in de Instellingen-tab."""
    page.locator("[data-testid=tab-instellingen]").click()
    expect(page.locator("[data-testid=ollama-rpm-input]")).not_to_be_attached()


# ---------------------------------------------------------------------------
# Waarden laden uit GET /api/settings
# ---------------------------------------------------------------------------

def test_groq_rpm_toont_geladen_waarde(page: Page):
    """Het Groq RPM-veld toont de waarde die via GET /api/settings is opgehaald."""
    page.locator("[data-testid=tab-instellingen]").click()
    waarde = page.locator("[data-testid=groq-rpm-input]").input_value()
    assert waarde == "30", f"Verwacht '30' als Groq RPM, maar kreeg {waarde!r}"


def test_google_rpm_toont_geladen_waarde(page: Page):
    """Het Google RPM-veld toont de waarde die via GET /api/settings is opgehaald."""
    page.locator("[data-testid=tab-instellingen]").click()
    waarde = page.locator("[data-testid=google-rpm-input]").input_value()
    assert waarde == "15", f"Verwacht '15' als Google RPM, maar kreeg {waarde!r}"


# ---------------------------------------------------------------------------
# Waarden opslaan via PUT /api/settings
# ---------------------------------------------------------------------------

def test_opslaan_verstuurt_put_naar_api_settings(page: Page):
    """Bij het klikken op 'Instellingen opslaan' wordt PUT /api/settings verstuurd."""
    verzoeken = []

    def vang_op(route):
        if route.request.method == "PUT":
            verzoeken.append(route.request)
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body=_STUB_SETTINGS)

    page.route(SETTINGS_ROUTE, vang_op)
    page.reload()
    page.locator("[data-testid=tab-instellingen]").click()
    page.get_by_role("button", name="Instellingen opslaan").click()

    assert len(verzoeken) >= 1, "PUT /api/settings werd niet verstuurd"


def test_opslaan_stuurt_groq_rpm_waarde_mee(page: Page):
    """De ingevoerde Groq RPM-waarde wordt meegestuurd bij het opslaan."""
    vastgelegd: dict = {}

    def vang_op(route):
        if route.request.method == "PUT":
            vastgelegd.update(route.request.post_data_json)
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body=_STUB_SETTINGS)

    page.route(SETTINGS_ROUTE, vang_op)
    page.reload()
    page.locator("[data-testid=tab-instellingen]").click()
    page.locator("[data-testid=groq-rpm-input]").fill("20")
    page.get_by_role("button", name="Instellingen opslaan").click()

    assert vastgelegd.get("groq_rpm") == 20, (
        f"Verwacht groq_rpm=20, maar verzoek bevat: {vastgelegd}"
    )


def test_opslaan_stuurt_google_rpm_waarde_mee(page: Page):
    """De ingevoerde Google RPM-waarde wordt meegestuurd bij het opslaan."""
    vastgelegd: dict = {}

    def vang_op(route):
        if route.request.method == "PUT":
            vastgelegd.update(route.request.post_data_json)
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body=_STUB_SETTINGS)

    page.route(SETTINGS_ROUTE, vang_op)
    page.reload()
    page.locator("[data-testid=tab-instellingen]").click()
    page.locator("[data-testid=google-rpm-input]").fill("10")
    page.get_by_role("button", name="Instellingen opslaan").click()

    assert vastgelegd.get("google_rpm") == 10, (
        f"Verwacht google_rpm=10, maar verzoek bevat: {vastgelegd}"
    )
