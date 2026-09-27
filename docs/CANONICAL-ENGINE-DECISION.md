# Canonical Engine Decision Record

Status: TARGET DECISION — not yet activated.

## Problem
The repository contains a generated valuation pipeline and a separate Flask/live calculation path. Parallel public calculation paths can drift.

## Target
For CekValuasi public production, precomputed JSON that has passed the repository validation/publication gates becomes the canonical public valuation artifact.

## Until migration
Existing production behavior remains unchanged. This document does not disable app.py or alter deployment.

## Promotion criteria
- schema/version contract documented;
- representative parity tests completed;
- frontend reads canonical artifacts consistently;
- stale/error behavior defined;
- rollback tested;
- no hidden live recomputation can overwrite displayed canonical fair value.

## Principle
Compute once through the governed engine; validate; publish immutable/current artifacts; let the reader-facing layer explain rather than recalculate.
