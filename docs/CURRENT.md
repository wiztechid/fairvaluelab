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
