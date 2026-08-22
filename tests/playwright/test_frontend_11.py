"""
Frontend-tests voor story 11: Groq-modelkeuze uitbreiden.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.

Aannames over de UI (niet expliciet vastgelegd in de AC, hier gedocumenteerd
zodat ze bij de implementatiesessie bevestigd kunnen worden):
- De modeldropdown heeft `data-testid="groq-model-select"`.
- De omringende wrapper (voor zichtbaarheid) heeft `data-testid="groq-model-veld"`.
- GET /api/settings levert een veld `groq_model` met de env-default, waarmee
  de frontend de dropdown vult en het default-model bepaalt.
- Bij het versturen van een prompt wordt het gekozen model meegestuurd als
  veld `model`; bij het opslaan van een sessie als veld `groq_model`.

AC gedekt:
- Modeldropdown zichtbaar wanneer provider Groq is geselecteerd
- Modeldropdown niet zichtbaar wanneer provider Ollama is geselecteerd (default)
- Dropdown bevat de vier nieuwe modellen
- Dropdown bevat het model ingesteld via GROQ_MODEL (env-default)
- Geen duplicaat als GROQ_MODEL overeenkomt met een van de vier nieuwe modellen
- Dropdown staat bij laden standaard op de GROQ_MODEL-waarde
- Geselecteerd model wordt meegestuurd bij een promptaanvraag
- Geselecteerd model wordt opgeslagen in de sessie (veld groq_model)
- Bij laden van een sessie met provider Groq wordt het opgeslagen model geselecteerd
- Sessies zonder groq_model-veld vallen terug op de GROQ_MODEL-default
"""
import json
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
SESSIONS_ROUTE = "**/api/sessions"
SESSION_ITEM_ROUTE = "**/api/sessions/*"
SETTINGS_ROUTE = "**/api/settings"
PROMPT_ROUTE = "**/api/prompt"

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

