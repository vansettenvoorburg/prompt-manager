"""
Frontend-tests voor story 10: Kopieerknop en formulieropmaak.

Vereist: de app draait op http://localhost:3000 (python app.py).

AC gedekt:
- Elk run-resultaatblok heeft een kopieerknop
- Elk reviewer-stap heeft een kopieerknop
- De eindoutput heeft een kopieerknop
- Na klikken op kopieerknop verandert de tekst tijdelijk naar 'Gekopieerd!'
- Na 2 seconden keert de knoptekst terug naar de originele tekst
- Bij mislukte klembordtoegang toont de knop kort 'Mislukt'
- `taak` is een textarea
- `doel` is een textarea
- `formaat` is een textarea
- `taak` heeft standaard 2 rijen
- `doel` heeft standaard 2 rijen
- `formaat` heeft standaard 3 rijen
- `eisen` blijft textarea met 3 rijen
- `voorbeelden` blijft textarea met 3 rijen
- `taak` accepteert newlines
- `doel` accepteert newlines
- `formaat` accepteert newlines
- Validatie op `taak` werkt na omzetting naar textarea
- Validatie op `doel` werkt na omzetting naar textarea
- Validatie op `rol` werkt ongewijzigd
"""
import json
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"
PROMPT_ROUTE = "**/api/prompt"
SESSIONS_ROUTE = "**/api/sessions"

_STUB_RESPONSE = json.dumps({
    "runs": [
        {"run_nummer": 1, "temperature": 0.8, "response": "dit is de uitvoer", "log_status": "ok"}
    ],
    "reviewer_stappen": [
        {
            "reviewer_nr": 1,
            "reviewer_rol": "QA engineer",
            "run_nummer": 1,
            "temperature": 0.5,
            "response": "dit is de revieweruitvoer",
            "log_status": "ok",
        }
    ],
    "eindoutput": "dit is de eindversie",
})


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


def _stub_prompt_response(page: Page):
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=_STUB_RESPONSE,
    ))


def _mock_clipboard_succesvol(page: Page):
    page.evaluate("navigator.clipboard = { writeText: (t) => Promise.resolve() }")


def _mock_clipboard_mislukt(page: Page):
    page.evaluate(
        "navigator.clipboard = { writeText: (t) => Promise.reject(new Error('geen toestemming')) }"
    )


# ---------------------------------------------------------------------------
# Kopieerknop — aanwezigheid
# ---------------------------------------------------------------------------

def test_run_result_heeft_kopieerknop(page: Page):
    """Elk run-resultaatblok heeft een kopieerknop."""
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(
        page.locator("[data-testid=run-results] [data-testid=kopieer-knop]").first
    ).to_be_visible()


def test_reviewer_stap_heeft_kopieerknop(page: Page):
    """Elk reviewer-stap heeft een kopieerknop."""
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first.fill("QA engineer")
    page.get_by_role("button", name="Verstuur").click()

    expect(
        page.locator("[data-testid=reviewer-stap-item] [data-testid=kopieer-knop]").first
    ).to_be_visible()


def test_eindoutput_heeft_kopieerknop(page: Page):
    """De eindoutput heeft een kopieerknop."""
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.locator("[data-testid=reviewer-toevoegen]").click()
    page.locator("[data-testid=reviewer-item] [data-testid=reviewer-rol]").first.fill("QA engineer")
    page.get_by_role("button", name="Verstuur").click()

    expect(
        page.locator("[data-testid=eindoutput] [data-testid=kopieer-knop]")
    ).to_be_visible()


# ---------------------------------------------------------------------------
# Kopieerknop — gedrag
# ---------------------------------------------------------------------------

def test_kopieerknop_tekst_verandert_naar_gekopieerd(page: Page):
    """Na klikken op de kopieerknop verandert de tekst tijdelijk naar 'Gekopieerd!'."""
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    _mock_clipboard_succesvol(page)

    knop = page.locator("[data-testid=run-results] [data-testid=kopieer-knop]").first
    knop.click()

    expect(knop).to_have_text("Gekopieerd!")


def test_kopieerknop_tekst_keert_terug_na_2_seconden(page: Page):
    """Na 2 seconden keert de knoptekst terug naar de originele tekst."""
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    _mock_clipboard_succesvol(page)

    knop = page.locator("[data-testid=run-results] [data-testid=kopieer-knop]").first
    originele_tekst = knop.inner_text()
    knop.click()

    page.wait_for_timeout(2200)
    expect(knop).to_have_text(originele_tekst)


def test_kopieerknop_toont_mislukt_bij_geen_klembord_toegang(page: Page):
    """Als het klembord niet beschikbaar is, toont de knop kort 'Mislukt'."""
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()
    _mock_clipboard_mislukt(page)

    knop = page.locator("[data-testid=run-results] [data-testid=kopieer-knop]").first
    knop.click()

    expect(knop).to_have_text("Mislukt")


