"""
Regressietest voor bug: Groq reasoning-tokens verbruiken onnodig veel van het TPM-budget
bij gpt-oss-modellen.

Gemeld gedrag: call_groq() stuurt geen 'reasoning_effort' mee in de JSON-body van de
aanroep naar de Groq API. Voor reasoning-modellen (de gpt-oss-familie) hanteert Groq
dan een hoog standaard redeneerniveau, wat een groot deel van het tokenbudget
opsoupeert zonder dat dit in het zichtbare antwoord terechtkomt. Gemeten met een
echte Groq-aanroep (model openai/gpt-oss-20b): zonder parameter 314 van de 606
tokens reasoning-tokens (~52%), met reasoning_effort=low nog maar 5 van de 499
tokens.

Verwacht gedrag: bij een aanroep naar een Groq-reasoningmodel (openai/gpt-oss-120b,
openai/gpt-oss-20b) bevat de uitgaande JSON-body 'reasoning_effort': 'low'. Bij
Groq-modellen zonder reasoning (qwen/qwen3.8-27b, allam-2-7b) en bij Ollama-aanroepen
blijft dit veld afwezig.

Mockt alleen de netwerklaag (httpx.AsyncClient.post), net als
tests/backend/test_backend_11_uitgaande_aanvraag.py, zodat de daadwerkelijke
uitgaande JSON-body van call_groq gecontroleerd wordt.
"""
import httpx
import pytest
from unittest.mock import patch

pytestmark = pytest.mark.asyncio

GROQ_REASONING_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

GROQ_NON_REASONING_MODELS = [
    "qwen/qwen3.8-27b",
    "allam-2-7b",
]

GROQ_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "reasoning-effort-test",
    "provider": "groq",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}

OLLAMA_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "reasoning-effort-test",
    "provider": "ollama",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}

_ECHTE_EXTERNE_PREFIXES = ("https://api.groq.com", "http://localhost:11434")
_ORIGINELE_ASYNC_CLIENT_POST = httpx.AsyncClient.post


@pytest.fixture
def groq_key(monkeypatch):
    monkeypatch.setattr("app.GROQ_API_KEY", "test-api-key")


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


def _stub_httpx_post(captured):
    async def fake_post(self, url, **kwargs):
        url_str = str(url)
        if not url_str.startswith(_ECHTE_EXTERNE_PREFIXES):
            return await _ORIGINELE_ASYNC_CLIENT_POST(self, url, **kwargs)

        captured.append({"url": url_str, "json": kwargs.get("json")})
        respons_data = {
            "response": "antwoord",
            "choices": [{"message": {"content": "antwoord"}}],
        }
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json=respons_data,
        )
    return fake_post


@pytest.mark.parametrize("model", GROQ_REASONING_MODELS)
async def test_reasoning_effort_low_bij_gpt_oss_modellen(client, groq_key, logs_dir, model):
    """Bij een gpt-oss-model bevat de uitgaande Groq-aanvraag reasoning_effort='low'."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured)):
        payload = {**GROQ_PAYLOAD, "model": model}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200, f"Model {model} gaf status {response.status_code}: {response.text}"
    assert captured[0]["json"].get("reasoning_effort") == "low", (
        f"Verwacht reasoning_effort='low' voor {model!r} in uitgaande aanvraag, "
        f"kreeg: {captured[0]['json']}"
    )


@pytest.mark.parametrize("model", GROQ_NON_REASONING_MODELS)
async def test_geen_reasoning_effort_bij_niet_reasoning_modellen(client, groq_key, logs_dir, model):
    """Bij een Groq-model zonder reasoning-ondersteuning blijft reasoning_effort afwezig."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured)):
        payload = {**GROQ_PAYLOAD, "model": model}
        response = await client.post("/api/prompt", json=payload)

    assert response.status_code == 200, f"Model {model} gaf status {response.status_code}: {response.text}"
    assert "reasoning_effort" not in captured[0]["json"], (
        f"Onterecht reasoning_effort voor {model!r} in uitgaande aanvraag: {captured[0]['json']}"
    )


async def test_geen_reasoning_effort_bij_ollama_aanvraag(client, logs_dir):
    """Bij provider 'ollama' bevat de uitgaande aanvraag geen reasoning_effort-veld."""
    captured = []
    with patch("httpx.AsyncClient.post", new=_stub_httpx_post(captured)):
        response = await client.post("/api/prompt", json=OLLAMA_PAYLOAD)

    assert response.status_code == 200
    assert len(captured) == 1, f"Verwacht 1 uitgaande aanvraag, kreeg {len(captured)}: {captured}"
    assert "reasoning_effort" not in captured[0]["json"], (
        f"Onterecht reasoning_effort in Ollama-aanvraag: {captured[0]['json']}"
    )
