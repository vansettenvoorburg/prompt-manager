const textarea = document.getElementById('prompt');
const button = document.getElementById('submit');
const validationEl = document.querySelector('[data-testid="validation-message"]');
const loadingEl = document.querySelector('[data-testid="loading"]');
const responseEl = document.querySelector('[data-testid="response"]');
const errorEl = document.querySelector('[data-testid="error"]');

function hideAll() {
  validationEl.classList.add('hidden');
  loadingEl.classList.add('hidden');
  responseEl.classList.add('hidden');
  errorEl.classList.add('hidden');
}

button.addEventListener('click', async () => {
  const prompt = textarea.value.trim();

  hideAll();

  if (!prompt) {
    validationEl.classList.remove('hidden');
    return;
  }

  loadingEl.classList.remove('hidden');

  try {
    const res = await fetch('/api/prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });

    loadingEl.classList.add('hidden');

    if (!res.ok) {
      const data = await res.json();
      errorEl.textContent = data.detail || 'Er is een fout opgetreden.';
      errorEl.classList.remove('hidden');
    } else {
      const data = await res.json();
      responseEl.textContent = data.response;
      responseEl.classList.remove('hidden');
    }
  } catch (err) {
    loadingEl.classList.add('hidden');
    errorEl.textContent = err.message || 'Netwerkfout — controleer de verbinding.';
    errorEl.classList.remove('hidden');
  }
});
