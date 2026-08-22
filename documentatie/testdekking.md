# Testdekking

Dit document legt per browser-gedrag uit **welk dekkingsitem** het betreft, **uit welk
acceptatiecriteria-bestand** het is afgeleid, en **in welke testlaag** het gedekt hoort te
worden: `playwright` (browser-gedrag, getest via `tests/playwright/`) of `reeds gedekt door
backend/integratie` (getest via `tests/backend/` of `tests/integratie/`, met verwijzing naar het
testbestand).

Elk dekkingsitem heeft een uniek ID in de vorm `TD-<story>-<volgnummer>`, bijv. `TD-02-03` =
story 02, dekkingsitem 3. Playwright-tests verwijzen in hun docstring naar het ID dat ze dekken
(`Dekt: TD-02-03`).

## Leeswijzer / uitgesloten gedrag

Niet elk AC-bullet uit `acceptatiecriteria/01` t/m `/12` levert een dekkingsitem op:

- **Niet-browsergedrag** (opstartcommando, bestandslocatie-config zoals `.env.example`) valt
  buiten het bereik van dit document — dat is geen "browser-gedrag" en niet zinvol via
  Playwright of een HTTP-testclient te verifiëren.
- **Zuiver visuele/CSS-criteria** (bijv. "kopieerknop is visueel subtiel") lenen zich niet voor
  een functionele Playwright-assertie en zijn uitgesloten.
- **AC-bullets die door een latere story letterlijk zijn overgenomen** (story 01 → story 02,
  zelfde scenario, zelfde test) krijgen één dekkingsitem onder de story die het scenario nu
  definieert; de oudere story verwijst ernaar in plaats van een dubbel item te krijgen.
- **AC-beschreven gedrag dat niet in de huidige implementatie bestaat** krijgt wél een
  dekkingsitem (categorie `playwright`), maar is gemarkeerd ❌ **niet geïmplementeerd — geen
  test mogelijk**. Er is voor dit document geen nieuwe applicatiefunctionaliteit gebouwd (buiten
  scope van story 13); zie het item TD-08-07.
- Bij twee items **⚠️** wijkt de praktijkbevinding af van de letterlijke AC-tekst (zie de noot
  bij het item). Ook dit valt buiten scope om te herstellen in deze story.

Story 12 (`12-betrouwbare-testsuite.md`) beschrijft alleen testinfrastructuur, geen browsergedrag,
en levert daarom geen dekkingsitems op.

---

## Story 01 — Prompt invoeren en resultaat ontvangen via Ollama

Bron: `acceptatiecriteria/01-prompt-invoeren-ollama.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-01-01 | Verstuurknop is zichtbaar | playwright | `tests/playwright/test_frontend.py::test_verstuurknop_is_zichtbaar` |

Overige AC-bullets van story 01 (acht velden zichtbaar, antwoord verschijnt, laadstatus,
per-veld validatie, Ollama-foutmelding) zijn letterlijk overgenomen en verfijnd door story 02 —
zie TD-02-01, TD-02-07, TD-02-08, TD-02-09, TD-02-10. "App start met één commando" is
niet-browsergedrag (zie leeswijzer).

---

## Story 02 — Prompt samenstellen via acht velden

Bron: `acceptatiecriteria/02-acht-promptvelden.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-02-01 | Interface toont acht invulvelden (rol, taak, doel, formaat, stijl, scope, eisen, voorbeelden) | playwright | `test_frontend_02.py::test_alle_acht_velden_zijn_zichtbaar` |
| TD-02-02 | Elk veld heeft een zichtbaar label | playwright | `test_frontend_02.py::test_elk_veld_heeft_een_label` |
| TD-02-03 | Elk veld heeft een niet-lege placeholder | playwright | `test_frontend_02.py::test_elk_veld_heeft_een_placeholder` |
| TD-02-04 | De losse textarea uit story 01 is verdwenen | playwright | `test_frontend_02.py::test_losse_textarea_is_verdwenen` |
| TD-02-05 | Samengestelde prompt volgt de vaste template | backend/integratie | `test_backend_02.py::test_prompt_template_vaste_structuur` |
| TD-02-06 | Lege optionele velden worden weggelaten uit de samengestelde prompt | backend/integratie | `test_backend_02.py::test_lege_optionele_velden_worden_weggelaten`, `test_gedeeltelijk_optioneel_ingevuld` |
| TD-02-07 | Antwoord van Ollama verschijnt na correct invullen en versturen | playwright | `test_frontend_02.py::test_antwoord_verschijnt_na_correct_invullen` |
| TD-02-08 | Leeg verplicht veld (rol/taak/doel) → per-veld validatiemelding, geen API-call | playwright | `test_frontend_02.py::test_leeg_rol_toont_validatiemelding`, `test_lege_taak_toont_validatiemelding`, `test_leeg_doel_toont_validatiemelding`, `test_meerdere_lege_verplichte_velden_tonen_elk_een_melding` |
| TD-02-09 | Laadstatus zichtbaar tijdens wachten (achterwaartse compat story 01) | playwright | `test_frontend_02.py::test_laadstatus_zichtbaar_tijdens_wachten` |
| TD-02-10 | Ollama-fout toont foutmelding (achterwaartse compat story 01) | playwright | `test_frontend_02.py::test_ollama_fout_toont_foutmelding` |
| TD-02-11 | Ingevulde optionele velden worden meegestuurd in de API-aanvraag | playwright | `test_frontend_02.py::test_optionele_velden_worden_meegestuurd_in_api_call` |

---

## Story 03 — Sessie opslaan en laden

