"""P6-0f: DPDPA pack follow-ups (Saqlain's decisions on the P6-0e open questions)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.dpdpa.framework import DPDPA_READINESS_NOTE, get_all_requirements
from app.dpdpa.questionnaire import _GUIDANCE_TEXT, _QUESTION_TEXT
from app.dpdpa.scope_questions import SCOPE_QUESTIONS, S17_3_REQUIREMENT_IDS
from app.services.scope_profiler import compute_scope, compute_scope_multi

REPO_ROOT = Path(__file__).resolve().parents[1]
REQS = {req["id"]: req for req in get_all_requirements()}


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def test_1_transfer_2_rewritten_around_section_16():
    req = REQS["CB.TRANSFER.2"]
    assert req["section_ref"] == "Section 16"
    assert "s.16(1)" in req["description"] and "s.16(2)" in req["description"]
    assert "contract" not in req["title"].lower() and "contract" not in req["description"].lower()
    assert "contract" not in _QUESTION_TEXT["CB.TRANSFER.2"].lower()
    assert "Section 16 requires contractual" not in _GUIDANCE_TEXT["CB.TRANSFER.2"]
    assert "supporting evidence only" in _GUIDANCE_TEXT["CB.TRANSFER.2"]


def test_2_records_2_is_change_of_purpose_only():
    req = REQS["CM.RECORDS.2"]
    assert req["section_ref"] == "Section 6(1)"
    for text in (req["title"], req["description"], _QUESTION_TEXT["CM.RECORDS.2"], _GUIDANCE_TEXT["CM.RECORDS.2"]):
        assert "reasonable period" not in text
        assert "refresh" not in text.lower()
    assert "new or changed purpose" in req["description"]
    assert "new or changed purpose" in _QUESTION_TEXT["CM.RECORDS.2"]


def test_3_consent_2_and_granular_1_split():
    consent2 = REQS["CH2.CONSENT.2"]["description"]
    granular1 = REQS["CM.GRANULAR.1"]["description"]
    assert "consent request" in consent2 and "records consent" in consent2 and "CM.GRANULAR.1" in consent2
    assert "toggles" in granular1 and "partial consent" in granular1 and "CH2.CONSENT.2" in granular1
    assert "toggle" not in consent2
    assert "record" not in _QUESTION_TEXT["CM.GRANULAR.1"]
    assert "toggle" not in _QUESTION_TEXT["CH2.CONSENT.2"]
    assert "CM.GRANULAR.1" in _GUIDANCE_TEXT["CH2.CONSENT.2"]
    assert "CH2.CONSENT.2" in _GUIDANCE_TEXT["CM.GRANULAR.1"]


SPDI = "Information Technology Act, 2000, s.43A and the SPDI Rules, 2011"


def test_4_spdi_sentence_in_note_and_rendered_under_same_gate():
    from tests.test_p6_0e_dpdpa_pack_correctness import AFTER, BEFORE, _board_pdf

    assert SPDI in DPDPA_READINESS_NOTE
    assert DPDPA_READINESS_NOTE.endswith("continue to apply and were not assessed.")
    assert "s.43A" in _board_pdf(["dpdpa"], BEFORE)
    assert "s.43A" not in _board_pdf(["iso27001"], BEFORE)
    assert "s.43A" not in _board_pdf(["dpdpa"], AFTER)


def test_5_scp6_yes_proposes_verified_s17_3_set_without_excluding():
    scp6 = next(q for q in SCOPE_QUESTIONS if q["id"] == "SCP.6")
    assert "s.17(3)" in scp6["question"]
    assert [o["value"] for o in scp6["options"]] == ["yes", "no", "unsure"]
    assert "consultant confirms" in scp6["help_text"]
    assert len(SCOPE_QUESTIONS) == 6

    # The set is derived from the section_refs that cite a provision s.17(3) names.
    exempt = re.compile(r"Section (5\b|8\(3\)|8\(7\)|10\b|10\(|11\b|11\()")
    derived = {rid for rid, req in REQS.items() if exempt.search(req["section_ref"])}
    assert set(S17_3_REQUIREMENT_IDS) == derived
    assert "CH2.NOTICE.3" not in derived

    answers = {"SCP.1": "yes", "SCP.2": "yes", "SCP.3": "yes", "SCP.4": "both", "SCP.5": "yes", "SCP.6": "yes"}
    multi = compute_scope_multi(answers, ["dpdpa"])
    proposed = [p["control_id"] for p in multi["proposed_not_applicable"]]
    assert proposed == list(S17_3_REQUIREMENT_IDS)
    assert all(p["framework_id"] == "dpdpa" and p["scope_question_id"] == "SCP.6" for p in multi["proposed_not_applicable"])
    assert multi["excluded_requirements"] == []
    assert set(S17_3_REQUIREMENT_IDS) <= set(multi["applicable_requirements"])
    assert compute_scope(answers)["excluded_requirements"] == []

    # Already-excluded SDF requirements are not proposed a second time.
    not_sdf = compute_scope_multi({**answers, "SCP.3": "no"}, ["dpdpa"])
    assert not any(p["control_id"].startswith("CH4.SDF") for p in not_sdf["proposed_not_applicable"])

    for other in ("no", "unsure"):
        assert compute_scope_multi({**answers, "SCP.6": other}, ["dpdpa"])["proposed_not_applicable"] == []


def test_5b_scp6_proposals_get_display_titles():
    from app.routers.web import _with_control_titles

    proposals = _with_control_titles(compute_scope_multi({"SCP.6": "yes"}, ["dpdpa"])["proposed_not_applicable"])
    for p in proposals:
        assert p["control_title"] == REQS[p["control_id"]]["title"]
        assert p["framework_name"] == "India DPDPA"


def test_6_notice_1_r3a_folded_in():
    req = REQS["CH2.NOTICE.1"]
    assert req["section_ref"] == "Section 5(1); DPDP Rules 2025 r.3"
    assert "understandable on its own" in req["description"]
    assert "r.3(a)" in req["description"]


def test_7_minimize_3_r8_3_folded_in():
    req = REQS["CH2.MINIMIZE.3"]
    assert req["section_ref"] == "Section 8(7); DPDP Rules 2025 r.8(3)"
    for phrase in ("traffic data", "at least one year", "Seventh Schedule", "r.8(3)"):
        assert phrase in req["description"]


def test_8_notice_3_reference_corrected():
    assert REQS["CH2.NOTICE.3"]["section_ref"] == "Section 6(3), 8(9); DPDP Rules 2025 r.9"
    assert "5(1)" not in REQS["CH2.NOTICE.3"]["section_ref"]


def test_9_question_text_matches_corrected_descriptions():
    notice = _QUESTION_TEXT["CH2.NOTICE.1"]
    assert "at or before the time of collecting" not in notice
    assert "consent request" in notice
    accuracy = _QUESTION_TEXT["CH2.ACCURACY.1"]
    assert "reasonable efforts" not in accuracy and "not misleading" not in accuracy
    assert "ensure" in accuracy and "decision" in accuracy and "another Data Fiduciary" in accuracy
    erasure = _QUESTION_TEXT["CH3.CORRECT.2"]
    assert "no longer necessary for the original purpose" not in erasure
    assert "at any time" in erasure


def test_10_without_delay_no_longer_flagged_as_vague():
    from app.dpdpa.prompts import __file__ as prompts_path

    text = Path(prompts_path).read_text(encoding="utf-8")
    block = text.split('(flag_type: "missing_timeline")', 1)[1].split("**Scope gaps**", 1)[0]
    assert "without undue delay" not in block
    assert '"as soon as possible"' in block
    assert "72-hour" in block
    assert 'No "without delay" intimation' in block


def test_11_security_3_penalty_is_residual_50():
    from types import SimpleNamespace

    from app.routers.web import _PENALTY_MAP, _compute_business_impact

    prefixes = [prefix for prefix, _ in _PENALTY_MAP]
    assert prefixes.index("CH2.SECURITY.3") < prefixes.index("CH2.SECURITY")

    def impact(req_id):
        item = SimpleNamespace(requirement_id=req_id, framework_id="dpdpa", compliance_status="non_compliant", risk_level="high")
        return _compute_business_impact([item])["max_penalty_cr"]

    assert impact("CH2.SECURITY.3") == 50
    assert impact("CH2.SECURITY.1") == 250
    assert impact("CH2.SECURITY.2") == 250
