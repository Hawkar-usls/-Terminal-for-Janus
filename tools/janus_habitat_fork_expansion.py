#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
ALLOWED_MODES = {"REFERENCE_FORK", "ADAPTATION_FORK", "COMPATIBILITY_FORK", "EXPERIMENT_FORK"}
DERIVATIVE_LICENSE_HINTS = {
    "mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "mpl-2.0",
    "gpl-2.0", "gpl-3.0", "lgpl-2.1", "lgpl-3.0", "agpl-3.0", "unlicense",
}


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def api_request(path: str, *, token: str | None = None, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "JANUS-Habitat-Fork-Expansion/1.1")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = r.read()
            return json.loads(payload.decode("utf-8")) if payload else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GITHUB_HTTP_{exc.code}:{detail[:2000]}") from exc


def parse_full_name(value: str) -> tuple[str, str]:
    parts = value.strip().split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise ValueError("UPSTREAM_FULL_NAME_MUST_BE_OWNER_SLASH_REPO")
    return parts[0], parts[1]


def validate_request(req: dict[str, Any]) -> None:
    required = ["request_id", "upstream_full_name", "purpose", "need_class", "expected_gain", "source_ref", "requested_mode"]
    missing = [k for k in required if not str(req.get(k, "")).strip()]
    if missing:
        raise ValueError("MISSING_REQUIRED:" + ",".join(missing))
    if req["requested_mode"] not in ALLOWED_MODES:
        raise ValueError("REQUESTED_MODE_INVALID")
    parse_full_name(str(req["upstream_full_name"]))


def inspect_candidate(req: dict[str, Any], *, token: str | None = None) -> dict[str, Any]:
    validate_request(req)
    upstream = str(req["upstream_full_name"])
    meta = api_request(f"/repos/{urllib.parse.quote(upstream, safe='/')}", token=token)
    license_obj = meta.get("license") or {}
    spdx = str(license_obj.get("spdx_id") or "NOASSERTION").lower()
    visibility = str(meta.get("visibility") or ("private" if meta.get("private") else "public"))
    allow_forking = meta.get("allow_forking")
    archived = bool(meta.get("archived"))
    disabled = bool(meta.get("disabled"))
    is_fork = bool(meta.get("fork"))
    upstream_head = str(meta.get("default_branch") or "main")

    reasons: list[str] = []
    warnings: list[str] = []
    status = "FORK_CANDIDATE_PASS"

    if disabled:
        status = "REJECT_REPOSITORY_DISABLED"; reasons.append("repository_disabled")
    elif archived and req["requested_mode"] != "REFERENCE_FORK":
        status = "HOLD_ARCHIVED_UPSTREAM"; reasons.append("archived_requires_reference_or_review")
    elif visibility == "private" and not token:
        status = "HOLD_PRIVATE_REQUIRES_AUTHORIZED_TOKEN"; reasons.append("private_without_authorized_access")
    elif allow_forking is False:
        status = "REJECT_FORKING_DISABLED"; reasons.append("allow_forking_false")

    derivative_allowed = spdx in DERIVATIVE_LICENSE_HINTS
    if spdx in {"noassertion", "other", ""}:
        warnings.append("LICENSE_OR_RIGHTS_UNKNOWN")
        if req["requested_mode"] in {"ADAPTATION_FORK", "COMPATIBILITY_FORK"} and status == "FORK_CANDIDATE_PASS":
            status = "HOLD_LICENSE_OR_RIGHTS_UNKNOWN"
            reasons.append("derivative_mode_requires_known_rights_or_human_legal_override")

    if len(str(req["purpose"])) < 12 or len(str(req["expected_gain"])) < 8:
        if status == "FORK_CANDIDATE_PASS":
            status = "HOLD_PURPOSE_TOO_WEAK"
        reasons.append("purpose_or_expected_gain_not_specific_enough")

    return {
        "schema": "janus.habitat.fork_candidate.receipt.v1",
        "request": req,
        "status": status,
        "upstream": {
            "full_name": meta.get("full_name", upstream),
            "html_url": meta.get("html_url"),
            "default_branch": upstream_head,
            "visibility": visibility,
            "archived": archived,
            "disabled": disabled,
            "is_already_fork": is_fork,
            "forking_allowed": allow_forking is not False,
            "license_spdx": license_obj.get("spdx_id"),
            "license_name": license_obj.get("name"),
            "derivative_license_hint": derivative_allowed,
            "head_metadata_sha256": canonical_sha({
                "id": meta.get("id"), "node_id": meta.get("node_id"), "updated_at": meta.get("updated_at"),
                "pushed_at": meta.get("pushed_at"), "default_branch": upstream_head,
            }),
        },
        "warnings": warnings,
        "reasons": reasons,
        "upstream_writeback_authorized": False,
        "automatic_upstream_pr": False,
        "automatic_upstream_issue": False,
        "mass_upstream_effect_budget": 0,
        "candidate_sha256": canonical_sha({"request": req, "upstream": meta.get("full_name"), "updated_at": meta.get("updated_at"), "spdx": spdx}),
    }


