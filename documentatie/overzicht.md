# Prompt Sessie Manager — Projectbeschrijving

## Doel

Een lokaal draaiende webapplicatie waarmee je herbruikbare prompt-sessies kunt bouwen en uitvoeren. De tool combineert een gedeelde specificatie met meerdere gefocuste taken, en stuurt elk naar een AI-model naar keuze.

---

## Kernfunctionaliteit

### Prompt structuur

Elke prompt wordt samengesteld uit de volgende velden. Elk veld is apart instelbaar en varieerbaar per taak of per run:

| Veld | Omschrijving | Voorbeeld |
|---|---|---|
| `rol` | Persona van het model | "senior Python developer" |
| `taak` | De basisopdracht | "schrijf unit tests voor een inlogscherm" |
| `doel` | Waarom de taak gedaan wordt | "zodat randgevallen gedekt zijn vóór release" |
| `formaat` | Structuur van de output | "Python code met pytest, commentaar per test" |
| `stijl` | Toon en detailniveau | "beknopt, geen uitleg tenzij gevraagd" |
| `scope` | Wat wel / wat niet | "alleen unit tests, geen integratietests" |
| `eisen` | Aanvullende instructies | "focus op randgevallen, gebruik fixtures" |
| `voorbeelden` | Few-shot voorbeelden | één voorbeeld van gewenste testopzet |

De samengestelde prompt heeft altijd deze vaste structuur:

```
Als [rol] wil ik [taak] zodat [doel].
Formaat: [formaat]
Stijl: [stijl]
Scope: [scope]
Extra eisen: [eisen]
Voorbeelden: [voorbeelden]
```

---

### Sessies

Een sessie bestaat uit:
- Een gedeelde **specificatie** (context die voor alle taken geldt)
- Een lijst van **taken** (elk een gerichte, losse opdracht)
- De gekozen **provider en model**
- Het **aantal runs** — hoe vaak elke taak wordt uitgevoerd, standaard 1
- De **temperature per run** — één waarde per run, standaard 0.7
- Een optionele **bijlage** — meegestuurd bij elke taak en elke review

Sessies worden opgeslagen als JSON-bestanden en zijn herbruikbaar.

### Runs en temperature

Je kunt per sessie instellen hoe vaak elke taak wordt uitgevoerd, en met welke temperature per run. Dit is nuttig om variatie in output te vergelijken.

```json
"runs": 3,
"temperatures": [0.3, 0.7, 1.0]
```

- Aantal temperatures mag minder zijn dan aantal runs — de rest wordt aangevuld met 0.7
- Ondersteunde range: 0.0 tot 2.0 (werkt bij alle providers)
- Elke run wordt apart gelogd met het temperature-niveau in de bestandsnaam

Voorbeeld van logbestanden bij 3 runs:

```
logs/
├── 2026-05-10_14-32-01_ollama_sessie-tests_run1_t0.3.json
├── 2026-05-10_14-32-08_ollama_sessie-tests_run2_t0.7.json
└── 2026-05-10_14-32-15_ollama_sessie-tests_run3_t1.0.json
```

---

### Bijlage

Per sessie kun je één bijlage toevoegen. De inhoud wordt automatisch geëxtraheerd en meegestuurd bij elke taak én elke review in de sessie.

Ondersteunde bestandstypen:

| Type | Extensies | Verwerking |
|---|---|---|
| Tekst en code | `.txt`, `.md`, `.py`, `.js`, `.ts`, `.html`, `.css`, `.json` | Direct inlezen |
| PDF | `.pdf` | Tekstextractie via `pymupdf` |
| Word | `.docx` | Tekstextractie via `python-docx` |

De bijlage wordt toegevoegd aan het einde van de prompt:

```
Als [rol] wil ik [taak] zodat [doel].
Formaat: [formaat]
...
Bijlage:
[geëxtraheerde tekst uit het bestand]
```

Opmaak, afbeeldingen en tabellen uit PDF en Word gaan verloren bij extractie — alleen de tekst wordt meegestuurd. Voor jouw gebruik case (inhoud meesturen, geen lay-out) is dat acceptabel.

Extra Python dependencies:
- `pymupdf` — voor PDF tekstextractie
- `python-docx` — voor Word tekstextractie

---

### Review pipeline — iteratief verbeteren

Na de hoofdprompt kun je één of meerdere reviewers toevoegen. Elke reviewer krijgt de laatste versie van de output en verbetert die. De verbeterde versie is de input voor de volgende reviewer of run.

De reviewprompt heeft een vaste structuur:

```
Je bent [rol].
Reviewfocus: [omschrijving]

Te reviewen tekst:
[output vorige stap]
```

