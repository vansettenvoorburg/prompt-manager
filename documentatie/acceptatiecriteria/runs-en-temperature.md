# Acceptatiecriteria: Runs en temperature

Instellen hoe vaak een taak wordt uitgevoerd en met welke temperature per run.

Bron: story 06.

## Weergave

- **RUNS-W-01** — De UI toont een invoerveld `Aantal runs` (standaard: `1`).
- **RUNS-W-02** — De UI toont een keuzeschakelaar met twee opties: `Één temperature voor alle
  runs` en `Één temperature per run`.
- **RUNS-W-03** — Het temperature-invoerveld wordt vooraf ingevuld met de standaardwaarde van de
  geselecteerde provider (Ollama: `0.8`, Groq: `1`).
- **RUNS-W-04** — De UI toont bij het temperature-veld een duidelijke aanduiding dat het veld
  verplicht is.

## Interactie

- **RUNS-I-01** — Bij het wisselen van provider wordt de vooraf ingevulde temperature bijgewerkt
  naar de standaardwaarde van de nieuwe provider, tenzij de gebruiker de waarde al handmatig heeft
  gewijzigd.
- **RUNS-I-02** — `runs`, temperature-modus en temperature-waarde(n) worden meegestuurd bij
  uitvoeren en bij sessie opslaan; bij het laden van een sessie worden ze automatisch ingevuld.
- **RUNS-I-03** — De prompt wordt precies `runs` keer verstuurd; in modus `alle` gebruikt elke run
  dezelfde temperature, in modus `per_run` de temperature die bij zijn volgnummer hoort; runs
  worden sequentieel uitgevoerd.
- **RUNS-I-04** — Na afloop toont de UI alle resultaten van de runs op volgorde.

## Validatie

- **RUNS-V-01** — `Aantal runs` moet een geheel getal zijn van minimaal 1; bij ongeldige invoer
  toont de UI een foutmelding en wordt de aanvraag niet verstuurd.
- **RUNS-V-02** — Het temperature-veld is verplicht; bij een lege invoer toont de UI een
  foutmelding en wordt de aanvraag geblokkeerd.
- **RUNS-V-03** — Elke temperature-waarde moet liggen tussen `0.0` en `2.0` (inclusief); bij een
  waarde buiten dit bereik toont de UI een foutmelding die het bereik noemt.
- **RUNS-V-04** — In modus `per run` moet het aantal ingevoerde temperatures exact gelijk zijn aan
  `Aantal runs`; bij een mismatch toont de UI een foutmelding met het verwachte aantal.
- **RUNS-V-05** — Als een individuele run mislukt (API-fout), toont de UI een foutmelding voor die
  run en gaat de uitvoering door met de volgende run.