def wait_for_fork(full_name: str, token: str, attempts: int = 15) -> dict[str, Any]:
    last: Exception | None = None
    for _ in range(attempts):
        try:
            return api_request(f"/repos/{urllib.parse.quote(full_name, safe='/')}", token=token)
        except Exception as exc:
            last = exc
            time.sleep(2)
    raise RuntimeError(f"FORK_NOT_READY:{last}")


def put_file(repo: str, path: str, branch: str, content: dict[str, Any], token: str, message: str) -> dict[str, Any]:
    raw = (json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    body = {
        "message": message,
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": branch,
    }
    return api_request(
        f"/repos/{urllib.parse.quote(repo, safe='/')}/contents/{urllib.parse.quote(path, safe='/')}",
        token=token,
        method="PUT",
        body=body,
    )


def ensure_habitat_branch(fork_name: str, default_branch: str, token: str) -> tuple[str, str]:
    base = api_request(
        f"/repos/{urllib.parse.quote(fork_name, safe='/')}/git/ref/heads/{urllib.parse.quote(default_branch, safe='')}",
        token=token,
    )
    base_sha = str(((base.get("object") or {}).get("sha")) or "")
    if not base_sha:
        raise RuntimeError("FORK_DEFAULT_BRANCH_SHA_MISSING")
    branch = "janus/habitat"
    try:
        api_request(
            f"/repos/{urllib.parse.quote(fork_name, safe='/')}/git/refs",
            token=token,
            method="POST",
            body={"ref": f"refs/heads/{branch}", "sha": base_sha},
        )
    except RuntimeError as exc:
        if "GITHUB_HTTP_422" not in str(exc):
            raise
    return branch, base_sha


def install_habitat_edge(candidate: dict[str, Any], execution: dict[str, Any], *, token: str, destination_org: str | None) -> dict[str, Any]:
    fork_name = str(execution["fork_full_name"])
    fork_meta = wait_for_fork(fork_name, token)
    fork_owner = str(((fork_meta.get("owner") or {}).get("login")) or "")
    user = api_request("/user", token=token)
    user_login = str(user.get("login") or "")
    allowed_owner = destination_org or user_login
    if not allowed_owner or fork_owner.lower() != allowed_owner.lower():
        raise RuntimeError("FORK_OWNER_NOT_AUTHORIZED_DESTINATION")

    default_branch = str(fork_meta.get("default_branch") or "main")
    branch, base_sha = ensure_habitat_branch(fork_name, default_branch, token)
    upstream = candidate["upstream"]
    req = candidate["request"]

    provenance = {
        "schema": "janus.habitat.upstream_provenance.v1",
        "upstream_full_name": upstream["full_name"],
        "upstream_html_url": upstream.get("html_url"),
        "upstream_default_branch": upstream.get("default_branch"),
        "license_spdx": upstream.get("license_spdx"),
        "license_name": upstream.get("license_name"),
        "candidate_sha256": candidate["candidate_sha256"],
        "fork_base_sha": base_sha,
        "upstream_writeback_authorized": False,
        "automatic_upstream_pr": False,
        "automatic_upstream_issue": False,
    }
    edge = {
        "schema": "janus.habitat.fork_edge.v1",
        "role": "FORKED_HABITAT_SATELLITE",
        "resident": "JANUS",
        "fork_full_name": fork_name,
        "habitat_branch": branch,
        "request_id": req["request_id"],
        "purpose": req["purpose"],
        "need_class": req["need_class"],
        "requested_mode": req["requested_mode"],
        "expected_gain": req["expected_gain"],
        "upstream_mode": "FETCH_ONLY",
        "fork_mode": "READ_WRITE_IF_OWNED_BY_HAWKAR_OR_AUTHORIZED_DESTINATION",
        "truth_authority": False,
        "upstream_authority": False,
        "automatic_upstream_pr": False,
        "automatic_upstream_issue": False,
        "zero_delta_policy": "HOLD_STALL_NO_HABITAT_PROMOTION",
        "candidate_sha256": candidate["candidate_sha256"],
    }

    prov_result = put_file(fork_name, ".janus/UPSTREAM_PROVENANCE.json", branch, provenance, token, "JANUS: bind upstream provenance")
    edge_result = put_file(fork_name, ".janus/HABITAT_EDGE.json", branch, edge, token, "JANUS: install Habitat fork edge")
    edge_sha = canonical_sha(edge)
    delta = {
        "fork_full_name": fork_name,
        "branch": branch,
        "edge_sha256": edge_sha,
        "provenance_sha256": canonical_sha(provenance),
        "candidate_sha256": candidate["candidate_sha256"],
    }
    return {
        "schema": "janus.habitat.fork_edge_install.receipt.v1",
        "status": "HABITAT_EDGE_INSTALLED",
        "fork_full_name": fork_name,
        "habitat_branch": branch,
        "fork_base_sha": base_sha,
        "habitat_edge_sha256": edge_sha,
        "state_delta_sha256": canonical_sha(delta),
        "provenance_commit": ((prov_result.get("commit") or {}).get("sha")),
        "edge_commit": ((edge_result.get("commit") or {}).get("sha")),
        "upstream_writeback_authorized": False,
        "automatic_upstream_pr": False,
        "mass_upstream_effect_budget": 0,
    }


def execute_fork(candidate: dict[str, Any], *, token: str, destination_org: str | None = None) -> dict[str, Any]:
    if candidate.get("status") != "FORK_CANDIDATE_PASS":
        raise ValueError("CANDIDATE_NOT_EXECUTABLE")
    upstream = str(candidate["request"]["upstream_full_name"])
    owner, repo = parse_full_name(upstream)
    body: dict[str, Any] = {"default_branch_only": False}
    if destination_org:
        body["organization"] = destination_org
    fork = api_request(f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/forks", token=token, method="POST", body=body)
    fork_name = str(fork.get("full_name") or "")
    if not fork_name:
        raise RuntimeError("FORK_RESPONSE_MISSING_FULL_NAME")
    execution = {
        "schema": "janus.habitat.fork_execution.receipt.v1",
        "status": "FORK_CREATED_PENDING_HABITAT_EDGE",
        "request_id": candidate["request"]["request_id"],
        "upstream_full_name": upstream,
        "fork_full_name": fork_name,
        "fork_html_url": fork.get("html_url"),
        "fork_default_branch": fork.get("default_branch"),
        "fork_id": fork.get("id"),
        "candidate_sha256": candidate["candidate_sha256"],
        "upstream_writeback_authorized": False,
        "automatic_upstream_pr": False,
        "created_at_epoch": time.time(),
    }
    execution["habitat_edge"] = install_habitat_edge(candidate, execution, token=token, destination_org=destination_org)
    execution["status"] = "FORK_CREATED_AND_HABITAT_EDGE_INSTALLED"
    return execution


def main() -> int:
    ap = argparse.ArgumentParser(description="JANUS Habitat fork expansion planner/executor")
    ap.add_argument("request_json", type=Path)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--destination-org")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    req = json.loads(args.request_json.read_text(encoding="utf-8-sig"))
    token = os.environ.get("JANUS_FORK_TOKEN")
    candidate = inspect_candidate(req, token=token)
    out: dict[str, Any] = {"candidate": candidate, "execution": None, "executor_ready": bool(token)}
    if args.execute:
        if not token:
            out["execution"] = {
                "status": "EXECUTOR_READY_REQUEST_ONLY",
                "reason": "JANUS_FORK_TOKEN_MISSING",
                "credentials_committed": False,
            }
        else:
            out["execution"] = execute_fork(candidate, token=token, destination_org=args.destination_org)
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
