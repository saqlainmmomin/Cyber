# Handoff: v3 Adversarial Seed Company — Multi-Framework "Red Team" Test Case for CyberAssess

## Goal

Create ONE new synthetic test company for CyberAssess (an AI-powered multi-framework compliance gap assessment tool) undergoing a **combined DPDPA + ISO 27001 + NIST CSF assessment**, whose hidden compliance gaps are as hard to detect as you can make them while remaining objectively real and scoreable. This is an adversarial test: you are the red team. The tool's Claude-powered pipeline (desk review of documents → adaptive Unified Control Cluster questionnaire → gap analysis) must find gaps that are invisible to any single-document, single-answer, or single-framework review — gaps that only emerge from cross-referencing multiple documents, questionnaire answers, dates, numbers, and the *differences between the three frameworks* against each other.

**Definition of done:** `python scripts/seed_test_companies.py` runs clean and seeds the new company alongside the existing three (which stay DPDPA-only); the new assessment has `selected_frameworks = ["dpdpa", "iso27001", "nist_csf"]` and cluster-keyed questionnaire responses covering the full resolved UCC cluster set; `scripts/test_ground_truth.json` contains the new company's gap manifest in the existing format; every seeded gap is defensible (a competent human auditor with unlimited time WOULD find it); and at least 3 deliberate false-positive traps (compliant controls that superficially look like gaps) are documented in the manifest.

## Current state

- The repo is `~/dpdpa-gap-tool` (project: CyberAssess), branch `feat/web-portal`.
- `scripts/seed_test_companies.py` already seeds 3 DPDPA-only companies (NovaPay, HealthBridge, Dakshin) with 8–9 gaps each at "probing depth" 2–4. The full v2 spec that produced them is in `scripts/seed-v2-prompt.md` — **read it first**; it defines the document conventions and gap-authoring style you must follow. v3 is the next difficulty tier above it, and the first to exercise the multi-framework path.
- The multi-framework path works like this: `Assessment.selected_frameworks` is a JSON list of framework ids (`"dpdpa"`, `"iso27001"`, `"nist_csf"` — see `app/frameworks/definitions/`). The questionnaire is built by `app/frameworks/questionnaire_builder.py::build_multi_questionnaire()`, which calls `app/frameworks/cluster_engine.py::resolve_clusters()` to de-duplicate the ~41 DPDPA + 93 ISO 27001 + 94 NIST CSF controls into Unified Control Clusters (mappings in `app/frameworks/mappings/clusters.py`). Each `QuestionnaireResponse` row carries both `question_id` and `cluster_id`. Gap report items (`app/models/report.py::GapItem`) are keyed by `requirement_id` (a per-framework control id).
- `scripts/score_test_results.py` scores the tool's output against `scripts/test_ground_truth.json` by matching `requirement_ids` against GapItems. It has no framework awareness — ISO/NIST control ids in `requirement_ids` should match the same way DPDPA ids do, but **verify this by reading the script**, and keep your manifest entry format-compatible. If matching genuinely can't work for the multi-framework report shape, say so in Results rather than silently bending the format.
- The seed script's scaffolding (`verify_counts()`, `insert_fixture()`) is DPDPA-oriented (checks all 41 DPDPA requirement IDs are answered). You may extend the scaffolding minimally to support a multi-framework fixture — but the three existing fixtures must continue to seed byte-identically to today.

## Task

### Read these files in full before writing anything

