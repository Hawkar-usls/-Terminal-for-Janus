#!/usr/bin/env python3
"""JANUS: provenance-checked, non-executable dialogue intake and learning admission gate.

No model output is executed. All writes are limited to a dedicated corpus branch
by the calling workflow; this module cannot train or promote model weights.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = "Hawkar-usls/-Terminal-for-Janus"
OWNER = "Hawkar-usls"
WORKFLOW = "JANUS Open LLM CPU Chat"
ALLOWED_EVENTS = {"issues", "issue_comment", "workflow_dispatch"}
ALLOWED_QWEN = {"Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"}
PEER = "HuggingFaceTB/SmolLM2-360M-Instruct"
ALLOWED_LABELS = {"REJECT_FACTUAL_ERROR", "REJECT_TRUNCATED", "HOLD_UNVERIFIED",
                  "APPROVED_FOR_SHADOW_TRAINING"}
MAX_ARCHIVE_BYTES = 125_000
MAX_JSON_BYTES = 45_000
MIN_TRAIN_PAIRS = 32
MIN_TRAIN_ISSUES = 8
SHA = re.compile(r"^[0-9a-f]{64}$")


def canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":")).encode("utf-8")).hexdigest()


def verify_dialogue(d):
    if not isinstance(d, dict) or d.get("schema") != "janus.open_llm.dialogue.v1":
        raise ValueError("INVALID_DIALOGUE_SCHEMA")
    actual = d.get("sha256")
    if not isinstance(actual, str) or not SHA.fullmatch(actual):
        raise ValueError("MISSING_DIALOGUE_DIGEST")
    if canonical_sha({k: v for k, v in d.items() if k != "sha256"}) != actual:
        raise ValueError("DIALOGUE_DIGEST_MISMATCH")
    req = d.get("request")
    if not isinstance(req, dict) or req.get("schema") != "janus.open_llm.request.v1":
        raise ValueError("INVALID_REQUEST_SCHEMA")
    rq_sha = req.get("request_sha256")
    if not isinstance(rq_sha, str) or not SHA.fullmatch(rq_sha):
        raise ValueError("REQUEST_DIGEST_MISSING")
    if canonical_sha({k: v for k, v in req.items() if k != "request_sha256"}) != rq_sha:
        raise ValueError("REQUEST_DIGEST_MISMATCH")
    if (req.get("requested_by") != OWNER or req.get("execution_authority") != "TEXT_ONLY"
            or req.get("request_source") not in ("github_issue", "github_issue_comment",
                                                  "manual_workflow_dispatch")):
        raise ValueError("REQUEST_NOT_OWNER_TEXT_ONLY")
    prompt = req.get("prompt")
    if not isinstance(prompt, str) or not 1 <= len(prompt) <= 2000:
        raise ValueError("INVALID_PROMPT")
    exchanges = d.get("exchanges")
    mode = req.get("mode")
    if mode not in ("qwen", "council") or not isinstance(exchanges, list):
        raise ValueError("INVALID_EXCHANGE_FORMAT")
    if len(exchanges) != (3 if mode == "council" else 1):
        raise ValueError("INVALID_EXCHANGE_COUNT")
    expected = ["initial", "critique", "revised"] if mode == "council" else ["initial"]
    for i, (turn, role) in enumerate(zip(exchanges, expected)):
        model = PEER if role == "critique" else None
        if (not isinstance(turn, dict) or turn.get("role") != role
                or (turn.get("model") != model if model else turn.get("model") not in ALLOWED_QWEN)
                or not isinstance(turn.get("text"), str) or not 1 <= len(turn["text"]) <= 2000):
            raise ValueError(f"INVALID_MODEL_TURN_{i}")
    if mode == "council" and exchanges[0]["model"] != exchanges[2]["model"]:
        raise ValueError("MODEL_REVISION_NOT_SAME_QWEN")
    if d.get("final_text") != exchanges[-1]["text"]:
        raise ValueError("FINAL_TEXT_NOT_FROM_LAST_TURN")
    for field in ("weight_update_performed", "peer_feedback_is_ground_truth",
                  "native_janus_model_modified", "self_evolution_verified"):
        if d.get(field) is not False:
            raise ValueError(f"UNSAFE_OR_UNVERIFIED_{field}")
    if d.get("classification") != "EXPERIMENTAL_PEER_DIALOGUE_UNVERIFIED":
        raise ValueError("WRONG_DIALOGUE_CLASSIFICATION")
    return True


def parse_request(body):
    body = (body or "").strip()
    if body.startswith("### Message"):
        body = body.partition("### Message")[2].split("### Conversation mode", 1)[0].strip()
    match = re.fullmatch(r"/(qwen|council)\s+(.+)", body, flags=re.DOTALL)
    if not match:
        raise ValueError("NO_SOURCE_COMMAND")
    return match.group(1), match.group(2).strip()


def verify_issue_binding(d, issue, comments):
    req = d["request"]
    if req.get("request_source") == "manual_workflow_dispatch":
        if req.get("issue_number") is not None:
            raise ValueError("DISPATCH_WITH_ISSUE")
        return {"kind": "MANUAL_DISPATCH_NO_ISSUE", "reply_url": None}
    if (not isinstance(issue, dict) or issue.get("number") != req.get("issue_number")
            or "pull_request" in issue):
        raise ValueError("ISSUE_ID_MISMATCH")
    if not isinstance(comments, list):
        raise ValueError("ISSUE_COMMENTS_NOT_VERIFIED")
    if req["request_source"] == "github_issue":
        source = issue
        if not str(issue.get("title", "")).startswith("[JANUS CHAT]"):
            raise ValueError("SOURCE_ISSUE_NOT_CHAT")
    else:
        source = next((c for c in comments if c.get("id") == req.get("source_id")), None)
        if source is None:
            raise ValueError("SOURCE_COMMENT_NOT_FOUND")
    if source.get("id") != req.get("source_id"):
        raise ValueError("SOURCE_OBJECT_ID_MISMATCH")
    if ((source.get("user") or {}).get("login")) != OWNER:
        raise ValueError("SOURCE_ACTOR_MISMATCH")
    mode, prompt = parse_request(source.get("body"))
    if (mode, prompt) != (req["mode"], req["prompt"]):
        raise ValueError("SOURCE_PROMPT_MISMATCH")

    # The issue comment is a second trace from an already completed workflow.
    # Matching the SHA is origin evidence, not independent verification of quality.
    anchor = f"Receipt SHA-256: \x60{d['sha256']}\x60"
    bot = next((c for c in comments
                if ((c.get("user") or {}).get("login")) == "github-actions[bot]"
                and str(c.get("body", "")).startswith("<!-- JANUS_OPEN_LLM_CPU_ADAPTER -->")
                and anchor in c["body"]), None)
    if bot is None:
        raise ValueError("NO_MATCHING_BOT_RESPONSE")
    return {"kind": "ISSUE_AND_BOT_REPLY_DIGEST_MATCH",
            "reply_url": bot.get("html_url") or
            f"https://github.com/{REPO}/issues/{req['issue_number']}"}


def verify_workflow_run(run):
    if (not isinstance(run, dict) or run.get("name") != WORKFLOW
            or run.get("conclusion") != "success"
            or run.get("event") not in ALLOWED_EVENTS):
        raise ValueError("WRONG_WORKFLOW_OR_CONCLUSION")
    if ((run.get("actor") or {}).get("login") != OWNER
            or (run.get("repository") or {}).get("full_name") != REPO
            or run.get("head_branch") != "main"):
        raise ValueError("WORKFLOW_SOURCE_NOT_OWNER_MAIN")
    return True


def extract_archive(archive):
    if not isinstance(archive, bytes) or not 100 <= len(archive) <= MAX_ARCHIVE_BYTES:
        raise ValueError("ARTIFACT_TOO_LARGE_OR_EMPTY")
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        members = zipped.infolist()
        if len(members) > 6 or len({m.filename for m in members}) != len(members):
            raise ValueError("UNEXPECTED_ZIP_MEMBERS")
        for member in members:
            if (member.filename.startswith("/") or ".." in member.filename.split("/")
                    or member.file_size > MAX_JSON_BYTES):
                raise ValueError("UNSAFE_ZIP_MEMBER")
        if "dialogue.json" not in zipped.namelist():
            raise ValueError("MISSING_DIALOGUE_JSON")
        raw = zipped.read("dialogue.json")
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("DIALOGUE_EXCEEDS_LIMIT")
    dialogue = json.loads(raw.decode("utf-8"))
    verify_dialogue(dialogue)
    return dialogue


def label_dialogue(d, config):
    label = (config.get("labels") or {}).get(d["sha256"], {
        "status": "HOLD_UNVERIFIED",
        "reason": "Neither model agreement nor fluent text constitutes a trusted label.",
    })
    if not isinstance(label, dict) or label.get("status") not in ALLOWED_LABELS:
        raise ValueError("INVALID_HUMAN_REVIEW_LABEL")
    if label["status"] == "APPROVED_FOR_SHADOW_TRAINING":
        # A machine-generated label is never sufficient to create training authority.
        reviews = label.get("human_review_sources", [])
        if (not isinstance(reviews, list) or len(set(reviews)) < 2
                or any(not isinstance(x, str) or not x.startswith("https://") for x in reviews)):
            raise ValueError("MISSING_TWO_HUMAN_REVIEW_REFERENCES")
        if label.get("independent_evidence") is not True:
            raise ValueError("NOT_INDEPENDENTLY_EVIDENCED")
    return label


def make_record(run, artifact, dialogue, issue, comments, labels):
    verify_workflow_run(run)
    verify_dialogue(dialogue)
    bind = verify_issue_binding(dialogue, issue, comments)
    request = dialogue["request"]
    if (run["event"] == "workflow_dispatch") != (request["request_source"] == "manual_workflow_dispatch"):
        raise ValueError("RUN_EVENT_NOT_MATCHING_REQUEST")
    record = {
        "schema": "janus.open_llm.corpus_record.v1",
        "source_repository": REPO,
        "source_run_id": run["id"],
        "source_run_url": run.get("html_url"),
        "head_sha": run.get("head_sha"),
        "artifact_id": artifact["id"],
        "source_sha256": dialogue["sha256"],
        "source_binding": bind,
        "review": label_dialogue(dialogue, labels),
        "dialogue": dialogue,
        "quality_is_independent_evidence": False,
        "model_weight_change": False,
        "auto_promotion_authority": False,
    }
    record["record_sha256"] = canonical_sha(record)
    return record


def summarize(records):
    unique = {}
    for r in records:
        source = r.get("dialogue", {}).get("sha256")
        if source in unique:
            if unique[source]["record_sha256"] != r.get("record_sha256"):
                raise ValueError("SAME_DIALOGUE_MULTIPLE_PROVENANCES")
            continue
        if r.get("record_sha256") != canonical_sha({k: v for k, v in r.items() if k != "record_sha256"}):
            raise ValueError("RECORD_INTEGRITY_FAILURE")
        unique[source] = r
    admitted = [r for r in unique.values()
                if r["review"]["status"] == "APPROVED_FOR_SHADOW_TRAINING"]
    issue_ids = {r["dialogue"]["request"]["issue_number"] for r in admitted}
    modes = {r["dialogue"]["request"]["mode"] for r in admitted}
    statuses = {}
    for r in unique.values():
        status = r["review"]["status"]
        statuses[status] = statuses.get(status, 0) + 1
    blockers = []
    if len(admitted) < MIN_TRAIN_PAIRS:
        blockers.append("HOLD_INSUFFICIENT_HUMAN_VERIFIED_PAIRS")
    if len(issue_ids) < MIN_TRAIN_ISSUES:
        blockers.append("HOLD_INSUFFICIENT_DISTINCT_ISSUES")
    if "council" not in modes:
        blockers.append("HOLD_NO_REVIEWED_COUNCIL_CASES")
    # A closed evaluation requires a custodian and separately frozen never-read tasks.
    blockers.append("HOLD_INDEPENDENT_PROSPECTIVE_CUSTODIAN_NOT_PROVIDED")
    return {
        "schema": "janus.open_llm.learning_gate.v1",
        "total_source_verified": len(unique),
        "label_counts": statuses,
        "approved_training_pairs": len(admitted),
        "distinct_approved_issues": len(issue_ids),
        "allowed_for_shadow_training": False if blockers else True,
        "automatic_weight_promotion": False,
        "native_janus_weights_changed": False,
        "three_node_sentinel_control_untouched": True,
        "blockers": blockers,
    }


def api_json(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True,
                            text=True, check=True, timeout=35)
    return json.loads(result.stdout)


def api_archive(artifact_id):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "artifact.zip"
        subprocess.run(["gh", "api", f"/repos/{REPO}/actions/artifacts/{int(artifact_id)}/zip",
                        "--output", str(path)], check=True, timeout=60,
                       stdout=subprocess.DEVNULL)
        return path.read_bytes()


def issue_and_comments(issue_number):
    issue = api_json(f"/repos/{REPO}/issues/{int(issue_number)}")
    comments = []
    for page in range(1, 6):
        part = api_json(f"/repos/{REPO}/issues/{int(issue_number)}/comments?per_page=100&page={page}")
        if not isinstance(part, list):
            raise ValueError("INVALID_ISSUE_COMMENTS_API")
        comments.extend(part)
        if len(part) < 100:
            break
    return issue, comments


def harvest(directory, labels, run_id=None, limit=50):
    dest = Path(directory) / "records"
    dest.mkdir(parents=True, exist_ok=True)
    if run_id:
        runs = [api_json(f"/repos/{REPO}/actions/runs/{int(run_id)}")]
    else:
        data = api_json(f"/repos/{REPO}/actions/workflows/janus-open-llm.yml/runs?per_page={min(max(limit, 1), 100)}")
        runs = data.get("workflow_runs", [])[:limit]
    errors, added = [], []
    for run in runs:
        try:
            # Contract/smoke jobs have no dialogue artifact, and are skipped.
            if run.get("event") not in ALLOWED_EVENTS or run.get("conclusion") != "success":
                continue
            verify_workflow_run(run)
            arts = api_json(f"/repos/{REPO}/actions/runs/{int(run['id'])}/artifacts").get("artifacts", [])
            matches = [a for a in arts if a.get("name") == f"janus-open-llm-{run['id']}" and not a.get("expired")]
            if len(matches) != 1:
                errors.append({"run_id": run["id"], "status": "HOLD_EXPECTED_ARTIFACT_NOT_FOUND"})
                continue
            artifact = matches[0]
            if artifact.get("size_in_bytes", MAX_ARCHIVE_BYTES + 1) > MAX_ARCHIVE_BYTES:
                raise ValueError("ARTIFACT_METADATA_TOO_LARGE")
            d = extract_archive(api_archive(artifact["id"]))
            req = d["request"]
            issue, comments = (issue_and_comments(req["issue_number"])
                               if req["issue_number"] is not None else (None, []))
            record = make_record(run, artifact, d, issue, comments, labels)
            target = dest / f"{run['id']}-{d['sha256']}.json"
            raw = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            if target.exists():
                if target.read_text(encoding="utf-8") != raw:
                    raise ValueError("CREATE_ONLY_EXISTING_RECORD_MISMATCH")
            else:
                target.write_text(raw, encoding="utf-8")
                added.append(str(target))
        except Exception as exc:
            errors.append({"run_id": run.get("id"), "status": "HOLD_SOURCE_VALIDATION_FAILURE",
                           "reason": str(exc)[:180]})
    all_records = []
    for file in sorted(dest.glob("*.json")):
        value = json.loads(file.read_text(encoding="utf-8"))
        if value.get("record_sha256") != canonical_sha(
                {k: v for k, v in value.items() if k != "record_sha256"}):
            raise ValueError("STORED_RECORD_MODIFIED")
        all_records.append(value)
    report = summarize(all_records)
    report["added_records"] = len(added)
    report["errors"] = errors
    report["candidate_only"] = True
    report["training_started"] = False
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--run-id", type=int, default=None)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))
    if labels.get("schema") != "janus.open_llm.review_labels.v1":
        raise ValueError("INVALID_REVIEW_LABELS_SCHEMA")
    report = harvest(args.dest, labels, args.run_id, args.limit)
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
