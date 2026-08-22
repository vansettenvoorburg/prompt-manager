"""
Frontend-tests voor story 01: prompt invoeren en resultaat ontvangen via Ollama.

Vereist: geen — de `server`-fixture (conftest.py) start de app automatisch op de testpoort.

De overige oorspronkelijke AC's van story 01 (invoervelden zichtbaar, antwoord
verschijnt, laadstatus, per-veld validatie, Ollama-foutmelding) zijn letterlijk
overgenomen door story 02 en worden daar gedekt (zie test_frontend_02.py en
specs/testdekking.md, TD-02-01/07/08/09/10). Dit bestand behoudt alleen het
dekkingsitem dat uniek aan story 01 is: de verstuurknop.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL
OLLAMA_ROUTE = "**/api/prompt"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.goto(BASE_URL)


def test_verstuurknop_is_zichtbaar(page: Page):
    """Dekt: TD-01-01 — er is een verstuurknop zichtbaar."""
    expect(page.get_by_role("button", name="Verstuur")).to_be_visible()
