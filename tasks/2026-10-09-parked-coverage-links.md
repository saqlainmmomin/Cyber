# Parked: turn desk review's "controls it covers" into control links (2026-10-09)

Status: parked by Saqlain on 2026-10-09. Don't build until he decides the open question below.

## The gap
Desk review writes a catalog entry per document with `coverage_areas`: every control (or DPDPA chapter area) the AI thinks the document covers, in one pass. Nothing turns that into `EvidenceUse` rows. Control links are only created by hand (`app/routers/evidence.py`), by client RFI uploads (`app/services/magic_links.py`), or by reuse (`app/services/evidence_reuse.py`).

Effect: an Access Management policy that desk review says covers A.5.15, A.5.16 and A.5.18 is not listed under "Evidence on this control" on those cards. The evidence page's empty state also says a file "is mapped when the pre-fill or gap analysis cites it", which the code doesn't do.

## Decision needed (Saqlain)
1. **Automatic:** create the links when desk review completes, marked "Suggested by desk review".
2. **Confirm first (Claude's recommendation):** show them as suggestions the auditor accepts with one click. An AI guess about coverage shouldn't count as evidence on a control without a person agreeing.

## Notes for whoever builds it
- DPDPA `coverage_areas` can be chapter areas (`CH2.CONSENT`), not control ids. They need expanding or a separate path.
- Catalog entries match files by filename only. Two files with the same name can't be told apart.
- Fix or remove the "mapped when the pre-fill or gap analysis cites it" empty-state copy in `app/templates/pages/evidence_detail.html` at the same time.
