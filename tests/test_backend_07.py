"""
Backend-tests voor story 07: Bijlage toevoegen aan een sessie.

AC gedekt:
- Ondersteunde bestandstypen worden geaccepteerd: .txt, .md, .py, .js, .ts, .html, .css, .json
- PDF-bestanden worden verwerkt via pymupdf (alleen tekst geëxtraheerd)
- Word-bestanden worden verwerkt via python-docx (alleen tekst geëxtraheerd)
- Niet-ondersteund bestandstype → HTTP 400 met melding "Niet-ondersteund bestandstype: ..."
- Leeg bestand → HTTP 400 met melding "Bijlage is leeg — upload een bestand met inhoud"
- PDF/Word extractiefout → HTTP 422 met melding "Bijlage kon niet worden gelezen: ..."
- Geëxtraheerde tekst wordt als "Bijlage:\n[tekst]" toegevoegd aan het einde van de prompt
- Bijlage wordt meegestuurd bij elke taak in de sessie
- Zonder bijlage ontbreekt het "Bijlage:"-blok volledig in de prompt
- Logbestand bevat veld "bijlage_bestandsnaam" (string of null)
- Logbestand bevat veld "bijlage_tekst" (string of null)
- Logbestandsnaam verandert niet door aanwezigheid van bijlage
- Bij fout in bijlageverwerking wordt geen logbestand aangemaakt
- Sessie opslaan bevat veld "bijlage_bestandsnaam" (string of null)
- Sessie laden geeft het veld "bijlage_bestandsnaam" terug
- Bestaande sessies zonder "bijlage_bestandsnaam" worden geladen zonder fout
"""
import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio

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

SESSIE_MET_BIJLAGE = {
    "name": "sessie-met-bijlage",
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "provider": "ollama",
    "bijlage_bestandsnaam": "document.pdf",
}

SESSIE_ZONDER_BIJLAGE = {
    "name": "sessie-zonder-bijlage",
    "rol": "Python developer",
    "taak": "een API bouwen",
    "doel": "data te verwerken",
    "provider": "ollama",
    "bijlage_bestandsnaam": None,
}


@pytest.fixture
def logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.LOGS_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Ondersteunde bestandstypen – tekst en code
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bestandsnaam", [
    "notities.txt",
    "readme.md",
    "script.py",
    "module.js",
    "types.ts",
    "pagina.html",
    "stijl.css",
    "config.json",
])
async def test_tekst_bestandstype_wordt_geaccepteerd(client, logs_dir, bestandsnaam):
    """Tekst- en codebestanden worden geaccepteerd en geven HTTP 200."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response = await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": (bestandsnaam, b"inhoud van het bestand", "text/plain")},
        )
    assert response.status_code == 200, (
        f"Verwacht 200 voor {bestandsnaam}, kreeg {response.status_code}: {response.text}"
    )


async def test_pdf_bestand_wordt_geaccepteerd(client, logs_dir):
    """PDF-bestanden worden geaccepteerd en geven HTTP 200."""
    pdf_inhoud = b"%PDF-1.4 nep-pdf-inhoud"
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"), \
         patch("app.extract_pdf_text", return_value="tekst uit PDF"):
        response = await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("document.pdf", pdf_inhoud, "application/pdf")},
        )
    assert response.status_code == 200


async def test_docx_bestand_wordt_geaccepteerd(client, logs_dir):
    """Word-bestanden worden geaccepteerd en geven HTTP 200."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"), \
         patch("app.extract_docx_text", return_value="tekst uit Word"):
        response = await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("verslag.docx", b"nep-docx-inhoud", "application/octet-stream")},
        )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Niet-ondersteund bestandstype
# ---------------------------------------------------------------------------

async def test_niet_ondersteund_type_geeft_400(client):
    """Een niet-ondersteund bestandstype retourneert HTTP 400."""
    response = await client.post(
        "/api/prompt/upload",
        data={k: str(v) for k, v in BASE_PAYLOAD.items()},
        files={"bijlage": ("foto.png", b"nep-afbeelding", "image/png")},
    )
    assert response.status_code == 400


async def test_niet_ondersteund_type_foutmelding_vermeldt_extensie(client):
    """De foutmelding bij een niet-ondersteund type vermeldt de extensie."""
    response = await client.post(
        "/api/prompt/upload",
        data={k: str(v) for k, v in BASE_PAYLOAD.items()},
        files={"bijlage": ("foto.png", b"nep-afbeelding", "image/png")},
    )
    detail = response.json()["detail"]
    assert ".png" in detail, f"Extensie '.png' ontbreekt in foutmelding: {detail!r}"


async def test_niet_ondersteund_type_foutmelding_vermeldt_ondersteunde_types(client):
    """De foutmelding bij een niet-ondersteund type vermeldt welke extensies wel geldig zijn."""
    response = await client.post(
        "/api/prompt/upload",
        data={k: str(v) for k, v in BASE_PAYLOAD.items()},
        files={"bijlage": ("data.xlsx", b"nep-excel", "application/octet-stream")},
    )
    detail = response.json()["detail"]
    assert ".pdf" in detail or ".txt" in detail, (
        f"Ondersteunde extensies ontbreken in foutmelding: {detail!r}"
    )


