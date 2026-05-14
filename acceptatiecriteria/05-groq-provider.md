## Story: Groq toevoegen als tweede provider

**Als** gebruiker
**wil ik** kunnen kiezen tussen Ollama en Groq als AI-provider
**zodat** ik online modellen via Groq kan gebruiken zonder mijn prompt-logica te hoeven aanpassen

---

### Acceptatiecriteria

**Providerkeuze in de UI**

- [ ] De UI toont een keuzelijst (dropdown) waarmee de gebruiker de provider kan selecteren: `Ollama` of `Groq`
- [ ] De standaardwaarde is `Ollama`
- [ ] De geselecteerde provider wordt meegestuurd bij elke promptaanvraag

**Groq API-configuratie**

- [ ] De Groq API key wordt uitsluitend gelezen uit de omgevingsvariabele `GROQ_API_KEY` in `.env`
- [ ] `.env.example` bevat een lege `GROQ_API_KEY=` entry met een kort commentaar
- [ ] De API key verschijnt nooit in de browser, in sessiebestanden of in logbestanden

**API-aanroep**

- [ ] Bij provider `Groq` verstuurt de backend de prompt naar de Groq API via de OpenAI-compatibele endpoint (`https://api.groq.com/openai/v1`)
- [ ] Het te gebruiken Groq-model is instelbaar via de omgevingsvariabele `GROQ_MODEL` (standaard: `llama3-8b-8192`)
- [ ] De samengestelde prompt wordt identiek opgebouwd als bij Ollama — alleen de API-aanroep verschilt

**Logging**

- [ ] Bij een Groq-aanvraag bevat de bestandsnaam `groq` als provider (bijv. `2026-05-14_10-00-00_groq_mijn-sessie.json`)
- [ ] Het veld `provider` in het logbestand bevat `"groq"`
- [ ] Het veld `model` in het logbestand bevat het gebruikte Groq-model

**Sessie opslaan**

- [ ] De geselecteerde provider wordt meegeslagen in het sessiebestand (veld `provider`)
- [ ] Bij het laden van een sessie wordt de opgeslagen provider automatisch geselecteerd in de dropdown

**Foutafhandeling**

- [ ] Als `GROQ_API_KEY` niet ingesteld of leeg is en de gebruiker kiest voor Groq, retourneert de backend HTTP 503 met de melding `"Groq API key ontbreekt — stel GROQ_API_KEY in via .env"`
- [ ] Als de Groq API niet bereikbaar is of een fout retourneert, toont de UI een foutmelding (geen stille mislukking)
- [ ] Bij een Groq-fout wordt er geen (leeg) logbestand aangemaakt

---

### Buiten scope

- Andere providers dan Ollama en Groq (Google AI Studio en OpenRouter volgen in latere stories)
- Modelkeuze via de UI (model is instelbaar via `.env`, niet per aanvraag wisselbaar)
- Vergelijken van output tussen providers binnen één sessie
