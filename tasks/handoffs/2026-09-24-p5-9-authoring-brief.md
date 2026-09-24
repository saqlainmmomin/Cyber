# P5-9 Stage A: authoring brief for the four validation companies

**Plan:** `docs/plans/2026-09-24-002-p5-9-end-to-end-validation-plan.md` (read decisions D-P5-9-A to D-P5-9-J).
**Harness and schemas:** `tasks/handoffs/2026-09-24-p5-9a-validation-harness.md`, D-P5-9a-B. That section is the authoritative definition of every JSON file below. If this brief and the harness schema disagree, the schema wins.
**Author model:** Gemini (D-P5-9-F; the tool assesses with DeepSeek and Claude, so authoring must use a different family). **Fairness auditor:** Codex or Claude, never the author.
**Output location:** `validation/companies/<slug>/` with slugs `c1-…`, `c2-…`, `c3-…`, `c4-…`. Choose the rest of each slug once the company is named.

---

## Part 1: For Saqlain (how to run this)

Run **one fresh Gemini session per company**, so companies don't bleed into each other. For each company:

| Step | You give Gemini | Gemini returns | You then run |
|---|---|---|---|
| A0 | This brief's Part 2 plus that company's section from Part 3 | `company.json` | Create the directory. Run `export_question_pack <slug> --stage intake`. |
| A1 | `question_pack.intake.json` | `answer_key.json` (truth first) | Nothing. Don't show it to anyone else yet. |
| A2 | (same session) | `client_visible/evidence/E01.json` … `Enn.json` | `render_evidence <slug>` |
| A3 | (same session) | `client_visible/intake_answers.json` | `export_question_pack <slug> --stage questionnaire` |
| A4 | `question_pack.questionnaire.json` | `client_visible/questionnaire_answers.json`, plus answer-key trail updates for any `answer:` sources | `render_evidence`, then `lint_pack <slug> --require-questionnaire`. Paste the errors back to Gemini until it's clean. |
| A5 | New Codex/Claude session: the Part 4 audit prompt, the pack directory **and** the rendered files | An audit report | Fix any gap it rules unfair or ambiguous (back in the Gemini session), then re-lint |

Steps A0 to A2 can start before P5-9a is merged if you hand-copy the control ids from `app/frameworks/definitions/`. A3 and later need the harness.

Gemini's JSON must be valid JSON with no comments or trailing commas. Ask it to output one file per fenced block, headed with the file path.

---

## Part 2: Rules for the author (give this to Gemini verbatim)

You are designing a **blind test case** for an AI compliance-assessment tool. You play two roles. First you're the examiner who decides the truth. Then you're the client company that produces the documents and questionnaire answers a real auditor would receive. The tool will see only the client material. A hidden answer key records what's actually true. Your job is to make the client material **realistic, internally consistent on its surface, and honest to the truth underneath**, so a sharp human auditor with unlimited time would reach exactly the answer key's conclusions.

### Order of work (never reverse it)

1. **Truth first.** Write `answer_key.json`: the status of every control (a `default` per framework plus `overrides`), the planted gaps, the decoys and the clean controls. Every later file must be consistent with this truth.
2. **Then evidence.** For each planted gap, decide the exact facts that reveal it (the `evidence_trail` and `key_facts`), and then write the documents that contain those facts. Don't write documents first and find gaps in them afterwards.
3. **Then answers.** Questionnaire answers are the client's *claims*. For planted gaps they usually show the `surface_answer` (an overclaim), with confident notes. For honest gaps they admit the weakness.

### Definitions

- **Planted gap:** a control whose true status is `non_compliant` or `partially_compliant`, with a deliberate trail of evidence proving it. Every gap has:
  - `key_facts`: 1 to 4 short strings (a number, a date, a name, a phrase) that must appear **verbatim** in the client material it cites. The lint checks this mechanically.
  - `what_followup_should_ask`: the single question that would crack it open.
