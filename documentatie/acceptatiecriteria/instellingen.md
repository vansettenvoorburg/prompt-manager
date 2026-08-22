# Acceptatiecriteria: Instellingen (rate limiting)

De tab waarin de gebruiker de rate-limitinstellingen (RPM) per provider kan inzien en aanpassen.

Bron: story 09.

## Weergave

- **INSTELLINGEN-W-01** — Er is een tab "Instellingen" aanwezig die het instellingenpaneel opent.
- **INSTELLINGEN-W-02** — De tab toont een RPM-invoerveld voor Groq en voor Google; er is geen
  RPM-veld voor Ollama.
- **INSTELLINGEN-W-03** — De RPM-velden tonen de waarde die via `GET /api/settings` is opgehaald.

## Interactie

- **INSTELLINGEN-I-01** — Opslaan verstuurt de ingevoerde RPM-waarden naar de backend en deze zijn
  direct van kracht, zonder herstart.

## Validatie

Geen criteria met een rechtstreeks zichtbaar UI-gevolg in deze categorie — de validatie van de
ingevoerde waarden (bijv. negatieve RPM) is een backend-only criterium, zie de story.
