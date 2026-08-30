#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

TERMINAL_REPOSITORY = "Hawkar-usls/-Terminal-for-Janus"
ALLOWED_HUMAN_ACTOR = "Hawkar-usls"
SCHEMA = "janus.terminal.message.v1"
CANCELLATION_SCHEMA = "janus.terminal.message_cancellation.v1"
AUTHORITY_MODE = "READ_ONLY_CONVERSATION"


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_time(value: str) -> float:
    text = str(value or "").strip()
    if not text:
        raise ValueError("EVENT_CREATED_AT_REQUIRED")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _issue(event: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
    if not isinstance(event, dict):
        raise ValueError("GITHUB_EVENT_OBJECT_REQUIRED")
    issue = event.get("issue")
    if not isinstance(issue, dict):
        raise ValueError("ISSUE_EVENT_REQUIRED")
    number = issue.get("number")
    if not isinstance(number, int) or number < 1:
        raise ValueError("ISSUE_NUMBER_REQUIRED")
    return issue, number


def build_from_github_event(event: Dict[str, Any]) -> Dict[str, Any]:
    issue, number = _issue(event)

    comment = event.get("comment")
    if isinstance(comment, dict):
        actor = str(((comment.get("user") or {}).get("login") or "")).strip()
        body = str(comment.get("body") or "").strip()
        created_at = parse_time(str(comment.get("created_at") or ""))
        object_id = str(comment.get("id") or "")
        source_ref = f"{TERMINAL_REPOSITORY}#{number}:comment:{object_id}"
    else:
        actor = str(((issue.get("user") or {}).get("login") or "")).strip()
        body = str(issue.get("body") or "").strip()
        created_at = parse_time(str(issue.get("created_at") or ""))
        object_id = str(issue.get("id") or "")
        source_ref = f"{TERMINAL_REPOSITORY}#{number}:issue:{object_id}"

    if actor != ALLOWED_HUMAN_ACTOR:
        raise ValueError("TERMINAL_CONVERSATION_ACTOR_NOT_ADMITTED_V1")
    if not body:
        raise ValueError("TERMINAL_MESSAGE_TEXT_REQUIRED")

    identity_core = {
        "terminal_repository": TERMINAL_REPOSITORY,
        "conversation_id": f"issue-{number}",
        "human_actor": actor,
        "source_ref": source_ref,
        "message_text": body,
        "created_at": created_at,
    }
    message_id = "tm-" + canonical_hash(identity_core)
    envelope: Dict[str, Any] = {
        "schema": SCHEMA,
        "message_id": message_id,
        **identity_core,
        "authority_mode": AUTHORITY_MODE,
        "fresh_human_stimulus": True,
        "command_authority_granted": False,
        "human_authorized_write": False,
        "claim_authority_granted": False,
        "scientific_evidence_authority_granted": False,
        "world_truth_authority_granted": False,
        "external_effect_authorized": False,
        "physical_runtime_effect_authorized": False,
    }
    envelope["message_hash"] = canonical_hash(envelope)
    return envelope


def verify(envelope: Dict[str, Any]) -> bool:
    if not isinstance(envelope, dict):
        return False
    body = dict(envelope)
    claimed = str(body.pop("message_hash", ""))
    if len(claimed) != 64 or canonical_hash(body) != claimed:
        return False
    identity_core = {
        "terminal_repository": body.get("terminal_repository"),
        "conversation_id": body.get("conversation_id"),
        "human_actor": body.get("human_actor"),
        "source_ref": body.get("source_ref"),
        "message_text": body.get("message_text"),
        "created_at": body.get("created_at"),
    }
    return all([
        body.get("schema") == SCHEMA,
        body.get("message_id") == "tm-" + canonical_hash(identity_core),
        body.get("terminal_repository") == TERMINAL_REPOSITORY,
        body.get("human_actor") == ALLOWED_HUMAN_ACTOR,
        body.get("authority_mode") == AUTHORITY_MODE,
        body.get("fresh_human_stimulus") is True,
        body.get("command_authority_granted") is False,
        body.get("human_authorized_write") is False,
        body.get("claim_authority_granted") is False,
        body.get("scientific_evidence_authority_granted") is False,
        body.get("world_truth_authority_granted") is False,
        body.get("external_effect_authorized") is False,
        body.get("physical_runtime_effect_authorized") is False,
    ])


def build_cancellation_from_github_event(event: Dict[str, Any]) -> Dict[str, Any]:
    issue, number = _issue(event)
    if str(event.get("action") or "") != "closed" or str(issue.get("state") or "") != "closed":
        raise ValueError("TERMINAL_CANCELLATION_CLOSED_ISSUE_EVENT_REQUIRED")
    actor = str(((event.get("sender") or {}).get("login") or "")).strip()
    if actor != ALLOWED_HUMAN_ACTOR:
        raise ValueError("TERMINAL_CANCELLATION_ACTOR_NOT_ADMITTED_V1")
    cancelled_at = parse_time(str(issue.get("closed_at") or ""))

    # Reconstruct the immutable issue-open envelope from the closure payload.
    # GitHub closure events retain issue id, author, body and created_at, so this
    # binds cancellation to exactly the already-sealed request without lookup,
    # fuzzy matching, mutation, or deletion.
    original = build_from_github_event({"issue": issue})
    identity = {
        "terminal_repository": TERMINAL_REPOSITORY,
        "message_id": original["message_id"],
        "message_hash": original["message_hash"],
        "conversation_id": original["conversation_id"],
        "source_ref": original["source_ref"],
        "cancelled_by": actor,
        "cancelled_at": cancelled_at,
        "reason": "ISSUE_CLOSED_BY_ADMITTED_HUMAN",
    }
    tombstone: Dict[str, Any] = {
        "schema": CANCELLATION_SCHEMA,
        "cancellation_id": "tc-" + canonical_hash(identity),
        **identity,
        "request_deleted": False,
        "response_deleted": False,
        "cognition_authorized": False,
        "command_authority_granted": False,
        "claim_authority_granted": False,
        "scientific_evidence_authority_granted": False,
        "world_truth_authority_granted": False,
        "external_effect_authorized": False,
        "physical_runtime_effect_authorized": False,
        "terminal": "TERMINAL_MESSAGE_CANCELLATION_TOMBSTONE_READY",
        "laws": [
            "CANCEL != DELETE",
            "CANCEL != ERASE_RESPONSE",
            "CANCELLED_REQUEST != FRESH_COGNITION",
            "CANCELLATION != COMMAND_AUTHORITY",
        ],
    }
    tombstone["cancellation_hash"] = canonical_hash(tombstone)
    return tombstone


def verify_cancellation(tombstone: Dict[str, Any]) -> bool:
    if not isinstance(tombstone, dict):
        return False
    body = dict(tombstone)
    claimed = str(body.pop("cancellation_hash", ""))
    if len(claimed) != 64 or canonical_hash(body) != claimed:
        return False
    identity = {
        "terminal_repository": body.get("terminal_repository"),
        "message_id": body.get("message_id"),
        "message_hash": body.get("message_hash"),
        "conversation_id": body.get("conversation_id"),
        "source_ref": body.get("source_ref"),
        "cancelled_by": body.get("cancelled_by"),
        "cancelled_at": body.get("cancelled_at"),
        "reason": body.get("reason"),
    }
    laws = set(body.get("laws") or [])
    return all([
        body.get("schema") == CANCELLATION_SCHEMA,
        body.get("cancellation_id") == "tc-" + canonical_hash(identity),
        body.get("terminal_repository") == TERMINAL_REPOSITORY,
        str(body.get("message_id") or "").startswith("tm-"),
        len(str(body.get("message_hash") or "")) == 64,
        body.get("cancelled_by") == ALLOWED_HUMAN_ACTOR,
        body.get("reason") == "ISSUE_CLOSED_BY_ADMITTED_HUMAN",
        body.get("request_deleted") is False,
        body.get("response_deleted") is False,
        body.get("cognition_authorized") is False,
        body.get("command_authority_granted") is False,
        body.get("claim_authority_granted") is False,
        body.get("scientific_evidence_authority_granted") is False,
        body.get("world_truth_authority_granted") is False,
        body.get("external_effect_authorized") is False,
        body.get("physical_runtime_effect_authorized") is False,
        body.get("terminal") == "TERMINAL_MESSAGE_CANCELLATION_TOMBSTONE_READY",
        {
            "CANCEL != DELETE",
            "CANCEL != ERASE_RESPONSE",
            "CANCELLED_REQUEST != FRESH_COGNITION",
        }.issubset(laws),
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=("message", "cancellation"), default="message")
    args = parser.parse_args()
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    if args.mode == "cancellation":
        value = build_cancellation_from_github_event(event)
        valid = verify_cancellation(value)
        terminal = "TERMINAL_MESSAGE_CANCELLATION_TOMBSTONE_READY"
        id_field = "cancellation_id"
        hash_field = "cancellation_hash"
    else:
        value = build_from_github_event(event)
        valid = verify(value)
        terminal = "TERMINAL_CONVERSATION_ENVELOPE_READY"
        id_field = "message_id"
        hash_field = "message_hash"
    if not valid:
        raise SystemExit("TERMINAL_CONVERSATION_ENVELOPE_SELF_VERIFY_FAILED")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "terminal": terminal,
        id_field: value[id_field],
        hash_field: value[hash_field],
        "message_id": value.get("message_id"),
        "conversation_id": value["conversation_id"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
