const button = document.getElementById('submit');
const loadingEl = document.querySelector('[data-testid="loading"]');
const responseEl = document.querySelector('[data-testid="response"]');
const errorEl = document.querySelector('[data-testid="error"]');
const logStatusEl = document.querySelector('[data-testid="log-status"]');
const logWarningEl = document.querySelector('[data-testid="log-warning"]');
const runResultsEl = document.querySelector('[data-testid="run-results"]');
const reviewerStappenListEl = document.querySelector('[data-testid="reviewer-stappen-lijst"]');
const eindoutputEl = document.querySelector('[data-testid="eindoutput"]');
const reviewerToevoegenKnop = document.getElementById('reviewer-toevoegen');
const reviewerLijstEl = document.getElementById('reviewer-lijst');
const reviewModusSelectEl = document.querySelector('[data-testid="review-modus-select"]');

const bijlageInputEl = document.getElementById('bijlage-input');
const bijlageStatusEl = document.getElementById('bijlage-status');
const bijlageVerwijderEl = document.getElementById('bijlage-verwijder');

const opslaanKnop = document.getElementById('opslaan-knop');
const sessieNaamInput = document.querySelector('[name="session-name"]');
const bevestigingEl = document.querySelector('[data-testid="save-confirmation"]');
const opslaanFoutEl = document.querySelector('[data-testid="save-error"]');
const validatieSessienaamEl = document.querySelector('[data-testid="validation-session-name"]');
const overschrijfDialogEl = document.querySelector('[data-testid="overwrite-dialog"]');
const sessiesListEl = document.querySelector('[data-testid="sessions-list"]');
const sessiesLeegEl = document.querySelector('[data-testid="sessions-empty"]');
const laadFoutEl = document.querySelector('[data-testid="load-error"]');
const providerSelectEl = document.querySelector('[data-testid="provider-select"]');
const sessionSelectEl = document.querySelector('[data-testid="session-select"]');
const runsInputEl = document.querySelector('[data-testid="runs-input"]');
const temperatureInputEl = document.querySelector('[data-testid="temperature-input"]');

const PROVIDER_DEFAULTS = { ollama: '0.8', groq: '1' };
let temperatureHandmatigGewijzigd = false;

const sessieCache = {};

function parseerFoutmelding(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(e => e.msg || JSON.stringify(e)).join('; ');
  return 'Er is een fout opgetreden.';
}

const VERPLICHTE_VELDEN = ['rol', 'taak', 'doel'];
const ALLE_VELDEN = ['rol', 'taak', 'doel', 'formaat', 'stijl', 'scope', 'eisen', 'voorbeelden'];

function hideAll() {
  loadingEl.classList.add('hidden');
  responseEl.classList.add('hidden');
  errorEl.classList.add('hidden');
  logStatusEl.classList.add('hidden');
  logWarningEl.classList.add('hidden');
  runResultsEl.classList.add('hidden');
  reviewerStappenListEl.classList.add('hidden');
  eindoutputEl.classList.add('hidden');
}

function maakReviewerItem() {
  const item = document.createElement('div');
  item.setAttribute('data-testid', 'reviewer-item');
  item.classList.add('reviewer-item');

  const rolInput = document.createElement('input');
  rolInput.type = 'text';
  rolInput.setAttribute('data-testid', 'reviewer-rol');
  rolInput.placeholder = 'Reviewerrol (bijv. kritische QA engineer)';

  const omschrijvingInput = document.createElement('textarea');
  omschrijvingInput.setAttribute('data-testid', 'reviewer-omschrijving');
  omschrijvingInput.placeholder = 'Wat moet de reviewer controleren of verbeteren?';
  omschrijvingInput.rows = 2;

  const runsInput = document.createElement('input');
  runsInput.type = 'number';
  runsInput.setAttribute('data-testid', 'reviewer-runs');
  runsInput.value = '1';
  runsInput.min = '1';

  const tempInput = document.createElement('input');
  tempInput.type = 'text';
  tempInput.setAttribute('data-testid', 'reviewer-temperatures');
  tempInput.placeholder = 'Temperatures (bijv. 0.7)';
  tempInput.value = '0.7';

  const verwijderKnop = document.createElement('button');
  verwijderKnop.type = 'button';
  verwijderKnop.setAttribute('data-testid', 'reviewer-verwijder');
  verwijderKnop.textContent = 'Verwijder';
  verwijderKnop.addEventListener('click', () => item.remove());

  item.appendChild(rolInput);
  item.appendChild(omschrijvingInput);
  item.appendChild(runsInput);
  item.appendChild(tempInput);
  item.appendChild(verwijderKnop);
  return item;
}

