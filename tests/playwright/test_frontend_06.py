"""
Frontend-tests voor story 06: Aantal runs en temperature per run.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.

AC gedekt:
- De UI toont een invoerveld 'Aantal runs' met standaardwaarde 1
- De UI toont een keuzeschakelaar (radio/toggle) voor temperature-modus
- Temperature-invoerveld wordt vooraf ingevuld met de standaard van de geselecteerde provider
  (Ollama: 0.8, Groq: 1)
- Bij wisselen van provider wordt de temperature bijgewerkt, tenzij handmatig gewijzigd
- De UI toont een verplicht-aanduiding bij het temperature-veld
- Alle drie velden ('runs', temperature-modus, temperature-waarde) worden meegestuurd bij uitvoeren
- Alle drie velden worden meegeslagen bij sessie-opslaan
- Bij laden van een sessie worden de velden automatisch ingevuld
- Validatie: runs < 1 → foutmelding, geen aanvraag
- Validatie: temperature leeg → foutmelding, geen aanvraag
- Validatie: temperature buiten 0–2 → foutmelding, geen aanvraag
- Validatie: per_run-modus met mismatch → foutmelding, geen aanvraag
- Na uitvoering toont de UI alle run-resultaten op volgorde
- Bij een mislukte run toont de UI een foutmelding voor die run
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


def _stub_runs_response(page: Page, runs: int = 1, temperature: float = 0.8):
    """Stubbt /api/prompt met een succesvolle multi-run response."""
    run_results = [
        {"run_nummer": i, "temperature": temperature, "response": f"Antwoord run {i}", "log_status": "ok"}
        for i in range(1, runs + 1)
    ]
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"runs": run_results}),
    ))


# ---------------------------------------------------------------------------
# UI structuur
# ---------------------------------------------------------------------------

def test_runs_invoerveld_is_zichtbaar(page: Page):
    """Dekt: TD-06-01 — de UI toont een invoerveld voor 'Aantal runs'."""
    expect(page.locator("[data-testid=runs-input]")).to_be_visible()


def test_runs_standaardwaarde_is_1(page: Page):
    """Dekt: TD-06-02 — het invoerveld 'Aantal runs' heeft als standaardwaarde 1."""
    waarde = page.locator("[data-testid=runs-input]").input_value()
    assert waarde == "1", f"Standaard runs is niet 1: {waarde!r}"


def test_temperature_modus_schakelaar_is_zichtbaar(page: Page):
    """Dekt: TD-06-03 — de UI toont een keuzeschakelaar voor de temperature-modus."""
    expect(page.locator("[data-testid=temperature-modus]")).to_be_visible()


def test_temperature_modus_heeft_optie_alle(page: Page):
    """Dekt: TD-06-04 — de schakelaar heeft een optie voor 'één temperature voor alle runs'."""
    expect(page.locator("[data-testid=temperature-modus-alle]")).to_be_visible()


def test_temperature_modus_heeft_optie_per_run(page: Page):
    """Dekt: TD-06-05 — de schakelaar heeft een optie voor 'één temperature per run'."""
    expect(page.locator("[data-testid=temperature-modus-per-run]")).to_be_visible()


def test_temperature_invoerveld_is_zichtbaar(page: Page):
    """Dekt: TD-06-06 — de UI toont een invoerveld voor de temperature."""
    expect(page.locator("[data-testid=temperature-input]")).to_be_visible()


# ---------------------------------------------------------------------------
# Standaard temperature per provider
# ---------------------------------------------------------------------------

def test_ollama_temperature_standaard_is_0_punt_8(page: Page):
    """Dekt: TD-06-07 — bij provider Ollama is de temperature vooraf ingevuld met 0.8."""
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde == "0.8", f"Standaard temperature voor Ollama is niet 0.8: {waarde!r}"


def test_groq_temperature_standaard_is_1(page: Page):
    """Dekt: TD-06-08 — bij provider Groq is de temperature vooraf ingevuld met 1."""
    page.locator("[data-testid=provider-select]").select_option("groq")
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde in ("1", "1.0"), f"Standaard temperature voor Groq is niet 1: {waarde!r}"


def test_wisselen_naar_groq_werkt_temperature_bij(page: Page):
    """Dekt: TD-06-09 — bij wisselen van Ollama naar Groq wordt de temperature bijgewerkt naar 1."""
    page.locator("[data-testid=provider-select]").select_option("groq")
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde in ("1", "1.0"), f"Temperature na wisselen naar Groq is niet 1: {waarde!r}"


def test_wisselen_naar_ollama_werkt_temperature_bij(page: Page):
    """Dekt: TD-06-10 — bij wisselen van Groq naar Ollama wordt de temperature bijgewerkt naar 0.8."""
    page.locator("[data-testid=provider-select]").select_option("groq")
    page.locator("[data-testid=provider-select]").select_option("ollama")
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde == "0.8", f"Temperature na wisselen naar Ollama is niet 0.8: {waarde!r}"


def test_handmatig_gewijzigde_temperature_wordt_niet_overschreven(page: Page):
    """Dekt: TD-06-11 — als de gebruiker de temperature handmatig heeft aangepast, wordt deze niet overschreven bij een provider-wissel."""
    page.locator("[data-testid=temperature-input]").fill("0.5")
    page.locator("[data-testid=provider-select]").select_option("groq")
    waarde = page.locator("[data-testid=temperature-input]").input_value()
    assert waarde == "0.5", f"Handmatig ingevoerde temperature werd overschreven: {waarde!r}"


# ---------------------------------------------------------------------------
# Verplicht-aanduiding temperature
# ---------------------------------------------------------------------------

def test_temperature_label_heeft_verplicht_aanduiding(page: Page):
    """Dekt: TD-06-12 — de UI toont bij het temperature-veld een aanduiding dat het verplicht is (bijv. *)."""
    label_tekst = page.locator("[data-testid=temperature-label]").inner_text()
    assert "*" in label_tekst or "Verplicht" in label_tekst, (
        f"Geen verplicht-aanduiding gevonden in het temperature-label: {label_tekst!r}"
    )


# ---------------------------------------------------------------------------
# Velden meegestuurd in aanvraag
# ---------------------------------------------------------------------------

def test_runs_wordt_meegestuurd_in_aanvraag(page: Page):
    """Dekt: TD-06-13 — het veld 'runs' wordt meegestuurd in de API-aanvraag."""
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

    assert "runs" in vastgelegd, f"Veld 'runs' ontbreekt in aanvraag: {vastgelegd}"
    assert vastgelegd["runs"] == 1


def test_temperature_modus_wordt_meegestuurd_in_aanvraag(page: Page):
    """Dekt: TD-06-13 — het veld 'temperature_modus' wordt meegestuurd in de API-aanvraag."""
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

    assert "temperature_modus" in vastgelegd, f"Veld 'temperature_modus' ontbreekt: {vastgelegd}"


def test_temperatures_wordt_meegestuurd_in_aanvraag(page: Page):
    """Dekt: TD-06-13 — het veld 'temperatures' wordt als array meegestuurd in de API-aanvraag."""
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

    assert "temperatures" in vastgelegd, f"Veld 'temperatures' ontbreekt: {vastgelegd}"
    assert isinstance(vastgelegd["temperatures"], list)


# ---------------------------------------------------------------------------
# Validatie in de UI
# ---------------------------------------------------------------------------

def test_runs_nul_toont_foutmelding_en_verstuurt_niet(page: Page):
    """Dekt: TD-06-17 — bij runs=0 toont de UI een foutmelding en wordt de aanvraag niet verstuurd."""
    calls = []
    page.route(PROMPT_ROUTE, lambda route: (calls.append(route) or route.abort()))

    page.locator("[data-testid=runs-input]").fill("0")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()
    assert len(calls) == 0, "Er mag geen aanvraag zijn verstuurd bij runs=0"


def test_temperature_leeg_toont_foutmelding_en_verstuurt_niet(page: Page):
    """Dekt: TD-06-18 — bij een lege temperature toont de UI een foutmelding en wordt de aanvraag niet verstuurd."""
    calls = []
    page.route(PROMPT_ROUTE, lambda route: (calls.append(route) or route.abort()))

    page.locator("[data-testid=temperature-input]").fill("")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()
    assert len(calls) == 0, "Er mag geen aanvraag zijn verstuurd bij lege temperature"


def test_temperature_buiten_bereik_toont_foutmelding(page: Page):
    """Dekt: TD-06-19 — bij een temperature buiten 0–2 toont de UI een foutmelding."""
    page.locator("[data-testid=temperature-input]").fill("2.5")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()


def test_temperature_foutmelding_noemt_bereik(page: Page):
    """Dekt: TD-06-19 — de foutmelding bij een ongeldige temperature vermeldt het geldige bereik (0 en 2)."""
    page.locator("[data-testid=temperature-input]").fill("3.0")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    foutmelding = page.locator("[data-testid=error]").inner_text()
    assert "0" in foutmelding and "2" in foutmelding, (
        f"Foutmelding vermeldt bereik niet: {foutmelding!r}"
    )


def test_per_run_mismatch_toont_foutmelding(page: Page):
    """Dekt: TD-06-20 — in modus 'per_run' met verkeerd aantal temperatures toont de UI een foutmelding."""
    page.locator("[data-testid=runs-input]").fill("3")
    page.locator("[data-testid=temperature-modus-per-run]").click()
    page.locator("[data-testid=temperature-input]").fill("0.3, 0.7")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()


def test_per_run_mismatch_foutmelding_noemt_verwacht_aantal(page: Page):
    """Dekt: TD-06-20 — de foutmelding bij een per_run-mismatch vermeldt het verwachte aantal temperatures."""
    page.locator("[data-testid=runs-input]").fill("3")
    page.locator("[data-testid=temperature-modus-per-run]").click()
    page.locator("[data-testid=temperature-input]").fill("0.3, 0.7")
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    foutmelding = page.locator("[data-testid=error]").inner_text()
    assert "3" in foutmelding, f"Foutmelding vermeldt verwacht aantal niet: {foutmelding!r}"


# ---------------------------------------------------------------------------
# UI toont run-resultaten
# ---------------------------------------------------------------------------

def test_ui_toont_alle_run_resultaten_na_uitvoering(page: Page):
    """Dekt: TD-06-16 — na uitvoering toont de UI alle run-resultaten op volgorde."""
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


def test_ui_toont_foutmelding_voor_mislukte_run(page: Page):
    """Dekt: TD-06-22 — als een run mislukt, toont de UI een foutmelding voor die specifieke run."""
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
    """Dekt: TD-06-22 — na een mislukte run toont de UI het resultaat van de geslaagde run wél."""
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


# ---------------------------------------------------------------------------
# Sessie opslaan en laden
# ---------------------------------------------------------------------------

def test_sessie_opslaan_stuurt_runs_mee(page: Page):
    """Dekt: TD-06-14 — bij het opslaan van een sessie wordt 'runs' meegestuurd in het verzoek."""
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
    """Dekt: TD-06-14 — bij het opslaan van een sessie wordt 'temperature_modus' meegestuurd."""
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
    """Dekt: TD-06-14 — bij het opslaan van een sessie wordt 'temperatures' meegestuurd."""
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
    """Dekt: TD-06-15 — bij het laden van een sessie wordt 'runs' ingevuld in het formulier."""
    sessie_data = json.dumps({
        "name": "test-runs",
        "provider": "ollama",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "runs": 3,
        "temperature_modus": "per_run",
        "temperatures": [0.3, 0.7, 1.0],
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
    """Dekt: TD-06-15 — bij het laden van een sessie wordt de temperature_modus correct geselecteerd."""
    sessie_data = json.dumps({
        "name": "test-runs",
        "provider": "ollama",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "runs": 2,
        "temperature_modus": "per_run",
        "temperatures": [0.3, 0.7],
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
    """Dekt: TD-06-15 — bij het laden van een sessie worden de temperatures ingevuld in het invoerveld."""
    sessie_data = json.dumps({
        "name": "test-runs",
        "provider": "ollama",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "runs": 3,
        "temperature_modus": "per_run",
        "temperatures": [0.3, 0.7, 1.0],
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
    """Dekt: TD-06-21 — bestaande sessies zonder runs/temperature-velden kunnen worden geladen zonder foutmelding."""
    sessie_data = json.dumps({
        "name": "oud-sessie",
        "provider": "ollama",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
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
