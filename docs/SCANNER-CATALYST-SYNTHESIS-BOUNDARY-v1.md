# Scanner ↔ Catalyst Synthesis Boundary v1

Status: PUBLIC-SAFE PRE-ENGINE ADAPTER CONTRACT.

## Purpose
Connect frozen Catalyst Context Parts 1–4 to the Scanner synthesis boundary without adding another Catalyst foundation layer and without implementing the private Opportunity Engine.

## One-way boundary
Frozen Catalyst artifacts
→ Catalyst Synthesis Adapter
→ categorical public-safe evidence projection
→ PRIVATE Scanner synthesis
→ existing Private Sanitizer
→ frozen Scanner public artifact/publication gate.

Scanner UI/publication code MUST NOT consume raw Catalyst event observations, revision traces, provenance graphs, consumption receipts, lifecycle assertions, or private synthesis traces.

## Allowed adapter output
Exactly:
- schemaVersion = scanner-catalyst-evidence-v1
- ticker
- asOf
- catalystEvidence: SUPPORTIVE | LIMITED | NOT_AVAILABLE
- catalystFreshness: CURRENT | NO_MATERIAL_EVENT | SOURCE_UNAVAILABLE | STALE
- reasonCodes: [] or [MATERIAL_CATALYST]
- caveatCodes: subset of CATALYST_UNVERIFIED, CATALYST_UNAVAILABLE, DATA_STALE, MATERIAL_EVENT_REVIEW
- sourceBinding:
  - contextAsOf
  - lifecycleSnapshotHash

No other field is allowed.

## Deterministic semantic mapping
- CURRENT_MATERIAL_EVIDENCE + at least one Part-4 CURRENT event → SUPPORTIVE / CURRENT / MATERIAL_CATALYST.
- NO_MATERIAL_EVENT → LIMITED / NO_MATERIAL_EVENT / no positive Catalyst reason.
- SOURCE_UNAVAILABLE → NOT_AVAILABLE / SOURCE_UNAVAILABLE / CATALYST_UNAVAILABLE.
- STALE_EVIDENCE or no CURRENT event while lifecycle contains STALE → LIMITED / STALE / DATA_STALE.
- SUPERSEDED or WITHDRAWN lifecycle information may emit MATERIAL_EVENT_REVIEW as a caveat, but never MATERIAL_CATALYST by itself.
- unresolved/unverified context may emit CATALYST_UNVERIFIED but cannot become SUPPORTIVE.

## Hard boundaries
1. NO_STATE_AUTHORITY — adapter cannot emit Scanner state/stateLabel/state history.
2. NO_SCORE — no score, rank, weight, threshold, percentile, contribution, penalty, confidence number, promotion/demotion or trade signal.
3. NO_DOUBLE_COUNT — Catalyst shared-origin evidence remains one Catalyst family. Adapter never turns FUNDAMENTALS/PRICE consumption receipts into extra confirmation.
4. PIT_BINDING — context asOf and lifecycle asOf must match exactly.
5. TICKER_BINDING — ticker must match across frozen Catalyst context and lifecycle artifact.
6. SNAPSHOT_BINDING — lifecycleSnapshotHash must be valid and carried unchanged.
7. CURRENT_REQUIRES_CURRENT — MATERIAL_CATALYST is impossible without a CURRENT lifecycle event.
8. MISSINGNESS — SOURCE_UNAVAILABLE, NO_MATERIAL_EVENT and STALE remain distinct.
9. LOSSY_PROJECTION — raw observations, revisions, provenance families, receipts, fact IDs, assertion lineage and event graph never cross this boundary.
10. PUBLIC_REGISTRY_ONLY — emitted semantic codes must already exist in the frozen Scanner public Reason Registry/schema.

This adapter supplies evidence semantics only. How private Scanner synthesis combines Catalyst with Quality, Valuation and Price remains outside the public repository.
