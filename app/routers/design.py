"""Debug-only Yozora component gallery and template preview routes."""

from collections.abc import Callable
from datetime import datetime, timezone
import json
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.dpdpa.context_questions import CONTEXT_BLOCKS
from app.database import get_db
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.engagement import Engagement
from app.routers.web import templates
from app.services import aws_evidence, workpaper
from app.services.screening import get_domain_coverage

router = APIRouter(tags=["design"])

# Debug-only pages that do not have standalone production routes register here.
PREVIEW_PAGES: dict[str, Callable[[Request, Session], Response]] = {}


def login_preview(request: Request, db: Session | None = None) -> Response:
    state = request.query_params.get("state", "default")
    if state not in {"default", "error", "loading"}:
        state = "default"
    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request, "preview_state": state},
    )


PREVIEW_PAGES["login"] = login_preview


def aws_evidence_preview(request: Request, db: Session) -> Response:
    state = request.query_params.get("state", "ready")
    if state not in {"ready", "pulling", "result", "error", "notconfigured"}:
        state = "ready"
    engagement = (
        db.query(Engagement)
        .join(Client, Client.id == Engagement.client_id)
        .filter(Client.name == "Meridian Ledger Technologies")
        .order_by(Engagement.created_at, Engagement.id)
        .first()
        or db.query(Engagement).order_by(Engagement.created_at, Engagement.id).first()
    )
    client = db.get(Client, engagement.client_id) if engagement else None
    engagement = engagement or SimpleNamespace(id="preview-engagement", name="Preview engagement", client_id="preview-client")
    client = client or SimpleNamespace(id="preview-client", name="Meridian Ledger Technologies")
    context = aws_evidence.page_context(db, engagement)
    external_id = "preview-external-id-1234567890"
    context.update(
        {
            "request": request,
            "engagement": engagement,
            "client": client,
            "configured": True,
            "external_id": external_id,
            "suggested_role_name": "YozoraReadOnlyAudit",
            "trust_policy_json": json.dumps(aws_evidence.trust_policy(external_id), indent=2),
            "permissions_policy_json": json.dumps(aws_evidence.permissions_policy(aws_evidence.EXAMPLE_ACCOUNT_ID), indent=2),
            "consultant_policy_json": json.dumps(aws_evidence.consultant_policy(), indent=2).replace("ComplianceEvidenceReadOnly", "YozoraReadOnlyAudit"),
        }
    )
    context["preview_state"] = state
    if state == "error":
        # Fixture copy for the refused-role alert (the mockup's wording); live pulls show
        # the service's own message from AwsPullFailed.
        context["error_title"] = "AWS refused the role"
        context["error"] = "Check the role ARN and the external ID, then pull again. No evidence was collected."
    if state == "result":
        started_at = datetime(2026, 3, 21, 10, tzinfo=timezone.utc)
        context["result"] = aws_evidence.PullResult(
            pull_id="preview-pull-001",
            account_id=aws_evidence.EXAMPLE_ACCOUNT_ID,
            regions=("ap-south-1", "us-east-1"),
            sources=(
                aws_evidence.SourceSummary("aws_config", "ap-south-1", "collected", 142, 12, 3, 127, 0, False, 0),
                aws_evidence.SourceSummary("aws_securityhub", "ap-south-1", "collected", 31, 4, 2, 25, 0, False, 0),
                aws_evidence.SourceSummary("aws_securityhub", "us-east-1", "not_enabled", 0, 0, 0, 0, 0, False, 0),
            ),
            evidence_ids=(),
            started_at=started_at,
            finished_at=datetime(2026, 3, 21, 10, 4, tzinfo=timezone.utc),
        )
    return templates.TemplateResponse(
        "pages/aws_evidence.html",
        context,
    )


PREVIEW_PAGES["aws_evidence"] = aws_evidence_preview


def evidence_reuse_preview(request: Request, db: Session) -> Response:
    """The real evidence-reuse page for ``?assessment=<id>``. ``?state=error`` renders the
    acknowledgement error exactly as the confirm route returns it when a warning-bearing
    candidate is confirmed without the tick; the live page never shows it from a query."""
    from app.routers.evidence_reuse import ACK_REQUIRED_TITLE, _page_context
    from app.services import evidence_reuse

    assessment = db.get(Assessment, request.query_params.get("assessment") or "")
    if assessment is None:
        raise HTTPException(status_code=404, detail="Pass ?assessment=<id>")
    error = request.query_params.get("state") == "error"
    return templates.TemplateResponse(
        "pages/evidence_reuse.html",
        _page_context(
            request,
            db,
            assessment,
            error=evidence_reuse.REUSE_ACK_REQUIRED if error else None,
            error_title=ACK_REQUIRED_TITLE if error else None,
        ),
    )


