"""
Unit tests for Phase 2 tier engine.
Tests all 7 tier assignment rules and batch assignment.
"""

from app.services.tier_engine import assign_tier, assign_tiers, compute_tier_stats


# ── Rule 1: Scope exclusions → SKIP ──

def test_skipped_question_maps_to_skip():
    q = {"status": "skipped", "criticality": "critical"}
    assert assign_tier(q) == "skip"


# ── Rule 2: Pre-filled + non-critical → LIGHT ──

def test_prefilled_medium_maps_to_light():
    q = {"status": "pre_filled", "criticality": "medium"}
    assert assign_tier(q) == "light"


def test_prefilled_high_maps_to_light():
    q = {"status": "pre_filled", "criticality": "high"}
    assert assign_tier(q) == "light"


# ── Rule 3: Pre-filled + critical → STANDARD ──

def test_prefilled_critical_maps_to_standard():
    q = {"status": "pre_filled", "criticality": "critical"}
    assert assign_tier(q) == "standard"


# ── Rule 4: Deepened → DEEP ──

def test_deepened_maps_to_deep():
    q = {"status": "deepened", "criticality": "medium"}
    assert assign_tier(q) == "deep"


def test_deepened_overrides_non_critical():
    q = {"status": "deepened", "criticality": "low"}
    assert assign_tier(q) == "deep"


# ── Rule 5: Critical + HIGH risk → DEEP ──

def test_critical_high_risk_maps_to_deep():
    q = {"status": "active", "criticality": "critical"}
    assert assign_tier(q, risk_tier="HIGH") == "deep"


# ── Rule 6: High criticality + HIGH risk → DEEP ──

def test_high_crit_high_risk_maps_to_deep():
    q = {"status": "active", "criticality": "high"}
    assert assign_tier(q, risk_tier="HIGH") == "deep"


# ── Rule 7: Default → STANDARD ──

def test_active_medium_maps_to_standard():
    q = {"status": "active", "criticality": "medium"}
    assert assign_tier(q) == "standard"


def test_active_high_medium_risk_maps_to_standard():
    q = {"status": "active", "criticality": "high"}
    assert assign_tier(q, risk_tier="MEDIUM") == "standard"


# ── Batch assignment ──

def test_assign_tiers_mutates_in_place():
    questions = [
        {"status": "skipped", "criticality": "medium"},
        {"status": "pre_filled", "criticality": "high"},
        {"status": "deepened", "criticality": "medium"},
        {"status": "active", "criticality": "medium"},
    ]
    result = assign_tiers(questions, risk_tier="MEDIUM")
    assert result is questions  # same list, mutated
    assert questions[0]["tier"] == "skip"
    assert questions[1]["tier"] == "light"
    assert questions[2]["tier"] == "deep"
    assert questions[3]["tier"] == "standard"


# ── Stats computation ──

def test_compute_tier_stats():
    questions = [
        {"tier": "deep"},
        {"tier": "deep"},
        {"tier": "standard"},
        {"tier": "light"},
        {"tier": "light"},
        {"tier": "light"},
        {"tier": "skip"},
    ]
    stats = compute_tier_stats(questions)
    assert stats == {"deep": 2, "standard": 1, "light": 3, "skip": 1}


# ── Edge cases ──

def test_missing_status_defaults_to_standard():
    q = {"criticality": "medium"}
    assert assign_tier(q) == "standard"


def test_missing_criticality_defaults_to_medium():
    q = {"status": "active"}
    assert assign_tier(q) == "standard"


def test_prefilled_critical_high_risk_still_standard():
    """Pre-filled critical → STANDARD (rule 3 fires before rule 5)."""
    q = {"status": "pre_filled", "criticality": "critical"}
    assert assign_tier(q, risk_tier="HIGH") == "standard"
