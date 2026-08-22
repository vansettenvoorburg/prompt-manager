# Acceptatiecriteria: Provider- en modelkeuze

De keuze tussen Ollama en Groq als AI-provider, en de Groq-modelkeuze.

Bronnen: story 01, 05, 11.

## Weergave

- **PROVIDER-W-01** — De UI toont een keuzelijst (dropdown) waarmee de gebruiker de provider kan
  selecteren: `Ollama` of `Groq`; de standaardwaarde is `Ollama`.
- **PROVIDER-W-02** — Wanneer provider `Groq` is geselecteerd, toont de UI een extra dropdown
  "Model"; deze is niet zichtbaar wanneer provider `Ollama` is geselecteerd.
- **PROVIDER-W-03** — De modeldropdown bevat de vier modellen (`openai/gpt-oss-120b`,
  `openai/gpt-oss-20b`, `moonshotai/kimi-k2-instruct`, `qwen3-32b`) plus het model ingesteld via
  `GROQ_MODEL` (geen duplicaat als `GROQ_MODEL` al één van de vier is); bij laden staat de
  dropdown standaard op de `GROQ_MODEL`-waarde.

## Interactie

- **PROVIDER-I-01** — De geselecteerde provider wordt meegestuurd bij elke promptaanvraag.
- **PROVIDER-I-02** — Bij het laden van een sessie wordt de opgeslagen provider automatisch
  geselecteerd in de dropdown.
- **PROVIDER-I-03** — Het geselecteerde Groq-model wordt meegestuurd bij elke promptaanvraag; bij
  het laden van een sessie met provider Groq wordt het opgeslagen model automatisch geselecteerd.
- **PROVIDER-I-04** — Bij provider `Ollama` heeft de modelkeuze geen effect.

## Validatie

- **PROVIDER-V-01** — Als Ollama niet bereikbaar is, verschijnt een foutmelding in de browser
  (geen lege pagina of stille mislukking).
- **PROVIDER-V-02** — Als de Groq API niet bereikbaar is, een fout retourneert, of de API key
  ontbreekt, toont de UI een foutmelding (geen stille mislukking).
