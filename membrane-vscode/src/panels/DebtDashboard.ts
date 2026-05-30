import * as vscode from 'vscode';
import { ContextRunner } from '../python/runner';
import { log } from '../utils/output';

export class DebtDashboard {
  static currentPanel: DebtDashboard | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];

  private constructor(
    panel: vscode.WebviewPanel,
    private runner: ContextRunner,
  ) {
    this.panel = panel;
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage(
      msg => this.handleMessage(msg),
      null,
      this.disposables,
    );
  }

  static show(runner: ContextRunner): void {
    if (DebtDashboard.currentPanel) {
      DebtDashboard.currentPanel.panel.reveal(vscode.ViewColumn.Two);
      DebtDashboard.currentPanel.loadData();
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      'membrane.debt',
      'Membrane — Context Debt',
      vscode.ViewColumn.Two,
      { enableScripts: true, retainContextWhenHidden: true },
    );

    const instance = new DebtDashboard(panel, runner);
    instance.panel.webview.html = getHtml();
    DebtDashboard.currentPanel = instance;
    setTimeout(() => instance.loadData(), 400);
  }

  private async loadData(): Promise<void> {
    try {
      const [debt, coupling] = await Promise.all([
        this.runner.runJson<any[]>(['debt', '--json']),
        this.runner.runJson<any>(['coupling', '--json']).catch(() => null),
      ]);
      this.panel.webview.postMessage({ type: 'data', debt: debt ?? [], coupling });
    } catch (err: any) {
      log(`DebtDashboard error: ${err.message}`);
      this.panel.webview.postMessage({ type: 'data', debt: [], coupling: null });
    }
  }

  private async handleMessage(msg: any): Promise<void> {
    if (msg.type === 'refresh') await this.loadData();
  }

  private dispose(): void {
    DebtDashboard.currentPanel = undefined;
    this.panel.dispose();
    this.disposables.forEach(d => d.dispose());
    this.disposables = [];
  }
}

