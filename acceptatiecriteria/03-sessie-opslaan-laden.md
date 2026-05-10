## Story: Sessie opslaan en laden

**Als** gebruiker
**wil ik** een sessie kunnen opslaan en later opnieuw laden
**zodat** ik eerder opgebouwde prompts kan hergebruiken zonder alles opnieuw in te typen

---

### Acceptatiecriteria

**Opslaan**

- [ ] Er is een invoerveld voor de sessienaam en een knop om op te slaan
- [ ] Na opslaan verschijnt een bevestiging met de naam waaronder de sessie is opgeslagen
- [ ] Een lege sessienaam toont een validatiemelding; er wordt niets opgeslagen
- [ ] Als een sessienaam al bestaat, word ik gevraagd of ik wil overschrijven; annuleren doet niets

**Laden**

- [ ] Alle opgeslagen sessies zijn zichtbaar als een lijst
- [ ] Ik kan een sessie uit de lijst selecteren; daarna wordt de promptinhoud hersteld in het formulier
- [ ] Als er nog geen sessies zijn, toont de lijst een lege-staat melding

**Opslag**

- [ ] Een sessie wordt opgeslagen als JSON-bestand in de `sessions/` map (bijv. `sessions/mijn-sessie.json`)
- [ ] Als de `sessions/` map nog niet bestaat, maakt de backend die automatisch aan
- [ ] De JSON bevat minimaal: `name`, `created_at` en de acht promptvelden (`rol`, `taak`, `doel`, `formaat`, `stijl`, `scope`, `eisen`, `voorbeelden`); `provider` wordt opgeslagen als vaste waarde `"ollama"` en `model` als de huidig geconfigureerde waarde (provider-keuze is story 04)

**Foutafhandeling**

- [ ] Als opslaan mislukt (schrijffout), verschijnt een foutmelding; de gebruiker raakt geen data kwijt
- [ ] Als laden mislukt (bestand niet leesbaar of ongeldig JSON), verschijnt een foutmelding

---

### Buiten scope

- Sessies verwijderen of hernoemen
- Versiegeschiedenis van een sessie
- De acht promptvelden (rol, taak, doel, …) — dat is story 02 (vereist voor deze story)
