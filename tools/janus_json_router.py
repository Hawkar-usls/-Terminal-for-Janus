#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from janus_json_mirror_pass import run as mirror_run, sha256
from janus_json_5d_deep import run as deep_run

ROUTED_SCHEMA = "janus.interagent.mirror_message.v1"
UNEXPLAINED_ALIGNMENT = "UNEXPLAINED_ALIGNMENT"


def _event_class(payload: dict[str, Any]) -> str | None:
    direct = payload.get("event_class")
    if isinstance(direct, str) and direct:
        return direct.upper()
    event = payload.get("event")
    if isinstance(event, dict):
        nested = event.get("class") or event.get("event_class")
        if isinstance(nested, str) and nested:
            return nested.upper()
    return None


def _force_deep(payload: dict[str, Any]) -> bool:
    mode = payload.get("analysis_mode")
    if isinstance(mode, str) and mode.upper() in {"DEEP", "DEEP_TRANSCEPTION_5D", "SPIRAL_5D"}:
        return True
    return _event_class(payload) == UNEXPLAINED_ALIGNMENT


def route(payload: dict[str, Any]) -> dict[str, Any]:
    event_class = _event_class(payload)
    if _force_deep(payload):
        deep = deep_run(payload)
        deep["routing"] = {
            "router": "JANUS_JSON_INTERCHANGE_v1.2",
            "selected_mode": "DEEP",
            "forced_by_event_class": event_class == UNEXPLAINED_ALIGNMENT,
            "event_class": event_class,
            "interest_priority": "ELEVATED" if event_class == UNEXPLAINED_ALIGNMENT else "REQUESTED_DEEP",
            "truth_weight_delta": 0,
            "canonical_principle": "JANUS-UNEXPLAINED-ALIGNMENT-PRINCIPLE-2026-08-21-v1.0" if event_class == UNEXPLAINED_ALIGNMENT else None,
            "required_checks": [
                "BASE_RATE",
                "ALTERNATIVE_EXPLANATIONS",
                "SOURCE_INDEPENDENCE",
                "SELECTION_BIAS",
                "MULTIPLE_COMPARISONS",
                "MEASUREMENT_ERROR",
            ] if event_class == UNEXPLAINED_ALIGNMENT else [],
        }
        deep["laws"] = list(dict.fromkeys([
            "5D_GRAPH_OUTPUT != WORLD_TRUTH",
            "ASSOCIATION != EVIDENCE",
            "BOTH_HEMISPHERES_AGREE != TRUTH",
        ] + ([
            "COINCIDENCE != CAUSALITY",
            "COINCIDENCE != AUTOMATIC_DISMISSAL",
            "UNEXPLAINED_ALIGNMENT -> INCREASE_ATTENTION_NOT_TRUTH",
        ] if event_class == UNEXPLAINED_ALIGNMENT else [])))
        deep["integrity"]["output_sha256_without_self"] = sha256({k: v for k, v in deep.items() if k != "integrity"} | {"integrity": {k: v for k, v in deep["integrity"].items() if k != "output_sha256_without_self"}})
        return deep

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
        "routing": {
            "router": "JANUS_JSON_INTERCHANGE_v1.2",
            "selected_mode": "STANDARD",
            "forced_by_event_class": False,
            "event_class": event_class,
            "interest_priority": "NORMAL",
            "truth_weight_delta": 0,
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
    parser = argparse.ArgumentParser(description="JANUS mirror/deep-aware JSON interagent router")
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