- **Decoy:** a control that *looks* like a gap and is actually compliant. It tests false positives. Document why it looks wrong and why it's right.
- **Clean control:** genuinely compliant, with good supporting evidence. It tests that the tool credits real evidence.
- **Probing depth (1-5):**
  - 1: stated plainly.
  - 2: one document, one careful read.
  - 3: two sources, or a subtle qualifier.
  - 4: three or more sources, or arithmetic or dates across documents.
  - 5: cross-framework reasoning plus multi-hop.

### Gap classes (`gap_class`)

| Class | Shape |
|---|---|
| `honest_gap` | The client admits it (`not_implemented`/`planned`). A baseline the tool should never miss. |
| `overclaim` | `fully_implemented` claimed, and a single document plainly contradicts it |
| `cross_document` | Only visible by joining 2+ documents |
| `chained_dependency` | Control Y looks fine but depends on control X, which is broken, so Y is hollow |
| `temporal` | Dates make the claim impossible: a policy effective after the audit that cites it, or metrics from before the owner was appointed |
| `quantitative` | Numbers don't reconcile across sources (14 requests vs 9 in the annex vs a "backlog") |
| `wrong_citation` | Confidently cites the wrong law or section, or imports a foreign standard (GDPR "legitimate interest" under DPDPA) |
| `joint_impossibility` | Two answers are each plausible but can't both be true |
| `substance_over_form` | The control runs, but for the wrong population or scope |
| `cross_framework_divergence` | One cluster is truly compliant for ISO/NIST but false for DPDPA (or the reverse) |
| `artifact_discrepancy` | An operational record contradicts the policy: an access review lists a leaver still active, a firewall rule allows any-any to a DB subnet the policy says is isolated, a scan shows criticals past the patch SLA |
| `stale_evidence` | The evidence is real but dated outside the assessment period or superseded |
| `scope_coverage` | The evidence covers 3 of 5 environments or entities, and the claim says "all" |

### Evidence artifacts

- Each artifact is an `EvidenceSpec` JSON with `render.kind`:
  - `prose`: policies, procedures, minutes, letters, reports
  - `table`: registers, access reviews, asset lists, vendor lists, scan summaries, request logs
  - `config`: firewall rules, router config, IAM policy JSON, sshd config
  - `console`: a screenshot of an admin console or terminal output
  - `external_image`: a realistic photo or scan that you describe
