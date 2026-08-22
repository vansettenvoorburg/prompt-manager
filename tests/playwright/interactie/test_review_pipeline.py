"""
Interactie-tests voor de review pipeline.

Bron: documentatie/acceptatiecriteria/review-pipeline.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
review_pipeline.interactie.01 — bewust een ander formaat dan de AC-codes (REVIEW-I-01).

REVIEW-I-02 (uitvoeringsvolgorde hoofdprompt/reviewers) wordt gedekt door de
backend/integratietests (tests/backend/) — geen aparte Playwright-test nodig.
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


def _stub_response_met_reviewer(page: Page):
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({
            "runs": [
                {"run_nummer": 1, "temperature": 0.7, "response": "hoofdantwoord", "log_status": "ok"}
            ],
            "reviewer_stappen": [
                {
                    "reviewer_nr": 1,
                    "reviewer_rol": "QA engineer",
                    "run_nummer": 1,
                    "temperature": 0.5,
                    "response": "eindversie",
                    "log_status": "ok",
                }
            ],
            "eindoutput": "eindversie",
        }),
    ))


# ---------------------------------------------------------------------------
# REVIEW-I-01 — reviewer verwijderen
# ---------------------------------------------------------------------------

def test_reviewer_verwijderen_verwijdert_item(page: Page):
    """Testcode: review_pipeline.interactie.01
    Dekt: REVIEW-I-01 — na klikken op de verwijderknop verdwijnt de reviewer uit de lijst.
    """
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-verwijder]").first.click()
    expect(page.locator("[data-testid=reviewer-item]")).to_have_count(0)


# ---------------------------------------------------------------------------
# REVIEW-I-03 — uitvoer toont elke stap en de eindoutput
# ---------------------------------------------------------------------------

def test_uitvoer_toont_reviewer_stap(page: Page):
    """Testcode: review_pipeline.interactie.02
    Dekt: REVIEW-I-03 — na uitvoering met reviewers toont de UI de uitvoer van de reviewer-stap.
    """
    _stub_response_met_reviewer(page)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first.fill("QA engineer")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=reviewer-stap-item]").first).to_be_visible()


def test_uitvoer_toont_eindoutput(page: Page):
    """Testcode: review_pipeline.interactie.03
    Dekt: REVIEW-I-03 — na uitvoering met reviewers is de eindoutput zichtbaar.
    """
    _stub_response_met_reviewer(page)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first.fill("QA engineer")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=eindoutput]")).to_be_visible()


# ---------------------------------------------------------------------------
# Regressie: sessie opslaan/laden van reviewers (geen exacte AC-bullet in
# review-pipeline.md, gerelateerd aan REVIEW-I-04 — reviewerdata moet correct
# door sessieopslag heen reizen)
# ---------------------------------------------------------------------------

def test_sessie_opslaan_stuurt_reviewers_mee(page: Page):
    """Testcode: review_pipeline.interactie.04
    Regressie — bij het opslaan van een sessie met reviewers worden ze meegestuurd.
    """
    vastgelegd: dict = {}

    def handle(route):
        if route.request.method == "POST":
            vastgelegd.update(route.request.post_data_json)
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')

    page.route(SESSIONS_ROUTE, handle)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first.fill("QA engineer")
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-omschrijving]").first.fill("Controleer op volledigheid.")
    page.locator("[name=session-name]").fill("test-sessie")
    page.get_by_role("button", name="Opslaan").click()
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert "reviewers" in vastgelegd, (
        f"Veld 'reviewers' ontbreekt bij opslaan: {vastgelegd}"
    )
    assert len(vastgelegd["reviewers"]) == 1
    assert vastgelegd["reviewers"][0]["rol"] == "QA engineer"


def test_sessie_opslaan_stuurt_omschrijving_mee(page: Page):
    """Testcode: review_pipeline.interactie.05
    Regressie — bij het opslaan van een sessie met reviewers wordt de omschrijving meegestuurd.
    """
    vastgelegd: dict = {}

    def handle(route):
        if route.request.method == "POST":
            vastgelegd.update(route.request.post_data_json)
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')

    page.route(SESSIONS_ROUTE, handle)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first.fill("QA engineer")
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-omschrijving]").first.fill("Controleer op volledigheid.")
    page.locator("[name=session-name]").fill("test-sessie")
    page.get_by_role("button", name="Opslaan").click()
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert "omschrijving" in vastgelegd["reviewers"][0], (
        f"'omschrijving' ontbreekt in meegestuurde reviewer: {vastgelegd.get('reviewers')}"
    )
    assert vastgelegd["reviewers"][0]["omschrijving"] == "Controleer op volledigheid."


def test_sessie_opslaan_stuurt_review_modus_mee(page: Page):
    """Testcode: review_pipeline.interactie.06
    Regressie — bij het opslaan wordt 'review_modus' meegestuurd.
    """
    vastgelegd: dict = {}

    def handle(route):
        if route.request.method == "POST":
            vastgelegd.update(route.request.post_data_json)
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')

    page.route(SESSIONS_ROUTE, handle)
    _vul_verplichte_velden(page)
    page.locator("[name=session-name]").fill("test-sessie")
    page.get_by_role("button", name="Opslaan").click()
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert "review_modus" in vastgelegd, (
        f"Veld 'review_modus' ontbreekt bij opslaan: {vastgelegd}"
    )


def test_sessie_opslaan_zonder_reviewers_stuurt_lege_lijst(page: Page):
    """Testcode: review_pipeline.interactie.07
    Regressie — bij het opslaan zonder reviewers is 'reviewers' een lege lijst.
    """
    vastgelegd: dict = {}

    def handle(route):
        if route.request.method == "POST":
            vastgelegd.update(route.request.post_data_json)
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')

    page.route(SESSIONS_ROUTE, handle)
    _vul_verplichte_velden(page)
    page.locator("[name=session-name]").fill("test-sessie")
    page.get_by_role("button", name="Opslaan").click()
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert vastgelegd.get("reviewers") == [], (
        f"'reviewers' is niet leeg bij opslaan zonder reviewers: {vastgelegd.get('reviewers')}"
    )


def test_sessie_laden_vult_reviewers_in(page: Page):
    """Testcode: review_pipeline.interactie.08
    Regressie — bij het laden van een sessie met reviewers worden de reviewer-items weergegeven.
    """
    sessie_data = json.dumps({
        "name": "sessie-met-reviewers", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["sessie-met-reviewers"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("sessie-met-reviewers")

    expect(page.locator("[data-testid=reviewer-item]")).to_have_count(1)


def test_sessie_laden_toont_reviewerrol(page: Page):
    """Testcode: review_pipeline.interactie.09
    Regressie — bij het laden van een sessie wordt de reviewerrol ingevuld.
    """
    sessie_data = json.dumps({
        "name": "sessie-met-reviewers", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["sessie-met-reviewers"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("sessie-met-reviewers")

    waarde = page.locator(
        "[data-testid=reviewer-item] [data-testid=reviewer-rol]"
    ).first.input_value()
    assert waarde == "QA engineer", f"Reviewerrol niet ingevuld: {waarde!r}"


def test_sessie_laden_toont_revieweromschrijving(page: Page):
    """Testcode: review_pipeline.interactie.10
    Regressie — bij het laden van een sessie wordt de omschrijving van de reviewer ingevuld.
    """
    sessie_data = json.dumps({
        "name": "sessie-met-reviewers", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["sessie-met-reviewers"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("sessie-met-reviewers")

    waarde = page.locator(
        "[data-testid=reviewer-item] [data-testid=reviewer-omschrijving]"
    ).first.input_value()
    assert waarde == "Controleer op volledigheid.", f"Omschrijving niet ingevuld: {waarde!r}"


def test_sessie_laden_zonder_reviewers_toont_geen_reviewer_items(page: Page):
    """Testcode: review_pipeline.interactie.11
    Regressie — bij het laden van een sessie zonder reviewers zijn er geen reviewer-items.
    """
    sessie_data = json.dumps({
        "name": "sessie-zonder-reviewers", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "reviewers": [],
        "review_modus": "iteratief",
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["sessie-zonder-reviewers"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("sessie-zonder-reviewers")

    expect(page.locator("[data-testid=reviewer-item]")).to_have_count(0)
