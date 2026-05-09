## Story: Prompt samenstellen via acht velden

**Als** gebruiker
**wil ik** een prompt kunnen samenstellen via acht aparte velden
**zodat** ik gestructureerde, herbruikbare prompts kan bouwen in plaats van alles handmatig te typen

---

### Acceptatiecriteria

**Formulier**

- [ ] De interface toont acht invulvelden: `rol`, `taak`, `doel`, `formaat`, `stijl`, `scope`, `eisen`, `voorbeelden`
- [ ] Elk veld heeft een label en een korte omschrijving als placeholder (bijv. `rol` → "senior Python developer")
- [ ] De velden `rol`, `taak` en `doel` zijn verplicht; de overige vijf zijn optioneel
- [ ] De losse `textarea` uit story 01 verdwijnt; de acht velden vervangen die volledig

**Samenstellen en versturen**

- [ ] Bij het klikken op Versturen worden de velden samengevoegd tot deze vaste template:
  ```
  Als [rol] wil ik [taak] zodat [doel].
  Formaat: [formaat]
  Stijl: [stijl]
  Scope: [scope]
  Extra eisen: [eisen]
  Voorbeelden: [voorbeelden]
  ```
- [ ] Optionele velden die leeg zijn worden weggelaten uit de samengestelde prompt (de bijbehorende regel verschijnt niet)
- [ ] De samengestelde prompt wordt naar Ollama gestuurd; het antwoord verschijnt op de pagina

**Validatie**

- [ ] Als een verplicht veld (`rol`, `taak` of `doel`) leeg is bij versturen, verschijnt per ontbrekend veld een validatiemelding
- [ ] Er wordt geen API-call gedaan zolang er een verplicht veld ontbreekt

**Achterwaartse compatibiliteit**

- [ ] De overige AC uit story 01 blijven van kracht: laadstatus, Ollama-fout tonen als 503, app start met één commando

---

### Buiten scope

- Sessies opslaan of laden — dat is story 03
- Provider kiezen — dat is story 04
