# Current State — CekValuasi

Updated: 2026-09-29

## Production baseline
- CekValuasi homepage is now the production root. The validated Fair Value engine lives at `/fair-value/`; QSTP remains at `/qstp.html`.
- Universe configuration: OJK DES Period I 2026 as encoded in the existing repository.
- Public architecture currently uses static HTML plus generated JSON, with a separate Flask application also present.
- Existing valuation pipeline includes sector-aware models, QC, indicative/reference states, family consensus, validation, technical/catalyst layers, and snapshot/backtest support.
- QSTP (Quick Syariah Trading Plan) is live as the second product surface.
- Permanent QSTP syntax + structural smoke gate is merged to main via PR #6. It guards JavaScript parseability, critical DOM contracts, DES loading, ticker rendering, auto SL/TP, planning, canonical snapshot, tick normalization, PDF Blob download, DES JSON presence, and known fatal regressions.

## Current product direction
CekValuasi is being shaped as a decision-support platform for Indonesian sharia equities, not merely a single valuation calculator.

Current product journey:
1. **Discover** — identify candidates worth deeper research.
2. **Understand** — explain why a candidate surfaced or did not.
3. **Verify / Value** — inspect fair value, Margin of Safety, model confidence, evidence quality, and price context.
4. **Plan** — translate a user-selected setup into position size and portfolio-risk consequences through QSTP.
5. **Monitor** — future opportunity/watchlist state tracking.

Product surfaces:
- **Product #1 — Fair Value Analyzer:** existing valuation/research engine.
- **Product #2 — QSTP:** risk-first sharia trading-plan builder.
- **Product #3 — Syariah Opportunity Scanner:** next planned product after the CekValuasi homepage.

## CekValuasi homepage — production
The homepage now operates as the product gateway. Fair Value remains a separate validated engine at `/fair-value/`.

Proposed public positioning:
> **Valuasi dulu. Atur risiko. Baru ambil keputusan.**

Reader journey:
**Pilih saham → Cek valuasi → Pahami harga → Atur risiko → Simpan trading plan**

Homepage v1.2 was promoted to production on 2026-09-28 after root-switch, migration, browser-interaction, QSTP, and Pages deployment gates passed.

## Product #3 — Syariah Opportunity Scanner

### Problem
Help users answer:
> “Dari ratusan saham DES, mana yang layak saya analisis lebih dalam?”

The scanner must not behave as a generic ratio screener or publish a simplistic “best stock” ranking. Its purpose is candidate discovery and research prioritization.

### Public product DNA
- **DES-native:** candidate universe begins from the canonical sharia-stock dataset.
- **Valuation-aware:** reuse validated Fair Value output; do not create a second valuation engine.
- **Explain every candidate:** each surfaced candidate must state why it appeared and relevant caveats/invalidation factors.
- **Intent-based:** users choose a research intent rather than needing to configure dozens of technical filters.
- **Evidence-aware:** weak or incomplete evidence must visibly reduce confidence/status.
- **Actionable journey:** Scanner → Fair Value detail → QSTP.
- **Why NOT:** when practical, explain why a searched ticker does not satisfy the selected scanner condition. Failure to qualify must not be framed as the stock being “bad”.

Candidate intents may include:
- Undervalued
- Quality at Reasonable Price
- Dividend Quality
- Quality Growth
- Value + Momentum
- Hidden Opportunity

These are research lenses, not BUY/SELL recommendations.

### Opportunity state concept
Prefer interpretable states over a single pseudo-precise master score. Public-safe state concepts include:
- DISCOVERED
- QUALIFIED
- VALUATION CONFIRMED
- PRICE WATCH
- EXTENDED
- DATA LIMITED / DATA WARNING

The scanner should explain the state and the evidence behind it rather than present the state as an investment recommendation.

### Architecture principle
```
Canonical DES Data
        ↓
Fair Value Engine
        ↓
Quality / Fundamental Gates
        ↓
Price Context
        ↓
Opportunity State Layer
        ↓
Explainability Layer
        ↓
Opportunity Scanner
        ↓
Fair Value Detail → QSTP
```

Fair-value figures displayed by the scanner must come from the same canonical validated output used by the Fair Value product.

## Explainability principle
A cross-product CekValuasi principle is:

> **Angka tanpa penjelasan tidak cukup.**

Fair Value should explain valuation/evidence; Opportunity Scanner should explain selection/rejection; QSTP should explain sizing and binding constraints.

## Private-moat boundary
This public repository may document product behavior and public-safe contracts only.

Do **not** commit exact proprietary scanner recipes, gate hierarchy, weights, thresholds beyond public product requirements, confidence weighting, evidence penalties, cyclicality treatment, state-transition rules, ranking heuristics, or other reusable research IP. Those belong in genuinely private storage/repository and must not enter public Git history.

## Current governance decision
Production architecture is now `/` = CekValuasi homepage, `/fair-value/` = Fair Value engine, and `/qstp.html` = QSTP. Future visual redesigns must preserve product routes, SEO contracts, engine/data semantics, and permanent gates unless separately approved.

## Open P0 items
- Establish one canonical public valuation engine/output.
- Harden data provenance and freshness metadata.
- Establish regression baseline before formula changes.
- Separate public presentation migration from valuation semantics.
- Preserve PIT PROVISIONAL vs VERIFIED distinction.

## Freeze rule
Fair Value formulas/engine semantics, canonical data, QSTP calculations, product routes, SEO canonical contracts, permanent gates, and private-moat boundaries are frozen unless separately approved. Homepage theme/presentation may be iterated only as an isolated visual layer with regression gates.


## Production checkpoint — Editorial v1.2.1 — 2026-09-29
Status: Editorial Research Theme v1.2 is now the production homepage on main.

Production state:
- Homepage: Editorial Research Theme v1.2
- Product journey: Scanner → Fair Value → QSTP → Monitor
- Scanner remains IN DEVELOPMENT; Fair Value remains the primary usable CTA
- Homepage semantic schema is active
- Trust/readiness pages are present: About, Privacy, Terms, Disclaimer, Contact
- Sitemap includes trust pages
- ads.txt exists as a safe readiness placeholder; no publisher ID is fabricated or active
- Fair Value Engine, QSTP calculations, canonical data, routes, and permanent gates remain unchanged

