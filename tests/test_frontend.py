"""
Frontend-tests voor story 01: prompt invoeren en resultaat ontvangen via Ollama.

Vereist: de app draait op http://localhost:3000 (python app.py).

AC gedekt:
- AC 1: invoervelden zichtbaar
- AC 2: verstuurknop zichtbaar
- AC 3: antwoord verschijnt na versturen
- AC 4: laadstatus zichtbaar terwijl Ollama bezig is
- AC 5: lege verplichte velden → validatiemeldingen per veld
- AC 6: Ollama-fout → foutmelding in de browser (geen stille mislukking)

Story 02 heeft de losse textarea vervangen door acht invulvelden. Tests zijn
bijgewerkt naar het nieuwe formulier (2026-05-10).
"""
import time
import threading
import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:3000"
OLLAMA_ROUTE = "**/api/prompt"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    page.goto(BASE_URL)


def _vul_verplichte_velden(page: Page):
    page.locator("[name=rol]").fill("senior developer")
    page.locator("[name=taak]").fill("een API ontwerpen")
    page.locator("[name=doel]").fill("data op te slaan")


def test_invoerveld_is_zichtbaar(page: Page):
    """AC 1 — het rol-veld (primair invoerveld) is zichtbaar."""
    expect(page.locator("[name=rol]")).to_be_visible()


def test_verstuurknop_is_zichtbaar(page: Page):
    """AC 2 — er is een verstuurknop zichtbaar."""
    expect(page.get_by_role("button", name="Verstuur")).to_be_visible()


def test_lege_verplichte_velden_tonen_validatiemeldingen(page: Page):
    """AC 5 — versturen met lege verplichte velden toont validatiemeldingen, doet geen API-call."""
    calls = []
    page.route(OLLAMA_ROUTE, lambda route: calls.append(route) or route.abort())

    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=validation-rol]")).to_be_visible()
    assert len(calls) == 0, "Er mag geen API-call zijn gedaan bij lege verplichte velden"


def test_laadstatus_zichtbaar_tijdens_wachten(page: Page):
    """AC 4 — laadstatus verschijnt direct na versturen, vóór het antwoord aankomt."""

    def trage_response(route):
        def fulfill():
            time.sleep(0.3)
            try:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"response": "Antwoord"}',
                )
            except Exception:
                # playwright sync API mag niet vanuit een andere thread worden aangeroepen
                # als de testcontext al is afgelopen
                pass
        threading.Thread(target=fulfill, daemon=True).start()

    page.route(OLLAMA_ROUTE, trage_response)
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=loading]")).to_be_visible()


def test_antwoord_verschijnt_na_versturen(page: Page):
    """AC 3 — het antwoord van Ollama verschijnt zichtbaar op de pagina."""
    page.route(
        OLLAMA_ROUTE,
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"response": "Dit is het antwoord van Ollama"}',
        ),
    )
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=response]")).to_be_visible()
    expect(page.locator("[data-testid=response]")).to_contain_text("Dit is het antwoord van Ollama")


def test_ollama_fout_toont_foutmelding(page: Page):
    """AC 6 — bij een Ollama-fout verschijnt een foutmelding (geen lege pagina)."""
    page.route(
        OLLAMA_ROUTE,
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"detail": "Ollama is niet bereikbaar"}',
        ),
    )
    _vul_verplichte_velden(page)
    page.get_by_role("button", name="Verstuur").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()
    expect(page.locator("[data-testid=error]")).not_to_be_empty()
