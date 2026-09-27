# Data Source Risk Register

## Third-party market/fundamental vendor
Current engine materially uses yfinance/Yahoo-sourced market and statement data.
Risks: rate limiting, schema changes, missing fields, delayed/restated data, inconsistent currency/units, corporate-action handling.
Policy: provider success is not proof of correctness. Material fields require provenance/freshness classification before CekValuasi production promotion.

## OJK DES universe
Purpose: eligibility universe.
Risk: periodic list changes and effective-date mismatch.
Policy: record source decision/effective period; do not imply that DES membership is an investment endorsement.

## Issuer/exchange/regulator disclosures
Preferred for authoritative event/filing evidence when available.
Risk: parsing/availability and publication timestamp capture.
Policy: preserve original date/source and distinguish reported fact from derived interpretation.

## Derived data
Examples: normalized growth, family consensus, confidence, fair value, technical context.
Risk: transformation/version drift.
Policy: retain engine/QC version and deterministic lineage where feasible.

## Failure behavior
Missing or stale evidence reduces coverage/status/confidence. It must never be silently replaced with invented values.
