# CekValuasi Upgrade Blueprint v1.0

Status: additive planning document. This file does not authorize changes to the existing engine, frontend, deployment, or data pipeline.

## North Star
Transform FairValueLab into CekValuasi as a reader-first public valuation product while preserving the validated valuation engine.

## Non-negotiables
- Existing production files are preserved until a separately approved migration.
- Precomputed validated valuation JSON is the intended public single source of truth.
- No public fair value may bypass engine validation.
- Market price is context/review trigger, never a hidden valuation anchor.
- Missing evidence must degrade status, not fabricate precision.
- SEO scaling must not create thin ticker pages.
- Model changes require regression evidence and changelog.

## Target layers
1. Data acquisition and provenance.
2. Normalization.
3. Valuation engine.
4. Engine/data QC.
5. Publication gate.
6. Generated public data/pages.
7. Reader-first CekValuasi frontend.

## Priority
P0: baseline freeze, canonical engine, provenance/freshness, regression.
P1: brand foundation, componentized frontend, permanent ticker URLs, SEO/legal/trust.
P2: explanation layer, confidence/freshness UX, sector discovery.
P3: high-quality programmatic SEO, history/comparison, monetization.

## Migration rule
All implementation must be incremental, reversible, and independently validated. Existing production behavior remains authoritative until a migration gate explicitly promotes a replacement.
