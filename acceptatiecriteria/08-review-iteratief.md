# Story 08: Review pipeline — iteratief verbeteren

**Als** gebruiker  
**wil ik** één of meerdere reviewers aan een sessie kunnen toevoegen, elk met een eigen rol en omschrijving van wat de review inhoudt, die elkaars output stap voor stap verbeteren  
**zodat** ik een gericht en iteratief verbeterd eindresultaat krijg

## Acceptatiecriteria

**Reviewers configureren**
- [ ] De gebruiker kan één of meerdere reviewers toevoegen aan een sessie
- [ ] Elke reviewer heeft een eigen rol, omschrijving, aantal runs en temperature per run
- [ ] De rol is een korte aanduiding van het perspectief (bijv. "kritische QA engineer")
- [ ] De omschrijving legt uit wat de reviewer concreet moet controleren of verbeteren (bijv. "Controleer op volledigheid, ontbrekende randgevallen en correctheid van de uitleg")
- [ ] Zowel rol als omschrijving zijn verplicht per reviewer
- [ ] De gebruiker kan reviewers verwijderen en herordenen
- [ ] Een sessie zonder reviewers gedraagt zich ongewijzigd

**Reviewprompt**
- [ ] De reviewprompt heeft de volgende structuur:

  ```
  Je bent [rol].
  Reviewfocus: [omschrijving]
  Geef als output een verbeterde en complete versie van de tekst. Geen commentaar of analyse.

  Originele eisen:
  Formaat: [formaat]          (alleen als ingesteld)
  Stijl: [stijl]              (alleen als ingesteld)
  Scope: [scope]              (alleen als ingesteld)
  Extra eisen: [eisen]        (alleen als ingesteld)
  Voorbeelden: [voorbeelden]  (alleen als ingesteld)
  Bijlage:                    (alleen als aanwezig)
  [bijlage_tekst]

  Te reviewen tekst:
  [output vorige stap]
  ```

- [ ] De prompt bevat altijd zowel de rol als de omschrijving van de reviewer
- [ ] De prompt bevat de instructie om een verbeterde en complete versie te produceren (zodat de keten bruikbaar blijft)
- [ ] De prompt bevat een sectie 'Originele eisen:' met de ingestelde velden (formaat, stijl, scope, eisen, voorbeelden) en bijlage
- [ ] De sectie 'Originele eisen:' is afwezig als geen optionele velden zijn ingesteld en er geen bijlage is
- [ ] De bijlage wordt meegestuurd bij elke reviewstap als die aanwezig is

**Uitvoervolgorde**
- [ ] De hoofdprompt wordt als eerste uitgevoerd
- [ ] Reviewer 1 ontvangt de output van de hoofdprompt en verbetert die
- [ ] Elke volgende run of reviewer ontvangt de output van de vorige stap
- [ ] De volgorde is: hoofdprompt → reviewer 1 run 1 → reviewer 1 run 2 → reviewer 2 run 1 → …
- [ ] Bij meerdere hoofdruns (aantal runs > 1) krijgt elke hoofdrun zijn eigen, volledige reviewketen
- [ ] De volgorde bij meerdere hoofdruns is: hoofdrun 1 → reviewketen van hoofdrun 1 (alle reviewers met al hun runs) → hoofdrun 2 → reviewketen van hoofdrun 2 → … → hoofdrun N → reviewketen van hoofdrun N
- [ ] Elke hoofdrun wordt dus eerst volledig doorlopen (inclusief zijn eigen reviewers) voordat de volgende hoofdrun start — reviewers van verschillende hoofdruns worden niet gebundeld in een aparte fase

**Resultaat**
- [ ] De gebruiker ziet de uitvoer van elke stap afzonderlijk
- [ ] De eindoutput is de output van de laatste stap

**Logging**
- [ ] Elke stap wordt apart gelogd
- [ ] Het logbestand bevat zowel de rol als de omschrijving van de reviewer
- [ ] Uit het logbestand is af te lezen welke stap het betreft (reviewer, run-nummer)

**Reviewmodus**
- [ ] De sessie heeft een instelbare reviewmodus; bij story 08 is dat `iteratief`
- [ ] De instelling wordt opgeslagen als onderdeel van de sessie
