"""
Frontend-tests voor story 07: Bijlage toevoegen aan een sessie.

Vereist: de app draait op http://localhost:3000 (python app.py).

AC gedekt:
- De UI toont een bestandskiezer-knop waarmee de gebruiker één bijlage kan selecteren
- Naast de knop staat de bestandsnaam of "Geen bijlage"
- De gebruiker kan een geselecteerde bijlage verwijderen via een ×-knop
- Na verwijderen keert de UI terug naar "Geen bijlage"
- De bijlage is optioneel — een sessie zonder bijlage werkt ongewijzigd
- Bij laden van een sessie met bijlage toont de UI de bestandsnaam + "(niet opnieuw geladen — upload indien nodig opnieuw)"
- Bij laden van een sessie zonder bijlage toont de UI "Geen bijlage"
- Sessie opslaan stuurt 'bijlage_bestandsnaam' mee
- Sessie laden vult 'bijlage_bestandsnaam' in het formulier
"""
import json
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"
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


def _stub_prompt_response(page: Page):
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"runs": [{"run_nummer": 1, "temperature": 0.7, "response": "antwoord", "log_status": "ok"}]}),
    ))


# ---------------------------------------------------------------------------
# UI structuur
# ---------------------------------------------------------------------------

def test_bijlage_knop_is_zichtbaar(page: Page):
    """De UI toont een bestandskiezer-knop voor het selecteren van een bijlage."""
    expect(page.locator("[data-testid=bijlage-input]")).to_be_attached()


def test_bijlage_label_toont_geen_bijlage_als_standaard(page: Page):
    """Zonder geselecteerde bijlage toont de UI 'Geen bijlage'."""
    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "Geen bijlage" in tekst, f"Standaard bijlagestatus klopt niet: {tekst!r}"


# ---------------------------------------------------------------------------
# Bestand selecteren
# ---------------------------------------------------------------------------

def test_geselecteerd_bestand_toont_bestandsnaam(page: Page, tmp_path):
    """Na het selecteren van een bestand toont de UI de bestandsnaam."""
    testbestand = tmp_path / "mijn_notities.txt"
    testbestand.write_text("inhoud van notities", encoding="utf-8")

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))

    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "mijn_notities.txt" in tekst, f"Bestandsnaam ontbreekt in status: {tekst!r}"


def test_verwijderknop_is_zichtbaar_na_selectie(page: Page, tmp_path):
    """Na het selecteren van een bestand is de ×-verwijderknop zichtbaar."""
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))

    expect(page.locator("[data-testid=bijlage-verwijder]")).to_be_visible()


def test_verwijderknop_reset_naar_geen_bijlage(page: Page, tmp_path):
    """Na het klikken op ×-knop keert de UI terug naar 'Geen bijlage'."""
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))
    page.locator("[data-testid=bijlage-verwijder]").click()

    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "Geen bijlage" in tekst, f"UI staat niet terug op 'Geen bijlage' na verwijderen: {tekst!r}"


def test_verwijderknop_verdwijnt_na_klikken(page: Page, tmp_path):
    """Na het klikken op × is de verwijderknop niet meer zichtbaar."""
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))
    page.locator("[data-testid=bijlage-verwijder]").click()

    expect(page.locator("[data-testid=bijlage-verwijder]")).not_to_be_visible()


# ---------------------------------------------------------------------------
# Bijlage is optioneel
# ---------------------------------------------------------------------------

def test_aanvraag_zonder_bijlage_slaagt(page: Page):
    """Een aanvraag zonder bijlage wordt succesvol verstuurd (HTTP 200)."""
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_be_visible()


# ---------------------------------------------------------------------------
# Sessie opslaan
# ---------------------------------------------------------------------------

def test_sessie_opslaan_stuurt_bijlage_bestandsnaam_mee(page: Page, tmp_path):
    """Bij het opslaan van een sessie met bijlage wordt 'bijlage_bestandsnaam' meegestuurd."""
    testbestand = tmp_path / "rapport.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    vastgelegd: dict = {}

    def handle(route):
        if route.request.method == "POST":
            vastgelegd.update(route.request.post_data_json)
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')
        else:
            route.fulfill(status=200, content_type="application/json", body='{"sessions": []}')

    page.route(SESSIONS_ROUTE, handle)

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))
    _vul_verplichte_velden(page)
    page.locator("[name=session-name]").fill("test-sessie")
    page.get_by_role("button", name="Opslaan").click()

    assert "bijlage_bestandsnaam" in vastgelegd, (
        f"Veld 'bijlage_bestandsnaam' ontbreekt bij opslaan: {vastgelegd}"
    )
    assert vastgelegd["bijlage_bestandsnaam"] == "rapport.txt"


def test_sessie_opslaan_zonder_bijlage_stuurt_null_mee(page: Page):
    """Bij het opslaan van een sessie zonder bijlage is 'bijlage_bestandsnaam' null."""
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

    assert "bijlage_bestandsnaam" in vastgelegd, (
        f"Veld 'bijlage_bestandsnaam' ontbreekt bij opslaan: {vastgelegd}"
    )
    assert vastgelegd["bijlage_bestandsnaam"] is None


# ---------------------------------------------------------------------------
# Sessie laden
# ---------------------------------------------------------------------------

def test_sessie_laden_met_bijlage_toont_bestandsnaam(page: Page):
    """Bij het laden van een sessie met bijlage toont de UI de opgeslagen bestandsnaam."""
    sessie_data = json.dumps({
        "name": "sessie-met-bijlage",
        "provider": "ollama",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "bijlage_bestandsnaam": "document.pdf",
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["sessie-met-bijlage"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("sessie-met-bijlage")

    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "document.pdf" in tekst, f"Bestandsnaam ontbreekt na laden sessie: {tekst!r}"


def test_sessie_laden_met_bijlage_toont_herlaad_melding(page: Page):
    """Bij het laden van een sessie met bijlage toont de UI de melding dat de bijlage niet opnieuw is geladen."""
    sessie_data = json.dumps({
        "name": "sessie-met-bijlage",
        "provider": "ollama",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "bijlage_bestandsnaam": "document.pdf",
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["sessie-met-bijlage"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("sessie-met-bijlage")

    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "niet opnieuw geladen" in tekst.lower() or "upload" in tekst.lower(), (
        f"Herlaad-melding ontbreekt na laden sessie: {tekst!r}"
    )


def test_sessie_laden_zonder_bijlage_toont_geen_bijlage(page: Page):
    """Bij het laden van een sessie zonder bijlage toont de UI 'Geen bijlage'."""
    sessie_data = json.dumps({
        "name": "sessie-zonder-bijlage",
        "provider": "ollama",
        "rol": "tester",
        "taak": "testen",
        "doel": "kwaliteit bewaken",
        "bijlage_bestandsnaam": None,
    })
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": ["sessie-zonder-bijlage"]}',
    ))
    page.route(SESSION_ITEM_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=sessie_data,
    ))
    page.reload()
    page.locator("[data-testid=session-select]").select_option("sessie-zonder-bijlage")

    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "Geen bijlage" in tekst, f"'Geen bijlage' ontbreekt na laden sessie zonder bijlage: {tekst!r}"


def test_sessie_laden_zonder_bijlage_veld_geeft_geen_fout(page: Page):
    """Bestaande sessies zonder 'bijlage_bestandsnaam' kunnen worden geladen zonder foutmelding."""
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
