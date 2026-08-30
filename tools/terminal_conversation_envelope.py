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


def build_from_github_event(event: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("GITHUB_EVENT_OBJECT_REQUIRED")
    issue = event.get("issue")
    if not isinstance(issue, dict):
        raise ValueError("ISSUE_EVENT_REQUIRED")
    number = issue.get("number")
    if not isinstance(number, int) or number < 1:
        raise ValueError("ISSUE_NUMBER_REQUIRED")

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    envelope = build_from_github_event(event)
    if not verify(envelope):
        raise SystemExit("TERMINAL_CONVERSATION_ENVELOPE_SELF_VERIFY_FAILED")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "terminal": "TERMINAL_CONVERSATION_ENVELOPE_READY",
        "message_id": envelope["message_id"],
        "message_hash": envelope["message_hash"],
        "conversation_id": envelope["conversation_id"],
        "authority_mode": envelope["authority_mode"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
