## Story: Bijlage toevoegen aan een sessie

**Als** gebruiker
**wil ik** per sessie één bijlage kunnen uploaden
**zodat** de inhoud automatisch wordt meegestuurd bij elke taak en elke review, zonder dat ik dit handmatig hoef te kopiëren

---

### Acceptatiecriteria

**Bijlage uploaden in de UI**

- [ ] De UI toont een bestandskiezer-knop waarmee de gebruiker één bijlage kan selecteren
- [ ] Naast de knop staat de bestandsnaam van de geselecteerde bijlage, of "Geen bijlage" als er niets is geselecteerd
- [ ] De gebruiker kan een geselecteerde bijlage verwijderen via een verwijderknop (×) naast de bestandsnaam — daarna keert de UI terug naar "Geen bijlage"
- [ ] De bijlage is optioneel — een sessie zonder bijlage werkt ongewijzigd

**Ondersteunde bestandstypen**

- [ ] Tekstbestanden en code worden direct ingelezen: `.txt`, `.md`, `.py`, `.js`, `.ts`, `.html`, `.css`, `.json`
- [ ] PDF-bestanden worden verwerkt via `pymupdf` — alleen tekst wordt geëxtraheerd
- [ ] Word-bestanden worden verwerkt via `python-docx` — alleen tekst wordt geëxtraheerd
- [ ] Bij een niet-ondersteund bestandstype retourneert de backend HTTP 400 met de melding `"Niet-ondersteund bestandstype: [extensie] — gebruik .txt, .md, .py, .js, .ts, .html, .css, .json, .pdf of .docx"` en wordt de aanvraag niet verwerkt

**Verwerking en prompt-opbouw**

- [ ] De geëxtraheerde tekst uit de bijlage wordt aan het einde van de samengestelde prompt toegevoegd, met het label `Bijlage:`
- [ ] Voorbeeld van de uitgebreide promptstructuur:
  ```
  Als [rol] wil ik [taak] zodat [doel].
  Formaat: [formaat]
  Stijl: [stijl]
  Scope: [scope]
  Extra eisen: [eisen]
  Voorbeelden: [voorbeelden]
  Bijlage:
  [geëxtraheerde tekst]
  ```
- [ ] De bijlage wordt meegestuurd bij elke taak in de sessie
- [ ] De bijlage wordt meegestuurd bij elke reviewstap in de sessie
- [ ] Als er geen bijlage is, ontbreekt het `Bijlage:`-blok volledig in de prompt — er wordt geen leeg label toegevoegd

**Sessie opslaan en laden**

- [ ] Het sessiebestand bevat een veld `bijlage_bestandsnaam` (string, of `null` bij geen bijlage)
- [ ] Het sessiebestand bevat geen bijlage-inhoud — bij het laden wordt alleen de bestandsnaam getoond, niet de inhoud opnieuw ingeladen
- [ ] Bij het laden van een sessie met een bijlage toont de UI de opgeslagen bestandsnaam met de melding "(niet opnieuw geladen — upload indien nodig opnieuw)"
- [ ] Bij het laden van een sessie zonder bijlage toont de UI "Geen bijlage"

**Logging**

- [ ] Het logbestand bevat een veld `bijlage_bestandsnaam` (string, of `null`)
- [ ] Het logbestand bevat een veld `bijlage_tekst` met de volledige geëxtraheerde tekst zoals die naar de API is gestuurd, of `null` als er geen bijlage was
- [ ] De bestandsnaam van het logbestand verandert niet door de aanwezigheid van een bijlage

**Foutafhandeling**

- [ ] Als tekstextractie uit een PDF of Word-bestand mislukt, retourneert de backend HTTP 422 met de melding `"Bijlage kon niet worden gelezen: [reden]"` en wordt de aanvraag niet verwerkt
- [ ] Als het geüploade bestand leeg is, retourneert de backend HTTP 400 met de melding `"Bijlage is leeg — upload een bestand met inhoud"`
- [ ] Bij een fout in de bijlageverwerking wordt er geen (leeg) logbestand aangemaakt

---

### Buiten scope

- Meerdere bijlagen per sessie
- Bijlagen per taak afzonderlijk (de bijlage geldt voor de hele sessie)
- Afbeeldingen, tabellen of opmaak uit PDF of Word — alleen tekst wordt geëxtraheerd
- Opslaan van de bijlage-inhoud in het sessiebestand
- Automatisch opnieuw laden van een bijlage bij het laden van een sessie
