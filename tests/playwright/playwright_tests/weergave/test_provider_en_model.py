"""
Weergave-tests voor provider- en modelkeuze.

Bron: documentatie/acceptatiecriteria/provider-en-model.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
provider_en_model.weergave.01 — bewust een ander formaat dan de AC-codes (PROVIDER-W-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
from tests.playwright.mocks import GROQ_MODEL_DEFAULT, GROQ_MODELS_NIEUW, stub_lege_sessies, stub_settings
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    stub_settings(page, groq_model=GROQ_MODEL_DEFAULT, groq_models_beschikbaar=GROQ_MODELS_NIEUW)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# PROVIDER-W-01 — providerdropdown
# ---------------------------------------------------------------------------

def test_provider_dropdown_is_zichtbaar(app: PromptPage):
    """Testcode: provider_en_model.weergave.01
    Dekt: PROVIDER-W-01 — de UI toont een dropdown om de provider te selecteren.
    """
    expect(app.provider_select).to_be_visible()


def test_dropdown_heeft_ollama_optie(app: PromptPage):
    """Testcode: provider_en_model.weergave.02
    Dekt: PROVIDER-W-01 — de dropdown bevat de optie 'Ollama'.
    """
    opties = app.expect_provider_opties()
    assert any("Ollama" in o or "ollama" in o for o in opties), f"'Ollama' ontbreekt in opties: {opties}"


def test_dropdown_heeft_groq_optie(app: PromptPage):
    """Testcode: provider_en_model.weergave.03
    Dekt: PROVIDER-W-01 — de dropdown bevat de optie 'Groq'.
    """
    opties = app.expect_provider_opties()
    assert any("Groq" in o or "groq" in o for o in opties), f"'Groq' ontbreekt in opties: {opties}"


def test_standaard_provider_is_ollama(app: PromptPage):
    """Testcode: provider_en_model.weergave.04
    Dekt: PROVIDER-W-01 — de standaardwaarde van de dropdown is 'Ollama'.
    """
    app.expect_provider_waarde("ollama")


# ---------------------------------------------------------------------------
# PROVIDER-W-02 — modeldropdown alleen bij Groq
# ---------------------------------------------------------------------------

def test_model_dropdown_niet_zichtbaar_bij_ollama(app: PromptPage):
    """Testcode: provider_en_model.weergave.05
    Dekt: PROVIDER-W-02 — de modeldropdown is niet zichtbaar bij de standaardprovider Ollama.
    """
    app.expect_groq_model_niet_zichtbaar()


def test_model_dropdown_zichtbaar_bij_groq(app: PromptPage):
    """Testcode: provider_en_model.weergave.06
    Dekt: PROVIDER-W-02 — de modeldropdown is zichtbaar wanneer provider Groq is geselecteerd.
    """
    app.kies_provider("groq")
    app.expect_groq_model_zichtbaar()


def test_model_dropdown_verdwijnt_bij_terug_naar_ollama(app: PromptPage):
    """Testcode: provider_en_model.weergave.07
    Dekt: PROVIDER-W-02 — de modeldropdown verdwijnt weer als de gebruiker teruggaat naar Ollama.
    """
    app.kies_provider("groq")
    app.kies_provider("ollama")
    app.expect_groq_model_niet_zichtbaar()


# ---------------------------------------------------------------------------
# PROVIDER-W-03 — inhoud en standaardwaarde van de modeldropdown
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model", GROQ_MODELS_NIEUW)
def test_dropdown_bevat_nieuw_model(app: PromptPage, model):
    """Testcode: provider_en_model.weergave.08
    Dekt: PROVIDER-W-03 — de dropdown bevat elk van de vier modellen als optie.
    """
    app.kies_provider("groq")
    waarden = app.expect_groq_model_opties()
    assert model in waarden, f"Model {model!r} ontbreekt in dropdown-opties: {waarden}"


def test_dropdown_bevat_env_default_model(app: PromptPage):
    """Testcode: provider_en_model.weergave.09
    Dekt: PROVIDER-W-03 — de dropdown bevat het model dat is ingesteld via GROQ_MODEL.
    """
    app.kies_provider("groq")
    waarden = app.expect_groq_model_opties()
    assert GROQ_MODEL_DEFAULT in waarden, f"Env-default ontbreekt in dropdown-opties: {waarden}"


def test_dropdown_geen_duplicaat_als_env_model_matcht_nieuw_model(app: PromptPage):
    """Testcode: provider_en_model.weergave.10
    Dekt: PROVIDER-W-03 — als GROQ_MODEL overeenkomt met een van de vier modellen, verschijnt deze niet dubbel.
    """
    stub_settings(app.page, groq_model="qwen3-32b")
    app.reload()
    app.kies_provider("groq")

    waarden = app.expect_groq_model_opties()
    aantal = waarden.count("qwen3-32b")
    assert aantal == 1, f"Verwacht 'qwen3-32b' precies 1x in de lijst, kreeg {aantal}x: {waarden}"


def test_dropdown_default_is_groq_model_env_waarde(app: PromptPage):
    """Testcode: provider_en_model.weergave.11
    Dekt: PROVIDER-W-03 — bij het laden van de pagina staat de dropdown standaard op de GROQ_MODEL-waarde.
    """
    app.kies_provider("groq")
    app.expect_groq_model_waarde(GROQ_MODEL_DEFAULT)
