# Acceptatiecriteria: Algemeen

Criteria die niet bij een specifiek schermonderdeel horen (zie
`documentatie/acc_indeling.md`).

Bron: story 14 (bugfixes uit code review).

## Weergave

(geen)

## Interactie

(geen)

## Validatie

- **ALGEMEEN-V-01** — Bevat de sessienaam bij het wegschrijven van een logbestand
  (hoofdrun of reviewerstap) tekens die niet toegestaan zijn in bestandsnamen (zoals `/`, `\`,
  `..`, `:`, `*`, `?`), dan worden die tekens vervangen door een veilig teken en blijft het
  logbestand binnen de logmap — net zoals nu al gebeurt voor de modelnaam.
- **ALGEMEEN-V-02** — Hetzelfde geldt voor de providerwaarde.
- **ALGEMEEN-V-03** — Een sessienaam of provider die alleen toegestane tekens bevat, levert nog
  steeds een logbestandsnaam op met de oorspronkelijke waarde erin (geen wijziging in het
  gangbare pad).
