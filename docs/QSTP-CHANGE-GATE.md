# QSTP Permanent Change Gate

Any change touching `qstp.html`, its DES dataset, or the QSTP gate itself must pass **QSTP Syntax & Smoke Gate** before merge.

The gate is intentionally dependency-free and checks:
- inline JavaScript parses successfully;
- critical DOM IDs remain present;
- DES loading, ticker rendering, auto SL/TP, planning, canonical snapshot, tick normalization, PDF builder and Blob download contracts remain present;
- known fatal regressions such as duplicate `heatState` declarations are absent;
- legacy iframe / `window.print()` PDF paths do not return;
- `data/summary.json` contains a non-empty `stocks` array.

## Local check

```bash
node scripts/qstp-smoke-gate.js
```

## Merge rule

For QSTP changes, do not merge a PR while **QSTP syntax + structural smoke** is failing. Configure the repository ruleset / branch protection to require this status check if repository permissions allow it.

This gate protects availability and structural contracts. It does **not** replace QSTP calculation boundary tests, Android/browser visual QC, or PDF output regression testing.
