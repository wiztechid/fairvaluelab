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


## Authoritative filing identity boundary
Status: CONTRACT PROVEN; EMPIRICAL BINDING UNPROVEN.

The dual-source filing provenance V1 resolver is a fail-closed security contract, not evidence that current public IDX channels can satisfy it. The repository currently has no production collector/adapter for IDX_FINANCIAL_DATA_RATIO that supplies a source-native externalDocumentId, and no authentic fixture demonstrates the same immutable externalDocumentId across the period and availability legs.

Public Financial Report evidence must preserve source=IDX_PUBLIC_FINANCIAL_REPORT and verification=OFFICIAL_IDX_PUBLIC. It must never be relabeled as IDX/OFFICIAL_IDX_API merely to satisfy the availability leg. The authentic AADI 2026Q1 public record is PUBLIC_ROUTE_IDENTITY_BLOCKED and prohibited from VERIFIED admission. This classification means the accessible public representation did not expose a source-native shared identity; it does not claim that IDX has no internal identifier.

Production promotion rule: keep VERIFIED closed until an authoritative source exposes a source-native document identity that can be independently bound across required evidence. Never synthesize identity from ticker, quarter, publication date, title, filename, URL, or their concatenation/hash.
