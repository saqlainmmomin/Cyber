"""Deterministic artifact grouping preserves signed checks separately."""
from dataclasses import replace

import pytest

from app.frameworks.registry import FrameworkRegistry
from app.main import _register_frameworks
from app.services.rfi_evidence_requests import document_request_fields, document_request_guidance, document_request_text


ACCESS_ARTIFACTS = [
    {
        "name": "Access control policy",
        "controls": ["ISO.A5.15", "ISO.A5.17", "ISO.A5.18", "ISO.A8.2", "ISO.A8.3", "ISO.A8.5"],
        "specifics": [
            {"text": "identity management procedure", "controls": ["ISO.A5.16"]},
            {"text": "access request tickets", "controls": ["ISO.A5.18"]},
            {"text": "user access review records", "controls": ["ISO.A5.18"]},
            {"text": "privileged account list, approvals", "controls": ["ISO.A8.2"]},
            {"text": "privileged access review records", "controls": ["ISO.A8.2"]},
        ],
    },
    {"name": "System access listings", "controls": ["ISO.A5.15", "ISO.A8.3"], "specifics": []},
    {"name": "Identity provider export", "controls": ["ISO.A5.16"], "specifics": []},
    {"name": "HR leaver list", "controls": ["ISO.A5.16", "ISO.A5.18"], "specifics": []},
    {"name": "Asset inventory", "controls": ["ISO.A5.16"], "specifics": []},
    {"name": "Information security policy", "controls": ["ISO.A5.17"], "specifics": []},
    {"name": "Training records", "controls": ["ISO.A5.17"], "specifics": []},
    {"name": "Configuration baselines", "controls": ["ISO.A5.17", "ISO.A8.5"], "specifics": []},
    {"name": "Identity provider logs", "controls": ["ISO.A5.18"], "specifics": []},
    {"name": "System role matrices", "controls": ["ISO.A8.3"], "specifics": []},
    {"name": "Assessor test results", "controls": ["ISO.A8.3"], "specifics": []},
    {"name": "Identity provider configuration export", "controls": ["ISO.A8.5"], "specifics": []},
]


@pytest.fixture(autouse=True)
def register():
    _register_frameworks()


def test_iso_access_artifacts_and_checks_exact():
    framework = FrameworkRegistry.get('iso27001')
    request = next(item for item in framework.evidence_requests if item.document_type == 'access_control_policy')
    pairs = [['iso27001', rid] for rid in request.maps_to]
    lines, rows = document_request_guidance(pairs)
    assert lines == ACCESS_ARTIFACTS
    assert len(lines) == 12
    assert [row['requirement_id'] for row in rows] == list(request.maps_to)
    assert len(rows) == 7
    assert sum(len(row['criteria']) for row in rows) == 20
    for row in rows:
        control = framework.get_control(row['requirement_id'])
        assert row['framework_id'] == 'iso27001'
        assert row['title'] == control.title
        assert [{k: v for k, v in c.items() if k != 'evidence_hint_label'} for c in row['criteria']] == [
            dict(kind=c.kind, statement=c.statement,
                 evidence_hint=c.evidence_hint, source_basis=c.source_basis)
            for c in control.test_criteria]
        assert all('_' not in c['evidence_hint_label'] for c in row['criteria'])


def test_parenthesis_aware_split_and_case_insensitive_grouping(monkeypatch):
    framework = FrameworkRegistry.get('iso27001')
    control = framework.get_control('ISO.A8.2')
    criteria = (
        replace(control.test_criteria[0], evidence_hint='access_control_policy (privileged account list; approvals); HR leaver list'),
        replace(control.test_criteria[0], evidence_hint='ACCESS_CONTROL_POLICY; hr LEAVER list'),
    )
    lookup = framework.get_control
    monkeypatch.setattr(type(framework), 'get_control',
                        lambda self, rid: replace(control, test_criteria=criteria) if rid == control.id else lookup(rid))
    lines, rows = document_request_guidance([['iso27001', control.id]])
    assert lines == [
        {"name": "Access control policy", "controls": ["ISO.A8.2"], "specifics": [
            {"text": "privileged account list, approvals", "controls": ["ISO.A8.2"]},
        ]},
        {"name": "HR leaver list", "controls": ["ISO.A8.2"], "specifics": []},
    ]
    assert rows[0]['criteria'][0]['evidence_hint'] == criteria[0].evidence_hint


