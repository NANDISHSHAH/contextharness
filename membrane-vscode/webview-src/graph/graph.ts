/**
 * Dependency graph webview using Cytoscape.js
 */

interface GraphData {
  nodes: Array<{ data: { id: string; label: string; isHub?: boolean } }>;
  edges: Array<{ data: { id: string; source: string; target: string } }>;
}

let cy: any = null;

window.addEventListener('message', (event) => {
  const message = event.data;

  switch (message.type) {
    case 'graphData':
      renderGraph(message.data);
      break;
  }
});

function renderGraph(data: GraphData): void {
  const container = document.getElementById('graph-container');
  if (!container) {
    return;
  }

  if (!cy) {
    // Initialize Cytoscape (assumes cytoscape.min.js is loaded globally)
    cy = (window as any).cytoscape({
      container,
      style: [
        {
          selector: 'node',
          style: {
            'content': 'data(label)',
            'background-color': '#3498db',
            'width': 'mapData(degree, 0, 50, 20, 60)',
            'height': 'mapData(degree, 0, 50, 20, 60)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': 12,
          },
        },
        {
          selector: 'node[isHub]',
          style: {
            'background-color': '#e74c3c',
          },
        },
        {
          selector: 'edge',
          style: {
            'target-arrow-shape': 'triangle',
            'line-color': '#95a5a6',
            'target-arrow-color': '#95a5a6',
          },
        },
      ],
      layout: {
        name: 'cose',
        directed: true,
        animate: true,
      },
    });

    // Handle node clicks
    cy.on('tap', 'node', (event: any) => {
      const nodeId = event.target.id();
      (window as any).vscode.postMessage({
        type: 'nodeSelected',
        nodeId,
      });
    });
  }

  // Update graph data
  cy.elements().remove();
  cy.add(data.nodes);
  cy.add(data.edges);

  // Run layout
  const layout = cy.layout({ name: 'cose', directed: true, animate: true });
  layout.run();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Load Cytoscape library
  const script = document.createElement('script');
  script.src = 'cytoscape.min.js';
  script.onload = () => {
    // Request initial data from extension
    (window as any).vscode.postMessage({ type: 'requestGraphData' });
  };
  document.head.appendChild(script);
});
