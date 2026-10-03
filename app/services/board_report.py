"""Document-first board report v2 generation and rendering."""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import shutil
import subprocess
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.config import settings
from app.dpdpa.framework import DPDPA_READINESS_NOTE, dpdpa_readiness_note_applies
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment, _new_id
from app.models.assessment_pack import AssessmentPack
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceVersion
from app.models.report_snapshot import ReportSnapshot
from app.services import (
    approved_report,
    board_derive,
    board_inputs,
    board_view,
    conclusion_review,
    firm_theme,
    narrative,
    prior_period,
    report_basis,
    report_content,
    report_snapshots,
    remediation_groups,
    soa,
)
from app.services.approved_report import ApprovedRow
from app.template_config import configure_templates
from app.utils import html_pdf
from app.utils.pdf_export import (
    GAP_STATUSES,
    LEGAL_FRAMEWORK_IDS,
    _follow_on_text,
    _nature_text,
    methodology_text,
)
from app.utils.review_gate import require_review_approval


SNAPSHOT_TYPE = "board_report"
DOCUMENT_SCHEMA_VERSION = 3
TOP_RISKS_LIMIT = 10
TEMPLATE = "reports/board_report.html"
PREVIEW_VERSION_LABEL = "Preview (not a report version)"
SHA_PREFIX_CHARS = 12
DATE_FORMAT = "%d %b %Y"
OUTCOME_LABELS = {
    "compliant": "Compliant",
    "partially_compliant": "Partially Compliant",
    "non_compliant": "Non-Compliant",
    "insufficient_evidence": "Insufficient Evidence",
    "not_applicable": "Not Applicable",
}
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
REGISTER_VERSION_STATUSES = ("active", "superseded")
EDITED_CITATION_NOTE = "Consultant decision; no cited evidence"
LEGACY_CITATION_NOTE = "Evidence support not captured"
NO_CITATION_NOTE = "No supporting citation"
NOT_COVERED_TEXT = (
    "This assessment does not include technical penetration testing, source code review, "
    "network security assessment, or any form of independent technical verification. "
    "Where the selected framework(s) include physical or environmental controls, findings "
    "on those controls are based on disclosed information and submitted documents, not on "
    "physical inspection or testing."
)
RELIANCE_TEXT = (
    "All findings reflect the information provided to the assessor at the time of the "
    "assessment. The assessor has not independently verified the accuracy or completeness "
    "of information provided. Material omissions or inaccuracies in disclosed information "
    "would affect the reliability of findings."
)
CONFIDENTIALITY_TEXT = (
    "This report is prepared solely for the use of the named organization. It should not "
    "be shared with third parties without the organization's explicit consent."
)
ISSUE_STATUS_TEXT = (
    "This version is a draft until it is issued. Whether it was issued, who issued it and "
    "the SHA-256 of the issued file are recorded in the report version history."
)
SIGN_OFF_NAMES_TEXT = "Names are recorded as entered by the consultant; they are not verified sign-ins."

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[1] / "templates"
)
configure_templates(_templates)
_templates.env.filters["display_date"] = lambda value: display_date(value)


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _display_or_none(value) -> str | None:
    return display_date(_iso(value)) if value is not None else None


