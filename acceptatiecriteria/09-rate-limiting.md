# Story 09: Rate limiting — API-quota's respecteren

**Als** gebruiker  
**wil ik** de rate limits per provider kunnen instellen en wil ik dat de applicatie die limieten respecteert bij het versturen van meerdere requests  
**zodat** mijn sessie niet mislukt door een overschreden quota

## Context

Online providers hanteren limieten op twee niveaus:

| Provider | RPM (requests/minuut) | Opmerking |
|---|---|---|
| Groq (gratis) | ~30 RPM | Varieert per model; 429 bevat `retry-after` header |
| Google AI Studio | 15 RPM | Gemini 2.0 Flash; 429 bevat `retry-after` header |
| Ollama | geen | Lokaal, geen limiet |

Bij een sessie met meerdere runs en/of reviewers kunnen er tientallen requests per sessie verstuurd worden. Zonder vertraging kan de quota overschreden worden.

---

## Acceptatiecriteria

### Rate limits configureren

- [ ] De RPM-limieten worden opgeslagen in `settings.json` (naast `app.py`), los van `.env` dat alleen voor API keys gebruikt wordt
- [ ] Standaardwaarden worden gebruikt als `settings.json` ontbreekt of een provider daarin niet voorkomt: Groq = 30 RPM, Google = 15 RPM
- [ ] De geconfigureerde rate limits zijn zichtbaar en aanpasbaar via een aparte tab "Instellingen" in de UI
- [ ] Wijzigingen in de tab worden via een API-endpoint teruggeschreven naar `settings.json` en zijn direct van kracht zonder herstart
- [ ] Ollama heeft geen RPM-instelling — het veld is niet zichtbaar voor Ollama in de tab

### Automatische vertraging op basis van RPM

- [ ] De applicatie berekent automatisch de minimale wachttijd tussen requests op basis van de geconfigureerde RPM: `vertraging = 60 / RPM` seconden
- [ ] De berekende vertraging wordt toegepast tussen opeenvolgende requests binnen één sessie (runs + reviewer-stappen)
- [ ] De vertraging geldt alleen tussen requests naar de API, niet vóór het eerste request
- [ ] Bij Ollama wordt geen vertraging toegepast
- [ ] Als RPM = 0 is ingesteld, wordt geen vertraging toegepast (effectief uitgeschakeld)

### Automatisch herstarten na 429

- [ ] Als de API een 429 (Too Many Requests) teruggeeft, wacht de applicatie en stuurt het request opnieuw
- [ ] De wachttijd wordt gelezen uit de `Retry-After` header van de 429-response (in seconden)
- [ ] Als er geen `Retry-After` header aanwezig is, gebruikt de applicatie exponential backoff: 5s, 10s, 20s
- [ ] Na maximaal 3 pogingen geeft de applicatie de fout terug aan de gebruiker met de melding dat de API-limiet bereikt is
- [ ] Elke retry wordt gelogd als waarschuwing in het logbestand van die stap

### Gebruikersfeedback

- [ ] Als een request opnieuw verstuurd wordt door een 429, bevat het resultaat van die stap een veld `rate_limit_retries` met het aantal retries dat nodig was
- [ ] Als de maximale retries bereikt zijn, bevat de stap een `fout`-veld met de melding: `"API-limiet bereikt na 3 pogingen — probeer later opnieuw"`
- [ ] Een stap die uiteindelijk slaagt na één of meer retries geeft alsnog een geldig resultaat terug (de retry is transparant)

### Logging

- [ ] Als een request opnieuw verstuurd is, bevat het logbestand een veld `rate_limit_retries` met het aantal retries
- [ ] Als de retry-wachttijd uit de `Retry-After` header gelezen is, bevat het logbestand ook `retry_after_seconden`

### Geen wijziging bij Ollama

- [ ] Ollama-requests zijn niet onderhevig aan rate limiting: geen retry-logica, geen vertraging, geen RPM-instelling
