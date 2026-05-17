## Story: Aantal runs en temperature per run

**Als** gebruiker
**wil ik** per sessie kunnen instellen hoe vaak een taak wordt uitgevoerd en met welke temperature per run
**zodat** ik variatie in output kunt vergelijken zonder de sessie handmatig opnieuw te starten

---

### Acceptatiecriteria

**Instellingen in de UI**

- [ ] De UI toont een invoerveld `Aantal runs` (standaard: `1`)
- [ ] De UI toont een keuzeschakelaar (radio of toggle) met twee opties voor temperature:
  - `Één temperature voor alle runs` — één invoerveld, dezelfde waarde wordt bij elke run gebruikt
  - `Één temperature per run` — één invoerveld per run, komma-gescheiden (bijv. `0.3, 0.7, 1.0`)
- [ ] Het temperature-invoerveld wordt vooraf ingevuld met de standaardwaarde van de geselecteerde provider:
  - Ollama: `0.8`
  - Groq: `1`
- [ ] Bij het wisselen van provider wordt de vooraf ingevulde waarde bijgewerkt naar de standaardwaarde van de nieuwe provider, tenzij de gebruiker de waarde al handmatig heeft gewijzigd
- [ ] De UI toont bij het temperature-veld een duidelijke aanduiding dat het veld verplicht is (bijv. label met `*` en een toelichting "Verplicht — voer een temperature in om de prompt uit te voeren")
- [ ] Alle drie velden (`runs`, temperature-modus en temperature-waarde(n)) worden meegeslagen in het sessiebestand bij opslaan
- [ ] Bij het laden van een sessie worden `runs`, de temperature-modus en de temperature-waarde(n) automatisch ingevuld in de UI

**Uitvoering**

- [ ] Bij het uitvoeren van een taak wordt de prompt precies `runs` keer verstuurd naar de API
- [ ] In modus `één voor alle runs`: elke run gebruikt dezelfde ingevoerde temperature
- [ ] In modus `per run`: elke run gebruikt de temperature die overeenkomt met zijn volgnummer (run 1 → temperatures[0], run 2 → temperatures[1], etc.)
- [ ] Runs worden sequentieel uitgevoerd — run 2 start pas als run 1 is voltooid
- [ ] De UI toont de voortgang per run (bijv. "Run 1 van 3 — bezig…")
- [ ] Na afloop toont de UI alle resultaten van de runs op volgorde

**Validatie**

- [ ] `Aantal runs` moet een geheel getal zijn van minimaal 1; bij ongeldige invoer toont de UI een foutmelding en wordt de aanvraag niet verstuurd
- [ ] Het temperature-veld is verplicht — bij een lege invoer toont de UI een foutmelding en wordt de aanvraag geblokkeerd
- [ ] Elke temperature-waarde moet liggen tussen `0.0` en `2.0` (inclusief); bij een waarde buiten dit bereik toont de UI een foutmelding: "Temperature moet tussen 0 en 2 liggen" en wordt de aanvraag niet verstuurd
- [ ] In modus `per run`: het aantal ingevoerde temperatures moet exact gelijk zijn aan `Aantal runs`; bij een mismatch toont de UI een foutmelding (bijv. "Vul 3 temperatures in, of kies 'één voor alle runs'") en wordt de aanvraag niet verstuurd

**Sessie opslaan**

- [ ] Het sessiebestand bevat de velden `runs` (integer), `temperature_modus` (`"alle"` of `"per_run"`) en `temperatures` (array van floats)
- [ ] Voorbeeld bij modus `per_run`: `"runs": 3, "temperature_modus": "per_run", "temperatures": [0.3, 0.7, 1.0]`
- [ ] Voorbeeld bij modus `alle`: `"runs": 3, "temperature_modus": "alle", "temperatures": [0.7]`
- [ ] Bestaande sessiebestanden zonder deze velden worden geladen met lege temperature-invoer — de gebruiker moet de waarde(n) zelf invullen voor de sessie opnieuw kan worden uitgevoerd

**Logging**

- [ ] Elke run wordt als een apart logbestand opgeslagen
- [ ] De bestandsnaam bevat het run-nummer en de gebruikte temperature: `[datum]_[tijd]_[provider]_[sessienaam]_run[N]_t[temperature].json`
- [ ] Voorbeeld bij 3 runs: `2026-05-10_14-32-01_ollama_sessie-tests_run1_t0.3.json`, `..._run2_t0.7.json`, `..._run3_t1.0.json`
- [ ] Het logbestand bevat een extra veld `run_nummer` (integer) en `temperature` (float)
- [ ] Bij een sessie met slechts 1 run blijft het formaat `_run1_t0.7` — het achtervoegsel wordt altijd toegevoegd

**Foutafhandeling**

- [ ] Als een individuele run mislukt (API-fout), toont de UI een foutmelding voor die run en gaat de uitvoering door met de volgende run
- [ ] Voor een mislukte run wordt geen (leeg) logbestand aangemaakt

---

### Buiten scope

- Temperature-instellingen per taak afzonderlijk (runs en temperatures gelden voor de hele sessie)
- Parallelle uitvoering van runs
- Samenvatting of vergelijking van run-resultaten in de UI