# ---------------------------------------------------------------------------
# Leeg bestand
# ---------------------------------------------------------------------------

async def test_leeg_bestand_geeft_400(client):
    """Een leeg geüpload bestand retourneert HTTP 400."""
    response = await client.post(
        "/api/prompt/upload",
        data={k: str(v) for k, v in BASE_PAYLOAD.items()},
        files={"bijlage": ("leeg.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


async def test_leeg_bestand_foutmelding(client):
    """De foutmelding bij een leeg bestand is de verwachte tekst."""
    response = await client.post(
        "/api/prompt/upload",
        data={k: str(v) for k, v in BASE_PAYLOAD.items()},
        files={"bijlage": ("leeg.txt", b"", "text/plain")},
    )
    detail = response.json()["detail"]
    assert "leeg" in detail.lower(), f"'leeg' ontbreekt in foutmelding: {detail!r}"


# ---------------------------------------------------------------------------
# Extractiefout PDF en Word
# ---------------------------------------------------------------------------

async def test_pdf_extractiefout_geeft_422(client):
    """Als PDF-extractie mislukt, retourneert de backend HTTP 422."""
    with patch("app.extract_pdf_text", side_effect=Exception("corrupt bestand")):
        response = await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("document.pdf", b"%PDF-nep", "application/pdf")},
        )
    assert response.status_code == 422


async def test_pdf_extractiefout_foutmelding_vermeldt_reden(client):
    """De foutmelding bij een PDF-extractiefout bevat de reden."""
    with patch("app.extract_pdf_text", side_effect=Exception("corrupt bestand")):
        response = await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("document.pdf", b"%PDF-nep", "application/pdf")},
        )
    detail = response.json()["detail"]
    assert "corrupt bestand" in detail, f"Reden ontbreekt in foutmelding: {detail!r}"


async def test_docx_extractiefout_geeft_422(client):
    """Als Word-extractie mislukt, retourneert de backend HTTP 422."""
    with patch("app.extract_docx_text", side_effect=Exception("onleesbaar bestand")):
        response = await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("verslag.docx", b"nep-docx", "application/octet-stream")},
        )
    assert response.status_code == 422


async def test_extractiefout_maakt_geen_logbestand(client, logs_dir):
    """Bij een extractiefout in de bijlageverwerking wordt geen logbestand aangemaakt."""
    with patch("app.extract_pdf_text", side_effect=Exception("corrupt")):
        await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("document.pdf", b"%PDF-nep", "application/pdf")},
        )
    assert len(list(logs_dir.iterdir())) == 0


# ---------------------------------------------------------------------------
# Prompt-opbouw: bijlage toegevoegd
# ---------------------------------------------------------------------------

async def test_bijlage_tekst_staat_in_prompt(client, logs_dir):
    """De bijlagetekst wordt als 'Bijlage:\n[tekst]' achteraan de prompt toegevoegd."""
    vastgelegde_prompt = []

    async def vang_prompt(prompt, temperature):
        vastgelegde_prompt.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_prompt):
        await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("notities.txt", b"dit zijn mijn notities", "text/plain")},
        )

    assert vastgelegde_prompt, "call_ollama is niet aangeroepen"
    prompt = vastgelegde_prompt[0]
    assert "Bijlage:" in prompt, f"'Bijlage:' ontbreekt in prompt: {prompt!r}"
    assert "dit zijn mijn notities" in prompt, f"Bijlagetekst ontbreekt in prompt: {prompt!r}"


async def test_bijlage_staat_aan_het_einde_van_prompt(client, logs_dir):
    """De 'Bijlage:'-sectie staat na de andere promptvelden."""
    vastgelegde_prompt = []

    async def vang_prompt(prompt, temperature):
        vastgelegde_prompt.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_prompt):
        await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("notities.txt", b"bijlagetekst", "text/plain")},
        )

    prompt = vastgelegde_prompt[0]
    bijlage_positie = prompt.index("Bijlage:")
    taak_positie = prompt.index("een API bouwen")
    assert bijlage_positie > taak_positie, (
        f"'Bijlage:' staat vóór de taakomschrijving in de prompt"
    )


async def test_zonder_bijlage_geen_bijlage_label_in_prompt(client, logs_dir):
    """Zonder bijlage ontbreekt het 'Bijlage:'-blok volledig in de prompt."""
    vastgelegde_prompt = []

    async def vang_prompt(prompt, temperature):
        vastgelegde_prompt.append(prompt)
        return "antwoord"

    with patch("app.call_ollama", side_effect=vang_prompt):
        await client.post("/api/prompt", json=BASE_PAYLOAD)

    assert vastgelegde_prompt, "call_ollama is niet aangeroepen"
    assert "Bijlage:" not in vastgelegde_prompt[0], (
        f"'Bijlage:' staat onterecht in prompt zonder bijlage: {vastgelegde_prompt[0]!r}"
    )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

