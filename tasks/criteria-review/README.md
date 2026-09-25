# Test criteria review sheets

1. **What this is.** Draft test criteria for sign-off. An LLM drafted them; nothing in the app reads them yet.
   - `dpdpa-criteria-v1.csv`: DPDPA (P6-2a), from the DPDP Act 2023 and DPDP Rules 2025.
   - `iso27001-criteria-v1.csv`: ISO/IEC 27001:2022 (P6-2c). Clauses 4-10 (new `ISO.C*` ids) first, then the 93 Annex A controls.
   - `iso27001-descriptions-v1.csv`: own-words description for every ISO id (D-P6-J), to replace the pack's near-verbatim ISO text. `source` is `clause` or `annex_a`; clause rows also carry the drafted title.
   - `nist-csf-criteria-v1.csv`: NIST CSF 2.0 (P6-2c), the 94 pack requirements.
2. **How to review.** Go one domain at a time; rows follow framework order. Start with the `drafter_confidence = low` rows, then `medium`.
3. **Columns you fill in.** `decision` takes `approve`, `edit` or `reject`. For `edit`, put the new wording in `edited_statement` (`edited_description` in the descriptions sheet). Use `reviewer_note` for your reasons or for changes to `kind`, `evidence_hint` or `source_basis`.
4. **Drafted columns.** Each row has `requirement_id`, `requirement_title`, `criticality`, `criterion_id` (`<req>.TC<n>`) and `kind`. `design` means the policy or process exists and says X. `operating` means records show it was done.
5. `statement` is one observable, pass/fail condition, in our own words. `evidence_hint` is the `document_type` key(s) or evidence form that would show it.
6. `source_basis` cites by number only: DPDPA section or Rules rule; `ISO/IEC 27001:2022 cl.x` / `A.x`, or `ISO/IEC 27002:2022 x (guidance)`; `NIST CSF 2.0 <subcategory>`, `CSF 2.0 IE ...` or `SP 800-53r5 ...`. `practice` marks a criterion that goes beyond the source. `[repo says ...]` marks a mismatch with the pack definition.
7. `in_force_note`: DPDPA gives commencement status as of 2026-09-25 (most obligations start mid-May 2027). ISO and NIST leave it blank unless a version point matters (ISO Amd 1:2024, controls new in 2022, CSF 2.0 withdrawals).
8. `drafter_confidence` is `high`, `medium` or `low`. `low` means the basis, or how to read it, is uncertain, or the pack departs from the standard. Guidance-only (27002, CSF implementation examples, SP 800-53) and `practice` rows are never `high`.
9. **Copyright (D4).** ISO text is licence-restricted. Edits must stay in our own words; cite ISO by number only.
10. **Independence.** Review without reference to `validation/` answer keys (D-P5-9-C).
11. **Next step.** The approved sheets are the only input to the P6-2b-style conversion into pack code. Regenerate with `python scripts/export_criteria_review.py --framework dpdpa|iso27001|nist_csf` (default `dpdpa`). Regenerating overwrites the review columns.
