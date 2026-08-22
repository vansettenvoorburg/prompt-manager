"""Gedeelde route-mocks en testdata voor de Playwright-suite.

Houdt testdata (welke waarden een test gebruikt) gescheiden van testlogica
(wat een test doet), zodat een wijziging in bijv. de vorm van de
settings-response op één plek wordt doorgevoerd in plaats van in elk
spec-bestand apart te worden gekopieerd.
"""
import json

from playwright.sync_api import Page, Route

PROMPT_ROUTE = "**/api/prompt"
SESSIONS_ROUTE = "**/api/sessions"
SESSION_ITEM_ROUTE = "**/api/sessions/*"
SETTINGS_ROUTE = "**/api/settings"

GROQ_MODEL_DEFAULT = "llama3-8b-8192"
GROQ_MODELS_NIEUW = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "moonshotai/kimi-k2-instruct",
    "qwen3-32b",
]

DEFAULT_ROL = "Python developer"
DEFAULT_TAAK = "een API bouwen"
DEFAULT_DOEL = "data te verwerken"

DEFAULT_RUN_RESPONSE = {
    "runs": [{"run_nummer": 1, "temperature": 0.8, "response": "antwoord", "log_status": "ok"}],
}


def stub_lege_sessies(page: Page) -> None:
    """Registreert GET /api/sessions -> lege lijst, zodat de app kan laden
    zonder dat sessiedata relevant is voor de test."""
    page.route(SESSIONS_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"sessions": []}',
    ))


def stub_sessies_met_doorgang(page: Page, namen: list[str] | None = None) -> None:
    """Registreert GET /api/sessions met een lijst van sessienamen, en laat
    aanvragen voor een individuele sessie (/api/sessions/<naam>) ongemoeid
    doorgaan zodat die apart met stub_sessie_item gemockt kunnen worden."""
    body = json.dumps({"sessions": namen or []})

    def handle(route: Route) -> None:
        is_lijst = route.request.method == "GET" and "/api/sessions/" not in route.request.url
        if is_lijst:
            route.fulfill(status=200, content_type="application/json", body=body)
        else:
            route.continue_()

    page.route(SESSIONS_ROUTE, handle)


def stub_sessie_item(page: Page, naam: str, sessie_data: dict) -> None:
    page.route(f"**/api/sessions/{naam}", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps(sessie_data),
    ))


def stub_settings(
    page: Page,
    *,
    groq_rpm: int = 30,
    google_rpm: int = 15,
    groq_model: str | None = None,
    groq_models_beschikbaar: list[str] | None = None,
) -> None:
    """Registreert GET/PUT /api/settings. Geef groq_model/groq_models_beschikbaar
    alleen mee als de test de modeldropdown nodig heeft — anders blijft de
    stub-body net zo minimaal als de tests die alleen de RPM-velden gebruiken."""
    body: dict = {"groq_rpm": groq_rpm, "google_rpm": google_rpm}
    if groq_model is not None:
        body["groq_model"] = groq_model
    if groq_models_beschikbaar is not None:
        body["groq_models_beschikbaar"] = groq_models_beschikbaar
    body_json = json.dumps(body)

    def handle(route: Route) -> None:
        if route.request.method == "GET":
            route.fulfill(status=200, content_type="application/json", body=body_json)
        else:
            route.fulfill(status=200, content_type="application/json", body='{"status": "ok"}')

    page.route(SETTINGS_ROUTE, handle)


def stub_prompt_response(page: Page, **overrides) -> None:
    """Registreert POST /api/prompt met een succesvolle standaardrespons;
    overrides (bijv. runs=[...], reviewer_stappen=[...], eindoutput=...)
    overschrijven of vullen die standaardrespons aan."""
    body = {**DEFAULT_RUN_RESPONSE, **overrides}
    page.route(PROMPT_ROUTE, lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps(body),
    ))