def test_single_control_and_no_criteria(monkeypatch):
    control = FrameworkRegistry.get('iso27001').get_control('ISO.A8.2')
    pairs = [['iso27001', control.id]]
    assert len(document_request_guidance(pairs)[1]) == 1
    assert 'What to send\n' in document_request_text('Original.', 'access_control_policy', pairs)
    framework = FrameworkRegistry.get('iso27001')
    lookup = framework.get_control
    monkeypatch.setattr(type(framework), 'get_control',
                        lambda self, rid: replace(control, test_criteria=()) if rid == control.id else lookup(rid))
    assert document_request_guidance(pairs) == ([], [])
    text = document_request_text('Original.', 'access_control_policy', pairs)
    assert 'What to send' not in text
    assert text.startswith('Original.\n\nExample of what to send:')


def test_access_plain_text_sections_are_wrapped_and_structured():
    request = next(item for item in FrameworkRegistry.get("iso27001").evidence_requests
                   if item.document_type == "access_control_policy")
    fields = document_request_fields(
        request.reason, request.document_type, [["iso27001", rid] for rid in request.maps_to]
    )
    assert fields["summary"] == request.reason
    assert fields["what_to_send"] == ACCESS_ARTIFACTS
    text = fields["request"]
    assert max(map(len, text.splitlines())) <= 100
    sections = text.split("\n\n")
    assert len(sections) == 4
    assert " ".join(sections[0].splitlines()) == request.reason
    assert sections[1].startswith("What to send\n- Access control policy\n    supports: ")
    assert "    - privileged account list, approvals (ISO.A8.2)" in sections[1]
    assert sections[2].startswith("Example of what to send: ")
    assert "\nGood looks like: " in sections[2]
    assert sections[3] == "Period (auditor): __________\nSample size (auditor): __________"
    assert not any(row["criteria"][0]["statement"] in text for row in fields["why_we_ask"])


def test_unknown_and_empty_types_use_other_catalogue():
    from app.services.rfi_examples import DOCUMENT_EXAMPLES

    for document_type in ("", "unknown_stored_type"):
        fields = document_request_fields("Original.", document_type, [])
        assert fields["example"] == DOCUMENT_EXAMPLES["other"]["example_artifacts"]
        assert fields["good_looks_like"] == DOCUMENT_EXAMPLES["other"]["good_looks_like"]
        assert fields["what_to_send"] == []
        assert "why_we_ask" not in fields
        assert "What to send" not in fields["request"]


def test_every_catalogue_type_has_a_plain_name():
    from app.services.rfi_examples import DOCUMENT_EXAMPLES, DOCUMENT_NAMES, artifact_name

    assert set(DOCUMENT_NAMES) == set(DOCUMENT_EXAMPLES)
    for document_type, name in DOCUMENT_NAMES.items():
        assert artifact_name(document_type) == name
        assert "_" not in name and name[:1].isupper()


def test_artifact_name_keeps_known_acronyms_and_unknown_text_readable():
    from app.services.rfi_examples import artifact_name

    assert artifact_name("hr_security") == "HR security procedures"
    assert artifact_name("identity provider export") == "Identity provider export"
    assert artifact_name("HR leaver list") == "HR leaver list"
    assert artifact_name("pam session logs") == "PAM session logs"
    assert artifact_name("new_unmapped_type") == "New unmapped type"
    assert artifact_name("") == ""


def test_security_policy_request_names_artifacts_in_plain_english():
    framework = FrameworkRegistry.get("iso27001")
    request = next(item for item in framework.evidence_requests if item.document_type == "security_policy")
    pairs = [["iso27001", rid] for rid in request.maps_to]
    artifacts, _rows = document_request_guidance(pairs)
    names = [artifact["name"] for artifact in artifacts]
    assert "HR security procedures" in names
    assert not any(name.startswith("Hr ") for name in names)
    assert all("_" not in name for name in names)


def test_display_hint_turns_internal_ids_into_plain_names():
    from app.services.rfi_evidence_requests import display_hint

    assert display_hint("access_control_policy") == "Access control policy"
    assert display_hint(
        "access_control_policy (privileged account list; approvals); HR leaver list"
    ) == "Access control policy (privileged account list; approvals); HR leaver list"
    assert display_hint("identity provider export; asset_inventory") == "Identity provider export; Asset inventory"
    assert display_hint("hr_security; pam session logs") == "HR security procedures; PAM session logs"
    assert display_hint("") == ""
