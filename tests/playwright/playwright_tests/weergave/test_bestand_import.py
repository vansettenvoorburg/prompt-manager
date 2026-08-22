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
from tests.playwright.mocks import stub_lege_sessies
from tests.playwright.pages.prompt_page import PromptPage


@pytest.fixture(autouse=True)
def app(page: Page) -> PromptPage:
    stub_lege_sessies(page)
    pagina = PromptPage(page)
    pagina.open(BASE_URL)
    return pagina


# ---------------------------------------------------------------------------
# IMPORT-W-01 — bestandskiezer-knop
# ---------------------------------------------------------------------------

def test_bijlage_knop_is_zichtbaar(app: PromptPage):
    """Testcode: bestand_import.weergave.01
    Dekt: IMPORT-W-01 — de UI toont een bestandskiezer-knop voor het selecteren van een bijlage.
    """
    expect(app.bijlage_input).to_be_attached()


# ---------------------------------------------------------------------------
# IMPORT-W-02 — bestandsnaam of "Geen bijlage"
# ---------------------------------------------------------------------------

def test_bijlage_label_toont_geen_bijlage_als_standaard(app: PromptPage):
    """Testcode: bestand_import.weergave.02
    Dekt: IMPORT-W-02 — zonder geselecteerde bijlage toont de UI 'Geen bijlage'.
    """
    app.expect_bijlage_status_bevat("Geen bijlage")


def test_geselecteerd_bestand_toont_bestandsnaam(app: PromptPage, tmp_path):
    """Testcode: bestand_import.weergave.03
    Dekt: IMPORT-W-02 — na het selecteren van een bestand toont de UI de bestandsnaam.
    """
    testbestand = tmp_path / "mijn_notities.txt"
    testbestand.write_text("inhoud van notities", encoding="utf-8")

    app.upload_bijlage(str(testbestand))

    app.expect_bijlage_status_bevat("mijn_notities.txt")


# ---------------------------------------------------------------------------
# IMPORT-W-03 — verwijderknop zichtbaar na selectie
# ---------------------------------------------------------------------------

def test_verwijderknop_is_zichtbaar_na_selectie(app: PromptPage, tmp_path):
    """Testcode: bestand_import.weergave.04
    Dekt: IMPORT-W-03 — na het selecteren van een bestand is de ×-verwijderknop zichtbaar.
    """
    testbestand = tmp_path / "notities.txt"
    testbestand.write_text("inhoud", encoding="utf-8")

    app.upload_bijlage(str(testbestand))

    app.expect_bijlage_verwijder_knop_zichtbaar()
