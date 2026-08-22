# Acceptatiecriteria: Resultaten weergeven en kopiëren

Hoe het antwoord/resultaat van een aanvraag getoond wordt, en de kopieerknop per resultaatblok.

Bronnen: story 01, 04, 09, 10.

## Weergave

- **RESULTAAT-W-01** — Na het versturen verschijnt het antwoord zichtbaar op de pagina.
- **RESULTAAT-W-02** — Zolang de aanvraag bezig is, is zichtbaar dat er gewacht wordt (laadstatus
  of vergelijkbaar).
- **RESULTAAT-W-03** — Elk resultaatblok (run-resultaat, reviewer-stap, eindoutput) heeft een
  kopieerknop rechtsboven in de header, visueel duidelijk onderscheiden van de overige knoppen
  (kleiner, subtiel, geen primaire kleur).
- **RESULTAAT-W-04** — Na een succesvolle aanvraag toont de UI bij elke run een korte melding met
  het volledige pad van het opgeslagen logbestand.

## Interactie

- **RESULTAAT-I-01** — De kopieerknop kopieert de platte tekst van het resultaat naar het
  klembord (zonder markdown-opmaaktekens); de knoptekst verandert tijdelijk naar "Gekopieerd!" en
  keert na 2 seconden terug naar de oorspronkelijke tekst.

## Validatie

- **RESULTAAT-V-01** — Als het klembord niet beschikbaar is (geen toestemming), toont de knop kort
  "Mislukt".
- **RESULTAAT-V-02** — Als het opslaan van het logbestand mislukt, toont de UI bij die run een
  waarschuwing; het antwoord blijft zichtbaar.
- **RESULTAAT-V-03** — Als de API-limiet na 3 pogingen nog niet is opgelost (rate limiting), toont
  het resultaat van die stap de melding "API-limiet bereikt na 3 pogingen — probeer later
  opnieuw" (zie ook RUNS-V-05 voor het algemene patroon van een mislukte run).
