# SEO Architecture Governance — CekValuasi

## Public architecture
/ — brand/product gateway
/saham/{ticker}/ — canonical ticker valuation report
/sektor/{slug}/ — useful sector discovery/analysis hub
/metodologi/ — methodology and limitations

Controlled acquisition layers:
- Valuation content/tool pages
- Syariah Discovery content/tool pages
- Risk content/tool pages

The canonical launch registry and intent owners are maintained in `SEO-OPPORTUNITY-MAP-v1.md`.

## Search-to-product architecture
Search → Understand → Verify → Plan.
Every acquisition page must have a legitimate next-decision bridge to a CekValuasi product or canonical supporting page.

## Intent ownership
Exactly one canonical URL owns each material search intent. A synonym is not automatically a new page. Before creating a URL, compare its intended answer, SERP composition, and user task with existing owners.

If two proposed pages would satisfy substantially the same user task, default to one stronger page unless live SERP evidence supports separate intent.

## Indexation rules
Index only pages with substantive, current, internally consistent content. Error, empty, duplicate, stale-without-context, and thin states must not become indexable inventory.

## Programmatic SEO guard
Ticker pages must expose genuine ticker-specific data/evidence. Template uniqueness alone is not content value. Keyword permutations, ticker substitutions, or near-duplicate explanatory text do not justify indexation.

## Canonical rules
Exactly one canonical URL per public entity/page intent. Query-string research views must not compete with permanent pages after migration.

## Internal linking
Links must follow user decisions, not keyword stuffing:
Discovery → valuation → interpretation/methodology → risk planning.
Use descriptive anchors where natural. Do not create circular boilerplate link blocks merely to increase link count.

## Sitemap gate
Only canonical, indexable URLs that passed publication gates. Sitemap, canonical, internal links, structured data, and actual HTTP destination must agree.

## Scaling guard
Scaling from 10 to 50–100 pages is permitted only by evidence-backed expansion. Page count is never a KPI by itself. Failed, redundant, or weak-opportunity candidates remain unpublished.
