"use strict";
(() => {
  // webview-src/harvest/harvest.ts
  var queryInput = document.getElementById("query-input");
  var branchInput = document.getElementById("branch-input");
  var submitBtn = document.getElementById("submit-btn");
  var outputDiv = document.getElementById("output");
  var copyBtn = document.getElementById("copy-btn");
  var openEditorBtn = document.getElementById("open-editor-btn");
  submitBtn?.addEventListener("click", () => {
    const query = queryInput?.value || "";
    const branch = branchInput?.value || "";
    if (!query) {
      alert("Please enter a query");
      return;
    }
    submitBtn.disabled = true;
    submitBtn.textContent = "Loading...";
    window.vscode.postMessage({
      type: "harvest",
      query,
      branch
    });
  });
  copyBtn?.addEventListener("click", () => {
    const text = outputDiv?.innerText || "";
    navigator.clipboard.writeText(text).then(() => {
      alert("Copied to clipboard");
    });
  });
  openEditorBtn?.addEventListener("click", () => {
    const text = outputDiv?.innerText || "";
    window.vscode.postMessage({
      type: "openInEditor",
      content: text
    });
  });
  window.addEventListener("message", (event) => {
    const message = event.data;
    switch (message.type) {
      case "harvestResult":
        outputDiv.innerHTML = message.content || "No results";
        submitBtn.disabled = false;
        submitBtn.textContent = "Harvest";
        break;
      case "harvestError":
        outputDiv.innerHTML = `<p style="color: red;">Error: ${message.error}</p>`;
        submitBtn.disabled = false;
        submitBtn.textContent = "Harvest";
        break;
    }
  });
  queryInput?.focus();
})();
