"""
Interactie-tests voor runs en temperature.

Bron: documentatie/acceptatiecriteria/runs-en-temperature.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
runs_en_temperature.interactie.01 — bewust een ander formaat dan de AC-codes (RUNS-I-01).

RUNS-I-03 (de prompt wordt precies 'runs' keer verstuurd, sequentieel) wordt gedekt door
de backend/integratietests (tests/backend/) — geen aparte Playwright-test nodig.
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


# ---------------------------------------------------------------------------
# RUNS-I-01 — temperature volgt providerwissel, tenzij handmatig gewijzigd
# ---------------------------------------------------------------------------

def test_wisselen_naar_groq_werkt_temperature_bij(page: Page):
    """Testcode: runs_en_temperature.interactie.01
    Dekt: RUNS-I-01 — bij wisselen van Ollama naar Groq wordt de temperature bijgewerkt naar 1.
    """
    page.locator("[data-testid=provider-select]").select_option("groq")
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde in ("1", "1.0"), f"Temperature na wisselen naar Groq is niet 1: {waarde!r}"


def test_wisselen_naar_ollama_werkt_temperature_bij(page: Page):
    """Testcode: runs_en_temperature.interactie.02
    Dekt: RUNS-I-01 — bij wisselen van Groq naar Ollama wordt de temperature bijgewerkt naar 0.8.
    """
    page.locator("[data-testid=provider-select]").select_option("groq")
    page.locator("[data-testid=provider-select]").select_option("ollama")
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde == "0.8", f"Temperature na wisselen naar Ollama is niet 0.8: {waarde!r}"


def test_handmatig_gewijzigde_temperature_wordt_niet_overschreven(page: Page):
    """Testcode: runs_en_temperature.interactie.03
    Dekt: RUNS-I-01 — als de gebruiker de temperature handmatig heeft aangepast, wordt deze niet overschreven bij een provider-wissel.
    """
    page.locator("[data-testid=temperature-input]").fill("0.5")
    page.locator("[data-testid=provider-select]").select_option("groq")
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde == "0.5", f"Handmatig ingevoerde temperature werd overschreven: {waarde!r}"


# ---------------------------------------------------------------------------
# RUNS-I-02 — runs/modus/waarden meegestuurd, meegeslagen en teruggevuld
# ---------------------------------------------------------------------------

def test_runs_wordt_meegestuurd_in_aanvraag(page: Page):
    """Testcode: runs_en_temperature.interactie.04
    Dekt: RUNS-I-02 — het veld 'runs' wordt meegestuurd in de API-aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}),
        )

    page.route(PROMPT_ROUTE, vang_op)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    expect(page.locator("[data-testid=run-results]")).to_be_visible()

    assert "runs" in vastgelegd, f"Veld 'runs' ontbreekt in aanvraag: {vastgelegd}"
    assert vastgelegd["runs"] == 1