PREVIEW_PAGES["evidence_reuse"] = evidence_reuse_preview


def _workpaper_entry_matches(entry, state: str) -> bool:
    if state == "legacy":
        return entry.in_scope and entry.card.legacy_bulk_approval
    if state == "excluded":
        return not entry.in_scope
    return entry.in_scope and entry.card.state == "edited"


def workpaper_entry_preview(request: Request, db: Session) -> Response:
    """Render one real workpaper entry as the entry page (no production route exists).

    ``?entry=<anchor>`` picks an entry; otherwise the state picks the first entry that
    has that shape in the seeded data: an edited conclusion (default), a legacy bulk
    approval (legacy) or a scope-excluded conclusion (excluded). The fixture below is
    used only when the database holds no conclusions at all."""
    state = request.query_params.get("state", "default")
    if state not in {"default", "legacy", "excluded"}:
        state = "default"
    anchor = request.query_params.get("entry")
    assessments = db.query(Assessment).order_by(Assessment.created_at, Assessment.id).all()
    found = []
    for candidate in assessments:
        sections = workpaper.build_workpaper(db, candidate).sections
        found.extend(
            (candidate, item)
            for section in sections
            for item in (*section.entries, *section.excluded_entries)
        )
    match = next(((a, e) for a, e in found if anchor and e.anchor == anchor), None)
    match = match or next(((a, e) for a, e in found if _workpaper_entry_matches(e, state)), None)
    match = match or (found[0] if found else None)
    if match is not None:
        assessment, entry = match
        from app.services.report_basis import basis_for

        basis = basis_for(assessment)
        engagement = db.get(Engagement, assessment.engagement_id) if assessment.engagement_id else None
        client = db.get(Client, engagement.client_id) if engagement else None
    else:
        assessment = SimpleNamespace(
            id="preview-assessment",
            display_name="Preview assessment",
            company_name="Meridian Ledger Technologies",
            frameworks=["dpdpa"],
        )
        conclusion = SimpleNamespace(
            framework_id="dpdpa", requirement_id="DPDPA-1", version=1, id="preview-conclusion",
            ai_proposed=True, outcome="compliant", risk_level="low", rationale="Documented practice",
            gaps_identified="None recorded", recommended_action="Maintain the control",
            evidence_summary="Privacy notice.pdf supports the conclusion",
        )
        card = SimpleNamespace(
            conclusion=conclusion, requirement_title="Privacy notice and transparency", state="approved",
            locked=True, legacy_bulk_approval=state == "legacy", legacy_report_status=None, last_decision=None,
            previous_outcome=None, unsupported_assertion=False, withheld_proposal=None,
        )
        entry = SimpleNamespace(
            card=card, anchor="wp-dpdpa-DPDPA-1", in_scope=state != "excluded", client_response=None,
            mapped_evidence=[], desk_review_findings=[], ai_proposal=None, revisions=[], findings=[],
        )
        basis = None
        engagement = client = None
    return templates.TemplateResponse(
        "pages/workpaper.html",
        {
            "request": request,
            "assessment": assessment,
            "preview_entry": entry,
            "preview_basis": basis,
            "engagement": engagement,
            "client": client,
        },
    )


PREVIEW_PAGES["workpaper_entry"] = workpaper_entry_preview


S5_PREVIEW_STATES = {
    "b3-screening-form": ("default", "loading", "error", "complete", "screened"),
    "b3-context-complete": ("default",),
    "b3-question-step": ("org", "data", "data-yes", "last"),
    "b3-followups": ("loaded",),
    "b3-sections": ("default", "saved", "empty"),
    "b3-section-questions": ("default",),
    "b4-desk_review": ("ready", "running", "findings", "rerun", "error"),
}


def _b4_desk_review_live(request: Request, db: Session, state: str) -> Response | None:
    """s5-prefill: render the b4 results page from a real assessment.

    With ``?assessment_id=`` this is the live ``/assessments/{id}/desk-review``
    page (same template and context) with polling switched off.
    ``rerun`` shows the findings; the live re-run asks through ``hx-confirm``.
    """
    from app.models.assessment import Assessment
    from app.routers.web import desk_review_page_context

    assessment_id = request.query_params.get("assessment_id")
    assessment = db.get(Assessment, assessment_id) if assessment_id else None
    if assessment is None:
        return None
    context = desk_review_page_context(request, db, assessment)
    context.update({"screen": "b4-desk_review", "state": state, "preview_static": True})
    return templates.TemplateResponse("pages/desk_review.html", context)


