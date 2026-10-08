# E4: signed test criteria in v1

**Recommendation:** show the signed checklist first. Add deterministic RFI drafting separately. E4 follows evidence fixes A-C (`tasks/2026-10-08-session-record.md:18,27`; `tasks/2026-10-08-ai-coherence-map.md:37`). No network, LLM calls, validation runs, or answer keys were used.

## 1. What exists

Frozen `TestCriterion` holds ID, statement, design/operating kind, hint, and source basis. `Control.test_criteria` defaults to empty (`app/frameworks/schema.py:13-39`). Saqlain signs the CSV with approve/edit/reject. Conversion rejects unsigned rows, applies edits, drops rejections, and emits versioned modules with a sheet hash (`app/frameworks/criteria/__init__.py:3-5`; `tasks/criteria-review/README.md:9-11`; `scripts/convert_criteria.py:140-156,174-186`). This is review sign-off, not a cryptographic signature.

Local enumeration of `all_controls()` found:

| Framework | Controls with criteria / total | Criteria | Attachment source |
|---|---:|---:|---|
| DPDPA | 41 / 41 | 150 | `app/frameworks/definitions/dpdpa.py:128`; `app/frameworks/criteria/dpdpa.py:12` |
| ISO 27001 | 93 / 93 | 230 | `app/frameworks/definitions/iso27001.py:1193`; `app/frameworks/criteria/iso27001.py:12` |
| NIST CSF | 106 / 106 | 348 | `app/frameworks/definitions/nist_csf.py:1377`; `app/frameworks/criteria/nist_csf.py:12` |
| GDPR | 0 / 54 | 0 | `app/frameworks/definitions/gdpr.py:1086`; schema default above |
| HIPAA | 0 / 54 | 0 | `app/frameworks/definitions/hipaa.py:826`; schema default above |
| PCI DSS | 0 / 64 | 0 | `app/frameworks/definitions/pci_dss.py:901`; schema default above |

ISO's 78 signed clause criteria are deferred, not attached to current controls (`tests/test_p6_2e_iso_nist_criteria.py:36-41`).

Real example, pasted verbatim from `app/frameworks/criteria/iso27001.py:363-368`:

```python
TestCriterion(
    id='ISO.A5.18.TC3',
    statement='Access reviews were completed at the defined frequency for in-scope systems, with inappropriate access removed.',
    kind='operating',
    evidence_hint='access_control_policy (user access review records)',
    source_basis='ISO/IEC 27001:2022 A.5.18',
)
```

The same control's design test requires approval before provisioning and a defined review frequency (`app/frameworks/criteria/iso27001.py:350-354`).

## 2. Where the judge would receive them

The route gathers confirmed answers, documents, context, desk review, and scope, then chooses legacy DPDPA or registry analysis (`app/routers/analysis.py:114-148,244-298`). Legacy `run_gap_analysis` truncates documents, reuses desk-review quotes or extracts them, builds `app/dpdpa/prompts.py` system/user prompts, calls the judge, and validates output (`app/services/claude_analyzer.py:89-136`).

Registry analysis collects grounded quotes, batches controls, calls `build_framework_system_prompt` and `build_framework_user_prompt`, merges results, and synthesizes for 2+ frameworks (`app/services/claude_analyzer.py:315-335,521-545,611-643,856-912`). Results become report scores, recorded runs, and conclusions (`app/routers/analysis.py:382,423-442`; `app/services/analysis_pipeline.py:333,414`).

Today the system reference contains ID, title, source, criticality, and description. Output includes status, rationale, remediation, maturity, and quote. User input includes company/risk context, exclusions, desk-review findings, answers, follow-ups, and quotes or documents (`app/frameworks/prompts.py:156-171,383-443,492-626`; legacy counterpart `app/dpdpa/prompts.py:13-53,422`). **Slot criteria beside each control in the system reference.** Keep current JSON unchanged. This would guide judgments, but would not produce criterion-level pass/fail results.

## 3. Input cost

Measured ID, kind, statement, and hint in the diff format. Tokens ≈ characters / 4, not provider-tokenizer counts. Source basis stays on the card. Current batching threshold/target: 90/25 controls (`app/config.py:58-59`; `app/frameworks/batching.py:108-132`).

| Framework | Added characters | Judge calls | Extra tokens per call | Full framework |
|---|---:|---:|---:|---:|
| DPDPA | 32,146 | 1 | ~8,037 | ~8,037 |
| ISO | 49,916 | 6 | ~1,091-3,330 | ~12,479 |
| NIST | 68,647 | 7 | ~1,013-3,928 | ~17,162 |

Measured modules and batches are cited above. Add ~60 tokens/call for guidance and separators. One full three-framework assessment adds **~38,500 input tokens across 14 judge calls**, before retries. Other frameworks add zero criteria tokens. Retry calls resend scoped criteria (`app/services/claude_analyzer.py:614-621`).

Loaded `Settings.llm_model_*` matches defaults: extract, judge, and synthesize use `deepseek/deepseek-v4-flash`; vision uses `anthropic/claude-sonnet-4` (`app/config.py:44-47`; routing `app/services/llm_client.py:53-58`). Direct increase: judge only. Synthesis may vary with judgments. No money estimate without pricing. Show-only adds zero tokens.

## 4. Risk and proof

P6-5c parks **v2**, keeps v1, and forbids a third judge wording attempt. Reopening v2 requires decisions on criterion-aware extraction and whether insufficient evidence stays flagged, with written scoring sign-off. Its prior v2 arms had about 76% insufficient evidence and failed false-positive gates (`tasks/2026-09-30-p6-5c-decision-park-v2.md:3,9-29`).

