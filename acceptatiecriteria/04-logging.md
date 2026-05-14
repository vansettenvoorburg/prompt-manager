## Story: Logging

**Als** gebruiker
**wil ik** dat elke promptaanvraag en het bijbehorende antwoord automatisch worden opgeslagen
**zodat** ik altijd kan terugzien wat ik heb gevraagd en wat het model heeft geantwoord

---

### Acceptatiecriteria

**Automatisch opslaan**

- [ ] Na elke voltooide promptaanvraag wordt automatisch een logbestand aangemaakt, zonder extra handeling van de gebruiker
- [ ] Er wordt één logbestand per aanvraag aangemaakt
- [ ] Na succesvol opslaan toont de UI een korte melding met het volledige pad van het opgeslagen logbestand (bijv. "Log opgeslagen: C:\Users\mvans\Documents\PromptSessieManager\logs\2026-05-14_14-21-24_ollama_blog.json")

**Locatie**

- [ ] Op Windows worden logs opgeslagen in `C:\Users\<gebruikersnaam>\Documents\PromptSessieManager\logs\`
- [ ] Op Mac en Linux worden logs opgeslagen in `~/Documents/PromptSessieManager/logs/`
- [ ] Als de `logs/` map nog niet bestaat, maakt de applicatie die automatisch aan bij de eerste aanvraag

**Bestandsnaam**

- [ ] De bestandsnaam heeft het formaat `[datum]_[tijd]_[provider]_[sessienaam].json` (bijv. `2026-05-10_14-32-01_ollama_sessie-tests.json`)
- [ ] De datum heeft het formaat `JJJJ-MM-DD`, de tijd `UU-MM-SS`
- [ ] Als er geen sessie geladen is, wordt `geen-sessie` als sessienaam gebruikt (bijv. `2026-05-10_14-32-01_ollama_geen-sessie.json`)

**Inhoud logbestand**

- [ ] Het logbestand is geldig JSON met exact de volgende velden: `timestamp`, `provider`, `model`, `sessie`, `prompt`, `request`, `response`, `duur_seconden`
- [ ] `prompt` bevat de acht promptvelden als subobject: `rol`, `taak`, `doel`, `formaat`, `stijl`, `scope`, `eisen`, `voorbeelden`
- [ ] `request` bevat de volledige samengestelde prompt zoals die naar de API is verstuurd
- [ ] `response` bevat de ruwe tekstoutput van het model
- [ ] `timestamp` heeft het formaat `JJJJ-MM-DDTHH:MM:SS`
- [ ] `duur_seconden` bevat de meting als decimaal getal (bijv. `4.2`) van het moment van versturen tot ontvangst van de response

**Foutafhandeling**

- [ ] Als het aanmaken van het logbestand mislukt (bijv. schrijffout of ontbrekende rechten), wordt de aanvraag wél voltooid en toont de UI een waarschuwing dat logging mislukt is
- [ ] Als de `logs/` map niet aangemaakt kan worden, wordt eveneens een waarschuwing getoond; de aanvraag wordt daarna toch uitgevoerd

---

### Buiten scope

- Logs inzien, filteren of doorzoeken vanuit de UI
- Logs verwijderen of archiveren
- Meerdere providers (in deze story is alleen Ollama actief)
