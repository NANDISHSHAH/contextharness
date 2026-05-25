/**
 * Setup wizard webview - multi-step initialization
 */

let currentStep = 0;
const totalSteps = 6;

const prevBtn = document.getElementById('prev-btn') as HTMLButtonElement;
const nextBtn = document.getElementById('next-btn') as HTMLButtonElement;
const skipBtn = document.getElementById('skip-btn') as HTMLButtonElement;
const finishBtn = document.getElementById('finish-btn') as HTMLButtonElement;

function updateStep(step: number): void {
  currentStep = step;

  // Hide all steps
  const steps = document.querySelectorAll('.step');
  steps.forEach((el) => el.classList.add('hidden'));

  // Show current step
  const currentStepEl = document.getElementById(`step-${step}`);
  if (currentStepEl) {
    currentStepEl.classList.remove('hidden');
  }

  // Update buttons
  prevBtn.disabled = step === 0;
  nextBtn.style.display = step === totalSteps - 1 ? 'none' : 'block';
  finishBtn.style.display = step === totalSteps - 1 ? 'block' : 'none';

  // Send step change to extension
  (window as any).vscode.postMessage({
    type: 'wizardStep',
    step,
  });
}

prevBtn?.addEventListener('click', () => {
  if (currentStep > 0) {
    updateStep(currentStep - 1);
  }
});

nextBtn?.addEventListener('click', () => {
  if (currentStep < totalSteps - 1) {
    updateStep(currentStep + 1);
  }
});

skipBtn?.addEventListener('click', () => {
  (window as any).vscode.postMessage({
    type: 'wizardSkip',
  });
});

finishBtn?.addEventListener('click', () => {
  (window as any).vscode.postMessage({
    type: 'wizardFinish',
  });
});

window.addEventListener('message', (event) => {
  const message = event.data;

  switch (message.type) {
    case 'wizardProgress':
      const progressEl = document.getElementById('step-progress');
      if (progressEl) {
        progressEl.innerHTML = message.message || '';
      }
      break;
    case 'wizardStepUpdate':
      updateStep(message.step || 0);
      break;
    case 'wizardComplete':
      alert('Setup complete!');
      break;
  }
});

// Initialize to step 0
updateStep(0);
