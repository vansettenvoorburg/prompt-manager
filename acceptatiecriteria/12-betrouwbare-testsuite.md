# Story 12: Betrouwbare volledige testsuite

**Als** ontwikkelaar
**wil ik** dat de testsuite betrouwbaar en zonder non-deterministische fails groen draait
**zodat** ik testresultaten kan vertrouwen en niet steeds handmatig hoef te bepalen of een fail echt is of een bekend flaky probleem

---

## Acceptatiecriteria

### Categorie-indeling

- [x] De testsuite is verdeeld in duidelijk gescheiden categorieën die elk met een eigen pytest-aanroep draaien (bijv. via markers, mappen of aparte commando's) — één enkele ongefilterde `pytest`-aanroep die de hele suite in dezelfde sessie draait is niet vereist
- [x] Het is voor een ontwikkelaar duidelijk (bijv. via documentatie, `pytest.ini`/`pyproject.toml`-config of een script) welk commando welke categorie draait
- [x] De categorie-indeling scheidt in elk geval de async integratietests die de `live_client`-fixture gebruiken (`tests/test_integratie_07.py`, `test_integratie_08.py`, `test_integratie_09.py`, `test_integratie_11.py`, `tests/test_review_volgorde_hoofdruns.py`) van de synchrone Playwright-gebaseerde tests

### Betrouwbaarheid per categorie

- [x] Elke categorie-aanroep slaagt 3 keer achter elkaar zonder enige `RuntimeError: Cannot run the event loop while another loop is running`
- [x] Elke categorie-aanroep slaagt 3 keer achter elkaar zonder incidentele losse fails in `tests/test_frontend_06.py` en `tests/test_frontend_08.py`
- [x] Een test die individueel (los gedraaid) slaagt, faalt niet meer wanneer deze binnen zijn categorie-run wordt meegedraaid
- [x] Geen van de bestaande tests wordt aangepast om een fail te maskeren (skip, andere verwachte uitkomst, etc.) — de oorzaak van de instabiliteit wordt weggenomen, niet de test

### Documentatie van de werkwijze

- [x] Het project bevat een korte, vindbare instructie (bijv. in `README.md` of `notes.md`) die aangeeft dat de suite per categorie gedraaid moet worden, inclusief de exacte commando's
- [x] Als een ontwikkelaar per ongeluk de volledige suite in één ongefilterde `pytest`-aanroep draait, is dat gedrag (mogelijke RuntimeError) bekend gedocumenteerd als "gebruik de categorie-commando's" — er hoeft geen foutmelding of guard in de code te komen die dit actief voorkomt

---

### Buiten scope

- Eén enkele ongefilterde `pytest`-aanroep die de volledige suite in dezelfde sessie draait alsnog volledig groen krijgen (structurele fix van de Playwright-sync/pytest-asyncio-interactie)
- Het verhogen van de teststabiliteit voor CI-omgevingen die niet lokaal zijn getest
- Het toevoegen van nieuwe tests of het uitbreiden van testdekking
- Het optimaliseren van de testduur (zie `test-performance-SKILL`)
