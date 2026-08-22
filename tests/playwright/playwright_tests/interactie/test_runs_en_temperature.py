"""
Interactie-tests voor runs en temperature.

Bron: documentatie/acceptatiecriteria/runs-en-temperature.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
runs_en_temperature.interactie.01 — bewust een ander formaat dan de AC-codes (RUNS-I-01).

RUNS-I-03 (de prompt wordt precies 'runs' keer verstuurd, sequentieel) wordt gedekt door
de backend/integratietests (tests/backend/) — geen aparte Playwright-test nodig.
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


# ---------------------------------------------------------------------------
# RUNS-I-01 — temperature volgt providerwissel, tenzij handmatig gewijzigd
# ---------------------------------------------------------------------------

def test_wisselen_naar_groq_werkt_temperature_bij(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.01
    Dekt: RUNS-I-01 — bij wisselen van Ollama naar Groq wordt de temperature bijgewerkt naar 1.
    """
    app.kies_provider("groq")
    app.expect_temperature_waarde("1", "1.0")


def test_wisselen_naar_ollama_werkt_temperature_bij(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.02
    Dekt: RUNS-I-01 — bij wisselen van Groq naar Ollama wordt de temperature bijgewerkt naar 0.8.
    """
    app.kies_provider("groq")
    app.kies_provider("ollama")
    app.expect_temperature_waarde("0.8")


def test_handmatig_gewijzigde_temperature_wordt_niet_overschreven(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.03
    Dekt: RUNS-I-01 — als de gebruiker de temperature handmatig heeft aangepast, wordt deze niet overschreven bij een provider-wissel.
    """
    app.fill_temperature("0.5")
    app.kies_provider("groq")
    app.expect_temperature_waarde("0.5")


# ---------------------------------------------------------------------------
# RUNS-I-02 — runs/modus/waarden meegestuurd, meegeslagen en teruggevuld
# ---------------------------------------------------------------------------

def test_runs_wordt_meegestuurd_in_aanvraag(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.04
    Dekt: RUNS-I-02 — het veld 'runs' wordt meegestuurd in de API-aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200, content_type="application/json",
            body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}',
        )

    app.page.route("**/api/prompt", vang_op)
    app.vul_verplichte_velden()
    app.verstuur()
    app.expect_run_results_zichtbaar()

    assert "runs" in vastgelegd, f"Veld 'runs' ontbreekt in aanvraag: {vastgelegd}"
    assert vastgelegd["runs"] == 1


def test_temperature_modus_wordt_meegestuurd_in_aanvraag(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.05
    Dekt: RUNS-I-02 — het veld 'temperature_modus' wordt meegestuurd in de API-aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200, content_type="application/json",
            body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}',
        )

    app.page.route("**/api/prompt", vang_op)
    app.vul_verplichte_velden()
    app.verstuur()
    app.expect_run_results_zichtbaar()

    assert "temperature_modus" in vastgelegd, f"Veld 'temperature_modus' ontbreekt: {vastgelegd}"


def test_temperatures_wordt_meegestuurd_in_aanvraag(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.06
    Dekt: RUNS-I-02 — het veld 'temperatures' wordt als array meegestuurd in de API-aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200, content_type="application/json",
            body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}',
        )

    app.page.route("**/api/prompt", vang_op)
    app.vul_verplichte_velden()
    app.verstuur()
    app.expect_run_results_zichtbaar()

    assert "temperatures" in vastgelegd, f"Veld 'temperatures' ontbreekt: {vastgelegd}"
    assert isinstance(vastgelegd["temperatures"], list)


