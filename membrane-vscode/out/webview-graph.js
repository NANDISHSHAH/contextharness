"use strict";
(() => {
  // webview-src/graph/graph.ts
  var cy = null;
  window.addEventListener("message", (event) => {
    const message = event.data;
    switch (message.type) {
      case "graphData":
        renderGraph(message.data);
        break;
    }
  });
  function renderGraph(data) {
    const container = document.getElementById("graph-container");
    if (!container) {
      return;
    }
    if (!cy) {
      cy = window.cytoscape({
        container,
        style: [
          {
            selector: "node",
            style: {
              "content": "data(label)",
              "background-color": "#3498db",
              "width": "mapData(degree, 0, 50, 20, 60)",
              "height": "mapData(degree, 0, 50, 20, 60)",
              "text-valign": "center",
              "text-halign": "center",
              "font-size": 12
            }
          },
          {
            selector: "node[isHub]",
            style: {
              "background-color": "#e74c3c"
            }
          },
          {
            selector: "edge",
            style: {
              "target-arrow-shape": "triangle",
              "line-color": "#95a5a6",
              "target-arrow-color": "#95a5a6"
            }
          }
        ],
        layout: {
          name: "cose",
          directed: true,
          animate: true
        }
      });
      cy.on("tap", "node", (event) => {
        const nodeId = event.target.id();
        window.vscode.postMessage({
          type: "nodeSelected",
          nodeId
        });
      });
    }
    cy.elements().remove();
    cy.add(data.nodes);
    cy.add(data.edges);
    const layout = cy.layout({ name: "cose", directed: true, animate: true });
    layout.run();
  }
  document.addEventListener("DOMContentLoaded", () => {
    const script = document.createElement("script");
    script.src = "cytoscape.min.js";
    script.onload = () => {
      window.vscode.postMessage({ type: "requestGraphData" });
    };
    document.head.appendChild(script);
  });
})();