```
scripts/seed-v2-prompt.md               — the v2 spec: document conventions, existing gap style (your baseline to exceed)
scripts/seed_test_companies.py          — existing script; you ADD one fixture, extend scaffolding only where multi-framework requires it
scripts/test_ground_truth.json          — manifest format your entry must match
scripts/score_test_results.py           — how detection is scored (keep your manifest compatible)
app/frameworks/registry.py              — framework registry (`get_all_controls`, ids)
app/frameworks/definitions/dpdpa.py     — DPDPA as a FrameworkDefinition (id="dpdpa")
app/frameworks/definitions/iso27001.py  — ISO 27001:2022 controls (id="iso27001", ids like "ISO.A.5.34")
app/frameworks/definitions/nist_csf.py  — NIST CSF 2.0 controls (id="nist_csf", ids like "NIST.GV.OC.01")
app/frameworks/cluster_engine.py        — resolve_clusters(): how controls merge into UCC clusters
app/frameworks/questionnaire_builder.py — build_multi_questionnaire(): the question set your responses must cover
app/frameworks/mappings/clusters.py     — the cluster mappings (which controls share a cluster)
app/routers/questionnaire.py, app/routers/analysis.py — how the live pipeline consumes multi-framework responses
app/dpdpa/framework.py, app/dpdpa/questionnaire.py, app/dpdpa/context_questions.py — legacy DPDPA path (still feeds the definitions)
app/models/assessment.py, app/models/questionnaire.py, app/models/report.py, app/models/desk_review.py
CLAUDE.md                               — architecture reference
```

Note: verify the exact control-id formats by reading the definition files — do not invent ids. Every `requirement_ids` entry in your manifest must exist in one of the three registered frameworks.

### Output

1. **Add one fixture function** to `scripts/seed_test_companies.py` (e.g. `veridian_fixture()` — name the company yourself) and register it in `main()` alongside the existing three. The fixture must set `selected_frameworks = ["dpdpa", "iso27001", "nist_csf"]` on the Assessment, and its `responses` must cover **every question returned by `build_multi_questionnaire(["dpdpa", "iso27001", "nist_csf"], ...)`**, with each response row carrying the correct `question_id` and `cluster_id` (derive them programmatically from `resolve_clusters()` inside the fixture — do not hardcode cluster ids that the engine might not produce). Do not modify the existing three fixtures; extend shared scaffolding (`insert_fixture()`, `verify_counts()`) only as needed to support the multi-framework shape while keeping the existing companies' seeded output unchanged. Respect document/finding counts: 3–5 documents, 10–20 desk-review findings.
2. **Append the company** to `scripts/test_ground_truth.json` in the existing `hidden_gaps` format — `requirement_ids` may mix DPDPA, ISO 27001, and NIST CSF control ids (list every mapped control the gap violates, across all three frameworks). Additionally include a new sibling key `decoy_controls` (list) documenting the false-positive traps — the score script ignores unknown keys, so this is safe.
3. **Write a short authoring note** at `tasks/handoffs/2026-07-10-v3-adversarial-seed-company.md` → `## Results` section (this file): company concept, gap inventory table (requirement IDs, class, depth), decoy inventory, and anything you couldn't make work.

### The company archetype: "the certified fortress with a paper moat"