Footer v1.2.1:
- commit: 1fd5c74c2c627cbb24d2e8809f42fec9c962f542
- editorial closing statement: “Riset lebih jernih. Keputusan tetap milik Anda.”
- navigation grouped into Produk / CekValuasi / Kepercayaan
- Scanner marked as coming soon
- mobile-responsive footer hierarchy
- compact investment disclaimer retained

Freeze:
- Homepage visual direction is considered production-ready and should remain visually frozen unless a regression or material usability issue is found.
- Future custom-domain work must migrate canonical/schema/OG/sitemap references deliberately from GitHub Pages to cekvaluasi.com.
- Future Scanner work must not expose private ranking weights, gates, penalties, or state-transition logic in the public repository.


## Custom-domain checkpoint — 2026-09-29
- Primary production domain: https://cekvaluasi.com
- GitHub Pages DNS check: successful.
- HTTPS enforcement: enabled.
- Repository CNAME: cekvaluasi.com.
- Canonical, Open Graph URL, homepage schema IDs/URLs, sitemap, robots sitemap reference, Fair Value OG image URL, and trust-page canonicals migrated from the GitHub Pages project URL to the custom domain.
- Fair Value engine semantics, QSTP calculations, DES data, routes, permanent gates, and private-moat boundaries remain unchanged.
- Post-merge requirement: production smoke-check /, /fair-value/, /qstp.html, sitemap.xml, robots.txt, canonical/OG/schema output, apex/www redirect behavior, and HTTPS.


## Scanner Architecture v1 checkpoint — 2026-09-29
Status: architecture/evidence contract agreed for the next product-planning phase. No Scanner engine implementation is authorized by this checkpoint.

### Repository/data audit baseline
- Canonical DES universe remains the OJK KEP-21/D.04/2026 Period I 2026 dataset; source universe contains 618 tickers and the current generated valuation summary contains 612 stocks.
- Existing reusable evidence layers include canonical Fair Value output, DES metadata, OHLC cache, Golden Zone/price-structure output, sector Margin of Safety context, valuation timeline, snapshots/backtest support, catalyst pipelines, and verified market-actor pipelines.
- Scanner must consume validated Fair Value output and must not calculate a competing fair value.
- Catalyst and market-actor evidence is additive/conditional in v1 because ingestion coverage may be incomplete; missing catalyst evidence must not be interpreted as negative evidence.

### Scanner Architecture v1
Canonical DES Universe
→ Eligibility & Data Gate
→ Evidence Features
→ Private Opportunity Engine
→ Confidence / Evidence Gate
→ Public Scanner Output
→ Fair Value Detail
→ QSTP

Product separation is explicit:
- Scanner answers: which DES candidates merit deeper research?
- Fair Value answers: what does the validated valuation evidence indicate?
- QSTP answers: how does the user structure risk for a user-selected setup?

### Evidence/scoring contract
Public-safe evidence pillars:
- Quality / fundamental evidence
- Valuation context
- Price / trend evidence
- Catalyst evidence when verified and available
- Risk / evidence-quality penalties

Rules:
- Do not use a simplistic public weighted master score as the product explanation.
- Not every evidence pillar is automatically substitutable for another.
- Missing evidence degrades confidence/status; it is not fabricated, silently imputed as favorable, or automatically treated as negative.
- Fair Value states such as SIAP, REVIEW, INDIKATIF, REFERENSI, and BELUM_DINILAI describe valuation evidence state and must not be directly converted into stock attractiveness rankings.
- A minimum evidence floor must be satisfied before promotion to the strongest public candidate state.

### Public UI/output contract
Preferred reader-facing states:
- Kandidat Riset
- Pantau
- Evidence Terbatas

Every surfaced candidate should expose public-safe reasons for surfacing plus material caveats / items to verify. Avoid BUY, SELL, STRONG BUY, “best stock”, or equivalent recommendation language.

The public UI should prioritize interpretable evidence and research lenses over a pseudo-precise proprietary score. Internal ranking may exist, but exact ranking logic is private.

### Anti-cannibalization contract
- /scanner/ owns discovery intent: finding DES stocks worth researching.
- /fair-value/ owns valuation / fair-value intent.
- /qstp.html owns position-sizing / trading-plan / risk-management intent.
- Homepage orchestrates the journey: Discover → Value → Plan.
- Scanner must not duplicate deep Fair Value analysis or QSTP calculations.

### Private-moat boundary
The public repository may contain schemas, public evidence categories, status definitions, freshness/explainability contracts, provenance, generic validation, UI, disclaimers, and public-safe generated output.

Do NOT commit exact proprietary weights, thresholds, feature interactions, ranking equations, penalty coefficients, normalization formulas, sector/regime adjustments, anti-gaming rules, tie-break logic, confidence calibration, promotion/demotion logic, backtest optimization criteria, or other reusable scanner research IP.

### Next authorized design step
Before writing the Scanner engine, build Scanner Data Feature Matrix v1 from the actual available data fields and classify each candidate feature as USE / CONDITIONAL / REJECT with evidence-quality rationale. Engine implementation begins only after that feature contract is reviewed and accepted.


## Scanner contracts freeze — Pre-Implementation Deep QC v1 — 2026-09-29
Status: PASS after contract patches. Scanner implementation may begin only at the public contract layer; Opportunity Engine logic remains out of scope for this checkpoint.

### Frozen public product flow
SCAN → PANTAU → CEK FAIR VALUE → ATUR RISIKO → MONITOR.

The Scanner discovers DES research candidates and manages a research watchlist. It is not a BUY/SELL signal, does not calculate an alternative fair value, and must not convert Scanner state into an automatic QSTP trade setup.

### Frozen evidence architecture
DES Eligibility
→ Reliability + lens-aware Freshness
→ Evidence Dependency / Independence Control
→ Quality Evidence Family + Valuation Evidence Family + Price Evidence Family
→ Opportunity Synthesis
→ Catalyst / Material Event Context
→ Internal State
→ Public Candidate State
→ Watchlist.

Hard anti-double-counting rules:
- Canonical FV, price/FV relationship, MoS, peer-relative MoS, dispersion, and valuation-family agreement belong to one VALUATION_EVIDENCE_FAMILY; they are not independent confirmations merely because they exist in separate fields/files.
- OHLC trend/momentum/extension/liquidity and Golden Zone structural context belong to one PRICE_EVIDENCE_FAMILY. Golden Zone score/dominanceScore must not become an additional Scanner vote.
- Quality and valuation evidence may share economic inputs. Cross-domain labels do not by themselves prove evidence independence. The private engine must maintain an Evidence Dependency Map.
- Repeated reporting of one catalyst does not create multiple confirmations.

