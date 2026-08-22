"""
Validatie-tests voor resultaten weergeven en kopiëren.

Bron: documentatie/acceptatiecriteria/resultaten-en-kopieren.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
resultaten_en_kopieren.validatie.01 — bewust een ander formaat dan de AC-codes
(RESULTAAT-V-01).

RESULTAAT-V-03 (API-limiet na 3 pogingen) wordt gedekt door de backend/integratietests
(tests/backend/test_backend_09.py) — geen aparte Playwright-test nodig.
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
# RESULTAAT-V-01 — klembord niet beschikbaar
# ---------------------------------------------------------------------------

def test_kopieerknop_toont_mislukt_bij_geen_klembord_toegang(app: PromptPage):
    """Testcode: resultaten_en_kopieren.validatie.01
    Dekt: RESULTAAT-V-01 — als het klembord niet beschikbaar is, toont de knop kort 'Mislukt'.
    """
    stub_prompt_response(app.page, runs=[{"run_nummer": 1, "temperature": 0.8, "response": "dit is de uitvoer", "log_status": "ok"}])
    app.vul_verplichte_velden()
    app.verstuur()
    app.mock_clipboard_mislukt()

    knop = app.eerste_kopieer_knop()
    knop.click()

    expect(knop).to_have_text("Mislukt")


# ---------------------------------------------------------------------------
# RESULTAAT-V-02 — logfout toont waarschuwing, antwoord blijft zichtbaar
# ---------------------------------------------------------------------------

def test_log_mislukt_toont_waarschuwing(app: PromptPage):
    """Testcode: resultaten_en_kopieren.validatie.02
    Dekt: RESULTAAT-V-02 — als logging mislukt (log_warning in response), toont de UI een waarschuwing.
    """
    stub_prompt_response(app.page, runs=[{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord van model", "log_warning": "Logging mislukt"}])
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_run_results_bevat("Logging mislukt")


def test_log_mislukt_toont_antwoord_toch(app: PromptPage):
    """Testcode: resultaten_en_kopieren.validatie.03
    Dekt: RESULTAAT-V-02 — bij een logfout wordt het modelantwoord nog steeds getoond.
    """
    stub_prompt_response(app.page, runs=[{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord ondanks logfout", "log_warning": "Logging mislukt"}])
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_run_results_bevat("Antwoord ondanks logfout")
    app.expect_run_results_bevat("Logging mislukt")


# ---------------------------------------------------------------------------
# RESULTAAT-V-04 — veilige weergave van run-resultaat en eindoutput
# ---------------------------------------------------------------------------

def test_run_resultaat_toont_scripttags_als_platte_tekst(app: PromptPage):
    """Testcode: resultaten_en_kopieren.validatie.04
    Dekt: RESULTAAT-V-04 — HTML-tags in een run-resultaat worden getoond als platte tekst en
    niet uitgevoerd als code.
    """
    stub_prompt_response(app.page, runs=[{"run_nummer": 1, "temperature": 0.8, "response": KWAADAARDIGE_HTML}])
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_html_getoond_als_platte_tekst(app.run_results, KWAADAARDIGE_HTML)


def test_eindoutput_toont_scripttags_als_platte_tekst(app: PromptPage):
    """Testcode: resultaten_en_kopieren.validatie.05
    Dekt: RESULTAAT-V-04 — HTML-tags in de eindoutput worden getoond als platte tekst en niet
    uitgevoerd als code.
    """
    stub_prompt_response(
        app.page,
        runs=[{"run_nummer": 1, "temperature": 0.7, "response": "hoofdantwoord", "log_status": "ok"}],
        reviewer_stappen=[{"reviewer_nr": 1, "reviewer_rol": "QA engineer", "run_nummer": 1,
                            "temperature": 0.5, "response": "revieweruitvoer", "log_status": "ok"}],
        eindoutput=KWAADAARDIGE_HTML,
    )
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    app.expect_html_getoond_als_platte_tekst(app.eindoutput, KWAADAARDIGE_HTML)


def test_run_resultaat_behoudt_markdown_opmaak(app: PromptPage):
    """Testcode: resultaten_en_kopieren.validatie.06
    Dekt: RESULTAAT-V-04 — normale markdown-opmaak (vet, lijst, codeblok) blijft correct
    weergegeven na het veilig maken van de weergave.
    """
    markdown_response = "**vet** en een lijst:\n- item een\n- item twee\n\n```\ncode()\n```"
    stub_prompt_response(app.page, runs=[{"run_nummer": 1, "temperature": 0.8, "response": markdown_response}])
    app.vul_verplichte_velden()
    app.verstuur()

    # <strong>/<code> hebben geen eigen ARIA-rol om op te selecteren — bewuste
    # uitzondering op selectorprioriteit (zie playwright-testing-skill), want dit test
    # juist welk HTML-element de markdown-parser produceert.
    expect(app.run_results.locator("strong")).to_have_text("vet")
    expect(app.run_results.get_by_role("listitem")).to_have_count(2)
    expect(app.run_results.locator("code")).to_be_visible()
