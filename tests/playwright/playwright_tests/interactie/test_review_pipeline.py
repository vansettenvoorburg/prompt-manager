"""
Interactie-tests voor de review pipeline.

Bron: documentatie/acceptatiecriteria/review-pipeline.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
review_pipeline.interactie.01 — bewust een ander formaat dan de AC-codes (REVIEW-I-01).

REVIEW-I-02 (uitvoeringsvolgorde hoofdprompt/reviewers) wordt gedekt door de
backend/integratietests (tests/backend/) — geen aparte Playwright-test nodig.
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.mocks import stub_lege_sessies, stub_prompt_response, stub_sessie_item, stub_sessies_met_doorgang
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


def _stub_response_met_reviewer(app: PromptPage) -> None:
    stub_prompt_response(
        app.page,
        runs=[{"run_nummer": 1, "temperature": 0.7, "response": "hoofdantwoord", "log_status": "ok"}],
        reviewer_stappen=[{
            "reviewer_nr": 1,
            "reviewer_rol": "QA engineer",
            "run_nummer": 1,
            "temperature": 0.5,
            "response": "eindversie",
            "log_status": "ok",
        }],
        eindoutput="eindversie",
    )


# ---------------------------------------------------------------------------
# REVIEW-I-01 — reviewer verwijderen
# ---------------------------------------------------------------------------

def test_reviewer_verwijderen_verwijdert_item(app: PromptPage):
    """Testcode: review_pipeline.interactie.01
    Dekt: REVIEW-I-01 — na klikken op de verwijderknop verdwijnt de reviewer uit de lijst.
    """
    item = app.reviewers.toevoegen()
    item.verwijder()
    app.reviewers.expect_aantal(0)


# ---------------------------------------------------------------------------
# REVIEW-I-03 — uitvoer toont elke stap en de eindoutput
# ---------------------------------------------------------------------------

def test_uitvoer_toont_reviewer_stap(app: PromptPage):
    """Testcode: review_pipeline.interactie.02
    Dekt: REVIEW-I-03 — na uitvoering met reviewers toont de UI de uitvoer van de reviewer-stap.
    """
    _stub_response_met_reviewer(app)
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    app.expect_reviewer_stap_zichtbaar()


def test_uitvoer_toont_eindoutput(app: PromptPage):
    """Testcode: review_pipeline.interactie.03
    Dekt: REVIEW-I-03 — na uitvoering met reviewers is de eindoutput zichtbaar.
    """
    _stub_response_met_reviewer(app)
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    app.verstuur()

    app.expect_eindoutput_zichtbaar()


# ---------------------------------------------------------------------------
# Regressie: sessie opslaan/laden van reviewers (geen exacte AC-bullet in
# review-pipeline.md, gerelateerd aan REVIEW-I-04 — reviewerdata moet correct
# door sessieopslag heen reizen)
# ---------------------------------------------------------------------------

def test_sessie_opslaan_stuurt_reviewers_mee(app: PromptPage):
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

    app.page.route("**/api/sessions", handle)
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    item.fill_omschrijving("Controleer op volledigheid.")
    app.sidebar.fill_naam("test-sessie")
    app.sidebar.opslaan()
    app.sidebar.wacht_op_bevestiging()

    assert "reviewers" in vastgelegd, (
        f"Veld 'reviewers' ontbreekt bij opslaan: {vastgelegd}"
    )
    assert len(vastgelegd["reviewers"]) == 1
    assert vastgelegd["reviewers"][0]["rol"] == "QA engineer"


def test_sessie_opslaan_stuurt_omschrijving_mee(app: PromptPage):
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

    app.page.route("**/api/sessions", handle)
    app.vul_verplichte_velden()
    item = app.reviewers.toevoegen()
    item.fill_rol("QA engineer")
    item.fill_omschrijving("Controleer op volledigheid.")
    app.sidebar.fill_naam("test-sessie")
    app.sidebar.opslaan()
    app.sidebar.wacht_op_bevestiging()

    assert "omschrijving" in vastgelegd["reviewers"][0], (
        f"'omschrijving' ontbreekt in meegestuurde reviewer: {vastgelegd.get('reviewers')}"
    )
    assert vastgelegd["reviewers"][0]["omschrijving"] == "Controleer op volledigheid."


def test_sessie_opslaan_stuurt_review_modus_mee(app: PromptPage):
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

    app.page.route("**/api/sessions", handle)
    app.vul_verplichte_velden()
    app.sidebar.fill_naam("test-sessie")
    app.sidebar.opslaan()
    app.sidebar.wacht_op_bevestiging()

    assert "review_modus" in vastgelegd, (
        f"Veld 'review_modus' ontbreekt bij opslaan: {vastgelegd}"
    )


def test_sessie_opslaan_zonder_reviewers_stuurt_lege_lijst(app: PromptPage):
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

    app.page.route("**/api/sessions", handle)
    app.vul_verplichte_velden()
    app.sidebar.fill_naam("test-sessie")
    app.sidebar.opslaan()
    app.sidebar.wacht_op_bevestiging()

    assert vastgelegd.get("reviewers") == [], (
        f"'reviewers' is niet leeg bij opslaan zonder reviewers: {vastgelegd.get('reviewers')}"
    )


def test_sessie_laden_vult_reviewers_in(app: PromptPage):
    """Testcode: review_pipeline.interactie.08
    Regressie — bij het laden van een sessie met reviewers worden de reviewer-items weergegeven.
    """
    sessie_data = {
        "name": "sessie-met-reviewers", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    stub_sessies_met_doorgang(app.page, ["sessie-met-reviewers"])
    stub_sessie_item(app.page, "sessie-met-reviewers", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("sessie-met-reviewers")

    app.reviewers.expect_aantal(1)


def test_sessie_laden_toont_reviewerrol(app: PromptPage):
    """Testcode: review_pipeline.interactie.09
    Regressie — bij het laden van een sessie wordt de reviewerrol ingevuld.
    """
    sessie_data = {
        "name": "sessie-met-reviewers", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    stub_sessies_met_doorgang(app.page, ["sessie-met-reviewers"])
    stub_sessie_item(app.page, "sessie-met-reviewers", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("sessie-met-reviewers")

    app.reviewers.eerste().expect_rol_waarde("QA engineer")


def test_sessie_laden_toont_revieweromschrijving(app: PromptPage):
    """Testcode: review_pipeline.interactie.10
    Regressie — bij het laden van een sessie wordt de omschrijving van de reviewer ingevuld.
    """
    sessie_data = {
        "name": "sessie-met-reviewers", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "reviewers": [{"rol": "QA engineer", "omschrijving": "Controleer op volledigheid.", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    stub_sessies_met_doorgang(app.page, ["sessie-met-reviewers"])
    stub_sessie_item(app.page, "sessie-met-reviewers", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("sessie-met-reviewers")

    app.reviewers.eerste().expect_omschrijving_waarde("Controleer op volledigheid.")


def test_sessie_laden_zonder_reviewers_toont_geen_reviewer_items(app: PromptPage):
    """Testcode: review_pipeline.interactie.11
    Regressie — bij het laden van een sessie zonder reviewers zijn er geen reviewer-items.
    """
    sessie_data = {
        "name": "sessie-zonder-reviewers", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "reviewers": [],
        "review_modus": "iteratief",
    }
    stub_sessies_met_doorgang(app.page, ["sessie-zonder-reviewers"])
    stub_sessie_item(app.page, "sessie-zonder-reviewers", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("sessie-zonder-reviewers")

    app.reviewers.expect_aantal(0)
