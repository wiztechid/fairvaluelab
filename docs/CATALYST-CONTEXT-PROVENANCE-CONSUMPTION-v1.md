# Catalyst Context Engine v1 Part 3 — Provenance, Syndication & Consumption Proof

Status: PRE-FREEZE IMPLEMENTATION CONTRACT. Part 1 and Part 2 remain frozen.

## Trust boundary
Raw source observation → provenance resolver → immutable origin lineage → Part 2 canonical event resolver → cross-domain consumption verifier → sanitized context.

## P0 invariants
1. ORIGIN_LINEAGE — every DERIVATIVE observation binds to exactly one earlier known origin observation.
2. NO_SELF_ATTESTATION — sourceClass alone never proves syndication or independence.
3. ORIGIN_IMMUTABILITY — origin identity binds ticker, source locator, content digest and observed timestamp.
4. SYNDICATION_COLLAPSE — mirrors, media rewrites, broker/news/social restatements that declare the same proven origin remain one provenance family.
5. PIT_LINEAGE — a derivative cannot bind to an origin not yet observed at derivative observedAt.
6. ACYCLIC_PROVENANCE — origin chains cannot self-link, fork backwards into unknown IDs, or cycle.
7. CONSUMPTION_PROOF — shared-domain dependency requires a valid immutable receipt, not bare fact-ID intersection.
8. RECEIPT_BINDING — receipt binds factId, domain, consumerArtifactId, consumerRevisionId, consumerSnapshotHash, consumedAt and receiptHash.
9. RECEIPT_PIT — consumedAt cannot exceed Catalyst asOf and cannot predate the referenced origin fact firstObservedAt.
10. DOMAIN_AUTHORITY — only FUNDAMENTALS and PRICE receipts are accepted here.
11. FAIL_CLOSED — malformed, conflicting, duplicate or unverifiable lineage/receipt data is rejected.
12. NO_PRIVATE_SCORING — no Scanner weights, thresholds, ranks, tie-breaks or promotion logic enter this layer.
13. RECEIPT_LIFECYCLE — consumption proof is an exact-parent immutable ledger; only the ACTIVE tip proves current consumption.
14. REVOCATION — a REVOKED tip contributes no shared-origin proof.
15. NO_ROLLBACK_OR_FORK — receipt lineage cannot fork, move backward in time, mutate its economic key, or leave an ancestor ACTIVE.
16. EVENT_BINDING — fact IDs cannot bind to multiple event anchors inside one proof artifact.

## Provenance record
Part 3 consumes observations with provenance metadata:
- observationId
- sourceClass
- sourceLocator
- contentHash
- observedAt
- originObservationId (required for DERIVATIVE; null for origin observations)

The resolver emits an immutable provenanceFamilyId derived from the canonical origin record. DERIVATIVE observations never create a new economic confirmation.

## Consumption receipt
A cross-domain receipt contains:
- receiptId
- factId
- domain
- consumerArtifactId
- consumerRevisionId
- consumerSnapshotHash
- consumedAt
- parentReceiptId
- receiptStatus (ACTIVE / SUPERSEDED / REVOKED)
- receiptHash

receiptHash is SHA-256 over canonical receipt payload excluding receiptHash. A receipt is valid only when its factId is present in the Catalyst event originFactIds and all bindings validate. Receipt identity is additionally bound to ticker and eventAnchorId. Successors bind to the exact parent receipt; only the unique ACTIVE chain tip proves current consumption. A REVOKED tip removes current proof without rewriting history.

Bare domainEvidenceRefs remain a Part 1/2 compatibility field, but Part 3 must derive effective shared-domain consumption from verified receipts. A bare intersection without a receipt is not sufficient proof for Part 3.

## Versioning
Part 3 is an additive proof layer. It does not silently mutate frozen Part 1/2 artifact semantics. Any future replacement of the Part 1 domainEvidenceRefs contract requires explicit versioning.
