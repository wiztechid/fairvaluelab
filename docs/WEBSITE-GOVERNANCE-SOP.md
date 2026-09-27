# Website Governance SOP — FairValueLab / CekValuasi Adoption

## Prime directive
Protect correctness, trust, reversibility, and reader value before growth or monetization.

## Change classes
CONTENT, SEO, UX, DATA, ENGINE, DEPLOYMENT, MONETIZATION, GOVERNANCE.

## Required lifecycle
Proposal → impact assessment → isolated implementation → validation → review → promotion → observation → rollback if needed.

## Additive-first rule
Prefer new isolated artifacts over destructive edits during migration. Existing production files are not replaced until an explicit migration gate approves replacement.

## Source of truth
Every critical concern must have one declared authority: valuation output, data provenance, public URL, governance state, and monetization configuration.

## Gate principle
A change is not complete because code exists. It is complete only after the relevant validation gate passes.

## Auditability
Material decisions must be recoverable from CURRENT, CHANGELOG, model changelog, and repository history.

## Exceptions
Exceptions must be explicit, scoped, time-bounded where possible, and must not silently weaken financial-data integrity.
