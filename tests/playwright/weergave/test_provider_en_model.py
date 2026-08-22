"""
Weergave-tests voor provider- en modelkeuze.

Bron: documentatie/acceptatiecriteria/provider-en-model.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
provider_en_model.weergave.01 — bewust een ander formaat dan de AC-codes (PROVIDER-W-01).
"""
import json
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

SESSIONS_ROUTE = "**/api/sessions"
SETTINGS_ROUTE = "**/api/settings"

GROQ_MODEL_DEFAULT = "llama3-8b-8192"
GROQ_MODELS_NIEUW = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "moonshotai/kimi-k2-instruct",
    "qwen3-32b",
]

_STUB_SETTINGS = json.dumps({
    "groq_rpm": 30,
    "google_rpm": 15,
    "groq_model": GROQ_MODEL_DEFAULT,
})


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


def _kies_groq(page: Page):
    page.locator("[data-testid=provider-select]").select_option("groq")


# ---------------------------------------------------------------------------
# PROVIDER-W-01 — providerdropdown
# ---------------------------------------------------------------------------

def test_provider_dropdown_is_zichtbaar(page: Page):
    """Testcode: provider_en_model.weergave.01
    Dekt: PROVIDER-W-01 — de UI toont een dropdown om de provider te selecteren.
    """
    expect(page.locator("[data-testid=provider-select]")).to_be_visible()


def test_dropdown_heeft_ollama_optie(page: Page):
    """Testcode: provider_en_model.weergave.02
    Dekt: PROVIDER-W-01 — de dropdown bevat de optie 'Ollama'.
    """
    opties = page.locator("[data-testid=provider-select] option").all_text_contents()
    assert any("Ollama" in o or "ollama" in o for o in opties), f"'Ollama' ontbreekt in opties: {opties}"


def test_dropdown_heeft_groq_optie(page: Page):
    """Testcode: provider_en_model.weergave.03
    Dekt: PROVIDER-W-01 — de dropdown bevat de optie 'Groq'.
    """
    opties = page.locator("[data-testid=provider-select] option").all_text_contents()
    assert any("Groq" in o or "groq" in o for o in opties), f"'Groq' ontbreekt in opties: {opties}"


def test_standaard_provider_is_ollama(page: Page):
    """Testcode: provider_en_model.weergave.04
    Dekt: PROVIDER-W-01 — de standaardwaarde van de dropdown is 'Ollama'.
    """
    geselecteerde_waarde = page.locator("[data-testid=provider-select]").input_value()
    assert geselecteerde_waarde.lower() == "ollama", f"Standaard provider is niet ollama: {geselecteerde_waarde!r}"


# ---------------------------------------------------------------------------
# PROVIDER-W-02 — modeldropdown alleen bij Groq
# ---------------------------------------------------------------------------

def test_model_dropdown_niet_zichtbaar_bij_ollama(page: Page):
    """Testcode: provider_en_model.weergave.05
    Dekt: PROVIDER-W-02 — de modeldropdown is niet zichtbaar bij de standaardprovider Ollama.
    """
    expect(page.locator("[data-testid=groq-model-select]")).not_to_be_visible()


def test_model_dropdown_zichtbaar_bij_groq(page: Page):
    """Testcode: provider_en_model.weergave.06
    Dekt: PROVIDER-W-02 — de modeldropdown is zichtbaar wanneer provider Groq is geselecteerd.
    """
    _kies_groq(page)
    expect(page.locator("[data-testid=groq-model-select]")).to_be_visible()


def test_model_dropdown_verdwijnt_bij_terug_naar_ollama(page: Page):
    """Testcode: provider_en_model.weergave.07
    Dekt: PROVIDER-W-02 — de modeldropdown verdwijnt weer als de gebruiker teruggaat naar Ollama.
    """
    _kies_groq(page)
    page.locator("[data-testid=provider-select]").select_option("ollama")
    expect(page.locator("[data-testid=groq-model-select]")).not_to_be_visible()


# ---------------------------------------------------------------------------
# PROVIDER-W-03 — inhoud en standaardwaarde van de modeldropdown
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model", GROQ_MODELS_NIEUW)
def test_dropdown_bevat_nieuw_model(page: Page, model):
    """Testcode: provider_en_model.weergave.08
    Dekt: PROVIDER-W-03 — de dropdown bevat elk van de vier modellen als optie.
    """
    _kies_groq(page)
    waarden = page.locator("[data-testid=groq-model-select] option").evaluate_all(
        "opts => opts.map(o => o.value)"
    )
    assert model in waarden, f"Model {model!r} ontbreekt in dropdown-opties: {waarden}"


def test_dropdown_bevat_env_default_model(page: Page):
    """Testcode: provider_en_model.weergave.09
    Dekt: PROVIDER-W-03 — de dropdown bevat het model dat is ingesteld via GROQ_MODEL.
    """
    _kies_groq(page)
    waarden = page.locator("[data-testid=groq-model-select] option").evaluate_all(
        "opts => opts.map(o => o.value)"
    )
    assert GROQ_MODEL_DEFAULT in waarden, f"Env-default ontbreekt in dropdown-opties: {waarden}"


def test_dropdown_geen_duplicaat_als_env_model_matcht_nieuw_model(page: Page):
    """Testcode: provider_en_model.weergave.10
    Dekt: PROVIDER-W-03 — als GROQ_MODEL overeenkomt met een van de vier modellen, verschijnt deze niet dubbel.
    """
    page.unroute(SETTINGS_ROUTE)
    matchende_settings = json.dumps({"groq_rpm": 30, "google_rpm": 15, "groq_model": "qwen3-32b"})
    page.route(SETTINGS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=matchende_settings,
    ) if route.request.method == "GET" else route.fulfill(
        status=200, content_type="application/json", body='{"status": "ok"}',
    ))
    page.reload()
    _kies_groq(page)

    waarden = page.locator("[data-testid=groq-model-select] option").evaluate_all(
        "opts => opts.map(o => o.value)"
    )
    aantal = waarden.count("qwen3-32b")
    assert aantal == 1, f"Verwacht 'qwen3-32b' precies 1x in de lijst, kreeg {aantal}x: {waarden}"


def test_dropdown_default_is_groq_model_env_waarde(page: Page):
    """Testcode: provider_en_model.weergave.11
    Dekt: PROVIDER-W-03 — bij het laden van de pagina staat de dropdown standaard op de GROQ_MODEL-waarde.
    """
    _kies_groq(page)
    expect(page.locator("[data-testid=groq-model-select]")).to_have_value(GROQ_MODEL_DEFAULT)