_STUB_PROMPT_RESPONSE = json.dumps({
    "runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}],
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


def _vul_verplichte_velden(page: Page):
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")


def _kies_groq(page: Page):
    page.locator("[data-testid=provider-select]").select_option("groq")


# ---------------------------------------------------------------------------
# Zichtbaarheid
# ---------------------------------------------------------------------------

def test_model_dropdown_niet_zichtbaar_bij_ollama(page: Page):
    """Dekt: TD-11-01 — de modeldropdown is niet zichtbaar bij de standaardprovider Ollama."""
    expect(page.locator("[data-testid=groq-model-select]")).not_to_be_visible()


def test_model_dropdown_zichtbaar_bij_groq(page: Page):
    """Dekt: TD-11-01 — de modeldropdown is zichtbaar wanneer provider Groq is geselecteerd."""
    _kies_groq(page)
    expect(page.locator("[data-testid=groq-model-select]")).to_be_visible()


def test_model_dropdown_verdwijnt_bij_terug_naar_ollama(page: Page):
    """Dekt: TD-11-01 — de modeldropdown verdwijnt weer als de gebruiker teruggaat naar Ollama."""
    _kies_groq(page)
    page.locator("[data-testid=provider-select]").select_option("ollama")
    expect(page.locator("[data-testid=groq-model-select]")).not_to_be_visible()


# ---------------------------------------------------------------------------
# Inhoud van de dropdown
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model", GROQ_MODELS_NIEUW)
def test_dropdown_bevat_nieuw_model(page: Page, model):
    """Dekt: TD-11-02 — de dropdown bevat elk van de vier nieuwe modellen als optie."""
    _kies_groq(page)
    waarden = page.locator("[data-testid=groq-model-select] option").evaluate_all(
        "opts => opts.map(o => o.value)"
    )
    assert model in waarden, f"Model {model!r} ontbreekt in dropdown-opties: {waarden}"


def test_dropdown_bevat_env_default_model(page: Page):
    """Dekt: TD-11-03 — de dropdown bevat het model dat is ingesteld via GROQ_MODEL."""
    _kies_groq(page)
    waarden = page.locator("[data-testid=groq-model-select] option").evaluate_all(
        "opts => opts.map(o => o.value)"
    )
    assert GROQ_MODEL_DEFAULT in waarden, f"Env-default ontbreekt in dropdown-opties: {waarden}"


def test_dropdown_geen_duplicaat_als_env_model_matcht_nieuw_model(page: Page):
    """Dekt: TD-11-04 — als GROQ_MODEL overeenkomt met een van de vier nieuwe modellen, verschijnt deze niet dubbel."""
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


# ---------------------------------------------------------------------------
# Default waarde bij laden
# ---------------------------------------------------------------------------

def test_dropdown_default_is_groq_model_env_waarde(page: Page):
    """Dekt: TD-11-05 — bij het laden van de pagina staat de dropdown standaard op de GROQ_MODEL-waarde."""
    _kies_groq(page)
    expect(page.locator("[data-testid=groq-model-select]")).to_have_value(GROQ_MODEL_DEFAULT)


# ---------------------------------------------------------------------------
# Meesturen bij promptaanvraag
# ---------------------------------------------------------------------------

def test_geselecteerd_model_wordt_meegestuurd_bij_aanvraag(page: Page):
    """Dekt: TD-11-06 — het geselecteerde model wordt meegestuurd bij een promptaanvraag naar de backend."""
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json or {})
        route.fulfill(status=200, content_type="application/json", body=_STUB_PROMPT_RESPONSE)

    page.route(PROMPT_ROUTE, vang_op)
    _vul_verplichte_velden(page)
    _kies_groq(page)
    page.locator("[data-testid=groq-model-select]").select_option("qwen3-32b")
    page.get_by_role("button", name="Verstuur").click()

    assert vastgelegd.get("model") == "qwen3-32b", (
        f"Verwacht model='qwen3-32b' in de aanvraag, kreeg: {vastgelegd}"
    )


# ---------------------------------------------------------------------------
# Sessie opslaan en laden
# ---------------------------------------------------------------------------

def test_geselecteerd_model_wordt_opgeslagen_in_sessie(page: Page):
    """Dekt: TD-11-07 — het geselecteerde Groq-model wordt meegestuurd bij het opslaan van een sessie."""
    vastgelegd: dict = {}

    def vang_op(route):
        if route.request.method == "POST":
            vastgelegd.update(route.request.post_data_json or {})
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')

    page.route(SESSIONS_ROUTE, vang_op)
    _vul_verplichte_velden(page)
    _kies_groq(page)
    page.locator("[data-testid=groq-model-select]").select_option("moonshotai/kimi-k2-instruct")
    page.locator("[name=session-name]").fill("model-sessie")
    page.get_by_role("button", name="Opslaan").click()
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert vastgelegd.get("groq_model") == "moonshotai/kimi-k2-instruct", (
        f"Verwacht groq_model='moonshotai/kimi-k2-instruct' bij opslaan, kreeg: {vastgelegd}"
    )


def test_sessie_laden_herstelt_groq_model(page: Page):
    """Dekt: TD-11-08 — bij het laden van een sessie met provider Groq wordt het opgeslagen model geselecteerd."""
    sessie_data = {
        "name": "model-sessie",
        "rol": "senior developer",
        "taak": "een API ontwerpen",
        "doel": "data op te slaan",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
        "provider": "groq",
        "groq_model": "openai/gpt-oss-20b",
    }

    page.unroute(SESSIONS_ROUTE)
    page.route("**/api/sessions", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"sessions": ["model-sessie"]}',
    ) if not route.request.url.endswith("/model-sessie") else route.continue_())
    page.route("**/api/sessions/model-sessie", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps(sessie_data),
    ))
    page.reload()

    page.locator("[data-testid=sessions-list]").get_by_text("model-sessie").click()

    expect(page.locator("[data-testid=groq-model-select]")).to_have_value("openai/gpt-oss-20b")


def test_sessie_zonder_groq_model_valt_terug_op_default(page: Page):
    """Dekt: TD-11-09 — een sessie zonder 'groq_model'-veld (opgeslagen vóór deze wijziging) laadt met GROQ_MODEL als default."""
    oude_sessie_data = {
        "name": "oude-sessie",
        "rol": "senior developer",
        "taak": "een API ontwerpen",
        "doel": "data op te slaan",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
        "provider": "groq",
    }

    page.unroute(SESSIONS_ROUTE)
    page.route("**/api/sessions", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"sessions": ["oude-sessie"]}',
    ) if not route.request.url.endswith("/oude-sessie") else route.continue_())
    page.route("**/api/sessions/oude-sessie", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps(oude_sessie_data),
    ))
    page.reload()

    page.locator("[data-testid=sessions-list]").get_by_text("oude-sessie").click()

    expect(page.locator("[data-testid=groq-model-select]")).to_have_value(GROQ_MODEL_DEFAULT)
