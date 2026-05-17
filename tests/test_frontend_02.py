"""
Frontend-tests voor story 02: prompt samenstellen via acht velden.

Vereist: de app draait op http://localhost:3000 (python app.py).

AC gedekt:
- Formulier toont acht invulvelden met labels en placeholders
- Losse textarea uit story 01 is verdwenen
- Verplichte velden (rol, taak, doel) tonen elk een eigen validatiemelding als ze leeg zijn
- Geen API-call zolang een verplicht veld leeg is
- Antwoord verschijnt na correct invullen van de verplichte velden
- Achterwaartse compat: laadstatus en Ollama-503 blijven werken
"""
import time
import threading
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"
OLLAMA_ROUTE = "**/api/prompt"

VERPLICHTE_VELDEN = ("rol", "taak", "doel")
ALLE_VELDEN = ("rol", "taak", "doel", "formaat", "stijl", "scope", "eisen", "voorbeelden")


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.goto(BASE_URL)


# ---------------------------------------------------------------------------
# Formulierstructuur
# ---------------------------------------------------------------------------

def test_alle_acht_velden_zijn_zichtbaar(page: Page):
    """Elk van de acht velden heeft een zichtbaar invoerveld."""
    for veld in ALLE_VELDEN:
        locator = page.locator(f"[name={veld}]")
        expect(locator).to_be_visible()


def test_elk_veld_heeft_een_label(page: Page):
    """Elk veld is gekoppeld aan een zichtbaar label."""
    for veld in ALLE_VELDEN:
        label = page.locator(f"label[for={veld}]")
        expect(label).to_be_visible()


def test_elk_veld_heeft_een_placeholder(page: Page):
    """Elk veld heeft een niet-lege placeholder als invulhulp."""
    for veld in ALLE_VELDEN:
        locator = page.locator(f"[name={veld}]")
        placeholder = locator.get_attribute("placeholder")
        assert placeholder, f"Veld '{veld}' heeft geen placeholder"


def test_losse_textarea_is_verdwenen(page: Page):
    """De enkelvoudige textarea uit story 01 is niet meer aanwezig."""
    expect(page.locator("textarea#prompt")).not_to_be_visible()


# ---------------------------------------------------------------------------
# Validatie verplichte velden
# ---------------------------------------------------------------------------

def _vul_verplichte_velden(page: Page, uitzondering: str | None = None):
    waarden = {"rol": "senior developer", "taak": "een API ontwerpen", "doel": "data op te slaan"}
    for veld, waarde in waarden.items():
        if veld != uitzondering:
            page.locator(f"[name={veld}]").fill(waarde)


def test_leeg_rol_toont_validatiemelding(page: Page):
    """Versturen met leeg veld rol toont een validatiemelding voor rol."""
    calls = []
    page.route(OLLAMA_ROUTE, lambda route: calls.append(route) or route.abort())

    _vul_verplichte_velden(page, uitzondering="rol")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-rol]")).to_be_visible()
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_lege_taak_toont_validatiemelding(page: Page):
    """Versturen met leeg veld taak toont een validatiemelding voor taak."""
    calls = []
    page.route(OLLAMA_ROUTE, lambda route: calls.append(route) or route.abort())

    _vul_verplichte_velden(page, uitzondering="taak")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-taak]")).to_be_visible()
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_leeg_doel_toont_validatiemelding(page: Page):
    """Versturen met leeg veld doel toont een validatiemelding voor doel."""
    calls = []
    page.route(OLLAMA_ROUTE, lambda route: calls.append(route) or route.abort())

    _vul_verplichte_velden(page, uitzondering="doel")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-doel]")).to_be_visible()
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_meerdere_lege_verplichte_velden_tonen_elk_een_melding(page: Page):
    """Als alle drie verplichte velden leeg zijn, verschijnt voor elk een eigen melding."""
    calls = []
    page.route(OLLAMA_ROUTE, lambda route: calls.append(route) or route.abort())

    page.get_by_role("button", name="Verstuur").click()

    for veld in VERPLICHTE_VELDEN:
        expect(page.locator(f"[data-testid=validation-{veld}]")).to_be_visible()
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


# ---------------------------------------------------------------------------
# Versturen en antwoord ontvangen
# ---------------------------------------------------------------------------

def test_antwoord_verschijnt_na_correct_invullen(page: Page):
    """Antwoord van Ollama verschijnt nadat alle verplichte velden zijn ingevuld."""
    page.route(
        OLLAMA_ROUTE,
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


def test_optionele_velden_worden_meegestuurd_in_api_call(page: Page):
    """Ingevulde optionele velden zijn aanwezig in het verstuurde JSON-body."""
    captured_body = {}

    def inspect_route(route):
        captured_body.update(route.request.post_data_json)
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"runs": [{"run_nummer": 1, "temperature": 0.8, "response": "ok"}]}',
        )

    page.route(OLLAMA_ROUTE, inspect_route)
    _vul_verplichte_velden(page)
    page.locator("[name=formaat]").fill("markdown")
    page.get_by_role("button", name="Verstuur").click()

    page.wait_for_selector("[data-testid=run-results]")
    assert captured_body.get("formaat") == "markdown"


# ---------------------------------------------------------------------------
# Achterwaartse compatibiliteit (story 01)
# ---------------------------------------------------------------------------

def test_laadstatus_zichtbaar_tijdens_wachten(page: Page):
    """Achterwaartse compat story 01: laadstatus verschijnt direct na versturen."""

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

    page.route(OLLAMA_ROUTE, trage_response)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=loading]")).to_be_visible()


def test_ollama_fout_toont_foutmelding(page: Page):
    """Achterwaartse compat story 01: Ollama-503 toont een foutmelding."""
    page.route(
        OLLAMA_ROUTE,
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"detail": "Ollama is niet bereikbaar"}',
        ),
    )
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()
    expect(page.locator("[data-testid=error]")).not_to_be_empty()
