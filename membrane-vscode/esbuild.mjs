#!/usr/bin/env node

import esbuild from 'esbuild';
import * as fs from 'fs';
import * as path from 'path';

const isWatch = process.argv.includes('--watch');

const mainConfig = {
  entryPoints: ['src/extension.ts'],
  bundle: true,
  platform: 'node',
  external: ['vscode'],
  format: 'cjs',
  target: 'node18',
  outfile: 'out/extension.js',
  sourcemap: true,
};

const webviewConfigs = [
  {
    entryPoints: ['webview-src/graph/graph.ts'],
    bundle: true,
    platform: 'browser',
    format: 'iife',
    target: 'ES2020',
    outfile: 'out/webview-graph.js',
    sourcemap: true,
  },
  {
    entryPoints: ['webview-src/harvest/harvest.ts'],
    bundle: true,
    platform: 'browser',
    format: 'iife',
    target: 'ES2020',
    outfile: 'out/webview-harvest.js',
    sourcemap: true,
  },
  {
    entryPoints: ['webview-src/wizard/wizard.ts'],
    bundle: true,
    platform: 'browser',
    format: 'iife',
    target: 'ES2020',
    outfile: 'out/webview-wizard.js',
    sourcemap: true,
  },
];

async function build() {
  try {
    // Ensure out directory exists
    if (!fs.existsSync('out')) {
      fs.mkdirSync('out', { recursive: true });
    }

    if (isWatch) {
      const mainCtx = await esbuild.context(mainConfig);
      const webviewCtxs = await Promise.all(webviewConfigs.map(cfg => esbuild.context(cfg)));

      await mainCtx.watch();
      await Promise.all(webviewCtxs.map(ctx => ctx.watch()));

      console.log('Watching for changes...');
    } else {
      await esbuild.build(mainConfig);
      await Promise.all(webviewConfigs.map(cfg => esbuild.build(cfg)));

      console.log('Build complete');
    }
  } catch (error) {
    console.error('Build failed:', error);
    process.exit(1);
  }
}

build();