Bron: `acceptatiecriteria/03-sessie-opslaan-laden.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-03-01 | Invoerveld sessienaam is zichtbaar | playwright | `test_frontend_03.py::test_sessienaam_invoerveld_is_zichtbaar` |
| TD-03-02 | Opslaan-knop is zichtbaar | playwright | `test_frontend_03.py::test_opslaan_knop_is_zichtbaar` |
| TD-03-03 | Na opslaan verschijnt bevestiging met de sessienaam | playwright | `test_frontend_03.py::test_opslaan_toont_bevestiging` |
| TD-03-04 | Lege sessienaam → validatiemelding, geen API-call | playwright | `test_frontend_03.py::test_lege_sessienaam_toont_validatiemelding` |
| TD-03-05 | Bestaande sessienaam → bevestigingsdialoog voor overschrijven | playwright | `test_frontend_03.py::test_bestaande_naam_toont_bevestigingsdialoog` |
| TD-03-06 | Annuleren bij overschrijven doet niets | playwright | `test_frontend_03.py::test_annuleren_bij_overschrijven_doet_niets` |
| TD-03-07 | Opgeslagen sessies zijn zichtbaar als lijst | playwright | `test_frontend_03.py::test_sessieslijst_is_zichtbaar`, `test_sessie_in_lijst_is_zichtbaar_na_ophalen` |
| TD-03-08 | Sessie selecteren herstelt de promptinhoud in het formulier | playwright | `test_frontend_03.py::test_sessie_selecteren_herstelt_formulier` |
| TD-03-09 | Lege sessieslijst toont een lege-staat melding | playwright | `test_frontend_03.py::test_lege_sessieslijst_toont_melding` |
| TD-03-10 | Opslaan mislukt (schrijffout) → foutmelding | playwright | `test_frontend_03.py::test_opslaan_mislukt_toont_foutmelding` |
| TD-03-11 | Laden mislukt (ongeldig bestand) → foutmelding | playwright | `test_frontend_03.py::test_laden_mislukt_toont_foutmelding` |
| TD-03-12 | Sessie opgeslagen als JSON in `sessions/`; map wordt automatisch aangemaakt | backend/integratie | `test_backend_03.py::test_sessie_opslaan_maakt_bestand_aan`, `test_sessions_map_wordt_automatisch_aangemaakt` |
| TD-03-13 | JSON bevat verplichte velden (`name`, `created_at`, 8 promptvelden); `provider` vast `"ollama"` | backend/integratie | `test_backend_03.py::test_sessie_json_bevat_verplichte_velden`, `test_sessie_json_provider_is_ollama` |
| TD-03-14 | Sessie-API: conflict (409)/force (200)/onbekend (404)/corrupt (500)/lijst ophalen | backend/integratie | `test_backend_03.py::test_lege_sessienaam_geeft_400`, `test_bestaande_naam_geeft_409`, `test_overschrijven_met_force_geeft_200`, `test_onbekende_sessie_geeft_404`, `test_corrupt_sessie_geeft_500`, `test_sessies_ophalen_geeft_lijst`, `test_sessies_ophalen_leeg`, `test_sessie_laden` |

---

## Story 04 — Logging

Bron: `acceptatiecriteria/04-logging.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-04-01 | Na succesvolle aanvraag toont de UI 'Log opgeslagen' met bestandspad | playwright | `test_frontend_04.py::test_log_opgeslagen_melding_zichtbaar_na_aanvraag` |
| TD-04-02 | Logging mislukt → UI toont waarschuwing, antwoord blijft zichtbaar | playwright | `test_frontend_04.py::test_log_mislukt_toont_waarschuwing`, `test_log_mislukt_toont_antwoord_toch` |
| TD-04-03 | Logbestand automatisch aangemaakt na elke aanvraag, één per run | backend/integratie | `test_backend_04.py::test_logbestand_aangemaakt_na_prompt`, `test_een_logbestand_per_aanvraag` |
| TD-04-04 | Logs-map (OS-specifieke locatie) wordt automatisch aangemaakt | backend/integratie | `test_backend_04.py::test_logs_map_wordt_automatisch_aangemaakt` |
| TD-04-05 | Bestandsnaamformaat `[datum]_[tijd]_[provider]_[sessienaam].json` | backend/integratie | `test_backend_04.py::test_bestandsnaam_formaat`, `test_bestandsnaam_bevat_provider`, `test_bestandsnaam_bevat_sessienaam` |
| TD-04-06 | Geen geladen sessie → `geen-sessie` in bestandsnaam | backend/integratie | `test_backend_04.py::test_bestandsnaam_zonder_sessie_gebruikt_geen_sessie` |
| TD-04-07 | Logbestand is geldig JSON met exact de verplichte velden | backend/integratie | `test_backend_04.py::test_loginhoud_bevat_verplichte_velden` |
| TD-04-08 | `prompt`-subobject bevat de acht promptvelden | backend/integratie | `test_backend_04.py::test_loginhoud_prompt_heeft_acht_velden` |
| TD-04-09 | `request` bevat de samengestelde prompt | backend/integratie | `test_backend_04.py::test_loginhoud_request_is_samengestelde_prompt` |
| TD-04-10 | `response` bevat de ruwe modeloutput | backend/integratie | `test_backend_04.py::test_loginhoud_response_is_modeloutput` |
| TD-04-11 | `timestamp`-formaat `JJJJ-MM-DDTHH:MM:SS` | backend/integratie | `test_backend_04.py::test_loginhoud_timestamp_formaat` |
| TD-04-12 | `duur_seconden` is een decimaal getal | backend/integratie | `test_backend_04.py::test_loginhoud_duur_seconden_is_decimaal` |
| TD-04-13 | Schrijffout bij loggen → aanvraag toch voltooid, `log_warning` teruggegeven | backend/integratie | `test_backend_04.py::test_schrijffout_voltooit_aanvraag_toch`, `test_schrijffout_retourneert_log_warning` |
| TD-04-14 | Logs-map niet aan te maken → waarschuwing, aanvraag toch uitgevoerd | backend/integratie | `test_backend_04.py::test_logs_map_aanmaken_mislukt_voltooit_aanvraag`, `test_logs_map_aanmaken_mislukt_retourneert_log_warning` |
| TD-04-15 | `sessie`-veld in log klopt (of `geen-sessie` zonder geladen sessie) | backend/integratie | `test_backend_04.py::test_loginhoud_sessie_klopt`, `test_loginhoud_sessie_is_geen_sessie_zonder_sessie` |

---

## Story 05 — Groq toevoegen als tweede provider

