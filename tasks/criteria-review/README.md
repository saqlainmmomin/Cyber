# Test criteria review sheets

1. **What this is.** `dpdpa-criteria-v1.csv` is the draft of the DPDPA test criteria (P6-2a). An LLM drafted it from the DPDP Act 2023 and the DPDP Rules 2025. Nothing in the app reads it yet.
2. **How to review.** Go one domain at a time; rows follow framework order. Start with the `drafter_confidence = low` rows, then `medium`.
3. **Columns you fill in.** `decision` takes `approve`, `edit` or `reject`. For `edit`, put the new wording in `edited_statement`. Use `reviewer_note` for your reasons or for changes to `kind`, `evidence_hint` or `source_basis`.
4. **Drafted columns.** Each row has `requirement_id`, `requirement_title`, `criticality`, `criterion_id` (`<req>.TC<n>`) and `kind`. `design` means the policy or process exists and says X. `operating` means records show it was done.
5. `statement` is one observable, pass/fail condition, in our own words. `evidence_hint` is the `document_type` key(s) or evidence form that would show it.
6. `source_basis` cites the Act section or Rules rule. `practice` marks a criterion that goes beyond the law. `[repo cites ...]` marks a mismatch with `app/dpdpa/framework.py`.
7. `in_force_note` is the commencement status as of 2026-09-25, checked against G.S.R. 843(E) and Rules r.1. Most obligations start in mid-May 2027.
8. `drafter_confidence` is `high`, `medium` or `low`. `low` means the legal basis, or how to read it, is uncertain.
9. **Independence.** Review without reference to `validation/` answer keys (D-P5-9-C).
10. **Next step.** The approved sheet is the only input to P6-2b, which converts it into pack code. Regenerate the sheet with `python scripts/export_criteria_review.py`. Regenerating overwrites the review columns.
