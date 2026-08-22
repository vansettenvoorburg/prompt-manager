# Story 13: Testdekkingsdocument en herstructurering testsuite

**Als** ontwikkelaar
**wil ik** een testdekkingsdocument dat de browserdekking per feature vastlegt met traceerbare
Playwright-tests, en een testsuite die in drie duidelijk gescheiden, apart draaibare categorieën
is ingedeeld (Playwright, integratie, backend)
**zodat** ik kan zien welke scenario's gedekt zijn, ontbrekende of dubbele dekking kan opsporen,
en gericht één categorie kan draaien zonder de andere te raken

---

## Aanleiding

- De bestaande `frontend`-marker scheidt Playwright-tests al van de rest, maar "integratie" en
  "backend" zijn nog niet apart draaibaar: beide draaien nu samen onder `pytest -m "not frontend"`.
- De bestandsnamen `test_integratie_*.py` zijn niet meer betrouwbaar: `test_integratie_07.py`,
  `test_integratie_08.py` en `test_integratie_09.py` gebruiken de `live_client`-fixture (echte
  HTTP-call naar de draaiende server), maar `test_integratie_11.py` en
  `test_review_volgorde_hoofdruns.py` gebruiken inmiddels de in-process `client`-fixture — net als
  alle `test_backend_*.py`-bestanden en `test_bugfix_reviewer_bijlage.py` /
  `test_bugfix_reviewer_per_hoofdrun.py`. De nieuwe indeling volgt de fixture die een test
  daadwerkelijk gebruikt, niet de huidige bestandsnaam.
- Er bestaat nog geen document dat in één oogopslag toont welke browserscenario's (velden,
  validaties, providers, knoppen) gedekt zijn en welke Playwright-test dat scenario dekt.

---

## Acceptatiecriteria

### Testdekkingsdocument

- [ ] `specs/testdekking.md` bevat, afgeleid van `acceptatiecriteria/01` t/m `acceptatiecriteria/12`,
      een lijst van concrete dekkingsitems voor elk browser-gedrag (bijv. per invoerveld: verplicht/
      optioneel, minimaal geldige waarde, ontbrekende-waarde-validatie; per knop: zichtbaarheid en
      klikgedrag; per providerkeuze: het bijbehorende scenario)
- [ ] Elk dekkingsitem heeft een uniek ID (bijv. `TD-02-03`: story 02, item 3) en verwijst naar het
      bron-AC-bestand + AC-nummer waarvan het is afgeleid
- [ ] Elk dekkingsitem is gemarkeerd met de categorie waarin het gedekt hoort te worden:
      `playwright` (browser-gedrag) of `reeds gedekt door backend/integratie` (met verwijzing naar
      het testbestand) — zodat er geen dekking dubbel in twee categorieën terechtkomt
- [ ] Het document bevat geen dekkingsitems voor gedrag dat niet in een bestaande acceptatiecriteria-
      file staat

### Playwright-tests traceerbaar naar dekking

- [ ] Elke Playwright-test in de herstructureerde locatie (zie hieronder) heeft in zijn docstring
      het dekkingsitem-ID dat hij dekt (bijv. `Dekt: TD-02-03`)
- [ ] Elk dekkingsitem met categorie `playwright` in `specs/testdekking.md` heeft minimaal één test
      die naar dat ID verwijst
- [ ] Geen twee tests dekken exact hetzelfde dekkingsitem met hetzelfde scenario (geen duplicatie)
- [ ] Bestaande Playwright-tests die geen overeenkomstig dekkingsitem hebben (verouderd/overbodig
      geworden gedrag) worden verwijderd; tests die wél overeenkomen maar nog geen ID-verwijzing
      hebben, krijgen die verwijzing toegevoegd

### Drie gescheiden testcategorieën

- [ ] De tests staan in drie mappen: `tests/playwright/` (huidige `test_frontend_*.py`),
      `tests/integratie/` (tests die de `live_client`-fixture gebruiken:
      `test_integratie_07.py`, `test_integratie_08.py`, `test_integratie_09.py`), `tests/backend/`
      (alle overige tests die de in-process `client`-fixture gebruiken, inclusief het huidige
      `test_integratie_11.py`, `test_review_volgorde_hoofdruns.py`,
      `test_bugfix_reviewer_bijlage.py`, `test_bugfix_reviewer_per_hoofdrun.py` en alle
      `test_backend_*.py`)
- [ ] Bestanden die naar `tests/backend/` verhuizen maar nog "integratie" in hun naam dragen
      (`test_integratie_11.py`) worden hernoemd zodat de naam de fixture/categorie weerspiegelt
- [ ] README.md documenteert drie aparte commando's, één per map (bijv.
      `pytest tests/playwright`, `pytest tests/integratie`, `pytest tests/backend`), inclusief de
      volgorde-onafhankelijke waarschuwing die er al staat over een ongefilterde `pytest`-aanroep
- [ ] De inhoud (assertions, scenario's, verwachte uitkomsten) van bestaande backend- en
      integratietests blijft ongewijzigd — alleen bestandslocatie, bestandsnaam en eventuele
      importpaden veranderen
- [ ] `tests/conftest.py` (of de fixtures die het bevat) werkt ongewijzigd voor alle drie de mappen

### Regressie

- [ ] Elk van de drie categorie-commando's slaagt 3 keer achter elkaar zonder non-deterministische
      fails (dezelfde controle als story 12)
- [ ] Samen dekken de drie categorieën exact dezelfde tests als de huidige twee categorieën
      (`pytest -m "not frontend"` + `pytest -m "frontend"`) — geen test gaat verloren of dubbel
      meetellen
- [ ] Geen bestaande test wordt aangepast om een fail te maskeren — alleen locatie/naam/ID-
      verwijzing verandert (zie hierboven)

---

### Buiten scope

- Migratie naar TypeScript Playwright (bewuste keuze: Python/pytest-playwright blijft de stack)
- Inhoudelijke uitbreiding of herziening van backend- of integratietest-scenario's (alleen
  herstructurering, geen nieuwe dekking daar)
- Nieuwe functionaliteit of gedragswijzigingen in `app.py`
- Het optimaliseren van testduur (zie `test-performance-SKILL`)
