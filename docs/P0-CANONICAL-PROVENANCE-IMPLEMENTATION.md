# P0 Canonical Engine & Data Provenance — Implementation

Status: candidate implementation; not production-promoted until QC and merge.

## Canonical public path
The existing static frontend already reads `data/{TICKER}.json`. P0 formalizes that generated/validated artifact as the sole canonical public fair-value output.

`app.py:/api/analyze` remains present for compatibility but is explicitly registered as LEGACY_NON_CANONICAL and may not publish authoritative CekValuasi fair value.

## Separation of concerns
- `validate_engine.py`: valuation semantics and evidence-state integrity.
- `canonical_contract.py`: stamps canonical/provenance lineage after semantic validation.
- `validate_canonical_contract.py`: validates canonical/provenance metadata only.
- frontend: unchanged.
- valuation formulas/models: unchanged.

## Provenance contract
Market/fundamental data = THIRD_PARTY.
DES universe = OFFICIAL.
Valuation output = DERIVED.
Growth/discount/terminal assumptions = ESTIMATED.

Each ticker artifact receives provider, observation timestamp, freshness state, universe source, and engine/QC lineage.

## Fail-closed order
Generate/model pipeline → validate_engine.py → canonical_contract.py → validate_canonical_contract.py → downstream non-valuation enrichment → commit.

A failed semantic or canonical contract validation prevents publication.

## Non-goals
No rebrand, no permanent ticker-route migration, no frontend refactor, no AdSense, no model-formula change, no deletion of legacy Flask code.
