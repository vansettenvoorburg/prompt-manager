## Story: Prompt invoeren en resultaat ontvangen via Ollama

**Als** gebruiker
**wil ik** een prompt kunnen invoeren en naar Ollama sturen
**zodat** ik een antwoord terugkrijg in de browser

### Acceptatiecriteria

- [ ] Er zijn acht invulvelden zichtbaar: `rol`, `taak`, `doel`, `formaat`, `stijl`, `scope`, `eisen`, `voorbeelden` _(losse textarea vervangen door story 02)_
- [ ] Er is een knop waarmee de prompt verstuurd kan worden
- [ ] Na het versturen verschijnt het antwoord van Ollama zichtbaar op de pagina
- [ ] Zolang Ollama bezig is, is zichtbaar dat er gewacht wordt (laden of vergelijkbaar)
- [ ] Als een verplicht veld (`rol`, `taak` of `doel`) leeg is bij versturen, verschijnt per ontbrekend veld een validatiemelding en wordt er geen API-call gedaan _(gewijzigd door story 02: was één generieke melding voor lege prompt)_
- [ ] Als Ollama niet bereikbaar is, verschijnt een foutmelding in de browser (geen lege pagina of stille mislukking)
- [ ] De app start met één commando (`python app.py`) en is bereikbaar op `http://localhost:3000`