function _leesReviewers() {
  return Array.from(reviewerLijstEl.querySelectorAll('[data-testid="reviewer-item"]')).map(item => {
    const rol = item.querySelector('[data-testid="reviewer-rol"]').value.trim();
    const omschrijving = item.querySelector('[data-testid="reviewer-omschrijving"]').value.trim();
    const runs = parseInt(item.querySelector('[data-testid="reviewer-runs"]').value, 10) || 1;
    const tempWaarde = item.querySelector('[data-testid="reviewer-temperatures"]').value.trim();
    const temperatures = tempWaarde
      ? tempWaarde.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n))
      : [0.7];
    return { rol, omschrijving, runs, temperatures };
  });
}

function renderReviewerStappen(stappen) {
  reviewerStappenListEl.innerHTML = '';
  for (const stap of stappen) {
    const item = document.createElement('div');
    item.setAttribute('data-testid', 'reviewer-stap-item');
    item.classList.add('reviewer-stap');
    if (stap.fout) {
      item.textContent = `Reviewer ${stap.reviewer_nr} run ${stap.run_nummer}: Fout — ${stap.fout}`;
    } else {
      const header = document.createElement('div');
      header.classList.add('run-header');
      header.textContent = `Reviewer ${stap.reviewer_nr} (${stap.reviewer_rol}) — run ${stap.run_nummer} — temperature ${stap.temperature}`;
      const body = document.createElement('div');
      body.classList.add('run-body');
      body.innerHTML = marked.parse(stap.response || '');
      item.appendChild(header);
      item.appendChild(body);
    }
    reviewerStappenListEl.appendChild(item);
  }
  reviewerStappenListEl.classList.remove('hidden');
}

function _getModus() {
  const checked = document.querySelector('[name="temperature-modus"]:checked');
  return checked ? checked.value : 'alle';
}

function _parseTemperatures(tempWaarde, modus) {
  if (modus === 'per_run') {
    return tempWaarde.split(',').map(s => parseFloat(s.trim()));
  }
  return [parseFloat(tempWaarde)];
}

function valideer() {
  let geldig = true;
  for (const veld of VERPLICHTE_VELDEN) {
    const input = document.querySelector(`[name="${veld}"]`);
    const melding = document.querySelector(`[data-testid="validation-${veld}"]`);
    if (!input.value.trim()) {
      melding.classList.remove('hidden');
      geldig = false;
    } else {
      melding.classList.add('hidden');
    }
  }
  if (!geldig) return false;

  const runs = parseInt(runsInputEl.value, 10);
  if (!runs || runs < 1) {
    errorEl.textContent = 'Aantal runs moet minimaal 1 zijn.';
    errorEl.classList.remove('hidden');
    return false;
  }

  const tempWaarde = temperatureInputEl.value.trim();
  if (!tempWaarde) {
    errorEl.textContent = 'Verplicht — voer een temperature in om de prompt uit te voeren.';
    errorEl.classList.remove('hidden');
    return false;
  }

  const modus = _getModus();
  const temperatures = _parseTemperatures(tempWaarde, modus);

  for (const t of temperatures) {
    if (isNaN(t) || t < 0.0 || t > 2.0) {
      errorEl.textContent = 'Temperature moet tussen 0 en 2 liggen.';
      errorEl.classList.remove('hidden');
      return false;
    }
  }

  if (modus === 'per_run' && temperatures.length !== runs) {
    errorEl.textContent = `Vul ${runs} temperatures in, of kies 'één voor alle runs'.`;
    errorEl.classList.remove('hidden');
    return false;
  }

  return true;
}