A mid-to-large Indian company (pick sector/size; something that activates high-risk DPDPA chapters — SDF scale, cross-border, or children's data) that is **genuinely ISO 27001-certified and NIST CSF-mature but treats DPDPA as a paperwork exercise**, run by a skilled GRC lead who papers over operational reality. The security program is real: certificates, audit reports, risk registers, incident metrics — much of it should be *actually compliant* for ISO/NIST controls. The trap is the assumption that security maturity equals privacy compliance. Every document is professional, internally consistent on its face, fluent in all three frameworks' terminology (correct citations most of the time), and cross-references the others. Nothing is an obvious template artifact. The questionnaire answers are confident and specific, with plausible notes and real evidence references. The gaps live **in the seams** — between documents, between numbers, between dates, between frameworks, between what's claimed and what's structurally possible.

### Required gap classes (12–14 gaps total; every gap must belong to one of these, and every class must appear at least once)

0. **Cross-framework divergence (the headline class — include at least 3 of these, depth 4–5).** A single UCC cluster answered `fully_implemented` where the claim is TRUE for the ISO 27001 / NIST CSF controls in the cluster but FALSE for the DPDPA-mapped requirement (or vice versa), because the frameworks demand different things. The tool must not let genuine ISO/NIST evidence satisfy a DPDPA-specific obligation that shares the cluster. Examples of the shape (design your own): a certified ISO A.5.34 privacy program whose consent model still fails DPDPA's freely-given standard; an incident response process with real NIST RS.CO metrics that has no Data Protection Board / data-principal notification path; an ISO-grade supplier security program (A.5.19–A.5.23) whose contracts have security clauses but no DPDPA processor obligations; an excellent NIST GV.OC risk register that treats privacy as a security risk and has never assessed data-principal harm. The evidence documents should *legitimately* support the ISO/NIST half — that's what makes the DPDPA half hard to spot.

1. **Multi-hop cross-document inference (depth 4–5).** The gap is only visible by joining 3+ sources. Example pattern: Document A says vendor risk reviews happen annually per the vendor inventory; Document B's vendor inventory (or a count mentioned in passing) shows 60+ vendors; the questionnaire notes say the privacy team is 1.5 FTE and lists their other duties — jointly impossible, individually unremarkable. No single quote reveals it.
2. **Chained dependency gap.** Control Y is genuinely well-implemented *on paper and in practice*, but it structurally depends on control X, which is broken — so Y's claimed compliance is hollow. Example: a polished 72-hour breach notification workflow that depends on a personal-data asset inventory that does not exist (no document, and a questionnaire answer elsewhere admits inventory is "in progress"). The tool should downgrade Y because X fails, not just flag X.
3. **Temporal impossibility.** Dates across documents prove a control could not have operated as claimed. Example: the DPO appointment letter is dated March 2025, but the grievance procedure "owned and operated by the DPO" claims metrics from 2024; or a policy's "effective date" postdates the audit it cites as evidence of the policy working.
4. **Quantitative non-reconciliation.** Numbers that don't add up across sources. Example: questionnaire says "all 14 data principal requests in the last year were resolved within SLA"; the grievance procedure's annexed metrics table shows 9 requests; a desk-review-visible line in another doc references "the backlog of pending requests." Any one number is fine; together they can't all be true.
5. **Legally-wrong-but-confident citation.** A document cites the wrong DPDPA section or imports a foreign-law standard with full confidence (e.g., applies a GDPR 30-day access-request clock, or claims "legitimate interest" as a DPDPA processing ground — which DPDPA does not have). The text *sounds* more authoritative than the compliant version would.
6. **Jointly-impossible questionnaire answers.** Two or more questionnaire responses that are individually plausible (both `fully_implemented` with good notes) but mutually exclusive given the context answers. Example: claims purpose-limited consent per purpose AND claims a single unified customer data lake used freely by analytics — with context answers establishing no consent-refresh ever ran.
7. **Substance-over-form gap** (carry over from v2, but subtler): a control that is formally complete and *actually operated*, but aimed at the wrong population or scope (e.g., rights portal works perfectly but only for the 5% of data principals acquired after 2024; the 95% legacy base has no path in — mentioned only via one sentence about the "post-migration cohort" in a data-flow doc).

### Required false-positive traps (3+ decoys)

These test the tool's **precision** — it must NOT flag them:

- **Unusual-but-compliant practice.** Something that pattern-matches to a red flag but is fine under DPDPA (e.g., consent manager outsourced to a registered third-party — looks like abdication, is actually permitted; or an aggressive 30-day retention-then-delete policy that sounds too short but is compliant and evidenced).
- **Honest self-reported weakness that is already remediated.** A document candidly describes a past gap and its completed fix with evidence. Tools that keyword-match on "gap"/"incident" language will wrongly flag it.
- **Deliberate near-miss language.** A quote that superficially resembles one of the v2 planted gap quotes (e.g., broad-sounding consent language) but, read carefully, IS granular/compliant.

Document each decoy in `decoy_controls` with: `requirement_ids`, `why_it_looks_like_a_gap`, `why_it_is_compliant`, `document_key`.

### Authoring rules

- Every gap must be **objectively real** — write the ground-truth entry first, then engineer the evidence. No gaps that are matters of opinion; a human expert reviewing your manifest should agree with every `actual_status`.
- Every gap must be **discoverable from the seeded data alone** — the evidence trail (quotes, numbers, dates, absences) must exist in the documents/answers you write. No gap may depend on facts only stated in the manifest.
- Documents: 500–2000 words each via `build_document()`, professional register, internally cross-referencing ("see the Vendor Governance Standard §4"), realistic Indian corporate voice. No GDPR-template artifacts this time — this company is DPDPA-literate.
- Desk-review findings mix per v2 spec: evidence / absence / signal findings, but signals must be subtle (a number, a date, a scope qualifier — not a screaming template artifact).
- Questionnaire: every UCC cluster question answered; gap clusters get confident surface answers; non-gap clusters get a realistic strong-program distribution — ISO/NIST-heavy clusters should skew `fully_implemented` and be genuinely fine (this company should score WELL on everything except the seeded gaps — a high baseline makes hidden gaps harder to find, and a strong ISO/NIST posture is exactly what camouflages the DPDPA divergence gaps).
- Documents should include at least one security-native artifact (e.g., an ISMS/Statement-of-Applicability-flavored summary or risk register extract) that provides *legitimate* ISO/NIST evidence — the desk review must be able to credit it for security clusters while not letting it bleed into privacy clusters.
- Manifest `probing_depth`: rate honestly, 3–5. Include `what_followup_should_ask` for each gap — the single question that cracks it open.
- Idempotent seeding (purge-by-company-name), same as existing fixtures.

## Constraints

- Python 3.13. Do not modify any `app/` code (read it freely — the fixture imports from `app.frameworks` are expected) and do not modify the existing three fixtures' output.
- Match the existing script's style exactly (dataclasses, `build_document()`, `json_dumps()`).
- No real company names, no credentials.
- Do not "helpfully" make gaps easier by leaving explanatory comments in document text.

## Verification (run before reporting done)

```bash
cd ~/dpdpa-gap-tool
python scripts/seed_test_companies.py           # must exit 0, verification passes for all 4 companies
python -c "import json; m=json.load(open('scripts/test_ground_truth.json')); print([c['company_name'] for c in m['companies']])"
python scripts/score_test_results.py --help     # confirm the script still loads the manifest without error
# Multi-framework integrity checks for the new company:
python - <<'EOF'
import json
from app.database import SessionLocal
from app.models.assessment import Assessment
from app.models.questionnaire import QuestionnaireResponse
from app.frameworks.questionnaire_builder import build_multi_questionnaire

db = SessionLocal()
a = db.query(Assessment).filter(Assessment.company_name.like("%<YourCompany>%")).one()
assert json.loads(a.selected_frameworks) == ["dpdpa", "iso27001", "nist_csf"]
expected = {q["cluster_id"] for q in build_multi_questionnaire(["dpdpa", "iso27001", "nist_csf"])}
seeded = {r.cluster_id for r in db.query(QuestionnaireResponse).filter_by(assessment_id=a.id)}
missing = expected - seeded
assert not missing, f"unanswered clusters: {sorted(missing)[:10]}"
print(f"OK: {len(seeded)} cluster responses cover all {len(expected)} expected clusters")
EOF
```

(Adapt the snippet to `build_multi_questionnaire`'s real signature after reading it — it may need a context profile argument.)

Also confirm the existing three companies still seed identically (e.g., diff their manifest entries before/after your change), and self-audit: for each of your 12–14 gaps, quote (in the Results section) the exact seeded evidence trail that makes it discoverable, and for each cross-framework divergence gap state explicitly which framework's controls are satisfied and which are violated. If you cannot quote a trail, the gap is unfair — fix it.

## Report back

Append a `## Results` section to this file: company concept paragraph, gap inventory table, decoy inventory, evidence-trail self-audit, and verification output.
