# Acceptatiecriteria: Promptvelden

De acht promptvelden (rol, taak, doel, formaat, stijl, scope, eisen, voorbeelden), de
verstuurknop, en het samenstellen van de prompt uit die velden.

Bronnen: story 01, 02, 10.

## Weergave

- **PROMPTVELDEN-W-01** — De interface toont acht invulvelden: `rol`, `taak`, `doel`, `formaat`,
  `stijl`, `scope`, `eisen`, `voorbeelden`.
- **PROMPTVELDEN-W-02** — Elk veld heeft een label en een korte omschrijving als placeholder
  (bijv. `rol` → "senior Python developer").
- **PROMPTVELDEN-W-03** — `rol`, `taak` en `doel` zijn verplicht; de overige vijf zijn optioneel.
- **PROMPTVELDEN-W-04** — Er is een knop waarmee de prompt verstuurd kan worden.
- **PROMPTVELDEN-W-05** — `formaat`, `taak` en `doel` zijn textarea's in plaats van tekstvelden;
  `formaat` heeft standaard 3 rijen zichtbare ruimte, `taak` en `doel` elk 2 rijen; `eisen` en
  `voorbeelden` blijven ongewijzigd textarea met 3 rijen.

## Interactie

- **PROMPTVELDEN-I-01** — Bij het klikken op Versturen worden de velden samengevoegd tot de vaste
  template:
  ```
  Als [rol] wil ik [taak] zodat [doel].
  Formaat: [formaat]
  Stijl: [stijl]
  Scope: [scope]
  Extra eisen: [eisen]
  Voorbeelden: [voorbeelden]
  ```
- **PROMPTVELDEN-I-02** — Optionele velden die leeg zijn worden weggelaten uit de samengestelde
  prompt (de bijbehorende regel verschijnt niet).
- **PROMPTVELDEN-I-03** — Enters (newlines) worden geaccepteerd in `formaat`, `taak` en `doel`, en
  blijven behouden bij opslaan en laden van een sessie.

## Validatie

- **PROMPTVELDEN-V-01** — Als een verplicht veld (`rol`, `taak` of `doel`) leeg is bij versturen,
  verschijnt per ontbrekend veld een validatiemelding en wordt er geen API-call gedaan.
- **PROMPTVELDEN-V-02** — Validatie op `rol`, `taak` en `doel` werkt ongewijzigd, ook na de
  omzetting naar textarea.
