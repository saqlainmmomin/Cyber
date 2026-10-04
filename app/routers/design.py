"""Debug-only Yozora component gallery and template preview routes."""

from collections.abc import Callable
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.dpdpa.context_questions import CONTEXT_BLOCKS
from app.database import get_db
from app.routers.web import templates
from app.services.screening import get_domain_coverage

router = APIRouter(tags=["design"])

# Later slices register preview pages here (for example the unrouted sign-in
# placeholder). S2 deliberately keeps the registry empty.
PREVIEW_PAGES: dict[str, Callable[[Request], Response]] = {}


def login_preview(request: Request) -> Response:
    state = request.query_params.get("state", "default")
    if state not in {"default", "error", "loading"}:
        state = "default"
    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request, "preview_state": state},
    )


PREVIEW_PAGES["login"] = login_preview


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
    def filler(prefix: str, count: int, **extra) -> list[dict]:
        return [
            {"id": f"{prefix}.{index}", "question": f"{prefix} question {index}", "status": "active", "tier": "standard", "source": "base", **extra}
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
        "framework_text": "India DPDPA and ISO 27001",
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
    if name == "b4-desk_review":
        return preview(request, db=db)
    return preview(request)