def display_date(value: str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        raw = str(value)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                parsed = date.fromisoformat(raw)
            except ValueError:
                return raw
    return parsed.strftime(DATE_FORMAT)


def canonical_bytes(document: dict) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _resolved_citations(card) -> list[dict]:
    return [citation for citation in card.citations if citation.get("resolved")]


def _citation_text(card) -> tuple[str | None, str | None, set[str]]:
    if card is None or not card.citations_captured:
        return None, LEGACY_CITATION_NOTE, set()
    citations = _resolved_citations(card)
    if not citations:
        return None, NO_CITATION_NOTE, set()
    rendered = "; ".join(
        f"{citation.get('filename')} v{citation.get('version_number')}, "
        f"{citation.get('location_ref')}"
        for citation in citations
    )
    return rendered, None, {
        citation["evidence_version_id"]
        for citation in citations
        if citation.get("evidence_version_id")
    }


def _register_row(row: ApprovedRow, card) -> tuple[dict, set[str]]:
    citation = None
    citation_note = None
    cited_ids: set[str] = set()
    if row.decision == "edited":
        citation_note = EDITED_CITATION_NOTE
    else:
        citation, citation_note, cited_ids = _citation_text(card)
    return (
        {
            "framework_id": row.framework_id,
            "requirement_id": row.requirement_id,
            "requirement_title": row.requirement_title,
            "domain_title": row.chapter_title,
            "outcome": row.compliance_status,
            "outcome_label": OUTCOME_LABELS.get(
                row.compliance_status, row.compliance_status.replace("_", " ").title()
            ),
            "risk_level": row.risk_level,
            "decision_label": report_content.DECISION_LABELS.get(
                row.decision, row.decision
            ),
            "decided_by": row.decided_by,
            "decided_on": _iso(row.decided_at.date() if row.decided_at else None),
            "citation": citation,
            "citation_note": citation_note,
        },
        cited_ids,
    )


def _finding_citations(finding) -> list[dict]:
    rendered = []
    for citation in finding.citations:
        if not citation.resolved:
            continue
        prefix = (citation.sha256 or "")[:SHA_PREFIX_CHARS]
        rendered.append(
            {
                "filename": citation.filename,
                "version_number": citation.version_number,
                "location_ref": citation.location_ref,
                "sha256_prefix": prefix,
                "is_current": citation.is_current,
            }
        )
    return rendered


def _evidence_register(db: Session, assessment: Assessment, cited_ids: set[str]) -> list[dict]:
    assessment_rows = db.execute(
        select(EvidenceVersion, Evidence)
        .join(Evidence, Evidence.id == EvidenceVersion.evidence_id)
        .where(
            Evidence.assessment_id == assessment.id,
            Evidence.status != "rejected",
            EvidenceVersion.status.in_(REGISTER_VERSION_STATUSES),
        )
    ).all()
    by_id = {version.id: (version, evidence) for version, evidence in assessment_rows}
    if cited_ids:
        cited_rows = db.execute(
            select(EvidenceVersion, Evidence)
            .join(Evidence, Evidence.id == EvidenceVersion.evidence_id)
            .where(EvidenceVersion.id.in_(cited_ids))
        ).all()
        by_id.update({version.id: (version, evidence) for version, evidence in cited_rows})

    rows = []
    for version, evidence in by_id.values():
        rows.append(
            {
                "filename": version.original_filename,
                "version_number": version.version_number,
                "sha256_prefix": version.file_hash_sha256[:SHA_PREFIX_CHARS],
                "added_on": _iso(version.created_at.date() if version.created_at else None),
                "status": version.status,
                "cited": version.id in cited_ids,
            }
        )
    return sorted(rows, key=lambda row: (row["filename"].lower(), row["version_number"]))


def _framework_summary(review) -> dict:
    coverage = review.coverage
    if review.status == "scored":
        headline = (
            f"{review.score['overall_score']:.0f}% ({review.score['overall_rating']}); "
            f"{coverage['insufficient_evidence']} requirement(s) insufficient evidence"
        )
    elif review.status == "not_scored":
        headline = (
            "Not scored: no in-scope requirement has a scoring outcome; "
            f"{coverage['insufficient_evidence']} requirement(s) insufficient evidence"
        )
    else:
        headline = "Not scored"
    return {
        "framework_id": review.framework_id,
        "name": review.name,
        "status": review.status,
        "score": review.score.get("overall_score"),
        "rating": review.score.get("overall_rating"),
        "coverage": coverage,
        "headline": headline,
        "narrative": None,
    }


def _framework_section(review) -> dict:
    framework = FrameworkRegistry.get(review.framework_id)
    domains = []
    domain_scores = review.score.get("domain_scores", {})
    for domain_id, domain in framework.as_legacy_framework_dict().items():
        score = domain_scores.get(domain_id, {})
        applicable = score.get("applicable", False)
        domains.append(
            {
                "domain_id": domain_id,
                "title": domain["title"],
                "score": score.get("score") if applicable else None,
                "rating": score.get("rating") if applicable else None,
            }
        )
    return {
        "framework_id": review.framework_id,
        "name": review.name,
        "version": framework.version,
        "status": review.status,
        "score": review.score.get("overall_score"),
        "rating": review.score.get("overall_rating"),
        "domains": domains,
        "gaps": [
            {
                "requirement_id": row.requirement_id,
                "requirement_title": row.requirement_title,
                "outcome": row.compliance_status,
                "outcome_label": OUTCOME_LABELS.get(
                    row.compliance_status, row.compliance_status.replace("_", " ").title()
                ),
                "risk_level": row.risk_level,
            }
            for row in review.rows
            if row.compliance_status in GAP_STATUSES
        ],
    }


def _frozen_theme() -> dict:
    resolved = firm_theme.resolve_theme()
    logo = None
    logo_path = resolved.get("logo_path")
    if logo_path:
        try:
            path = Path(logo_path)
            if path.is_file() and path.stat().st_size <= 2 * 1024 * 1024:
                content = path.read_bytes()
                if len(content) <= 2 * 1024 * 1024:
                    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                    logo = {
                        "media_type": media_type,
                        "data_base64": base64.b64encode(content).decode("ascii"),
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
        except (OSError, ValueError):
            logo = None
    return {
        "firm_name": resolved["firm_name"],
        "primary": resolved["primary"],
        "secondary": resolved["secondary"],
        "accent": resolved["accent"],
        "logo": logo,
    }


def build_document(
    db: Session,
    assessment: Assessment,
    *,
    snapshot_id: str | None,
    version_label: str,
    generated_at: datetime,
) -> dict:
    approved = approved_report.build_approved_report(db, assessment)
    basis = report_basis.current_basis(db, assessment)
    framework_ids = list(assessment.frameworks)
    cards = {
        (card.conclusion.framework_id, card.conclusion.requirement_id): card
        for card in conclusion_review.conclusion_cards(db, assessment.id)
    }
    register = []
    cited_ids: set[str] = set()
    for row in approved.rows:
        register_row, row_citations = _register_row(
            row,
            cards.get((row.framework_id, row.requirement_id)),
        )
        register.append(register_row)
        cited_ids.update(row_citations)

    findings = report_content.assessment_findings(db, assessment).findings
    indexed_findings = list(enumerate(findings))
    indexed_findings.sort(
        key=lambda pair: (
            SEVERITY_RANK.get(pair[1].severity, 4),
            pair[1].priority,
            pair[0],
        )
    )
    top_risks = []
    findings_by_key = {}
    for finding in findings:
        findings_by_key[(finding.framework_id, finding.requirement_id)] = finding
    for rank, (_original_index, finding) in enumerate(
        indexed_findings[:TOP_RISKS_LIMIT], start=1
    ):
        citations = _finding_citations(finding)
        first_action = finding.actions[0] if finding.actions else None
        top_risks.append(
            {
                "rank": rank,
                "finding_id": finding.finding_id,
                "title": finding.title,
                "description": finding.description,
                "business_impact": finding.business_impact,
                "recommendation": finding.recommendation,
                "severity": finding.severity,
                "framework_id": finding.framework_id,
                "framework_name": finding.framework_name,
                "requirement_id": finding.requirement_id,
                "requirement_title": finding.requirement_title,
                "outcome_label": finding.outcome_label,
                "citations": citations,
                "owner": first_action.owner if first_action else None,
                "target_date": _iso(first_action.target_date if first_action else None),
                "action_title": first_action.title if first_action else None,
                "action_status_label": first_action.status_label if first_action else None,
            }
        )

    register_domain = {
        (row["framework_id"], row["requirement_id"]): row["domain_title"].split(" — ", 1)[-1]
        for row in register
    }
    observations = []
    for rank, (_original_index, finding) in enumerate(indexed_findings, start=1):
        responsibility = board_derive.responsibility_for(
            action.responsibility for action in finding.actions
        )
        observations.append(
            {
                "domain": register_domain.get(
                    (finding.framework_id, finding.requirement_id), finding.requirement_title
                ),
                "finding_id": finding.finding_id,
                "framework_id": finding.framework_id,
                "framework_name": finding.framework_name,
                "observation": finding.description,
                "rank": rank,
                "rating": finding.severity,
                "recommendation": finding.recommendation,
                "ref": board_derive.observation_ref(rank),
                "references": board_derive.reference_clauses(
                    finding.framework_id, finding.requirement_id, framework_ids
                ),
                "requirement_id": finding.requirement_id,
                "responsibility": responsibility,
                "risk": finding.business_impact,
                "title": finding.title,
            }
        )

    roadmap_actions = []
    for finding in findings:
        for action in finding.actions:
            roadmap_actions.append(
                {
                    "_sort": (
                        action.target_date is None,
                        action.target_date,
                        SEVERITY_RANK.get(finding.severity, 4),
                    ),
                    "title": action.title,
                    "owner": action.owner,
                    "target_date": _iso(action.target_date),
                    "status_label": action.status_label,
                    "finding_id": finding.finding_id,
                    "responsibility": action.responsibility,
                    "closes": [
                        {
                            "framework_name": finding.framework_name,
                            "requirement_id": finding.requirement_id,
                            "finding_title": finding.title,
                        }
                    ],
                }
            )
    roadmap_actions.sort(key=lambda action: action["_sort"])
    for action in roadmap_actions:
        del action["_sort"]
    roadmap_groups = remediation_groups.build_groups(findings, framework_ids)
    finding_keys = set(findings_by_key)
    unplanned_gap_count = sum(
        row.compliance_status in GAP_STATUSES
        and (row.framework_id, row.requirement_id) not in finding_keys
        for row in approved.rows
    )

    rfi = {"version_label": None, "items": []}
    current_rfi = report_snapshots.current_rfi_issue(db, assessment)
    if current_rfi is not None:
        rfi_document = report_snapshots.read_rfi_document(db, current_rfi)
        rfi = {
            "version_label": next(
                (
                    f"v{row.sequence}"
                    for row in report_snapshots.rfi_snapshot_rows(
                        db, assessment, current_source=None
                    )
                    if row.snapshot.id == current_rfi.id
                ),
                None,
            ),
            "items": [
                {
                    "item_id": item["item_id"],
                    "title": item["title"],
                    "required": item["required"],
                }
                for item in rfi_document.get("items", [])
            ],
        }

    release = approved.release
    engagement = db.get(Engagement, assessment.engagement_id)
    pack_versions = {}
    for pack in (
        db.query(AssessmentPack)
        .filter(AssessmentPack.assessment_id == assessment.id)
        .order_by(AssessmentPack.created_at, literal_column("assessment_packs.rowid"))
        .all()
    ):
        pack_versions[pack.framework_id] = pack.pack_version
    limitations = [NOT_COVERED_TEXT, RELIANCE_TEXT, _follow_on_text(framework_ids)]
    if dpdpa_readiness_note_applies(framework_ids, generated_at.date()):
        limitations.append(DPDPA_READINESS_NOTE)
    frameworks = [
        {
            "framework_id": framework_id,
            "name": FrameworkRegistry.get(framework_id).name,
            "version": FrameworkRegistry.get(framework_id).version,
            "legal": framework_id in LEGAL_FRAMEWORK_IDS,
            "pack_version": pack_versions.get(framework_id),
        }
        for framework_id in framework_ids
    ]
    summary_frameworks = [
        _framework_summary(approved.framework_reviews[framework_id])
        for framework_id in framework_ids
    ]
    totals = {
        "requirements": len(approved.rows),
        "gaps": sum(row.compliance_status in GAP_STATUSES for row in approved.rows),
        "critical_high_gaps": sum(
            row.compliance_status in GAP_STATUSES
            and row.risk_level in ("critical", "high")
            for row in approved.rows
        ),
        "insufficient_evidence": sum(
            row.compliance_status == "insufficient_evidence" for row in approved.rows
        ),
        "not_applicable": sum(
            row.compliance_status == "not_applicable" for row in approved.rows
        ),
    }
    framework_sections = [
        _framework_section(approved.framework_reviews[framework_id])
        for framework_id in framework_ids
    ]
    generated_on = generated_at.date()
    initiative_metadata = board_inputs.initiative_metadata(db, assessment.id)
    initiatives = board_derive.build_initiatives(
        roadmap_groups,
        initiative_metadata,
        observations,
        generated_on,
    )
    status_board = board_derive.build_status_board(framework_sections, register)
    risk_matrix = board_derive.build_risk_matrix(framework_sections, register)
    severity_dashboard = board_derive.build_severity_dashboard(framework_sections, register)
    status_counts = {label: 0 for label in report_content.ACTION_STATUS_LABELS.values()}
    for action in roadmap_actions:
        status_counts[action["status_label"]] = status_counts.get(action["status_label"], 0) + 1
    overdue_count = sum(
        board_derive.is_overdue(action.get("target_date"), generated_on, action.get("status_label"))
        for action in roadmap_actions
    )
    asks = board_inputs.board_asks(assessment)
    board_asks = {
        "derived": board_derive.derived_asks(
            initiatives,
            observations,
            insufficient_evidence=totals["insufficient_evidence"],
            rfi_open=len(rfi["items"]),
        ),
        "consultant": asks.get("consultant", []),
        "consultant_by": asks.get("consultant_by"),
    }
    theme = _frozen_theme()
    document = {
        "schema_version": DOCUMENT_SCHEMA_VERSION,
        "kind": SNAPSHOT_TYPE,
        "snapshot": {
            "id": snapshot_id,
            "version_label": version_label,
            "generated_at": generated_at.isoformat(),
            "generated_on": display_date(generated_at.isoformat()),
        },
        "firm_name": settings.firm_name,
        "company_name": assessment.company_name,
        "engagement_name": engagement.name if engagement else None,
        "assessment_id": assessment.id,
        "frameworks": frameworks,
        "basis": {
            **basis.to_metadata(),
            "period_label": basis.period_label,
            "cutoff_label": basis.cutoff_label,
        },
        "release": {
            "released_by": release.released_by,
            "released_on": _display_or_none(release.released_at),
        },
        "summary": {
            "basis_of_assessment": _nature_text(framework_ids),
            "scope": [
                f"{review.name}: {len(review.in_scope_ids)} requirements in scope"
                for review in (approved.framework_reviews[framework_id] for framework_id in framework_ids)
            ],
            "limitations": limitations,
            "confidentiality": (
                f"{CONFIDENTIALITY_TEXT} {settings.firm_name} and the named organization "
                "are the intended recipients of this report."
            ),
            "frameworks": summary_frameworks,
            "totals": totals,
            "risk_matrix": risk_matrix,
        },
        "top_risks": top_risks,
        "observations": observations,
        "initiatives": initiatives,
        "status_board": status_board,
        "severity_dashboard": severity_dashboard,
        "takeaways": board_derive.build_takeaways(
            status_board, severity_dashboard, totals, initiatives, observations
        ),
        "board_asks": board_asks,
        "theme": theme,
        "roadmap": {
            "actions": roadmap_actions,
            "unplanned_gap_count": unplanned_gap_count,
            "groups": roadmap_groups,
            "status_counts": status_counts,
            "overdue_count": overdue_count,
        },
        "not_assessed": {
            "insufficient_evidence": [
                {
                    "framework_id": row.framework_id,
                    "requirement_id": row.requirement_id,
                    "requirement_title": row.requirement_title,
                }
                for row in approved.rows
                if row.compliance_status == "insufficient_evidence"
            ],
            "rfi": rfi,
        },
        "framework_sections": framework_sections,
        "sign_off": {
            "prepared_by": basis.prepared_by,
            "reviewed_by": basis.reviewed_by,
            "issue_status": ISSUE_STATUS_TEXT,
            "names_note": SIGN_OFF_NAMES_TEXT,
        },
        "appendices": {
            "methodology": methodology_text(framework_ids, len(approved.rows)),
            "requirement_register": register,
            "evidence_register": _evidence_register(db, assessment, cited_ids),
        },
        "soa": soa.build_soa(db, assessment, approved),
        "source": report_snapshots.source_manifest(db, assessment),
    }
    document["prior_period"] = prior_period.build_comparison(db, assessment, document)
    narrative.apply_to_document(db, assessment, document)
    return document


def render_html(document: dict, *, embed_fonts: bool) -> str:
    # The preview view may normalize an absent owner for text-only consumers;
    # issued documents are rendered with embedded fonts and keep the sidecar null.
    if not embed_fonts:
        for initiative in document.get("initiatives", []):
            if initiative.get("owner") is None:
                initiative["owner"] = ""
    presentation = board_view.view(document)
    presentation.update(
        {
            "p1": document.get("theme", {}).get("primary", "#161A5C"),
            "p2": document.get("theme", {}).get("secondary", "#2D3FD3"),
            "acc": document.get("theme", {}).get("accent", "#12B3A6"),
            "obs_pages": [
                document.get("observations", [])[start : start + 4]
                for start in range(0, presentation["observation_pages"] * 4, 4)
            ] or [[]],
            "reg_pages": [
                document.get("appendices", {}).get("requirement_register", [])[start : start + 21]
                for start in range(0, presentation["register_pages"] * 21, 21)
            ] or [[]],
            "ref_by_finding": {
                observation.get("finding_id"): observation.get("ref")
                for observation in document.get("observations", [])
            },
            "framework_names": {
                framework.get("framework_id"): framework.get("name")
                for framework in document.get("frameworks", [])
            },
        }
    )
    return _templates.get_template(TEMPLATE).render(
        doc=document,
        v=presentation,
        font_face_css=Markup(html_pdf.font_face_css()) if embed_fonts else Markup(""),
        display_font_face_css=(
            Markup(html_pdf.display_font_face_css()) if embed_fonts else Markup("")
        ),
        font_stack=Markup(html_pdf.FONT_STACK),
        embed_fonts=embed_fonts,
        narrative_note=narrative.NARRATIVE_NOTE,
    )


def render_pdf(document: dict) -> bytes:
    rendered = html_pdf.render_pdf(render_html(document, embed_fonts=True))
    # Pango's Devanagari shaping is visually correct but some PDF text
    # extractors split conjuncts.  When Poppler is available, replace only the
    # cover with an fpdf2 text layer whose ToUnicode map preserves the client
    # name; all deck pages and the embedded display font remain WeasyPrint's.
    company = str(document.get("company_name") or "")
    if not any("\u0900" <= character <= "\u097f" for character in company):
        return rendered
    pdfseparate = shutil.which("pdfseparate")
    pdfunite = shutil.which("pdfunite")
    if not pdfseparate or not pdfunite:
        return rendered
    try:
        from fpdf import FPDF

        with tempfile.TemporaryDirectory(prefix="cyberassess-board-") as temp_dir:
            root = Path(temp_dir)
            source = root / "source.pdf"
            source.write_bytes(rendered)
            cover = root / "cover.pdf"
            cover_pdf = FPDF(unit="pt", format=(960, 540))
            cover_pdf.add_page()
            cover_pdf.set_fill_color(22, 26, 92)
            cover_pdf.rect(0, 0, 960, 540, style="F")
            cover_pdf.add_font(
                "Noto Devanagari",
                fname=str(html_pdf.FONT_DIR / "NotoSansDevanagari-Regular.ttf"),
            )
            cover_pdf.set_text_color(255, 255, 255)
            cover_pdf.set_font("helvetica", size=11)
            cover_pdf.text(52, 55, str(document["firm_name"]))
            cover_pdf.set_font("helvetica", size=26)
            cover_pdf.text(52, 180, "Board report")
            cover_pdf.set_font("Noto Devanagari", size=18)
            cover_pdf.text(52, 230, company)
            cover_pdf.set_font("helvetica", size=13)
            cover_pdf.text(52, 275, "Privacy and information security compliance assessment")
            cover_pdf.set_font("helvetica", size=9)
            cover_pdf.text(52, 480, str(document["basis"]["period_label"]))
            cover_pdf.text(300, 480, str(document["basis"]["cutoff_label"]))
            cover_pdf.text(650, 480, str(document["snapshot"]["version_label"]))
            cover.write_bytes(bytes(cover_pdf.output()))
            rest_pattern = str(root / "rest-%d.pdf")
            subprocess.run(
                [pdfseparate, "-f", "2", "-l", str(len(board_view.view(document)["slides"])), str(source), rest_pattern],
                check=True,
                capture_output=True,
            )
            parts = [str(cover)] + [str(root / f"rest-{index}.pdf") for index in range(2, len(board_view.view(document)["slides"]) + 1)]
            output = root / "combined.pdf"
            subprocess.run([pdfunite, *parts, str(output)], check=True, capture_output=True)
            return output.read_bytes()
    except (OSError, RuntimeError, subprocess.SubprocessError):
        return rendered


def generate_version(
    db: Session,
    assessment: Assessment,
    *,
    actor: str,
) -> ReportSnapshot:
    require_review_approval(assessment.id, db)
    narrative.require_report_ready(db, assessment)
    snapshot_id = _new_id()
    sequence = len(
        report_snapshots.snapshot_rows(db, assessment)[SNAPSHOT_TYPE]
    ) + 1
    generated_at = datetime.now(timezone.utc)
    document = build_document(
        db,
        assessment,
        snapshot_id=snapshot_id,
        version_label=f"v{sequence}",
        generated_at=generated_at,
    )
    pdf = render_pdf(document)
    return report_snapshots.create_board_report_snapshot(
        db,
        assessment=assessment,
        snapshot_id=snapshot_id,
        pdf_content=pdf,
        document_content=canonical_bytes(document),
        actor=actor,
    )
