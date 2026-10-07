"""Storage helpers for free-text questionnaire follow-up responses."""

from __future__ import annotations

import json


FOLLOWUP_ANSWER_PLACEHOLDER = "not_applicable"


def parent_question_id(followup_id: str) -> str:
    """Return the question id that produced a ``FU.`` response id."""
    parts = followup_id.split(".")
    return ".".join(parts[1:-1]) if len(parts) > 2 else ""


def cluster_id_for(followup_id: str) -> str | None:
    """Return the UCC cluster for a multi-framework follow-up, if applicable."""
    parent_id = parent_question_id(followup_id)
    return parent_id if parent_id.startswith("CLUSTER_") else None


def encode_notes(
    followup_id: str,
    question_text: str,
    answer_text: str,
) -> str:
    """Store the question and free-text answer in the existing notes column."""
    return json.dumps(
        {
            "type": "followup",
            "parent_question_id": parent_question_id(followup_id),
            "question": question_text,
            "answer": answer_text,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def decode(
    followup_id: str,
    notes: str | None,
    placeholder_answer: str = "",
) -> dict:
    """Decode a stored follow-up, tolerating the pre-hotfix notes format."""
    payload = None
    if notes:
        try:
            candidate = json.loads(notes)
        except (TypeError, json.JSONDecodeError):
            candidate = None
        if isinstance(candidate, dict) and candidate.get("type") == "followup":
            payload = candidate

    return {
        "id": followup_id,
        "parent_question_id": (
            payload.get("parent_question_id")
            if payload
            else parent_question_id(followup_id)
        ),
        "text": payload.get("question", "") if payload else "",
        "answer": payload.get("answer", placeholder_answer) if payload else placeholder_answer,
    }
