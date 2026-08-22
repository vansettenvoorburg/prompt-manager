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

SESSIONS_ROUTE = "**/api/sessions"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))
    page.goto(BASE_URL)


# ---------------------------------------------------------------------------
# REVIEW-W-01 — reviewer toevoegen: knop, invoervelden, meerdere reviewers
# ---------------------------------------------------------------------------

def test_reviewer_toevoegen_knop_is_aanwezig(page: Page):
    """Testcode: review_pipeline.weergave.01
    Dekt: REVIEW-W-01 — de UI toont een knop om een reviewer toe te voegen.
    """
    expect(page.locator("[data-testid=reviewer-toevoegen]")).to_be_visible()


def test_reviewer_toevoegen_toont_invoervelden(page: Page):
    """Testcode: review_pipeline.weergave.02
    Dekt: REVIEW-W-01 — na klikken op 'Reviewer toevoegen' zijn de invoervelden zichtbaar.
    """
    page.locator("[data-testid=reviewer-toevoegen]").click()
    expect(page.locator("[data-testid=reviewer-item]").first).to_be_visible()


def test_reviewer_rol_invoerveld_is_aanwezig_na_toevoegen(page: Page):
    """Testcode: review_pipeline.weergave.03
    Dekt: REVIEW-W-01 — na toevoegen van een reviewer is een invoerveld voor de rol zichtbaar.
    """
    page.locator("[data-testid=reviewer-toevoegen]").click()
    expect(
        page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first
    ).to_be_visible()


def test_reviewer_omschrijving_invoerveld_is_aanwezig_na_toevoegen(page: Page):
    """Testcode: review_pipeline.weergave.04
    Dekt: REVIEW-W-01 — na toevoegen van een reviewer is een invoerveld voor de omschrijving zichtbaar.
    """
    page.locator("[data-testid=reviewer-toevoegen]").click()
    expect(
        page.locator("[data-testid=reviewer-item] [data-testid=reviewer-omschrijving]").first
    ).to_be_visible()


def test_reviewer_runs_invoerveld_is_aanwezig_na_toevoegen(page: Page):
    """Testcode: review_pipeline.weergave.05
    Dekt: REVIEW-W-01 — na toevoegen van een reviewer is een invoerveld voor het aantal runs zichtbaar.
    """
    page.locator("[data-testid=reviewer-toevoegen]").click()
    expect(
        page.locator("[data-testid=reviewer-item] [data-testid=reviewer-runs]").first
    ).to_be_visible()


def test_reviewer_temperatures_invoerveld_is_aanwezig_na_toevoegen(page: Page):
    """Testcode: review_pipeline.weergave.06
    Dekt: REVIEW-W-01 — na toevoegen van een reviewer is een invoerveld voor de temperatures zichtbaar.
    """
    page.locator("[data-testid=reviewer-toevoegen]").click()
    expect(
        page.locator("[data-testid=reviewer-item] [data-testid=reviewer-temperatures]").first
    ).to_be_visible()


def test_meerdere_reviewers_kunnen_worden_toegevoegd(page: Page):
    """Testcode: review_pipeline.weergave.07
    Dekt: REVIEW-W-01 — de gebruiker kan meerdere reviewers toevoegen.
    """
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-toevoegen]").click()
    expect(page.locator("[data-testid=reviewer-item]")).to_have_count(2)


# ---------------------------------------------------------------------------
# REVIEW-W-02 — keuzemenu reviewmodus
# ---------------------------------------------------------------------------

def test_review_modus_selector_is_aanwezig(page: Page):
    """Testcode: review_pipeline.weergave.08
    Dekt: REVIEW-W-02 — de UI toont een keuzemenu voor de reviewmodus.
    """
    expect(page.locator("[data-testid=review-modus-select]")).to_be_attached()


# ---------------------------------------------------------------------------
# REVIEW-W-03 — verwijderknop per reviewer
# ---------------------------------------------------------------------------

def test_reviewer_verwijder_knop_is_zichtbaar(page: Page):
    """Testcode: review_pipeline.weergave.09
    Dekt: REVIEW-W-03 — na toevoegen van een reviewer is de verwijderknop zichtbaar.
    """
    page.locator("[data-testid=reviewer-toevoegen]").click()
    expect(page.locator("[data-testid=reviewer-verwijder]").first).to_be_visible()
