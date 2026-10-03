"""Assessment stage (Yozora): where an assessment is in the five-stage flow (Scope, Evidence,
Questionnaire, Review, Report), a short progress note, and the next step. Derived only from what the
app already stores; read-only; never calls a model and never scores.

Rules, first match wins:

1. Scope not recorded (assessment.scope_answers is None) -> scope, "Scope not set", Set scope.
2. No questionnaire answer yet:
   a. no available document (app.services.evidence.analysis_documents) -> evidence,
      "No documents yet", Upload evidence;
   b. a pre-fill (desk review) is running -> evidence, "Pre-fill running", no next step;
   c. the pre-fill has not completed -> evidence, "N documents ready to pre-fill", Pre-fill
      questionnaire.
3. Fewer confirmed answers than questions (question_engine.questionnaire_progress over the
   rendered, non-skipped questions) -> questionnaire, "A of Q answered", Continue questionnaire.
4. No conclusions yet:
   a. analysis running (assessment.status == "analyzing") -> questionnaire, "Analysis running",
      no next step;
   b. otherwise -> questionnaire, "Q of Q answered", Run analysis.
5. Conclusions still pending a decision -> review, "A of C approved", Review N conclusions.
6. Not released (approved_report.release_state) -> report, "A of C approved", Release report.
7. Released without a board report snapshot -> report, "Released D", Generate board report.
8. Otherwise -> report, "Board report generated D", no next step.

"Approved" counts conclusions in an approved or edited decision state (findings.ELIGIBLE_STATES).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.questionnaire import QuestionnaireResponse
from app.models.report_snapshot import ReportSnapshot
from app.services import approved_report, conclusion_review
from app.services import evidence as evidence_service
from app.services.findings import ELIGIBLE_STATES
from app.services.report_snapshots import BOARD_REPORT_SNAPSHOT_TYPE

STAGES = ("scope", "evidence", "questionnaire", "review", "report")
STAGE_LABELS = {
    "scope": "Scope",
    "evidence": "Evidence",
    "questionnaire": "Questionnaire",
    "review": "Review",
    "report": "Report",
}
SET_SCOPE = "Set scope"
UPLOAD_EVIDENCE = "Upload evidence"
PREFILL = "Pre-fill questionnaire"
CONTINUE_QUESTIONNAIRE = "Continue questionnaire"
RUN_ANALYSIS = "Run analysis"
RELEASE_REPORT = "Release report"
GENERATE_BOARD_REPORT = "Generate board report"


@dataclass(frozen=True)
class Stage:
    stage: str
    label: str
    note: str
    next_label: str | None
    next_href: str | None


def _date(moment) -> str:
    return f"{moment.day} {moment:%b %Y}"


def _stage(stage: str, note: str, next_label: str | None = None, next_href: str | None = None) -> Stage:
    return Stage(stage, STAGE_LABELS[stage], note, next_label, next_href)


def review_label(pending: int) -> str:
    return f"Review {pending} conclusion{'s' if pending != 1 else ''}"


def _questionnaire_counts(db: Session, assessment: Assessment) -> tuple[int, int]:
    from app.services.question_engine import build_adaptive_questionnaire, questionnaire_progress

    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    total = sum(
        1
        for section in questionnaire.get("sections", [])
        for question in section.get("questions", [])
        if question.get("status") != "skipped"
    )
    answered = questionnaire_progress(questionnaire, assessment.id, db)["answered_questions"]
    return answered, total


def stage(db: Session, assessment: Assessment) -> Stage:
    base = f"/assessments/{assessment.id}"
    if assessment.scope_answers is None:
        return _stage("scope", "Scope not set", SET_SCOPE, f"{base}?tab=scope")

    responses = db.execute(
        select(func.count()).select_from(QuestionnaireResponse).where(
            QuestionnaireResponse.assessment_id == assessment.id
        )
    ).scalar_one()
    if not responses:
        documents = evidence_service.analysis_documents(db, assessment.id)
        if not documents:
            return _stage("evidence", "No documents yet", UPLOAD_EVIDENCE, f"{base}?tab=documents")
        if assessment.desk_review_status == "analyzing":
            return _stage("evidence", "Pre-fill running")
        if assessment.desk_review_status != "completed":
            count = len(documents)
            return _stage(
                "evidence",
                f"{count} document{'s' if count != 1 else ''} ready to pre-fill",
                PREFILL,
                f"{base}?tab=documents",
            )

    answered, total = _questionnaire_counts(db, assessment)
    if answered < total:
        return _stage(
            "questionnaire", f"{answered} of {total} answered", CONTINUE_QUESTIONNAIRE, f"{base}?tab=questionnaire"
        )

    cards = conclusion_review.conclusion_cards(db, assessment.id)
    if not cards:
        if assessment.status == "analyzing":
            return _stage("questionnaire", "Analysis running")
        return _stage("questionnaire", f"{answered} of {total} answered", RUN_ANALYSIS, f"{base}?tab=questionnaire")

    approved = sum(1 for card in cards if card.state in ELIGIBLE_STATES)
    pending = sum(1 for card in cards if card.state == "pending")
    progress = f"{approved} of {len(cards)} approved"
    if pending:
        return _stage("review", progress, review_label(pending), f"{base}/conclusions")

    release = approved_report.release_state(db, assessment)
    if not release.released:
        return _stage("report", progress, RELEASE_REPORT, f"{base}?tab=report")

    board = db.execute(
        select(ReportSnapshot)
        .where(
            ReportSnapshot.assessment_id == assessment.id,
            ReportSnapshot.type == BOARD_REPORT_SNAPSHOT_TYPE,
        )
        .order_by(ReportSnapshot.generated_at.desc())
        .limit(1)
    ).scalars().first()
    if board is None:
        released = f"Released {_date(release.released_at)}" if release.released_at else "Released"
        return _stage("report", released, GENERATE_BOARD_REPORT, f"{base}/snapshots")
    return _stage("report", f"Board report generated {_date(board.generated_at)}")
