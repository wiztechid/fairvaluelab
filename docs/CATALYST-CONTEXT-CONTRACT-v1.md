# Catalyst Context Engine v1 — Event Identity, Provenance & Independence Contract

Status: PRE-ENGINE CONTRACT. This does not authorize Opportunity Engine scoring, weights, thresholds, ranking, promotion/demotion logic, or trade signals.

## Trust boundary
Raw observations → canonical event resolver → provenance/revision resolver → shared-origin resolver → sanitized Catalyst Context artifact → strict validator → downstream research context.

## P0 invariants
1. EVENT_IDENTITY — one economic event has one stable eventAnchorId independent of publisher/headline wording.
2. PROVENANCE — SUPPORT identifies source class, locator, observedAt, publishedAt, and verification status.
3. REVISION_LINEAGE — corrections/amendments bind to the exact parent revision; superseded revisions cannot remain active.
4. ONE_FAMILY_INDEPENDENCE — repeated coverage, syndication, mirrors, summaries, and derivative commentary never create independent catalyst confirmations.
5. SHARED_ORIGIN — if the same economic fact is consumed by Fundamentals or Price, Catalyst declares that dependency and cannot present it as an independent confirmation.
6. RUMOR_GUARD — rumor/unverified commentary cannot become SUPPORT because derivative sources repeat it.
7. CANONICAL_THESIS_IMMUTABILITY — event identity cannot be reused after material mutation of issuer, event type, economic subject, or anchor facts.
8. CYCLE_FREE — related-event and revision graphs are acyclic.
9. PIT — an observation affects evaluation only after observedAt; later revisions cannot rewrite historical knowledge.
10. MISSINGNESS — no material event, source unavailable, stale evidence, and not evaluated are distinct states.

## Event anchor
eventAnchorId is an opaque stable identifier for the economic event. It must not be derived solely from headline text, publisher, URL, or publication time. Anchor identity is bound to ticker/issuer, eventType, economicSubject, anchorFactsHash, and firstObservedAt. A changed anchorFactsHash requires explicit revision lineage or a new event anchor; silent mutation fails closed.

## Observation roles
PRIMARY = authoritative origin when available.
CORROBORATION = genuinely separate reporting of the same event; not a second economic event.
DERIVATIVE = syndication, mirror, summary, commentary, or downstream restatement.
RUMOR = unverified claim.
CORRECTION = explicit correction/amendment linked to a prior revision.

Only VERIFIED observations may carry SUPPORT. RUMOR and DERIVATIVE observations cannot self-promote to SUPPORT.

## Shared origin
Each event carries opaque originFactIds. The artifact also carries domainEvidenceRefs for FUNDAMENTALS and PRICE. The validator computes shared origin by exact opaque fact-ID intersection; sharedOriginDomains must equal that computed result. Any non-empty result forces independenceStatus=DEPENDENT_SHARED_ORIGIN. The public contract exposes identity linkage, not the private recipe used to construct fact IDs. Earnings/dividend/corporate-action facts already consumed elsewhere remain useful context but are not another independent vote.

## Revisions
Each revision has revisionId, revisionNumber, parentRevisionId, revisionStatus and contentHash. Revision 1 has no parent; later revisions bind to the immediately preceding revision; only the highest non-withdrawn revision may be ACTIVE; SUPERSEDED revisions cannot provide active SUPPORT.

## Related events
relatedEventIds may express related but distinct events. Self-links, duplicates, unknown targets, and cycles fail closed. Relationship never implies independence.

## Downstream rule
Catalyst Context may affect research context only through separately governed downstream policy. This contract defines no attractiveness score, BUY/SELL semantics, or ranking.
