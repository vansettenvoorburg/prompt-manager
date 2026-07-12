"""
Frontend-tests voor story 05: Groq als tweede provider.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.

AC gedekt:
- De UI toont een dropdown met de opties 'Ollama' en 'Groq'
- Standaardwaarde van de dropdown is 'Ollama'
- De geselecteerde provider wordt meegestuurd in de aanvraag
- Bij laden van een sessie wordt de opgeslagen provider geselecteerd in de dropdown
- Als Groq een fout retourneert (503), toont de UI een foutmelding (geen stille mislukking)
"""
import json
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
PROMPT_ROUTE = "**/api/prompt"
SESSIONS_ROUTE = "**/api/sessions"
SESSION_ITEM_ROUTE = "**/api/sessions/*"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))
    page.goto(BASE_URL)


def _vul_verplichte_velden(page: Page):
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")


# ---------------------------------------------------------------------------
# Dropdown structuur
# ---------------------------------------------------------------------------

def test_provider_dropdown_is_zichtbaar(page: Page):
    """De UI toont een dropdown om de provider te selecteren."""
    expect(page.locator("[data-testid=provider-select]")).to_be_visible()


def test_dropdown_heeft_ollama_optie(page: Page):
    """De dropdown bevat de optie 'Ollama'."""
    opties = page.locator("[data-testid=provider-select] option").all_text_contents()
    assert any("Ollama" in o or "ollama" in o for o in opties), f"'Ollama' ontbreekt in opties: {opties}"


def test_dropdown_heeft_groq_optie(page: Page):
    """De dropdown bevat de optie 'Groq'."""
    opties = page.locator("[data-testid=provider-select] option").all_text_contents()
    assert any("Groq" in o or "groq" in o for o in opties), f"'Groq' ontbreekt in opties: {opties}"


def test_standaard_provider_is_ollama(page: Page):
    """De standaardwaarde van de dropdown is 'Ollama'."""
    geselecteerde_waarde = page.locator("[data-testid=provider-select]").input_value()
    assert geselecteerde_waarde.lower() == "ollama", f"Standaard provider is niet ollama: {geselecteerde_waarde!r}"


# ---------------------------------------------------------------------------
# Provider meegestuurd in aanvraag
# ---------------------------------------------------------------------------

def test_ollama_provider_meegestuurd_in_aanvraag(page: Page):
    """Bij standaard (Ollama) wordt provider='ollama' meegestuurd in de aanvraag."""
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
    """Als Groq geselecteerd is, wordt provider='groq' meegestuurd in de aanvraag."""
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"response": "Groq antwoord", "log_status": "ok", "log_path": "/logs/test.json"}',
        )

    page.route(PROMPT_ROUTE, vang_op)
    page.locator("[data-testid=provider-select]").select_option("groq")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    assert vastgelegd.get("provider") == "groq", f"Verwacht 'groq', kreeg: {vastgelegd.get('provider')!r}"


# ---------------------------------------------------------------------------
# Sessie laden herstelt provider
# ---------------------------------------------------------------------------

def test_sessie_laden_herstelt_provider_in_dropdown(page: Page):
    """Bij het laden van een sessie met provider='groq' wordt Groq geselecteerd in de dropdown."""
    sessie_data = json.dumps({
        "name": "test-groq",
        "provider": "groq",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "formaat": "",
        "stijl": "",
        "scope": "",
        "eisen": "",
        "voorbeelden": "",
    })

    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"sessions": ["test-groq"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=sessie_data,
    ))
    page.reload()

    page.locator("[data-testid=session-select]").select_option("test-groq")

    geselecteerde_waarde = page.locator("[data-testid=provider-select]").input_value()
    assert geselecteerde_waarde.lower() == "groq", (
        f"Provider na laden sessie is niet 'groq': {geselecteerde_waarde!r}"
    )


def test_sessie_laden_herstelt_ollama_provider(page: Page):
    """Bij het laden van een sessie met provider='ollama' wordt Ollama geselecteerd in de dropdown."""
    sessie_data = json.dumps({
        "name": "test-ollama",
        "provider": "ollama",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "formaat": "",
        "stijl": "",
        "scope": "",
        "eisen": "",
        "voorbeelden": "",
    })

    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"sessions": ["test-ollama"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=sessie_data,
    ))
    page.reload()

    page.locator("[data-testid=session-select]").select_option("test-ollama")

    geselecteerde_waarde = page.locator("[data-testid=provider-select]").input_value()
    assert geselecteerde_waarde.lower() == "ollama", (
        f"Provider na laden sessie is niet 'ollama': {geselecteerde_waarde!r}"
    )


# ---------------------------------------------------------------------------
# Foutafhandeling Groq
# ---------------------------------------------------------------------------

def test_groq_fout_toont_foutmelding(page: Page):
    """Als de Groq API een fout retourneert (503), toont de UI een foutmelding."""
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=503,
        content_type="application/json",
        body='{"detail": "Groq niet bereikbaar"}',
    ))
    page.locator("[data-testid=provider-select]").select_option("groq")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()


def test_groq_fout_geen_stille_mislukking(page: Page):
    """Een Groq-fout resulteert in een zichtbare melding, niet in een lege response-sectie."""
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=503,
        content_type="application/json",
        body='{"detail": "Groq niet bereikbaar"}',
    ))
    page.locator("[data-testid=provider-select]").select_option("groq")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=response]")).not_to_contain_text("Groq niet bereikbaar")
    expect(page.locator("[data-testid=error]")).to_be_visible()