# s5-quest: questionnaire sections fixture (b3-sections, b3-section-questions previews).
def _s5_questionnaire_fixture(screen: str, state: str) -> dict:
    filler_questions = {
        "RIGHTS": (
            "Can a data principal ask for a summary of the personal data you process about them?",
            "Is there a documented process to correct or complete inaccurate personal data?",
            "Can a data principal ask for their personal data to be erased?",
            "Is each rights request answered within a defined time?",
            "Can a data principal nominate someone to exercise their rights?",
            "Is there a grievance channel that is published in the privacy notice?",
            "Are rights requests logged with their outcome?",
            "Is the identity of a requester verified before data is shared?",
        ),
        "ACCESS": (
            "Is access to personal data granted on a need-to-know basis?",
            "Are user accounts reviewed at least every quarter?",
            "Is access removed on the day an employee leaves?",
            "Do administrators use separate privileged accounts?",
            "Is multi-factor authentication required for remote access?",
            "Are shared accounts prohibited or individually tracked?",
            "Are access requests approved by the data owner?",
            "Is access to production data logged?",
            "Are service accounts inventoried with an owner?",
        ),
        "ACCESS.DEEP": ("Are access logs reviewed for unusual activity?",),
        "PAY": (
            "Are card numbers stored only in tokenised form?",
            "Is lending data shared only with registered partners?",
            "Are payment processors bound by a data processing agreement?",
            "Is repayment history kept only for the period the law requires?",
            "Are credit decisions explained to the borrower?",
            "Is access to payment records limited to the payments team?",
            "Are collection agents bound by the same privacy terms?",
        ),
        "SAFE": (
            "Is personal data encrypted at rest?",
            "Is personal data encrypted in transit?",
            "Are backups tested at least once a year?",
            "Are systems patched within a defined window?",
            "Is there a written incident response plan?",
            "Are security events monitored around the clock?",
            "Are laptops protected with full-disk encryption?",
            "Is malware protection installed on every endpoint?",
            "Are penetration tests run at least once a year?",
        ),
        "POLICY": (
            "Is there an approved information security policy?",
            "Is the policy reviewed at least once a year?",
            "Have all employees acknowledged the policy?",
            "Is a named owner accountable for the policy?",
            "Are policy exceptions recorded and approved?",
        ),
    }

    def filler(prefix: str, count: int, **extra) -> list[dict]:
        return [
            {"id": f"{prefix}.{index}", "question": filler_questions[prefix][index - 1], "status": "active", "tier": "standard", "source": "base", **extra}
            for index in range(1, count + 1)
        ]

    notice = [
        {"id": "CH2.NOTICE.1", "question": "Does every consent request name each purpose in plain language?", "status": "active", "tier": "deep",
         "criticality": "critical", "source": "base", "guidance": "Check sign-up, checkout and marketing preferences.",
         "desk_review_evidence": [{"content": "Purposes are listed in the privacy notice.", "source_quote": "We use your personal data to provide the ledger service, prevent fraud and send service notices. Marketing messages are sent only if you opt in.", "source_location": "privacy_notice_v3.2.pdf, page 4"}]},
        {"id": "CH2.CONSENT.1", "question": "Can a data principal withdraw consent as easily as they gave it?", "status": "pre_filled", "tier": "standard",
         "criticality": "high", "source": "base", "pre_fill_source": "document", "pre_fill_answer": "partially_implemented", "pre_fill_confidence": "medium",
         "pre_fill_evidence_summary": "Withdrawal requests are accepted by email to privacy@meridianledger.example and processed by the support team. No in-app control is described.",
         "desk_review_evidence": [{"content": "Withdrawal is handled by email.", "source_quote": "processed by the support team", "source_location": "consent_policy.docx, page 2"}]},
        {"id": "CH2.CONSENT.2", "question": "Is each consent stored with a timestamp and the notice version?", "status": "pre_filled", "tier": "standard",
         "criticality": "medium", "source": "base", "pre_fill_source": "inferred", "pre_fill_answer": "fully_implemented", "pre_fill_confidence": "high"},
        {"id": "CH2.CHILD.1", "question": "Is verifiable parental consent obtained before processing a child's data?", "status": "skipped", "tier": "skip", "source": "base",
         "skip_reason": "Out of scope. The scope records no processing of children's data.",
         "desk_review_evidence": [{"content": "All users are adults.", "source_quote": "Age at sign-up: 18 or over, verified at onboarding.", "source_location": "data_inventory.xlsx, page Sheet 2"}]},
        {"id": "CH2.NOTICE.2", "question": "Are notices offered in the languages your data principals read?", "status": "active", "tier": "standard",
         "criticality": "medium", "source": "base", "guidance": "Count the languages used in your apps and customer support."},
        {"id": "CH2.CONSENT.3", "question": "Which processors receive consent records?", "status": "deepened", "tier": "standard", "criticality": "medium", "source": "base",
         "desk_review_note": "Your earlier answer conflicts with the vendor list, which names two processors that hold consent records."},
    ]
    if screen == "b3-sections":
        # The sections mockup shows three cards of this section, in this order.
        notice = [notice[4], notice[1], notice[2]]
    sections = [
        {"section_id": "notice", "section_title": "Notice and consent", "chapter_title": "Obligations of the data fiduciary", "source": "base", "questions": notice},
        {"section_id": "rights", "section_title": "Data principal rights", "chapter_title": "Rights and duties of the data principal", "source": "base", "questions": filler("RIGHTS", 8)},
        {"section_id": "access", "section_title": "Access control", "chapter_title": "Technical safeguards", "source": "base", "questions": filler("ACCESS", 9) + filler("ACCESS.DEEP", 1, tier="deep")},
        {"section_id": "industry.payments", "section_title": "Payments and lending", "chapter_title": "Industry-specific", "source": "industry", "questions": filler("PAY", 7, source="industry")},
        {"section_id": "safeguards", "section_title": "Security safeguards", "chapter_title": "Technical safeguards", "source": "base", "questions": filler("SAFE", 9)},
        {"section_id": "policy", "section_title": "Information security policy", "chapter_title": "Governance", "source": "base", "questions": filler("POLICY", 5)},
    ]
    existing = {
        "CH2.CONSENT.1": {"answer": "partially_implemented"},
        "CH2.CONSENT.2": {"answer": "fully_implemented"},
        "CH2.CONSENT.3": {"answer": "partially_implemented"},
    }
    for prefix, count in (("ACCESS", 3), ("SAFE", 9), ("POLICY", 5)):
        existing.update({f"{prefix}.{index}": {"answer": "fully_implemented"} for index in range(1, count + 1)})
    if state == "empty":
        sections = []
    selected = sections[0] if sections else {"section_id": None, "section_title": "", "chapter_title": "", "questions": []}
    return {
        "sections": sections,
        "existing": existing,
        "stats": {"total_questions": 42, "answered_questions": 18, "awaiting_confirmation": 6, "deepened_questions": 5},
        "selected_section_id": selected["section_id"],
        "section_id": selected["section_id"],
        "section_title": selected["section_title"],
        "chapter_title": selected["chapter_title"],
        "questions": selected["questions"],
    }


