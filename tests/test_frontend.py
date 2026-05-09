"""
Frontend-tests voor story 01: prompt invoeren en resultaat ontvangen via Ollama.

Vereist: de app draait op http://localhost:3000 (python app.py).

AC gedekt:
- AC 1: tekstvak zichtbaar
- AC 2: verstuurknop zichtbaar
- AC 3: antwoord verschijnt na versturen
- AC 4: laadstatus zichtbaar terwijl Ollama bezig is
- AC 5: lege prompt → validatiemelding in de browser
- AC 6: Ollama-fout → foutmelding in de browser (geen stille mislukking)
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


def test_tekstvak_is_zichtbaar(page: Page):
    """AC 1 — er is een textarea zichtbaar."""
    expect(page.locator("textarea")).to_be_visible()


def test_verstuurknop_is_zichtbaar(page: Page):
    """AC 2 — er is een verstuurknop zichtbaar."""
    expect(page.get_by_role("button")).to_be_visible()


def test_lege_prompt_toont_validatiemelding(page: Page):
    """AC 5 — versturen met leeg tekstvak toont melding, doet geen API-call."""
    calls = []
    page.route(OLLAMA_ROUTE, lambda route: calls.append(route) or route.abort())

    page.get_by_role("button").click()

    expect(page.locator("[data-testid=validation-message]")).to_be_visible()
    assert len(calls) == 0, "Er mag geen API-call zijn gedaan bij een lege prompt"


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
                # greenlet.error: Playwright's sync API mag niet vanuit een andere
                # thread worden aangeroepen als de testcontext al is afgelopen.
                pass
        threading.Thread(target=fulfill, daemon=True).start()

    page.route(OLLAMA_ROUTE, trage_response)
    page.locator("textarea").fill("Test prompt")
    page.get_by_role("button").click()

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
    page.locator("textarea").fill("Test prompt")
    page.get_by_role("button").click()

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
    page.locator("textarea").fill("Test prompt")
    page.get_by_role("button").click()

    expect(page.locator("[data-testid=error]")).to_be_visible()
    expect(page.locator("[data-testid=error]")).not_to_be_empty()
