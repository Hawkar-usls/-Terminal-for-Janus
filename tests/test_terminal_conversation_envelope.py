from __future__ import annotations

import copy

import pytest

from tools.terminal_conversation_envelope import (
    build_cancellation_from_github_event,
    build_from_github_event,
    verify,
    verify_cancellation,
)


def issue_event():
    return {
        "action": "opened",
        "sender": {"login": "Hawkar-usls"},
        "issue": {
            "id": 101,
            "number": 7,
            "body": "### Message\nJanus, are you online?",
            "created_at": "2026-08-30T17:30:00Z",
            "closed_at": None,
            "state": "open",
            "user": {"login": "Hawkar-usls"},
        },
    }


def closed_issue_event():
    event = issue_event()
    event["action"] = "closed"
    event["issue"]["state"] = "closed"
    event["issue"]["closed_at"] = "2026-08-30T17:45:00Z"
    return event


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


def test_issue_close_reconstructs_exact_original_request_identity():
    original = build_from_github_event(issue_event())
    tombstone = build_cancellation_from_github_event(closed_issue_event())
    assert verify_cancellation(tombstone)
    assert tombstone["message_id"] == original["message_id"]
    assert tombstone["message_hash"] == original["message_hash"]
    assert tombstone["conversation_id"] == original["conversation_id"]
    assert tombstone["source_ref"] == original["source_ref"]
    assert tombstone["cancelled_by"] == "Hawkar-usls"
    assert tombstone["reason"] == "ISSUE_CLOSED_BY_ADMITTED_HUMAN"


def test_cancellation_is_append_only_tombstone_not_deletion_or_cognition():
    tombstone = build_cancellation_from_github_event(closed_issue_event())
    assert verify_cancellation(tombstone)
    assert tombstone["request_deleted"] is False
    assert tombstone["response_deleted"] is False
    assert tombstone["cognition_authorized"] is False
    assert tombstone["command_authority_granted"] is False
    assert tombstone["external_effect_authorized"] is False
    assert "CANCEL != DELETE" in tombstone["laws"]
    assert "CANCELLED_REQUEST != FRESH_COGNITION" in tombstone["laws"]


def test_non_owner_actor_is_rejected_in_v1():
    event = issue_event()
    event["issue"]["user"]["login"] = "external-user"
    with pytest.raises(ValueError, match="ACTOR_NOT_ADMITTED"):
        build_from_github_event(event)


def test_non_owner_closer_cannot_cancel_sealed_owner_request():
    event = closed_issue_event()
    event["sender"]["login"] = "external-user"
    with pytest.raises(ValueError, match="CANCELLATION_ACTOR_NOT_ADMITTED"):
        build_cancellation_from_github_event(event)


def test_non_closed_event_cannot_mint_cancellation():
    with pytest.raises(ValueError, match="CLOSED_ISSUE_EVENT_REQUIRED"):
        build_cancellation_from_github_event(issue_event())


def test_tamper_breaks_integrity():
    value = build_from_github_event(issue_event())
    bad = copy.deepcopy(value)
    bad["message_text"] = "changed after sealing"
    assert verify(bad) is False


def test_cancellation_target_tamper_breaks_integrity():
    value = build_cancellation_from_github_event(closed_issue_event())
    bad = copy.deepcopy(value)
    bad["message_id"] = "tm-" + "0" * 64
    assert verify_cancellation(bad) is False


def test_rehashed_cancellation_cannot_gain_cognition_authority():
    value = build_cancellation_from_github_event(closed_issue_event())
    value["cognition_authorized"] = True
    body = dict(value)
    body.pop("cancellation_hash")
    from tools.terminal_conversation_envelope import canonical_hash
    value["cancellation_hash"] = canonical_hash(body)
    assert verify_cancellation(value) is False


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
