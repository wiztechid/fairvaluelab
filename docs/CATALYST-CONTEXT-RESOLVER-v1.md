# Catalyst Context Engine v1 — Part 2 Resolver Contract

Status: IMPLEMENTATION BOUNDARY. Part 1 semantics remain frozen.

## Input boundary
The resolver consumes normalized raw observations. Each input observation must provide:
- ticker, eventType, economicSubject;
- anchorFacts object;
- originFactIds (opaque identifiers produced upstream);
- sourceClass and sourceLocator;
- publishedAt and observedAt;
- verificationStatus;
- contentHash;
- optional correctionOfObservationId.

The resolver does not infer Scanner attractiveness, score, rank, BUY/SELL semantics, or private thresholds.

## Canonical event resolution
A canonical event key is built from normalized ticker + eventType + economicSubject + canonical anchorFacts. Publisher, URL, headline wording, and publication time are excluded from event identity.

Observations with the same canonical event key collapse into one event. Distinct anchor facts remain distinct events even when headlines are similar.

## Revision resolution
A new revision is created only when verified PRIMARY/CORRECTION content changes for the same event identity.
- identical authoritative content remains the same revision;
- changed authoritative content creates the next revision;
- the previous revision becomes SUPERSEDED;
- the new revision points exactly to the previous revision;
- derivative/corroborating/rumor observations never create a canonical revision by themselves;
- correctionOfObservationId must resolve within the same event.

## PIT
Only observations with observedAt <= asOf participate. Future observations are excluded, never backfilled into earlier artifacts.

## Shared-origin adapter
The resolver receives domainEvidenceRefs for FUNDAMENTALS and PRICE. It computes sharedOriginDomains from exact intersection with event originFactIds. This adapter does not know or expose the private recipe used to generate opaque fact IDs.

## Fail-closed behavior
An event with no verified authoritative observation is CONTEXT_ONLY/UNRESOLVED and cannot emit SUPPORT. Conflicting authoritative observations require explicit revision/correction lineage rather than silent overwrite.
