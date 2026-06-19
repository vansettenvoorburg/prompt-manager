# Story 10: Kopieerknop en formulieropmaak

**Als** gebruiker  
**wil ik** elk resultaat met één klik naar het klembord kunnen kopiëren en wil ik dat tekstvelden die vaak langere inhoud bevatten meer ruimte bieden en enters accepteren  
**zodat** ik uitvoer snel kan hergebruiken en mijn prompts comfortabeler kan invoeren

---

## Acceptatiecriteria

### Kopieerknop per resultaat

- [ ] Elk resultaatblok (run-result, reviewer-stap, eindoutput) heeft een kopieerknop rechtsboven in de header
- [ ] De knop kopieert de platte tekst van het resultaat naar het klembord (zonder markdown-opmaaktekens)
- [ ] Na een succesvolle kopieractie verandert de knoptekst tijdelijk naar "Gekopieerd!" en keert na 2 seconden terug naar de oorspronkelijke tekst
- [ ] Als het klembord niet beschikbaar is (geen toestemming), toont de knop kort "Mislukt"
- [ ] De kopieerknop is visueel duidelijk onderscheiden van de overige knoppen (kleiner, subtiel, geen primaire kleur)

### Tekstvelden met meer ruimte

- [ ] De velden `formaat`, `taak` en `doel` zijn textarea's in plaats van tekstvelden
- [ ] Enters (newlines) worden geaccepteerd in `formaat`, `taak` en `doel`
- [ ] `formaat` heeft standaard 3 rijen zichtbaar ruimte, `taak` en `doel` elk 2 rijen
- [ ] De bestaande textarea's `eisen` en `voorbeelden` blijven ongewijzigd (3 rijen)
- [ ] De opgeslagen waarden in sessie-JSON blijven ongewijzigd — newlines in een textarea worden gewoon als `\n` opgeslagen en bij laden hersteld
- [ ] Validatie op `rol`, `taak` en `doel` werkt ongewijzigd ook na de omzetting naar textarea
