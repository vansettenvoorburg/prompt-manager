# Acceptatiecriteria: Review pipeline

Eén of meerdere reviewers aan een sessie toevoegen die elkaars output stap voor stap verbeteren.

Bron: story 08.

## Weergave

- **REVIEW-W-01** — Er is een knop om een reviewer toe te voegen; na toevoegen toont deze
  invoervelden voor rol, omschrijving, aantal runs en temperatures; meerdere reviewers zijn
  mogelijk.
- **REVIEW-W-02** — Er is een keuzemenu voor de reviewmodus.
- **REVIEW-W-03** — Elke reviewer heeft een zichtbare verwijderknop.

## Interactie

- **REVIEW-I-01** — Reviewer verwijderen verwijdert het item uit de lijst.
- **REVIEW-I-02** — De hoofdprompt wordt als eerste uitgevoerd; reviewer 1 ontvangt de output van
  de hoofdprompt; elke volgende run of reviewer ontvangt de output van de vorige stap. Bij
  meerdere hoofdruns krijgt elke hoofdrun zijn eigen, volledige reviewketen vóórdat de volgende
  hoofdrun start.
- **REVIEW-I-03** — Na uitvoering toont de UI de uitvoer van elke stap afzonderlijk (reviewer-stap)
  en de eindoutput (de output van de laatste stap).
- **REVIEW-I-04** — Een sessie zonder reviewers gedraagt zich ongewijzigd.

## Validatie

- **REVIEW-V-01** — Zowel rol als omschrijving zijn verplicht per reviewer.
- **REVIEW-V-02** — Bevat een reviewerstap-resultaat HTML- of scripttags, dan worden deze getoond
  als platte tekst in plaats van als uitvoerbare code in de browser.
