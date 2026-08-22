"""
Weergave-tests voor runs en temperature.

Bron: documentatie/acceptatiecriteria/runs-en-temperature.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
runs_en_temperature.weergave.01 — bewust een ander formaat dan de AC-codes (RUNS-W-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

SESSIONS_ROUTE = "**/api/sessions"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))
    page.goto(BASE_URL)


# ---------------------------------------------------------------------------
# RUNS-W-01 — invoerveld 'Aantal runs'
# ---------------------------------------------------------------------------

def test_runs_invoerveld_is_zichtbaar(page: Page):
    """Testcode: runs_en_temperature.weergave.01
    Dekt: RUNS-W-01 — de UI toont een invoerveld voor 'Aantal runs'.
    """
    expect(page.locator("[data-testid=runs-input]")).to_be_visible()


def test_runs_standaardwaarde_is_1(page: Page):
    """Testcode: runs_en_temperature.weergave.02
    Dekt: RUNS-W-01 — het invoerveld 'Aantal runs' heeft als standaardwaarde 1.
    """
    waarde = page.locator("[data-testid=runs-input]").input_value()
    assert waarde == "1", f"Standaard runs is niet 1: {waarde!r}"


# ---------------------------------------------------------------------------
# RUNS-W-02 — keuzeschakelaar temperature-modus
# ---------------------------------------------------------------------------

def test_temperature_modus_schakelaar_is_zichtbaar(page: Page):
    """Testcode: runs_en_temperature.weergave.03
    Dekt: RUNS-W-02 — de UI toont een keuzeschakelaar voor de temperature-modus.
    """
    expect(page.locator("[data-testid=temperature-modus]")).to_be_visible()


def test_temperature_modus_heeft_optie_alle(page: Page):
    """Testcode: runs_en_temperature.weergave.04
    Dekt: RUNS-W-02 — de schakelaar heeft een optie voor 'één temperature voor alle runs'.
    """
    expect(page.locator("[data-testid=temperature-modus-alle]")).to_be_visible()


def test_temperature_modus_heeft_optie_per_run(page: Page):
    """Testcode: runs_en_temperature.weergave.05
    Dekt: RUNS-W-02 — de schakelaar heeft een optie voor 'één temperature per run'.
    """
    expect(page.locator("[data-testid=temperature-modus-per-run]")).to_be_visible()


# ---------------------------------------------------------------------------
# RUNS-W-03 — temperature vooraf ingevuld met providerdefault
# ---------------------------------------------------------------------------

def test_temperature_invoerveld_is_zichtbaar(page: Page):
    """Testcode: runs_en_temperature.weergave.06
    Dekt: RUNS-W-03 — de UI toont een invoerveld voor de temperature.
    """
    expect(page.locator("[data-testid=temperature-input]")).to_be_visible()


def test_ollama_temperature_standaard_is_0_punt_8(page: Page):
    """Testcode: runs_en_temperature.weergave.07
    Dekt: RUNS-W-03 — bij provider Ollama is de temperature vooraf ingevuld met 0.8.
    """
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde == "0.8", f"Standaard temperature voor Ollama is niet 0.8: {waarde!r}"


def test_groq_temperature_standaard_is_1(page: Page):
    """Testcode: runs_en_temperature.weergave.08
    Dekt: RUNS-W-03 — bij provider Groq is de temperature vooraf ingevuld met 1.
    """
    page.locator("[data-testid=provider-select]").select_option("groq")
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde in ("1", "1.0"), f"Standaard temperature voor Groq is niet 1: {waarde!r}"


# ---------------------------------------------------------------------------
# RUNS-W-04 — verplicht-aanduiding temperature
# ---------------------------------------------------------------------------

def test_temperature_label_heeft_verplicht_aanduiding(page: Page):
    """Testcode: runs_en_temperature.weergave.09
    Dekt: RUNS-W-04 — de UI toont bij het temperature-veld een aanduiding dat het verplicht is (bijv. *).
    """
    label_tekst = page.locator("[data-testid=temperature-label]").inner_text()
    assert "*" in label_tekst or "Verplicht" in label_tekst, (
        f"Geen verplicht-aanduiding gevonden in het temperature-label: {label_tekst!r}"
    )
