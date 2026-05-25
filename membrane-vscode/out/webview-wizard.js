"use strict";
(() => {
  // webview-src/wizard/wizard.ts
  var currentStep = 0;
  var totalSteps = 6;
  var prevBtn = document.getElementById("prev-btn");
  var nextBtn = document.getElementById("next-btn");
  var skipBtn = document.getElementById("skip-btn");
  var finishBtn = document.getElementById("finish-btn");
  function updateStep(step) {
    currentStep = step;
    const steps = document.querySelectorAll(".step");
    steps.forEach((el) => el.classList.add("hidden"));
    const currentStepEl = document.getElementById(`step-${step}`);
    if (currentStepEl) {
      currentStepEl.classList.remove("hidden");
    }
    prevBtn.disabled = step === 0;
    nextBtn.style.display = step === totalSteps - 1 ? "none" : "block";
    finishBtn.style.display = step === totalSteps - 1 ? "block" : "none";
    window.vscode.postMessage({
      type: "wizardStep",
      step
    });
  }
  prevBtn?.addEventListener("click", () => {
    if (currentStep > 0) {
      updateStep(currentStep - 1);
    }
  });
  nextBtn?.addEventListener("click", () => {
    if (currentStep < totalSteps - 1) {
      updateStep(currentStep + 1);
    }
  });
  skipBtn?.addEventListener("click", () => {
    window.vscode.postMessage({
      type: "wizardSkip"
    });
  });
  finishBtn?.addEventListener("click", () => {
    window.vscode.postMessage({
      type: "wizardFinish"
    });
  });
  window.addEventListener("message", (event) => {
    const message = event.data;
    switch (message.type) {
      case "wizardProgress":
        const progressEl = document.getElementById("step-progress");
        if (progressEl) {
          progressEl.innerHTML = message.message || "";
        }
        break;
      case "wizardStepUpdate":
        updateStep(message.step || 0);
        break;
      case "wizardComplete":
        alert("Setup complete!");
        break;
    }
  });
  updateStep(0);
})();
