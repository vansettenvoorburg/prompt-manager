"""
Interactie-tests voor provider- en modelkeuze.

Bron: documentatie/acceptatiecriteria/provider-en-model.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
provider_en_model.interactie.01 — bewust een ander formaat dan de AC-codes (PROVIDER-I-01).

PROVIDER-I-04 (modelkeuze heeft geen effect bij Ollama) wordt gedekt door de
backend/integratietests (tests/backend/) — geen aparte Playwright-test nodig.
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.mocks import (
    GROQ_MODEL_DEFAULT,
    GROQ_MODELS_NIEUW,
    stub_lege_sessies,
    stub_settings,
    stub_sessie_item,
    stub_sessies_met_doorgang,
)
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    stub_settings(page, groq_model=GROQ_MODEL_DEFAULT, groq_models_beschikbaar=GROQ_MODELS_NIEUW)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# PROVIDER-I-01 — geselecteerde provider meegestuurd
# ---------------------------------------------------------------------------

def test_ollama_provider_meegestuurd_in_aanvraag(app: PromptPage):
    """Testcode: provider_en_model.interactie.01
    Dekt: PROVIDER-I-01 — bij standaard (Ollama) wordt provider='ollama' meegestuurd in de aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(status=200, content_type="application/json", body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}')

    app.page.route("**/api/prompt", vang_op)
    app.vul_verplichte_velden()
    app.verstuur()
    app.expect_run_results_zichtbaar()

    assert vastgelegd.get("provider") == "ollama", f"Verwacht 'ollama', kreeg: {vastgelegd.get('provider')!r}"


def test_groq_provider_meegestuurd_in_aanvraag(app: PromptPage):
    """Testcode: provider_en_model.interactie.02
    Dekt: PROVIDER-I-01 — als Groq geselecteerd is, wordt provider='groq' meegestuurd in de aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(status=200, content_type="application/json", body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}')

    app.page.route("**/api/prompt", vang_op)
    app.kies_provider("groq")
    app.vul_verplichte_velden()
    app.verstuur()
    app.expect_run_results_zichtbaar()

    assert vastgelegd.get("provider") == "groq", f"Verwacht 'groq', kreeg: {vastgelegd.get('provider')!r}"


# ---------------------------------------------------------------------------
# PROVIDER-I-02 — sessie laden herstelt provider
# ---------------------------------------------------------------------------

def test_sessie_laden_herstelt_provider_in_dropdown(app: PromptPage):
    """Testcode: provider_en_model.interactie.03
    Dekt: PROVIDER-I-02 — bij het laden van een sessie met provider='groq' wordt Groq geselecteerd in de dropdown.
    """
    sessie_data = {
        "name": "test-groq", "provider": "groq",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
    }
    stub_sessies_met_doorgang(app.page, ["test-groq"])
    stub_sessie_item(app.page, "test-groq", sessie_data)
    app.reload()

    app.sidebar.selecteer_via_dropdown("test-groq")

    app.expect_provider_waarde("groq")


def test_sessie_laden_herstelt_ollama_provider(app: PromptPage):
    """Testcode: provider_en_model.interactie.04
    Dekt: PROVIDER-I-02 — bij het laden van een sessie met provider='ollama' wordt Ollama geselecteerd in de dropdown.
    """
    sessie_data = {
        "name": "test-ollama", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
    }
    stub_sessies_met_doorgang(app.page, ["test-ollama"])
    stub_sessie_item(app.page, "test-ollama", sessie_data)
    app.reload()

    app.sidebar.selecteer_via_dropdown("test-ollama")

    app.expect_provider_waarde("ollama")


# ---------------------------------------------------------------------------
# PROVIDER-I-03 — Groq-model meegestuurd en hersteld
# ---------------------------------------------------------------------------

def test_geselecteerd_model_wordt_meegestuurd_bij_aanvraag(app: PromptPage):
    """Testcode: provider_en_model.interactie.05
    Dekt: PROVIDER-I-03 — het geselecteerde model wordt meegestuurd bij een promptaanvraag naar de backend.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json or {})
        route.fulfill(status=200, content_type="application/json", body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}')

    app.page.route("**/api/prompt", vang_op)
    app.vul_verplichte_velden()
    app.kies_provider("groq")
    app.kies_groq_model("qwen3-32b")
    app.verstuur()
    app.expect_run_results_zichtbaar()

    assert vastgelegd.get("model") == "qwen3-32b", (
        f"Verwacht model='qwen3-32b' in de aanvraag, kreeg: {vastgelegd}"
    )


def test_geselecteerd_model_wordt_opgeslagen_in_sessie(app: PromptPage):
    """Testcode: provider_en_model.interactie.06
    Dekt: PROVIDER-I-03 — het geselecteerde Groq-model wordt meegestuurd bij het opslaan van een sessie.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        if route.request.method == "POST":
            vastgelegd.update(route.request.post_data_json or {})
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')

    app.page.route("**/api/sessions", vang_op)
    app.vul_verplichte_velden()
    app.kies_provider("groq")
    app.kies_groq_model("moonshotai/kimi-k2-instruct")
    app.sidebar.fill_naam("model-sessie")
    app.sidebar.opslaan()
    app.sidebar.wacht_op_bevestiging()

    assert vastgelegd.get("groq_model") == "moonshotai/kimi-k2-instruct", (
        f"Verwacht groq_model='moonshotai/kimi-k2-instruct' bij opslaan, kreeg: {vastgelegd}"
    )


def test_sessie_laden_herstelt_groq_model(app: PromptPage):
    """Testcode: provider_en_model.interactie.07
    Dekt: PROVIDER-I-03 — bij het laden van een sessie met provider Groq wordt het opgeslagen model geselecteerd.
    """
    sessie_data = {
        "name": "model-sessie",
        "rol": "senior developer", "taak": "een API ontwerpen", "doel": "data op te slaan",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
        "provider": "groq", "groq_model": "openai/gpt-oss-20b",
    }
    stub_sessies_met_doorgang(app.page, ["model-sessie"])
    stub_sessie_item(app.page, "model-sessie", sessie_data)
    app.reload()

    app.sidebar.selecteer_via_lijst("model-sessie")

    app.expect_groq_model_waarde("openai/gpt-oss-20b")


def test_sessie_zonder_groq_model_valt_terug_op_default(app: PromptPage):
    """Testcode: provider_en_model.interactie.08
    Dekt: PROVIDER-I-03 — een sessie zonder 'groq_model'-veld (opgeslagen vóór deze wijziging) laadt met GROQ_MODEL als default.
    """
    oude_sessie_data = {
        "name": "oude-sessie",
        "rol": "senior developer", "taak": "een API ontwerpen", "doel": "data op te slaan",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
        "provider": "groq",
    }
    stub_sessies_met_doorgang(app.page, ["oude-sessie"])
    stub_sessie_item(app.page, "oude-sessie", oude_sessie_data)
    app.reload()

    app.sidebar.selecteer_via_lijst("oude-sessie")

    app.expect_groq_model_waarde(GROQ_MODEL_DEFAULT)
