/**
 * Harvest context webview
 */

const queryInput = document.getElementById('query-input') as HTMLInputElement;
const branchInput = document.getElementById('branch-input') as HTMLInputElement;
const submitBtn = document.getElementById('submit-btn') as HTMLButtonElement;
const outputDiv = document.getElementById('output') as HTMLDivElement;
const copyBtn = document.getElementById('copy-btn') as HTMLButtonElement;
const openEditorBtn = document.getElementById('open-editor-btn') as HTMLButtonElement;

submitBtn?.addEventListener('click', () => {
  const query = queryInput?.value || '';
  const branch = branchInput?.value || '';

  if (!query) {
    alert('Please enter a query');
    return;
  }

  submitBtn!.disabled = true;
  submitBtn!.textContent = 'Loading...';

  (window as any).vscode.postMessage({
    type: 'harvest',
    query,
    branch,
  });
});

copyBtn?.addEventListener('click', () => {
  const text = outputDiv?.innerText || '';
  navigator.clipboard.writeText(text).then(() => {
    alert('Copied to clipboard');
  });
});

openEditorBtn?.addEventListener('click', () => {
  const text = outputDiv?.innerText || '';
  (window as any).vscode.postMessage({
    type: 'openInEditor',
    content: text,
  });
});

window.addEventListener('message', (event) => {
  const message = event.data;

  switch (message.type) {
    case 'harvestResult':
      outputDiv!.innerHTML = message.content || 'No results';
      submitBtn!.disabled = false;
      submitBtn!.textContent = 'Harvest';
      break;
    case 'harvestError':
      outputDiv!.innerHTML = `<p style="color: red;">Error: ${message.error}</p>`;
      submitBtn!.disabled = false;
      submitBtn!.textContent = 'Harvest';
      break;
  }
});

// Focus on load
queryInput?.focus();