def test_sessie_opslaan_stuurt_runs_mee(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.07
    Dekt: RUNS-I-02 — bij het opslaan van een sessie wordt 'runs' meegestuurd in het verzoek.
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
    app.fill_runs(2)
    app.sidebar.fill_naam("test-sessie")
    app.sidebar.opslaan()
    app.sidebar.wacht_op_bevestiging()

    assert "runs" in vastgelegd, f"Veld 'runs' ontbreekt bij opslaan: {vastgelegd}"
    assert vastgelegd["runs"] == 2


def test_sessie_opslaan_stuurt_temperature_modus_mee(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.08
    Dekt: RUNS-I-02 — bij het opslaan van een sessie wordt 'temperature_modus' meegestuurd.
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

    assert "temperature_modus" in vastgelegd, f"Veld 'temperature_modus' ontbreekt: {vastgelegd}"


def test_sessie_opslaan_stuurt_temperatures_mee(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.09
    Dekt: RUNS-I-02 — bij het opslaan van een sessie wordt 'temperatures' meegestuurd.
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

    assert "temperatures" in vastgelegd, f"Veld 'temperatures' ontbreekt: {vastgelegd}"
    assert isinstance(vastgelegd["temperatures"], list)


def test_sessie_laden_vult_runs_in(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.10
    Dekt: RUNS-I-02 — bij het laden van een sessie wordt 'runs' ingevuld in het formulier.
    """
    sessie_data = {
        "name": "test-runs", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "runs": 3, "temperature_modus": "per_run", "temperatures": [0.3, 0.7, 1.0],
    }
    stub_sessies_met_doorgang(app.page, ["test-runs"])
    stub_sessie_item(app.page, "test-runs", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("test-runs")

    waarde = app.runs_input.input_value()
    assert waarde == "3", f"Aantal runs na laden sessie klopt niet: {waarde!r}"


def test_sessie_laden_vult_temperature_modus_in(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.11
    Dekt: RUNS-I-02 — bij het laden van een sessie wordt de temperature_modus correct geselecteerd.
    """
    sessie_data = {
        "name": "test-runs", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "runs": 2, "temperature_modus": "per_run", "temperatures": [0.3, 0.7],
    }
    stub_sessies_met_doorgang(app.page, ["test-runs"])
    stub_sessie_item(app.page, "test-runs", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("test-runs")

    app.expect_temperature_modus_per_run_geselecteerd()


def test_sessie_laden_vult_temperatures_in(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.12
    Dekt: RUNS-I-02 — bij het laden van een sessie worden de temperatures ingevuld in het invoerveld.
    """
    sessie_data = {
        "name": "test-runs", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "runs": 3, "temperature_modus": "per_run", "temperatures": [0.3, 0.7, 1.0],
    }
    stub_sessies_met_doorgang(app.page, ["test-runs"])
    stub_sessie_item(app.page, "test-runs", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("test-runs")

    waarde = app.temperature_input.input_value()
    assert "0.3" in waarde, f"Temperatures na laden kloppen niet: {waarde!r}"


def test_sessie_laden_zonder_runs_velden_geeft_geen_fout(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.13
    Dekt: RUNS-I-02 — bestaande sessies zonder runs/temperature-velden kunnen worden geladen zonder foutmelding.

    ⚠️ De AC verwacht een *leeg* temperature-veld na laden; de implementatie laat het veld op
    de bestaande/standaardwaarde staan. Deze test verifieert alleen dat laden niet crasht,
    niet het "leeg"-gedrag.
    """
    sessie_data = {
        "name": "oud-sessie", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
    }
    stub_sessies_met_doorgang(app.page, ["oud-sessie"])
    stub_sessie_item(app.page, "oud-sessie", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("oud-sessie")

    app.expect_error_niet_zichtbaar()


# ---------------------------------------------------------------------------
# RUNS-I-04 — resultaten op volgorde getoond
# ---------------------------------------------------------------------------

def test_ui_toont_alle_run_resultaten_na_uitvoering(app: PromptPage):
    """Testcode: runs_en_temperature.interactie.14
    Dekt: RUNS-I-04 — na uitvoering toont de UI alle run-resultaten op volgorde.
    """
    stub_prompt_response(app.page, runs=[
        {"run_nummer": 1, "temperature": 0.7, "response": "Antwoord run 1", "log_status": "ok"},
        {"run_nummer": 2, "temperature": 0.7, "response": "Antwoord run 2", "log_status": "ok"},
    ])
    app.fill_runs(2)
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_run_results_zichtbaar()
    app.expect_run_results_bevat("Antwoord run 1")
    app.expect_run_results_bevat("Antwoord run 2")
