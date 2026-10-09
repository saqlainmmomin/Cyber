## Summary
Part C of `tasks/handoffs/2026-10-08-evidence-fixes.md`: the conclusion card becomes checkable.
- Every citation shows a human location ("Characters 37–93", "Page 3", "Whole document") that opens the highlighted passage. The filename opens the evidence record.
- New "Evidence on this control" block lists every file linked to the control, each marked "Cited" or "Not cited by the analysis".
- When files are linked, "N files linked, M cited" replaces the AI's missing-evidence suggestions. Requests already on the draft RFI stay visible. With nothing linked, the suggestions show as before.
- Desk review records which files it didn't send because of the 20,000-word limit, in the existing summary JSON. The desk-review page and affected cards say "Not read by the analysis (size limit): ...".
- Desk-review citations show real filenames for new uploads instead of "Document".

No prompt change, no new LLM call, no migration. Evidence links load in one query per page.

## AI-coherence test
- **Loop step:** judge (conclusion review), plus read (desk review).
- **What the AI produces:** a proposed conclusion with quoted citations; desk-review findings.
- **Where the auditor sees it:** the conclusion card on Review, Conclusions; the desk-review page.
- **Can they check it against the original in one click:** yes. The location label opens the highlighted passage, the filename opens the evidence record with the original file, and the card lists linked files the AI didn't cite or didn't read.
- **What it changes downstream:** the auditor stops asking the client for evidence that is already linked, and can see which files to read themselves before approving.

## Click-through
On the demo seed (`scripts/demo/README.md`), current assessment, Review, Conclusions, open Access rights (ISO A.5.18):
1. The citation shows a page or characters label. Opening it lands on the highlighted passage, which matches the quote on the card.
2. The filename opens that file's evidence record.
3. "Evidence on this control" lists every file linked to A.5.18. The cited file says Cited; the others say Not cited by the analysis. The count line matches.
4. No "Missing evidence" box.
5. At phone width (375px) the card doesn't scroll sideways.

## Checked in the browser
Demo-depth hadn't merged, so this ran on the current demo. Access rights citation reads "Characters 37–93" and opens "The quarterly review covered 9 of 11 production systems." highlighted. "2 files linked, 1 cited": Q2 review Cited, user access review export Not cited. No Missing evidence box. No sideways scroll at 375px.

## Open questions
- The Dec 2023 review isn't listed because the seed doesn't link it to A.5.18. That is a seed question, not a card bug.
- Citation and filename links look like plain text (existing `.cite-head` style). Worth a design call.
- A file cut mid-way by the word limit is partly read and isn't flagged. Flag it as "Partly read"?
- The size-limit notice and filename fix aren't visible on the demo (no desk-review findings); covered by tests.

## Tests
1627 passed, 29 skipped (baseline 1614 passed, 29 skipped). 13 new tests in `tests/test_evidence_c_card.py` and `tests/test_evidence_c_desk_review.py`.
