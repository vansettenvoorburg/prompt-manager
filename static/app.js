const button = document.getElementById('submit');
const loadingEl = document.querySelector('[data-testid="loading"]');
const responseEl = document.querySelector('[data-testid="response"]');
const errorEl = document.querySelector('[data-testid="error"]');
const logStatusEl = document.querySelector('[data-testid="log-status"]');
const logWarningEl = document.querySelector('[data-testid="log-warning"]');
const runResultsEl = document.querySelector('[data-testid="run-results"]');

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
        logNote.textContent = ` · Log: ${run.log_path}`;
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

laadSessiesLijst();

button.addEventListener('click', async () => {
  hideAll();

  if (!valideer()) return;

  const runs = parseInt(runsInputEl.value, 10);
  const modus = _getModus();
  const tempWaarde = temperatureInputEl.value.trim();
  const temperaturesArray = _parseTemperatures(tempWaarde, modus);

  const body = {};
  body.provider = providerSelectEl ? providerSelectEl.value : 'ollama';
  for (const veld of ALLE_VELDEN) {
    body[veld] = document.querySelector(`[name="${veld}"]`).value.trim();
  }
  body.sessie = sessieNaamInput.value.trim();
  body.runs = runs;
  body.temperature_modus = modus;
  body.temperatures = temperaturesArray;

  loadingEl.classList.remove('hidden');

  try {
    const response = await fetch('/api/prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    loadingEl.classList.add('hidden');

    const data = await response.json();
    if (response.ok) {
      renderRunResultaten(data.runs);
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