function renderRunResultaten(runs) {
  runResultsEl.innerHTML = '';
  logStatusEl.classList.add('hidden');
  logWarningEl.classList.add('hidden');
  for (const run of runs) {
    const item = document.createElement('div');
    item.classList.add('run-result');
    if (run.fout) {
      item.classList.add('run-fout');
      item.textContent = `Run ${run.run_nummer}: Fout — ${run.fout}`;
    } else {
      const header = document.createElement('div');
      header.classList.add('run-header');
      header.textContent = `Run ${run.run_nummer} — temperature ${run.temperature}`;
      if (run.log_status === 'ok') {
        const logNote = document.createElement('span');
        logNote.classList.add('run-log-note');
        logNote.textContent = ` · Log opgeslagen: ${run.log_path}`;
        header.appendChild(logNote);
      }
      if (run.log_warning) {
        const warnNote = document.createElement('span');
        warnNote.classList.add('run-log-warning');
        warnNote.textContent = ` · Waarschuwing: ${run.log_warning}`;
        header.appendChild(warnNote);
      }
      const body = document.createElement('div');
      body.classList.add('run-body');
      body.innerHTML = marked.parse(run.response || '');
      item.appendChild(header);
      item.appendChild(body);
    }
    runResultsEl.appendChild(item);
  }
  runResultsEl.classList.remove('hidden');
}

function renderSessiesLijst(sessions) {
  sessiesListEl.querySelectorAll('[data-testid="session-item"]').forEach(el => el.remove());
  while (sessionSelectEl.options.length > 1) {
    sessionSelectEl.remove(1);
  }
  if (sessions.length === 0) {
    sessiesLeegEl.classList.remove('hidden');
  } else {
    sessiesLeegEl.classList.add('hidden');
    for (const naam of sessions) {
      const item = document.createElement('button');
      item.setAttribute('type', 'button');
      item.setAttribute('data-testid', 'session-item');
      item.textContent = naam;
      item.addEventListener('click', () => laadSessie(naam));
      sessiesListEl.appendChild(item);

      const optie = document.createElement('option');
      optie.value = naam;
      optie.textContent = naam;
      sessionSelectEl.appendChild(optie);
    }
  }
}

function _pasSessieToe(data) {
  for (const veld of ALLE_VELDEN) {
    const input = document.querySelector(`[name="${veld}"]`);
    if (input) input.value = data[veld] || '';
  }
  if (data.provider && providerSelectEl) {
    providerSelectEl.value = data.provider;
  }
  if (data.runs !== undefined) {
    runsInputEl.value = String(data.runs);
  }
  if (data.temperature_modus) {
    const radio = document.querySelector(`[name="temperature-modus"][value="${data.temperature_modus}"]`);
    if (radio) radio.checked = true;
  }
  if (data.temperatures && data.temperatures.length > 0) {
    temperatureInputEl.value = data.temperatures.join(', ');
    temperatureHandmatigGewijzigd = true;
  }
  if (data.bijlage_bestandsnaam) {
    bijlageStatusEl.textContent = `${data.bijlage_bestandsnaam} (niet opnieuw geladen — upload indien nodig opnieuw)`;
    bijlageVerwijderEl.style.display = '';
  } else if ('bijlage_bestandsnaam' in data) {
    bijlageStatusEl.textContent = 'Geen bijlage';
    bijlageVerwijderEl.style.display = 'none';
    bijlageInputEl.value = '';
  }

  reviewerLijstEl.innerHTML = '';
  const reviewers = data.reviewers || [];
  for (const r of reviewers) {
    const item = maakReviewerItem();
    item.querySelector('[data-testid="reviewer-rol"]').value = r.rol || '';
    item.querySelector('[data-testid="reviewer-omschrijving"]').value = r.omschrijving || '';
    item.querySelector('[data-testid="reviewer-runs"]').value = String(r.runs || 1);
    item.querySelector('[data-testid="reviewer-temperatures"]').value = (r.temperatures || []).join(', ');
    reviewerLijstEl.appendChild(item);
  }
  if (data.review_modus && reviewModusSelectEl) {
    reviewModusSelectEl.value = data.review_modus;
  }
}

async function laadSessiesLijst() {
  try {
    const res = await fetch('/api/sessions');
    if (!res.ok) return;
    const data = await res.json();
    const sessions = data.sessions || [];
    await Promise.all(sessions.map(async naam => {
      try {
        const r = await fetch(`/api/sessions/${encodeURIComponent(naam)}`);
        if (r.ok) sessieCache[naam] = await r.json();
      } catch (_) {}
    }));
    renderSessiesLijst(sessions);
  } catch (_) {}
}

async function laadSessie(naam) {
  laadFoutEl.classList.add('hidden');
  sessieNaamInput.value = naam;
  if (sessieCache[naam]) {
    _pasSessieToe(sessieCache[naam]);
    return;
  }
  try {
    const res = await fetch(`/api/sessions/${encodeURIComponent(naam)}`);
    if (!res.ok) {
      laadFoutEl.textContent = 'Laden mislukt.';
      laadFoutEl.classList.remove('hidden');
      return;
    }
    const data = await res.json();
    sessieCache[naam] = data;
    _pasSessieToe(data);
  } catch (err) {
    laadFoutEl.textContent = err.message || 'Laden mislukt.';
    laadFoutEl.classList.remove('hidden');
  }
}

