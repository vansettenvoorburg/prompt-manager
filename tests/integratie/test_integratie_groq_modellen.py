"""
Integratietest: verifieert dat elk geconfigureerd Groq-model nog een geldige,
bereikbare modelnaam is bij Groq zelf.

Aanleiding: GROQ_MODEL/GROQ_MODELS_BESCHIKBAAR kunnen modelnamen bevatten die
Groq inmiddels heeft gedecommissioned of hernoemd. De bestaande integratietests
(test_integratie_07/08/09) accepteren 400/503 als geldige uitkomst en signaleren
dit dus niet — deze test doet daarom een echte aanroep naar de Groq API (geen
mock) voor elk model, zodat een niet meer toegestaan model direct opvalt.

Vereist: GROQ_API_KEY in .env. Wordt overgeslagen als de key ontbreekt.
"""
import app as app_module
import pytest

ALLE_GROQ_MODELLEN = sorted({app_module.GROQ_MODEL, *app_module.GROQ_MODELS_BESCHIKBAAR})

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(not app_module.GROQ_API_KEY, reason="GROQ_API_KEY ontbreekt"),
]


@pytest.mark.parametrize("model", ALLE_GROQ_MODELLEN)
async def test_groq_model_is_bereikbaar_en_toegestaan(model):
    """Elk geconfigureerd Groq-model moet een echte aanroep naar Groq kunnen beantwoorden."""
    try:
        antwoord = await app_module.call_groq("Antwoord met het woord 'ok'.", 0.0, model)
    except Exception as exc:
        pytest.fail(f"Model '{model}' is niet bereikbaar of niet (meer) toegestaan bij Groq: {exc}")
    assert antwoord, f"Model '{model}' gaf een leeg antwoord terug"
