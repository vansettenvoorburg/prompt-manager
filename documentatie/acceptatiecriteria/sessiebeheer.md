# Acceptatiecriteria: Sessiebeheer

Een sessie (promptinhoud) opslaan onder een naam en later opnieuw laden.

Bron: story 03.

## Weergave

- **SESSIE-W-01** — Er is een invoerveld voor de sessienaam en een knop om op te slaan.
- **SESSIE-W-02** — Alle opgeslagen sessies zijn zichtbaar als een lijst; als er nog geen sessies
  zijn, toont de lijst een lege-staat melding.

## Interactie

- **SESSIE-I-01** — Na opslaan verschijnt een bevestiging met de naam waaronder de sessie is
  opgeslagen.
- **SESSIE-I-02** — Een sessie uit de lijst selecteren herstelt de promptinhoud in het formulier.

## Validatie

- **SESSIE-V-01** — Een lege sessienaam toont een validatiemelding; er wordt niets opgeslagen.
- **SESSIE-V-02** — Als een sessienaam al bestaat, wordt gevraagd of overschreven moet worden;
  annuleren doet niets.
- **SESSIE-V-03** — Als opslaan mislukt (schrijffout), verschijnt een foutmelding; de gebruiker
  raakt geen data kwijt.
- **SESSIE-V-04** — Als laden mislukt (bestand niet leesbaar of ongeldig JSON), verschijnt een
  foutmelding.
