# Components needed by batch b3

- Answer scale: a five-option radio group (Fully implemented, Partially implemented, Planned, Not implemented, Not applicable) with a short-label variant for quick-confirm rows. Built from `.choice` radios in a wrapping row (`.x-opts.inline`). Needed because `.seg` allows two to four options and the scale carries five.
- Question card: solid card with title, optional pill/chip on the right, evidence citation, scale, notes disclosure, inline error. Built from `.solid` plus local `.x-qc` spacing. Quick-confirm and out-of-scope variants are local too.
- Form group (fieldset with legend as `.label`, help and error below) for scope and wizard questions: local `.x-q`, `.x-opts`.
- Disclosure (details/summary) styling for "Add notes" and "View evidence": local `.x-sum`.
- Two-pane section navigator on the questionnaire tab: reuses `.item`, `.grp` but needs its own container (`.x-split`, `.x-list`, `.x-pane`) because `.rq` is fixed-height for the review queue.
- Layout helpers (`.x-stack`, `.x-between`, `.x-row`, `.x-bar`, `.x-center`, `.x-gap-top`) are token-only spacing utilities; a shared set would remove them.
