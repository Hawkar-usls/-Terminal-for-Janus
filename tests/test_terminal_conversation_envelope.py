from __future__ import annotations

import copy

import pytest

from tools.terminal_conversation_envelope import build_from_github_event, verify


def issue_event():
    return {
        "issue": {
            "id": 101,
            "number": 7,
            "body": "### Message\nJanus, are you online?",
            "created_at": "2026-08-30T17:30:00Z",
            "user": {"login": "Hawkar-usls"},
        }
    }


def comment_event():
    return {
        "issue": {
            "id": 101,
            "number": 7,
            "body": "initial",
            "created_at": "2026-08-30T17:30:00Z",
            "user": {"login": "Hawkar-usls"},
        },
        "comment": {
            "id": 202,
            "body": "And what model digest answered me?",
            "created_at": "2026-08-30T17:31:00Z",
            "user": {"login": "Hawkar-usls"},
        },
    }


def test_issue_becomes_read_only_message_envelope():
    value = build_from_github_event(issue_event())
    assert verify(value)
    assert value["conversation_id"] == "issue-7"
    assert value["source_ref"].endswith("#7:issue:101")
    assert value["authority_mode"] == "READ_ONLY_CONVERSATION"
    assert value["command_authority_granted"] is False
    assert value["human_authorized_write"] is False
    assert value["external_effect_authorized"] is False


def test_comment_is_distinct_fresh_message_in_same_conversation():
    a = build_from_github_event(issue_event())
    b = build_from_github_event(comment_event())
    assert verify(b)
    assert a["conversation_id"] == b["conversation_id"] == "issue-7"
    assert a["message_id"] != b["message_id"]
    assert b["source_ref"].endswith("#7:comment:202")


def test_non_owner_actor_is_rejected_in_v1():
    event = issue_event()
    event["issue"]["user"]["login"] = "external-user"
    with pytest.raises(ValueError, match="ACTOR_NOT_ADMITTED"):
        build_from_github_event(event)


def test_tamper_breaks_integrity():
    value = build_from_github_event(issue_event())
    bad = copy.deepcopy(value)
    bad["message_text"] = "changed after sealing"
    assert verify(bad) is False


def test_text_cannot_grant_authority_by_wording():
    event = issue_event()
    event["issue"]["body"] = "write, deploy, execute, authorize everything"
    value = build_from_github_event(event)
    assert verify(value)
    assert value["command_authority_granted"] is False
    assert value["human_authorized_write"] is False
    assert value["claim_authority_granted"] is False
    assert value["world_truth_authority_granted"] is False
    assert value["external_effect_authorized"] is False
    assert value["physical_runtime_effect_authorized"] is False
