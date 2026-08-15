"""
End-to-end test for Phase 1: Document-Driven Pre-Fill with Signal Override.

Tests the full flow:
  1. Seed a company with desk review data (coverage + signals + evidence)
  2. Run auto_answer.persist_document_answers() → verify signal suppression
  3. Build adaptive questionnaire → verify signals override pre-fills
  4. Simulate confirm/override → verify answer_source transitions

Uses NovaPay fixture from the existing seed data (realistic hidden-gap scenario).
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: E402,F401
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.assessment import Assessment, AssessmentDocument  # noqa: E402
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary  # noqa: E402
from app.models.questionnaire import QuestionnaireResponse  # noqa: E402
from app.services.auto_answer import persist_document_answers  # noqa: E402
from app.services.question_engine import build_adaptive_questionnaire  # noqa: E402

# Import NovaPay fixture builder from seed script
sys.path.insert(0, str(ROOT / "scripts"))
from seed_test_companies import (  # noqa: E402
    ALL_REQUIREMENT_IDS,
    novapay_fixture,
)

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def json_dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True)


def setup_novapay(session) -> tuple[str, dict]:
    """Insert NovaPay fixture with desk review data but WITHOUT questionnaire responses.

    We intentionally omit the seed responses so we can test auto_answer
    creating them from scratch (the real Phase 1 flow).
    """
    fixture = novapay_fixture()
    assessment_id = str(uuid.uuid4())

    assessment = Assessment(
        id=assessment_id,
        company_name=fixture["company_name"] + " [TEST]",
        industry=fixture["industry"],
        company_size=fixture["company_size"],
        description=fixture["description"],
        status="context_gathered",
        context_answers=json_dumps(fixture["context_answers"]),
        context_profile=json_dumps(fixture["context_profile"]),
        desk_review_status="completed",
    )
    session.add(assessment)
    session.flush()

    # Add documents
    doc_id_by_key: dict[str, str] = {}
    catalog = []
    for doc in fixture["documents"]:
        document_id = str(uuid.uuid4())
        session.add(AssessmentDocument(
            id=document_id,
            assessment_id=assessment_id,
            filename=doc.filename,
            file_path=f"test/{assessment_id}/{doc.filename}",
            file_type=doc.file_type,
            document_category=doc.document_category,
            extracted_text=doc.text,
        ))
        doc_id_by_key[doc.key] = document_id
        from scripts.seed_test_companies import page_count
        catalog.append({"filename": doc.filename, "type": doc.file_type, "pages": page_count(doc.text)})

    # Add desk review summary
    session.add(DeskReviewSummary(
        assessment_id=assessment_id,
        document_catalog=json_dumps(catalog),
        coverage_summary=json_dumps(fixture["coverage"]),
        status="completed",
        started_at=NOW,
        completed_at=NOW,
    ))

    # Add desk review findings (evidence + signals + absences)
    for finding in fixture["findings"]:
        session.add(DeskReviewFinding(
            assessment_id=assessment_id,
            finding_type=finding["finding_type"],
            requirement_id=finding["requirement_id"],
            document_id=doc_id_by_key.get(finding["document_key"]) if finding["document_key"] else None,
            content=finding["content"],
            severity=finding["severity"],
            source_quote=finding["source_quote"],
            source_location=finding["source_location"],
        ))

    session.flush()
    return assessment_id, fixture


def get_signal_requirement_ids(fixture: dict) -> set[str]:
    """Get requirement IDs that have signals in the fixture."""
    signal_req_ids = set()
    for finding in fixture["findings"]:
        if finding["finding_type"] in ("signal", "absence") and finding["requirement_id"]:
            signal_req_ids.add(finding["requirement_id"])
    return signal_req_ids


def get_prefillable_requirement_ids(fixture: dict) -> set[str]:
    """Get requirement IDs that have adequate/partial coverage and evidence but NO signals."""
    signal_req_ids = get_signal_requirement_ids(fixture)

    evidence_req_ids = set()
    for finding in fixture["findings"]:
        if finding["finding_type"] == "evidence" and finding["requirement_id"]:
            evidence_req_ids.add(finding["requirement_id"])

    prefillable = set()
    for req_id, coverage_level in fixture["coverage"].items():
        if coverage_level in ("adequate", "partial") and req_id in evidence_req_ids and req_id not in signal_req_ids:
            prefillable.add(req_id)
    return prefillable


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def check(self, condition: bool, description: str):
        if condition:
            self.passed += 1
            print(f"  ✅ {description}")
        else:
            self.failed += 1
            self.errors.append(description)
            print(f"  ❌ {description}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print(f"\nFailed tests:")
            for err in self.errors:
                print(f"  ❌ {err}")
        print(f"{'='*60}")
        return self.failed == 0


def test_auto_answer_signal_suppression(session, assessment_id: str, fixture: dict, results: TestResults):
    """Test that persist_document_answers() skips requirements with signals."""
    print("\n── Test 1: Auto-Answer Signal Suppression ──")

    signal_req_ids = get_signal_requirement_ids(fixture)
    prefillable_req_ids = get_prefillable_requirement_ids(fixture)

    # Run auto-answer
    created_count = persist_document_answers(assessment_id, session)
    session.flush()

    # Load created responses
    responses = session.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment_id
    ).all()
    response_map = {r.question_id: r for r in responses}

    results.check(
        created_count > 0,
        f"Auto-answer created {created_count} responses (expected > 0)"
    )

    # Verify NO signal requirements got pre-filled
    signal_prefilled = []
    for req_id in signal_req_ids:
        resp = response_map.get(req_id)
        if resp and resp.answer_source == "document":
            signal_prefilled.append(req_id)

    results.check(
        len(signal_prefilled) == 0,
        f"No signal requirements pre-filled (found {len(signal_prefilled)}: {signal_prefilled})"
    )

    # Verify signal-free requirements with coverage DID get pre-filled
    prefill_created = []
    for req_id in prefillable_req_ids:
        resp = response_map.get(req_id)
        if resp and resp.answer_source == "document":
            prefill_created.append(req_id)

    results.check(
        len(prefill_created) > 0,
        f"Signal-free requirements pre-filled: {len(prefill_created)} out of {len(prefillable_req_ids)}"
    )

    # Verify specific hidden gap requirements are NOT pre-filled
    # NovaPay ground truth: CH2.CONSENT.2 has a signal about bundled consent → should NOT be pre-filled
    results.check(
        "CH2.CONSENT.2" not in response_map or response_map["CH2.CONSENT.2"].answer_source != "document",
        "CH2.CONSENT.2 (bundled consent signal) NOT pre-filled"
    )

    # BN.NOTIFY.1 has a critical signal about missing DPB notification → should NOT be pre-filled
    results.check(
        "BN.NOTIFY.1" not in response_map or response_map["BN.NOTIFY.1"].answer_source != "document",
        "BN.NOTIFY.1 (missing DPB notification signal) NOT pre-filled"
    )

    # CH2.NOTICE.1 has a signal about vague analytics disclosure → should NOT be pre-filled
    results.check(
        "CH2.NOTICE.1" not in response_map or response_map["CH2.NOTICE.1"].answer_source != "document",
        "CH2.NOTICE.1 (vague analytics disclosure signal) NOT pre-filled"
    )

    # CH2.SECURITY.1 has evidence + adequate coverage + NO signal → SHOULD be pre-filled
    sec1_resp = response_map.get("CH2.SECURITY.1")
    results.check(
        sec1_resp is not None and sec1_resp.answer_source == "document",
        "CH2.SECURITY.1 (adequate coverage, no signal) WAS pre-filled"
    )

    return response_map


def test_question_engine_signal_override(session, assessment_id: str, fixture: dict, results: TestResults):
    """Test that build_adaptive_questionnaire() deepens questions with signals instead of pre-filling."""
    print("\n── Test 2: Question Engine Signal Override ──")

    signal_req_ids = get_signal_requirement_ids(fixture)
    result = build_adaptive_questionnaire(assessment_id, session)

    # Flatten all questions
    all_questions = []
    for section in result["sections"]:
        all_questions.extend(section["questions"])

    question_map = {q["id"]: q for q in all_questions if q.get("source") == "base"}

    # Verify signal requirements are DEEPENED (not pre-filled)
    deepened_signal_reqs = []
    prefilled_signal_reqs = []
    for req_id in signal_req_ids:
        q = question_map.get(req_id)
        if not q:
            continue
        if q["status"] == "deepened":
            deepened_signal_reqs.append(req_id)
        elif q["status"] == "pre_filled":
            prefilled_signal_reqs.append(req_id)

    results.check(
        len(deepened_signal_reqs) > 0,
        f"Signal requirements deepened: {len(deepened_signal_reqs)} ({', '.join(deepened_signal_reqs[:5])}...)"
    )

    results.check(
        len(prefilled_signal_reqs) == 0,
        f"No signal requirements pre-filled by question engine (found {len(prefilled_signal_reqs)}: {prefilled_signal_reqs})"
    )

    # Verify deepened questions have follow-ups enabled
    for req_id in deepened_signal_reqs[:5]:
        q = question_map[req_id]
        results.check(
            q["follow_up_enabled"] is True,
            f"{req_id}: follow_up_enabled=True when deepened"
        )

    # Verify deepened questions show signal content in notes
    consent_q = question_map.get("CH2.CONSENT.2")
    if consent_q:
        results.check(
            consent_q["desk_review_note"] is not None and "Signal detected" in consent_q["desk_review_note"],
            "CH2.CONSENT.2: desk_review_note contains signal text"
        )

    # Verify deepened questions still have evidence attached (side-by-side view)
    for req_id in deepened_signal_reqs[:3]:
        q = question_map[req_id]
        has_evidence = q.get("desk_review_evidence") is not None and len(q["desk_review_evidence"]) > 0
        # Only check if the fixture actually has evidence for this req
        fixture_has_evidence = any(
            f["finding_type"] == "evidence" and f["requirement_id"] == req_id
            for f in fixture["findings"]
        )
        if fixture_has_evidence:
            results.check(
                has_evidence,
                f"{req_id}: evidence attached alongside signal for side-by-side review"
            )

    # Verify signal-free requirements with coverage ARE pre-filled
    prefillable_req_ids = get_prefillable_requirement_ids(fixture)
    prefilled_clean = [
        req_id for req_id in prefillable_req_ids
        if question_map.get(req_id, {}).get("status") == "pre_filled"
    ]

    results.check(
        len(prefilled_clean) > 0,
        f"Signal-free requirements pre-filled: {len(prefilled_clean)} out of {len(prefillable_req_ids)}"
    )

    # Verify stats
    stats = result["stats"]
    results.check(
        stats["pre_filled_questions"] > 0,
        f"Stats show {stats['pre_filled_questions']} pre-filled questions"
    )
    results.check(
        stats["deepened_questions"] > 0,
        f"Stats show {stats['deepened_questions']} deepened questions"
    )

    return question_map


def test_confirm_override_tracking(session, assessment_id: str, results: TestResults):
    """Test that confirming vs overriding a pre-fill sets the correct answer_source."""
    print("\n── Test 3: Confirm vs Override Tracking ──")

    # Find a document pre-fill to confirm
    doc_responses = session.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment_id,
        QuestionnaireResponse.answer_source == "document",
    ).all()

    if len(doc_responses) < 2:
        results.check(False, f"Need at least 2 document pre-fills to test, found {len(doc_responses)}")
        return

    # Simulate confirming the first pre-fill (same answer)
    confirm_resp = doc_responses[0]
    original_answer = confirm_resp.answer
    # Mimic web.py save_questionnaire_responses() logic
    if confirm_resp.answer_source == "document":
        confirm_resp.answer_source = "document_confirmed"
    session.flush()

    results.check(
        confirm_resp.answer_source == "document_confirmed",
        f"{confirm_resp.question_id}: confirm → answer_source='document_confirmed'"
    )

    # Simulate overriding the second pre-fill (different answer)
    override_resp = doc_responses[1]
    old_answer = override_resp.answer
    new_answer = "not_implemented" if old_answer != "not_implemented" else "partially_implemented"
    if override_resp.answer_source == "document":
        override_resp.answer = new_answer
        override_resp.answer_source = "human_override"
    session.flush()

    results.check(
        override_resp.answer_source == "human_override",
        f"{override_resp.question_id}: override → answer_source='human_override'"
    )
    results.check(
        override_resp.answer == new_answer,
        f"{override_resp.question_id}: answer changed from '{old_answer}' to '{new_answer}'"
    )

    # Verify unchanged pre-fills still have answer_source="document"
    remaining = session.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment_id,
        QuestionnaireResponse.answer_source == "document",
    ).count()

    results.check(
        remaining == len(doc_responses) - 2,
        f"Remaining unconfirmed pre-fills: {remaining} (expected {len(doc_responses) - 2})"
    )


def test_hidden_gap_not_prefilled(session, assessment_id: str, fixture: dict, results: TestResults):
    """Verify that hidden gap requirements WITH signals/absences are NOT pre-filled.

    Note: some hidden gap requirements have no signal/absence of their own —
    those are correctly pre-fillable because the documents DO look adequate for
    those specific controls. The gap is hidden precisely because the documents
    say the right things; it only surfaces through follow-up probing.
    """
    print("\n── Test 4: Hidden Gaps with Signals Not Pre-Filled ──")

    signal_req_ids = get_signal_requirement_ids(fixture)

    responses = session.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment_id
    ).all()
    response_map = {r.question_id: r for r in responses}

    hidden_gaps = fixture["hidden_gaps"]

    # Only check hidden gap requirements that HAVE their own signal/absence
    hidden_with_signal = set()
    hidden_without_signal = set()
    for gap in hidden_gaps:
        for req_id in gap["requirement_ids"]:
            if req_id in signal_req_ids:
                hidden_with_signal.add(req_id)
            else:
                hidden_without_signal.add(req_id)

    # Requirements with signals should NOT be pre-filled
    prefilled_hidden_signaled = []
    for req_id in hidden_with_signal:
        resp = response_map.get(req_id)
        if resp and resp.answer_source == "document":
            prefilled_hidden_signaled.append(req_id)

    results.check(
        len(prefilled_hidden_signaled) == 0,
        f"Hidden gap reqs WITH signals: 0 pre-filled (found {len(prefilled_hidden_signaled)}: {prefilled_hidden_signaled})"
    )

    # Report on hidden gap reqs WITHOUT signals (these are pre-fillable — by design)
    prefilled_hidden_no_signal = []
    for req_id in hidden_without_signal:
        resp = response_map.get(req_id)
        if resp and resp.answer_source == "document":
            prefilled_hidden_no_signal.append(req_id)

    print(f"  ℹ️  Hidden gap reqs without own signal ({len(hidden_without_signal)}): {sorted(hidden_without_signal)}")
    print(f"  ℹ️  Of those, pre-filled: {len(prefilled_hidden_no_signal)} — these need follow-up probing to surface")

    # Check each hidden gap group
    for gap in hidden_gaps:
        req_ids = gap["requirement_ids"]
        gap_label = ", ".join(req_ids[:2])
        signaled_ids = [r for r in req_ids if r in signal_req_ids]
        any_signaled_prefilled = any(
            response_map.get(rid, type("X", (), {"answer_source": None})()).answer_source == "document"
            for rid in signaled_ids
        )
        if signaled_ids:
            results.check(
                not any_signaled_prefilled,
                f"Hidden gap [{gap_label}] ({gap['actual_status']}): signaled reqs NOT pre-filled"
            )
        else:
            print(f"  ℹ️  Hidden gap [{gap_label}] ({gap['actual_status']}): no own signals — relies on follow-up probing")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Phase 1 E2E Test: Document Pre-Fill with Signal Override")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    results = TestResults()

    try:
        # Setup
        print("\n── Setup: Seeding NovaPay [TEST] ──")
        assessment_id, fixture = setup_novapay(session)
        session.commit()

        signal_req_ids = get_signal_requirement_ids(fixture)
        prefillable_req_ids = get_prefillable_requirement_ids(fixture)
        print(f"  Requirements with signals: {len(signal_req_ids)}")
        print(f"  Requirements pre-fillable (clean): {len(prefillable_req_ids)}")
        print(f"  Total requirements: {len(ALL_REQUIREMENT_IDS)}")

        # Test 1: auto_answer signal suppression
        test_auto_answer_signal_suppression(session, assessment_id, fixture, results)
        session.commit()

        # Test 2: question engine signal override
        test_question_engine_signal_override(session, assessment_id, fixture, results)

        # Test 3: confirm/override tracking
        test_confirm_override_tracking(session, assessment_id, results)
        session.commit()

        # Test 4: hidden gap cross-check
        test_hidden_gap_not_prefilled(session, assessment_id, fixture, results)

        # Summary
        all_passed = results.summary()

    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    finally:
        # Cleanup: remove test data
        print("\n── Cleanup ──")
        try:
            session.query(QuestionnaireResponse).filter(
                QuestionnaireResponse.assessment_id == assessment_id
            ).delete()
            session.query(DeskReviewFinding).filter(
                DeskReviewFinding.assessment_id == assessment_id
            ).delete()
            session.query(DeskReviewSummary).filter(
                DeskReviewSummary.assessment_id == assessment_id
            ).delete()
            session.query(AssessmentDocument).filter(
                AssessmentDocument.assessment_id == assessment_id
            ).delete()
            session.query(Assessment).filter(
                Assessment.id == assessment_id
            ).delete()
            session.commit()
            print("  Cleaned up test data")
        except Exception:
            session.rollback()
        finally:
            session.close()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
