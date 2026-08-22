"""
Backend-tests voor story 08: Review pipeline — iteratief verbeteren.

AC gedekt:
- Sessie zonder reviewers gedraagt zich ongewijzigd
- Aanvraag met reviewer geeft HTTP 200 en bevat 'reviewer_stappen' in de respons
- Reviewer ontvangt de output van de hoofdprompt als te reviewen tekst
- Reviewerprompt vermeldt de reviewerrol
- Reviewerprompt bevat het label 'Reviewfocus:' en de omschrijving
- Reviewer zonder omschrijving wordt afgewezen met 422
- Elke volgende stap ontvangt de output van de vorige stap
- Volgorde: hoofdprompt → reviewer1 run1 → reviewer1 run2 → reviewer2 run1
- Resultaat bevat de uitvoer van elke stap afzonderlijk via 'reviewer_stappen'
- Eindoutput is de output van de laatste stap
- Bij 1 reviewer met 1 run zijn er 2 logbestanden (1 hoofd + 1 reviewer)
- Bij 2 reviewers (2+1 runs) zijn er 4 logbestanden (1 hoofd + 3 reviewer)
- Logbestand van reviewerstap bevat de rol én omschrijving van de reviewer
- Sessie opslaan bevat 'reviewers' (met omschrijving) en 'review_modus'
- Sessie laden geeft 'reviewers' (met omschrijving) en 'review_modus' terug
- Bestaande sessies zonder 'reviewers' worden geladen zonder fout
"""
import json
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.asyncio

OMSCHRIJVING_QA = "Controleer op volledigheid en correctheid van de uitleg."
OMSCHRIJVING_DEV = "Verbeter de structuur en formulering zodat de tekst helder is."

BASE_PAYLOAD = {
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "sessie": "mijn-sessie",
    "provider": "ollama",
    "runs": 1,
    "temperature_modus": "alle",
    "temperatures": [0.7],
}

PAYLOAD_MET_REVIEWER = {
    **BASE_PAYLOAD,
    "reviewers": [
        {"rol": "kritische QA engineer", "omschrijving": OMSCHRIJVING_QA, "runs": 1, "temperatures": [0.5]},
    ],
    "review_modus": "iteratief",
}

PAYLOAD_MET_TWEE_REVIEWERS = {
    **BASE_PAYLOAD,
    "reviewers": [
        {"rol": "QA engineer", "omschrijving": OMSCHRIJVING_QA, "runs": 2, "temperatures": [0.5, 0.8]},
        {"rol": "senior developer", "omschrijving": OMSCHRIJVING_DEV, "runs": 1, "temperatures": [0.7]},
    ],
    "review_modus": "iteratief",
}

SESSIE_MET_REVIEWERS = {
    "name": "sessie-met-reviewers",
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "provider": "ollama",
    "reviewers": [
        {"rol": "kritische QA engineer", "omschrijving": OMSCHRIJVING_QA, "runs": 2, "temperatures": [0.5, 0.8]},
    ],
    "review_modus": "iteratief",
}

SESSIE_ZONDER_REVIEWERS = {
    "name": "sessie-zonder-reviewers",
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "provider": "ollama",
}


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Sessie zonder reviewers — ongewijzigd gedrag
# ---------------------------------------------------------------------------

async def test_sessie_zonder_reviewers_geeft_200(client, logs_dir):
    """Een aanvraag zonder reviewers werkt ongewijzigd."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=BASE_PAYLOAD)
    assert response.status_code == 200


async def test_sessie_zonder_reviewers_heeft_runs_in_resultaat(client, logs_dir):
    """Een aanvraag zonder reviewers geeft het bestaande 'runs'-formaat terug."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=BASE_PAYLOAD)
    assert "runs" in response.json()


# ---------------------------------------------------------------------------
# Aanvraag met één reviewer
# ---------------------------------------------------------------------------

