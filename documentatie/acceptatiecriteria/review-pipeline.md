# Acceptatiecriteria: Review pipeline

Eén of meerdere reviewers aan een sessie toevoegen die elkaars output stap voor stap verbeteren.

Bron: story 08.

## Weergave

- **REVIEW-W-01** — Er is een knop om een reviewer toe te voegen; na toevoegen toont deze
  invoervelden voor rol, omschrijving, aantal runs en temperatures; meerdere reviewers zijn
  mogelijk.
- **REVIEW-W-02** — Er is een keuzemenu voor de reviewmodus.
- **REVIEW-W-03** — Elke reviewer heeft een zichtbare verwijderknop.
- **REVIEW-W-04** — Bij meerdere hoofdruns met reviewers toont de UI per hoofdrun een eigen
  eindoutput-blok, zichtbaar gekoppeld aan die hoofdrun (bv. "Eindoutput — run X"), in plaats van
  één gedeeld blok met alleen het resultaat van de laatste hoofdrun.
- **REVIEW-W-05** — Elk eindoutput-blok heeft zijn eigen kopieerknop (consistent met
  RESULTAAT-W-03).
- **REVIEW-W-06** — Bij precies één hoofdrun blijft het gedrag ongewijzigd: één eindoutput-blok,
  zonder run-aanduiding.

## Interactie

- **REVIEW-I-01** — Reviewer verwijderen verwijdert het item uit de lijst.
- **REVIEW-I-02** — De hoofdprompt wordt als eerste uitgevoerd; reviewer 1 ontvangt de output van
  de hoofdprompt; elke volgende run of reviewer ontvangt de output van de vorige stap. Bij
  meerdere hoofdruns krijgt elke hoofdrun zijn eigen, volledige reviewketen vóórdat de volgende
  hoofdrun start.
- **REVIEW-I-03** — Na uitvoering toont de UI de uitvoer van elke stap afzonderlijk (reviewer-stap)
  en de eindoutput (de output van de laatste stap).
- **REVIEW-I-04** — Een sessie zonder reviewers gedraagt zich ongewijzigd (geen eindoutput-blok(ken)).
- **REVIEW-I-05** — Bij meerdere hoofdruns met reviewers geeft de API-response het eindresultaat
  per hoofdrun terug, gekoppeld aan het hoofdrun-nummer (in plaats van één enkele
  eindoutput-waarde).

## Validatie

- **REVIEW-V-01** — Zowel rol als omschrijving zijn verplicht per reviewer.
- **REVIEW-V-02** — Bevat een reviewerstap-resultaat HTML- of scripttags, dan worden deze getoond
  als platte tekst in plaats van als uitvoerbare code in de browser.
- **REVIEW-V-03** — Faalt de reviewketen van één hoofdrun (bv. API-limiet of verbindingsfout op de
  laatste stap van die keten), dan toont het eindoutput-blok van die hoofdrun de foutmelding van
  die stap; de eindoutput-blokken van de andere hoofdruns blijven onaangetast en tonen hun eigen
  resultaat.