**Interpretation:** show-only stays outside the freeze. Sending criteria to v1 does not enable v2, but reopens production judge wording and needs an explicit E4 exception. Judge-only criteria leave extraction unchanged: the registry judge often sees selected quotes instead of full documents (`app/services/claude_analyzer.py:324-331`; `app/frameworks/prompts.py:583-621`). More demanding tests could therefore flag missing operating evidence that was never extracted.

- Display: extend `tests/test_p6_7_requirement_card.py:760-813`. Assert kind/hints and no invented met status. Today v1 returns empty criteria and renders a label (`app/services/requirement_card.py:610-629`; `app/templates/components/requirement_card_body.html:15-31`). Label old runs: “Auditor checklist; not used by this analysis.”
- Judge plumbing: `tests/test_p6_1b_framework_batching.py:152-173` pins prompt fingerprints. Update deliberately. Retain grounding/status guards (`tests/test_llm_output_validation.py:41-73,161-233`) and human-conclusion protection (`tests/test_analysis_pipeline.py:571`). `tests/test_p6_2b_dpdpa_criteria.py:400-402` only forbids criteria references in the analyzer, so prompt-only edits can evade it.
- Quality: new dev fixtures with operating records, then unchanged-v1 versus criteria-v1, four companies × three runs/arm. Runner/scorer/report and comparator measure catch, decoy/clean false positives, stability, failures, and cost (`validation/README.md:29-37`; `scripts/validation/ab_compare.py:369-409`; original design `tasks/2026-09-30-p6-5c-decision-park-v2.md:9`). Mock runs prove plumbing only. Keep keys held out; inspect aggregates (`validation/README.md:63-67`).

## 5. RFI without an LLM

**Yes.** Enrich document requests at `build_rfi_document`, where checklist reasons become request text (`app/services/rfi_requests.py:191-209`). Use mapped controls' signed statements and hints. Hints do not prove evidence missing. They are free text, sometimes several document types. Use explicit mapping or `other` (`app/frameworks/schema.py:25`; example above; `app/services/rfi_evidence_requests.py:108-136`).

Card requests can reuse deterministic text, idempotent recording, and next-RFI inclusion (`app/services/rfi_evidence_requests.py:117-136,278-315`; `app/services/rfi_requests.py:229-233`). That action currently rejects v1, so it also needs service guards, template, and tests changed (`app/services/requirement_card.py:418-419,743-746`; `tests/test_p6_7b_add_to_rfi.py:442-465`). Hints alone do not specify exact dates or sample sizes; let the auditor set those.

## 6. Options and recommendation

Sizes and risks below are estimates. File names are relative to `app/`, except tests. RFI is an optional, separate M-sized addition to any option: `services/rfi_requests.py`, corresponding `tests/test_p5_6_rfi_rebuild.py:312`; card actions also need the guards above.

| Option | Changes and files touched | Size / risk | Auditor sees |
|---|---|---|---|
| (a) Show-only | Registry criteria into `services/requirement_card.py`; display kind/hint/basis in `templates/components/requirement_card_body.html`; card tests | S / low; avoid implying the AI used them | Signed checklist beside the existing proposal; no AI criterion results |
| (b) Send to judge | `frameworks/prompts.py`, `dpdpa/prompts.py`; prompt/batch tests and new dev evaluation fixtures | M / high judgment risk; E4 freeze exception | Existing proposal may change; card still hides the checklist |
| (c) Both | Union of (a) and (b), plus honest current-run versus old-run labeling | M / same judgment risk, better visibility | Checklist and changed proposal; still no criterion-level results |

**Choose (a), then RFI drafting.** Approve (c) after an explicit experiment passes the quality gate. Criterion-level results require a larger output-contract change.

Saqlain must answer:

1. Show-only first, or authorize a v1 prompt experiment now as an E4 exception?
2. Should missing operating evidence lower compliance, or remain an evidence request until the auditor reviews it? If reopening v2, what is the written decision on flagged insufficient evidence?
3. Should hints enrich every scoped RFI request, or only requests selected by the auditor? What period and sample defaults should they use?

## Unapplied diff sketch

Illustrative minimal wiring at `app/frameworks/prompts.py:156,441` and `app/dpdpa/prompts.py:13,53`. Existing output schema stays intact. The exact guidance is an experiment, not an approved scoring policy.

```diff
--- a/app/frameworks/prompts.py
+++ b/app/frameworks/prompts.py
@@ before _build_controls_text
+def _signed_criteria_text(control) -> str:
+    return "".join(
+        f"  - {c.id} [{c.kind}]: {c.statement}\n"
+        f"    Evidence hint: {c.evidence_hint}\n"
+        for c in control.test_criteria
+    )
@@ inside _build_controls_text, after each control reference
+        criteria = _signed_criteria_text(fw.get_control(ctrl_dict["id"]))
+        if criteria:
+            lines[-1] += "\n" + criteria
@@ Assessment Instructions / Important Guidelines
+- Use the signed design and operating criteria as audit tests for each control.
+- Evidence hints describe evidence to seek; they are not evidence supplied by the organization. Keep the existing status vocabulary and JSON schema.
--- a/app/dpdpa/prompts.py
+++ b/app/dpdpa/prompts.py
@@ imports
+from app.frameworks.registry import FrameworkRegistry
+from app.frameworks.prompts import _signed_criteria_text
@@ inside _build_requirements_text, after each requirement reference
+        control = FrameworkRegistry.get("dpdpa").get_control(req["id"])
+        criteria = _signed_criteria_text(control)
+        if criteria:
+            req_lines[-1] += "\n" + criteria
@@ Assessment Instructions / Important Guidelines
+- Use the signed design and operating criteria as audit tests for each control.
+- Evidence hints describe evidence to seek; they are not evidence supplied by the organization. Keep the existing status vocabulary and JSON schema.
```
