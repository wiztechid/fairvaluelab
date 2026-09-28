# Current State — FairValueLab / CekValuasi Preparation

Updated: 2026-09-28

## Production baseline
- FairValueLab remains the current production baseline while the CekValuasi migration is prepared incrementally.
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

## CekValuasi homepage direction
The future homepage should operate as a product gateway rather than replacing the valuation engine prematurely.

Proposed public positioning:
> **Valuasi dulu. Atur risiko. Baru ambil keputusan.**

Reader journey:
**Pilih saham → Cek valuasi → Pahami harga → Atur risiko → Simpan trading plan**

Homepage implementation remains pending. Until separately approved, do not replace the current production `index.html`.

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
CekValuasi migration remains incremental. Existing production behavior stays authoritative until an explicit migration gate promotes a replacement.

## Open P0 items
- Establish one canonical public valuation engine/output.
- Harden data provenance and freshness metadata.
- Establish regression baseline before formula changes.
- Separate public presentation migration from valuation semantics.
- Preserve PIT PROVISIONAL vs VERIFIED distinction.

## Freeze rule
No formula rewrite, URL migration, workflow replacement, production deletion, homepage replacement, or private-moat disclosure is implied by this document.
