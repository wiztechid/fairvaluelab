# Current State — CekValuasi

Updated: 2026-09-28

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


## Editorial Research Theme — checkpoint 2026-09-29

Status: v1.1 built and visually previewed; NOT promoted to production.

Branch:
- feature/cekvaluasi-editorial-theme
- Theme implementation commit: 138378d3ce75c1bafe5d1d965f8d1db6aa9526cf

Preview:
- /preview/editorial-v1/ is an isolated noindex,nofollow snapshot published only for visual review.
- Production root remains the previously promoted CekValuasi homepage until a separate approval promotes the editorial theme.

### Product journey — locked direction
Public journey:
1. Scanner / Discover — identify DES candidates worth researching.
2. Fair Value / Verify — test reasonable value, Margin of Safety, evidence/data quality and price context.
3. QSTP / Plan — translate a chosen setup into position size and portfolio-risk consequences.
4. Monitor — revisit when price, evidence or conditions change.

Scanner remains IN DEVELOPMENT. Therefore the homepage may show Scanner as Step 01 conceptually, but the primary usable hero CTA remains Fair Value until Scanner is live. Do not imply Scanner is currently operational.

### Editorial visual DNA
Direction: financial research desk / editorial investment research, not generic SaaS landing page.
Preserve:
- strong typography and editorial rules
- numbered research instruments 01/02/03
- limited emerald as signal rather than decorative gradient
- distinct visual grammar per instrument:
  - Scanner = evidence/state rails
  - Fair Value = valuation range rail
  - QSTP = risk allocation strip
- dark signature decision-sequence section
- manifesto: “Angka tanpa penjelasan tidak cukup.”
- brand discipline:
  - Bukti sebelum kesimpulan.
  - Valuasi sebelum euforia.
  - Risiko sebelum posisi.

Avoid returning to:
- excessive rounded white cards
- pill overload
- generic gradients/shadows
- emoji/icon-led product identity
- visually identical product cards
- generic AI/SaaS landing-page grammar

### v1.1 polish already applied
- product order corrected to Scanner → Fair Value → QSTP
- section headline: “Scan. Nilai. Rencanakan. Satu disiplin keputusan.”
- signature sequence: “Scan peluang. Uji nilai. Batasi risiko.”
- mobile micro typography increased
- instrument numbers strengthened
- Scanner rail/readability improved
- QSTP risk strip readability improved
- product body copy increased
- principle hierarchy strengthened
- manifesto differentiated
- footer strengthened
- rule density reduced relative to v1

### Next QC
Before any production promotion, perform Deep Reader-First + Visual QC of v1.1 content and details, especially:
- first-screen comprehension
- Indonesian terminology consistency vs unnecessary English
- Scanner explanation clarity while still unavailable
- microcopy hierarchy and legibility on mobile
- instrument visualization semantics
- section transitions/rule density
- manifesto/scanner-preview duplication
- footer/disclaimer readability
- accessibility/tap targets
- desktop balance
- regression against canonical/routes/SEO contracts

### Freeze boundary
Theme work may change homepage presentation and reader-first microcopy only. Do not change Fair Value formulas/engine, canonical data, QSTP calculations, DES universe, Scanner proprietary logic, product routes, SEO canonical contracts, sitemap semantics, or permanent gates without separate explicit approval.


## Editorial Research Theme v1.2 — Content & Micro-Detail Polish — 2026-09-29
Status: built on editorial branch and published to isolated noindex preview; NOT promoted to production.

Scope was polish only, not redesign:
- retained editorial research visual DNA and layout
- retained Scanner → Fair Value → QSTP → Monitor journey
- retained Fair Value as primary usable hero CTA while Scanner is still in development
- clarified Scanner availability and purpose
- replaced avoidable mixed-language/generic SaaS copy with clearer Indonesian
- strengthened evidence/data-quality wording
- clarified Fair Value as an estimate, not certainty
- clarified QSTP as risk-to-position-size workflow
- changed “BUY score” wording to “skor beli”
- improved mobile tap-target/readability details without changing layout
- strengthened footer disclaimer
- preserved canonical, product routes, engine/data/QSTP/Scanner logic and SEO architecture

Intentional investment terms retained where clearer for users: Margin of Safety, stop loss, QSTP, Fair Value.

Theme commits:
- a28b26bba8151a6b0d85980fa25ef36cfb906cd5 — v1.2 content/micro-detail polish
- 14fc5140b8c968bb92a05f629879e629b8d17a0f — residual copy cleanup

Preview remains /preview/editorial-v1/ with noindex,nofollow.
