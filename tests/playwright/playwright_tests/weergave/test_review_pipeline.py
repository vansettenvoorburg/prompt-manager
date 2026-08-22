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
from tests.playwright.mocks import stub_lege_sessies
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