Bron: `acceptatiecriteria/05-groq-provider.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-05-01 | Providerdropdown is zichtbaar | playwright | `test_frontend_05.py::test_provider_dropdown_is_zichtbaar` |
| TD-05-02 | Dropdown bevat de optie 'Ollama' | playwright | `test_frontend_05.py::test_dropdown_heeft_ollama_optie` |
| TD-05-03 | Dropdown bevat de optie 'Groq' | playwright | `test_frontend_05.py::test_dropdown_heeft_groq_optie` |
| TD-05-04 | Standaardwaarde van de dropdown is 'Ollama' | playwright | `test_frontend_05.py::test_standaard_provider_is_ollama` |
| TD-05-05 | Geselecteerde provider wordt meegestuurd in de aanvraag | playwright | `test_frontend_05.py::test_ollama_provider_meegestuurd_in_aanvraag`, `test_groq_provider_meegestuurd_in_aanvraag` |
| TD-05-06 | Bij laden van een sessie wordt de opgeslagen provider geselecteerd in de dropdown | playwright | `test_frontend_05.py::test_sessie_laden_herstelt_provider_in_dropdown`, `test_sessie_laden_herstelt_ollama_provider` |
| TD-05-07 | Groq-fout → zichtbare foutmelding, geen stille mislukking | playwright | `test_frontend_05.py::test_groq_fout_toont_foutmelding`, `test_groq_fout_geen_stille_mislukking` |
| TD-05-08 | Groq-aanroep via OpenAI-compatibele endpoint met `GROQ_API_KEY` uit `.env` | backend/integratie | `test_backend_05.py::test_groq_provider_roept_call_groq_aan` |
| TD-05-09 | `GROQ_MODEL` instelbaar via env, standaard `llama3-8b-8192` | backend/integratie | `test_backend_05.py::test_groq_model_standaard_is_llama3`, `test_groq_model_instelbaar_via_env` |
| TD-05-10 | Samengestelde prompt identiek opgebouwd bij Ollama en Groq | backend/integratie | `test_backend_05.py::test_prompt_identiek_opgebouwd_bij_groq_en_ollama` |
| TD-05-11 | Logbestandsnaam bevat `groq` als provider | backend/integratie | `test_backend_05.py::test_groq_logbestandsnaam_bevat_groq` |
| TD-05-12 | Logveld `provider` bevat `"groq"` | backend/integratie | `test_backend_05.py::test_groq_logveld_provider_is_groq` |
| TD-05-13 | Logveld `model` bevat het gebruikte Groq-model | backend/integratie | `test_backend_05.py::test_groq_logveld_model_bevat_groq_model` |
| TD-05-14 | Geselecteerde provider meegeslagen in sessiebestand | backend/integratie | `test_backend_05.py::test_sessie_opslaan_bevat_provider`, `test_sessie_opslaan_slaat_groq_provider_op`, `test_sessie_laden_geeft_provider_terug` |
| TD-05-15 | `GROQ_API_KEY` ontbreekt/leeg + Groq gekozen → 503 met vaste melding | backend/integratie | `test_backend_05.py::test_groq_key_ontbreekt_geeft_503`, `test_groq_key_ontbreekt_foutmelding` |
| TD-05-16 | Groq-fout of ontbrekende key → geen (leeg) logbestand | backend/integratie | `test_backend_05.py::test_groq_fout_geen_logbestand`, `test_groq_key_ontbreekt_geen_logbestand` |
| TD-05-17 | API key verschijnt nooit in sessiebestand of logbestand (velden bevatten exact het verwachte, geen key) | backend/integratie | `test_backend_04.py::test_loginhoud_bevat_verplichte_velden`, `test_backend_03.py::test_sessie_json_bevat_verplichte_velden` |

---

## Story 06 — Aantal runs en temperature per run

Bron: `acceptatiecriteria/06-runs-en-temperature.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-06-01 | Invoerveld 'Aantal runs' is zichtbaar | playwright | `test_frontend_06.py::test_runs_invoerveld_is_zichtbaar` |
| TD-06-02 | Standaardwaarde 'Aantal runs' is 1 | playwright | `test_frontend_06.py::test_runs_standaardwaarde_is_1` |
| TD-06-03 | Keuzeschakelaar temperature-modus is zichtbaar | playwright | `test_frontend_06.py::test_temperature_modus_schakelaar_is_zichtbaar` |
| TD-06-04 | Schakelaar heeft optie 'één temperature voor alle runs' | playwright | `test_frontend_06.py::test_temperature_modus_heeft_optie_alle` |
| TD-06-05 | Schakelaar heeft optie 'één temperature per run' | playwright | `test_frontend_06.py::test_temperature_modus_heeft_optie_per_run` |
| TD-06-06 | Temperature-invoerveld is zichtbaar | playwright | `test_frontend_06.py::test_temperature_invoerveld_is_zichtbaar` |
| TD-06-07 | Ollama-default temperature is 0.8 | playwright | `test_frontend_06.py::test_ollama_temperature_standaard_is_0_punt_8` |
| TD-06-08 | Groq-default temperature is 1 | playwright | `test_frontend_06.py::test_groq_temperature_standaard_is_1` |
| TD-06-09 | Wisselen naar Groq werkt temperature bij naar 1 | playwright | `test_frontend_06.py::test_wisselen_naar_groq_werkt_temperature_bij` |
| TD-06-10 | Wisselen naar Ollama werkt temperature bij naar 0.8 | playwright | `test_frontend_06.py::test_wisselen_naar_ollama_werkt_temperature_bij` |
| TD-06-11 | Handmatig gewijzigde temperature wordt niet overschreven bij providerwissel | playwright | `test_frontend_06.py::test_handmatig_gewijzigde_temperature_wordt_niet_overschreven` |
| TD-06-12 | Temperature-label toont een verplicht-aanduiding | playwright | `test_frontend_06.py::test_temperature_label_heeft_verplicht_aanduiding` |
| TD-06-13 | `runs`/`temperature_modus`/`temperatures` worden meegestuurd bij uitvoeren | playwright | `test_frontend_06.py::test_runs_wordt_meegestuurd_in_aanvraag`, `test_temperature_modus_wordt_meegestuurd_in_aanvraag`, `test_temperatures_wordt_meegestuurd_in_aanvraag` |
| TD-06-14 | `runs`/`temperature_modus`/`temperatures` worden meegestuurd bij sessie opslaan | playwright | `test_frontend_06.py::test_sessie_opslaan_stuurt_runs_mee`, `test_sessie_opslaan_stuurt_temperature_modus_mee`, `test_sessie_opslaan_stuurt_temperatures_mee` |
| TD-06-15 | Bij laden sessie worden `runs`/modus/waarden automatisch ingevuld | playwright | `test_frontend_06.py::test_sessie_laden_vult_runs_in`, `test_sessie_laden_vult_temperature_modus_in`, `test_sessie_laden_vult_temperatures_in` |
| TD-06-16 | Na afloop toont de UI alle run-resultaten op volgorde | playwright | `test_frontend_06.py::test_ui_toont_alle_run_resultaten_na_uitvoering` |
| TD-06-17 | `runs` < 1 → foutmelding, aanvraag niet verstuurd | playwright | `test_frontend_06.py::test_runs_nul_toont_foutmelding_en_verstuurt_niet` |
| TD-06-18 | Lege temperature → foutmelding, aanvraag geblokkeerd | playwright | `test_frontend_06.py::test_temperature_leeg_toont_foutmelding_en_verstuurt_niet` |
| TD-06-19 | Temperature buiten 0–2 → foutmelding die het bereik noemt | playwright | `test_frontend_06.py::test_temperature_buiten_bereik_toont_foutmelding`, `test_temperature_foutmelding_noemt_bereik` |
| TD-06-20 | Modus `per_run` met verkeerd aantal temperatures → foutmelding met verwacht aantal | playwright | `test_frontend_06.py::test_per_run_mismatch_toont_foutmelding`, `test_per_run_mismatch_foutmelding_noemt_verwacht_aantal` |
| TD-06-21 | Sessie zonder runs/temperature-velden laadt zonder foutmelding | playwright | `test_frontend_06.py::test_sessie_laden_zonder_runs_velden_geeft_geen_fout` ⚠️ AC verwacht een *leeg* temperature-veld na laden; de implementatie laat het veld op de bestaande/standaardwaarde staan. De test verifieert alleen dat laden niet crasht, niet het "leeg"-gedrag. |
| TD-06-22 | Mislukte run → foutmelding voor die run, geslaagde run blijft zichtbaar | playwright | `test_frontend_06.py::test_ui_toont_foutmelding_voor_mislukte_run`, `test_ui_toont_geslaagde_run_ondanks_mislukte_run` |
| TD-06-23 | Prompt wordt precies `runs` keer verstuurd | backend/integratie | `test_backend_06.py::test_drie_runs_roept_api_drie_keer_aan`, `test_een_run_roept_api_een_keer_aan` |
| TD-06-24 | Modus `alle` gebruikt dezelfde temperature voor elke run | backend/integratie | `test_backend_06.py::test_modus_alle_geeft_zelfde_temperature_aan_elke_run` |
| TD-06-25 | Modus `per_run` gebruikt de temperature die bij het volgnummer hoort | backend/integratie | `test_backend_06.py::test_modus_per_run_geeft_juiste_temperature_per_run` |
| TD-06-26 | Runs worden sequentieel uitgevoerd en op volgorde teruggegeven | backend/integratie | `test_backend_06.py::test_response_runs_bevat_antwoorden_op_volgorde` |
| TD-06-27 | Sessiebestand bevat `runs`/`temperature_modus`/`temperatures` | backend/integratie | `test_backend_06.py::test_sessie_opslaan_bevat_runs`, `test_sessie_opslaan_bevat_temperature_modus`, `test_sessie_opslaan_bevat_temperatures` |
| TD-06-28 | Elke run apart logbestand, bestandsnaam bevat run-nummer + temperature, `run_nummer`/`temperature`-velden, altijd `_run1`-suffix bij 1 run | backend/integratie | `test_backend_06.py::test_drie_runs_maakt_drie_logbestanden`, `test_logbestandsnaam_bevat_run_nummers`, `test_logbestandsnaam_bevat_temperature`, `test_logbestand_bevat_run_nummer_veld`, `test_logbestand_bevat_temperature_veld`, `test_een_run_heeft_altijd_run_suffix` |
| TD-06-29 | Mislukte run → uitvoering gaat door, geen logbestand voor die run | backend/integratie | `test_backend_06.py::test_uitvoering_gaat_door_na_mislukte_run`, `test_mislukte_run_maakt_geen_logbestand`, `test_geslaagde_run_na_mislukte_run_heeft_log` |
| TD-06-30 | Mislukte run bevat foutmelding in de response | backend/integratie | `test_backend_06.py::test_mislukte_run_bevat_foutmelding_in_response` |

