# Notes

## Story 13 — Testdekkingsdocument en herstructurering testsuite

### Wat is opgeleverd

- `specs/testdekking.md`: 186 dekkingsitems (TD-01-01 t/m TD-11-19), afgeleid van
  `acceptatiecriteria/01` t/m `/12`, elk gemarkeerd `playwright` of
  `reeds gedekt door backend/integratie` met testverwijzing.
- Tests herstructureerd naar `tests/playwright/`, `tests/integratie/`, `tests/backend/`
  (indeling volgt de gebruikte fixture — `client` vs `live_client` — niet de oude
  bestandsnaam). `tests/test_integratie_11.py` gebruikte al de in-process `client`-fixture en
  is hernoemd naar `tests/backend/test_backend_11_uitgaande_aanvraag.py`.
- Elke Playwright-test heeft nu `Dekt: TD-xx-yy` in zijn docstring (143 tests, 1:1 met de
  dekkingsitems in categorie `playwright`).
- `tests/playwright/test_frontend.py` (story 01) teruggebracht van 6 naar 1 test: de overige
  5 waren letterlijke duplicaten van story 02 (achterwaartse-compat-tests met identieke code).
- 2 nieuwe Playwright-tests toegevoegd voor bestaand maar ongetest gedrag (story 08:
  `reviewer-runs`/`reviewer-temperatures`-invoervelden bestonden al in `static/app.js` maar
  hadden geen test).

### Bevinding: 2 AC-bullets beschrijven niet-geïmplementeerd gedrag

- Story 06: "UI toont de voortgang per run" — geen voortgangsindicator in `static/app.js`.
- Story 08: "gebruiker kan reviewers herordenen" — geen herordenknoppen/drag-and-drop.

Op instructie van de gebruiker gemarkeerd in `specs/testdekking.md` als
❌ niet geïmplementeerd — geen test mogelijk (TD-06-16, TD-08-07). Geen nieuwe
applicatiefunctionaliteit gebouwd (buiten scope story 13).

### Bevinding en fix: sporadische race condition in "sessie opslaan stuurt X mee"-tests

Bij het verplichte 3x-achter-elkaar-draaien (zelfde controle als story 12) faalde
`test_sessie_opslaan_stuurt_reviewers_mee` (`tests/playwright/test_frontend_08.py`)
1 op de ~3 runs met een `AssertionError` op het ontbrekende `reviewers`-veld. Oorzaak: de
test asserteerde op de opgevangen requestbody direct na `.click()` op de Opslaan-knop, zonder
te wachten tot de save daadwerkelijk was afgerond — `.click()` wacht alleen op het dispatchen
van het click-event, niet op de daaropvolgende async `fetch()` in `static/app.js`.

**2026-08-22 opgelost, met expliciete toestemming van de gebruiker** (dit is normaliter niet
toegestaan binnen story 13 — alleen locatie/naam/ID-verwijzing van bestaande tests mag
veranderen): `page.wait_for_selector("[data-testid=save-confirmation]")` toegevoegd na de
`Opslaan`-klik, vóór de assertie, in alle 9 tests met hetzelfde patroon
(`test_frontend_06.py` ×3, `test_frontend_07.py` ×2, `test_frontend_08.py` ×4,
`test_frontend_11.py` ×1). Geverifieerd: 4x achter elkaar groen op de getroffen bestanden,
en de volledige `tests/playwright`-suite 3x achter elkaar groen (146 tests, geen fails) ná de fix.

### Bevinding en fix: zelfde race condition, andere flows (na de herstructurering)

Na de herstructurering naar `weergave/`/`interactie/`/`validatie/` (commit `dea58be`) bleek
dezelfde racecondition als hierboven ook te bestaan in twee flows die niet door de eerdere
fix gedekt waren — die dekte alleen het `save-confirmation`-patroon voor "sessie opslaan"-tests:

- **Verstuur-flow** (`tests/playwright/interactie/test_provider_en_model.py` ×3,
  `test_runs_en_temperature.py` ×3): assert op de opgevangen requestbody direct na de
  Verstuur-klik, zonder te wachten op `[data-testid=run-results]`.
- **Instellingen opslaan-flow** (`tests/playwright/interactie/test_instellingen.py` ×3):
  zelfde patroon, geen equivalent van `save-confirmation` gebruikt terwijl die al bestond
  (`[data-testid=instellingen-bevestiging]`, `static/app.js:527`).

Symptoom was zichtbaar bij volledige-suite-runs (146 tests): incidenteel 1 test faalde met een
lege `vastgelegd`-dict, telkens een andere test — gemeld door de gebruiker na twee runs
(`test_geselecteerd_model_wordt_meegestuurd_bij_aanvraag`, `test_opslaan_stuurt_groq_rpm_waarde_mee`).

