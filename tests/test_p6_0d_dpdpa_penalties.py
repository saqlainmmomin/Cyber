"""P6-0d: DPDPA penalty map against the Schedule to the Act (s.33).

Schedule item 2 (Rs 200 crore) covers only the s.8(6) duty to give notice of a
breach. An incident response plan (s.8(4)) and a breach register fall under the
residual item 7 (Rs 50 crore). Signed off by Saqlain on 2026-09-27.
"""

from types import SimpleNamespace

from app.routers.web import _PENALTY_MAP, _compute_business_impact


def _impact(req_id):
    item = SimpleNamespace(
        requirement_id=req_id, framework_id="dpdpa",
        compliance_status="non_compliant", risk_level="high",
    )
    return _compute_business_impact([item])["max_penalty_cr"]


def test_breach_notice_duties_are_item_2():
    assert _impact("BN.NOTIFY.1") == 200
    assert _impact("BN.NOTIFY.2") == 200


def test_ir_plan_and_breach_register_are_residual_item_7():
    assert _impact("BN.NOTIFY.3") == 50
    assert _impact("BN.NOTIFY.4") == 50


def test_specific_overrides_precede_the_prefix():
    prefixes = [prefix for prefix, _ in _PENALTY_MAP]
    for specific in ("BN.NOTIFY.3", "BN.NOTIFY.4"):
        assert prefixes.index(specific) < prefixes.index("BN.NOTIFY")


def test_every_schedule_item_amount_in_the_map_is_a_real_amount():
    # Items 1-4 and 7 are the only fiduciary amounts in the Schedule.
    assert {amount for _, amount in _PENALTY_MAP} <= {250, 200, 150, 50}
