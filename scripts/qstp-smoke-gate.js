#!/usr/bin/env node
/**
 * QSTP permanent syntax + structural smoke gate.
 * Zero external dependencies: Node built-ins only.
 * Fails closed when qstp.html cannot be parsed or critical QSTP contracts disappear.
 */
const fs = require('fs');
const vm = require('vm');

const file = 'qstp.html';
const html = fs.readFileSync(file, 'utf8');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(m => m[1]);

function fail(msg) {
  console.error('❌ QSTP GATE:', msg);
  process.exitCode = 1;
}
function pass(msg) { console.log('✅', msg); }

if (scripts.length !== 1) fail(`expected exactly 1 inline <script>, found ${scripts.length}`);
else {
  try { new vm.Script(scripts[0], { filename: 'qstp.inline.js' }); pass('JavaScript syntax parses'); }
  catch (e) { fail('JavaScript syntax error: ' + e.message); }
}

const requiredIds = ['capital','count','riskPct','maxPos','deployPct','heatPct','stopPct','rewardR','tickers','result','warnings','kpis','rows','education','generate','pdf'];
for (const id of requiredIds) if (!new RegExp(`id=["']${id}["']`).test(html)) fail('missing critical DOM id #' + id);
if (!process.exitCode) pass('critical DOM contracts present');

const contracts = [
  ['DES loader', /(?:fetch\(['"]data\/summary\.json|new\s+URL\(['"]\/data\/summary\.json['"],\s*location\.origin\))/],
  ['ticker renderer', /function\s+renderTickers\s*\(/],
  ['auto SL\/TP', /function\s+applyQuick\s*\(/],
  ['planning engine', /function\s+plan\s*\(/],
  ['generate action', /function\s+generate\s*\(/],
  ['PDF builder', /function\s+makePdf\s*\(/],
  ['Blob PDF download', /URL\.createObjectURL\s*\(/],
  ['canonical snapshot', /snapshot\s*=\s*structuredClone\s*\(/],
  ['tick normalization', /function\s+tickSize\s*\(/],
  ['heat status', /EFFECTIVELY FULL/],
];
for (const [name, re] of contracts) if (!re.test(html)) fail('missing contract: ' + name);
if (!process.exitCode) pass('QSTP structural smoke contracts present');

const forbidden = [
  ['iframe PDF preview', /<iframe/i],
  ['window.print PDF path', /window\.print\s*\(/],
  ['known duplicate heatState regression', /heatState\s*=\s*remainingHeat\s*=.*heatState\s*=/s],
];
for (const [name, re] of forbidden) if (re.test(html)) fail('forbidden regression detected: ' + name);
if (!process.exitCode) pass('known regressions absent');

if (process.exitCode) process.exit(1);
console.log('🟢 QSTP syntax/smoke gate PASS');