async def test_met_reviewer_retourneert_reviewer_stappen(client, logs_dir):
    """Een aanvraag met reviewer geeft een respons met 'reviewer_stappen'."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)
    assert response.status_code == 200
    assert "reviewer_stappen" in response.json(), (
        f"'reviewer_stappen' ontbreekt in respons: {list(response.json().keys())}"
    )


async def test_reviewer_ontvangt_output_van_hoofdprompt(client, logs_dir):
    """De reviewer krijgt de output van de hoofdprompt als te reviewen tekst."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return f"antwoord_{len(aanroepen)}"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    assert len(aanroepen) == 2, f"Verwacht 2 aanroepen, kreeg {len(aanroepen)}"
    reviewerprompt = aanroepen[1]
    assert "antwoord_1" in reviewerprompt, (
        f"Output van hoofdprompt ontbreekt in reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_bevat_reviewer_rol(client, logs_dir):
    """De reviewerprompt vermeldt de reviewerrol."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    reviewerprompt = aanroepen[1]
    assert "kritische QA engineer" in reviewerprompt, (
        f"Reviewerrol ontbreekt in prompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_bevat_reviewfocus_label(client, logs_dir):
    """De reviewerprompt bevat het label 'Reviewfocus:'."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    reviewerprompt = aanroepen[1]
    assert "Reviewfocus:" in reviewerprompt, (
        f"'Reviewfocus:' ontbreekt in reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_bevat_omschrijving(client, logs_dir):
    """De reviewerprompt bevat de omschrijving van de reviewer."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    reviewerprompt = aanroepen[1]
    assert OMSCHRIJVING_QA in reviewerprompt, (
        f"Omschrijving ontbreekt in reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_iteratief_bevat_verbetering_instructie(client, logs_dir):
    """Bij iteratief modus bevat de reviewerprompt een instructie om een verbeterde versie te produceren."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    reviewerprompt = aanroepen[1]
    assert "verbeterde en complete versie" in reviewerprompt, (
        f"Verbeteringsinstructie ontbreekt in iteratief reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_zonder_omschrijving_geeft_422(client, logs_dir):
    """Een reviewer zonder omschrijving wordt afgewezen met 422."""
    payload = {
        **BASE_PAYLOAD,
        "reviewers": [{"rol": "QA engineer", "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    response = await client.post("/api/prompt", json=payload)
    assert response.status_code == 422, (
        f"Verwacht 422 voor reviewer zonder omschrijving, kreeg {response.status_code}"
    )


# ---------------------------------------------------------------------------
# Twee reviewers — iteratieve keten
# ---------------------------------------------------------------------------

async def test_volgorde_is_hoofd_reviewer1_run1_run2_reviewer2(client, logs_dir):
    """De volgorde is: hoofdprompt → reviewer1 run1 → reviewer1 run2 → reviewer2 run1."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return f"v{len(aanroepen)}"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_TWEE_REVIEWERS)

    assert len(aanroepen) == 4, (
        f"Verwacht 4 aanroepen (1 hoofd + 2 reviewer1 + 1 reviewer2), kreeg {len(aanroepen)}"
    )


async def test_reviewer1_run2_ontvangt_output_van_reviewer1_run1(client, logs_dir):
    """Reviewer1 run2 krijgt de output van reviewer1 run1, niet van de hoofdprompt."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return f"v{len(aanroepen)}"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_TWEE_REVIEWERS)

    # Aanroep 3 (index 2) is reviewer1 run2 — moet "v2" bevatten
    assert "v2" in aanroepen[2], (
        f"Reviewer1 run2 ontvangt niet de output van reviewer1 run1: {aanroepen[2]!r}"
    )


async def test_reviewer2_ontvangt_output_van_laatste_reviewer1_run(client, logs_dir):
    """Reviewer2 krijgt de output van de laatste run van reviewer1."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return f"v{len(aanroepen)}"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_TWEE_REVIEWERS)

    # Aanroep 4 (index 3) is reviewer2 run1 — moet "v3" bevatten
    assert "v3" in aanroepen[3], (
        f"Reviewer2 ontvangt niet de output van reviewer1 run2: {aanroepen[3]!r}"
    )


# ---------------------------------------------------------------------------
# Resultaat — uitvoer per stap en eindoutput
# ---------------------------------------------------------------------------

async def test_resultaat_bevat_alle_reviewer_stappen(client, logs_dir):
    """Het resultaat bevat alle reviewer-stappen in 'reviewer_stappen'."""
    aanroep = [0]

    async def vang_aanroepen(prompt, temperature):
        aanroep[0] += 1
        return f"v{aanroep[0]}"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        response = await client.post("/api/prompt", json=PAYLOAD_MET_TWEE_REVIEWERS)

    data = response.json()
    assert len(data["reviewer_stappen"]) == 3, (
        f"Verwacht 3 reviewer-stappen, kreeg {len(data['reviewer_stappen'])}"
    )


async def test_eindoutput_is_output_van_laatste_stap(client, logs_dir):
    """De eindoutput is de output van de laatste reviewer-run."""
    aanroep = [0]

    async def vang_aanroepen(prompt, temperature):
        aanroep[0] += 1
        return f"v{aanroep[0]}"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        response = await client.post("/api/prompt", json=PAYLOAD_MET_TWEE_REVIEWERS)

    data = response.json()
    assert data.get("eindoutput") == "v4", (
        f"Eindoutput is niet de output van de laatste stap: {data.get('eindoutput')!r}"
    )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

async def test_twee_logbestanden_bij_een_reviewer(client, logs_dir):
    """Bij 1 reviewer met 1 run zijn er 2 logbestanden: 1 hoofd + 1 reviewer."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    logbestanden = list(logs_dir.iterdir())
    assert len(logbestanden) == 2, (
        f"Verwacht 2 logbestanden (hoofd + reviewer), gevonden: {len(logbestanden)}"
    )


async def test_vier_logbestanden_bij_twee_reviewers(client, logs_dir):
    """Bij 2 reviewers (2+1 runs) zijn er 4 logbestanden: 1 hoofd + 3 reviewer."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=PAYLOAD_MET_TWEE_REVIEWERS)

    logbestanden = list(logs_dir.iterdir())
    assert len(logbestanden) == 4, (
        f"Verwacht 4 logbestanden, gevonden: {len(logbestanden)}"
    )


async def test_reviewerstap_log_heeft_reviewer_in_bestandsnaam(client, logs_dir):
    """Logbestanden van reviewerstappen zijn herkenbaar aan hun bestandsnaam."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    reviewer_logs = [
        f for f in logs_dir.iterdir()
        if "reviewer" in f.name.lower()
    ]
    assert len(reviewer_logs) >= 1, (
        f"Geen logbestand met 'reviewer' in de naam gevonden: "
        f"{[f.name for f in logs_dir.iterdir()]}"
    )


async def test_reviewerstap_log_bevat_reviewer_identificatie(client, logs_dir):
    """Het logbestand van een reviewerstap bevat velden die de stap identificeren."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    reviewer_logs = [
        f for f in logs_dir.iterdir()
        if "reviewer" in f.name.lower()
    ]
    data = json.loads(reviewer_logs[0].read_text(encoding="utf-8"))
    heeft_identificatie = "reviewer_nr" in data or "reviewer_rol" in data
    assert heeft_identificatie, (
        f"Reviewer-identificatie ontbreekt in logbestand: {list(data.keys())}"
    )


async def test_reviewerstap_log_bevat_omschrijving(client, logs_dir):
    """Het logbestand van een reviewerstap bevat de omschrijving van de reviewer."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    reviewer_logs = [
        f for f in logs_dir.iterdir()
        if "reviewer" in f.name.lower()
    ]
    data = json.loads(reviewer_logs[0].read_text(encoding="utf-8"))
    assert "reviewer_omschrijving" in data, (
        f"'reviewer_omschrijving' ontbreekt in logbestand: {list(data.keys())}"
    )
    assert data["reviewer_omschrijving"] == OMSCHRIJVING_QA


# ---------------------------------------------------------------------------
# Sessie opslaan en laden
# ---------------------------------------------------------------------------

async def test_sessie_opslaan_bevat_reviewers(client, tmp_path, monkeypatch):
    """Opgeslagen sessie bevat het veld 'reviewers'."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_MET_REVIEWERS)
    data = json.loads((tmp_path / "sessie-met-reviewers.json").read_text(encoding="utf-8"))
    assert "reviewers" in data
    assert len(data["reviewers"]) == 1
    assert data["reviewers"][0]["rol"] == "kritische QA engineer"


async def test_sessie_opslaan_bevat_omschrijving_per_reviewer(client, tmp_path, monkeypatch):
    """Opgeslagen sessie bevat de omschrijving per reviewer."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_MET_REVIEWERS)
    data = json.loads((tmp_path / "sessie-met-reviewers.json").read_text(encoding="utf-8"))
    reviewer = data["reviewers"][0]
    assert "omschrijving" in reviewer, (
        f"'omschrijving' ontbreekt in opgeslagen reviewer: {list(reviewer.keys())}"
    )
    assert reviewer["omschrijving"] == OMSCHRIJVING_QA


async def test_sessie_opslaan_bevat_review_modus(client, tmp_path, monkeypatch):
    """Opgeslagen sessie bevat het veld 'review_modus' met waarde 'iteratief'."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_MET_REVIEWERS)
    data = json.loads((tmp_path / "sessie-met-reviewers.json").read_text(encoding="utf-8"))
    assert "review_modus" in data
    assert data["review_modus"] == "iteratief"


async def test_sessie_laden_geeft_reviewers_terug(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie worden de reviewers meegeleverd."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "sessie-met-reviewers.json").write_text(
        json.dumps(SESSIE_MET_REVIEWERS, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/sessie-met-reviewers")
    assert response.status_code == 200
    data = response.json()
    assert "reviewers" in data
    assert data["reviewers"][0]["rol"] == "kritische QA engineer"


async def test_sessie_laden_geeft_omschrijving_terug(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie wordt de omschrijving per reviewer meegeleverd."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "sessie-met-reviewers.json").write_text(
        json.dumps(SESSIE_MET_REVIEWERS, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/sessie-met-reviewers")
    assert response.status_code == 200
    reviewer = response.json()["reviewers"][0]
    assert "omschrijving" in reviewer, (
        f"'omschrijving' ontbreekt in geladen reviewer: {list(reviewer.keys())}"
    )
    assert reviewer["omschrijving"] == OMSCHRIJVING_QA


async def test_sessie_laden_geeft_review_modus_terug(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie wordt 'review_modus' meegeleverd."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "sessie-met-reviewers.json").write_text(
        json.dumps(SESSIE_MET_REVIEWERS, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/sessie-met-reviewers")
    assert response.status_code == 200
    assert response.json()["review_modus"] == "iteratief"


async def test_bestaande_sessie_zonder_reviewers_laadt_zonder_fout(client, tmp_path, monkeypatch):
    """Bestaande sessies zonder 'reviewers' worden geladen zonder fout."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "sessie-zonder-reviewers.json").write_text(
        json.dumps(SESSIE_ZONDER_REVIEWERS, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/sessie-zonder-reviewers")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Reviewer prompt — optionele velden en bijlage als context
# ---------------------------------------------------------------------------

async def test_reviewer_prompt_bevat_formaat_als_ingesteld(client, logs_dir):
    """De reviewerprompt bevat het formaat als dat is ingesteld."""
    payload = {
        **BASE_PAYLOAD,
        "formaat": "Python code met pytest",
        "reviewers": [{"rol": "QA engineer", "omschrijving": OMSCHRIJVING_QA, "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=payload)

    reviewerprompt = aanroepen[1]
    assert "Python code met pytest" in reviewerprompt, (
        f"Formaat ontbreekt in reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_bevat_stijl_als_ingesteld(client, logs_dir):
    """De reviewerprompt bevat de stijl als die is ingesteld."""
    payload = {
        **BASE_PAYLOAD,
        "stijl": "beknopt, geen uitleg",
        "reviewers": [{"rol": "QA engineer", "omschrijving": OMSCHRIJVING_QA, "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=payload)

    reviewerprompt = aanroepen[1]
    assert "beknopt, geen uitleg" in reviewerprompt, (
        f"Stijl ontbreekt in reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_bevat_scope_als_ingesteld(client, logs_dir):
    """De reviewerprompt bevat de scope als die is ingesteld."""
    payload = {
        **BASE_PAYLOAD,
        "scope": "alleen unit tests",
        "reviewers": [{"rol": "QA engineer", "omschrijving": OMSCHRIJVING_QA, "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=payload)

    reviewerprompt = aanroepen[1]
    assert "alleen unit tests" in reviewerprompt, (
        f"Scope ontbreekt in reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_bevat_eisen_als_ingesteld(client, logs_dir):
    """De reviewerprompt bevat de extra eisen als die zijn ingesteld."""
    payload = {
        **BASE_PAYLOAD,
        "eisen": "gebruik fixtures",
        "reviewers": [{"rol": "QA engineer", "omschrijving": OMSCHRIJVING_QA, "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=payload)

    reviewerprompt = aanroepen[1]
    assert "gebruik fixtures" in reviewerprompt, (
        f"Extra eisen ontbreken in reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_bevat_voorbeelden_als_ingesteld(client, logs_dir):
    """De reviewerprompt bevat de voorbeelden als die zijn ingesteld."""
    payload = {
        **BASE_PAYLOAD,
        "voorbeelden": "def test_login(): ...",
        "reviewers": [{"rol": "QA engineer", "omschrijving": OMSCHRIJVING_QA, "runs": 1, "temperatures": [0.5]}],
        "review_modus": "iteratief",
    }
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=payload)

    reviewerprompt = aanroepen[1]
    assert "def test_login(): ..." in reviewerprompt, (
        f"Voorbeelden ontbreken in reviewerprompt: {reviewerprompt!r}"
    )


async def test_reviewer_prompt_bevat_geen_originele_eisen_als_niets_ingesteld(client, logs_dir):
    """Als geen optionele velden zijn ingesteld, bevat de reviewerprompt geen 'Originele eisen:'."""
    aanroepen = []

    async def vang_aanroepen(prompt, temperature):
        aanroepen.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_aanroepen):
        await client.post("/api/prompt", json=PAYLOAD_MET_REVIEWER)

    reviewerprompt = aanroepen[1]
    assert "Originele eisen:" not in reviewerprompt, (
        f"'Originele eisen:' staat onterecht in reviewerprompt: {reviewerprompt!r}"
    )


def test_reviewer_prompt_bevat_bijlage_als_aanwezig():
    """De reviewerprompt bevat de bijlagetekst als die aanwezig is."""
    from app import bouw_reviewer_prompt, PromptRequest

    body = PromptRequest(
        rol="tester", taak="testen", doel="kwaliteit",
        provider="ollama", runs=1, temperature_modus="alle", temperatures=[0.7],
    )
    prompt = bouw_reviewer_prompt(
        reviewer_rol="QA engineer",
        reviewer_omschrijving=OMSCHRIJVING_QA,
        body=body,
        vorige_output="output tekst",
        review_modus="iteratief",
        bijlage_tekst="dit is de bijlage",
    )
    assert "dit is de bijlage" in prompt, f"Bijlagetekst ontbreekt in reviewerprompt: {prompt!r}"


def test_reviewer_prompt_bevat_geen_bijlage_sectie_als_niet_aanwezig():
    """Als er geen bijlage is, bevat de reviewerprompt geen 'Bijlage:'-sectie."""
    from app import bouw_reviewer_prompt, PromptRequest

    body = PromptRequest(
        rol="tester", taak="testen", doel="kwaliteit",
        provider="ollama", runs=1, temperature_modus="alle", temperatures=[0.7],
    )
    prompt = bouw_reviewer_prompt(
        reviewer_rol="QA engineer",
        reviewer_omschrijving=OMSCHRIJVING_QA,
        body=body,
        vorige_output="output tekst",
        review_modus="iteratief",
        bijlage_tekst=None,
    )
    assert "Bijlage:" not in prompt, f"'Bijlage:' staat onterecht in reviewerprompt: {prompt!r}"
