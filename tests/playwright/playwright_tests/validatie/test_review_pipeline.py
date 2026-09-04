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


# ---------------------------------------------------------------------------
# REVIEW-V-03 — falende reviewketen van één hoofdrun
# ---------------------------------------------------------------------------

def _stub_response_hoofdrun_2_reviewketen_faalt(app: PromptPage) -> None:
    stub_prompt_response(
        app.page,
        runs=[
            {"run_nummer": 1, "temperature": 0.7, "response": "hoofdrun 1 antwoord", "log_status": "ok"},
            {"run_nummer": 2, "temperature": 0.7, "response": "hoofdrun 2 antwoord", "log_status": "ok"},
        ],
        reviewer_stappen=[
            {"hoofdrun_nummer": 1, "reviewer_nr": 1, "reviewer_rol": "QA engineer", "run_nummer": 1,
             "temperature": 0.5, "response": "hoofdrun 1 review", "log_status": "ok"},
            {"hoofdrun_nummer": 2, "reviewer_nr": 1, "reviewer_rol": "QA engineer", "run_nummer": 1,
             "temperature": 0.5, "fout": "API-limiet bereikt na 3 pogingen — probeer later opnieuw"},
        ],
        eindoutputs=[
            {"hoofdrun_nummer": 1, "eindoutput": "hoofdrun 1 review"},
            {"hoofdrun_nummer": 2, "fout": "API-limiet bereikt na 3 pogingen — probeer later opnieuw"},
        ],
    )


def test_falende_reviewketen_toont_foutmelding_in_eigen_eindoutput_blok(app: PromptPage):
    """Testcode: review_pipeline.validatie.03
    Dekt: REVIEW-V-03 — faalt de reviewketen van hoofdrun 2 (bv. API-limiet op de laatste
    stap), dan toont het eindoutput-blok van hoofdrun 2 de foutmelding van die stap.
    """
    _stub_response_hoofdrun_2_reviewketen_faalt(app)
    app.vul_verplichte_velden()
    app.fill_runs(2)
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    expect(app.eindoutput_items.nth(1)).to_contain_text("API-limiet bereikt na 3 pogingen")


def test_falende_reviewketen_laat_eindoutput_blok_van_andere_hoofdrun_ongemoeid(app: PromptPage):
    """Testcode: review_pipeline.validatie.04
    Dekt: REVIEW-V-03 — de eindoutput-blokken van de andere hoofdruns blijven onaangetast
    en tonen hun eigen resultaat wanneer de reviewketen van hoofdrun 2 faalt.
    """
    _stub_response_hoofdrun_2_reviewketen_faalt(app)
    app.vul_verplichte_velden()
    app.fill_runs(2)
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    expect(app.eindoutput_items.nth(0)).to_contain_text("hoofdrun 1 review")
