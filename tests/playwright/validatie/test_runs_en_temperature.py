"""
Validatie-tests voor runs en temperature.

Bron: documentatie/acceptatiecriteria/runs-en-temperature.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
runs_en_temperature.validatie.01 — bewust een ander formaat dan de AC-codes (RUNS-V-01).
"""
import json
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
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")


# ---------------------------------------------------------------------------
# RUNS-V-01 — runs < 1
# ---------------------------------------------------------------------------

def test_runs_nul_toont_foutmelding_en_verstuurt_niet(page: Page):
    """Testcode: runs_en_temperature.validatie.01
    Dekt: RUNS-V-01 — bij runs=0 toont de UI een foutmelding en wordt de aanvraag niet verstuurd.
    """
    calls = []
    page.route(PROMPT_ROUTE, lambda route: (calls.append(route) or route.abort()))

    page.locator("[data-testid=runs-input]").fill("0")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()
    assert len(calls) == 0, "Er mag geen aanvraag zijn verstuurd bij runs=0"


# ---------------------------------------------------------------------------
# RUNS-V-02 — temperature verplicht
# ---------------------------------------------------------------------------

def test_temperature_leeg_toont_foutmelding_en_verstuurt_niet(page: Page):
    """Testcode: runs_en_temperature.validatie.02
    Dekt: RUNS-V-02 — bij een lege temperature toont de UI een foutmelding en wordt de aanvraag niet verstuurd.
    """
    calls = []
    page.route(PROMPT_ROUTE, lambda route: (calls.append(route) or route.abort()))

    page.locator("[data-testid=temperature-input]").fill("")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()
    assert len(calls) == 0, "Er mag geen aanvraag zijn verstuurd bij lege temperature"


# ---------------------------------------------------------------------------
# RUNS-V-03 — temperature buiten 0.0–2.0
# ---------------------------------------------------------------------------

def test_temperature_buiten_bereik_toont_foutmelding(page: Page):
    """Testcode: runs_en_temperature.validatie.03
    Dekt: RUNS-V-03 — bij een temperature buiten 0–2 toont de UI een foutmelding.
    """
    page.locator("[data-testid=temperature-input]").fill("2.5")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()


def test_temperature_foutmelding_noemt_bereik(page: Page):
    """Testcode: runs_en_temperature.validatie.04
    Dekt: RUNS-V-03 — de foutmelding bij een ongeldige temperature vermeldt het geldige bereik (0 en 2).
    """
    page.locator("[data-testid=temperature-input]").fill("3.0")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    foutmelding = page.locator("[data-testid=error]").inner_text()
    assert "0" in foutmelding and "2" in foutmelding, (
        f"Foutmelding vermeldt bereik niet: {foutmelding!r}"
    )


# ---------------------------------------------------------------------------
# RUNS-V-04 — mismatch aantal temperatures in modus per_run
# ---------------------------------------------------------------------------

def test_per_run_mismatch_toont_foutmelding(page: Page):
    """Testcode: runs_en_temperature.validatie.05
    Dekt: RUNS-V-04 — in modus 'per_run' met verkeerd aantal temperatures toont de UI een foutmelding.
    """
    page.locator("[data-testid=runs-input]").fill("3")
    page.locator("[data-testid=temperature-modus-per-run]").click()
    page.locator("[data-testid=temperature-input]").fill("0.3, 0.7")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()


def test_per_run_mismatch_foutmelding_noemt_verwacht_aantal(page: Page):
    """Testcode: runs_en_temperature.validatie.06
    Dekt: RUNS-V-04 — de foutmelding bij een per_run-mismatch vermeldt het verwachte aantal temperatures.
    """
    page.locator("[data-testid=runs-input]").fill("3")
    page.locator("[data-testid=temperature-modus-per-run]").click()
    page.locator("[data-testid=temperature-input]").fill("0.3, 0.7")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    foutmelding = page.locator("[data-testid=error]").inner_text()
    assert "3" in foutmelding, f"Foutmelding vermeldt verwacht aantal niet: {foutmelding!r}"


# ---------------------------------------------------------------------------
# RUNS-V-05 — mislukte run toont foutmelding voor die run, uitvoering gaat door
# ---------------------------------------------------------------------------

def test_ui_toont_foutmelding_voor_mislukte_run(page: Page):
    """Testcode: runs_en_temperature.validatie.07
    Dekt: RUNS-V-05 — als een run mislukt, toont de UI een foutmelding voor die specifieke run.
    """
    run_data = json.dumps({"runs": [
        {"run_nummer": 1, "fout": "Ollama niet bereikbaar"},
        {"run_nummer": 2, "temperature": 0.7, "response": "Antwoord run 2", "log_status": "ok"},
    ]})
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=run_data,
    ))
    page.locator("[data-testid=runs-input]").fill("2")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_be_visible()
    tekst = page.locator("[data-testid=run-results]").inner_text()
    assert "Ollama niet bereikbaar" in tekst or "fout" in tekst.lower(), (
        f"Foutmelding voor mislukte run ontbreekt: {tekst!r}"
    )


def test_ui_toont_geslaagde_run_ondanks_mislukte_run(page: Page):
    """Testcode: runs_en_temperature.validatie.08
    Dekt: RUNS-V-05 — na een mislukte run toont de UI het resultaat van de geslaagde run wél.
    """
    run_data = json.dumps({"runs": [
        {"run_nummer": 1, "fout": "Ollama niet bereikbaar"},
        {"run_nummer": 2, "temperature": 0.7, "response": "Antwoord run 2", "log_status": "ok"},
    ]})
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=run_data,
    ))
    page.locator("[data-testid=runs-input]").fill("2")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_be_visible()
    tekst = page.locator("[data-testid=run-results]").inner_text()
    assert "Antwoord run 2" in tekst, f"Resultaat van geslaagde run 2 ontbreekt: {tekst!r}"
