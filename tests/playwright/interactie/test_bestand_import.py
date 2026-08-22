"""
Interactie-tests voor bestand import (bijlage).

Bron: documentatie/acceptatiecriteria/bestand-import.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
bestand_import.interactie.01 — bewust een ander formaat dan de AC-codes (IMPORT-I-01).

IMPORT-I-02 (bijlagetekst toegevoegd met label 'Bijlage:') en IMPORT-I-03 (bijlage
meegestuurd bij elke taak/reviewstap) worden gedekt door de backend/integratietests
(tests/backend/) — geen aparte Playwright-test nodig.
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


def _stub_prompt_response(page: Page):
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"runs": [{"run_nummer": 1, "temperature": 0.7, "response": "antwoord", "log_status": "ok"}]}),
    ))


# ---------------------------------------------------------------------------
# IMPORT-I-01 — bijlage verwijderen
# ---------------------------------------------------------------------------

def test_verwijderknop_reset_naar_geen_bijlage(page: Page, tmp_path):
    """Testcode: bestand_import.interactie.01
    Dekt: IMPORT-I-01 — na het klikken op ×-knop keert de UI terug naar 'Geen bijlage'.
    """
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))
    page.locator("[data-testid=bijlage-verwijder]").click()

    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "Geen bijlage" in tekst, f"UI staat niet terug op 'Geen bijlage' na verwijderen: {tekst!r}"


def test_verwijderknop_verdwijnt_na_klikken(page: Page, tmp_path):
    """Testcode: bestand_import.interactie.02
    Dekt: IMPORT-I-01 — na het klikken op × is de verwijderknop niet meer zichtbaar.
    """
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))
    page.locator("[data-testid=bijlage-verwijder]").click()

    expect(page.locator("[data-testid=bijlage-verwijder]")).not_to_be_visible()


# ---------------------------------------------------------------------------
# Regressie: bijlage is optioneel (geen exacte AC-bullet in bestand-import.md,
# gerelateerd aan IMPORT-I-02/I-03 — bijlage mag ontbreken zonder gedrag te breken)
# ---------------------------------------------------------------------------

def test_aanvraag_zonder_bijlage_slaagt(page: Page):
    """Testcode: bestand_import.interactie.03
    Regressie — een aanvraag zonder bijlage wordt succesvol verstuurd (HTTP 200).
    """
    _stub_prompt_response(page)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=run-results]")).to_be_visible()


def test_sessie_opslaan_stuurt_bijlage_bestandsnaam_mee(page: Page, tmp_path):
    """Testcode: bestand_import.interactie.04
    Regressie — bij het opslaan van een sessie met bijlage wordt 'bijlage_bestandsnaam' meegestuurd.
    """
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
    page.wait_for_selector("[data-testid=save-confirmation]")

    assert "bijlage_bestandsnaam" in vastgelegd, (
        f"Veld 'bijlage_bestandsnaam' ontbreekt bij opslaan: {vastgelegd}"
    )
    assert vastgelegd["bijlage_bestandsnaam"] == "rapport.txt"


def test_sessie_opslaan_zonder_bijlage_stuurt_null_mee(page: Page):
    """Testcode: bestand_import.interactie.05
    Regressie — bij het opslaan van een sessie zonder bijlage is 'bijlage_bestandsnaam' null.
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

    assert "bijlage_bestandsnaam" in vastgelegd, (
        f"Veld 'bijlage_bestandsnaam' ontbreekt bij opslaan: {vastgelegd}"
    )
    assert vastgelegd["bijlage_bestandsnaam"] is None


# ---------------------------------------------------------------------------
# IMPORT-I-05 — sessie laden herstelt bijlagestatus
# ---------------------------------------------------------------------------

def test_sessie_laden_met_bijlage_toont_bestandsnaam(page: Page):
    """Testcode: bestand_import.interactie.06
    Dekt: IMPORT-I-05 — bij het laden van een sessie met bijlage toont de UI de opgeslagen bestandsnaam.
    """
    sessie_data = json.dumps({
        "name": "sessie-met-bijlage", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
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
    """Testcode: bestand_import.interactie.07
    Dekt: IMPORT-I-05 — bij het laden van een sessie met bijlage toont de UI de melding dat de bijlage niet opnieuw is geladen.
    """
    sessie_data = json.dumps({
        "name": "sessie-met-bijlage", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
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
    """Testcode: bestand_import.interactie.08
    Dekt: IMPORT-I-05 — bij het laden van een sessie zonder bijlage toont de UI 'Geen bijlage'.
    """
    sessie_data = json.dumps({
        "name": "sessie-zonder-bijlage", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
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
    """Testcode: bestand_import.interactie.09
    Dekt: IMPORT-I-05 — bestaande sessies zonder 'bijlage_bestandsnaam' kunnen worden geladen zonder foutmelding.
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
