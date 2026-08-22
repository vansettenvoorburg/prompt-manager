"""
Backend-tests voor story 14: bugfixes uit code review.

Vereist: geen — de `server`-fixture (tests/conftest.py) start de app automatisch op de testpoort.

AC gedekt:
- ALGEMEEN-V-01 — sessienaam met onveilige bestandsnaamtekens wordt gesaneerd in het logbestand
  (hoofdrun en reviewerstap), en het logbestand blijft binnen de logmap
- ALGEMEEN-V-02 — hetzelfde geldt voor de providerwaarde
- ALGEMEEN-V-03 — sessienaam/provider met alleen toegestane tekens blijft ongewijzigd in de
  bestandsnaam
- IMPORT-V-04 — ongeldige 'runs' of ongeldige reviewer-configuratie bij een aanvraag mét bijlage
  geeft dezelfde foutmelding als bij hetzelfde probleem zonder bijlage
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio

_ONVEILIGE_TEKENS = '<>:"/\\|?*'

_ONVEILIGE_WAARDEN = [
    "../../etc/passwd",
    "sessie/naam",
    "sessie\\naam",
    "sessie:naam",
    "sessie*naam",
    "sessie?naam",
]

BASE_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "mijn-sessie",
    "provider": "ollama",
}

BASE_FORM = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "mijn-sessie",
    "provider": "ollama",
    "runs": "1",
    "temperature_modus": "alle",
    "temperatures": "[0.7]",
    "reviewers": "[]",
    "review_modus": "iteratief",
}


# ---------------------------------------------------------------------------
# ALGEMEEN-V-01 — sessienaam met onveilige tekens
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("onveilige_sessie", _ONVEILIGE_WAARDEN)
async def test_sessienaam_met_onveilige_tekens_blijft_binnen_logmap_bij_hoofdrun(tmp_path, monkeypatch, onveilige_sessie):
    """Een sessienaam met onveilige bestandsnaamtekens levert bij een hoofdrun-logbestand
    nog steeds een pad binnen de logmap op, met die tekens vervangen."""
    from app import PromptRequest, _schrijf_log

    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    body = PromptRequest(rol="tester", taak="testen", doel="kwaliteit", provider="ollama", sessie=onveilige_sessie)

    pad, fout = _schrijf_log(body, "prompt", "antwoord", datetime.now(), 0.1, "model-x", 1, 0.7)

    assert fout is None, f"Onverwachte fout bij wegschrijven logbestand: {fout}"
    assert pad.parent == tmp_path, f"Logbestand belandde buiten de logmap: {pad}"


@pytest.mark.parametrize("onveilige_sessie", _ONVEILIGE_WAARDEN)
async def test_sessienaam_met_onveilige_tekens_bevat_geen_onveilige_tekens_in_bestandsnaam_bij_hoofdrun(tmp_path, monkeypatch, onveilige_sessie):
    """De onveilige tekens uit de sessienaam komen niet terug in de bestandsnaam van een
    hoofdrun-logbestand."""
    from app import PromptRequest, _schrijf_log

    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    body = PromptRequest(rol="tester", taak="testen", doel="kwaliteit", provider="ollama", sessie=onveilige_sessie)

    pad, _fout = _schrijf_log(body, "prompt", "antwoord", datetime.now(), 0.1, "model-x", 1, 0.7)

    for teken in _ONVEILIGE_TEKENS:
        assert teken not in pad.name, f"Onveilig teken {teken!r} nog aanwezig in bestandsnaam: {pad.name}"


@pytest.mark.parametrize("onveilige_sessie", _ONVEILIGE_WAARDEN)
async def test_sessienaam_met_onveilige_tekens_blijft_binnen_logmap_bij_reviewerstap(tmp_path, monkeypatch, onveilige_sessie):
    """Een sessienaam met onveilige bestandsnaamtekens levert bij een reviewerstap-logbestand
    nog steeds een pad binnen de logmap op."""
    from app import PromptRequest, _schrijf_reviewer_log

    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    body = PromptRequest(rol="tester", taak="testen", doel="kwaliteit", provider="ollama", sessie=onveilige_sessie)

    pad, fout = _schrijf_reviewer_log(
        body, 1, "QA engineer", "Controleer volledigheid.", 1, 0.5, "prompt", "antwoord", datetime.now(), 0.1, "model-x",
    )

    assert fout is None, f"Onverwachte fout bij wegschrijven logbestand: {fout}"
    assert pad.parent == tmp_path, f"Logbestand belandde buiten de logmap: {pad}"
    for teken in _ONVEILIGE_TEKENS:
        assert teken not in pad.name, f"Onveilig teken {teken!r} nog aanwezig in bestandsnaam: {pad.name}"


# ---------------------------------------------------------------------------
# ALGEMEEN-V-02 — providerwaarde met onveilige tekens
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("onveilige_provider", _ONVEILIGE_WAARDEN)
async def test_provider_met_onveilige_tekens_blijft_binnen_logmap_bij_hoofdrun(tmp_path, monkeypatch, onveilige_provider):
    """Een providerwaarde met onveilige bestandsnaamtekens levert bij een hoofdrun-logbestand
    nog steeds een pad binnen de logmap op, met die tekens vervangen."""
    from app import PromptRequest, _schrijf_log

    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    body = PromptRequest(rol="tester", taak="testen", doel="kwaliteit", provider=onveilige_provider, sessie="mijn-sessie")

    pad, fout = _schrijf_log(body, "prompt", "antwoord", datetime.now(), 0.1, "model-x", 1, 0.7)

    assert fout is None, f"Onverwachte fout bij wegschrijven logbestand: {fout}"
    assert pad.parent == tmp_path, f"Logbestand belandde buiten de logmap: {pad}"
    for teken in _ONVEILIGE_TEKENS:
        assert teken not in pad.name, f"Onveilig teken {teken!r} nog aanwezig in bestandsnaam: {pad.name}"


@pytest.mark.parametrize("onveilige_provider", _ONVEILIGE_WAARDEN)
async def test_provider_met_onveilige_tekens_blijft_binnen_logmap_bij_reviewerstap(tmp_path, monkeypatch, onveilige_provider):
    """Een providerwaarde met onveilige bestandsnaamtekens levert bij een reviewerstap-logbestand
    nog steeds een pad binnen de logmap op, met die tekens vervangen."""
    from app import PromptRequest, _schrijf_reviewer_log

    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    body = PromptRequest(rol="tester", taak="testen", doel="kwaliteit", provider=onveilige_provider, sessie="mijn-sessie")

    pad, fout = _schrijf_reviewer_log(
        body, 1, "QA engineer", "Controleer volledigheid.", 1, 0.5, "prompt", "antwoord", datetime.now(), 0.1, "model-x",
    )

    assert fout is None, f"Onverwachte fout bij wegschrijven logbestand: {fout}"
    assert pad.parent == tmp_path, f"Logbestand belandde buiten de logmap: {pad}"
    for teken in _ONVEILIGE_TEKENS:
        assert teken not in pad.name, f"Onveilig teken {teken!r} nog aanwezig in bestandsnaam: {pad.name}"


# ---------------------------------------------------------------------------
# ALGEMEEN-V-03 — alleen toegestane tekens blijft ongewijzigd
# ---------------------------------------------------------------------------

async def test_veilige_sessienaam_blijft_ongewijzigd_in_bestandsnaam(tmp_path, monkeypatch):
    """Een sessienaam die alleen toegestane tekens bevat, komt ongewijzigd terug in de
    bestandsnaam van het hoofdrun-logbestand."""
    from app import PromptRequest, _schrijf_log

    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    body = PromptRequest(rol="tester", taak="testen", doel="kwaliteit", provider="ollama", sessie="mijn-veilige-sessie")

    pad, _fout = _schrijf_log(body, "prompt", "antwoord", datetime.now(), 0.1, "model-x", 1, 0.7)

    assert "mijn-veilige-sessie" in pad.name, f"Oorspronkelijke sessienaam ontbreekt in bestandsnaam: {pad.name}"


async def test_veilige_providerwaarde_blijft_ongewijzigd_in_bestandsnaam(tmp_path, monkeypatch):
    """Een providerwaarde die alleen toegestane tekens bevat, komt ongewijzigd terug in de
    bestandsnaam van het hoofdrun-logbestand."""
    from app import PromptRequest, _schrijf_log

    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    body = PromptRequest(rol="tester", taak="testen", doel="kwaliteit", provider="ollama", sessie="mijn-sessie")

    pad, _fout = _schrijf_log(body, "prompt", "antwoord", datetime.now(), 0.1, "model-x", 1, 0.7)

    assert "ollama" in pad.name, f"Oorspronkelijke providerwaarde ontbreekt in bestandsnaam: {pad.name}"


# ---------------------------------------------------------------------------
# IMPORT-V-04 — validatie-pariteit met en zonder bijlage
# ---------------------------------------------------------------------------

async def test_ongeldige_runs_bij_upload_geeft_foutmelding(client, tmp_path, monkeypatch):
    """Een niet-numerieke 'runs'-waarde bij /api/prompt/upload geeft een foutmelding in
    plaats van stilzwijgend met 1 run uit te voeren."""
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    form = {**BASE_FORM, "runs": "abc"}

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post(
            "/api/prompt/upload", data=form,
            files={"bijlage": ("notitie.txt", b"inhoud", "text/plain")},
        )

    assert response.status_code in (400, 422), (
        f"Verwacht een foutmelding voor ongeldige 'runs', kreeg {response.status_code}: {response.text}"
    )


async def test_ongeldige_runs_geeft_zelfde_statuscode_met_en_zonder_bijlage(client, tmp_path, monkeypatch):
    """Een ongeldige 'runs'-waarde geeft dezelfde statuscode met bijlage als zonder bijlage."""
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        json_response = await client.post("/api/prompt", json={**BASE_PAYLOAD, "runs": "abc"})

        upload_response = await client.post(
            "/api/prompt/upload", data={**BASE_FORM, "runs": "abc"},
            files={"bijlage": ("notitie.txt", b"inhoud", "text/plain")},
        )

    assert upload_response.status_code == json_response.status_code, (
        f"Verschillende statuscodes voor ongeldige 'runs': zonder bijlage="
        f"{json_response.status_code}, met bijlage={upload_response.status_code}"
    )


async def test_ongeldige_reviewer_bij_upload_geeft_foutmelding(client, tmp_path, monkeypatch):
    """Een reviewer-configuratie zonder verplichte omschrijving bij /api/prompt/upload geeft
    een foutmelding in plaats van stilzwijgend zonder reviewers uit te voeren."""
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    reviewers = json.dumps([{"rol": "QA engineer", "runs": 1, "temperatures": [0.5]}])
    form = {**BASE_FORM, "reviewers": reviewers}

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post(
            "/api/prompt/upload", data=form,
            files={"bijlage": ("notitie.txt", b"inhoud", "text/plain")},
        )

    assert response.status_code in (400, 422), (
        f"Verwacht een foutmelding voor ongeldige reviewer-configuratie, kreeg "
        f"{response.status_code}: {response.text}"
    )


async def test_ongeldige_reviewer_geeft_zelfde_statuscode_met_en_zonder_bijlage(client, tmp_path, monkeypatch):
    """Een ongeldige reviewer-configuratie geeft dezelfde statuscode met bijlage als zonder
    bijlage."""
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    reviewers_payload = [{"rol": "QA engineer", "runs": 1, "temperatures": [0.5]}]

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        json_response = await client.post("/api/prompt", json={
            **BASE_PAYLOAD, "reviewers": reviewers_payload, "review_modus": "iteratief",
        })

        upload_response = await client.post(
            "/api/prompt/upload",
            data={**BASE_FORM, "reviewers": json.dumps(reviewers_payload)},
            files={"bijlage": ("notitie.txt", b"inhoud", "text/plain")},
        )

    assert upload_response.status_code == json_response.status_code, (
        f"Verschillende statuscodes voor ongeldige reviewer-configuratie: zonder bijlage="
        f"{json_response.status_code}, met bijlage={upload_response.status_code}"
    )


async def test_geldige_runs_en_reviewer_met_bijlage_blijft_werken(client, tmp_path, monkeypatch):
    """Regressie: geldige 'runs' en een geldige reviewer-configuratie bij een aanvraag met
    bijlage blijven normaal werken (runs-aantal en reviewerstap kloppen in de respons)."""
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    reviewers = json.dumps([
        {"rol": "QA engineer", "omschrijving": "Controleer volledigheid.", "runs": 1, "temperatures": [0.5]}
    ])
    form = {**BASE_FORM, "runs": "2", "temperatures": "[0.5, 0.7]", "reviewers": reviewers}

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post(
            "/api/prompt/upload", data=form,
            files={"bijlage": ("notitie.txt", b"inhoud", "text/plain")},
        )

    assert response.status_code == 200, f"Verwacht 200 voor geldige invoer met bijlage: {response.text}"
    data = response.json()
    assert len(data["runs"]) == 2, f"Verwacht 2 runs in de respons, kreeg: {data['runs']}"
    assert len(data["reviewer_stappen"]) > 0, f"Reviewer-stap ontbreekt in de respons: {data}"
