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

Sessies worden opgeslagen als JSON-bestanden en zijn herbruikbaar.

---

## Technische opzet

### Stack

- **Backend**: Python met FastAPI
- **Frontend**: HTML + Vanilla JS (geen framework, minimale dependencies)
- **Opslag**: JSON-bestanden voor sessies en outputs, `.env` voor API keys
- **Starten**: één commando — `python app.py`
- **Gebruik**: via de browser op `http://localhost:3000`

Python is gekozen omdat Ollama, Groq en Google AI Studio alle drie uitstekende Python SDK's en documentatie hebben. Als je later iets toevoegt of een bug oplost via Claude Code, zijn Python-voorbeelden het meest beschikbaar.

### Vereisten

- **Python 3.10+** — via [python.org](https://python.org) (op Mac/Linux vaak al aanwezig)
- **Ollama** — via [ollama.com](https://ollama.com), voor offline gebruik zonder API key

### Mapstructuur

```
prompt-sessie-manager/
├── app.py                      # backend server (FastAPI)
├── requirements.txt            # Python dependencies
├── .env                        # API keys (niet in versiebeheer)
├── .env.example                # voorbeeld zonder keys
├── sessions/                   # opgeslagen sessies als JSON
├── outputs/                    # opgeslagen resultaten
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
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
python app.py
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
4. **Groq** toevoegen als tweede provider — gratis account, OpenAI-compatibel, minimale codewijziging
5. **Google AI Studio** toevoegen als derde provider — zelfde patroon
6. **OpenRouter** toevoegen voor model-vergelijking
7. Betaalde providers (OpenAI, Mistral, Azure OpenAI) als optionele uitbreiding
