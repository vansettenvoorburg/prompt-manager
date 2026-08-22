# Acceptatiecriteria: Bestand import (bijlage)

Per sessie één bijlage uploaden, waarvan de inhoud automatisch wordt meegestuurd bij elke taak en
elke review.

Bron: story 07.

## Weergave

- **IMPORT-W-01** — De UI toont een bestandskiezer-knop waarmee de gebruiker één bijlage kan
  selecteren.
- **IMPORT-W-02** — Naast de knop staat de bestandsnaam van de geselecteerde bijlage, of "Geen
  bijlage" als er niets is geselecteerd.
- **IMPORT-W-03** — Er is een verwijderknop (×) zichtbaar naast de bestandsnaam zodra een bijlage
  is geselecteerd.

## Interactie

- **IMPORT-I-01** — De gebruiker kan een geselecteerde bijlage verwijderen via de verwijderknop;
  daarna keert de UI terug naar "Geen bijlage".
- **IMPORT-I-02** — De geëxtraheerde tekst uit de bijlage wordt aan het einde van de samengestelde
  prompt toegevoegd met het label `Bijlage:`; zonder bijlage ontbreekt dit blok volledig.
- **IMPORT-I-03** — De bijlage wordt meegestuurd bij elke taak en bij elke reviewstap in de sessie.
- **IMPORT-I-04** — Tekstbestanden en code (`.txt`, `.md`, `.py`, `.js`, `.ts`, `.html`, `.css`,
  `.json`) worden direct ingelezen; PDF via `pymupdf`; Word via `python-docx` (alleen tekst).
- **IMPORT-I-05** — Bij het laden van een sessie met een bijlage toont de UI de opgeslagen
  bestandsnaam met een herlaad-melding; zonder bijlage toont de UI "Geen bijlage".

## Validatie

- **IMPORT-V-01** — Bij een niet-ondersteund bestandstype retourneert de backend HTTP 400 met een
  melding, en wordt de aanvraag niet verwerkt.
- **IMPORT-V-02** — Als tekstextractie uit een PDF of Word-bestand mislukt, retourneert de backend
  HTTP 422 met een melding.
- **IMPORT-V-03** — Als het geüploade bestand leeg is, retourneert de backend HTTP 400 met een
  melding.
