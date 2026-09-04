## Story: Eigen eindoutput per hoofdrun

**Als** gebruiker die een sessie met meerdere hoofdruns én één of meerdere reviewers uitvoert
**wil ik** per hoofdrun een eigen eindoutput te zien krijgen
**zodat** ik het eindresultaat van elke hoofdrun kan beoordelen, in plaats van alleen dat van de
laatste hoofdrun

### Aanleiding

Bij meerdere hoofdruns krijgt elke hoofdrun al zijn eigen, volledige reviewketen (REVIEW-I-02).
De backend berekent momenteel echter maar één `eindoutput`-waarde: die wordt in de loop over de
hoofdruns bij elke hoofdrun overschreven, waardoor alleen het eindresultaat van de láátste
hoofdrun overblijft. De UI toont ook maar één gedeeld eindoutput-blok. Voor de gebruiker ziet dit
eruit als een samenvoeging van de verschillende hoofdruns tot één resultaat, terwijl elke hoofdrun
juist zijn eigen, onderscheiden eindresultaat heeft.

### Acceptatiecriteria
Acceptatiecriteria: zie `documentatie/acceptatiecriteria/review-pipeline.md`
(codes REVIEW-W-04, REVIEW-W-05, REVIEW-W-06, REVIEW-I-05, REVIEW-V-03; REVIEW-I-04 is
hergebruikt/aangevuld voor het geval zonder reviewers).

### Buiten scope
- Het reviewmodus-gedrag zelf (bv. "iteratief") wijzigt niet — alleen de koppeling en weergave
  van het eindresultaat per hoofdrun.
- Het aantal/tellen van reviewer-stappen per hoofdrun (al opgelost, zie
  `test_bugfix_reviewer_per_hoofdrun.py`).
- HTML/script-tag-escaping in eindoutput: al gedekt door bestaande AC RESULTAAT-V-04, ongeacht
  aantal eindoutput-blokken.
