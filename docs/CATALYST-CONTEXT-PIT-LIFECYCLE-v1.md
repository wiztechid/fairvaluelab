# Catalyst Context Engine v1 Part 4 — PIT Materiality & Event Lifecycle Resolver

Status: PRE-FREEZE IMPLEMENTATION CONTRACT. Parts 1–3 remain frozen.

## Purpose
Resolve temporal truth at an explicit asOf. This layer answers whether an already-identified event is CURRENT, STALE, SUPERSEDED, or WITHDRAWN, and whether the ticker has NO_MATERIAL_EVENT. It defines no attractiveness, score, rank, trade signal, or Scanner promotion/demotion rule.

## Boundary
Parts 1–3 establish event identity, revision truth, provenance and consumption proof. Part 4 consumes immutable lifecycle assertions. It MUST NOT infer materiality from a hidden age/score threshold.

Lifecycle input per event:
- eventAnchorId
- lifecycleAssertionId
- lifecycleStatus: ACTIVE | SUPERSEDED | WITHDRAWN
- assertedAt
- effectiveAt
- materialUntil (ISO timestamp or null)
- supersededByEventAnchorId (required only for SUPERSEDED)
- assertionHash

assertionHash binds the canonical assertion payload excluding assertionHash.

## PIT states
CURRENT — ACTIVE assertion is effective by asOf and materialUntil is null or >= asOf.
STALE — ACTIVE assertion remains the latest truth but materialUntil < asOf.
SUPERSEDED — latest effective assertion says this event was replaced by another known event.
WITHDRAWN — latest effective assertion explicitly withdraws the event.
NO_MATERIAL_EVENT — after PIT filtering there is no CURRENT event. Historical STALE/SUPERSEDED/WITHDRAWN records may remain in lifecycle history but do not become current evidence.

## P0 invariants
1. PIT_ONLY — assertions with assertedAt or effectiveAt after asOf cannot alter historical state.
2. IDENTITY_BINDING — assertion is bound to one eventAnchorId and immutable hash.
3. LATEST_EFFECTIVE_TRUTH — state is derived only from the latest effective assertion known by asOf.
4. NO_HIDDEN_AGE_POLICY — resolver never invents stale-after-N-days.
5. EXPLICIT_SUPERSESSION — SUPERSEDED requires a distinct known successor event and cannot self-target.
6. EXPLICIT_WITHDRAWAL — WITHDRAWN is not inferred from silence or source failure.
7. STALE_IS_NOT_WITHDRAWN — expiry of materialUntil does not rewrite event/revision history.
8. SOURCE_FAILURE_IS_NOT_NO_EVENT — source availability remains a separate upstream missingness concern.
9. DETERMINISM — observation/assertion input ordering cannot change PIT result.
10. NO_PRIVATE_SCORING — no weights, thresholds, ranks, feature vectors or promotion logic enter this layer.
11. FROZEN_PARITY — Parts 1–3 regression gates must remain green.

## Output
Part 4 emits a separate `catalyst-lifecycle-v1` artifact rather than mutating frozen `catalyst-context-v1`.