async function slaOp(force = false) {
  const naam = sessieNaamInput.value.trim();
  validatieSessienaamEl.classList.add('hidden');
  bevestigingEl.classList.add('hidden');
  opslaanFoutEl.classList.add('hidden');

  if (!naam) {
    validatieSessienaamEl.classList.remove('hidden');
    return;
  }

  const runs = parseInt(runsInputEl.value, 10) || 1;
  const modus = _getModus();
  const tempWaarde = temperatureInputEl.value.trim();
  const temperaturesArray = tempWaarde
    ? _parseTemperatures(tempWaarde, modus).filter(n => !isNaN(n))
    : [];

  const body = { name: naam, force };
  body.provider = providerSelectEl ? providerSelectEl.value : 'ollama';
  for (const veld of ALLE_VELDEN) {
    body[veld] = document.querySelector(`[name="${veld}"]`).value.trim();
  }
  body.runs = runs;
  body.temperature_modus = modus;
  body.temperatures = temperaturesArray;
  body.bijlage_bestandsnaam = bijlageInputEl.files.length > 0 ? bijlageInputEl.files[0].name : null;
  body.reviewers = _leesReviewers();
  body.review_modus = reviewModusSelectEl ? reviewModusSelectEl.value : 'iteratief';

  try {
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (res.status === 409) {
      overschrijfDialogEl.classList.remove('hidden');
      return;
    }

    if (!res.ok) {
      opslaanFoutEl.textContent = 'Opslaan mislukt.';
      opslaanFoutEl.classList.remove('hidden');
      return;
    }

    overschrijfDialogEl.classList.add('hidden');
    bevestigingEl.textContent = `Sessie "${naam}" is opgeslagen.`;
    bevestigingEl.classList.remove('hidden');
    laadSessiesLijst();
  } catch (err) {
    opslaanFoutEl.textContent = err.message || 'Opslaan mislukt.';
    opslaanFoutEl.classList.remove('hidden');
  }
}

reviewerToevoegenKnop.addEventListener('click', () => {
  reviewerLijstEl.appendChild(maakReviewerItem());
});

providerSelectEl.addEventListener('change', () => {
  if (!temperatureHandmatigGewijzigd) {
    temperatureInputEl.value = PROVIDER_DEFAULTS[providerSelectEl.value] || '0.8';
  }
});

temperatureInputEl.addEventListener('input', () => {
  temperatureHandmatigGewijzigd = true;
});

opslaanKnop.addEventListener('click', () => slaOp(false));
document.getElementById('bevestig-overschrijven').addEventListener('click', () => slaOp(true));
document.getElementById('annuleer-overschrijven').addEventListener('click', () => {
  overschrijfDialogEl.classList.add('hidden');
});

sessionSelectEl.addEventListener('change', () => {
  const naam = sessionSelectEl.value;
  if (naam) laadSessie(naam);
});

bijlageInputEl.addEventListener('change', () => {
  if (bijlageInputEl.files.length > 0) {
    bijlageStatusEl.textContent = bijlageInputEl.files[0].name;
    bijlageVerwijderEl.style.display = '';
  } else {
    bijlageStatusEl.textContent = 'Geen bijlage';
    bijlageVerwijderEl.style.display = 'none';
  }
});

bijlageVerwijderEl.addEventListener('click', () => {
  bijlageInputEl.value = '';
  bijlageStatusEl.textContent = 'Geen bijlage';
  bijlageVerwijderEl.style.display = 'none';
});

const tabPromptEl = document.querySelector('[data-testid="tab-prompt"]');
const tabInstellingenEl = document.querySelector('[data-testid="tab-instellingen"]');
const promptPaneelEl = document.querySelector('[data-testid="prompt-paneel"]');
const instellingenPaneelEl = document.querySelector('[data-testid="instellingen-paneel"]');
const groqRpmInputEl = document.querySelector('[data-testid="groq-rpm-input"]');
const googleRpmInputEl = document.querySelector('[data-testid="google-rpm-input"]');
const instellingenOpslaanEl = document.getElementById('instellingen-opslaan');
const instellingenBevestigingEl = document.querySelector('[data-testid="instellingen-bevestiging"]');
const instellingenFoutEl = document.querySelector('[data-testid="instellingen-fout"]');

