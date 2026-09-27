# Valuation Status Contract

This contract documents current engine states; it does not change engine behavior.

## SIAP
Full fair value is available from at least two independent valuation families and no current REVIEW trigger is active.

## REVIEW
Full fair value exists, but forensic attention is required. Current v3.20 triggers include extreme base-to-market divergence (<0.25x or >3.0x) or cross-family spread >3.0x. REVIEW is not a buy/sell label.

## INDIKATIF
Indicative range only. Current validator requires at least two valid methods but evidence does not meet full independent-family requirements. Valuation confidence is capped at 55.

## REFERENSI
Reference-only range from exactly one valid method. Confidence is capped at 35.

## BELUM_DINILAI
No defensible valid method. Fair-value scenarios must remain null; the system must not fabricate a value.

## ERROR
Current-run ticker is explicitly represented as a fetch/process failure rather than silently disappearing from the universe.

## STALE
Reserved/recognized by validator for stale output handling. Publication policy must distinguish stale data from fresh analysis.

## Invariants
Status wording in the public UI must not overstate evidence. Public pages must preserve the distinction among full, review, indicative, reference, unvalued, stale, and error states.
