"""
Weergave-tests voor de review pipeline.

Bron: documentatie/acceptatiecriteria/review-pipeline.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
review_pipeline.weergave.01 — bewust een ander formaat dan de AC-codes (REVIEW-W-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
from tests.playwright.mocks import stub_lege_sessies, stub_prompt_response
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# REVIEW-W-01 — reviewer toevoegen: knop, invoervelden, meerdere reviewers
# ---------------------------------------------------------------------------

def test_reviewer_toevoegen_knop_is_aanwezig(app: PromptPage):
    """Testcode: review_pipeline.weergave.01
    Dekt: REVIEW-W-01 — de UI toont een knop om een reviewer toe te voegen.
    """
    app.reviewers.expect_toevoegen_knop_zichtbaar()


def test_reviewer_toevoegen_toont_invoervelden(app: PromptPage):
    """Testcode: review_pipeline.weergave.02
    Dekt: REVIEW-W-01 — na klikken op 'Reviewer toevoegen' zijn de invoervelden zichtbaar.
    """
    item = app.reviewers.toevoegen()
    item.expect_zichtbaar()


def test_reviewer_rol_invoerveld_is_aanwezig_na_toevoegen(app: PromptPage):
    """Testcode: review_pipeline.weergave.03
    Dekt: REVIEW-W-01 — na toevoegen van een reviewer is een invoerveld voor de rol zichtbaar.
    """
    item = app.reviewers.toevoegen()
    item.expect_rol_zichtbaar()


def test_reviewer_omschrijving_invoerveld_is_aanwezig_na_toevoegen(app: PromptPage):
    """Testcode: review_pipeline.weergave.04
    Dekt: REVIEW-W-01 — na toevoegen van een reviewer is een invoerveld voor de omschrijving zichtbaar.
    """
    item = app.reviewers.toevoegen()
    item.expect_omschrijving_zichtbaar()


def test_reviewer_runs_invoerveld_is_aanwezig_na_toevoegen(app: PromptPage):
    """Testcode: review_pipeline.weergave.05
    Dekt: REVIEW-W-01 — na toevoegen van een reviewer is een invoerveld voor het aantal runs zichtbaar.
    """
    item = app.reviewers.toevoegen()
    item.expect_runs_zichtbaar()


def test_reviewer_temperatures_invoerveld_is_aanwezig_na_toevoegen(app: PromptPage):
    """Testcode: review_pipeline.weergave.06
    Dekt: REVIEW-W-01 — na toevoegen van een reviewer is een invoerveld voor de temperatures zichtbaar.
    """
    item = app.reviewers.toevoegen()
    item.expect_temperatures_zichtbaar()


def test_meerdere_reviewers_kunnen_worden_toegevoegd(app: PromptPage):
    """Testcode: review_pipeline.weergave.07
    Dekt: REVIEW-W-01 — de gebruiker kan meerdere reviewers toevoegen.
    """
    app.reviewers.toevoegen_knop.click()
    app.reviewers.toevoegen_knop.click()
    app.reviewers.expect_aantal(2)


# ---------------------------------------------------------------------------
# REVIEW-W-02 — keuzemenu reviewmodus
# ---------------------------------------------------------------------------

def test_review_modus_selector_is_aanwezig(app: PromptPage):
    """Testcode: review_pipeline.weergave.08
    Dekt: REVIEW-W-02 — de UI toont een keuzemenu voor de reviewmodus.
    """
    expect(app.review_modus_select).to_be_attached()


# ---------------------------------------------------------------------------
# REVIEW-W-03 — verwijderknop per reviewer
# ---------------------------------------------------------------------------

def test_reviewer_verwijder_knop_is_zichtbaar(app: PromptPage):
    """Testcode: review_pipeline.weergave.09
    Dekt: REVIEW-W-03 — na toevoegen van een reviewer is de verwijderknop zichtbaar.
    """
    item = app.reviewers.toevoegen()
    item.expect_verwijder_knop_zichtbaar()


# ---------------------------------------------------------------------------
# REVIEW-W-04 / REVIEW-W-05 / REVIEW-W-06 — eigen eindoutput-blok per hoofdrun
# ---------------------------------------------------------------------------

def _stub_response_twee_hoofdruns_met_reviewer(app: PromptPage) -> None:
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
             "temperature": 0.5, "response": "hoofdrun 2 review", "log_status": "ok"},
        ],
        eindoutputs=[
            {"hoofdrun_nummer": 1, "eindoutput": "hoofdrun 1 review"},
            {"hoofdrun_nummer": 2, "eindoutput": "hoofdrun 2 review"},
        ],
    )


def test_meerdere_hoofdruns_toont_eigen_eindoutput_blok_per_hoofdrun(app: PromptPage):
    """Testcode: review_pipeline.weergave.10
    Dekt: REVIEW-W-04 — bij 2 hoofdruns met reviewers toont de UI 2 eindoutput-blokken
    (in plaats van één gedeeld blok met alleen het resultaat van de laatste hoofdrun).
    """
    _stub_response_twee_hoofdruns_met_reviewer(app)
    app.vul_verplichte_velden()
    app.fill_runs(2)
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    app.expect_eindoutput_blokken_aantal(2)


def test_eindoutput_blok_is_gekoppeld_aan_zijn_hoofdrun_nummer(app: PromptPage):
    """Testcode: review_pipeline.weergave.11
    Dekt: REVIEW-W-04 — elk eindoutput-blok is zichtbaar gekoppeld aan zijn hoofdrun
    (bv. "Eindoutput — run X").
    """
    _stub_response_twee_hoofdruns_met_reviewer(app)
    app.vul_verplichte_velden()
    app.fill_runs(2)
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    app.expect_eindoutput_blok_toont_hoofdrun_nummer(app.eindoutput_items.nth(0), 1)
    app.expect_eindoutput_blok_toont_hoofdrun_nummer(app.eindoutput_items.nth(1), 2)


def test_elk_eindoutput_blok_heeft_eigen_kopieerknop(app: PromptPage):
    """Testcode: review_pipeline.weergave.12
    Dekt: REVIEW-W-05 — elk eindoutput-blok heeft zijn eigen kopieerknop.
    """
    _stub_response_twee_hoofdruns_met_reviewer(app)
    app.vul_verplichte_velden()
    app.fill_runs(2)
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    expect(app.eindoutput.get_by_test_id("kopieer-knop")).to_have_count(2)


def test_een_hoofdrun_blijft_een_eindoutput_blok_zonder_run_aanduiding(app: PromptPage):
    """Testcode: review_pipeline.weergave.13
    Dekt: REVIEW-W-06 — bij precies één hoofdrun blijft het gedrag ongewijzigd: één
    eindoutput-blok, zonder run-aanduiding (geen 'eindoutput-item'-elementen).
    """
    stub_prompt_response(
        app.page,
        runs=[{"run_nummer": 1, "temperature": 0.7, "response": "hoofdantwoord", "log_status": "ok"}],
        reviewer_stappen=[{
            "reviewer_nr": 1, "reviewer_rol": "QA engineer", "run_nummer": 1,
            "temperature": 0.5, "response": "eindversie", "log_status": "ok",
        }],
        eindoutput="eindversie",
    )
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    app.expect_eindoutput_zichtbaar()
    app.expect_eindoutput_blokken_aantal(0)