# ---------------------------------------------------------------------------
# Tekstvelden — element-type
# ---------------------------------------------------------------------------

def test_taak_is_textarea(page: Page):
    """Het `taak`-veld is een textarea-element."""
    tag = page.locator("[name=taak]").evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'taak', maar het element is: {tag!r}"


def test_doel_is_textarea(page: Page):
    """Het `doel`-veld is een textarea-element."""
    tag = page.locator("[name=doel]").evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'doel', maar het element is: {tag!r}"


def test_formaat_is_textarea(page: Page):
    """Het `formaat`-veld is een textarea-element."""
    tag = page.locator("[name=formaat]").evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'formaat', maar het element is: {tag!r}"


# ---------------------------------------------------------------------------
# Tekstvelden — aantal rijen
# ---------------------------------------------------------------------------

def test_taak_heeft_2_rijen(page: Page):
    """Het `taak`-veld heeft standaard 2 rijen zichtbare ruimte."""
    rijen = page.locator("[name=taak]").get_attribute("rows")
    assert rijen == "2", f"Verwacht rows='2' voor 'taak', maar kreeg {rijen!r}"


def test_doel_heeft_2_rijen(page: Page):
    """Het `doel`-veld heeft standaard 2 rijen zichtbare ruimte."""
    rijen = page.locator("[name=doel]").get_attribute("rows")
    assert rijen == "2", f"Verwacht rows='2' voor 'doel', maar kreeg {rijen!r}"


def test_formaat_heeft_3_rijen(page: Page):
    """Het `formaat`-veld heeft standaard 3 rijen zichtbare ruimte."""
    rijen = page.locator("[name=formaat]").get_attribute("rows")
    assert rijen == "3", f"Verwacht rows='3' voor 'formaat', maar kreeg {rijen!r}"


def test_eisen_blijft_textarea_met_3_rijen(page: Page):
    """Het `eisen`-veld blijft een textarea met 3 rijen."""
    eisen = page.locator("[name=eisen]")
    tag = eisen.evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'eisen', maar het element is: {tag!r}"
    rijen = eisen.get_attribute("rows")
    assert rijen == "3", f"Verwacht rows='3' voor 'eisen', maar kreeg {rijen!r}"


def test_voorbeelden_blijft_textarea_met_3_rijen(page: Page):
    """Het `voorbeelden`-veld blijft een textarea met 3 rijen."""
    voorbeelden = page.locator("[name=voorbeelden]")
    tag = voorbeelden.evaluate("el => el.tagName.toLowerCase()")
    assert tag == "textarea", f"Verwacht textarea voor 'voorbeelden', maar het element is: {tag!r}"
    rijen = voorbeelden.get_attribute("rows")
    assert rijen == "3", f"Verwacht rows='3' voor 'voorbeelden', maar kreeg {rijen!r}"


# ---------------------------------------------------------------------------
# Tekstvelden — newlines accepteren
# ---------------------------------------------------------------------------

def test_taak_accepteert_newlines(page: Page):
    """Het `taak`-veld accepteert newlines (Enter-toets)."""
    page.locator("[name=taak]").fill("regel 1\nregel 2")
    waarde = page.locator("[name=taak]").input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'taak': {waarde!r}"


def test_doel_accepteert_newlines(page: Page):
    """Het `doel`-veld accepteert newlines (Enter-toets)."""
    page.locator("[name=doel]").fill("doel A\ndoel B")
    waarde = page.locator("[name=doel]").input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'doel': {waarde!r}"


def test_formaat_accepteert_newlines(page: Page):
    """Het `formaat`-veld accepteert newlines (Enter-toets)."""
    page.locator("[name=formaat]").fill("JSON\nmarkdown")
    waarde = page.locator("[name=formaat]").input_value()
    assert "\n" in waarde, f"Newline ontbreekt in 'formaat': {waarde!r}"


# ---------------------------------------------------------------------------
# Validatie — ongewijzigd na omzetting naar textarea
# ---------------------------------------------------------------------------

def test_validatie_taak_werkt_na_omzetting_naar_textarea(page: Page):
    """Lege `taak` toont een validatiefout, ook nadat het een textarea is geworden."""
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=doel]").fill("data te verwerken")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-taak]")).to_be_visible()


def test_validatie_doel_werkt_na_omzetting_naar_textarea(page: Page):
    """Leeg `doel` toont een validatiefout, ook nadat het een textarea is geworden."""
    page.locator("[name=rol]").fill("Python developer")
    page.locator("[name=taak]").fill("een API bouwen")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-doel]")).to_be_visible()


def test_validatie_rol_werkt_ongewijzigd(page: Page):
    """Lege `rol` toont een validatiefout."""
    page.locator("[name=taak]").fill("een API bouwen")
    page.locator("[name=doel]").fill("data te verwerken")
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-rol]")).to_be_visible()
