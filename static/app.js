const button = document.getElementById('submit');
const loadingEl = document.querySelector('[data-testid="loading"]');
const responseEl = document.querySelector('[data-testid="response"]');
const errorEl = document.querySelector('[data-testid="error"]');

const VERPLICHTE_VELDEN = ['rol', 'taak', 'doel'];
const ALLE_VELDEN = ['rol', 'taak', 'doel', 'formaat', 'stijl', 'scope', 'eisen', 'voorbeelden'];

function hideAll() {
  loadingEl.classList.add('hidden');
  responseEl.classList.add('hidden');
  errorEl.classList.add('hidden');
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

button.addEventListener('click', async () => {
  hideAll();

  if (!valideer()) return;

  const body = {};
  for (const veld of ALLE_VELDEN) {
    body[veld] = document.querySelector(`[name="${veld}"]`).value.trim();
  }

  loadingEl.classList.remove('hidden');

  try {
    const res = await fetch('/api/prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    loadingEl.classList.add('hidden');

    if (!res.ok) {
      const data = await res.json();
      const detail = data.detail;
      errorEl.textContent = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map(e => e.msg || JSON.stringify(e)).join('; ')
          : 'Er is een fout opgetreden.';
      errorEl.classList.remove('hidden');
    } else {
      const data = await res.json();
      const response = data.response;
      responseEl.textContent = typeof response === 'string' ? response : JSON.stringify(response);
      responseEl.classList.remove('hidden');
    }
  } catch (err) {
    loadingEl.classList.add('hidden');
    errorEl.textContent = err.message || 'Netwerkfout — controleer de verbinding.';
    errorEl.classList.remove('hidden');
  }
});
