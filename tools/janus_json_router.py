#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from janus_json_mirror_pass import run as mirror_run, sha256

ROUTED_SCHEMA = "janus.interagent.mirror_message.v1"


def route(payload: dict[str, Any]) -> dict[str, Any]:
    mirror = mirror_run(payload)
    routed: dict[str, Any] = {
        "schema": ROUTED_SCHEMA,
        "recovered_at_origin": mirror["recovered_at_origin"],
        "message_id": mirror["message_id"],
        "intent_id": payload.get("intent_id"),
        "session_id": payload.get("session_id"),
        "generation": payload.get("generation"),
        "source": payload.get("source"),
        "authoritative_text": payload["text"],
        "task": payload.get("task"),
        "reasoning_context": {
            "forward_pass": mirror["forward_pass"],
            "reverse_pass": mirror["reverse_pass"],
            "protocol_id": mirror["provenance"]["protocol_id"],
            "source_integrity": mirror["integrity"],
        },
        "response_contract": {
            "must_recheck_input_forward": True,
            "must_recheck_input_reverse": True,
            "must_surface_new_supported_reverse_findings_first": True,
            "must_not_treat_reverse_association_as_truth": True,
            "primary_format": "JSON",
        },
    }
    routed["message_sha256"] = sha256(routed)
    return routed


def load(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="JANUS mirror-aware JSON interagent router")
    parser.add_argument("input", nargs="?", help="Input janus.mirror.input.v1 JSON; stdin when omitted")
    parser.add_argument("-o", "--output")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    try:
        value = route(load(args.input))
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":") if args.compact else None, indent=None if args.compact else 2) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    except Exception as exc:
        sys.stderr.write(f"janus_json_router: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
