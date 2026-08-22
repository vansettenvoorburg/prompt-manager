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
import pytest
from playwright.sync_api import Page

from tests.conftest import BASE_URL
from tests.playwright.mocks import stub_lege_sessies, stub_prompt_response, stub_sessie_item, stub_sessies_met_doorgang
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# IMPORT-I-01 — bijlage verwijderen
# ---------------------------------------------------------------------------

def test_verwijderknop_reset_naar_geen_bijlage(app: PromptPage, tmp_path):
    """Testcode: bestand_import.interactie.01
    Dekt: IMPORT-I-01 — na het klikken op ×-knop keert de UI terug naar 'Geen bijlage'.
    """
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    app.upload_bijlage(str(testbestand))
    app.verwijder_bijlage()

    app.expect_bijlage_status_bevat("Geen bijlage")


def test_verwijderknop_verdwijnt_na_klikken(app: PromptPage, tmp_path):
    """Testcode: bestand_import.interactie.02
    Dekt: IMPORT-I-01 — na het klikken op × is de verwijderknop niet meer zichtbaar.
    """
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    app.upload_bijlage(str(testbestand))
    app.verwijder_bijlage()

    app.expect_bijlage_verwijder_knop_niet_zichtbaar()


# ---------------------------------------------------------------------------
# Regressie: bijlage is optioneel (geen exacte AC-bullet in bestand-import.md,
# gerelateerd aan IMPORT-I-02/I-03 — bijlage mag ontbreken zonder gedrag te breken)
# ---------------------------------------------------------------------------

def test_aanvraag_zonder_bijlage_slaagt(app: PromptPage):
    """Testcode: bestand_import.interactie.03
    Regressie — een aanvraag zonder bijlage wordt succesvol verstuurd (HTTP 200).
    """
    stub_prompt_response(app.page)
    app.vul_verplichte_velden()
    app.verstuur()

    app.expect_run_results_zichtbaar()


def test_sessie_opslaan_stuurt_bijlage_bestandsnaam_mee(app: PromptPage, tmp_path):
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

    app.page.route("**/api/sessions", handle)

    app.upload_bijlage(str(testbestand))
    app.vul_verplichte_velden()
    app.sidebar.fill_naam("test-sessie")
    app.sidebar.opslaan()
    app.sidebar.wacht_op_bevestiging()

    assert "bijlage_bestandsnaam" in vastgelegd, (
        f"Veld 'bijlage_bestandsnaam' ontbreekt bij opslaan: {vastgelegd}"
    )
    assert vastgelegd["bijlage_bestandsnaam"] == "rapport.txt"


def test_sessie_opslaan_zonder_bijlage_stuurt_null_mee(app: PromptPage):
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

    app.page.route("**/api/sessions", handle)
    app.vul_verplichte_velden()
    app.sidebar.fill_naam("test-sessie")
    app.sidebar.opslaan()
    app.sidebar.wacht_op_bevestiging()

    assert "bijlage_bestandsnaam" in vastgelegd, (
        f"Veld 'bijlage_bestandsnaam' ontbreekt bij opslaan: {vastgelegd}"
    )
    assert vastgelegd["bijlage_bestandsnaam"] is None


# ---------------------------------------------------------------------------
# IMPORT-I-05 — sessie laden herstelt bijlagestatus
# ---------------------------------------------------------------------------

def test_sessie_laden_met_bijlage_toont_bestandsnaam(app: PromptPage):
    """Testcode: bestand_import.interactie.06
    Dekt: IMPORT-I-05 — bij het laden van een sessie met bijlage toont de UI de opgeslagen bestandsnaam.
    """
    sessie_data = {
        "name": "sessie-met-bijlage", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "bijlage_bestandsnaam": "document.pdf",
    }
    stub_sessies_met_doorgang(app.page, ["sessie-met-bijlage"])
    stub_sessie_item(app.page, "sessie-met-bijlage", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("sessie-met-bijlage")

    app.expect_bijlage_status_bevat("document.pdf")


def test_sessie_laden_met_bijlage_toont_herlaad_melding(app: PromptPage):
    """Testcode: bestand_import.interactie.07
    Dekt: IMPORT-I-05 — bij het laden van een sessie met bijlage toont de UI de melding dat de bijlage niet opnieuw is geladen.
    """
    sessie_data = {
        "name": "sessie-met-bijlage", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "bijlage_bestandsnaam": "document.pdf",
    }
    stub_sessies_met_doorgang(app.page, ["sessie-met-bijlage"])
    stub_sessie_item(app.page, "sessie-met-bijlage", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("sessie-met-bijlage")

    tekst = app.bijlage_status.inner_text()
    assert "niet opnieuw geladen" in tekst.lower() or "upload" in tekst.lower(), (
        f"Herlaad-melding ontbreekt na laden sessie: {tekst!r}"
    )


def test_sessie_laden_zonder_bijlage_toont_geen_bijlage(app: PromptPage):
    """Testcode: bestand_import.interactie.08
    Dekt: IMPORT-I-05 — bij het laden van een sessie zonder bijlage toont de UI 'Geen bijlage'.
    """
    sessie_data = {
        "name": "sessie-zonder-bijlage", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
        "bijlage_bestandsnaam": None,
    }
    stub_sessies_met_doorgang(app.page, ["sessie-zonder-bijlage"])
    stub_sessie_item(app.page, "sessie-zonder-bijlage", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("sessie-zonder-bijlage")

    app.expect_bijlage_status_bevat("Geen bijlage")


def test_sessie_laden_zonder_bijlage_veld_geeft_geen_fout(app: PromptPage):
    """Testcode: bestand_import.interactie.09
    Dekt: IMPORT-I-05 — bestaande sessies zonder 'bijlage_bestandsnaam' kunnen worden geladen zonder foutmelding.
    """
    sessie_data = {
        "name": "oud-sessie", "provider": "ollama",
        "rol": "tester", "taak": "testen", "doel": "kwaliteit bewaken",
    }
    stub_sessies_met_doorgang(app.page, ["oud-sessie"])
    stub_sessie_item(app.page, "oud-sessie", sessie_data)
    app.reload()
    app.sidebar.selecteer_via_dropdown("oud-sessie")

    app.expect_error_niet_zichtbaar()
