"""
Interactie-tests voor provider- en modelkeuze.

Bron: documentatie/acceptatiecriteria/provider-en-model.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
provider_en_model.interactie.01 — bewust een ander formaat dan de AC-codes (PROVIDER-I-01).

PROVIDER-I-04 (modelkeuze heeft geen effect bij Ollama) wordt gedekt door de
backend/integratietests (tests/backend/) — geen aparte Playwright-test nodig.
"""
import json
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

PROMPT_ROUTE = "**/api/prompt"
SESSIONS_ROUTE = "**/api/sessions"
SESSION_ITEM_ROUTE = "**/api/sessions/*"
SETTINGS_ROUTE = "**/api/settings"

GROQ_MODEL_DEFAULT = "llama3-8b-8192"

_STUB_SETTINGS = json.dumps({"groq_rpm": 30, "google_rpm": 15, "groq_model": GROQ_MODEL_DEFAULT})
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
# PROVIDER-I-01 — geselecteerde provider meegestuurd
# ---------------------------------------------------------------------------

def test_ollama_provider_meegestuurd_in_aanvraag(page: Page):
    """Testcode: provider_en_model.interactie.01
    Dekt: PROVIDER-I-01 — bij standaard (Ollama) wordt provider='ollama' meegestuurd in de aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"response": "Antwoord", "log_status": "ok", "log_path": "/logs/test.json"}',
        )

    page.route(PROMPT_ROUTE, vang_op)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    assert vastgelegd.get("provider") == "ollama", f"Verwacht 'ollama', kreeg: {vastgelegd.get('provider')!r}"


def test_groq_provider_meegestuurd_in_aanvraag(page: Page):
    """Testcode: provider_en_model.interactie.02
    Dekt: PROVIDER-I-01 — als Groq geselecteerd is, wordt provider='groq' meegestuurd in de aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"response": "Groq antwoord", "log_status": "ok", "log_path": "/logs/test.json"}',
        )

    page.route(PROMPT_ROUTE, vang_op)
    _kies_groq(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    assert vastgelegd.get("provider") == "groq", f"Verwacht 'groq', kreeg: {vastgelegd.get('provider')!r}"


# ---------------------------------------------------------------------------
# PROVIDER-I-02 — sessie laden herstelt provider
# ---------------------------------------------------------------------------

def test_sessie_laden_herstelt_provider_in_dropdown(page: Page):
    """Testcode: provider_en_model.interactie.03
    Dekt: PROVIDER-I-02 — bij het laden van een sessie met provider='groq' wordt Groq geselecteerd in de dropdown.
    """
    sessie_data = json.dumps({
        "name": "test-groq", "provider": "groq",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
    })

    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["test-groq"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()

    page.locator("[data-testid=session-select]").select_option("test-groq")

    geselecteerde_waarde = page.locator("[data-testid=provider-select]").input_value()
    assert geselecteerde_waarde.lower() == "groq", (
        f"Provider na laden sessie is niet 'groq': {geselecteerde_waarde!r}"
    )


def test_sessie_laden_herstelt_ollama_provider(page: Page):
    """Testcode: provider_en_model.interactie.04
    Dekt: PROVIDER-I-02 — bij het laden van een sessie met provider='ollama' wordt Ollama geselecteerd in de dropdown.
    """
    sessie_data = json.dumps({
        "name": "test-ollama", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
    })

    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["test-ollama"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()

    page.locator("[data-testid=session-select]").select_option("test-ollama")

    geselecteerde_waarde = page.locator("[data-testid=provider-select]").input_value()
    assert geselecteerde_waarde.lower() == "ollama", (
        f"Provider na laden sessie is niet 'ollama': {geselecteerde_waarde!r}"
    )


# ---------------------------------------------------------------------------
# PROVIDER-I-03 — Groq-model meegestuurd en hersteld
# ---------------------------------------------------------------------------

def test_geselecteerd_model_wordt_meegestuurd_bij_aanvraag(page: Page):
    """Testcode: provider_en_model.interactie.05
    Dekt: PROVIDER-I-03 — het geselecteerde model wordt meegestuurd bij een promptaanvraag naar de backend.
    """
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


def test_geselecteerd_model_wordt_opgeslagen_in_sessie(page: Page):
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
    """Testcode: provider_en_model.interactie.07
    Dekt: PROVIDER-I-03 — bij het laden van een sessie met provider Groq wordt het opgeslagen model geselecteerd.
    """
    sessie_data = {
        "name": "model-sessie",
        "rol": "senior developer", "taak": "een API ontwerpen", "doel": "data op te slaan",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
        "provider": "groq", "groq_model": "openai/gpt-oss-20b",
    }

    page.unroute(SESSIONS_ROUTE)
    page.route("**/api/sessions", lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["model-sessie"]}',
    ) if not route.request.url.endswith("/model-sessie") else route.continue_())
    page.route("**/api/sessions/model-sessie", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps(sessie_data),
    ))
    page.reload()

    page.locator("[data-testid=sessions-list]").get_by_text("model-sessie").click()

    expect(page.locator("[data-testid=groq-model-select]")).to_have_value("openai/gpt-oss-20b")


def test_sessie_zonder_groq_model_valt_terug_op_default(page: Page):
    """Testcode: provider_en_model.interactie.08
    Dekt: PROVIDER-I-03 — een sessie zonder 'groq_model'-veld (opgeslagen vóór deze wijziging) laadt met GROQ_MODEL als default.
    """
    oude_sessie_data = {
        "name": "oude-sessie",
        "rol": "senior developer", "taak": "een API ontwerpen", "doel": "data op te slaan",
        "formaat": "", "stijl": "", "scope": "", "eisen": "", "voorbeelden": "",
        "provider": "groq",
    }

    page.unroute(SESSIONS_ROUTE)
    page.route("**/api/sessions", lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["oude-sessie"]}',
    ) if not route.request.url.endswith("/oude-sessie") else route.continue_())
    page.route("**/api/sessions/oude-sessie", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps(oude_sessie_data),
    ))
    page.reload()

    page.locator("[data-testid=sessions-list]").get_by_text("oude-sessie").click()

    expect(page.locator("[data-testid=groq-model-select]")).to_have_value(GROQ_MODEL_DEFAULT)
