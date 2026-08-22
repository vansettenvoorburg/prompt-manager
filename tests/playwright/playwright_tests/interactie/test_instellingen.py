"""
Interactie-tests voor de instellingen-tab (rate limiting).

Bron: documentatie/acceptatiecriteria/instellingen.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
instellingen.interactie.01 — bewust een ander formaat dan de AC-codes (INSTELLINGEN-I-01).
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.mocks import SETTINGS_ROUTE, stub_lege_sessies, stub_settings
from tests.playwright.pages.prompt_page import PromptPage

_STUB_SETTINGS = '{"groq_rpm": 30, "google_rpm": 15}'


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    stub_settings(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# INSTELLINGEN-I-01 — opslaan verstuurt PUT met de ingevoerde waarden
# ---------------------------------------------------------------------------

def test_opslaan_verstuurt_put_naar_api_settings(app: PromptPage):
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

    app.page.route(SETTINGS_ROUTE, vang_op)
    app.reload()
    app.open_tab_instellingen()
    app.instellingen.opslaan()
    app.instellingen.expect_bevestiging_zichtbaar()

    assert len(verzoeken) >= 1, "PUT /api/settings werd niet verstuurd"


def test_opslaan_stuurt_groq_rpm_waarde_mee(app: PromptPage):
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

    app.page.route(SETTINGS_ROUTE, vang_op)
    app.reload()
    app.open_tab_instellingen()
    app.instellingen.fill_groq_rpm("20")
    app.instellingen.opslaan()
    app.instellingen.expect_bevestiging_zichtbaar()

    assert vastgelegd.get("groq_rpm") == 20, (
        f"Verwacht groq_rpm=20, maar verzoek bevat: {vastgelegd}"
    )


def test_opslaan_stuurt_google_rpm_waarde_mee(app: PromptPage):
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

    app.page.route(SETTINGS_ROUTE, vang_op)
    app.reload()
    app.open_tab_instellingen()
    app.instellingen.fill_google_rpm("10")
    app.instellingen.opslaan()
    app.instellingen.expect_bevestiging_zichtbaar()

    assert vastgelegd.get("google_rpm") == 10, (
        f"Verwacht google_rpm=10, maar verzoek bevat: {vastgelegd}"
    )