### Engine invariants
1. CANONICALITY — Scanner never calculates Fair Value independently; valuation context comes only from canonical validated Fair Value output.
2. INDEPENDENCE — one economic fact cannot become multiple independent confirmations.
3. MISSINGNESS — missing/unavailable evidence is not automatically negative evidence.
4. INTEGRITY FIRST — unreliable, stale, conflicting, or materially incomplete required evidence can cap public state; attractiveness cannot override evidence integrity.
5. POINT-IN-TIME — historical evaluation may use only evidence available at the evaluation timestamp.

### Freshness and catalyst patch
- Freshness is evaluated by evidence domain and research-lens requirement; overall freshness is not simply the worst status across all optional domains.
- Catalyst states must distinguish at least: current material evidence, no material event, unavailable/source failure, and stale evidence.
- No catalyst is not a negative catalyst.
- Catalyst expiry alone must not demote a candidate unless the research thesis materially depended on that event.
- Material events may trigger review/re-evaluation, not an automatic positive/negative score.

### State-model patch
Public state is a synthesis of evidenceIntegrity + opportunityState + priceCondition rather than one public score crossing one threshold.
- WATCHLIST / Daftar Pantau
- RESEARCH_CONFIRMED / Terkonfirmasi Riset
- WAITING_CONFIRMATION / Tunggu Konfirmasi
- EXTENDED
- LIMITED_EVIDENCE / Evidence Terbatas

Internally, opportunity maturity and price condition remain separable axes so EXTENDED and WAITING_CONFIRMATION do not destroy an otherwise valid research thesis. DETECTED, REVIEW_HOLD, OUT, and INELIGIBLE remain lifecycle/internal states unless disclosure is useful.
State changes require evidence persistence to reduce daily oscillation; material integrity events may override normal persistence. Exact persistence, promotion, demotion, and override boundaries remain private.
Re-entry is evidence-driven using current evidence; previous state does not grant automatic re-entry.

### Research-lens patch
Initial v1 lenses are frozen:
- UNDERVALUED
- QUALITY_VALUE
- DIVIDEND_QUALITY
- QUALITY_GROWTH
- VALUE_MOMENTUM
- HIDDEN_OPPORTUNITY

Qualification is lens-specific. Evidence from different lenses must not be mixed merely to manufacture confirmation. Public output may expose primary and secondary qualifying lenses without exposing qualification recipes.

### Public Scanner Output Schema v1
Public per-ticker output may contain:
- schemaVersion / public engine version
- ticker, name, sector, industry
- DES eligibility/universe metadata
- public candidate state and reader-facing label
- primary/secondary research lenses
- categorical evidence strength
- whyWatching[] public-safe reason codes + text
- whatToVerify[] public-safe caveat codes + text
- domain freshness and last evaluation date/time as appropriate
- minimal canonical valuation context
- public provenance
- Fair Value deep-link and state-appropriate actions
- limited public lifecycle history

Public output MUST NOT contain raw/internal rank, opportunity score, component scores, sort score, weights, thresholds, raw feature vectors, penalties, normalization coefficients, feature contribution, promotion/demotion margin, sector/regime adjustments, anti-gaming logic, tie-break rules, confidence calibration, private reason combinations, or full private backtest/state history.
Public reason codes must remain semantic (for example VALUATION_OPPORTUNITY, QUALITY_SUPPORT, PRICE_CONFIRMATION_PENDING), never encode hidden thresholds.
Public transition history should be coarse enough to avoid becoming a threshold-reconstruction side channel. Presentation order must not be documented or guaranteed as exact internal-score order.

### Cross-product boundary
- Scanner owns discovery/watchlist intent.
- Fair Value owns valuation and remains the single canonical valuation destination.
- QSTP owns user-selected risk/position planning. Scanner may deep-link to QSTP only when contextually appropriate; Scanner state must never auto-create a BUY setup or trade instruction.
- Homepage continues to orchestrate Discover → Value → Plan.

### Implementation authorization
The first Scanner implementation phase is PUBLIC CONTRACT ONLY:
1. public JSON schema/contract,
2. validator,
3. honest empty-state fixture,
4. permanent Scanner contract/smoke gate.

No Opportunity Engine, private scoring logic, proprietary threshold, ranking recipe, or candidate-generation implementation is authorized in this phase.


