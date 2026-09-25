# P5-9 Stage A5 — independent Claude fairness audit

**Owner:** Claude, independent reviewer. **Status:** pending. Codex authored the current Stage A0–A4 packs; this audit must be independent of that authorship. Do not run a live assessment, change application or harness code, or rewrite the packs during the audit.

## Material to inspect

Repository: `/Users/saqlainmomin/.codex/worktrees/7d10/dpdpa-gap-tool` (current working tree, including untracked pack files). For **each** directory below, read its hidden `answer_key.json`, `company.json`, both exported `question_pack.*.json` files, all files under `client_visible/`, and all files under `rendered/` including `manifest.json` and the actual PDF/DOCX/PNG/JPG outputs:

- `validation/companies/c1-app-startup/`
- `validation/companies/c2-b2b-saas/`
- `validation/companies/c3-certified-fortress/`
- `validation/companies/c4-healthsaas/`

Read `tasks/handoffs/2026-09-24-p5-9-authoring-brief.md` Parts 2–4 for the company matrix and authoring rules, `tasks/handoffs/2026-09-24-p5-9-stage-a-gemini-corrections.md` top Codex takeover brief and Results, and `scripts/validation/models.py` and `scripts/validation/lint_pack.py` for schema/lint meaning. Historical Gemini/Codex sections lower in the takeover file are superseded.

Codex's A0–A4 lint checks pass for all four packs with zero errors and warnings, but lint checks structure and verbatim facts, not substantive fairness. The author has not performed A5. The generated C4 intake pack contains generic context-question wording (“data principals”) from the harness; inspect C4's authored material for any non-NIST copy leak and report any finding separately from generated question text.

## Part 4: Fairness audit prompt (verbatim from the authoring brief)

> You are auditing a blind test case for an AI compliance-assessment tool. You have the full pack: `answer_key.json`, everything under `client_visible/`, and the rendered files under `rendered/`. Treat the answer key as a claim to verify, not as truth.
>
> For each planted gap:
> 1. Using **only** client-visible material, quote the exact passages, with file and location, that prove the answer key's `actual_status`.
> 2. Say whether a competent auditor with unlimited time would reach that status. Answer **yes**, **no** or **debatable**, with one sentence of reasons.
> 3. State the `probing_depth` you'd assign.
> 4. Say whether anything in the client material gives the gap away too easily: a filename, a heading, an explanatory sentence.
>
> For each decoy and each clean control, say whether the client material actually supports `compliant`, or whether a careful auditor could reasonably flag it. If they could, it isn't a fair decoy.
>
> Then list any **unplanted** problems you notice: inconsistencies, dates or numbers that contradict each other, or controls that look non-compliant but that the answer key marks compliant. Each one is either a bug in the pack or an extra gap the key is missing.
>
> Output a table per section and end with a verdict: `PASS`, or `FIX` with the numbered list of required changes. Don't rewrite the pack yourself.

A pack is ready for Stage C when:
- the audit returns `PASS`;
- `lint_pack <slug> --require-questionnaire` exits 0.

## Deliverable and boundary

Return one audit table per company for every gap, decoy and clean control, plus unplanted problems and a `PASS` or `FIX` verdict per company. Include exact rendered-file locations for factual support and name any answer-key status, class or depth that needs correction. Do not declare Stage C ready until all four receive `PASS` and any changes are re-linted. Stop after reporting findings; Codex will address actionable corrections in a separate turn.