function getHtml(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';" />
<style>
  :root {
    --bg: var(--vscode-editor-background, #1e1e1e);
    --surface: var(--vscode-editorWidget-background, #252526);
    --border: var(--vscode-widget-border, #3c3c3c);
    --text: var(--vscode-editor-foreground, #cccccc);
    --text-dim: var(--vscode-descriptionForeground, #999);
    --accent: var(--vscode-focusBorder, #007acc);
    --red: #e74c3c;
    --orange: #e67e22;
    --green: #2ecc71;
    --mono: var(--vscode-editor-font-family, 'Courier New', monospace);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: var(--mono); background: var(--bg); color: var(--text); padding: 20px; font-size: 12px; }

  h1 { font-size: 13px; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: var(--accent); margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }
  button.refresh-btn { font-family: var(--mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; background: none; border: 1px solid var(--border); color: var(--text-dim); cursor: pointer; padding: 4px 10px; transition: all 0.15s; }
  button.refresh-btn:hover { border-color: var(--accent); color: var(--accent); }

  .section { margin-bottom: 28px; }
  .section-title { font-size: 9px; letter-spacing: 0.2em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }

  /* bar chart */
  .bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .bar-label { width: 160px; font-size: 11px; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 0; }
  .bar-track { flex: 1; height: 16px; background: var(--surface); border: 1px solid var(--border); position: relative; overflow: hidden; }
  .bar-fill { height: 100%; transition: width 0.6s cubic-bezier(0.4,0,0.2,1); position: relative; }
  .bar-fill::after { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08)); }
  .bar-score { width: 36px; font-size: 11px; text-align: right; flex-shrink: 0; }
  .bar-trend { width: 20px; text-align: center; font-size: 12px; flex-shrink: 0; }

  /* summary cards */
  .card-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
  .card { background: var(--surface); border: 1px solid var(--border); padding: 12px 14px; }
  .card-val { font-size: 22px; font-weight: 600; line-height: 1; margin-bottom: 4px; }
  .card-lbl { font-size: 9px; letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-dim); }

  .empty { color: var(--text-dim); font-size: 11px; padding: 20px 0; text-align: center; }

  /* coupling section */
  .coupling-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .coupling-item { background: var(--surface); border: 1px solid var(--border); padding: 10px 12px; }
  .coupling-key { font-size: 9px; color: var(--text-dim); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px; }
  .coupling-val { font-size: 13px; font-weight: 600; }
</style>
</head>
<body>
<h1>Context Debt <button class="refresh-btn" onclick="refresh()">↻ Refresh</button></h1>

<div class="card-row" id="summary-cards">
  <div class="card"><div class="card-val" id="s-total">—</div><div class="card-lbl">Modules</div></div>
  <div class="card"><div class="card-val" id="s-critical" style="color:var(--red)">—</div><div class="card-lbl">Critical</div></div>
  <div class="card"><div class="card-val" id="s-avg">—</div><div class="card-lbl">Avg Score</div></div>
</div>

<div class="section">
  <div class="section-title">Module Debt Scores</div>
  <div id="bars"><div class="empty">Loading…</div></div>
</div>

<div class="section" id="coupling-section" style="display:none">
  <div class="section-title">Coupling Trend</div>
  <div class="coupling-grid" id="coupling-grid"></div>
</div>

<script>
const vscode = acquireVsCodeApi();

function refresh() { vscode.postMessage({ type: 'refresh' }); }

window.addEventListener('message', e => {
  const { debt, coupling } = e.data;
  if (!debt) return;

  // Summary
  const critical = debt.filter(d => (d.score ?? d.debt_score ?? 0) >= 70).length;
  const avg = debt.length ? Math.round(debt.reduce((s, d) => s + (d.score ?? d.debt_score ?? 0), 0) / debt.length) : 0;
  document.getElementById('s-total').textContent = debt.length;
  document.getElementById('s-critical').textContent = critical;
  document.getElementById('s-avg').textContent = avg;

  // Bars
  const barsEl = document.getElementById('bars');
  if (!debt.length) { barsEl.innerHTML = '<div class="empty">No debt data — run Build Index first</div>'; return; }

  const sorted = [...debt].sort((a, b) => (b.score ?? b.debt_score ?? 0) - (a.score ?? a.debt_score ?? 0));

  barsEl.innerHTML = sorted.map(m => {
    const score = Math.round(m.score ?? m.debt_score ?? 0);
    const name = m.module ?? m.name ?? '?';
    const trend = m.trend === 'rising' ? '↑' : m.trend === 'falling' ? '↓' : '→';
    const trendColor = m.trend === 'rising' ? 'var(--red)' : m.trend === 'falling' ? 'var(--green)' : 'var(--text-dim)';
    const fillColor = score >= 70 ? 'var(--red)' : score >= 40 ? 'var(--orange)' : 'var(--green)';
    const label = name.split('/').pop() ?? name;

    return \`<div class="bar-row">
      <div class="bar-label" title="\${name}">\${label}</div>
      <div class="bar-track">
        <div class="bar-fill" style="width:\${score}%;background:\${fillColor}"></div>
      </div>
      <div class="bar-score" style="color:\${fillColor}">\${score}</div>
      <div class="bar-trend" style="color:\${trendColor}">\${trend}</div>
    </div>\`;
  }).join('');

  // Coupling
  if (coupling) {
    const sec = document.getElementById('coupling-section');
    const grid = document.getElementById('coupling-grid');
    sec.style.display = 'block';
    const items = [
      { key: 'Hub Count', val: coupling.hub_count ?? coupling.hubs ?? '—' },
      { key: 'Cycle Count', val: coupling.cycle_count ?? coupling.cycles ?? '—' },
      { key: 'Decay Alerts', val: coupling.decay_alerts ?? '—' },
      { key: '30d Trend', val: coupling.trend_30d ?? coupling.trend ?? '—' },
    ];
    grid.innerHTML = items.map(i => \`<div class="coupling-item"><div class="coupling-key">\${i.key}</div><div class="coupling-val">\${i.val}</div></div>\`).join('');
  }
});
</script>
</body>
</html>`;
}
