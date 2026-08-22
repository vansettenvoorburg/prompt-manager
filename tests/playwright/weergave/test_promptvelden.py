"""
Weergave-tests voor promptvelden.

Bron: documentatie/acceptatiecriteria/promptvelden.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
promptvelden.weergave.01 — bewust een ander formaat dan de AC-codes (PROMPTVELDEN-W-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

ALLE_VELDEN = ("rol", "taak", "doel", "formaat", "stijl", "scope", "eisen", "voorbeelden")


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.goto(BASE_URL)


# ---------------------------------------------------------------------------
# PROMPTVELDEN-W-01 — acht invulvelden zichtbaar
# ---------------------------------------------------------------------------

def test_alle_acht_velden_zijn_zichtbaar(page: Page):
    """Testcode: promptvelden.weergave.01
    Dekt: PROMPTVELDEN-W-01 — elk van de acht velden heeft een zichtbaar invoerveld.
    """
    for veld in ALLE_VELDEN:
        locator = page.locator(f"[name={veld}]")
        expect(locator).to_be_visible()


def test_losse_textarea_is_verdwenen(page: Page):
    """Testcode: promptvelden.weergave.02
    Regressie bij PROMPTVELDEN-W-01 — de enkelvoudige textarea van vóór de acht
    promptvelden is niet meer aanwezig.
    """
    expect(page.locator("textarea#prompt")).not_to_be_visible()


# ---------------------------------------------------------------------------
# PROMPTVELDEN-W-02 — label en placeholder per veld
# ---------------------------------------------------------------------------

def test_elk_veld_heeft_een_label(page: Page):
    """Testcode: promptvelden.weergave.03
    Dekt: PROMPTVELDEN-W-02 — elk veld is gekoppeld aan een zichtbaar label.
    """
    for veld in ALLE_VELDEN:
        label = page.locator(f"label[for={veld}]")
        expect(label).to_be_visible()


def test_elk_veld_heeft_een_placeholder(page: Page):
    """Testcode: promptvelden.weergave.04
    Dekt: PROMPTVELDEN-W-02 — elk veld heeft een niet-lege placeholder als invulhulp.
    """
    for veld in ALLE_VELDEN:
        locator = page.locator(f"[name={veld}]")
        placeholder = locator.get_attribute("placeholder")
        assert placeholder, f"Veld '{veld}' heeft geen placeholder"


# ---------------------------------------------------------------------------
# PROMPTVELDEN-W-04 — verstuurknop
# ---------------------------------------------------------------------------

def test_verstuurknop_is_zichtbaar(page: Page):
    """Testcode: promptvelden.weergave.05
    Dekt: PROMPTVELDEN-W-04 — er is een verstuurknop zichtbaar.
    """
    expect(page.get_by_role("button", name="Verstuur")).to_be_visible()


# ---------------------------------------------------------------------------
# PROMPTVELDEN-W-05 — formaat/taak/doel als textarea met vast aantal rijen
# ---------------------------------------------------------------------------

def test_taak_is_textarea(page: Page):
    """Testcode: promptvelden.weergave.06
    Dekt: PROMPTVELDEN-W-05 — het `taak`-veld is een textarea-element.
    """
    tag = page.locator("[name=taak]").evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'taak', maar het element is: {tag!r}"


def test_taak_heeft_2_rijen(page: Page):
    """Testcode: promptvelden.weergave.07
    Dekt: PROMPTVELDEN-W-05 — het `taak`-veld heeft standaard 2 rijen zichtbare ruimte.
    """
    rijen = page.locator("[name=taak]").get_attribute("rows")
    assert rijen == "2", f"Verwacht rows='2' voor 'taak', maar kreeg {rijen!r}"


def test_doel_is_textarea(page: Page):
    """Testcode: promptvelden.weergave.08
    Dekt: PROMPTVELDEN-W-05 — het `doel`-veld is een textarea-element.
    """
    tag = page.locator("[name=doel]").evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'doel', maar het element is: {tag!r}"


def test_doel_heeft_2_rijen(page: Page):
    """Testcode: promptvelden.weergave.09
    Dekt: PROMPTVELDEN-W-05 — het `doel`-veld heeft standaard 2 rijen zichtbare ruimte.
    """
    rijen = page.locator("[name=doel]").get_attribute("rows")
    assert rijen == "2", f"Verwacht rows='2' voor 'doel', maar kreeg {rijen!r}"


def test_formaat_is_textarea(page: Page):
    """Testcode: promptvelden.weergave.10
    Dekt: PROMPTVELDEN-W-05 — het `formaat`-veld is een textarea-element.
    """
    tag = page.locator("[name=formaat]").evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'formaat', maar het element is: {tag!r}"


def test_formaat_heeft_3_rijen(page: Page):
    """Testcode: promptvelden.weergave.11
    Dekt: PROMPTVELDEN-W-05 — het `formaat`-veld heeft standaard 3 rijen zichtbare ruimte.
    """
    rijen = page.locator("[name=formaat]").get_attribute("rows")
    assert rijen == "3", f"Verwacht rows='3' voor 'formaat', maar kreeg {rijen!r}"


def test_eisen_blijft_textarea_met_3_rijen(page: Page):
    """Testcode: promptvelden.weergave.12
    Dekt: PROMPTVELDEN-W-05 — het `eisen`-veld blijft een textarea met 3 rijen.
    """
    eisen = page.locator("[name=eisen]")
    tag = eisen.evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'eisen', maar het element is: {tag!r}"
    rijen = eisen.get_attribute("rows")
    assert rijen == "3", f"Verwacht rows='3' voor 'eisen', maar kreeg {rijen!r}"


def test_voorbeelden_blijft_textarea_met_3_rijen(page: Page):
    """Testcode: promptvelden.weergave.13
    Dekt: PROMPTVELDEN-W-05 — het `voorbeelden`-veld blijft een textarea met 3 rijen.
    """
    voorbeelden = page.locator("[name=voorbeelden]")
    tag = voorbeelden.evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'voorbeelden', maar het element is: {tag!r}"
    rijen = voorbeelden.get_attribute("rows")
    assert rijen == "3", f"Verwacht rows='3' voor 'voorbeelden', maar kreeg {rijen!r}"
