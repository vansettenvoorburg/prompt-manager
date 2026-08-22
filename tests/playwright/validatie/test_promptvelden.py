"""
Validatie-tests voor promptvelden.

Bron: documentatie/acceptatiecriteria/promptvelden.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
promptvelden.validatie.01 — bewust een ander formaat dan de AC-codes (PROMPTVELDEN-V-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

PROMPT_ROUTE = "**/api/prompt"
VERPLICHTE_VELDEN = ("rol", "taak", "doel")


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.goto(BASE_URL)


def _vul_verplichte_velden(page: Page, uitzondering: str | None = None):
    waarden = {"rol": "senior developer", "taak": "een API ontwerpen", "doel": "data op te slaan"}
    for veld, waarde in waarden.items():
        if veld != uitzondering:
            page.locator(f"[name={veld}]").fill(waarde)


# ---------------------------------------------------------------------------
# PROMPTVELDEN-V-01 — leeg verplicht veld toont validatiemelding, geen API-call
# ---------------------------------------------------------------------------

def test_leeg_rol_toont_validatiemelding(page: Page):
    """Testcode: promptvelden.validatie.01
    Dekt: PROMPTVELDEN-V-01 — versturen met leeg veld rol toont een validatiemelding voor rol.
    """
    calls = []
    page.route(PROMPT_ROUTE, lambda route: calls.append(route) or route.abort())

    _vul_verplichte_velden(page, uitzondering="rol")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-rol]")).to_be_visible()
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_lege_taak_toont_validatiemelding(page: Page):
    """Testcode: promptvelden.validatie.02
    Dekt: PROMPTVELDEN-V-01 — versturen met leeg veld taak toont een validatiemelding voor taak.
    """
    calls = []
    page.route(PROMPT_ROUTE, lambda route: calls.append(route) or route.abort())

    _vul_verplichte_velden(page, uitzondering="taak")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-taak]")).to_be_visible()
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_leeg_doel_toont_validatiemelding(page: Page):
    """Testcode: promptvelden.validatie.03
    Dekt: PROMPTVELDEN-V-01 — versturen met leeg veld doel toont een validatiemelding voor doel.
    """
    calls = []
    page.route(PROMPT_ROUTE, lambda route: calls.append(route) or route.abort())

    _vul_verplichte_velden(page, uitzondering="doel")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-doel]")).to_be_visible()
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_meerdere_lege_verplichte_velden_tonen_elk_een_melding(page: Page):
    """Testcode: promptvelden.validatie.04
    Dekt: PROMPTVELDEN-V-01 — als alle drie verplichte velden leeg zijn, verschijnt voor elk een eigen melding.
    """
    calls = []
    page.route(PROMPT_ROUTE, lambda route: calls.append(route) or route.abort())

    page.get_by_role("button", name="Verstuur").click()

    for veld in VERPLICHTE_VELDEN:
        expect(page.locator(f"[data-testid=validation-{veld}]")).to_be_visible()
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


# ---------------------------------------------------------------------------
# PROMPTVELDEN-V-02 — validatie ongewijzigd na omzetting naar textarea
# ---------------------------------------------------------------------------

def test_validatie_taak_werkt_na_omzetting_naar_textarea(page: Page):
    """Testcode: promptvelden.validatie.05
    Dekt: PROMPTVELDEN-V-02 — lege `taak` toont een validatiefout, ook nadat het een textarea is geworden.
    """
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=doel]").fill("data te verwerken")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-taak]")).to_be_visible()


def test_validatie_doel_werkt_na_omzetting_naar_textarea(page: Page):
    """Testcode: promptvelden.validatie.06
    Dekt: PROMPTVELDEN-V-02 — leeg `doel` toont een validatiefout, ook nadat het een textarea is geworden.
    """
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-doel]")).to_be_visible()


def test_validatie_rol_werkt_ongewijzigd(page: Page):
    """Testcode: promptvelden.validatie.07
    Dekt: PROMPTVELDEN-V-02 — lege `rol` toont een validatiefout.
    """
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-rol]")).to_be_visible()
