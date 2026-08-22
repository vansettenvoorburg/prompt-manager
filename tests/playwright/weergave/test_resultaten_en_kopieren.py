"""
Weergave-tests voor resultaten weergeven en kopiëren.

Bron: documentatie/acceptatiecriteria/resultaten-en-kopieren.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
resultaten_en_kopieren.weergave.01 — bewust een ander formaat dan de AC-codes
(RESULTAAT-W-01).
"""
import time
import threading
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

PROMPT_ROUTE = "**/api/prompt"
SESSIONS_ROUTE = "**/api/sessions"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))
    page.goto(BASE_URL)


def _vul_verplichte_velden(page: Page):
    waarden = {"rol": "senior developer", "taak": "een API ontwerpen", "doel": "data op te slaan"}
    for veld, waarde in waarden.items():
        page.locator(f"[name={veld}]").fill(waarde)


# ---------------------------------------------------------------------------
# RESULTAAT-W-01 — antwoord verschijnt na versturen
# ---------------------------------------------------------------------------

def test_antwoord_verschijnt_na_correct_invullen(page: Page):
    """Testcode: resultaten_en_kopieren.weergave.01
    Dekt: RESULTAAT-W-01 — het antwoord verschijnt zichtbaar op de pagina na versturen.
    """
    page.route(
        PROMPT_ROUTE,
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "Hier is het antwoord"}]}',
        ),
    )
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_be_visible()
    expect(page.locator("[data-testid=run-results]")).to_contain_text("Hier is het antwoord")


# ---------------------------------------------------------------------------
# RESULTAAT-W-02 — laadstatus tijdens wachten
# ---------------------------------------------------------------------------

def test_laadstatus_zichtbaar_tijdens_wachten(page: Page):
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

    page.route(PROMPT_ROUTE, trage_response)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=loading]")).to_be_visible()


# ---------------------------------------------------------------------------
# RESULTAAT-W-03 — kopieerknop op elk resultaatblok
# ---------------------------------------------------------------------------

def _stub_prompt_response_met_reviewer(page: Page):
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json",
        body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "dit is de uitvoer", "log_status": "ok"}], '
             '"reviewer_stappen": [{"reviewer_nr": 1, "reviewer_rol": "QA engineer", "run_nummer": 1, '
             '"temperature": 0.5, "response": "revieweruitvoer", "log_status": "ok"}], '
             '"eindoutput": "eindversie"}',
    ))


def test_run_result_heeft_kopieerknop(page: Page):
    """Testcode: resultaten_en_kopieren.weergave.03
    Dekt: RESULTAAT-W-03 — elk run-resultaatblok heeft een kopieerknop.
    """
    _stub_prompt_response_met_reviewer(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(
        page.locator("[data-testid=run-results] [data-testid=kopieer-knop]").first
    ).to_be_visible()


def test_reviewer_stap_heeft_kopieerknop(page: Page):
    """Testcode: resultaten_en_kopieren.weergave.04
    Dekt: RESULTAAT-W-03 — elk reviewer-stap-blok heeft een kopieerknop.
    """
    _stub_prompt_response_met_reviewer(page)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first.fill("QA engineer")
    page.get_by_role("button", name="Verstuur").click()

    expect(
        page.locator("[data-testid=reviewer-stap-item] [data-testid=kopieer-knop]").first
    ).to_be_visible()


def test_eindoutput_heeft_kopieerknop(page: Page):
    """Testcode: resultaten_en_kopieren.weergave.05
    Dekt: RESULTAAT-W-03 — de eindoutput heeft een kopieerknop.
    """
    _stub_prompt_response_met_reviewer(page)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first.fill("QA engineer")
    page.get_by_role("button", name="Verstuur").click()

    expect(
        page.locator("[data-testid=eindoutput] [data-testid=kopieer-knop]")
    ).to_be_visible()


# ---------------------------------------------------------------------------
# RESULTAAT-W-04 — melding met logbestandspad
# ---------------------------------------------------------------------------

def test_log_opgeslagen_melding_zichtbaar_na_aanvraag(page: Page):
    """Testcode: resultaten_en_kopieren.weergave.06
    Dekt: RESULTAAT-W-04 — na een succesvolle aanvraag toont de UI 'Log opgeslagen' met het bestandspad.
    """
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "Antwoord van model", "log_status": "ok", "log_path": "/logs/2026-05-14_ollama_test.json"}]}',
    ))
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_contain_text("Log opgeslagen")
    expect(page.locator("[data-testid=run-results]")).to_contain_text("2026-05-14_ollama_test.json")
