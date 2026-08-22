# Prompt Sessie Manager

Een lokale webapplicatie voor het samenstellen, versturen en opslaan van prompts naar een AI-provider (Ollama of Groq). Draait volledig in de browser op `http://localhost:3000`.

## Vereisten

- Python 3.10 of hoger
- [Ollama](https://ollama.com) lokaal geïnstalleerd (voor de Ollama-provider)
- Een [Groq API key](https://console.groq.com) (optioneel, voor de Groq-provider)

## Installatie

**1. Clone de repository en ga naar de map**

```
git clone <repo-url>
cd "Prompt manager"
```

**2. Maak een virtuele omgeving aan en activeer die**

```
python -m venv .venv
.venv\Scripts\activate
```

**3. Installeer de dependencies**

```
pip install -r requirements.txt
```

**4. Kopieer de omgevingsvariabelen**

```
copy .env.example .env
```

Open `.env` en vul eventueel je eigen waarden in:

| Variabele      | Standaard                                 | Beschrijving                          |
|----------------|-------------------------------------------|---------------------------------------|
| `OLLAMA_URL`   | `http://localhost:11434/api/generate`     | URL van de lokale Ollama-server       |
| `OLLAMA_MODEL` | `llama3.2`                                | Ollama-model om te gebruiken          |
| `GROQ_API_KEY` | *(leeg)*                                  | Vereist als je Groq als provider kiest |
| `GROQ_MODEL`   | `llama3-8b-8192`                          | Groq-model om te gebruiken            |

## App starten

```
python development/app.py
```

Open daarna `http://localhost:3000` in je browser.

## Gebruik

Vul de promptvelden in en klik op **Verstuur**:

| Veld          | Verplicht | Beschrijving                          |
|---------------|-----------|---------------------------------------|
| Rol           | Ja        | De rol die het model moet aannemen    |
| Taak          | Ja        | Wat het model moet doen               |
| Doel          | Ja        | Het beoogde resultaat                 |
| Formaat       | Nee       | Gewenste opmaak van het antwoord      |
| Stijl         | Nee       | Schrijfstijl of toon                  |
| Scope         | Nee       | Beperkingen of afbakening             |
| Extra eisen   | Nee       | Aanvullende vereisten                 |
| Voorbeelden   | Nee       | Voorbeeldinvoer of -uitvoer           |

Kies de provider (Ollama of Groq), het aantal runs en de temperature(s). Sessies kunnen worden opgeslagen en later opnieuw geladen.

Logs worden weggeschreven naar `~/Documents/PromptSessieManager/logs/`.

## Tests draaien

Installeer de testafhankelijkheden en de Playwright-browsers:

```
pip install -r requirements-test.txt
playwright install
```

Draai de suite altijd per categorie — een enkele ongefilterde `pytest`-aanroep combineert
Playwright's sync API met async tests in dezelfde sessie, wat een
`RuntimeError: Cannot run the event loop while another loop is running` kan veroorzaken.

De tests staan in drie mappen, elk met een eigen commando:

Playwright-tests (browser):

```
pytest tests/playwright
```

Integratietests (async, via een draaiende server op de testpoort):

```
pytest tests/integratie
```

Backendtests (async, in-process testclient):

```
pytest tests/backend
```

Zie `documentatie/testdekking.md` voor het overzicht van welk browserscenario door welke
Playwright-test gedekt wordt.
