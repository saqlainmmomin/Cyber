"""Build the standalone consultant pack without an application or database."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

COMPANY = "Veldhara Logistics Pvt Ltd."
PERIOD_START = "2026-07-01"
PERIOD_END = "2026-09-30"
CUTOFF = "2026-10-05"
SCOPE = {"ISO.SCP.1": "full_org", "ISO.SCP.2": "yes", "ISO.SCP.3": "both", "ISO.SCP.4": "yes_datacenter"}

FOLLOWUP_FACTS = [
    ("Access coverage", ["ISO.A5.18", "ISO.A8.2"], "July and August review requests were chased but no completed sheets were supplied. September covered nine of eleven systems. TMS and the driver app were excluded. Terminated enabled accounts and privileged accounts without a decision remain in the September export.", "Only September has a completed review. We cannot represent the initiation emails as completed reviews. Remediation references in the export do not prove closure where closure is open."),
    ("Supplier assurance", ["ISO.A5.19", "ISO.A5.21", "ISO.A5.22", "ISO.A8.30"], "The company uses onboarded SaaS and occasional vendor development. Agreements and specific change acceptance records exist. The risk-based supplier assurance cycle remains incomplete.", "We supplied the existing agreements and change records. We have not supplied a complete current assurance report set or a completed recurring review for every supplier."),
    ("Incident readiness", ["ISO.A5.24", "ISO.A5.25", "ISO.A5.26", "ISO.A5.27"], "The incident plan has assigned roles. No tabletop exercise has been completed by the evidence cut-off. Routine events are not proof of a tested major incident response.", "There is no exercise report to upload. Please distinguish routine event handling from readiness for a serious incident."),
    ("Recovery", ["ISO.A5.30", "ISO.A8.13", "ISO.A8.14"], "The DR failover completed in 3h 10m against a 4h objective. A backup restore test has not been supplied for this period.", "Failover switches to a replica. It does not demonstrate recovery from backup. We cannot claim that the DR record closes the restore-testing gap."),
    ("Awareness", ["ISO.A6.3"], "Annual training lapsed in this period. Prior-cycle completion does not establish current annual completion.", "The current register records the overdue annual cycle. Do not reuse the prior baseline as proof of completion in 2026."),
    ("Development", ["ISO.A8.25", "ISO.A8.26", "ISO.A8.29", "ISO.A8.30", "ISO.A8.32"], "The internal team builds integrations. Occasional vendor development is accepted through the internal change process. The supplied security standards, review and test records, and deployment tickets describe the sampled releases.", "Software development is in scope. Please ask for a specific release or test reference if the supplied sample does not answer your question. A sampled change does not establish assurance over the entire supplier population."),
    ("Honest evidence limits", [], "The pack is the evidence supplied at cut-off. Missing records are missing, not assumed successful. The company does not claim certification from this walkthrough.", "I can give the known facts and supplied record references. I cannot invent a missing approval, test result, review cycle, or client statement. Record the limitation and request evidence if needed."),
]

SUBCLAUSES = {
    "6.1.1": ("risk_methodology", "Owners identify information assets, threat events, existing safeguards and business impact with the service owner and risk coordinator.", "Check the current risk and opportunity response against the context and objectives. The risk register records the open operational risks."),
    "6.1.2": ("risk_methodology", "Likelihood and impact are rated from 1 to 5; the product sets the inherent score and the owner records the residual view after current safeguards.", "Check consistent criteria, risk owners and the quarterly register application, not policy alone."),
    "6.1.3": ("risk_methodology", "Treatment options are reduce, avoid, transfer or accept. Acceptance above the delegated threshold requires Board Risk Committee approval.", "Check the individual 93-control SoA, treatment owners, dates and acceptance. Open treatments are not completed controls."),
    "7.5.1": ("policy", "Version 3.1 replaced version 3.0 after the driver integration team and two new SaaS services entered scope.", "Check that the documented ISMS is sufficient for this organisation, using the scope, risk method and operating records as well as the policy."),
    "7.5.2": ("policy", "Version 3.0 was approved on 15 June 2025. Version 3.1 was approved on 1 July 2026 after scope and service changes were reviewed.", "Check identification, format, review and approval in the originals' document-control fields and approval record."),
    "7.5.3": ("records_protection", None, "Check availability, access, revision control, retention and disposal against the records register. Missing restore and deletion evidence remains a limit."),
    "9.2.1": ("internal_audit", "The audit objective was to compare defined procedures with a sample of current-period operating records and report whether actions had been effective.", "Check conformity and effective implementation in the audit's operating sample and findings."),
    "9.2.2": ("internal_audit", "The annual audit schedule gives priority to high-risk access, supplier, incident, backup and development processes and names a lead auditor for each review.", "Check programme, criteria, scope, impartiality, reporting and retained records. The Information Security Lead did not select samples or approve audit conclusions."),
    "9.3.1": ("management_review", "The Board Risk Committee and senior service owners met on 24 September 2026 to review ISMS performance and changes in context.", "Check the planned interval and senior management review against the annual schedule and minutes."),
    "9.3.2": ("management_review", "The committee reviewed the July-September objective measures, internal audit observations, supplier changes, risks and open corrective actions.", "Check every required review input against the minutes and attachments. Do not infer an omitted input from this selected passage."),
    "9.3.3": ("management_review", "The IT Operations Manager will run a database restore test by 31 October and retain the job, sample and recovery result.", "Check decisions on improvements and ISMS changes, owner acceptance and retained review evidence. Planned actions remain open until verified."),
}


def register_frameworks() -> None:
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.registry import FrameworkRegistry

    for framework in (DPDPA_DEFINITION, ISO27001_DEFINITION):
        if not FrameworkRegistry.is_registered(framework.id):
            FrameworkRegistry.register(framework)


def native_controls() -> set[str]:
    register_frameworks()
    from app.frameworks.registry import FrameworkRegistry

    return {control.id for control in FrameworkRegistry.get_all_controls("iso27001")}


def question_response(question: dict, records: dict) -> dict:
    """Combine explicitly authored member facts into the real shared question."""
    members = question.get("controls") or question.get("member_controls") or []
    ids = [member["control_id"] for member in members]
    entries = [(control_id, records[control_id]) for control_id in ids if control_id in records]
    if not entries:
        raise ValueError(f"No authored company facts for {question.get('id', question.get('cluster_id'))}: {ids}")
    rank = {"not_implemented": 0, "planned": 1, "partially_implemented": 2, "fully_implemented": 3, "not_applicable": 4}
    answer = min((entry["answer"] for _, entry in entries), key=rank.__getitem__)
    notes = "\n".join(f"{control_id}: {entry['notes']}" for control_id, entry in entries)
    return {"question_id": question.get("id", question.get("cluster_id")), "answer": answer, "notes": notes, "confidence": "medium", "controls": ids}


def questionnaire_rows(records: dict) -> list[dict]:
    register_frameworks()
    from app.frameworks.questionnaire_builder import build_multi_questionnaire

    return [{**question_response(question, records), "question": question["primary_question"], "follow_ups": question["follow_ups"]} for question in build_multi_questionnaire(["iso27001"])]


def _csv(rows: list[dict]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def generate_pack(output_dir: Path) -> tuple[Path, Path]:
    from scripts.demo.files import generate_demo_files
    from scripts.demo.scenario import CONTROLS, DOCUMENTS

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = generate_demo_files(output_dir / "evidence")
    native = native_controls()
    if native - CONTROLS.keys():
        raise ValueError(f"Scenario lacks registered controls: {native - CONTROLS.keys()}")
    mappings = {key: [] for key in paths}
    for control_id, record in CONTROLS.items():
        for key in set(record["design"] + record["operating"] + [record["primary"]]):
            if key not in paths:
                raise ValueError(f"Missing evidence {key} for {control_id}")
            mappings[key].append(control_id)
    upload_categories = {"privacy_policy", "consent_form", "data_flow_diagram", "dpia", "processing_records", "breach_procedure", "retention_policy", "vendor_agreement", "other"}
    manifest = [{"key": key, "filename": f"evidence/{path.name}", "category": DOCUMENTS[key]["category"] if DOCUMENTS[key]["category"] in upload_categories else "other", "evidence_type": DOCUMENTS[key]["category"], "document_date": DOCUMENTS[key]["date"], "mappings": "; ".join(mappings[key]), "upload_instruction": "Historical only. Leave unmapped in current assessment." if key in {"stale_access", "prior_baseline"} else "Upload once. Keep listed control references as consultant mapping notes; use available reuse actions within the engagement. Keep clause references in the supplemental workpaper.", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for key, path in paths.items()]
    next(row for row in manifest if row["key"] == "prior_baseline")["upload_instruction"] = "Upload only to a separate 2025 baseline assessment. Do not upload this file to the current assessment."
    (output_dir / "upload-manifest.csv").write_text(_csv(manifest), encoding="utf-8")
    coverage = [{"control": control_id, "applicability": entry["applicability"], "rationale": entry["rationale"], "design_files": "; ".join(paths[key].name for key in entry["design"]), "operating_files": "; ".join(paths[key].name for key in entry["operating"]), "passage": entry["quote"], "story": entry["notes"], "scope": "Native app item" if control_id in native else "Supplemental clause workpaper"} for control_id, entry in CONTROLS.items()]
    (output_dir / "coverage-matrix.csv").write_text(_csv(coverage), encoding="utf-8")
    questions = questionnaire_rows(CONTROLS)
    for row in questions:
        row["sources"] = {control_id: {"design": [paths[key].name for key in CONTROLS[control_id]["design"]], "operating": [paths[key].name for key in CONTROLS[control_id]["operating"]], "passage": CONTROLS[control_id]["quote"]} for control_id in row["controls"]}
    (output_dir / "questionnaire-entry.json").write_text(json.dumps(questions, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    guide = ["# Veldhara consultant entry guide", "", "This is a fictional company walkthrough. The originals are client evidence. This guide and the coverage matrix are consultant aids. Upload only originals from evidence/. Keep this guide, the intended judgments, and the coverage matrix outside live analysis input.", "", "## Company and engagement", "", f"Company: {COMPANY}. Industry: Other (freight and warehousing). Size: Large. Engagement: Q2 FY2026-27 ISO 27001 assessment. Engagement type: Gap assessment. Framework: ISO 27001:2022.", f"Period: {PERIOD_START} through {PERIOD_END}. Evidence cut-off: {CUTOFF}. Prepared by: Meera Joshi. Keep the reviewed-by field empty until review is actually completed.", "Scope: the Indian logistics operations, depots, head office, eleven production systems, hosted services, and internal integrations team. Include occasional vendor development and onboarded SaaS. The TMS and driver app remain inside the ISMS even though their access reviews are missing.", "Scope answers: full organisation; outsourced IT yes; software development yes; physical facilities yes. Use the options shown by the app. Do not select the blanket no-development exclusion.", "Context: identity, financial and location data; mobile app, forms and third-party APIs; foreign group reporting; sensitive personal data; high risk; internal policy posture; customer due diligence; shared security owner. Treat these as company facts. The consultant must confirm the final context rather than claiming an AI profile was supplied by the company.", "", "## Scope limitation", "", f"The current application registers {len(native)} Annex A controls. Clauses 4 through 10 are not native scored questionnaire items. The coverage matrix and supplemental entries below cover them explicitly. Record them in the external workpaper. Do not describe the native app report as a scored full clauses 4 through 10 assessment. This pack does not change the production framework.", "", "## Manual walkthrough", "", "1. Create the client and engagement with the values above. Complete context and scope in the actual app. Confirm internal and vendor development are included.", "2. Open upload-manifest.csv. Upload originals from evidence/ with the stated categories. Upload once and reuse within the engagement when appropriate. Do not map December 2023 or the 2025 baseline to current controls. The report access_q2 is primary on A.5.18; the workbook access_export is supporting. Missing July and August cycles remain missing.", "3. If running live desk review, use your configured API key. Inspect file summaries and exclusions. Verify quoted passages in the originals. The app may use an evidence word budget; a large pack can exceed it. Record exclusions and run appropriately scoped review rather than assuming all files were considered.", "4. Use the actual-question entries below. Shared questions have all member controls listed. The selected shared answer reflects the least complete member; notes preserve every member's state. If desk review changes a question or adds a probe, use the linked member facts and follow-up bank. Confirm every pre-fill yourself.", "5. Generate and answer actual follow-ups if using live AI. The sample responses are a fact bank, not promises of fixed questions. Never claim a missing operating record exists. Check each generated question against the period, system, and supplied file.", "6. Run analysis with your configured key. Review every conclusion against design and operating records. Inspect citations in their source, especially access exceptions, supplier oversight, annual training, incident exercises, and restore tests. Change judgments when the evidence warrants it. Create findings with owners and dates from confirmed facts.", "7. Set reporting period and cut-off. Approve conclusions individually after review. Inspect the report and snapshots before release. Record clauses 4 through 10 separately because the native report cannot score them. The offline seed demonstrates screens; its scripted judgments do not prove live AI performance.", "", "## Upload manifest", "", "See upload-manifest.csv for exact filenames, categories, dates, mappings, SHA-256 hashes and reuse instructions. All evidence is synthetic. No real client data is included.", "", "## Actual questionnaire entries", ""]
    guide = [line.replace("Size: Large.", "Size: SME (280 personnel in the supplied population).") for line in guide]
    guide = [line.replace("The app may use an evidence word budget; a large pack can exceed it. Record exclusions and run appropriately scoped review rather than assuming all files were considered.", "The final verified seed stores 22,515 current evidence words (the earlier pre-addendum total was 22,304), exceeding the default 20,000-word budget. For this complete manual walkthrough, start the app with MAX_TOTAL_DOCUMENT_WORDS=30000, using the existing configuration setting, then inspect exclusions and coverage. Inspect the exclusions list; do not assume all files were considered merely because upload succeeded.") for line in guide]
    guide = [line.replace("Upload originals from evidence/ with the stated categories.", "Upload current originals from evidence/ with the stated categories. Keep the 2025 baseline out of the current assessment. The December 2023 file is optional historical viewer evidence and cannot prove current operation.").replace("outsourced IT yes", "cloud services yes") for line in guide]
    guide += [f"Exact scope values: {json.dumps(SCOPE, sort_keys=True)}.", "", "The manifest category column uses the nine options available in the upload interface. Select Other for ISO evidence types such as security_policy or access_control_policy. The evidence_type column preserves the substantive document type. The control mapping column is a consultant reference; the manual interface does not expose every seed API mapping action. Record control references in questionnaire evidence notes and use the available engagement reuse actions.", "", "Image and scanned-PDF OCR uses the live configured key in the manual path. The offline seed uses faithful visible-text transcriptions and cannot verify live OCR. A clean text original accompanies the selected scanned approval. Keep screenshots and scans as originals when testing OCR.", "", "Known app limitation: some report and review footer shortcuts may omit the assessment ID. Use the explicit assessment URLs in scripts/demo/README.md or the app tabs. This pack does not change the production interface.", ""]
    for row in questions:
        guide += [f"### {row['question_id']}", "", row["question"], "", f"Member controls: {', '.join(row['controls'])}.", f"Response: {row['answer']}.", "", row["notes"], ""]
        for control_id, sources in row["sources"].items():
            guide += [f"Evidence for {control_id}: design {', '.join(sources['design'])}; operating {', '.join(sources['operating']) or 'not supplied'}. Passage to check: {sources['passage']}", ""]
        for followup in row["follow_ups"]:
            guide += [f"Framework-specific probe ({followup['control_id']}): {followup['question']}", "Use the member facts above and the facts below to answer this actual app probe.", ""]
    guide += ["## Supplemental clauses 4 through 10", "", "Applicability and client facts are separate from the intended consultant judgment. These references are external workpaper entries, not injectable native questionnaire records.", ""]
    for control_id, entry in CONTROLS.items():
        if control_id not in native:
            guide += [f"### {control_id}", "", f"Applicability: {entry['applicability']}. {entry['rationale']}", f"Client response: {entry['answer']}. {entry['notes']}", f"Consultant judgment to check: {entry['outcome']}. {entry['gap']}", f"Sources: {', '.join(paths[key].name for key in dict.fromkeys(entry['design'] + entry['operating']))}.", ""]
    guide += ["## Child clause obligations", "", "These references expand the 23 top-level workpaper entries. They are supplemental obligations, not additional native scored controls. Verify all obligations against the supplied ISO standard during consultant review. Selected passages locate evidence; they do not establish an untested obligation.", "", "| Reference | Source and selected passage | Consultant check |", "|---|---|---|"]
    for reference, (key, quote, check) in SUBCLAUSES.items():
        if quote is None:
            quote = DOCUMENTS[key]["sections"][0][1][0]
        assert quote in "\n".join(line for _, lines in DOCUMENTS[key]["sections"] for line in lines)
        guide += [f"| {reference} | {paths[key].name}: {quote} | {check} |"]
    guide += ["", "## Follow-up facts and sample responses", "", "Known facts below come from the supplied scenario. A sample response gives a factual answer. An auditor judgment remains the consultant's decision.", ""]
    for title, ids, facts, sample in FOLLOWUP_FACTS:
        guide += [f"### {title}", "", f"Linked controls: {', '.join(ids) or 'all'}.", f"Known company facts: {facts}", f"Sample response: {sample}", ""]
    guide_path = output_dir / "consultant-entry-guide.md"
    guide_path.write_text("\n".join(guide), encoding="utf-8")
    (output_dir / "scenario.json").write_text(json.dumps({"company": COMPANY, "period_start": PERIOD_START, "period_end": PERIOD_END, "cutoff": CUTOFF, "native_controls": sorted(native), "supplemental_clauses": sorted(CONTROLS.keys() - native)}, indent=2) + "\n", encoding="utf-8")
    archive = output_dir.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package_files = list(paths.values()) + [output_dir / name for name in ("upload-manifest.csv", "coverage-matrix.csv", "questionnaire-entry.json", "consultant-entry-guide.md", "scenario.json")]
        for path in sorted(package_files):
            info = zipfile.ZipInfo(path.relative_to(output_dir).as_posix(), date_time=(2026, 10, 5, 9, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            package.writestr(info, path.read_bytes())
    return guide_path, archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/demo/veldhara-upload-pack")
    args = parser.parse_args()
    guide, archive = generate_pack(args.output)
    print(f"Guide: {guide}\nArchive: {archive}")


if __name__ == "__main__":
    main()
