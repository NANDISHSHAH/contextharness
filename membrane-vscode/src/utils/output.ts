import * as vscode from 'vscode';
import { OUTPUT_CHANNEL } from '../constants';

let outputChannel: vscode.OutputChannel | null = null;

export function getOutputChannel(): vscode.OutputChannel {
  if (!outputChannel) {
    outputChannel = vscode.window.createOutputChannel(OUTPUT_CHANNEL);
  }
  return outputChannel;
}

export function showOutput(): void {
  getOutputChannel().show();
}

export function log(message: string): void {
  getOutputChannel().appendLine(`[${new Date().toLocaleTimeString()}] ${message}`);
}

export function logJson(label: string, data: any): void {
  log(`${label}: ${JSON.stringify(data, null, 2)}`);
}

export function clear(): void {
  getOutputChannel().clear();
}

export function dispose(): void {
  outputChannel?.dispose();
  outputChannel = null;
}