async def test_logbestand_bevat_bijlage_bestandsnaam(client, logs_dir):
    """Het logbestand bevat het veld 'bijlage_bestandsnaam' als string."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("notities.txt", b"inhoud", "text/plain")},
        )
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert "bijlage_bestandsnaam" in data
    assert data["bijlage_bestandsnaam"] == "notities.txt"


async def test_logbestand_bevat_bijlage_tekst(client, logs_dir):
    """Het logbestand bevat het veld 'bijlage_tekst' met de geëxtraheerde tekst."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("notities.txt", b"dit zijn mijn notities", "text/plain")},
        )
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert "bijlage_tekst" in data
    assert "dit zijn mijn notities" in data["bijlage_tekst"]


async def test_logbestand_bijlage_bestandsnaam_is_null_zonder_bijlage(client, logs_dir):
    """Zonder bijlage is 'bijlage_bestandsnaam' in het logbestand null."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=BASE_PAYLOAD)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert "bijlage_bestandsnaam" in data
    assert data["bijlage_bestandsnaam"] is None


async def test_logbestand_bijlage_tekst_is_null_zonder_bijlage(client, logs_dir):
    """Zonder bijlage is 'bijlage_tekst' in het logbestand null."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post("/api/prompt", json=BASE_PAYLOAD)
    bestand = next(logs_dir.iterdir())
    data = json.loads(bestand.read_text(encoding="utf-8"))
    assert "bijlage_tekst" in data
    assert data["bijlage_tekst"] is None


async def test_logbestandsnaam_verandert_niet_door_bijlage(client, logs_dir):
    """De aanwezigheid van een bijlage verandert de naam van het logbestand niet."""
    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        response_zonder = await client.post("/api/prompt", json=BASE_PAYLOAD)
    naam_zonder = list(logs_dir.iterdir())[0].name

    for f in logs_dir.iterdir():
        f.unlink()

    with patch("app.call_ollama", new_callable=AsyncMock, return_value="antwoord"):
        await client.post(
            "/api/prompt/upload",
            data={k: str(v) for k, v in BASE_PAYLOAD.items()},
            files={"bijlage": ("notities.txt", b"inhoud", "text/plain")},
        )
    naam_met = list(logs_dir.iterdir())[0].name

    assert naam_zonder == naam_met, (
        f"Logbestandsnaam veranderde door bijlage: {naam_zonder!r} → {naam_met!r}"
    )


# ---------------------------------------------------------------------------
# Sessie opslaan en laden
# ---------------------------------------------------------------------------

async def test_sessie_opslaan_bevat_bijlage_bestandsnaam(client, tmp_path, monkeypatch):
    """Opgeslagen sessie bevat het veld 'bijlage_bestandsnaam'."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_MET_BIJLAGE)
    data = json.loads((tmp_path / "sessie-met-bijlage.json").read_text(encoding="utf-8"))
    assert "bijlage_bestandsnaam" in data
    assert data["bijlage_bestandsnaam"] == "document.pdf"


async def test_sessie_opslaan_null_bijlage_bestandsnaam(client, tmp_path, monkeypatch):
    """Opgeslagen sessie zonder bijlage bevat 'bijlage_bestandsnaam': null."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    await client.post("/api/sessions", json=SESSIE_ZONDER_BIJLAGE)
    data = json.loads((tmp_path / "sessie-zonder-bijlage.json").read_text(encoding="utf-8"))
    assert "bijlage_bestandsnaam" in data
    assert data["bijlage_bestandsnaam"] is None


async def test_sessie_laden_geeft_bijlage_bestandsnaam_terug(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie wordt 'bijlage_bestandsnaam' meegeleverd."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "sessie-met-bijlage.json").write_text(
        json.dumps(SESSIE_MET_BIJLAGE, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/sessie-met-bijlage")
    assert response.status_code == 200
    assert response.json()["bijlage_bestandsnaam"] == "document.pdf"


async def test_sessie_laden_null_bijlage_bestandsnaam(client, tmp_path, monkeypatch):
    """Bij het laden van een sessie zonder bijlage is 'bijlage_bestandsnaam' null."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    (tmp_path / "sessie-zonder-bijlage.json").write_text(
        json.dumps(SESSIE_ZONDER_BIJLAGE, ensure_ascii=False), encoding="utf-8"
    )
    response = await client.get("/api/sessions/sessie-zonder-bijlage")
    assert response.status_code == 200
    assert response.json()["bijlage_bestandsnaam"] is None


async def test_bestaande_sessie_zonder_bijlage_veld_laadt_zonder_fout(client, tmp_path, monkeypatch):
    """Bestaande sessiebestanden zonder 'bijlage_bestandsnaam' worden geladen zonder fout."""
    monkeypatch.setattr("app.SESSIONS_DIR", tmp_path)
    oud = {"name": "oud-sessie", "provider": "ollama", "rol": "tester", "taak": "testen", "doel": "kwaliteit"}
    (tmp_path / "oud-sessie.json").write_text(json.dumps(oud, ensure_ascii=False), encoding="utf-8")
    response = await client.get("/api/sessions/oud-sessie")
    assert response.status_code == 200