---

## Story 07 — Bijlage toevoegen aan een sessie

Bron: `acceptatiecriteria/07-bijlage.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-07-01 | Bestandskiezer-knop voor bijlage is zichtbaar | playwright | `test_frontend_07.py::test_bijlage_knop_is_zichtbaar` |
| TD-07-02 | Status toont "Geen bijlage" of de geselecteerde bestandsnaam | playwright | `test_frontend_07.py::test_bijlage_label_toont_geen_bijlage_als_standaard`, `test_geselecteerd_bestand_toont_bestandsnaam` |
| TD-07-03 | Verwijderknop (×): zichtbaar na selectie, reset naar "Geen bijlage", verdwijnt na klik | playwright | `test_frontend_07.py::test_verwijderknop_is_zichtbaar_na_selectie`, `test_verwijderknop_reset_naar_geen_bijlage`, `test_verwijderknop_verdwijnt_na_klikken` |
| TD-07-04 | Aanvraag zonder bijlage slaagt (bijlage is optioneel) | playwright | `test_frontend_07.py::test_aanvraag_zonder_bijlage_slaagt` |
| TD-07-05 | Sessie opslaan stuurt `bijlage_bestandsnaam` mee (of `null` zonder bijlage) | playwright | `test_frontend_07.py::test_sessie_opslaan_stuurt_bijlage_bestandsnaam_mee`, `test_sessie_opslaan_zonder_bijlage_stuurt_null_mee` |
| TD-07-06 | Sessie laden met bijlage toont bestandsnaam + herlaad-melding | playwright | `test_frontend_07.py::test_sessie_laden_met_bijlage_toont_bestandsnaam`, `test_sessie_laden_met_bijlage_toont_herlaad_melding` |
| TD-07-07 | Sessie laden zonder bijlage toont "Geen bijlage" | playwright | `test_frontend_07.py::test_sessie_laden_zonder_bijlage_toont_geen_bijlage`, `test_sessie_laden_zonder_bijlage_veld_geeft_geen_fout` |
| TD-07-08 | Tekst/code-bestanden worden direct ingelezen | backend/integratie | `test_backend_07.py::test_tekst_bestandstype_wordt_geaccepteerd` |
| TD-07-09 | PDF wordt verwerkt via `pymupdf` | backend/integratie | `test_backend_07.py::test_pdf_bestand_wordt_geaccepteerd` |
| TD-07-10 | Word wordt verwerkt via `python-docx` | backend/integratie | `test_backend_07.py::test_docx_bestand_wordt_geaccepteerd` |
| TD-07-11 | Niet-ondersteund bestandstype → 400 met melding | backend/integratie | `test_backend_07.py::test_niet_ondersteund_type_geeft_400`, `test_niet_ondersteund_type_foutmelding_vermeldt_extensie`, `test_niet_ondersteund_type_foutmelding_vermeldt_ondersteunde_types` |
| TD-07-12 | Bijlagetekst toegevoegd aan einde van prompt met label `Bijlage:` | backend/integratie | `test_backend_07.py::test_bijlage_tekst_staat_in_prompt`, `test_bijlage_staat_aan_het_einde_van_prompt` |
| TD-07-13 | Bijlage wordt meegestuurd bij elke reviewstap | backend/integratie | `test_bugfix_reviewer_bijlage.py::test_reviewer_wordt_uitgevoerd_bij_aanvraag_met_bijlage` |
| TD-07-14 | Geen bijlage → geen `Bijlage:`-blok in de prompt | backend/integratie | `test_backend_07.py::test_zonder_bijlage_geen_bijlage_label_in_prompt` |
| TD-07-15 | Sessiebestand bevat `bijlage_bestandsnaam` (of `null`), correct bij laden | backend/integratie | `test_backend_07.py::test_sessie_opslaan_bevat_bijlage_bestandsnaam`, `test_sessie_opslaan_null_bijlage_bestandsnaam`, `test_sessie_laden_geeft_bijlage_bestandsnaam_terug`, `test_sessie_laden_null_bijlage_bestandsnaam` |
| TD-07-16 | Logbestand bevat `bijlage_bestandsnaam` en `bijlage_tekst` | backend/integratie | `test_backend_07.py::test_logbestand_bevat_bijlage_bestandsnaam`, `test_logbestand_bevat_bijlage_tekst`, `test_logbestand_bijlage_bestandsnaam_is_null_zonder_bijlage`, `test_logbestand_bijlage_tekst_is_null_zonder_bijlage` |
| TD-07-17 | Logbestandsnaam verandert niet door aanwezigheid van bijlage | backend/integratie | `test_backend_07.py::test_logbestandsnaam_verandert_niet_door_bijlage` |
| TD-07-18 | PDF/Word-extractiefout → 422 met melding | backend/integratie | `test_backend_07.py::test_pdf_extractiefout_geeft_422`, `test_pdf_extractiefout_foutmelding_vermeldt_reden`, `test_docx_extractiefout_geeft_422` |
| TD-07-19 | Leeg bestand → 400 met melding | backend/integratie | `test_backend_07.py::test_leeg_bestand_geeft_400`, `test_leeg_bestand_foutmelding` |
| TD-07-20 | Fout in bijlageverwerking → geen (leeg) logbestand | backend/integratie | `test_backend_07.py::test_extractiefout_maakt_geen_logbestand` |

---

## Story 08 — Review pipeline: iteratief verbeteren

Bron: `acceptatiecriteria/08-review-iteratief.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-08-01 | Reviewer toevoegen: knop aanwezig, toont invoervelden, meerdere reviewers mogelijk | playwright | `test_frontend_08.py::test_reviewer_toevoegen_knop_is_aanwezig`, `test_reviewer_toevoegen_toont_invoervelden`, `test_meerdere_reviewers_kunnen_worden_toegevoegd` |
| TD-08-02 | Reviewer heeft een rol-invoerveld | playwright | `test_frontend_08.py::test_reviewer_rol_invoerveld_is_aanwezig_na_toevoegen` |
| TD-08-03 | Reviewer heeft een omschrijving-invoerveld | playwright | `test_frontend_08.py::test_reviewer_omschrijving_invoerveld_is_aanwezig_na_toevoegen` |
| TD-08-04 | Reviewer heeft een 'aantal runs'-invoerveld | playwright | `test_frontend_08.py::test_reviewer_runs_invoerveld_is_aanwezig_na_toevoegen` |
| TD-08-05 | Reviewer heeft een temperatures-invoerveld | playwright | `test_frontend_08.py::test_reviewer_temperatures_invoerveld_is_aanwezig_na_toevoegen` |
| TD-08-06 | Reviewer verwijderen: knop zichtbaar, verwijdert item uit de lijst | playwright | `test_frontend_08.py::test_reviewer_verwijder_knop_is_zichtbaar`, `test_reviewer_verwijderen_verwijdert_item` |
| TD-08-07 | Gebruiker kan reviewers herordenen | playwright | ❌ **niet geïmplementeerd — geen test mogelijk.** Geen herordenknoppen of drag-and-drop in `static/app.js`/`index.html`. |
| TD-08-08 | Sessie opslaan stuurt `reviewers` (met rol + omschrijving) mee, lege lijst zonder reviewers | playwright | `test_frontend_08.py::test_sessie_opslaan_stuurt_reviewers_mee`, `test_sessie_opslaan_stuurt_omschrijving_mee`, `test_sessie_opslaan_zonder_reviewers_stuurt_lege_lijst` |
| TD-08-09 | Sessie opslaan stuurt `review_modus` mee | playwright | `test_frontend_08.py::test_sessie_opslaan_stuurt_review_modus_mee` |
| TD-08-10 | Sessie laden vult reviewer-items (rol, omschrijving) in, leeg zonder reviewers | playwright | `test_frontend_08.py::test_sessie_laden_vult_reviewers_in`, `test_sessie_laden_toont_reviewerrol`, `test_sessie_laden_toont_revieweromschrijving`, `test_sessie_laden_zonder_reviewers_toont_geen_reviewer_items` |
| TD-08-11 | Keuzemenu voor reviewmodus is aanwezig | playwright | `test_frontend_08.py::test_review_modus_selector_is_aanwezig` |
| TD-08-12 | Na uitvoering toont de UI de reviewer-stap | playwright | `test_frontend_08.py::test_uitvoer_toont_reviewer_stap` |
| TD-08-13 | Na uitvoering is de eindoutput zichtbaar | playwright | `test_frontend_08.py::test_uitvoer_toont_eindoutput` |
| TD-08-14 | Sessie zonder reviewers gedraagt zich ongewijzigd | backend/integratie | `test_backend_08.py::test_sessie_zonder_reviewers_geeft_200`, `test_sessie_zonder_reviewers_heeft_runs_in_resultaat` |
| TD-08-15 | Rol en omschrijving zijn verplicht per reviewer | backend/integratie | `test_backend_08.py::test_reviewer_zonder_omschrijving_geeft_422` |
| TD-08-16 | Reviewprompt bevat rol, reviewfocus-label en omschrijving | backend/integratie | `test_backend_08.py::test_reviewer_prompt_bevat_reviewer_rol`, `test_reviewer_prompt_bevat_reviewfocus_label`, `test_reviewer_prompt_bevat_omschrijving` |
| TD-08-17 | Reviewprompt bevat de instructie tot een verbeterde, complete versie | backend/integratie | `test_backend_08.py::test_reviewer_prompt_iteratief_bevat_verbetering_instructie` |
| TD-08-18 | Sectie 'Originele eisen:' bevat ingestelde optionele velden en bijlage | backend/integratie | `test_backend_08.py::test_reviewer_prompt_bevat_formaat_als_ingesteld`, `test_reviewer_prompt_bevat_stijl_als_ingesteld`, `test_reviewer_prompt_bevat_scope_als_ingesteld`, `test_reviewer_prompt_bevat_eisen_als_ingesteld`, `test_reviewer_prompt_bevat_voorbeelden_als_ingesteld`, `test_reviewer_prompt_bevat_bijlage_als_aanwezig` |
| TD-08-19 | Sectie 'Originele eisen:'/bijlage afwezig zonder optionele velden of bijlage | backend/integratie | `test_backend_08.py::test_reviewer_prompt_bevat_geen_originele_eisen_als_niets_ingesteld`, `test_reviewer_prompt_bevat_geen_bijlage_sectie_als_niet_aanwezig` |
| TD-08-20 | Hoofdprompt eerst uitgevoerd; reviewer 1 ontvangt de hoofdoutput | backend/integratie | `test_backend_08.py::test_reviewer_ontvangt_output_van_hoofdprompt` |
| TD-08-21 | Elke volgende run/reviewer ontvangt de output van de vorige stap | backend/integratie | `test_backend_08.py::test_reviewer1_run2_ontvangt_output_van_reviewer1_run1`, `test_reviewer2_ontvangt_output_van_laatste_reviewer1_run` |
| TD-08-22 | Volgorde: hoofdprompt → reviewer1 run1 → run2 → reviewer2 | backend/integratie | `test_backend_08.py::test_volgorde_is_hoofd_reviewer1_run1_run2_reviewer2` |
| TD-08-23 | Meerdere hoofdruns krijgen elk hun eigen volledige reviewketen | backend/integratie | `test_bugfix_reviewer_per_hoofdrun.py::test_elke_hoofdrun_krijgt_eigen_reviewketen` |
| TD-08-24 | Volgorde bij meerdere hoofdruns: hoofdrun1+keten1 volledig vóór hoofdrun2+keten2 | backend/integratie | `test_review_volgorde_hoofdruns.py::test_volgorde_is_per_hoofdrun_volledige_reviewketen_voor_volgende_hoofdrun` |
| TD-08-25 | Eindoutput is de output van de laatste stap | backend/integratie | `test_backend_08.py::test_eindoutput_is_output_van_laatste_stap` |
| TD-08-26 | Elke stap wordt apart gelogd | backend/integratie | `test_backend_08.py::test_twee_logbestanden_bij_een_reviewer`, `test_vier_logbestanden_bij_twee_reviewers` |
| TD-08-27 | Logbestand bevat rol + omschrijving; herkenbaar welke stap het betreft | backend/integratie | `test_backend_08.py::test_reviewerstap_log_bevat_reviewer_identificatie`, `test_reviewerstap_log_bevat_omschrijving`, `test_reviewerstap_log_heeft_reviewer_in_bestandsnaam` |
| TD-08-28 | Sessiebestand bevat `reviewers` (met omschrijving) en `review_modus`, correct bij laden | backend/integratie | `test_backend_08.py::test_sessie_opslaan_bevat_reviewers`, `test_sessie_opslaan_bevat_omschrijving_per_reviewer`, `test_sessie_opslaan_bevat_review_modus`, `test_sessie_laden_geeft_reviewers_terug`, `test_sessie_laden_geeft_omschrijving_terug`, `test_sessie_laden_geeft_review_modus_terug`, `test_bestaande_sessie_zonder_reviewers_laadt_zonder_fout` |