- **Every artifact that carries a gap, a decoy or a key fact must be `prose`, `table`, `config` or `console`.** These are rendered exactly from your text. `external_image` is for realism only: a photographed whiteboard or a signed cover letter with nothing load-bearing in it. If you want an image to be generated, include a one-paragraph image prompt in `authoring_notes` and list the file under `client_visible/images/`. Saqlain generates it separately.
- Formats: `prose` → `pdf` or `docx`; `table` → `pdf`, `docx` or `png`; `config` → `pdf` or `png`; `console` → `png` or `jpg`. Use `degrade: "scan_light"` or `"scan_heavy"` on 1-2 image artifacts per company, to test OCR on imperfect scans.
- **The tool can't accept `.xlsx`, `.csv`, `.txt` or `.conf`.** Render spreadsheets as a `table` (png or pdf) and configs as `config` (pdf or png), as if the client exported or printed them.
- Tables: realistic sizes (an access review with 25-60 rows, a firewall rule set with 20-50 lines). The discrepancy is **one or two rows among many**, not highlighted.
- Filenames look like a real client's (`Q2-FY27-Privileged-Access-Review.pdf`, `fw-edge-01-running-config.png`). **Never** put words like gap, test, decoy, issue, bad or error in a filename or title unless a real client would.
- `category` must be one of the tool's `document_categories` (see the intake pack). Security-native evidence usually has to be `other`. That's expected.
- `channel`: most artifacts are `consultant_upload`. Put 2-4 per company through `magic_link`, each with a `magic_item` that matches an entry in `intake_answers.magic_link_items` and a sensible `consultant_maps_to` (the consultant's topical mapping, **not** a hint about the gap).

### Realism rules

- Fictional companies, people, domains and products only. No real company or person names, no real IP ranges (use RFC 5737 `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` and RFC 1918 ranges), no real credentials or keys.
- The assessment takes place in **October 2026**. The assessment period is the 12 months before that. Indian fiscal year FY27 runs April 2026 to March 2027. Dates must be consistent everywhere except where a `temporal` gap needs them not to be.
- Voice: professional and specific. Indian corporate register for C1-C3 and US register for C4. Documents cross-reference each other ("see Vendor Governance Standard §4.2"). Don't explain the gaps inside the documents. Don't leave "template artifacts" unless a gap is *about* one.
- A strong company must look strong. For a high-maturity company, the non-gap controls should be genuinely well evidenced. A high baseline is what makes the hidden gaps hard to find.
- Most facts should be **true and boring**. The traps are a small minority of the material.

### Leak rules (the lint enforces these; a single hit fails the pack)

Client-visible text (documents, filenames, answers, notes, magic item titles) must never contain:
- the words "answer key", "ground truth", "planted", "decoy", "hidden gap", "test company", "validation pack" or "seeded gap";
- any gap or decoy id like `G03` or `D01`;
- any run of 8 consecutive words copied from your answer key's descriptions or notes. **Describe the gap differently in the key from how the documents show it.**

### Questionnaire answers

- Answer **every** question in `question_pack.questionnaire.json` whose `status` isn't `skipped`, by its `id`.
- `answer` is one of `fully_implemented`, `partially_implemented`, `planned`, `not_implemented`, `not_applicable`. The company's maturity should show in the spread.
- `notes`: 1-3 sentences in the client's voice, often naming a document ("Per the Access Control Standard v3.1 §5, reviews are quarterly"). `evidence_reference`: the filename(s) the client points to.
- Planted gaps: use the gap's `surface_answer`. A good trap often has a confident, specific note.
- A gap whose trail uses `answer:<question_id>` must have its key fact inside that answer's `notes` or `evidence_reference`.

---

## Part 3: The four companies

Counts are ranges from the plan's matrix (D-P5-9-A). Every company must use **at least** the listed gap classes. Choose everything else.

### C1: low maturity, DPDPA only (`c1-…`)

- **Company:** An Indian consumer app startup, about 40 staff, Series A. It processes **children's personal data** (for example an ed-tech or kids' learning app), uses 6-10 SaaS processors, and has no dedicated security or privacy hire (the CTO "owns" it).
- **Frameworks:** `["dpdpa"]`. Screening answers are required.
- **Intake:** answer the scope questions truthfully so that the children's data obligations apply. Make at least one scope answer exclude something legitimately (for example no cross-border transfer), so scope exclusion is exercised.
- **Gaps:** 10-14. Mostly `honest_gap` (4-6) and `overclaim` (3-4), with depth 1-3. At least 1 `wrong_citation` (for example a privacy policy copied from a GDPR template that cites "legitimate interest") and at least 1 `quantitative`.
- **Decoys:** 2. For example a genuinely compliant verifiable parental-consent flow that looks unusual, or a very short retention period that's correct.
- **Clean controls:** ≥ 6.
- **Artifacts:** 5-7 (small companies hand over little). A privacy policy (docx), a signup and consent screen (`console` png), a processor list (`table` png, `scan_light`), a one-page "security policy" (pdf), a Slack-style incident note (`console` jpg), and optionally a breach-response one-pager.
- **Intent:** the tool should find most of these. If it doesn't, basic detection is broken.

### C2: medium maturity, DPDPA + ISO 27001 (`c2-…`)

