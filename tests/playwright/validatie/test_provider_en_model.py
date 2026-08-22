"""
Validatie-tests voor provider- en modelkeuze.

Bron: documentatie/acceptatiecriteria/provider-en-model.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
provider_en_model.validatie.01 — bewust een ander formaat dan de AC-codes (PROVIDER-V-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

PROMPT_ROUTE = "**/api/prompt"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.goto(BASE_URL)


def _vul_verplichte_velden(page: Page):
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")


# ---------------------------------------------------------------------------
# PROVIDER-V-01 — Ollama niet bereikbaar
# ---------------------------------------------------------------------------

def test_ollama_fout_toont_foutmelding(page: Page):
    """Testcode: provider_en_model.validatie.01
    Dekt: PROVIDER-V-01 — als Ollama niet bereikbaar is (503), toont de UI een foutmelding.
    """
    page.route(
        PROMPT_ROUTE,
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"detail": "Ollama is niet bereikbaar"}',
        ),
    )
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()
    expect(page.locator("[data-testid=error]")).not_to_be_empty()


# ---------------------------------------------------------------------------
# PROVIDER-V-02 — Groq niet bereikbaar / fout / ontbrekende key
# ---------------------------------------------------------------------------

def test_groq_fout_toont_foutmelding(page: Page):
    """Testcode: provider_en_model.validatie.02
    Dekt: PROVIDER-V-02 — als de Groq API een fout retourneert (503), toont de UI een foutmelding.
    """
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
    """Testcode: provider_en_model.validatie.03
    Dekt: PROVIDER-V-02 — een Groq-fout resulteert in een zichtbare melding, niet in een lege response-sectie.
    """
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
