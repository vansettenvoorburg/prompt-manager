# Story 11: Groq-modelkeuze uitbreiden

**Als** gebruiker
**wil ik** per aanvraag kunnen kiezen tussen meerdere Groq-modellen (waaronder `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `moonshotai/kimi-k2-instruct` en `qwen3-32b`)
**zodat** ik het model kan gebruiken dat het beste past bij mijn taak, zonder `.env` te hoeven aanpassen

---

## Acceptatiecriteria

### Modelkeuze in de UI

- [ ] Wanneer provider `Groq` is geselecteerd, toont de UI een extra dropdown "Model"
- [ ] De dropdown bevat de vier nieuwe modellen: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `moonshotai/kimi-k2-instruct`, `qwen3-32b`, plus het model dat is ingesteld via `GROQ_MODEL` in `.env` (standaard `llama3-8b-8192`)
- [ ] Als de waarde van `GROQ_MODEL` overeenkomt met een van de vier nieuwe modellen, verschijnt deze niet dubbel in de lijst
- [ ] De modeldropdown is niet zichtbaar wanneer provider `Ollama` is geselecteerd
- [ ] Bij het laden van de pagina staat de dropdown standaard op de waarde van `GROQ_MODEL` (het huidige model blijft de default)
- [ ] Het geselecteerde model wordt meegestuurd bij elke promptaanvraag naar de backend

### API-aanroep

- [ ] De backend gebruikt bij provider `Groq` het door de gebruiker geselecteerde model voor de aanroep naar de Groq API, in plaats van altijd de env-waarde `GROQ_MODEL`
- [ ] Als er geen model is meegestuurd, valt de backend terug op `GROQ_MODEL`
- [ ] Bij provider `Ollama` heeft de modelkeuze geen effect — `OLLAMA_MODEL` blijft leidend
- [ ] Elk van de vier nieuwe modellen kan een aanvraag uitvoeren via de bestaande Groq-integratie (dezelfde OpenAI-compatibele endpoint, alleen de modelnaam verschilt)

### Validatie

- [ ] Als de backend bij provider `Groq` een lege of onbekende modelwaarde ontvangt, retourneert de backend HTTP 400 met een duidelijke foutmelding
- [ ] Bekende modelwaarden zijn: `llama3-8b-8192` (of de ingestelde `GROQ_MODEL`-waarde), `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `moonshotai/kimi-k2-instruct`, `qwen3-32b`

### Logging

- [ ] Het veld `model` in het logbestand bevat het daadwerkelijk gebruikte model, niet altijd de env-default
- [ ] De bestandsnaam van het logbestand bevat zowel `groq` als providernaam als de gebruikte modelnaam (bijv. `2026-07-11_10-00-00_groq_openai-gpt-oss-120b_mijn-sessie.json`)
- [ ] Tekens in de modelnaam die ongeldig zijn voor bestandsnamen (zoals `/`) worden vervangen door een leesteken (bijv. `-`)

### Modelbevestiging

- [ ] Naast het veld `model` (het aangevraagde model) bevat het logbestand een veld `model_bevestigd_door_groq` met het model dat de Groq API in haar respons terugmeldt
- [ ] Als het door Groq bevestigde model afwijkt van het aangevraagde model, bevat het bijbehorende run-resultaat een waarschuwingsveld `model_mismatch_warning` met zowel het aangevraagde als het bevestigde model
- [ ] Als aangevraagd en bevestigd model overeenkomen, verschijnt er geen `model_mismatch_warning`
- [ ] Als de Groq-respons geen `model`-veld bevat, wordt dit niet als mismatch behandeld (geen waarschuwing) — de vergelijking wordt overgeslagen

### Sessie opslaan

- [ ] Het geselecteerde Groq-model wordt meegeslagen in het sessiebestand (veld `groq_model`)
- [ ] Bij het laden van een sessie met provider `Groq` wordt het opgeslagen model automatisch geselecteerd in de modeldropdown
- [ ] Sessies die zijn opgeslagen vóór deze wijziging (zonder `groq_model`-veld) laden nog steeds correct, met `GROQ_MODEL` als geselecteerd model

---

### Buiten scope

- Modelkeuze voor de Ollama-provider (blijft via `OLLAMA_MODEL` in `.env`)
- Andere Groq-modellen dan de genoemde vijf toevoegen
- Automatisch aanbevelen van een model op basis van de taak
- Prijs- of snelheidsvergelijking tussen modellen tonen in de UI
