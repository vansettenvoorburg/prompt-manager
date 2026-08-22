"""
Interactie-tests voor de instellingen-tab (rate limiting).

Bron: documentatie/acceptatiecriteria/instellingen.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
instellingen.interactie.01 — bewust een ander formaat dan de AC-codes (INSTELLINGEN-I-01).
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
# INSTELLINGEN-I-01 — opslaan verstuurt PUT met de ingevoerde waarden
# ---------------------------------------------------------------------------

def test_opslaan_verstuurt_put_naar_api_settings(page: Page):
    """Testcode: instellingen.interactie.01
    Dekt: INSTELLINGEN-I-01 — bij het klikken op 'Instellingen opslaan' wordt PUT /api/settings verstuurd.
    """
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
    expect(page.locator("[data-testid=instellingen-bevestiging]")).to_be_visible()

    assert len(verzoeken) >= 1, "PUT /api/settings werd niet verstuurd"


def test_opslaan_stuurt_groq_rpm_waarde_mee(page: Page):
    """Testcode: instellingen.interactie.02
    Dekt: INSTELLINGEN-I-01 — de ingevoerde Groq RPM-waarde wordt meegestuurd bij het opslaan.
    """
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
    expect(page.locator("[data-testid=instellingen-bevestiging]")).to_be_visible()

    assert vastgelegd.get("groq_rpm") == 20, (
        f"Verwacht groq_rpm=20, maar verzoek bevat: {vastgelegd}"
    )


def test_opslaan_stuurt_google_rpm_waarde_mee(page: Page):
    """Testcode: instellingen.interactie.03
    Dekt: INSTELLINGEN-I-01 — de ingevoerde Google RPM-waarde wordt meegestuurd bij het opslaan.
    """
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
    expect(page.locator("[data-testid=instellingen-bevestiging]")).to_be_visible()

    assert vastgelegd.get("google_rpm") == 10, (
        f"Verwacht google_rpm=10, maar verzoek bevat: {vastgelegd}"
    )
