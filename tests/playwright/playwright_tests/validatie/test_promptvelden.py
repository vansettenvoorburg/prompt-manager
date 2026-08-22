"""
Validatie-tests voor promptvelden.

Bron: documentatie/acceptatiecriteria/promptvelden.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
promptvelden.validatie.01 — bewust een ander formaat dan de AC-codes (PROMPTVELDEN-V-01).
"""
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.pages.prompt_page import PromptPage

PROMPT_ROUTE = "**/api/prompt"
VERPLICHTE_VELDEN = ("rol", "taak", "doel")


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# PROMPTVELDEN-V-01 — leeg verplicht veld toont validatiemelding, geen API-call
# ---------------------------------------------------------------------------

def test_leeg_rol_toont_validatiemelding(app: PromptPage):
    """Testcode: promptvelden.validatie.01
    Dekt: PROMPTVELDEN-V-01 — versturen met leeg veld rol toont een validatiemelding voor rol.
    """
    calls = []
    app.page.route(PROMPT_ROUTE, lambda route: calls.append(route) or route.abort())

    app.vul_verplichte_velden(uitzondering="rol")
    app.verstuur()

    app.expect_validation_zichtbaar("rol")
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_lege_taak_toont_validatiemelding(app: PromptPage):
    """Testcode: promptvelden.validatie.02
    Dekt: PROMPTVELDEN-V-01 — versturen met leeg veld taak toont een validatiemelding voor taak.
    """
    calls = []
    app.page.route(PROMPT_ROUTE, lambda route: calls.append(route) or route.abort())

    app.vul_verplichte_velden(uitzondering="taak")
    app.verstuur()

    app.expect_validation_zichtbaar("taak")
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_leeg_doel_toont_validatiemelding(app: PromptPage):
    """Testcode: promptvelden.validatie.03
    Dekt: PROMPTVELDEN-V-01 — versturen met leeg veld doel toont een validatiemelding voor doel.
    """
    calls = []
    app.page.route(PROMPT_ROUTE, lambda route: calls.append(route) or route.abort())

    app.vul_verplichte_velden(uitzondering="doel")
    app.verstuur()

    app.expect_validation_zichtbaar("doel")
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


def test_meerdere_lege_verplichte_velden_tonen_elk_een_melding(app: PromptPage):
    """Testcode: promptvelden.validatie.04
    Dekt: PROMPTVELDEN-V-01 — als alle drie verplichte velden leeg zijn, verschijnt voor elk een eigen melding.
    """
    calls = []
    app.page.route(PROMPT_ROUTE, lambda route: calls.append(route) or route.abort())

    app.verstuur()

    for veld in VERPLICHTE_VELDEN:
        app.expect_validation_zichtbaar(veld)
    assert len(calls) == 0, "Er mocht geen API-call zijn gedaan"


# ---------------------------------------------------------------------------
# PROMPTVELDEN-V-02 — validatie ongewijzigd na omzetting naar textarea
# ---------------------------------------------------------------------------

def test_validatie_taak_werkt_na_omzetting_naar_textarea(app: PromptPage):
    """Testcode: promptvelden.validatie.05
    Dekt: PROMPTVELDEN-V-02 — lege `taak` toont een validatiefout, ook nadat het een textarea is geworden.
    """
    app.fill_veld("rol", "Python developer")
    app.fill_veld("doel", "data te verwerken")
    app.verstuur()

    app.expect_validation_zichtbaar("taak")


def test_validatie_doel_werkt_na_omzetting_naar_textarea(app: PromptPage):
    """Testcode: promptvelden.validatie.06
    Dekt: PROMPTVELDEN-V-02 — leeg `doel` toont een validatiefout, ook nadat het een textarea is geworden.
    """
    app.fill_veld("rol", "Python developer")
    app.fill_veld("taak", "een API bouwen")
    app.verstuur()

    app.expect_validation_zichtbaar("doel")


def test_validatie_rol_werkt_ongewijzigd(app: PromptPage):
    """Testcode: promptvelden.validatie.07
    Dekt: PROMPTVELDEN-V-02 — lege `rol` toont een validatiefout.
    """
    app.fill_veld("taak", "een API bouwen")
    app.fill_veld("doel", "data te verwerken")
    app.verstuur()

    app.expect_validation_zichtbaar("rol")