---

## Story 09 — Rate limiting: API-quota's respecteren

Bron: `acceptatiecriteria/09-rate-limiting.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-09-01 | 'Instellingen'-tab aanwezig en opent het instellingenpaneel | playwright | `test_frontend_09.py::test_instellingen_tab_is_aanwezig`, `test_instellingen_tab_opent_paneel` |
| TD-09-02 | Groq RPM-invoerveld is aanwezig | playwright | `test_frontend_09.py::test_groq_rpm_veld_is_aanwezig` |
| TD-09-03 | Google RPM-invoerveld is aanwezig | playwright | `test_frontend_09.py::test_google_rpm_veld_is_aanwezig` |
| TD-09-04 | Geen Ollama RPM-veld in de tab | playwright | `test_frontend_09.py::test_ollama_rpm_veld_is_niet_aanwezig` |
| TD-09-05 | RPM-velden tonen de waarde uit `GET /api/settings` | playwright | `test_frontend_09.py::test_groq_rpm_toont_geladen_waarde`, `test_google_rpm_toont_geladen_waarde` |
| TD-09-06 | Opslaan verstuurt `PUT /api/settings` met de ingevoerde RPM-waarden | playwright | `test_frontend_09.py::test_opslaan_verstuurt_put_naar_api_settings`, `test_opslaan_stuurt_groq_rpm_waarde_mee`, `test_opslaan_stuurt_google_rpm_waarde_mee` |
| TD-09-07 | RPM-limieten in `settings.json`, standaardwaarden Groq 30 / Google 15 | backend/integratie | `test_backend_09.py::test_get_settings_geeft_standaardwaarden_als_settings_ontbreekt`, `test_get_settings_geeft_opgeslagen_waarden_terug` |
| TD-09-08 | Wijzigingen teruggeschreven naar `settings.json`, direct van kracht | backend/integratie | `test_backend_09.py::test_put_settings_slaat_waarden_op_in_settings_json`, `test_get_settings_na_put_geeft_nieuwe_waarden_terug` |
| TD-09-09 | Vertraging = `60 / RPM` tussen requests, niet vóór het eerste request | backend/integratie | `test_backend_09.py::test_sleep_tussen_requests_op_basis_van_rpm`, `test_geen_delay_sleep_voor_eerste_request` |
| TD-09-10 | Geen vertraging bij Ollama | backend/integratie | `test_backend_09.py::test_geen_delay_sleep_bij_ollama` |
| TD-09-11 | RPM = 0 → geen vertraging | backend/integratie | `test_backend_09.py::test_geen_delay_sleep_als_rpm_nul_is` |
| TD-09-12 | 429 → wacht `Retry-After`, stuurt opnieuw | backend/integratie | `test_backend_09.py::test_429_met_retry_after_header_wacht_opgegeven_tijd` |
| TD-09-13 | Geen `Retry-After` → exponential backoff 5s/10s/20s | backend/integratie | `test_backend_09.py::test_429_zonder_retry_after_gebruikt_backoff` |
| TD-09-14 | Na 3 mislukte pogingen → fout met vaste melding | backend/integratie | `test_backend_09.py::test_na_drie_mislukte_pogingen_geeft_fout_terug`, `test_fout_na_max_retries_bevat_rate_limit_retries` |
| TD-09-15 | `rate_limit_retries`-veld bij retry, afwezig zonder retry | backend/integratie | `test_backend_09.py::test_succesvolle_retry_geeft_rate_limit_retries_terug`, `test_geen_rate_limit_retries_als_geen_retry_nodig` |
| TD-09-16 | Logbestand bevat `rate_limit_retries` en `retry_after_seconden` | backend/integratie | `test_backend_09.py::test_log_bevat_rate_limit_retries_na_succesvolle_retry`, `test_log_bevat_retry_after_seconden_als_header_aanwezig` |
| TD-09-17 | `PUT /api/settings` validatie: negatieve RPM → 422, RPM 0 toegestaan | backend/integratie | `test_backend_09.py::test_put_settings_met_negatieve_rpm_geeft_422`, `test_put_settings_rpm_nul_is_toegestaan` |

---

## Story 10 — Kopieerknop en formulieropmaak

Bron: `acceptatiecriteria/10-kopieerknop-en-opmaak.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-10-01 | Run-resultaat heeft een kopieerknop | playwright | `test_frontend_10.py::test_run_result_heeft_kopieerknop` |
| TD-10-02 | Reviewer-stap heeft een kopieerknop | playwright | `test_frontend_10.py::test_reviewer_stap_heeft_kopieerknop` |
| TD-10-03 | Eindoutput heeft een kopieerknop | playwright | `test_frontend_10.py::test_eindoutput_heeft_kopieerknop` |
| TD-10-04 | Klik op kopieerknop → 'Gekopieerd!' tijdelijk, terug na 2 seconden | playwright | `test_frontend_10.py::test_kopieerknop_tekst_verandert_naar_gekopieerd`, `test_kopieerknop_tekst_keert_terug_na_2_seconden` ⚠️ Bevestigt het knop-mechanisme; verifieert niet apart dat de gekopieerde tekst vrij is van markdown-opmaaktekens. |
| TD-10-05 | Klembord niet beschikbaar → knop toont 'Mislukt' | playwright | `test_frontend_10.py::test_kopieerknop_toont_mislukt_bij_geen_klembord_toegang` |
| TD-10-06 | `taak` is een textarea (2 rijen), accepteert newlines | playwright | `test_frontend_10.py::test_taak_is_textarea`, `test_taak_heeft_2_rijen`, `test_taak_accepteert_newlines` |
| TD-10-07 | `doel` is een textarea (2 rijen), accepteert newlines | playwright | `test_frontend_10.py::test_doel_is_textarea`, `test_doel_heeft_2_rijen`, `test_doel_accepteert_newlines` |
| TD-10-08 | `formaat` is een textarea (3 rijen), accepteert newlines | playwright | `test_frontend_10.py::test_formaat_is_textarea`, `test_formaat_heeft_3_rijen`, `test_formaat_accepteert_newlines` |
| TD-10-09 | `eisen`/`voorbeelden` blijven ongewijzigd textarea met 3 rijen | playwright | `test_frontend_10.py::test_eisen_blijft_textarea_met_3_rijen`, `test_voorbeelden_blijft_textarea_met_3_rijen` |
| TD-10-10 | Validatie op `rol`/`taak`/`doel` werkt ongewijzigd na omzetting naar textarea | playwright | `test_frontend_10.py::test_validatie_taak_werkt_na_omzetting_naar_textarea`, `test_validatie_doel_werkt_na_omzetting_naar_textarea`, `test_validatie_rol_werkt_ongewijzigd` |
| TD-10-11 | Newlines in sessie-JSON blijven ongewijzigd opgeslagen en worden hersteld bij laden | backend/integratie | `test_backend_10.py::test_newlines_in_taak_worden_opgeslagen`, `test_newlines_in_doel_worden_opgeslagen`, `test_newlines_in_formaat_worden_opgeslagen`, `test_newlines_worden_hersteld_bij_laden` |