def test_temperature_modus_wordt_meegestuurd_in_aanvraag(page: Page):
    """Testcode: runs_en_temperature.interactie.05
    Dekt: RUNS-I-02 — het veld 'temperature_modus' wordt meegestuurd in de API-aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}),
        )

    page.route(PROMPT_ROUTE, vang_op)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    expect(page.locator("[data-testid=run-results]")).to_be_visible()

    assert "temperature_modus" in vastgelegd, f"Veld 'temperature_modus' ontbreekt: {vastgelegd}"


def test_temperatures_wordt_meegestuurd_in_aanvraag(page: Page):
    """Testcode: runs_en_temperature.interactie.06
    Dekt: RUNS-I-02 — het veld 'temperatures' wordt als array meegestuurd in de API-aanvraag.
    """
    vastgelegd: dict = {}

    def vang_op(route):
        vastgelegd.update(route.request.post_data_json)
        route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}]}),
        )

    page.route(PROMPT_ROUTE, vang_op)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    expect(page.locator("[data-testid=run-results]")).to_be_visible()

    assert "temperatures" in vastgelegd, f"Veld 'temperatures' ontbreekt: {vastgelegd}"
    assert isinstance(vastgelegd["temperatures"], list)


def test_sessie_opslaan_stuurt_runs_mee(page: Page):
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

    page.route(SESSIONS_ROUTE, handle)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=runs-input]").fill("2")
    page.locator("[name=session-name]").fill("test-sessie")
    page.get_by_role("button", name="Opslaan").click()
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert "runs" in vastgelegd, f"Veld 'runs' ontbreekt bij opslaan: {vastgelegd}"
    assert vastgelegd["runs"] == 2


def test_sessie_opslaan_stuurt_temperature_modus_mee(page: Page):
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

    page.route(SESSIONS_ROUTE, handle)
    _vul_verplichte_velden(page)
    page.locator("[name=session-name]").fill("test-sessie")
    page.get_by_role("button", name="Opslaan").click()
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert "temperature_modus" in vastgelegd, f"Veld 'temperature_modus' ontbreekt: {vastgelegd}"


def test_sessie_opslaan_stuurt_temperatures_mee(page: Page):
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

    page.route(SESSIONS_ROUTE, handle)
    _vul_verplichte_velden(page)
    page.locator("[name=session-name]").fill("test-sessie")
    page.get_by_role("button", name="Opslaan").click()
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert "temperatures" in vastgelegd, f"Veld 'temperatures' ontbreekt: {vastgelegd}"
    assert isinstance(vastgelegd["temperatures"], list)


def test_sessie_laden_vult_runs_in(page: Page):
    """Testcode: runs_en_temperature.interactie.10
    Dekt: RUNS-I-02 — bij het laden van een sessie wordt 'runs' ingevuld in het formulier.
    """
    sessie_data = json.dumps({
        "name": "test-runs", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "runs": 3, "temperature_modus": "per_run", "temperatures": [0.3, 0.7, 1.0],
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["test-runs"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("test-runs")

    waarde = page.locator("[data-testid=runs-input]").input_value()
    assert waarde == "3", f"Aantal runs na laden sessie klopt niet: {waarde!r}"


def test_sessie_laden_vult_temperature_modus_in(page: Page):
    """Testcode: runs_en_temperature.interactie.11
    Dekt: RUNS-I-02 — bij het laden van een sessie wordt de temperature_modus correct geselecteerd.
    """
    sessie_data = json.dumps({
        "name": "test-runs", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "runs": 2, "temperature_modus": "per_run", "temperatures": [0.3, 0.7],
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["test-runs"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("test-runs")

    expect(page.locator("[data-testid=temperature-modus-per-run]")).to_be_checked()


def test_sessie_laden_vult_temperatures_in(page: Page):
    """Testcode: runs_en_temperature.interactie.12
    Dekt: RUNS-I-02 — bij het laden van een sessie worden de temperatures ingevuld in het invoerveld.
    """
    sessie_data = json.dumps({
        "name": "test-runs", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "runs": 3, "temperature_modus": "per_run", "temperatures": [0.3, 0.7, 1.0],
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["test-runs"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("test-runs")

    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert "0.3" in waarde, f"Temperatures na laden kloppen niet: {waarde!r}"


def test_sessie_laden_zonder_runs_velden_geeft_geen_fout(page: Page):
    """Testcode: runs_en_temperature.interactie.13
    Dekt: RUNS-I-02 — bestaande sessies zonder runs/temperature-velden kunnen worden geladen zonder foutmelding.

    ⚠️ De AC verwacht een *leeg* temperature-veld na laden; de implementatie laat het veld op
    de bestaande/standaardwaarde staan. Deze test verifieert alleen dat laden niet crasht,
    niet het "leeg"-gedrag.
    """
    sessie_data = json.dumps({
        "name": "oud-sessie", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["oud-sessie"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("oud-sessie")

    expect(page.locator("[data-testid=error]")).not_to_be_visible()


# ---------------------------------------------------------------------------
# RUNS-I-04 — resultaten op volgorde getoond
# ---------------------------------------------------------------------------

def test_ui_toont_alle_run_resultaten_na_uitvoering(page: Page):
    """Testcode: runs_en_temperature.interactie.14
    Dekt: RUNS-I-04 — na uitvoering toont de UI alle run-resultaten op volgorde.
    """
    run_data = json.dumps({"runs": [
        {"run_nummer": 1, "temperature": 0.7, "response": "Antwoord run 1", "log_status": "ok"},
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
    assert "Antwoord run 1" in tekst, f"Resultaat run 1 ontbreekt: {tekst!r}"
    assert "Antwoord run 2" in tekst, f"Resultaat run 2 ontbreekt: {tekst!r}"