Elke reviewer heeft een rol (het perspectief) en een omschrijving (wat concreet gecontroleerd of verbeterd moet worden). Beide zijn verplicht. Zonder omschrijving is de reviewprompt te vaag om bruikbaar te zijn.

Voorbeeld met twee reviewers, elk met eigen rol, omschrijving, aantal runs en temperature:

```json
"reviewers": [
  {
    "rol": "kritische QA engineer",
    "omschrijving": "Controleer op volledigheid, ontbrekende randgevallen en correctheid van de uitleg.",
    "runs": 2,
    "temperatures": [0.5, 0.8]
  },
  {
    "rol": "senior developer met focus op leesbaarheid",
    "omschrijving": "Verbeter de structuur en formulering zodat de tekst helder en bondig is.",
    "runs": 1,
    "temperatures": [0.7]
  }
]
```

De verwerkingsvolgorde bij iteratief verbeteren:

```
Hoofdprompt → output v1
Reviewer 1, run 1 (t0.5) → verbetert v1 → output v2
Reviewer 1, run 2 (t0.8) → verbetert v2 → output v3
Reviewer 2, run 1 (t0.7) → verbetert v3 → output v4
```

Elke stap wordt apart gelogd.

---

### Review pipeline — alleen loggen

Alle reviewers ontvangen altijd de originele output van de hoofdprompt. Ze reviewen onafhankelijk van elkaar en worden apart gelogd. Er vindt geen terugkoppeling plaats.

```
Hoofdprompt → output v1
Reviewer 1, run 1 → reviewt v1 → gelogd
Reviewer 1, run 2 → reviewt v1 → gelogd
Reviewer 2, run 1 → reviewt v1 → gelogd
```

De modus (iteratief of alleen loggen) is instelbaar per sessie:

```json
"review_modus": "iteratief"   // of: "loggen"
```

---

## Technische opzet

### Stack

- **Backend**: Python met FastAPI
- **Frontend**: HTML + Vanilla JS (geen framework, minimale dependencies)
- **Opslag**: JSON-bestanden voor sessies en outputs, `.env` voor API keys
- **Starten**: één commando — `python development/app.py`
- **Gebruik**: via de browser op `http://localhost:3000`

Python is gekozen omdat Ollama, Groq en Google AI Studio alle drie uitstekende Python SDK's en documentatie hebben. Als je later iets toevoegt of een bug oplost via Claude Code, zijn Python-voorbeelden het meest beschikbaar.

### Vereisten

