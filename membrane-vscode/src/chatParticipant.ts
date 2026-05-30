import * as vscode from 'vscode';
import { ContextRunner } from './python/runner';
import { log } from './utils/output';

export function registerChatParticipant(
  context: vscode.ExtensionContext,
  runner: ContextRunner,
): void {
  // VS Code chat API is only available in newer versions — guard against missing API
  if (!('chat' in vscode)) {
    log('VS Code Chat API not available — skipping @membrane participant');
    return;
  }

  try {
    const participant = (vscode as any).chat.createChatParticipant(
      'membrane',
      async (
        request: any,
        _ctx: any,
        stream: any,
        _token: vscode.CancellationToken,
      ) => {
        const q = request.prompt.toLowerCase().trim();
        log(`@membrane: "${request.prompt}"`);

        try {
          if (q.includes('debt') || q.includes('stale') || q.includes('health')) {
            const debt = await runner.runJson<any[]>(['debt', '--json']);
            if (!debt?.length) { stream.markdown('No context debt data. Run **Build Index** first.'); return; }
            const critical = debt.filter(d => (d.score ?? 0) >= 70);
            stream.markdown(`## Context Debt\n\n**${debt.length}** modules tracked · **${critical.length}** critical\n\n`);
            stream.markdown('| Module | Score | Trend |\n|---|---|---|\n');
            debt.slice(0, 15).forEach(m => {
              const score = Math.round(m.score ?? m.debt_score ?? 0);
              const trend = m.trend === 'rising' ? '↑' : m.trend === 'falling' ? '↓' : '→';
              stream.markdown(`| \`${m.module ?? m.name}\` | ${score} | ${trend} |\n`);
            });

          } else if (q.includes('conflict') || q.includes('lock')) {
            const locks = await runner.runJson<any[]>(['locks', '--json']);
            if (!locks?.length) { stream.markdown('No active agent locks.'); return; }
            stream.markdown(`## Agent Locks\n\n**${locks.length}** active lock(s):\n\n`);
            locks.forEach(l => stream.markdown(`- \`${l.agent_id ?? 'agent'}\` → \`${l.files?.join(', ') ?? 'unknown'}\` (since ${l.acquired_at ?? '?'})\n`));

          } else if (q.includes('pattern') || q.includes('failure') || q.includes('bug')) {
            const patterns = await runner.runJson<any[]>(['patterns', '--json']);
            if (!patterns?.length) { stream.markdown('No failure patterns detected. Good shape!'); return; }
            stream.markdown(`## Failure Patterns\n\n**${patterns.length}** pattern(s) detected:\n\n`);
            patterns.slice(0, 10).forEach(p => {
              const freq = p.count ?? p.frequency ?? 0;
              stream.markdown(`- **${p.category ?? p.pattern ?? 'Unknown'}** (${freq}x) — \`${p.glob ?? 'N/A'}\`\n`);
            });

          } else if (q.includes('trust') || q.includes('score')) {
            const trust = await runner.runJson<any[]>(['trust', '--json']);
            if (!trust?.length) { stream.markdown('No trust data yet. Build the index first.'); return; }
            stream.markdown(`## Trust Scores\n\n**${trust.length}** entries\n\n`);
            const low = trust.filter(t => (t.tier ?? 5) >= 4);
            if (low.length) {
              stream.markdown(`**${low.length}** low-trust file(s):\n`);
              low.slice(0, 8).forEach(t => stream.markdown(`- \`${t.file ?? t.path}\` — T${t.tier} (${t.score ?? '?'})\n`));
            } else {
              stream.markdown('All files at acceptable trust levels.');
            }

          } else if (q.includes('status') || q.includes('ready') || q.includes('summary')) {
            const outline = await runner.runJson<any>(['outline', '--json']);
            stream.markdown('## Membrane Status\n\n');
            if (outline) {
              stream.markdown(`- **Entities**: ${outline.entities?.length ?? 0}\n`);
              stream.markdown(`- **Files**: ${outline.files?.length ?? 0}\n`);
              stream.markdown(`- **Staleness**: ${outline.staleness ?? 'unknown'}\n`);
              stream.markdown(`- **Hubs**: ${outline.hubs?.length ?? 0} hub node(s)\n`);
            } else {
              stream.markdown('No index found. Run **Build Index** first.\n');
            }

          } else {
            // Generic harvest
            stream.markdown(`Harvesting context for: *${request.prompt}*…\n\n`);
            const result = await runner.run(['harvest', request.prompt], { timeout: 60_000 });
            if (result.exitCode === 0 && result.stdout) {
              stream.markdown(result.stdout);
            } else {
              stream.markdown('No results. Try: `@membrane status`, `@membrane debt`, `@membrane conflicts`, `@membrane patterns`.');
            }
          }
        } catch (err: any) {
          stream.markdown(`Error: ${err.message}`);
        }
      },
    );

    participant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'media', 'membrane.svg');
    context.subscriptions.push(participant);
    log('@membrane chat participant registered');
  } catch (err: any) {
    log(`Chat participant registration failed: ${err.message}`);
  }
}
