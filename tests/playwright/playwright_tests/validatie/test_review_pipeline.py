"""
Validatie-tests voor de review pipeline.

Bron: documentatie/acceptatiecriteria/review-pipeline.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
review_pipeline.validatie.01 — bewust een ander formaat dan de AC-codes (REVIEW-V-01).

REVIEW-V-01 (rol/omschrijving verplicht) wordt gedekt door de backend/integratietests
(tests/backend/test_backend_08.py) — geen aparte Playwright-test nodig.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
from tests.playwright.mocks import KWAADAARDIGE_HTML, stub_lege_sessies, stub_prompt_response
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# REVIEW-V-02 — veilige weergave van reviewerstap-resultaat
# ---------------------------------------------------------------------------

def test_reviewerstap_toont_scripttags_als_platte_tekst(app: PromptPage):
    """Testcode: review_pipeline.validatie.01
    Dekt: REVIEW-V-02 — HTML-tags in een reviewerstap-resultaat worden getoond als platte
    tekst en niet uitgevoerd als code.
    """
    stub_prompt_response(
        app.page,
        runs=[{"run_nummer": 1, "temperature": 0.7, "response": "hoofdantwoord", "log_status": "ok"}],
        reviewer_stappen=[{"reviewer_nr": 1, "reviewer_rol": "QA engineer", "run_nummer": 1,
                            "temperature": 0.5, "response": KWAADAARDIGE_HTML, "log_status": "ok"}],
        eindoutput=KWAADAARDIGE_HTML,
    )
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    app.expect_html_getoond_als_platte_tekst(app.reviewer_stap_items.first, KWAADAARDIGE_HTML)


def test_reviewerstap_behoudt_markdown_opmaak(app: PromptPage):
    """Testcode: review_pipeline.validatie.02
    Dekt: REVIEW-V-02 — normale markdown-opmaak (vet) blijft correct weergegeven na het veilig
    maken van de weergave.
    """
    stub_prompt_response(
        app.page,
        runs=[{"run_nummer": 1, "temperature": 0.7, "response": "hoofdantwoord", "log_status": "ok"}],
        reviewer_stappen=[{"reviewer_nr": 1, "reviewer_rol": "QA engineer", "run_nummer": 1,
                            "temperature": 0.5, "response": "**verbeterde tekst**", "log_status": "ok"}],
        eindoutput="**verbeterde tekst**",
    )
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    # <strong> heeft geen eigen ARIA-rol om op te selecteren — bewuste uitzondering op
    # selectorprioriteit (zie playwright-testing-skill), want dit test juist welk
    # HTML-element de markdown-parser produceert.
    expect(app.reviewer_stap_items.first.locator("strong")).to_have_text("verbeterde tekst")
