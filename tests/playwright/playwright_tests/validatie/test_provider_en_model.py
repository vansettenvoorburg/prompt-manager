"""
Validatie-tests voor provider- en modelkeuze.

Bron: documentatie/acceptatiecriteria/provider-en-model.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
provider_en_model.validatie.01 — bewust een ander formaat dan de AC-codes (PROVIDER-V-01).
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# PROVIDER-V-01 — Ollama niet bereikbaar
# ---------------------------------------------------------------------------

def test_ollama_fout_toont_foutmelding(app: PromptPage):
    """Testcode: provider_en_model.validatie.01
    Dekt: PROVIDER-V-01 — als Ollama niet bereikbaar is (503), toont de UI een foutmelding.
    """
    app.page.route(
        "**/api/prompt",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"detail": "Ollama is niet bereikbaar"}',
        ),
    )
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_error_zichtbaar()
    app.expect_error_niet_leeg()


# ---------------------------------------------------------------------------
# PROVIDER-V-02 — Groq niet bereikbaar / fout / ontbrekende key
# ---------------------------------------------------------------------------

def test_groq_fout_toont_foutmelding(app: PromptPage):
    """Testcode: provider_en_model.validatie.02
    Dekt: PROVIDER-V-02 — als de Groq API een fout retourneert (503), toont de UI een foutmelding.
    """
    app.page.route("**/api/prompt", lambda route: route.fulfill(
        status=503,
        content_type="application/json",
        body='{"detail": "Groq niet bereikbaar"}',
    ))
    app.kies_provider("groq")
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_error_zichtbaar()


def test_groq_fout_geen_stille_mislukking(app: PromptPage):
    """Testcode: provider_en_model.validatie.03
    Dekt: PROVIDER-V-02 — een Groq-fout resulteert in een zichtbare melding, niet in een lege response-sectie.
    """
    app.page.route("**/api/prompt", lambda route: route.fulfill(
        status=503,
        content_type="application/json",
        body='{"detail": "Groq niet bereikbaar"}',
    ))
    app.kies_provider("groq")
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_response_bevat_niet("Groq niet bereikbaar")
    app.expect_error_zichtbaar()