def _s5_preview(request: Request, screen: str, db: Session | None = None) -> Response:
    states = S5_PREVIEW_STATES[screen]
    state = request.query_params.get("state", states[0])
    if state not in states:
        state = states[0]
    if screen == "b4-desk_review" and db is not None:
        live = _b4_desk_review_live(request, db, state)
        if live is not None:
            return live

    assessment_id = "assessment-s5-preview"
    assessment = SimpleNamespace(
        id=assessment_id,
        display_name="Head office",
        company_name="Meridian Ledger Technologies",
        status="created",
    )
    engagement = SimpleNamespace(id="engagement-s5-preview", name="FY2026 privacy readiness")
    period = SimpleNamespace(period="1 Apr 2025 to 31 Mar 2026", cutoff="15 Mar 2026")
    block_index = {"org": 0, "data": 1, "data-yes": 0, "last": len(CONTEXT_BLOCKS) - 1}.get(state, 0)
    sections = [
        {
            "section_id": "notice",
            "section_title": "Notice and consent",
            "chapter_title": "Obligations of the data fiduciary",
            "source": "base",
            "questions": [
                {
                    "id": "CH2.NOTICE.1",
                    "question": "Does every notice name each purpose in plain language?",
                    "status": "active",
                    "tier": "deep",
                    "guidance": "Check sign-up, checkout and marketing preferences.",
                    "source": "base",
                },
                {
                    "id": "CH2.CONSENT.1",
                    "question": "Can a data principal withdraw consent as easily as they gave it?",
                    "status": "pre_filled",
                    "tier": "standard",
                    "guidance": "The answer counts once you save the section.",
                    "source": "base",
                    "pre_fill_source": "document",
                    "pre_fill_answer": "partially_implemented",
                    "pre_fill_confidence": "medium",
                    "pre_fill_evidence_summary": "Withdrawal requests are accepted by email and processed by the support team.",
                    "desk_review_evidence": [{
                        "content": "Withdrawal requests are accepted by email.",
                        "source_quote": "processed by the support team",
                        "source_location": "Consent policy, page 2",
                    }],
                },
            ],
        },
        {
            "section_id": "industry.payments",
            "section_title": "Payments and lending",
            "chapter_title": "Industry-specific",
            "source": "industry",
            "questions": [{
                "id": "IND.PAY.1",
                "question": "Are payment records protected throughout their lifecycle?",
                "status": "active",
                "tier": "standard",
                "guidance": "Include payment processors and support tooling.",
                "source": "industry",
            }],
        },
    ]
    selected_section = sections[0]
    common = {
        "request": request,
        "screen": screen,
        "state": state,
        "assessment_id": assessment_id,
        "assessment": assessment,
        "engagement": engagement,
        "period": period,
        "tab": "questionnaire",
        "active_framework": "dpdpa",
        "engagement_archived": False,
        "workflow": {"action_href": None},
        "preview_state": state,
        "questionnaire_child": screen in {"b3-screening-form", "b3-context-complete", "b3-question-step", "b3-followups"},
        "preview_rendered": True,
        "preview_static": True,
        "standalone_preview": True,
        "page_title": {
            "b3-screening-form": "Domain screening",
            "b3-context-complete": "Context",
            "b3-question-step": "Context",
            "b3-followups": "Notice and consent",
            "b3-sections": "Questionnaire",
            "b3-section-questions": "Notice and consent",
            "b4-desk_review": "Pre-fill from documents",
        }[screen],
    }
    common.update({
        "screening_available": True,
        "screening_done": screen == "b3-screening-form" and state == "complete",
        "error": (
            "The model did not respond in time. Your answers are kept. Run screening again."
            if screen == "b3-screening-form"
            else "The screening service did not respond. Your answers are kept."
        ) if state == "error" else None,
        "tier_counts": {"deep": 12, "standard": 21, "light": 9, "skip": 0},
        "domains": get_domain_coverage(),
        "block": CONTEXT_BLOCKS[block_index],
        "block_index": block_index,
        "total_blocks": len(CONTEXT_BLOCKS),
        "followups": [
            {"id": "FU.CH2.CONSENT.1.1", "text": "Which channels can withdraw consent today?", "reason": "Your answer is partial, so this shows how far coverage goes."},
            {"id": "FU.CH2.CONSENT.1.2", "text": "Is withdrawal processed within a defined time?", "reason": ""},
        ],
        "sections": sections,
        "existing": {"CH2.CONSENT.1": {"answer": "partially_implemented"}},
        "stats": {"total_questions": 3, "answered_questions": 1, "awaiting_confirmation": 1, "pre_filled_questions": 1, "inferred_questions": 0, "deepened_questions": 1, "industry_questions": 1, "tier_counts": {"deep": 1, "standard": 2, "light": 0, "skip": 0}},
        "selected_section_id": selected_section["section_id"],
        "section_id": selected_section["section_id"],
        "section_title": selected_section["section_title"],
        "chapter_title": selected_section["chapter_title"],
        "questions": selected_section["questions"],
        "prefill_available": 6,
        "prefill_freshness": SimpleNamespace(available=6, new_since_last_prefill=3, last_prefill_at=datetime.now(timezone.utc)),
        "framework_names": ["DPDPA 2023", "ISO 27001:2022"],
        "catalog": [{"filename": f"policy-{index}.pdf"} for index in range(1, 7)],
        "evidence": [{"requirement_id": "CH2.CONSENT.1", "content": "Withdrawal is handled by email.", "source_quote": "processed by the support team", "source_location": "Consent policy, page 2"}],
        "absences": [{"requirement_id": "CH4.SDF.1", "content": "No retained evidence of the latest access review was found.", "severity": "high", "source_location": "Policy 2026, page 4"}],
        "signals": [{"content": "Operating evidence is incomplete.", "severity": "medium", "source_quote": "Evidence is retained by the control owner.", "source_location": "Policy 2026, page 5", "requirement_ids": ["CH4.SDF.1"]}],
        "coverage": {"CH2.CONSENT.1": "partial", "CH4.SDF.1": "absent"},
        "failed_framework_names": [],
        "total_findings": 3,
        "document_count": 6,
        "framework_text": "DPDPA and ISO 27001",
        "desk_review_partial": {
            "ready": "partials/desk_review_ready.html",
            "running": "partials/desk_review_running.html",
            "error": "partials/desk_review_error.html",
        }.get(state, "partials/desk_review_findings.html"),
        "questionnaire_surface": False,
    })
    if screen in {"b3-sections", "b3-section-questions"}:
        common.update(_s5_questionnaire_fixture(screen, state))
    if screen == "b4-desk_review":
        return templates.TemplateResponse("pages/desk_review.html", common)
    return templates.TemplateResponse("pages/design_assessment_preview.html", common)