- **Company:** An Indian B2B SaaS company (HR tech or fintech infrastructure), about 250 staff, on AWS, **mid-way to ISO 27001 certification**, with a Stage 1 audit booked. It has a small security team (3 people) and a part-time DPO.
- **Frameworks:** `["dpdpa", "iso27001"]`. This exercises the mixed cluster questionnaire.
- **Gaps:** 12-16, depth 2-4. Required classes: `artifact_discrepancy` ×2 (for example **a quarterly privileged-access review table in which 1-2 leavers are still active or approvers review their own access**, and **a firewall or security-group export that allows `0.0.0.0/0` to a management port the network policy says is VPN-only**), `stale_evidence` ×1, `scope_coverage` ×1, `chained_dependency` ×1, `cross_document` ×1, `temporal` ×1, and at least 1 `cross_framework_divergence`.
- **Decoys:** 3. At least one should be an access-review row that *looks* like a leaver but is documented as a rehire or contractor conversion elsewhere in the evidence.
- **Clean controls:** ≥ 8. Include at least one **perfect** operational artifact, for example a clean backup-restore test record.
- **Artifacts:** 9-12. Include an ISMS scope statement, a draft SoA extract (reference control ids only; no ISO standard text), an access control policy, the privileged-access review (`table` pdf), the firewall or security-group export (`config` png), a risk register extract (`table`), a vendor register, a privacy notice, and an incident-response procedure. Put 2-3 through a magic link.

### C3: "certified fortress, paper moat", DPDPA + ISO 27001 + NIST CSF (`c3-…`)

- **Company:** A large Indian enterprise (consumer fintech or health platform) at SDF scale, **genuinely ISO 27001-certified and NIST CSF-mature**, which treats DPDPA as paperwork. A skilled GRC lead writes polished, framework-fluent documents.
- **Frameworks:** `["dpdpa", "iso27001", "nist_csf"]`.
- **Take over the v3 spec:** `tasks/handoffs/2026-07-10-v3-adversarial-seed-company.md`, sections "The company archetype", "Required gap classes" and "Required false-positive traps". Ignore its instructions about `seed_test_companies.py` and `test_ground_truth.json`. This pack format replaces them.
- **Gaps:** 12-16, depth 3-5. At least 3 `cross_framework_divergence`, plus `cross_document` (multi-hop, 3+ sources), `chained_dependency`, `temporal`, `quantitative`, `wrong_citation`, `joint_impossibility`, `substance_over_form` and 1 `artifact_discrepancy`.
- **Decoys:** 4. Include the v3 decoy types: an unusual-but-compliant practice, an honestly disclosed and already-remediated past weakness, and near-miss language.
- **Clean controls:** ≥ 10, mostly ISO/NIST security controls with excellent evidence. The strong security posture is the camouflage.
- **Artifacts:** 10-15. Include at least one security-native artifact that legitimately evidences ISO/NIST controls (a certificate summary, an internal audit report, a risk register, a SOC runbook) and must not "bleed" into DPDPA credit.

### C4: medium-high maturity, NIST CSF only (`c4-…`)

- **Company:** A US-headquartered health-data SaaS company (for example remote patient monitoring analytics), about 400 staff, with an engineering centre in Pune. It's security-native: a SOC 2 Type II history, AWS multi-account, EDR everywhere.
- **Frameworks:** `["nist_csf"]`. **No DPDPA anywhere.** Nothing in its documents should read like DPDPA. Part of this company's purpose is to catch DPDPA copy leaking into the tool's output.
- **Gaps:** 10-14, depth 2-4. Required classes: `artifact_discrepancy` ×2 (for example **a vulnerability scan summary with criticals open past the documented 15-day SLA** and **an IAM or access listing with a service account holding admin plus long-lived keys against a policy that forbids it**), `scope_coverage` ×1 (for example EDR coverage covers the US fleet but not the Pune contractor laptops), `stale_evidence` ×1, `temporal` ×1, `quantitative` ×1, `chained_dependency` ×1.
- **Decoys:** 3. For example a firewall rule that looks overly broad but is scoped to an RFC 1918 management VLAN with a documented compensating control.
- **Clean controls:** ≥ 8. Include a genuinely good incident-response tabletop report and a clean backup-restore record.
- **Artifacts:** 10-14. Include a Security Hub or Config findings summary (`console` png), a vuln scan summary (`table` pdf), an IAM credential report (`table` png), the edge firewall config (`config` pdf), an IR plan, a tabletop after-action report, a BCP/DR test record, a vendor risk register, and an asset inventory extract. Put 2-3 through a magic link.

---

## Part 4: Fairness audit prompt (A5; run it in Codex or Claude, not Gemini)

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
