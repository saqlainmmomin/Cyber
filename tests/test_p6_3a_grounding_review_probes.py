"""Throwaway adversarial probes for P6-3a. Each test asserts the DESIRED behaviour;
a failure is a finding."""
from __future__ import annotations

import json
import random
import re

import pytest

from app.config import settings
from app.services.grounding import SourceDocument, pipeline, prompts
from app.services.grounding.batches import extraction_batches
from app.services.grounding.chunking import chunk_source
from app.services.grounding.claims import claim_set_is_current
from app.services.grounding.metadata import extract_metadata


@pytest.fixture(scope="module", autouse=True)
def _reg():
    from app.main import _register_frameworks
    _register_frameworks()


@pytest.fixture(autouse=True)
def _serial(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_concurrency", 1)


def src(text, sid="ev:1", fn="doc.txt", mime="text/plain"):
    return SourceDocument(sid, "e1", sid.split(":")[1], None, fn, "policy", mime, text)


BODY = ("Audits are performed biannually by the risk team and results are filed in the register. "
        "Access Control Policy\n") * 3


def install_fake(monkeypatch, extraction_items, support_fn=None, capture=None):
    """extraction_items: callable(system, user) -> list[dict]; support_fn(entries)->verdicts"""
    def fake(*, tier, stream=False, **req):
        user = req["messages"][0]["content"]
        if capture is not None:
            capture.append(req)
        if "\nstatement: " in user and user.startswith("["):
            refs = re.findall(r"^\[(c\d+)\]\nstatement: (.*)$", user, re.M)
            verdicts = support_fn(refs) if support_fn else [
                {"ref": r, "verdict": "yes", "supported_statement": None} for r, _ in refs]
            return {"text": json.dumps({"verdicts": verdicts}), "usage": {}}
        return {"text": json.dumps({"claims": extraction_items(req["system"], user)}), "usage": {}}
    monkeypatch.setattr(pipeline, "_call_llm", fake)


def first_id(system):
    return re.search(r"^- (\S+) \[", system, re.M).group(1)


def item(system, quote, statement="The risk team performs audits.", **kw):
    base = {"quote": quote, "statement": statement, "kind": "design",
            "stated_period": None, "stated_owner": None, "requirement_ids": [first_id(system)]}
    base.update(kw)
    return base


# ---- F1: attribute verification is an unbounded substring match --------------
def test_stated_owner_IT_not_grounded_by_substring_in_audits(monkeypatch):
    s = src(BODY)
    install_fake(monkeypatch, lambda sys_, u: [item(
        sys_, "Audits are performed biannually by the risk team",
        stated_owner="IT", stated_period="annually")])
    cs = pipeline.run_stages_0_1([s], ["dpdpa"])
    c = cs.claims[0]
    # desired: 'IT' is not a stated owner (it only matches inside 'Audits'),
    # 'annually' is not the period (text says 'biannually')
    assert c.stated_owner is None, c.stated_owner
    assert c.stated_period is None, c.stated_period


# ---- F2: support prompt never describes the output shape --------------------
def test_support_system_prompt_describes_json_shape():
    p = prompts.SUPPORT_SYSTEM_PROMPT
    assert "verdicts" in p and "ref" in p


def test_extraction_prompt_states_numeric_claim_cap():
    b = extraction_batches(["dpdpa"])[0]
    assert str(settings.v2_max_claims_per_call) in prompts.build_extraction_system_prompt(b)


# ---- F3: bracketed ref / omitted null -> silent support_missing, status complete
def test_bracketed_ref_is_not_silently_complete(monkeypatch):
    s = src(BODY)
    install_fake(monkeypatch,
                 lambda sys_, u: [item(sys_, "Audits are performed biannually by the risk team")],
                 support_fn=lambda refs: [{"ref": f"[{r}]", "verdict": "yes"} for r, _ in refs])
    cs = pipeline.run_stages_0_1([s], ["dpdpa"])
    print(cs.status, cs.metrics["rejected_by_reason"]["support_missing"], len(cs.claims))
    assert not (cs.status == "complete" and len(cs.claims) == 0)


# ---- F4: post-support merge leaves support='yes' with original_statement set --
def test_post_support_merge_consistency(monkeypatch):
    s = src(BODY)
    q = "Audits are performed biannually by the risk team"
    install_fake(
        monkeypatch,
        lambda sys_, u: [item(sys_, q, statement="The risk team performs audits."),
                         item(sys_, q, statement="The risk team performs audits every month.")],
        support_fn=lambda refs: [
            {"ref": r, "verdict": "yes" if "month" not in st else "partial",
             "supported_statement": None if "month" not in st else "The risk team performs audits."}
            for r, st in refs])
    cs = pipeline.run_stages_0_1([s], ["dpdpa"])
    assert len(cs.claims) == 1
    c = cs.claims[0]
    print(c.support, c.original_statement, c.needs_review)
    assert (c.original_statement is None) == (c.support == "yes")


# ---- F5: heading-only quote grounds a broad statement -----------------------
def test_heading_only_quote_is_accepted(monkeypatch):
    s = src(BODY)
    install_fake(monkeypatch, lambda sys_, u: [item(
        sys_, "Access Control Policy",
        statement="The organisation has an approved access control policy.")])
    cs = pipeline.run_stages_0_1([s], ["dpdpa"])
    # documents current behaviour: only the support check stands in the way
    assert len(cs.claims) == 0, [c.quote for c in cs.claims]


# ---- F7: İ span ending mid-expansion is rejected -----------------------------
def test_dotted_I_span_normalises_equal(monkeypatch):
    text = "The access register is maintained by Mr. Kİm and reviewed every quarter.\n" * 3
    s = src(text)
    mq = "The access register is maintained by Mr. Ki"
    install_fake(monkeypatch, lambda sys_, u: [item(sys_, mq)])
    cs = pipeline.run_stages_0_1([s], ["dpdpa"])
    assert cs.claims == ()
    assert cs.metrics["rejected_by_reason"]["quote_unicode_mismatch"] == len(cs.rejected) > 0


# ---- F7: metadata on CR-only text ---------------------------------------------
def test_metadata_cr_only_line_endings():
    text = "Version: 2.1\rApproved by: Chief Risk Officer\rEffective Date: 14 March 2025\rBody text."
    md = {f.name: f for f in extract_metadata(src(text)).fields}
    print({k: v.value for k, v in md.items()})
    assert md["approver"].value == "Chief Risk Officer"
    assert md["version"].value == "2.1"


def test_metadata_line_straddling_top_window():
    pad = "x" * 3990 + "\n"
    text = pad + "Version: 2.13\n" + ("filler words here\n" * 400)
    md = {f.name: f for f in extract_metadata(src(text)).fields}
    print({k: v.value for k, v in md.items()})
    assert "version" not in md or md["version"].value == "2.13"


# ---- F8: freshness ignores prompt-visible source attributes -----------------
def test_is_current_notices_filename_or_mime_change(monkeypatch):
    s = src(BODY)
    install_fake(monkeypatch, lambda sys_, u: [])
    cs = pipeline.run_stages_0_1([s], ["dpdpa"])
    renamed = SourceDocument(s.source_id, s.evidence_id, s.evidence_version_id, None,
                             "renamed.png", "other", "image/png", s.text)
    assert not claim_set_is_current(cs, [renamed], ["dpdpa"])


# ---- Tiling probes ------------------------------------------------------------
SEPS = ["\n", "\r\n", "\r", "\x0b", "\x0c", "\x1c", "\x85", " ", " "]


@pytest.mark.parametrize("seed", range(60))
def test_tiling_random(seed):
    r = random.Random(seed)
    parts = []
    for _ in range(r.randint(1, 400)):
        n = r.choice([0, 1, 3, 8, 40, 300, 1700])
        words = " ".join(r.choice(["alpha", "Beta.", "γ", "x!", "3.5", "e.g."]) for _ in range(n))
        if r.random() < 0.1:
            words = "ACCESS CONTROL"
        parts.append(words + r.choice(SEPS + [""]))
    text = "".join(parts)
    if r.random() < 0.5:
        text = text.rstrip()
    cs = chunk_source(src(text), min_words=r.choice([5, 50, 800]), max_words=r.choice([20, 100, 1500]))
    if not text.strip():
        assert cs == ()
        return
    assert cs[0].start == 0 and cs[-1].end == len(text)
    for a, b in zip(cs, cs[1:]):
        assert a.end == b.start
    assert "".join(text[c.start:c.end] for c in cs) == text
