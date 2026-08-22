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
from tests.playwright.mocks import stub_lege_sessies
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# RUNS-W-01 — invoerveld 'Aantal runs'
# ---------------------------------------------------------------------------

def test_runs_invoerveld_is_zichtbaar(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.01
    Dekt: RUNS-W-01 — de UI toont een invoerveld voor 'Aantal runs'.
    """
    expect(app.runs_input).to_be_visible()


def test_runs_standaardwaarde_is_1(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.02
    Dekt: RUNS-W-01 — het invoerveld 'Aantal runs' heeft als standaardwaarde 1.
    """
    waarde = app.runs_input.input_value()
    assert waarde == "1", f"Standaard runs is niet 1: {waarde!r}"


# ---------------------------------------------------------------------------
# RUNS-W-02 — keuzeschakelaar temperature-modus
# ---------------------------------------------------------------------------

def test_temperature_modus_schakelaar_is_zichtbaar(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.03
    Dekt: RUNS-W-02 — de UI toont een keuzeschakelaar voor de temperature-modus.
    """
    expect(app.temperature_modus).to_be_visible()


def test_temperature_modus_heeft_optie_alle(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.04
    Dekt: RUNS-W-02 — de schakelaar heeft een optie voor 'één temperature voor alle runs'.
    """
    expect(app.temperature_modus_alle).to_be_visible()


def test_temperature_modus_heeft_optie_per_run(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.05
    Dekt: RUNS-W-02 — de schakelaar heeft een optie voor 'één temperature per run'.
    """
    expect(app.temperature_modus_per_run).to_be_visible()


# ---------------------------------------------------------------------------
# RUNS-W-03 — temperature vooraf ingevuld met providerdefault
# ---------------------------------------------------------------------------

def test_temperature_invoerveld_is_zichtbaar(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.06
    Dekt: RUNS-W-03 — de UI toont een invoerveld voor de temperature.
    """
    expect(app.temperature_input).to_be_visible()


def test_ollama_temperature_standaard_is_0_punt_8(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.07
    Dekt: RUNS-W-03 — bij provider Ollama is de temperature vooraf ingevuld met 0.8.
    """
    app.expect_temperature_waarde("0.8")


def test_groq_temperature_standaard_is_1(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.08
    Dekt: RUNS-W-03 — bij provider Groq is de temperature vooraf ingevuld met 1.
    """
    app.kies_provider("groq")
    app.expect_temperature_waarde("1", "1.0")


# ---------------------------------------------------------------------------
# RUNS-W-04 — verplicht-aanduiding temperature
# ---------------------------------------------------------------------------

def test_temperature_label_heeft_verplicht_aanduiding(app: PromptPage):
    """Testcode: runs_en_temperature.weergave.09
    Dekt: RUNS-W-04 — de UI toont bij het temperature-veld een aanduiding dat het verplicht is (bijv. *).
    """
    label_tekst = app.temperature_label.inner_text()
    assert "*" in label_tekst or "Verplicht" in label_tekst, (
        f"Geen verplicht-aanduiding gevonden in het temperature-label: {label_tekst!r}"
    )
