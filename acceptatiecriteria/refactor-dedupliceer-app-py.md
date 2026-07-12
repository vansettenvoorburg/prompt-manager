# Refactor: dedupliceer app.py

**Aanleiding:** code-review van story 12 signaleerde drie stukken gedupliceerde logica in
`app.py`, los van story 12 zelf. Dit is een pure refactor: geen gedragswijziging voor
eindgebruikers, bestaande functionaliteit blijft identiek.

---

## Acceptatiecriteria

### 1. Multipart-tak van `/api/prompt` verwijderen

- [ ] `/api/prompt` accepteert alleen nog een JSON-body (huidige non-multipart pad);
      de multipart-tak (bijlage-validatie + form-parsing, huidige regels ±593-662) vervalt
- [ ] `/api/prompt/upload` blijft ongewijzigd het enige endpoint voor bijlage-uploads
- [ ] `tests/test_backend_07.py` wordt aangepast: alle aanroepen die nu `files=` naar
      `/api/prompt` sturen, gaan naar `/api/prompt/upload` (multipart-veldnamen blijven
      hetzelfde: `rol`, `taak`, `doel`, etc. als losse form-velden i.p.v. één JSON-body)
- [ ] Alle assertions in `test_backend_07.py` (status codes, foutmeldingen, log-inhoud)
      blijven ongewijzigd van betekenis — alleen de aanroep verandert
- [ ] Geen ander testbestand raakt de multipart-tak van `/api/prompt` aan (frontend en
      live-integratietests gebruiken al uitsluitend `/api/prompt/upload`)

### 2. Gedeelde log-schrijf-helper

- [ ] `_schrijf_log` en `_schrijf_reviewer_log` delen één helperfunctie voor de
      mkdir/write_text-foutafhandeling en bestandsnaam-opbouw
- [ ] Alleen de inhoud van `log_data` blijft per functie verschillend
- [ ] Bestaande logbestand-structuur en -inhoud blijven exact hetzelfde

### 3. Gedeelde provider-dispatch

- [ ] Het blok "if provider == groq: retry-aanroep, else: call_ollama" in `_voer_prompt_uit`
      wordt geëxtraheerd naar één gedeelde functie
- [ ] Deze functie wordt gebruikt in zowel de hoofdrun-loop als de reviewer-loop
- [ ] Retry-gedrag voor Groq en het model-gebruik voor Ollama blijven functioneel identiek

### Regressie

- [ ] `pytest -m "not frontend"` slaagt volledig
- [ ] `pytest -m "frontend"` slaagt volledig
- [ ] Geen enkel testbestand wordt aangepast om een fail te maskeren — alleen
      `test_backend_07.py` wordt aangepast, en uitsluitend om endpoint-aanroepen te
      verplaatsen naar `/api/prompt/upload` (zie AC 1)

---

### Buiten scope

- Functionele wijzigingen aan bijlage-verwerking, logging of provider-gedrag
- Het toevoegen van nieuwe tests
- Refactors elders in `app.py` die niet in de bevindingen hierboven genoemd zijn
