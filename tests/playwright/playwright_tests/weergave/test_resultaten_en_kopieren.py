"""
Weergave-tests voor resultaten weergeven en kopiëren.

Bron: documentatie/acceptatiecriteria/resultaten-en-kopieren.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
resultaten_en_kopieren.weergave.01 — bewust een ander formaat dan de AC-codes
(RESULTAAT-W-01).
"""
import threading
import time

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
from tests.playwright.mocks import PROMPT_ROUTE, stub_lege_sessies, stub_prompt_response
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# RESULTAAT-W-01 — antwoord verschijnt na versturen
# ---------------------------------------------------------------------------

def test_antwoord_verschijnt_na_correct_invullen(app: PromptPage):
    """Testcode: resultaten_en_kopieren.weergave.01
    Dekt: RESULTAAT-W-01 — het antwoord verschijnt zichtbaar op de pagina na versturen.
    """
    stub_prompt_response(app.page, runs=[{"run_nummer": 1, "temperature": 0.8, "response": "Hier is het antwoord"}])
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_run_results_zichtbaar()
    app.expect_run_results_bevat("Hier is het antwoord")


# ---------------------------------------------------------------------------
# RESULTAAT-W-02 — laadstatus tijdens wachten
# ---------------------------------------------------------------------------

def test_laadstatus_zichtbaar_tijdens_wachten(app: PromptPage):
    """Testcode: resultaten_en_kopieren.weergave.02
    Dekt: RESULTAAT-W-02 — zolang de aanvraag bezig is, is een laadstatus zichtbaar.
    """

    def trage_response(route):
        def fulfill():
            time.sleep(0.3)
            try:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord"}]}',
                )
            except Exception:
                pass
        threading.Thread(target=fulfill, daemon=True).start()

    app.page.route(PROMPT_ROUTE, trage_response)
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_loading_zichtbaar()


# ---------------------------------------------------------------------------
# RESULTAAT-W-03 — kopieerknop op elk resultaatblok
# ---------------------------------------------------------------------------

def _stub_prompt_response_met_reviewer(app: PromptPage) -> None:
    stub_prompt_response(
        app.page,
        runs=[{"run_nummer": 1, "temperature": 0.8, "response": "dit is de uitvoer", "log_status": "ok"}],
        reviewer_stappen=[{"reviewer_nr": 1, "reviewer_rol": "QA engineer", "run_nummer": 1,
                            "temperature": 0.5, "response": "revieweruitvoer", "log_status": "ok"}],
        eindoutput="eindversie",
    )


def test_run_result_heeft_kopieerknop(app: PromptPage):
    """Testcode: resultaten_en_kopieren.weergave.03
    Dekt: RESULTAAT-W-03 — elk run-resultaatblok heeft een kopieerknop.
    """
    _stub_prompt_response_met_reviewer(app)
    app.vul_verplichte_velden()
    app.verstuur()

    expect(app.eerste_kopieer_knop("run-results")).to_be_visible()


def test_reviewer_stap_heeft_kopieerknop(app: PromptPage):
    """Testcode: resultaten_en_kopieren.weergave.04
    Dekt: RESULTAAT-W-03 — elk reviewer-stap-blok heeft een kopieerknop.
    """
    _stub_prompt_response_met_reviewer(app)
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    expect(app.eerste_kopieer_knop("reviewer-stap-item")).to_be_visible()


def test_eindoutput_heeft_kopieerknop(app: PromptPage):
    """Testcode: resultaten_en_kopieren.weergave.05
    Dekt: RESULTAAT-W-03 — de eindoutput heeft een kopieerknop.
    """
    _stub_prompt_response_met_reviewer(app)
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    expect(app.eerste_kopieer_knop("eindoutput")).to_be_visible()


# ---------------------------------------------------------------------------
# RESULTAAT-W-04 — melding met logbestandspad
# ---------------------------------------------------------------------------

def test_log_opgeslagen_melding_zichtbaar_na_aanvraag(app: PromptPage):
    """Testcode: resultaten_en_kopieren.weergave.06
    Dekt: RESULTAAT-W-04 — na een succesvolle aanvraag toont de UI 'Log opgeslagen' met het bestandspad.
    """
    stub_prompt_response(app.page, runs=[{
        "run_nummer": 1, "temperature": 0.8, "response": "Antwoord van model",
        "log_status": "ok", "log_path": "/logs/2026-05-14_ollama_test.json",
    }])
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_run_results_bevat("Log opgeslagen")
    app.expect_run_results_bevat("2026-05-14_ollama_test.json")