**2026-08-22 opgelost:** `expect(page.locator(...)).to_be_visible()` toegevoegd na de klik,
vóór de assertie — op `run-results` resp. `instellingen-bevestiging` — in alle 9 tests.

**Bijvangst:** de fix legde bloot dat 2 tests (`test_ollama_provider_meegestuurd_in_aanvraag`,
`test_groq_provider_meegestuurd_in_aanvraag`) hun `/api/prompt`-mock nog in het verouderde
responseformaat (`{"response": ...}`) hadden staan, terwijl de huidige backend altijd
`{"runs": [...]}` teruggeeft (`app.py:488`/`566`) — `run-results` bleef daardoor verborgen.
Gefixt door de bestaande `_STUB_PROMPT_RESPONSE`-constante te hergebruiken (al gebruikt door
de overige tests in hetzelfde bestand); alleen de mock aangepast, niet de assertie.

Geverifieerd: volledige `tests/playwright`-suite 3x achter elkaar groen (146/146, ~93s per run).

**Les:** dit patroon (assert op een dict gevuld in een `page.route()`-callback, direct na
`.click()`, zonder wachten op een element dat pas ná de request verschijnt) is blijkbaar
makkelijk opnieuw te introduceren bij het toevoegen/kopiëren van tests. Bij nieuwe
Playwright-tests met dit patroon: altijd eerst `expect(...).to_be_visible()` op een
post-request-element, nooit direct na `.click()` asserteren op async-gevulde state.

### Regressiecontrole (zelfde controle als story 12)

- `pytest tests/backend` — 227 tests, 3x achter elkaar groen (~12s per run)
- `pytest tests/integratie` — 19 tests, 3x achter elkaar groen (~16s per run)
- `pytest tests/playwright` — 146 tests, 3x achter elkaar groen (~90s per run, ná de race-condition-fix)

## Story 12 — Betrouwbare volledige testsuite

### Bevinding: `frontend`-marker (story 09) loste het probleem al op, alleen niemand gebruikte hem

Het `frontend`-marker in `pytest.ini` / `tests/conftest.py` (`pytest_collection_modifyitems`)
bestond al sinds story 09 en was al bedoeld om Playwright-tests apart te draaien van de
async backend-tests. Alleen werd de suite in de praktijk nog steeds met een kale `pytest`
gedraaid, wat de event-loop-conflict tussen Playwright's sync API en pytest-asyncio
opriep (`RuntimeError: Cannot run the event loop while another loop is running`).

**2026-07-12 geverifieerd:** met de bestaande marker gesplitst draaien is al voldoende:
- `pytest -m "not frontend"` — 246 tests, 3x achter elkaar groen (~52-62s per run)
- `pytest -m "frontend"` — 149 tests, 3x achter elkaar groen (~92-98s per run)

Geen van beide categorieën vertoonde de RuntimeError of de eerder gemelde incidentele
fails in `test_frontend_06.py`/`test_frontend_08.py`. Er was dus geen codewijziging nodig —
alleen de documentatie in `README.md` bijgewerkt zodat "Tests draaien" de twee
categorie-commando's voorschrijft in plaats van een kale `pytest`.

### Beslissing

- Eén ongefilterde `pytest`-aanroep die de hele suite in dezelfde sessie draait blijft
  bewust niet ondersteund (buiten scope van story 12, zie `acceptatiecriteria/12-betrouwbare-testsuite.md`).
  Een structurele fix van de Playwright-sync/pytest-asyncio-interactie is niet uitgevoerd.

## Story 02 — Acht promptvelden

### Bevinding: Playwright `post_data_json` is een property, geen methode

**Bestand:** `tests/test_frontend_02.py`, regel 147
**Test:** `test_optionele_velden_worden_meegestuurd_in_api_call`

```python
# Fout (test-bug):
captured_body.update(route.request.post_data_json())

# Correct:
captured_body.update(route.request.post_data_json)
```

In de geïnstalleerde Playwright-versie (`playwright-0.7.2`) is `post_data_json` een property die direct een `dict` teruggeeft. De test riep het aan als methode (met `()`), waardoor een `TypeError: 'dict' object is not callable` optrad. **Opgelost:** haakjes verwijderd op regel 147.

### Beslissingen

- De story 01 backend-tests (`test_backend.py`) testten het oude `{"prompt": "..."}` formaat dat door story 02 is vervangen. **2026-05-10 bijgewerkt:** tests en acceptatiecriteria van story 01 zijn aangepast naar het nieuwe acht-velden formaat conform het protocol gewijzigde requirement (implement-skill). De gedragingen voor 503 en laadstatus blijven via achterwaartse compat gedekt.
- Optionele velden worden in de frontend als lege string verstuurd; de backend laat lege optionele velden weg uit de samengestelde prompt.