### Contract Hardening Patch v1.0.1 — 2026-09-29
Deep QC of PR #10 hardened the pre-engine public contract before merge:
- split the ambiguous combined output schema into strict scanner-summary-v1 and scanner-ticker-v1 contracts;
- introduced generationStatus so NOT_GENERATED/unknown is not represented as numeric zero;
- retained an honest non-candidate ticker fixture rather than fabricating a real candidate;
- validator now uses strict public-field allowlists plus forbidden-field defense-in-depth;
- state and reader-facing stateLabel are bound to an approved mapping;
- whyWatching / whatToVerify use public semantic reason-code allowlists;
- ticker freshness is domain-aware and catalyst freshness distinguishes NO_MATERIAL_EVENT from SOURCE_UNAVAILABLE;
- generated summary invariants require evaluated <= eligible, watchlist <= evaluated, state totals = watchlist count, item totals = watchlist count, and unique tickers;
- Scanner detail and Fair Value links are canonical ticker-bound routes; QSTP remains an optional secondary action and cannot replace Fair Value as the primary action;
- workflow path coverage now protects contracts/scanner-**, data/scanner/**, and scripts/scanner-**;
- the empty Scanner is protected by an explicit PRE_ENGINE_LOCK until a separately reviewed Opportunity Engine implementation is authorized;
- exact internal ranking/scoring/thresholds and private decision logic remain absent from the public repository.


## Scanner publication boundary checkpoint — 2026-09-29
Public-repo phase after Scanner Contract v1 is restricted to the Private/Public Adapter Contract, Public Reason Registry, and Scanner Publication Gate. Opportunity Engine implementation remains prohibited from this public repository.

### Frozen trust boundary
Private Engine → Private Sanitizer → Sanitized Public Artifact → strict public validator → Scanner Publication Gate → production.

- Private engine/scoring source, exact weights/thresholds, dependency-map details, ranking/tie-break logic, persistence parameters, calibration, private feature vectors, and raw decision traces must never enter public Git history.
- Public artifacts carry only frozen schema fields and allowlisted categorical semantics.
- Reader-facing whyWatching/whatToVerify text is controlled by the public Reason Registry; private raw explanation text is not accepted.
- Publication is a complete summary + referenced ticker-artifact set. Missing, orphaned, mismatched, or uncontrolled artifacts fail closed.
- PRE_ENGINE_LOCK remains active while generationStatus=NOT_GENERATED; ticker artifacts are forbidden in that state.
- Fair Value remains canonical valuation provenance and primary Scanner action. QSTP remains optional secondary navigation and never an automatic trade instruction.
- Frontend remains presentation-only and must not recreate proprietary research intelligence.


## Catalyst Context Engine v1 — Part 1 checkpoint — 2026-09-30
Status: CONTRACT HARDENING IMPLEMENTED on branch `catalyst-context-contract-v1`; Opportunity Engine/scoring remains out of scope.

### Frozen Catalyst integrity rules
- One economic event must resolve to one stable `eventAnchorId`; publisher/headline duplication is not independent confirmation.
- Observation provenance distinguishes PRIMARY, CORROBORATION, DERIVATIVE, RUMOR, and CORRECTION.
- SUPPORT requires VERIFIED evidence. RUMOR and DERIVATIVE observations cannot be laundered into SUPPORT.
- Revision lineage is exact-parent bound. Only the highest non-withdrawn revision may be ACTIVE/canonical; superseded revisions cannot provide active SUPPORT.
- Shared economic origin with FUNDAMENTALS and/or PRICE must be declared and forces `DEPENDENT_SHARED_ORIGIN`; Catalyst cannot double-count the same earnings/dividend/corporate-action fact as an independent confirmation.
- Related-event graphs reject self-links, unknown targets, duplicates, and cycles.
- PIT semantics bind evidence use to `observedAt`; later revisions must not rewrite what was knowable historically.
- NO_MATERIAL_EVENT, SOURCE_UNAVAILABLE, STALE_EVIDENCE, and NOT_EVALUATED remain distinct missingness states.

### Permanent gate
`scripts/catalyst-context-validator.js` enforces the fail-closed integrity invariants.
`scripts/catalyst-context-adversarial-test.js` attacks rumor SUPPORT laundering, syndication SUPPORT laundering, hidden shared-origin independence, exact-parent revision spoofing, superseded SUPPORT, and graph cycles.
`.github/workflows/catalyst-context-gate.yml` makes the adversarial suite permanent for changes to the Catalyst context contract surface.

### Next authorized step
Catalyst Context Engine v1 Part 2 may implement the canonical event resolver / revision resolver / shared-origin adapter against this contract. It must not expose private Scanner weights, thresholds, ranking logic, or promotion/demotion rules.


## Final Catalyst Part 1 Freeze Audit — 2026-09-30
Status: FROZE on PR #12 after adversarial hardening.

Freeze audit closed additional false-pass surfaces found during final review:
- anchorFacts is now hash-bound; silent canonical-thesis mutation fails;
- sourceClass / verificationStatus / evidenceStatus are strict enums;
- observation identity is globally unique within an artifact;
- source locator completeness is enforced;
- observedAt cannot predate publishedAt or exceed artifact asOf;
- firstObservedAt must equal the earliest observation time;
- revision content hashes and exact-parent lineage are validated;
- eventAnchorId collisions and multi-event related cycles fail closed;
- non-current missingness states cannot smuggle active events;
- shared-origin is no longer trusted as self-declaration: originFactIds are intersected automatically with FUNDAMENTALS/PRICE domainEvidenceRefs, and sharedOriginDomains must equal the computed result.

Final adversarial matrix covers rumor laundering, derivative/syndication laundering, automatic FUNDAMENTALS/PRICE shared-origin detection, spoofed shared-origin declarations, exact-parent revision spoofing, superseded SUPPORT, canonical-thesis mutation, source semantic aliases/completeness, duplicate observation identity, future PIT evidence, first-observed spoofing, missingness smuggling, revision hash aliases, event-anchor collisions, and related-event cycles.

CI evidence at freeze:
- Catalyst Context Integrity Gate / adversarial: PASS.
- Scanner Public Contract & Smoke Gate: PASS, including Scanner publication-boundary adversarial attack.

Part 1 is frozen as the public Catalyst evidence-integrity contract. Part 2 may implement resolver/adapters against this frozen boundary; any semantic contract change requires explicit versioning rather than silent mutation.


## Final Catalyst Part 2 Freeze Audit — 2026-09-30
Status: FROZE & MERGED via PR #13 (merge 7b36e62d).

Closed freeze attacks:
- eventAnchorId remains stable across later PIT snapshots for the same canonical economic event;
- prior revisionId remains stable when a later exact correction is appended;
- recursive anchor canonicalization and NFKC/whitespace normalization prevent key-order and Unicode compatibility aliases from splitting identity;
- same-timestamp/conflicting authoritative content cannot silently become a revision; exact correction lineage is required;
- correction forks, cross-event correction references, duplicate observation replay, invalid/future timestamps and cross-ticker observations fail closed;
- malformed originFactIds/domainEvidenceRefs are rejected before shared-origin intersection;
- FUNDAMENTALS/PRICE shared origin remains exact opaque-ID intersection; private fact-ID construction is outside the public resolver;
- resolver and frozen validator now share recursive canonical hash semantics;
- nested-anchor resolver output is explicitly regression-tested against the frozen validator.

Final SHA gate evidence:
- Catalyst Context Resolver Gate: PASS.
- Frozen Part 1 adversarial regression inside Resolver Gate: PASS.
- Catalyst Context Integrity Gate: PASS.

Part 2 is frozen. Future resolver semantic changes require explicit versioning or a separately reviewed contract change.


## Final Catalyst Part 3 Freeze Audit — 2026-09-30
Status: FROZE & MERGED via PR #14 (merge 9672194c).

Closed freeze attacks:
- provenanceFamilyId remains stable when later derivative observations are appended to a snapshot;
- origin binding is immutable across ticker, observation identity, source locator, content hash and observedAt;
- 20-source syndication fan-out collapses to one provenance family;
- trusted root classes are locked to PRIMARY/CORRECTION and cannot be overridden by caller input;
- CORROBORATION/RUMOR cannot launder themselves into independent roots;
- derivative lineage rejects unknown, future, self/cyclic and unproven origins;
- consumption receipts bind ticker + eventAnchorId + factId + domain + consumer artifact + consumer revision + consumer snapshot hash + consumedAt;
- one fact cannot bind to multiple Catalyst event anchors inside a proof artifact;
- receipt lifecycle is an immutable exact-parent chain with ACTIVE/SUPERSEDED/REVOKED semantics;
- only the unique ACTIVE tip proves current shared-origin consumption; a REVOKED tip proves none;
- receipt forks, time rollback, lineage-key mutation, duplicate IDs and stale ACTIVE ancestors fail closed;
- bare fact-ID intersection remains insufficient Part 3 consumption proof;
- the same economic fact may have FUNDAMENTALS and PRICE receipts, but remains one fact with domain-specific consumption evidence rather than multiple Catalyst confirmations.

Final gate evidence on executable head:
- Catalyst Part 3 provenance/consumption adversarial suite: PASS.
- Frozen Part 2 resolver regression: PASS.
- Frozen Part 1 integrity regression: PASS.

Part 3 is frozen. Future provenance/receipt semantic changes require explicit versioning or a separately reviewed contract change.


## Final Catalyst Part 4 Freeze Audit — 2026-09-30
Status: FROZE & MERGED via PR #15 (merge 105f696b).

Part 4 is the PIT temporal-truth layer only. No Scanner score, rank, weight, attractiveness threshold, trade signal, or promotion/demotion rule enters this layer.

Closed freeze attacks:
- knowledge-time assertedAt and effective-time are distinct; future-known backdated assertions cannot rewrite historical snapshots;
- lifecycle assertions are immutable-hash bound directly to ticker, eventAnchorId and exact payload;
- assertion replay across ticker fails even when a foreign event object is supplied;
- lifecycle mutations require exact-parent lineage; gaps, cross-event parents and time rollback fail closed;
- materialUntil extension cannot silently resurrect stale evidence without explicit lineage;
- same-time contradictory assertions fail closed;
- self-supersession and supersession cycles fail closed;
- A→B→C remains auditable; a withdrawn terminal successor does not leak CURRENT materiality;
- source failure remains SOURCE_UNAVAILABLE, never NO_MATERIAL_EVENT;
- no hidden stale-after-N-days rule exists; materialUntil is upstream assertion data;
- output is deterministic under input reordering;
- every PIT result carries deterministic snapshotHash over canonical lifecycle body;
- later knowledge creates a new snapshot identity rather than mutating an earlier asOf snapshot.

Final gate evidence: Part 4 PASS; frozen Part 3 PASS; frozen Part 2 PASS; frozen Part 1 PASS; overall gate SUCCESS.

Part 4 is frozen. Future lifecycle semantic changes require explicit versioning or separately reviewed contract change.


## Scanner ↔ Catalyst Synthesis Boundary Final Freeze — 2026-09-30
Status: FROZE & MERGED via PR #16 (merge 5c0e874f6e800e5030de055cbde3c5fafddafe7a).

This is a boundary adapter, not Catalyst Part 5 and not an Opportunity Engine. Frozen Catalyst Parts 1–4 project one lossy categorical Catalyst evidence family into private Scanner synthesis.

Final Deep QC closed: MATERIAL_CATALYST laundering via mismatched event identity; CURRENT context/lifecycle disagreement; NO_MATERIAL_EVENT with hidden CURRENT event; shared-origin FUNDAMENTALS/PRICE double-confirmation; raw fact/provenance/receipt/event identity leakage; dynamic reason/caveat code misuse; lifecycle snapshot substitution; frozen-context substitution via contextBindingHash; output/sourceBinding field drift; and mini-Opportunity-Engine semantics such as score/rank/weight/threshold/confidence/promotion/trade signals.

Final allowed projection remains categorical only: SUPPORTIVE, LIMITED, NOT_AVAILABLE plus CURRENT/STALE/NO_MATERIAL_EVENT/SOURCE_UNAVAILABLE and hard-allowlisted semantic reason/caveat codes. No counts or numeric evidence strength cross the boundary.

Final gates: synthesis boundary PASS; Catalyst Parts 1–4 regressions PASS; Scanner publication boundary PASS; Scanner Public Contract & Smoke Gate PASS; Catalyst PIT Lifecycle Gate PASS.

Boundary v1 is FROZEN & MERGED. Future semantic expansion requires explicit versioning. No Catalyst Part 5 is authorized or needed.

Next continuation point: return to Scanner product completion. Consume the frozen Quality + Valuation + Price + Catalyst evidence boundaries through PRIVATE Scanner synthesis; do not reopen Catalyst Parts 1–4 or the Synthesis Boundary unless a demonstrated regression requires an explicitly reviewed/versioned change.


## SEO Formula Documentation checkpoint — 2026-10-03
Status: AUTHORIZED — editorial/SEO layer only; frozen Fair Value semantics remain unchanged.

### Strategy
CekValuasi will build a two-way documentation/SEO bridge between the canonical Fair Value product and reader-facing research articles:
Google/Search → SEO formula/article → Fair Value Analyzer → “how this is calculated” contextual link → canonical explanatory article.

### Governance
- Article formulas must be derived from the actual production engine implementation, not generic internet formulas presented as CekValuasi behavior.
- Editorial work must not modify Fair Value formulas, weights, QC, model inclusion, canonical data, Scanner private moat, or QSTP calculations.
- Formula inventory must classify methods as ACTIVE/OUTPUT-CAPABLE, CANDIDATE/FALLBACK, or DIAGNOSTIC/NOT-ACTIVE before publication claims are made.
- Each method article should explain: purpose, formula, variables, source/input meaning, worked example, applicability, limitations, interpretation, and how CekValuasi uses the method where public-safe.
- Pillar articles may summarize several methods but must link to dedicated method articles rather than duplicating their full territory.
- Product intent boundaries remain: /scanner/ = discovery; /fair-value/ = valuation; /qstp.html = risk/position planning; /riset/ = educational/research documentation.

### Initial code-grounded formula inventory
Verified from current public engine code:
- Historical P/E 3Y and 5Y: EPS TTM × adaptive historical P/E band; output-capable candidate method.
- Historical EV/EBITDA: historical EV/EBITDA band converted back to equity value per share using EBITDA, net debt/cash and shares; output-capable candidate method for non-financial sectors when evidence is sufficient.
- Graham Number: sqrt(22.5 × EPS × BVPS), with bear/base/bull cross-check bands; output-capable candidate method when EPS and BVPS are positive/validated.
- Historical Dividend Yield: latest DPS divided by historical yield band; output-capable candidate method when dividend history is sufficient.
- Composite Fair Value: combines QC-passing methods across at least two independent method families using normalized method weights; this is a product methodology article, not a generic single-formula article.
- PBV, DCF and FCF Yield appear in diagnostics/input readiness in the inspected augmentation layer; do not describe them as active production Fair Value methods until the canonical implementation path is separately verified.

### SEO architecture direction
Preferred editorial namespace: /riset/ with clusters such as /riset/valuasi-saham/, /riset/fundamental/, /riset/saham-syariah/, /riset/risiko-trading/, and /riset/metode-riset/.

Next continuation point: complete the canonical Formula Inventory across the remaining valuation pipeline, map each verified method to one primary SEO URL/search intent, then run Deep SERP analysis before drafting the first article.


## Valuation SEO audit v1 — 2026-10-03
Status: audited for editorial SEO; valuation semantics unchanged.

Canonical documentation source: production generated-data pipeline (generate_data.py plus production post-processing). Do not mix reader-facing formula claims with the older/alternate app.py Flask path.

Verified output-capable methods and primary URLs:
- DCF -> /riset/valuasi-saham/dcf-harga-wajar-saham/
- FCF Yield -> /riset/valuasi-saham/fcf-yield-saham/
- Historical P/E 3Y + 5Y -> one owner URL: /riset/valuasi-saham/per-historis-harga-wajar-saham/
- Historical PBV 5Y -> /riset/valuasi-saham/pbv-historis-harga-wajar-saham/
- Historical EV/EBITDA -> /riset/valuasi-saham/ev-ebitda-harga-wajar-saham/
- Graham Number -> /riset/valuasi-saham/graham-number/
- Historical Dividend Yield -> /riset/valuasi-saham/dividend-yield-historis-harga-wajar/
- Composite Fair Value methodology -> /riset/valuasi-saham/cara-cekvaluasi-menghitung-harga-wajar/

Supporting documentation planned for EPS, BVPS, FCF, EBITDA, Enterprise Value, Cost of Equity, Terminal Value, and Margin of Safety.

SERP/content-gap decision: do not compete primarily with generic multi-method list articles. CekValuasi should own code-grounded worked documentation: actual production formula, validated inputs, applicability/failure conditions, robust historical bands, QC, and the path from method output to the displayed Fair Value. Historical P/E 3Y and 5Y must share one page. Graham Number must not be conflated with the separate Benjamin Graham growth/yield formula. Historical Dividend Yield must distinguish ordinary dividend-yield calculation from reverse historical-yield fair-value reconstruction.

FIRST SEO URL authorized for drafting:
/riset/valuasi-saham/cara-cekvaluasi-menghitung-harga-wajar/
Purpose: methodology hub and trust bridge from Fair Value results. It explains model families, QC and publication conditions, then links to dedicated formula pages. It must not imply every method is used for every ticker.

Planned child sequence after hub: Historical P/E -> DCF -> Historical PBV -> Graham Number -> Historical EV/EBITDA -> Historical Dividend Yield -> FCF Yield, followed by supporting-input articles according to internal-link demand and SERP validation.

Next: draft only the first URL, then formula-parity, worked-example arithmetic, title/H1/meta, canonical/schema/sitemap, internal-link, responsive and publication gates before moving to article #2.


## SEO Article #1 freeze — 2026-10-03
URL: /riset/valuasi-saham/cara-cekvaluasi-menghitung-harga-wajar/
Status: FROZEN after formula-parity and integration gate.
- Published methodology hub with canonical, Article schema, Breadcrumb schema, disclaimer and Fair Value CTA.
- Added to sitemap.xml.
- Added contextual link from /fair-value/ results: “Bagaimana harga wajar ini dihitung?”
- Two-way product/documentation loop verified.
- Wording aligned with current UI behavior: full Composite FV requires >=2 methods from >=2 independent families; an indicative estimate may still be shown with lower confidence when valid methods exist but independence evidence is insufficient.
- No links to unpublished child formula articles.
- No Scanner/private-engine logic exposed.

Next: Article #2 owner URL /riset/valuasi-saham/per-historis-harga-wajar-saham/. Run Deep SERP specifically for historical P/E intent, then draft from adaptive_pe.py + generate_data.py parity. Do not split 3Y and 5Y into separate URLs.


## SEO Article #2 freeze — 2026-10-03
URL: /riset/valuasi-saham/per-historis-harga-wajar-saham/
Status: FROZEN after Deep SERP, adaptive-P/E formula parity and contextual-link gate.
- One owner page covers Historical P/E 3Y + 5Y; no split URLs.
- Documents production adaptive pipeline: EPS multi-source validation, 0.5x–500x observation guard, minimum 20 initial observations, 5th/95th percentile trim, minimum 12 post-trim, log-MAD robust filter, minimum 10 final observations, median base, robust sigma=max(1.4826*MAD, 8% of median), Bear/Base/Bull, and 0.05x–5x market-price economic sanity.
- Documents HIGH MULTIPLE behavior: >60x may survive adaptive distribution but confidence is reduced and warning exposed.
- Explicitly states P/E 3Y and 5Y share the earnings family and do not count as two independent valuation families.
- Added sitemap entry; methodology hub now links to Article #2.
- Fair Value method table now renders “ⓘ Cara hitung” only for Historical P/E rows whose documentation is published.
- No links were added for unpublished formula articles.

Next SEO owner: /riset/valuasi-saham/dcf-harga-wajar-saham/. Audit DCF production implementation + Deep SERP before drafting Article #3.


## SEO Article #3 freeze — 2026-10-03
URL: /riset/valuasi-saham/dcf-harga-wajar-saham/
Status: FROZEN after production-formula audit, Deep SERP and contextual-link gate.
- Documentation explicitly follows CekValuasi production implementation rather than presenting a generic FCFF/WACC template as engine behavior.
- Production DCF documented: positive FCF/share prerequisite; historical growth from median available CAGR of NI/revenue/FCF with 8% fallback; sustainable-growth proxy from ROE and normalized payout; final growth clamp -3%..18%; cost of equity clamp(6.5% + beta*7.38%, 10.5%, 22%) with beta fallback 1; terminal growth 3.5%; five-year explicit projection; perpetuity terminal value; k-terminal guard >1 percentage point.
- Scenario parity: Bear max(-2%, growth-5pp), min(24%, ke+2pp); Base growth/ke; Bull min(22%, growth+4pp), max(9.5%, ke-1.5pp).
- Documents >70% terminal-value-share warning and DCF relevance reduction before sector adjustment.
- Documents common economic sanity 0.05x..5x market price and cashflow family relationship with FCF Yield.
- Added sitemap, methodology-hub child link, and Fair Value per-method “ⓘ Cara hitung” link for DCF only after article publication.

Next SEO owner: /riset/valuasi-saham/pbv-historis-harga-wajar-saham/. Audit Historical PBV 5Y production formula + Deep SERP before Article #4.


## SEO Article #4 freeze — 2026-10-03
URL: /riset/valuasi-saham/pbv-historis-harga-wajar-saham/
Status: FROZEN after production-formula audit, Deep SERP and contextual-link gate.
- Historical PBV 5Y documented separately from adaptive P/E; no false reuse of P/E minimum-dispersion logic.
- Production parity: BVPS from positive equity/shares after FX normalization where applicable; current P/BV guard 0.2x..12x; >=4.5 years history; >=30 initial observations; P5/P95 trim; >=10 post-trim; base=median; robust sigma=1.4826*MAD; Bear floor 0.2x; Bull cap 12x; all scenario FV outputs subject to 0.05x..5x market-price sanity.
- Explicitly documents that core PBV currently has no adaptive-P/E 8% minimum dispersion.
- Sector relevance documented as engine policy, not universal investing truth: Finance PBV multiplier 1.55; lower multipliers in several other profiles including Technology 0.25 and Healthcare 0.45.
- Rejects simplistic “PBV <1 means cheap” interpretation.
- Added sitemap, methodology-hub child link, and per-method Fair Value “ⓘ Cara hitung” link only after article publication.

Next SEO owner: /riset/valuasi-saham/graham-number/. Audit Graham augmentation implementation + Deep SERP and explicitly separate Graham Number from the different Graham growth/yield formula before Article #5.


## CekValuasi SEO adoption — Private Moat v3.0 Gate — 2026-10-03
Status: ACTIVE for all indexable /riset/ assets from Article #1 onward.
Source policy: owner-only Private Moat SOP remains outside the public repository. This repository records only the site-specific public-safe application and release state.

Required sequence for each SEO asset:
Opportunity/Deep SERP -> canonical intent ownership -> owner editorial quality gate -> cannibalization decision -> corpus graph -> technical/deployment validation -> public live QC -> GO/FROZEN.

Detailed scoring mechanics and private editorial playbooks remain owner-only and are intentionally not documented in this public repository.

Operational correction: prior Article #1-#4 “FROZEN” labels recorded before adoption are provisional source freezes, not final publication freezes. Final GO/FROZEN requires live-production QC in addition to source/validator/deployment checks.

Public-safe CekValuasi adaptation:
- Formula documentation must be code-grounded to the canonical production valuation pipeline.
- One meaningful formula/search intent has one canonical owner URL; wording variants do not justify new pages.
- Every article must have a page-specific moat based on actual engine behavior, validation/guard logic, worked interpretation, or product workflow—not word count or generic completeness.
- Article formulas may explain public Fair Value behavior, but must not disclose private Scanner weights, thresholds, feature interactions, calibration, ranking logic, persistence, anti-gaming, decision traces, or other reusable private research IP.
- Parent hub for valuation-formula articles: /riset/valuasi-saham/cara-cekvaluasi-menghitung-harga-wajar/ until a broader /riset/ hub is deliberately introduced.
- Formula articles must link to /fair-value/ and receive inbound discovery from the methodology hub and, when the documented method is published, its Fair Value method row.
- No per-method “Cara hitung” link may point to an unpublished child page.

Article #1-#4 are now under retrospective Private Moat v3.0 re-gate. Final status will be recorded only after AQS, Deep QC, corpus and live-production checks pass.


## SEO Article #1-#4 — Private Moat v3 retrospective release gate — 2026-10-03
Final state: GO / FROZEN for current production semantics.

Owner-only editorial gate: PASS for all four assets. Detailed AQS scoring and Deep-QC mechanics are retained outside public Git history.

Public-safe release evidence:
- Article #1 methodology hub: canonical intent owner for how CekValuasi forms multi-model Fair Value; distinct moat is first-party production methodology + QC/failure-state explanation + direct product bridge.
- Article #2 Historical P/E: canonical owner for CekValuasi Historical P/E 3Y/5Y; distinct moat is adaptive production band, multi-source EPS validation, robust outlier handling and HIGH MULTIPLE behavior. Cannibalization decision: one URL owns both 3Y and 5Y.
- Article #3 DCF: canonical owner for CekValuasi DCF implementation; distinct moat is explicit documentation of the actual FCF/share + cost-of-equity production model rather than substituting a generic FCFF/WACC article.
- Article #4 Historical PBV: canonical owner for Historical PBV 5Y; distinct moat is robust 5Y P/BV reconstruction, data/observation guards and transparent sector-relevance policy. It remains separate from Historical P/E because user input, evidence family and decision path differ.
- Parent/inbound graph: methodology hub -> published child formula pages; each child -> methodology hub + /fair-value/; /fair-value/ exposes contextual documentation links only for published method pages.
- Sitemap/indexability: PASS. Canonicals and robots directives verified live.
- Live-production QC: PASS across methodology hub, Historical P/E, DCF, Historical PBV and Fair Value integration. Public render, navigation/TOC, CTAs, method documentation links, tables and responsive presentation showed no blocking defects.
- Private-moat boundary: PASS. No Scanner private weights, thresholds, feature interactions, calibration, persistence, ranking equations or decision traces were added.

Corpus P2 (non-blocking): /riset/ and /riset/valuasi-saham/ are not yet dedicated editorial hub pages. The methodology article remains the canonical parent for this formula cluster until a broader research hub is deliberately built. Do not create an empty/thin hub merely to satisfy hierarchy.

Release rule going forward: Article #5+ cannot receive final GO/FROZEN until the same owner editorial gate, corpus graph, technical validation, deployment and live-production QC pass. Formula/source parity remains mandatory before drafting.


## Private Moat v3 retrospective gate — Articles #1-#4 — 2026-10-03
Audit state: CONDITIONAL PASS / awaiting final live verification after corpus-hub deployment.

Canonical ownership + moat:
1. #1 /cara-cekvaluasi-menghitung-harga-wajar/ — owns CekValuasi multi-model/composite methodology. Moat: code-grounded path from validated inputs and method eligibility through independent-family evidence, normalized weighting, dispersion/agreement and displayed Fair Value.
2. #2 /per-historis-harga-wajar-saham/ — owns Historical P/E 3Y+5Y. Moat: documents adaptive EPS validation, robust historical multiple construction, high-multiple handling and same-family treatment instead of generic PER education.
3. #3 /dcf-harga-wajar-saham/ — owns production DCF. Moat: documents the actual CekValuasi FCF/share + cost-of-equity implementation, scenario parameters, terminal-value diagnostic and production guards rather than substituting a generic FCFF/WACC template.
4. #4 /pbv-historis-harga-wajar-saham/ — owns Historical PBV 5Y. Moat: documents production BVPS normalization, 5Y robust P/BV band, observation/trim/MAD guards and sector relevance while rejecting simplistic PBV<1 interpretation.

Cannibalization decisions: KEEP all four. #1 remains parent methodology owner; #2-#4 are child formula owners. P/E 3Y and 5Y remain merged into one canonical owner. No competing generic formula pages authorized.

AQS v3 retrospective score (100-point site-specific rubric: intent 15, truth/formula fidelity 20, moat/originality 15, reader utility 15, trust/safety 10, corpus/internal links 10, technical SEO 10, live readiness 5):
- #1: 93/100
- #2: 94/100
- #3: 95/100
- #4: 94/100
All exceed AQS>=80. Scores do not by themselves authorize publication.

10-layer Deep QC:
1 Truth/evidence PASS — production-code-grounded claims audited per article.
2 Intent PASS — one owner per substantive intent.
3 Reader-first PASS — direct explanation, worked interpretation and failure conditions.
4 Moat PASS — page-specific production behavior; not generic word-count expansion.
5 Safety/trust PASS — educational framing, uncertainty/limitations, no BUY/SELL promise.
6 Search architecture PASS after corpus patch.
7 Cannibalization PASS — parent vs child territory explicit; P/E windows merged.
8 Corpus appearance PASS after source patch; static research hubs added.
9 Monetization PASS — no ad/affiliate insertion compromises article purpose.
10 Live reality CONDITIONAL — Articles #1-#4, canonical metadata, robots and sitemap were publicly reachable; audit found /riset/ and /riset/valuasi-saham/ returning 404, so final freeze was withheld. Source patch now adds both static hubs and sitemap entries; production recheck is required after deployment.

Corpus patch:
- Added /riset/ as static Research Library hub.
- Added /riset/valuasi-saham/ as static valuation cluster hub linking #1-#4.
- Added both hubs to sitemap.
- This also supplies non-JavaScript discovery because Fair Value per-method “Cara hitung” links are runtime-generated after ticker rendering and should not be the sole crawl path.

Private-moat check: PASS. Public pages expose public Fair Value calculation behavior needed for auditability but do not publish Scanner proprietary weights/thresholds/feature interactions/calibration/ranking/persistence/anti-gaming/decision traces.

Release rule: Articles #1-#4 become FINAL GO/FROZEN only when live recheck confirms both new hubs resolve successfully, sitemap includes them, article canonicals remain self-referential, and existing article/tool routes have no regression.


## Private Moat v3 FINAL baseline — Articles #1-#4 — 2026-10-03
Status: FINAL GO / FROZEN.
- GitHub Pages latest deployment succeeded after explicit-hub routing patch.
- Live /riset.html: 200, self-canonical, index/follow, links to valuation hub and Fair Value.
- Live /valuasi-saham.html: 200, self-canonical, index/follow, static links to canonical owners #1-#4 and Fair Value.
- Live sitemap: 15 URLs including both explicit hubs and all four article owners.
- Articles #1-#4 remain publicly reachable with self-referential canonicals and no observed route regression.
- Retrospective AQS remains #1 93, #2 94, #3 95, #4 94; 10-layer Deep QC now closes PASS including live reality.
- Directory-index hub routes that returned 404 are superseded by explicit /riset.html and /valuasi-saham.html. Do not restore them as canonical corpus routes without a separate routing test.
- Freeze boundary: no further substantive edits to #1-#4 unless factual production parity, broken link/schema, material search-intent drift, or another P0/P1 regression is demonstrated.

## SEO Article #5 opportunity gate — Graham Number — 2026-10-03
Status: AUTHORIZED TO DRAFT under Private Moat v3; not yet FROZEN.
Canonical owner: /riset/valuasi-saham/graham-number/
Intent owner: explain the Graham Number actually used by CekValuasi, its inputs, production scenario treatment, applicability and limitations.
Moat sentence: Unlike generic Graham calculators, the CekValuasi owner documents the exact production cross-check built from validated EPS/BVPS, the 80/100/120 Bear-Base-Bull treatment, confidence/relevance role, economic sanity/outlier gates, and how it participates as the fundamental family in Composite Fair Value.
SERP separation rule: Graham Number sqrt(22.5*EPS*BVPS) is the owner territory. Do not conflate it with the separate growth/bond-yield Graham formula EPS*(8.5+2g)*4.4/Y, which is not a production CekValuasi method.
Production parity: requires EPS>0 and BVPS>0; Base=sqrt(22.5*EPS*BVPS); Bear=.8*Base; Bull=1.2*Base; confidence=.60; relevance=.55; family=fundamental; general 0.05x-5x market-price sanity plus composite robust-outlier rules still apply.
Next gate: draft -> AQS -> 10-layer Deep QC -> corpus/tool integration -> live-production QC -> GO/FROZEN.