for _screen in S5_PREVIEW_STATES:
    PREVIEW_PAGES[_screen] = lambda request, screen=_screen, db=None: _s5_preview(request, screen, db)


# Transient states of live assessment pages. Live routes ignore ``?state=``;
# these previews render the real page for a real assessment
# (``?assessment_id=``) with the state set here, so only the design preview can
# show a loading skeleton, a load error or a saving placeholder.
S5_LIVE_PREVIEWS = {
    "b3-hub": ("overview", ("loading", "error")),
    "b3-scope": ("scope", ("error", "saving")),
    "b3-scope-complete": ("scope", ("loading", "error")),
}


def _s5_live_preview(request: Request, screen: str, db: Session) -> Response:
    from app.routers.web import render_assessment_detail

    tab, states = S5_LIVE_PREVIEWS[screen]
    state = request.query_params.get("state")
    assessment_id = request.query_params.get("assessment_id")
    if state not in states or not assessment_id:
        raise HTTPException(status_code=404, detail="Not found")
    # Render as if at the live URL, so the shell, breadcrumb and engagement
    # context come from the same context processors as the real page.
    path = f"/assessments/{assessment_id}"
    live_request = Request(dict(request.scope, path=path, raw_path=path.encode()), request.receive)
    return render_assessment_detail(live_request, db, assessment_id, tab=tab, preview_state=state)


