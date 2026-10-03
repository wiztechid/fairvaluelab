# Deep QC Report v1.0 — Governance vs FairValueLab v3.20

Date: 2026-09-27
Scope: additive CekValuasi governance versus current FairValueLab engine.
Production files changed: none.

## P0 findings
1. Private moat must not be committed to this public repository. Resolved in clean candidate branch: no private/ content included.
2. Canonical public engine ambiguity exists between generated v3.20 artifacts and separate live Flask calculation path. Governance target recorded; production unchanged.
3. Full provenance/freshness is not yet present in current engine output. Publication/data documents treat this as a migration requirement, not as a claim that it already passes.

## P1 findings
1. Status semantics were implicit in code. Added VALUATION-STATUS-CONTRACT.
2. Model risks were distributed across code/comments. Added MODEL-RISK-REGISTER.
3. Vendor/source risks lacked a single register. Added DATA-SOURCE-RISK-REGISTER.
4. PIT backtest fallback is not verified filing-time evidence. Governance preserves PROVISIONAL distinction.
5. Current validator family-dominance check is implementation-specific and should not be misrepresented as the family-consensus vote algorithm. Governance treats current validator as authoritative until separately changed.

## Alignment confirmed
- >=2 independent families for full FV.
- Indicative/reference confidence caps.
- no fabricated value for BELUM_DINILAI.
- cross-family conflict preserved rather than discarded.
- market price used as forensic review trigger, not valuation anchor.
- extreme divergence routes to REVIEW.
- atomic universe representation.
- version/QC checks.
- point-in-time quality distinction.

## Merge verdict
PASS for documentation/governance adoption only, using the clean candidate branch.
This is NOT a PASS to activate CekValuasi rebrand, canonical-engine migration, provenance enforcement, SEO migration, AdSense, or model changes. Those remain separate gated implementations.


## IDX authoritative filing transport boundary — 2026-10-03
Status: **FROZEN — FAILURE SEMANTICS ONLY; AUTHORITATIVE TRANSPORT NOT RECOVERED**.

The GitHub Actions collector currently receives HTTP 403 from the internal IDX announcement endpoint. This state is recorded explicitly as `IDX_COLLECTOR_STATUS_V1 / SOURCE_BLOCKED`; it is not treated as a healthy empty corpus. Existing validated cache is preserved on collection failure, and no Yahoo/valuation data may be promoted as official filing provenance.

Collector health is schema-narrow and CI rejects unrelated valuation payload fields. Filing promotion requires official IDX verification plus explicit normalized `FINANCIAL_STATEMENT` document type and exact `financialQuarter`; publication date alone is never used to infer quarter. Existing historical PROVISIONAL backtest snapshots remain immutable and are not retroactively promoted.

Workflow run `37114665627` SUCCESS with `IDX_DISCLOSURE_RECORDS 0`, `IDX_NORMALIZED_FINANCIAL_FILINGS 0`, and `IDX_COLLECTOR_STATE SOURCE_BLOCKED`. This proves fail-closed behavior, not transport availability.


## Filing provenance adversarial closure — 2026-10-03
Status: **FROZEN — PROMOTION CONTRACT; LIVE AUTHORITATIVE CORPUS STILL BLOCKED**.

The filing resolver now has a dedicated adversarial gate. VERIFIED promotion requires exact ticker, explicit normalized financial quarter, FINANCIAL_STATEMENT document type, OFFICIAL_IDX_API verification, valid publishedAt, and a non-empty disclosure ID. Wrong ticker/quarter/source/verification, missing timestamp, wrong document type, missing ID, or missing disclosure all preserve PROVISIONAL state.

Official IDX Financial Data and Ratio may support financial-period identity but is not treated as publication-time evidence. Availability time remains a separate requirement; no FS date or report period is converted into publishedAt.

Workflow run `37115252527` SUCCESS and printed `FILING_PROVENANCE_ADVERSARIAL_V1_PASS`. The live announcement transport still returned HTTP 403 and correctly remained `SOURCE_BLOCKED` with zero normalized filings. Therefore the promotion contract is frozen, while real VERIFIED corpus admission remains closed.
