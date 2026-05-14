const button = document.getElementById('submit');
const loadingEl = document.querySelector('[data-testid="loading"]');
const responseEl = document.querySelector('[data-testid="response"]');
const errorEl = document.querySelector('[data-testid="error"]');
const logStatusEl = document.querySelector('[data-testid="log-status"]');
const logWarningEl = document.querySelector('[data-testid="log-warning"]');

const opslaanKnop = document.getElementById('opslaan-knop');
const sessieNaamInput = document.querySelector('[name="session-name"]');
const bevestigingEl = document.querySelector('[data-testid="save-confirmation"]');
const opslaanFoutEl = document.querySelector('[data-testid="save-error"]');
const validatieSessienaamEl = document.querySelector('[data-testid="validation-session-name"]');
const overschrijfDialogEl = document.querySelector('[data-testid="overwrite-dialog"]');
const sessiesListEl = document.querySelector('[data-testid="sessions-list"]');
const sessiesLeegEl = document.querySelector('[data-testid="sessions-empty"]');
const laadFoutEl = document.querySelector('[data-testid="load-error"]');

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
  return geldig;
}

function renderSessiesLijst(sessions) {
  sessiesListEl.querySelectorAll('[data-testid="session-item"]').forEach(el => el.remove());
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
    }
  }
}

async function laadSessiesLijst() {
  try {
    const res = await fetch('/api/sessions');
    if (!res.ok) return;
    const data = await res.json();
    renderSessiesLijst(data.sessions || []);
  } catch (_) {
    // Bewust stil: de sessieslijst is niet-kritisch bij het laden van de pagina.
  }
}

async function laadSessie(naam) {
  laadFoutEl.classList.add('hidden');
  try {
    const res = await fetch(`/api/sessions/${encodeURIComponent(naam)}`);
    if (!res.ok) {
      laadFoutEl.textContent = 'Laden mislukt.';
      laadFoutEl.classList.remove('hidden');
      return;
    }
    const data = await res.json();
    for (const veld of ALLE_VELDEN) {
      const input = document.querySelector(`[name="${veld}"]`);
      if (input) input.value = data[veld] || '';
    }
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

  const body = { name: naam, force };
  for (const veld of ALLE_VELDEN) {
    body[veld] = document.querySelector(`[name="${veld}"]`).value.trim();
  }

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

opslaanKnop.addEventListener('click', () => slaOp(false));
document.getElementById('bevestig-overschrijven').addEventListener('click', () => slaOp(true));
document.getElementById('annuleer-overschrijven').addEventListener('click', () => {
  overschrijfDialogEl.classList.add('hidden');
});

laadSessiesLijst();

button.addEventListener('click', async () => {
  hideAll();

  if (!valideer()) return;

  const body = {};
  for (const veld of ALLE_VELDEN) {
    body[veld] = document.querySelector(`[name="${veld}"]`).value.trim();
  }
  body.sessie = sessieNaamInput.value.trim();

  loadingEl.classList.remove('hidden');

  try {
    const res = await fetch('/api/prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const data = await res.json();
      errorEl.textContent = parseerFoutmelding(data.detail);
      errorEl.classList.remove('hidden');
    } else {
      const data = await res.json();
      const response = data.response;
      responseEl.textContent = typeof response === 'string' ? response : JSON.stringify(response);
      responseEl.classList.remove('hidden');
      if (data.log_warning) {
        logWarningEl.textContent = data.log_warning;
        logWarningEl.classList.remove('hidden');
      } else if (data.log_status === 'ok') {
        logStatusEl.textContent = 'Log opgeslagen';
        logStatusEl.classList.remove('hidden');
      }
    }
  } catch (err) {
    errorEl.textContent = err.message || 'Netwerkfout — controleer de verbinding.';
    errorEl.classList.remove('hidden');
  } finally {
    loadingEl.classList.add('hidden');
  }
});
