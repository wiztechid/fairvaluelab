# Scanner Private/Public Adapter Contract v1

Status: PUBLIC-SAFE CONTRACT. This document does not define or implement the Opportunity Engine.

## Trust boundary
The public repository may contain public evidence inputs, public schemas, controlled semantic codes/copy, sanitized Scanner artifacts, validators, publication gates, and UI rendering. It MUST NOT contain proprietary opportunity scoring, weights, thresholds, normalization, dependency-map details, ranking/tie-break logic, persistence parameters, calibration, backtest optimization, private feature vectors, or private transition margins.

Private computation MUST occur outside this public repository. A directory named `private/`, gitignore, or repository secrets do not make proprietary source code safe to commit here.

## One-way projection
Private Engine → Private Sanitizer → trust boundary → Sanitized Public Artifact → Public Validator → Publication Gate → Production.

The projection is intentionally lossy. Public artifacts must not contain enough information to reconstruct private scoring or transition boundaries.

## Adapter rules
1. Only fields defined by the frozen Scanner public schemas may cross the boundary.
2. Private numeric scores, rank/order metadata, thresholds, feature contributions, penalties, calibration, and raw decision traces MUST be discarded before ingress.
3. Private explanation text MUST NOT cross the boundary. The artifact carries allowlisted semantic reason/caveat codes; reader-facing copy is resolved from the public Reason Registry.
4. Public state and evidence strength are categorical projections only.
5. Public state history is limited/coarsened and never copies the private transition log. A GENERATED ticker exposes 1–3 date-only public transitions; dates are chronological and no later than evaluation date, adjacent duplicate states are forbidden, and the latest public transition must equal the current state and `stateChangedDate`.
6. Fair Value context must originate from canonical validated Fair Value output.
7. QSTP is never a private-engine execution instruction; it remains an optional public secondary navigation action.
8. Unknown fields/codes/states fail closed.
9. Frontend code may filter/group/render sanitized artifacts but must not recreate proprietary research intelligence.
10. Public artifact versioning must not expose private engine versioning.

## Publication semantics
A publication is a complete set: summary + every referenced ticker artifact. Partial publication is invalid. Validation occurs before production replacement. If the candidate set fails validation, the previously known-good public artifact remains authoritative.

## Repository rule
Opportunity Engine source code is explicitly out of scope for `wiztechid/fairvaluelab`. Any future change that introduces proprietary scoring/ranking source into this repository violates this contract.