- **Python 3.10+** — via [python.org](https://python.org) (op Mac/Linux vaak al aanwezig)
- **Ollama** — via [ollama.com](https://ollama.com), voor offline gebruik zonder API key

### Mapstructuur

```
prompt-sessie-manager/
├── development/
│   ├── app.py                  # backend server (FastAPI)
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── requirements.txt            # Python dependencies
├── .env                        # API keys (niet in versiebeheer)
├── .env.example                # voorbeeld zonder keys
├── sessions/                   # opgeslagen sessies als JSON
├── outputs/                    # opgeslagen resultaten
└── README.md
```

---

## Provider ondersteuning

De tool werkt als adapter-laag. Providers zijn inwisselbaar zonder de prompt-logica te wijzigen. Groq en Google AI Studio gebruiken een OpenAI-compatibele API — alleen `base_url` en `api_key` hoeven te worden aangepast, de rest van de code blijft identiek.

### Prioriteit 1 — Gratis, geen creditcard, direct testbaar

| Provider | Key vereist | Limiet (gratis) | Opmerking |
|---|---|---|---|
| **Ollama** | Nee | Onbeperkt (lokaal) | Volledig offline, geen account |
| **Groq** | Ja (gratis account) | ~1.000 req/dag per model | Zeer snel, OpenAI-compatibel, aanbevolen als eerste online provider |
| **Google AI Studio** | Ja (gratis account) | 1.500 req/dag, 15 RPM | Gemini 2.0 Flash, geen creditcard |
| **OpenRouter** | Ja (gratis account) | Wisselend per model | Toegang tot meerdere modellen via één key, handig voor vergelijken |

### Prioriteit 2 — Betaald of organisatie-afhankelijk, later toe te voegen

| Provider | Vereiste | Opmerking |
|---|---|---|
| OpenAI | Betaalde API key | GPT-4o en verder |
| Mistral | Betaalde API key | Sterk in instructies volgen |
| Azure OpenAI | Azure-abonnement | Brug naar Microsoft 365 Copilot Business omgevingen |

Standaard provider bij eerste gebruik: **Ollama** (geen key, geen account, werkt direct).

API keys worden opgeslagen in `.env` op de lokale machine, nooit in de browser of in sessiebestanden.

---

## Variatie-mechanisme

Per sessie kun je varianten aanmaken door één of meerdere velden te wisselen:

- **Rol wisselen** → zelfde taak vanuit ander perspectief (dev vs. QA)
- **Eisen stapelen** → eerst happy path, dan randgevallen, dan security
- **Formaat aanpassen** → eerst code, dan samenvatting als tabel
- **Scope versmallen** → eerst volledig scherm, dan alleen wachtwoord-reset
- **Model wisselen** → zelfde prompt vergelijken tussen Llama en Gemini

---

## Logging

Elke request en response wordt automatisch opgeslagen in een herkenbare map in de gebruikersmap. Geen extra instelling nodig — de map wordt aangemaakt bij eerste gebruik.

### Locatie

| Besturingssysteem | Pad |
|---|---|
| Windows | `C:\Users\jouw-naam\Documents\PromptSessieManager\logs\` |
| Mac | `~/Documents/PromptSessieManager/logs/` |
| Linux | `~/Documents/PromptSessieManager/logs/` |

Python bepaalt het juiste pad automatisch via `pathlib.Path.home()`, ongeacht het besturingssysteem.

### Bestandsnaam

Elk request krijgt een eigen bestand, direct herkenbaar zonder te openen:

```
logs/
├── 2026-05-10_14-32-01_ollama_sessie-tests.json
├── 2026-05-10_14-35-22_groq_sessie-tests.json
└── 2026-05-10_15-01-44_google_oefeningen.json
```

Formaat: `[datum]_[tijd]_[provider]_[sessienaam].json`

### Inhoud per logbestand

```json
{
  "timestamp": "2026-05-10T14:32:01",
  "provider": "ollama",
  "model": "llama3.2",
  "sessie": "unit-tests-inlogscherm",
  "prompt": {
    "rol": "...",
    "taak": "...",
    "doel": "...",
    "formaat": "...",
    "stijl": "...",
    "scope": "...",
    "eisen": "...",
    "voorbeelden": "..."
  },
  "request": "volledige samengestelde prompt zoals verstuurd naar de API",
  "response": "output van het model",
  "duur_seconden": 4.2
}
```

---

## Uitvoer-opties

- **Één taak uitvoeren** — handmatig, stap voor stap
- **Hele sessie uitvoeren** — alle taken in volgorde
- **Output opslaan** — resultaat per taak opgeslagen in `outputs/` als Markdown of JSON

---

## Installatie

### Eenmalig instellen

**Stap 1 — Python installeren** (als nog niet aanwezig)
Ga naar [python.org](https://python.org) en download Python 3.10 of hoger. Op Mac en Linux is Python vaak al aanwezig; controleer met `python3 --version`.

**Stap 2 — Ollama installeren** (voor offline gebruik)
Ga naar [ollama.com](https://ollama.com) en installeer Ollama. Daarna één model downloaden:
```bash
ollama pull llama3.2
```

**Stap 3 — Project installeren**
```bash
git clone https://github.com/jouw-naam/prompt-sessie-manager
cd prompt-sessie-manager
pip install -r requirements.txt
cp .env.example .env
```

**Stap 4 — API keys instellen** (optioneel, alleen voor online providers)
Open `.env` en vul de gewenste keys in:
```
GROQ_API_KEY=...
GOOGLE_API_KEY=...
```
Zonder keys werkt de tool al volledig via Ollama.

### Dagelijks gebruik

```bash
python development/app.py
# open http://localhost:3000
```

---

## Niet in scope (eerste versie)

- Gebruikersaccounts of authenticatie
- Cloud hosting
- Realtime samenwerking
- Betaalde API-beheer of key-rotatie
- Mobiele interface

---

## Suggestie voor Claude Code

Bouw in deze volgorde, zodat je na elke stap iets werkends hebt:

1. Backend die één prompt samenstelt en naar **Ollama** stuurt — werkt zonder account
2. Eenvoudige HTML-interface met de acht promptvelden
3. Sessie opslaan en laden als JSON
4. **Logging** toevoegen — request en response opslaan als JSON in de gebruikersmap
5. **Groq** toevoegen als tweede provider — gratis account, OpenAI-compatibel, minimale codewijziging
6. **Aantal runs en temperature per run** toevoegen — instelbaar per sessie, elke run apart gelogd
7. **Bijlage** toevoegen — tekstbestanden en code direct, PDF via `pymupdf`, Word via `python-docx`, meegestuurd bij elke taak en review
8. **Review pipeline — iteratief verbeteren** — reviewers die de laatste output verbeteren, elke stap apart gelogd
9. **Review pipeline — alleen loggen** — reviewers die altijd de originele output reviewen, onafhankelijk van elkaar
9. **Google AI Studio** toevoegen als derde provider — zelfde patroon
10. **OpenRouter** toevoegen voor model-vergelijking
11. Betaalde providers (OpenAI, Mistral, Azure OpenAI) als optionele uitbreiding
