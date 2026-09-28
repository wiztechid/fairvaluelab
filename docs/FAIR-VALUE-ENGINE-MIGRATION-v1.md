# Fair Value Engine Migration Plan v1

Status: REHEARSAL on feature/cekvaluasi-homepage. Production root remains unchanged.

## Objective
Move the existing Fair Value engine from root `/index.html` to `/fair-value/index.html` without changing valuation semantics or runtime behavior. Only after parity passes may a separate approved change promote the CekValuasi homepage to root.

## Migration invariant
Migration and redesign are separate changes. Do not rewrite formulas, UI behavior, ticker state, valuation logic, or dynamic ticker SEO semantics during parity migration.

## Current dependency inventory
### Data/runtime
The root engine performs seven fetch families:
- data/{ticker}.json
- data/golden_zone/{ticker}.json
- data/market_actors/{ticker}.json
- data/sector_mos.json
- data/{ticker}.json (additional runtime path)
- data/catalysts/{ticker}.json
- ./data/summary.json

At /fair-value/ these resolve through ../data/.

### Static dependencies
- universe.html → ../universe.html
- methodology.html → ../methodology.html
- assets/saweria-qr.svg → ../assets/saweria-qr.svg

### URL state
Preserve:
- ?ticker= query contract
- URLSearchParams(location.search)
- localStorage key wiss:lastTicker
- history.replaceState
- popstate handling
- internal ?ticker= links

### SEO/meta
Static tool canonical/OG base for the rehearsal is /fair-value/.
Dynamic ticker metadata currently points to /harga-wajar-saham/{ticker}/. Preserve this behavior during parity; review its long-term SEO ownership separately after migration.

### Structured data
SoftwareApplication JSON-LD remains behavior-equivalent during migration. Brand/schema redesign is outside parity scope.

### QSTP bridge
The current Fair Value root has no direct QSTP link. Do not add one during parity migration. Product-journey changes require a separate UX change gate.

### Responsive/mobile
All existing CSS/media-query behavior must remain unchanged except for URL/path adjustments.

## Expected source deltas
Only:
1. data paths gain ../
2. root static links/assets gain ../
3. static Fair Value canonical/OG URL becomes /fair-value/

After reversing those expected deltas, fair-value/index.html must normalize exactly to the source root index.html.

## Smoke / parity gate
Required before root switch:
- source normalization parity = 100%
- all seven fetch contracts resolve to existing root data
- summary search loads
- ticker direct query works
- ticker switch updates query without navigation loss
- browser back/popstate works
- sector MOS ticker links remain local to /fair-value/?ticker=
- universe/methodology links resolve
- QR asset resolves
- canonical/OG static tool URL is /fair-value/
- dynamic ticker metadata behavior matches baseline
- mobile breakpoints remain present
- no valuation formula/DOM/JS behavior change
- production root index.html remains unchanged during rehearsal

## Switch sequence (separate explicit approval)
1. Freeze a known-good Fair Value baseline.
2. Verify /fair-value/ on branch/deployment.
3. Run runtime parity on representative tickers and error/review states.
4. Promote CekValuasi homepage to root.
5. Promote /fair-value/ as the Fair Value tool canonical.
6. Update homepage/product navigation, sitemap, canonical and internal links in one controlled migration.
7. Re-run SEO, runtime, mobile and QSTP journey regression.
8. Roll back root switch if any P0 engine or routing contract fails.

## Rollback
The current root index.html remains the known-good baseline until the switch is explicitly approved. Do not delete it as part of rehearsal.

## Out of scope
- formula changes
- valuation model changes
- ticker-page SEO redesign
- Scanner implementation
- QSTP redesign
- content-page publication


## Runtime Parity Gate v1 — 2026-09-28

Status: CONDITIONAL PASS — CI GREEN; final browser-preview interaction gate remains before root switch.

Evidence:
- GitHub Actions run 36414113816 completed successfully on commit 387147ac1c11848a2ac6a8e237988a592f622811.
- checkout, Node setup, and fair-value-migration-smoke-gate.js all passed.
- normalized source parity remains enforced at 100%.
- executable inline JavaScript is syntax-checked separately from JSON-LD; JSON-LD is parsed as JSON.
- seven migrated fetch contracts are enforced.
- representative SIAP, INDIKATIF, REVIEW, REFERENSI, and BELUM_DINILAI records are required by the gate.
- URL-state, fallback, canonical, dependency, and responsive contracts are enforced.
- production root index.html remains untouched by this branch.

### Pre-switch synchronization requirement
At this checkpoint the feature branch is one commit behind main. Before any root promotion, synchronize/reconcile the latest main into the migration branch, rerun the full migration smoke gate, and confirm normalized parity against the then-current production Fair Value baseline. Do not assume today's parity remains valid after main changes.

### Remaining final interaction gate
Before promotion, use a deployed/previewable branch build to click-test:
1. initial /fair-value/ load
2. direct /fair-value/?ticker=<SIAP>
3. representative INDIKATIF, REVIEW, REFERENSI, BELUM_DINILAI states
4. ticker search/change and URL replacement
5. browser back/popstate
6. Golden Zone available/fallback
7. Market Actor available/fallback
8. Catalyst available/404
9. sector MoS links
10. universe/methodology/QR links/assets
11. mobile viewport behavior
12. console/network: no migration-caused P0 errors

Root switch remains prohibited until this interaction gate passes after branch synchronization.


## Post-sync parity checkpoint — 2026-09-28
- Latest main synchronized into this migration branch via PR #7 (main → feature only).
- Sync merge commit: 6b6018c66810fe77b7b235711b49867298338d23.
- Branch state immediately after sync: behind main = 0.
- The incoming main change was a canonical data refresh; production root index.html was not changed by the migration work.
- Fair Value Migration Smoke Gate run 36414750958 completed SUCCESS after synchronization.
- Therefore structural/source parity and runtime-contract CI are revalidated against the latest main baseline/data at this checkpoint.
- Root promotion is still prohibited until the deployed browser interaction gate passes.


## FINAL MIGRATION READINESS — 2026-09-28

Status: MIGRATION READY.

Final evidence:
- latest main synchronized: behind main = 0 at readiness checkpoint
- production root index.html remains untouched by migration branch
- structural/source normalization parity: PASS
- Fair Value Migration Smoke Gate after latest-main sync: PASS (run 36414750958)
- Fair Value Browser Interaction Gate: PASS (run 36415077438)
- Chromium installed and executed the branch locally over HTTP
- representative SIAP / INDIKATIF / REVIEW / REFERENSI / BELUM_DINILAI direct-ticker states exercised
- ticker change and URL-state behavior exercised
- browser navigation did not break the application
- optional Golden Zone / Market Actor / Catalyst 404s are explicitly attributed and allowed only for known graceful-fallback paths; unexpected local HTTP errors remain fatal
- universe, methodology and QR dependencies verified
- sector MoS local ticker-link contract verified when present
- 390x844 mobile viewport verified without migration-caused horizontal overflow
- migration-caused local request failures and unexpected console errors remain fatal

MIGRATION READY does not authorize production promotion. Root switch remains a separate controlled change requiring explicit approval. At promotion time rerun both smoke and browser gates against the exact promotion commit.