---

## Story 11 — Groq-modelkeuze uitbreiden

Bron: `acceptatiecriteria/11-groq-modelkeuze.md`

| ID | Dekkingsitem | Categorie | Test |
|---|---|---|---|
| TD-11-01 | Modeldropdown zichtbaar bij Groq, niet bij Ollama, verdwijnt bij terugwisselen | playwright | `test_frontend_11.py::test_model_dropdown_zichtbaar_bij_groq`, `test_model_dropdown_niet_zichtbaar_bij_ollama`, `test_model_dropdown_verdwijnt_bij_terug_naar_ollama` |
| TD-11-02 | Dropdown bevat de vier nieuwe modellen | playwright | `test_frontend_11.py::test_dropdown_bevat_nieuw_model` |
| TD-11-03 | Dropdown bevat het model ingesteld via `GROQ_MODEL` | playwright | `test_frontend_11.py::test_dropdown_bevat_env_default_model` |
| TD-11-04 | Geen duplicaat als `GROQ_MODEL` overeenkomt met een nieuw model | playwright | `test_frontend_11.py::test_dropdown_geen_duplicaat_als_env_model_matcht_nieuw_model` |
| TD-11-05 | Dropdown staat bij laden standaard op de `GROQ_MODEL`-waarde | playwright | `test_frontend_11.py::test_dropdown_default_is_groq_model_env_waarde` |
| TD-11-06 | Geselecteerd model wordt meegestuurd bij een promptaanvraag | playwright | `test_frontend_11.py::test_geselecteerd_model_wordt_meegestuurd_bij_aanvraag` |
| TD-11-07 | Geselecteerd model wordt meegestuurd bij sessie opslaan (`groq_model`) | playwright | `test_frontend_11.py::test_geselecteerd_model_wordt_opgeslagen_in_sessie` |
| TD-11-08 | Bij laden sessie met Groq wordt het opgeslagen model geselecteerd | playwright | `test_frontend_11.py::test_sessie_laden_herstelt_groq_model` |
| TD-11-09 | Sessie zonder `groq_model` valt terug op de env-default | playwright | `test_frontend_11.py::test_sessie_zonder_groq_model_valt_terug_op_default` |
| TD-11-10 | Backend gebruikt het geselecteerde model i.p.v. altijd `GROQ_MODEL` | backend/integratie | `test_backend_11.py::test_geselecteerd_model_wordt_gebruikt_voor_groq_aanroep`, `test_backend_11_uitgaande_aanvraag.py::test_geselecteerd_model_zit_in_uitgaande_groq_aanvraag` |
| TD-11-11 | Geen model meegestuurd → valt terug op `GROQ_MODEL` | backend/integratie | `test_backend_11.py::test_geen_model_meegestuurd_valt_terug_op_groq_model`, `test_backend_11_uitgaande_aanvraag.py::test_geen_model_meegestuurd_gebruikt_groq_model_env_in_aanvraag` |
| TD-11-12 | Bij Ollama heeft modelkeuze geen effect | backend/integratie | `test_backend_11.py::test_model_veld_heeft_geen_effect_bij_ollama`, `test_backend_11_uitgaande_aanvraag.py::test_ollama_roept_groq_endpoint_niet_aan_ondanks_model_veld` |
| TD-11-13 | Elk nieuw model kan een aanvraag uitvoeren, endpoint blijft gelijk | backend/integratie | `test_backend_11.py::test_elk_nieuw_model_voert_aanvraag_uit`, `test_nieuwe_modelwaarden_worden_geaccepteerd`, `test_backend_11_uitgaande_aanvraag.py::test_groq_aanvraag_blijft_naar_dezelfde_endpoint_gaan` |
| TD-11-14 | Lege/onbekende modelwaarde → 400 | backend/integratie | `test_backend_11.py::test_lege_modelwaarde_geeft_400`, `test_onbekende_modelwaarde_geeft_400` |
| TD-11-15 | Logveld `model` bevat het daadwerkelijk gebruikte model | backend/integratie | `test_backend_11.py::test_log_model_veld_bevat_daadwerkelijk_gebruikte_model` |
| TD-11-16 | Logbestandsnaam bevat provider + model; ongeldige tekens vervangen | backend/integratie | `test_backend_11.py::test_logbestandsnaam_bevat_provider_en_model`, `test_ongeldige_tekens_in_modelnaam_vervangen_in_bestandsnaam` |
| TD-11-17 | `model_bevestigd_door_groq`-veld in het logbestand | backend/integratie | `test_backend_11_uitgaande_aanvraag.py::test_bevestigd_model_wordt_gelogd` |
| TD-11-18 | Mismatch aangevraagd/bevestigd model → waarschuwing; gelijk → geen; ontbrekend veld → geen mismatch | backend/integratie | `test_backend_11_uitgaande_aanvraag.py::test_mismatch_tussen_aangevraagd_en_bevestigd_model_geeft_waarschuwing`, `test_geen_mismatch_waarschuwing_bij_gelijk_model`, `test_ontbrekend_model_veld_in_respons_geeft_geen_waarschuwing` |
| TD-11-19 | Sessiebestand bevat `groq_model`; oude sessie zonder veld laadt nog correct | backend/integratie | `test_backend_11.py::test_sessie_opslaan_bevat_groq_model_veld`, `test_sessie_laden_geeft_groq_model_terug`, `test_oude_sessie_zonder_groq_model_laadt_nog_steeds` |

---

## Totaaloverzicht

| Story | Playwright-items | Backend/integratie-items | Waarvan niet-implementeerbaar |
|---|---|---|---|
| 01 | 1 | 0 | 0 |
| 02 | 9 | 2 | 0 |
| 03 | 11 | 3 | 0 |
| 04 | 2 | 13 | 0 |
| 05 | 7 | 10 | 0 |
| 06 | 22 | 8 | 0 |
| 07 | 7 | 13 | 0 |
| 08 | 13 | 15 | 1 (TD-08-07) |
| 09 | 6 | 11 | 0 |
| 10 | 10 | 1 | 0 |
| 11 | 9 | 10 | 0 |
| **Totaal** | **97** | **86** | **1** |