async function laadInstellingen() {
  try {
    const res = await fetch('/api/settings');
    if (!res.ok) return;
    const data = await res.json();
    groqRpmInputEl.value = data.groq_rpm;
    googleRpmInputEl.value = data.google_rpm;
  } catch (_) {}
}

async function slaInstellingenOp() {
  instellingenBevestigingEl.classList.add('hidden');
  instellingenFoutEl.classList.add('hidden');
  const groqRpm = parseInt(groqRpmInputEl.value, 10);
  const googleRpm = parseInt(googleRpmInputEl.value, 10);
  try {
    const res = await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ groq_rpm: groqRpm, google_rpm: googleRpm }),
    });
    if (res.ok) {
      instellingenBevestigingEl.textContent = 'Instellingen opgeslagen.';
      instellingenBevestigingEl.classList.remove('hidden');
    } else {
      instellingenFoutEl.textContent = 'Opslaan mislukt.';
      instellingenFoutEl.classList.remove('hidden');
    }
  } catch (err) {
    instellingenFoutEl.textContent = err.message || 'Opslaan mislukt.';
    instellingenFoutEl.classList.remove('hidden');
  }
}

tabPromptEl.addEventListener('click', () => {
  promptPaneelEl.classList.remove('hidden');
  instellingenPaneelEl.classList.add('hidden');
  tabPromptEl.classList.add('tab-actief');
  tabInstellingenEl.classList.remove('tab-actief');
});

tabInstellingenEl.addEventListener('click', () => {
  promptPaneelEl.classList.add('hidden');
  instellingenPaneelEl.classList.remove('hidden');
  tabInstellingenEl.classList.add('tab-actief');
  tabPromptEl.classList.remove('tab-actief');
});

instellingenOpslaanEl.addEventListener('click', slaInstellingenOp);

laadSessiesLijst();
laadInstellingen();

button.addEventListener('click', async () => {
  hideAll();

  if (!valideer()) return;

  const runs = parseInt(runsInputEl.value, 10);
  const modus = _getModus();
  const tempWaarde = temperatureInputEl.value.trim();
  const temperaturesArray = _parseTemperatures(tempWaarde, modus);

  const veldWaarden = {};
  veldWaarden.provider = providerSelectEl ? providerSelectEl.value : 'ollama';
  for (const veld of ALLE_VELDEN) {
    veldWaarden[veld] = document.querySelector(`[name="${veld}"]`).value.trim();
  }
  veldWaarden.sessie = sessieNaamInput.value.trim();
  veldWaarden.runs = runs;
  veldWaarden.temperature_modus = modus;
  veldWaarden.temperatures = temperaturesArray;
  veldWaarden.reviewers = _leesReviewers();
  veldWaarden.review_modus = reviewModusSelectEl ? reviewModusSelectEl.value : 'iteratief';

  const heeftBijlage = bijlageInputEl.files.length > 0;
  let fetchOpties;
  let promptUrl;
  if (heeftBijlage) {
    const fd = new FormData();
    for (const [k, v] of Object.entries(veldWaarden)) {
      fd.append(k, Array.isArray(v) ? JSON.stringify(v) : String(v));
    }
    fd.append('bijlage', bijlageInputEl.files[0]);
    fetchOpties = { method: 'POST', body: fd };
    promptUrl = '/api/prompt/upload';
  } else {
    fetchOpties = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(veldWaarden),
    };
    promptUrl = '/api/prompt';
  }

  loadingEl.classList.remove('hidden');

  try {
    const response = await fetch(promptUrl, fetchOpties);

    loadingEl.classList.add('hidden');

    const data = await response.json();
    if (response.ok) {
      renderRunResultaten(data.runs);
      if (data.reviewer_stappen && data.reviewer_stappen.length > 0) {
        renderReviewerStappen(data.reviewer_stappen);
      }
      if (data.eindoutput !== undefined) {
        eindoutputEl.innerHTML = marked.parse(data.eindoutput || '');
        eindoutputEl.classList.remove('hidden');
      }
    } else {
      errorEl.textContent = parseerFoutmelding(data.detail);
      errorEl.classList.remove('hidden');
    }
  } catch (err) {
    loadingEl.classList.add('hidden');
    errorEl.textContent = err.message || 'Netwerkfout — controleer de verbinding.';
    errorEl.classList.remove('hidden');
  }
});
