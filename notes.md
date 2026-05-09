# Notes

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

- De story 01 backend-tests (`test_backend.py`) testen het oude `{"prompt": "..."}` formaat dat door story 02 is vervangen. Die tests zullen falen — dit is verwacht. De relevante gedragingen (503 bij Ollama-fout, e.d.) worden gedekt door de nieuwe tests in `test_backend_02.py`.
- Optionele velden worden in de frontend als lege string verstuurd; de backend laat lege optionele velden weg uit de samengestelde prompt.
