## Story: Bugfixes uit code review — veilige logbestandsnamen, upload-validatie en weergave

**Als** gebruiker
**wil ik** dat de applicatie veilig omgaat met vrije tekstinvoer in bestandsnamen, invoer via de
bijlage-upload net zo streng valideert als zonder bijlage, en AI-gegenereerde tekst nooit als
uitvoerbare code toont
**zodat** mijn systeem en browser veilig blijven en ik altijd dezelfde, duidelijke foutmeldingen
krijg ongeacht welke route ik gebruik

### Aanleiding
Gevonden tijdens code review van de volledige applicatiecode (2026-08-22):
1. `sessie` en `provider` worden ongesaneerd in de logbestandsnaam verwerkt (in tegenstelling tot
   `model`, dat al wel gesaneerd wordt) — een sessienaam of provider met padtekens kan een
   logbestand buiten de logmap laten schrijven.
2. `/api/prompt/upload` valideert `runs` en `reviewers` losser dan `/api/prompt`: ongeldige invoer
   valt daar stil terug op een default in plaats van een foutmelding te geven.
3. AI-gegenereerde tekst (hoofdrun, reviewerstap, eindoutput) wordt via `innerHTML` getoond zonder
   sanering — HTML/script-inhoud in een modelrespons wordt uitgevoerd in de browser.

### Acceptatiecriteria

**Veilige logbestandsnamen**
- [ ] Bevat de sessienaam bij het uitvoeren van een prompt tekens die niet toegestaan zijn in
      bestandsnamen (zoals `/`, `\`, `..`, `:`, `*`, `?`), dan wordt het logbestand alsnog
      binnen de logmap aangemaakt, met die tekens vervangen door een veilig teken — net zoals nu
      al gebeurt voor de modelnaam.
- [ ] Hetzelfde geldt wanneer de providerwaarde niet-toegestane bestandsnaamtekens bevat.
- [ ] Dit geldt zowel voor het logbestand van een hoofdrun als voor het logbestand van een
      reviewerstap.
- [ ] Een sessienaam of provider die alleen toegestane tekens bevat, levert nog steeds een
      logbestandsnaam op met de oorspronkelijke waarde erin (geen wijziging in het gangbare pad).

**Gelijke validatie met en zonder bijlage**
- [ ] Bij het uitvoeren van een prompt mét bijlage waarbij "Aantal runs" geen geldig getal is,
      ziet de gebruiker een foutmelding in plaats van dat de prompt stilzwijgend met 1 run wordt
      uitgevoerd.
- [ ] Bij het uitvoeren van een prompt mét bijlage waarbij de reviewer-configuratie ongeldig is,
      ziet de gebruiker een foutmelding in plaats van dat de prompt stilzwijgend zonder reviewers
      wordt uitgevoerd.
- [ ] Deze foutmeldingen zijn gelijk aan de foutmeldingen die al bestaan bij hetzelfde probleem
      zonder bijlage.
- [ ] Geldige invoer (aantal runs is een geheel getal ≥ 1, reviewers correct ingevuld) met
      bijlage blijft werken zoals nu.

**Veilige weergave van AI-output**
- [ ] Bevat een hoofdrun-resultaat HTML- of scripttags, dan worden deze getoond als platte tekst
      en niet als uitvoerbare code in de browser.
- [ ] Hetzelfde geldt voor een reviewerstap-resultaat.
- [ ] Hetzelfde geldt voor de eindoutput-sectie.
- [ ] Normale markdown-opmaak (vetgedrukt, lijsten, codeblokken, tabellen) blijft na deze
      wijziging correct weergegeven.

### Buiten scope
- Overige bevindingen uit dezelfde code review die geen gebruikersgedrag veranderen: versie
  pinnen/SRI voor de marked.js CDN-link, verbreding van brede `except Exception`-afvanging,
  opsplitsen van `_voer_prompt_uit`, samenvoegen van de gedupliceerde Groq-modellenlijst,
  datetime-inconsistentie tussen logs en sessies.
- Nieuwe reviewmodi naast "iteratief".
