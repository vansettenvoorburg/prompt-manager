# Notes

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