for _screen in S5_LIVE_PREVIEWS:
    PREVIEW_PAGES[_screen] = lambda request, screen=_screen, db=None: _s5_live_preview(request, screen, db)

DB_PREVIEWS = {"b4-desk_review", *S5_LIVE_PREVIEWS, "aws_evidence", "evidence_reuse", "workpaper_entry"}


def _debug_only() -> None:
    if settings.env.casefold() == "production":
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/design", response_class=HTMLResponse, include_in_schema=False)
def design_gallery(request: Request) -> Response:
    _debug_only()
    return templates.TemplateResponse(
        "pages/design.html",
        {
            "request": request,
            "dark": "dark" in request.query_params,
            "focus": "focus" in request.query_params,
        },
    )


@router.get("/design/pages/{name}", response_class=HTMLResponse, include_in_schema=False)
def design_preview(request: Request, name: str, db: Session = Depends(get_db)) -> Response:
    _debug_only()
    preview = PREVIEW_PAGES.get(name)
    if preview is None:
        raise HTTPException(status_code=404, detail="Not found")
    if name in DB_PREVIEWS:
        return preview(request, db=db)
    return preview(request)


# S7 preview fixtures live in app/routers/design_s7_*.py; each module registers
# its own PREVIEW_PAGES entries on import so slice groups never share this file.
def _load_s7_previews() -> None:
    import importlib
    import pkgutil

    import app.routers as routers_package

    for module in pkgutil.iter_modules(routers_package.__path__):
        if module.name.startswith("design_s7_"):
            importlib.import_module(f"app.routers.{module.name}")


_load_s7_previews()


# S8 preview fixtures follow the same group-owned registration pattern as S7.
def _load_s8_previews() -> None:
    import importlib
    import pkgutil

    import app.routers as routers_package

    for module in pkgutil.iter_modules(routers_package.__path__):
        if module.name.startswith("design_s8_"):
            importlib.import_module(f"app.routers.{module.name}")


_load_s8_previews()
