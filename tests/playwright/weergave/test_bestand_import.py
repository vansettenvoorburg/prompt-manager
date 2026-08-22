"""
Weergave-tests voor bestand import (bijlage).

Bron: documentatie/acceptatiecriteria/bestand-import.md
Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

Testcodes volgen het formaat <bestand>.<categorie>.<volgnummer>, bijv.
bestand_import.weergave.01 — bewust een ander formaat dan de AC-codes (IMPORT-W-01).
"""
import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

SESSIONS_ROUTE = "**/api/sessions"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))
    page.goto(BASE_URL)


# ---------------------------------------------------------------------------
# IMPORT-W-01 — bestandskiezer-knop
# ---------------------------------------------------------------------------

def test_bijlage_knop_is_zichtbaar(page: Page):
    """Testcode: bestand_import.weergave.01
    Dekt: IMPORT-W-01 — de UI toont een bestandskiezer-knop voor het selecteren van een bijlage.
    """
    expect(page.locator("[data-testid=bijlage-input]")).to_be_attached()


# ---------------------------------------------------------------------------
# IMPORT-W-02 — bestandsnaam of "Geen bijlage"
# ---------------------------------------------------------------------------

def test_bijlage_label_toont_geen_bijlage_als_standaard(page: Page):
    """Testcode: bestand_import.weergave.02
    Dekt: IMPORT-W-02 — zonder geselecteerde bijlage toont de UI 'Geen bijlage'.
    """
    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "Geen bijlage" in tekst, f"Standaard bijlagestatus klopt niet: {tekst!r}"


def test_geselecteerd_bestand_toont_bestandsnaam(page: Page, tmp_path):
    """Testcode: bestand_import.weergave.03
    Dekt: IMPORT-W-02 — na het selecteren van een bestand toont de UI de bestandsnaam.
    """
    testbestand = tmp_path / "mijn_notities.txt"
    testbestand.write_text("inhoud van notities", encoding="utf-8")

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))

    tekst = page.locator("[data-testid=bijlage-status]").inner_text()
    assert "mijn_notities.txt" in tekst, f"Bestandsnaam ontbreekt in status: {tekst!r}"


# ---------------------------------------------------------------------------
# IMPORT-W-03 — verwijderknop zichtbaar na selectie
# ---------------------------------------------------------------------------

def test_verwijderknop_is_zichtbaar_na_selectie(page: Page, tmp_path):
    """Testcode: bestand_import.weergave.04
    Dekt: IMPORT-W-03 — na het selecteren van een bestand is de ×-verwijderknop zichtbaar.
    """
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    page.locator("[data-testid=bijlage-input]").set_input_files(str(testbestand))

    expect(page.locator("[data-testid=bijlage-verwijder]")).to_be_visible()
