#!/usr/bin/env python3
"""Pure-Python objective scoring of archived JANUS model dialogues.

This is an arithmetic check on disclosed public tasks, not an independent
external scientific benchmark or permission to learn from self-generated text.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

PROMPT = re.compile(
    r"^JANUS_ORACLE_ARITH_V1 a=(\d+) b=(\d+) offset=(\d+) modulus=(\d+)\. "
)
STRICT_ANSWER = re.compile(r"^(0|[1-9][0-9]*)$")
RECORD_SCHEMA = "janus.open_llm.corpus_record.v1"
SCHEMA = "janus.open_llm.objective_quality/1"


def seal(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def parse_prompt(prompt):
    if not isinstance(prompt, str):
        return None
    match = PROMPT.match(prompt)
    if not match:
        return None
    a, b, offset, modulus = map(int, match.groups())
    if any(not 0 <= v <= 999 for v in (a, b, offset)) or not 2 <= modulus <= 999:
        raise ValueError("ORACLE_PARAMETERS_OUT_OF_BOUNDS")
    return a, b, offset, modulus


def independent_oracles(a, b, offset, modulus):
    expected_a = (a*b + offset) % modulus
    # Independent implementation using repeated additive reduction, not the
    # same multiplication or modulo operation for the product.
    value = offset
    while value >= modulus:
        value -= modulus
    for _ in range(b):
        value += a
        while value >= modulus:
            value -= modulus
    expected_b = value
    if expected_a != expected_b:
        raise ValueError("ORACLE_DISAGREEMENT")
    return expected_a


def score_text(text, expected):
    if not isinstance(text, str):
        return {"status": "FAIL_FORMAT", "correct": False, "answer": None}
    t = text.strip()
    if not STRICT_ANSWER.fullmatch(t):
        return {"status": "FAIL_FORMAT", "correct": False, "answer": None}
    value = int(t)
    return {"status": "PASS_ORACLE_VALUE" if value == expected else "FAIL_WRONG_VALUE",
            "correct": value == expected, "answer": value}


def score_record(record):
    if not isinstance(record, dict) or record.get("schema") != RECORD_SCHEMA:
        raise ValueError("INVALID_SOURCE_RECORD")
    if record.get("record_sha256") != seal({
            k:v for k,v in record.items() if k!="record_sha256"}):
        raise ValueError("TAMPERED_CORPUS_RECORD")
    if record.get("source_binding", {}).get("kind") != "ISSUE_AND_BOT_REPLY_DIGEST_MATCH":
        raise ValueError("UNVERIFIED_SOURCE_GITHUB_BOUNDARY")
    dialogue = record.get("dialogue")
    if not isinstance(dialogue, dict) or dialogue.get("sha256") != seal({
            k:v for k,v in dialogue.items() if k!="sha256"}):
        raise ValueError("UNVERIFIED_DIALOGUE_SHA")
    req = dialogue.get("request") or {}
    if req.get("request_sha256") != seal({
            k:v for k,v in req.items() if k!="request_sha256"}):
        raise ValueError("UNVERIFIED_REQUEST_SHA")
    params = parse_prompt(req.get("prompt"))
    if params is None:
        return None
    expected = independent_oracles(*params)
    exchanges = dialogue.get("exchanges") or []
    if len(exchanges) != (3 if req.get("mode") == "council" else 1):
        raise ValueError("UNEXPECTED_PEER_EXCHANGE_LENGTH")
    if exchanges[-1].get("text") != dialogue.get("final_text"):
        raise ValueError("FINAL_TEXT_NOT_LAST_MODEL_TURN")
    if any(t.get("role") != role for t,role in zip(
            exchanges, ["initial","critique","revised"] if req.get("mode")=="council"
            else ["initial"])):
        raise ValueError("BAD_ROLE_ORDER")
    initial = score_text(exchanges[0].get("text"), expected)
    final = score_text(dialogue.get("final_text"), expected)
    return {
        "schema": SCHEMA,
        "source_issue_number": req.get("issue_number"),
        "source_run_id": record.get("source_run_id"),
        "source_dialogue_sha256": dialogue["sha256"],
        "mode": req.get("mode"),
        "params": {"a":params[0], "b":params[1],
                   "offset":params[2], "modulus":params[3]},
        "expected": expected,
        "initial": initial,
        "final": final,
        "peer_changed_correctness": (
            final["correct"] != initial["correct"] if req.get("mode")=="council" else None),
        "quality_verified_by_two_internal_code_oracles": True,
        "independent_external_replication": False,
        "human_reviewed": False,
        "admitted_for_training": False,
        "model_weight_update": False,
    }


def report(directory):
    root = Path(directory)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("MISSING_SOURCE_CORPUS")
    files = sorted((root/"records").glob("*.json"))
    if len(files) > 400:
        raise ValueError("CORPUS_EXCEEDS_BOUNDS")
    scored = []
    skipped = 0
    seen = set()
    for file in files:
        if file.is_symlink() or file.stat().st_size > 75_000:
            raise ValueError("UNTRUSTED_SOURCE_FILE")
        record = json.loads(file.read_text(encoding="utf-8"))
        score = score_record(record)
        if score is None:
            skipped += 1
            continue
        sha = score["source_dialogue_sha256"]
        if sha in seen:
            raise ValueError("DUPLICATED_DIALOGUE_SHA")
        seen.add(sha)
        scored.append(score)
    return {
        "schema": "janus.open_llm.objective_report/1",
        "source_count": len(files),
        "objective_challenges": len(scored),
        "nonobjective_held_out": skipped,
        "initial_correct": sum(v["initial"]["correct"] for v in scored),
        "final_correct": sum(v["final"]["correct"] for v in scored),
        "peer_corrections": sum(v["peer_changed_correctness"] is True and
                                v["final"]["correct"] for v in scored),
        "peer_regressions": sum(v["peer_changed_correctness"] is True and
                               not v["final"]["correct"] for v in scored),
        "records": scored,
        "interpretation": "INTERNAL_DETERMINISTIC_ORACLE_CHECK_ONLY",
        "external_validation": False,
        "automatic_dataset_admission": False,
        "automatic_weight_update": False,
        "sentinel_dispatch": False,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    r = report(args.corpus)
    r["report_sha256"] = seal(r)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in r.items() if k!="records"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
