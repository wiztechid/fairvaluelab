# CekValuasi Publication Gate

A generated valuation may become public only when all mandatory gates pass.

## Gate A — Run integrity
- Pipeline completed.
- Current universe represented or failures explicitly recorded.
- Output JSON is parseable and finite.
- Engine/QC versions are expected.

## Gate B — Valuation integrity
- Scenario ordering valid.
- Evidence status matches method/family count.
- Family dominance guard passes.
- Extreme/conflict cases route to REVIEW.
- No fabricated value for insufficient evidence.

## Gate C — Data integrity
- Provenance known for material inputs.
- Freshness state present.
- Currency/unit normalization checked.
- Provider fallback/degradation disclosed.

## Gate D — Historical integrity
- Snapshot lock is immutable.
- PIT quality is VERIFIED or explicitly PROVISIONAL.
- No backfill may masquerade as information known at the historical date.

## Gate E — Public page integrity
- Ticker/name/status/value match canonical JSON.
- Timestamp and data quality are visible.
- Disclaimer/methodology are reachable.
- Structured data does not contradict visible content.

## Failure behavior
Fail closed for new publication. Preserve the last known-good public artifact when safe; otherwise expose a clear unavailable/stale state. Never substitute invented data.
