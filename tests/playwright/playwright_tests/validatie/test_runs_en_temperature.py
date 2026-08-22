"""
Validatie-tests voor runs en temperature.

Bron: documentatie/acceptatiecriteria/runs-en-temperature.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
runs_en_temperature.validatie.01 — bewust een ander formaat dan de AC-codes (RUNS-V-01).
"""
import pytest
from playwright.sync_api import Page

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
# RUNS-V-01 — runs < 1
# ---------------------------------------------------------------------------

def test_runs_nul_toont_foutmelding_en_verstuurt_niet(app: PromptPage):
    """Testcode: runs_en_temperature.validatie.01
    Dekt: RUNS-V-01 — bij runs=0 toont de UI een foutmelding en wordt de aanvraag niet verstuurd.
    """
    calls = []
    app.page.route(PROMPT_ROUTE, lambda route: (calls.append(route) or route.abort()))

    app.fill_runs(0)
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_error_zichtbaar()
    assert len(calls) == 0, "Er mag geen aanvraag zijn verstuurd bij runs=0"


# ---------------------------------------------------------------------------
# RUNS-V-02 — temperature verplicht
# ---------------------------------------------------------------------------

def test_temperature_leeg_toont_foutmelding_en_verstuurt_niet(app: PromptPage):
    """Testcode: runs_en_temperature.validatie.02
    Dekt: RUNS-V-02 — bij een lege temperature toont de UI een foutmelding en wordt de aanvraag niet verstuurd.
    """
    calls = []
    app.page.route(PROMPT_ROUTE, lambda route: (calls.append(route) or route.abort()))

    app.fill_temperature("")
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_error_zichtbaar()
    assert len(calls) == 0, "Er mag geen aanvraag zijn verstuurd bij lege temperature"


# ---------------------------------------------------------------------------
# RUNS-V-03 — temperature buiten 0.0–2.0
# ---------------------------------------------------------------------------

def test_temperature_buiten_bereik_toont_foutmelding(app: PromptPage):
    """Testcode: runs_en_temperature.validatie.03
    Dekt: RUNS-V-03 — bij een temperature buiten 0–2 toont de UI een foutmelding.
    """
    app.fill_temperature("2.5")
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_error_zichtbaar()


def test_temperature_foutmelding_noemt_bereik(app: PromptPage):
    """Testcode: runs_en_temperature.validatie.04
    Dekt: RUNS-V-03 — de foutmelding bij een ongeldige temperature vermeldt het geldige bereik (0 en 2).
    """
    app.fill_temperature("3.0")
    app.vul_verplichte_velden()
    app.verstuur()

    foutmelding = app.error.inner_text()
    assert "0" in foutmelding and "2" in foutmelding, (
        f"Foutmelding vermeldt bereik niet: {foutmelding!r}"
    )


# ---------------------------------------------------------------------------
# RUNS-V-04 — mismatch aantal temperatures in modus per_run
# ---------------------------------------------------------------------------

def test_per_run_mismatch_toont_foutmelding(app: PromptPage):
    """Testcode: runs_en_temperature.validatie.05
    Dekt: RUNS-V-04 — in modus 'per_run' met verkeerd aantal temperatures toont de UI een foutmelding.
    """
    app.fill_runs(3)
    app.kies_temperature_modus_per_run()
    app.fill_temperature("0.3, 0.7")
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_error_zichtbaar()


def test_per_run_mismatch_foutmelding_noemt_verwacht_aantal(app: PromptPage):
    """Testcode: runs_en_temperature.validatie.06
    Dekt: RUNS-V-04 — de foutmelding bij een per_run-mismatch vermeldt het verwachte aantal temperatures.
    """
    app.fill_runs(3)
    app.kies_temperature_modus_per_run()
    app.fill_temperature("0.3, 0.7")
    app.vul_verplichte_velden()
    app.verstuur()

    foutmelding = app.error.inner_text()
    assert "3" in foutmelding, f"Foutmelding vermeldt verwacht aantal niet: {foutmelding!r}"


# ---------------------------------------------------------------------------
# RUNS-V-05 — mislukte run toont foutmelding voor die run, uitvoering gaat door
# ---------------------------------------------------------------------------

def test_ui_toont_foutmelding_voor_mislukte_run(app: PromptPage):
    """Testcode: runs_en_temperature.validatie.07
    Dekt: RUNS-V-05 — als een run mislukt, toont de UI een foutmelding voor die specifieke run.
    """
    stub_prompt_response(app.page, runs=[
        {"run_nummer": 1, "fout": "Ollama niet bereikbaar"},
        {"run_nummer": 2, "temperature": 0.7, "response": "Antwoord run 2", "log_status": "ok"},
    ])
    app.fill_runs(2)
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_run_results_zichtbaar()
    tekst = app.run_results.inner_text()
    assert "Ollama niet bereikbaar" in tekst or "fout" in tekst.lower(), (
        f"Foutmelding voor mislukte run ontbreekt: {tekst!r}"
    )


def test_ui_toont_geslaagde_run_ondanks_mislukte_run(app: PromptPage):
    """Testcode: runs_en_temperature.validatie.08
    Dekt: RUNS-V-05 — na een mislukte run toont de UI het resultaat van de geslaagde run wél.
    """
    stub_prompt_response(app.page, runs=[
        {"run_nummer": 1, "fout": "Ollama niet bereikbaar"},
        {"run_nummer": 2, "temperature": 0.7, "response": "Antwoord run 2", "log_status": "ok"},
    ])
    app.fill_runs(2)
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_run_results_zichtbaar()
    app.expect_run_results_bevat("Antwoord run 2")
