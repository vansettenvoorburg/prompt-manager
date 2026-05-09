## Story: Prompt invoeren en resultaat ontvangen via Ollama

**Als** gebruiker
**wil ik** een prompt kunnen invoeren en naar Ollama sturen
**zodat** ik een antwoord terugkrijg in de browser

### Acceptatiecriteria

- [ ] Er is een tekstvak zichtbaar waarin ik een prompt kan typen
- [ ] Er is een knop waarmee ik de prompt kan versturen
- [ ] Na het versturen verschijnt het antwoord van Ollama zichtbaar op de pagina
- [ ] Zolang Ollama bezig is, is zichtbaar dat er gewacht wordt (laden of vergelijkbaar)
- [ ] Als het tekstvak leeg is en ik verstuur, gebeurt er niets en verschijnt een melding dat een prompt vereist is
- [ ] Als Ollama niet bereikbaar is, verschijnt een foutmelding in de browser (geen lege pagina of stille mislukking)
- [ ] De app start met één commando (`python app.py`) en is bereikbaar op `http://localhost:3000`
