#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
R1_EXECUTION_BINDING_REQUIRED = "R1_EXECUTION_BINDING_REQUIRED"
R1_BINDING = Path(__file__).resolve().parents[1] / "config/JANUS_R1_ADMISSION_BINDING.json"
MAX_METADATA_BYTES = 2_000_000
ALLOWED_MODES = {"REFERENCE_FORK", "ADAPTATION_FORK", "COMPATIBILITY_FORK", "EXPERIMENT_FORK"}
DERIVATIVE_LICENSE_HINTS = {
    "mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "mpl-2.0",
    "gpl-2.0", "gpl-3.0", "lgpl-2.1", "lgpl-3.0", "agpl-3.0", "unlicense",
}


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("R1_REDIRECT_DENIED")


def load_r1_binding() -> dict[str, Any]:
    """Declarative routing only. No setting or environment switch enables effects."""
    binding = json.loads(R1_BINDING.read_text(encoding="utf-8"))
    if (binding.get("schema") != "janus.terminal.r1_admission_binding.v1" or
            binding.get("mode") != "OBSERVE_AND_PROPOSE_ONLY" or
            type(binding.get("authority_delta")) is not int or binding["authority_delta"] != 0 or
            binding.get("execution_allowed") is not False or
            binding.get("external_effects") is not False):
        raise PermissionError(R1_EXECUTION_BINDING_REQUIRED)
    return binding


def api_request(path: str, *, token: str | None = None, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    # Hard barrier below every legacy mutation helper, independent of config,
    # candidate PASS strings, policy_grant_id, tokens or environment variables.
    if method != "GET" or body is not None or token is not None:
        raise PermissionError(R1_EXECUTION_BINDING_REQUIRED)
    if not re.fullmatch(r"/repos/[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", path):
        raise ValueError("R1_PUBLIC_METADATA_ROUTE_ONLY")
    if path.rsplit("/", 1)[-1] in {".", ".."}:
        raise ValueError("R1_PUBLIC_METADATA_ROUTE_ONLY")
    req = urllib.request.Request(API + path, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "JANUS-Habitat-Fork-Expansion/1.1")
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=20) as r:
            if r.geturl() != req.full_url:
                raise ValueError("R1_RESPONSE_LOCATION_CHANGED")
            payload = r.read(MAX_METADATA_BYTES + 1)
            if len(payload) > MAX_METADATA_BYTES:
                raise ValueError("R1_METADATA_TOO_LARGE")
            return json.loads(payload.decode("utf-8")) if payload else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GITHUB_HTTP_{exc.code}") from None


def parse_full_name(value: str) -> tuple[str, str]:
    if (type(value) is not str or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", value) or
            value.split("/")[-1] in {".", ".."}):
        raise ValueError("UPSTREAM_FULL_NAME_MUST_BE_OWNER_SLASH_REPO")
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
    if token is not None:
        raise PermissionError(R1_EXECUTION_BINDING_REQUIRED)
    load_r1_binding()
    validate_request(req)
    upstream = str(req["upstream_full_name"])
    meta = api_request(f"/repos/{urllib.parse.quote(upstream, safe='/')}")
    if (not isinstance(meta, dict) or meta.get("private") is not False or
            meta.get("visibility") != "public" or
            str(meta.get("full_name", "")).lower() != upstream.lower()):
        raise ValueError("R1_PUBLIC_CANONICAL_SOURCE_REQUIRED")
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
    status = "R1_REFERENCE_PROPOSAL_ONLY"

    if disabled:
        status = "REJECT_REPOSITORY_DISABLED"; reasons.append("repository_disabled")
    elif archived and req["requested_mode"] != "REFERENCE_FORK":
        status = "HOLD_ARCHIVED_UPSTREAM"; reasons.append("archived_requires_reference_or_review")
    elif allow_forking is False:
        status = "REJECT_FORKING_DISABLED"; reasons.append("allow_forking_false")

    derivative_allowed = spdx in DERIVATIVE_LICENSE_HINTS
    if spdx in {"noassertion", "other", ""}:
        warnings.append("LICENSE_OR_RIGHTS_UNKNOWN")
        if status == "R1_REFERENCE_PROPOSAL_ONLY":
            status = "HOLD_LICENSE_OR_RIGHTS_UNKNOWN"
            reasons.append("derivative_mode_requires_known_rights_or_human_legal_override")

    if len(str(req["purpose"])) < 12 or len(str(req["expected_gain"])) < 8:
        if status == "R1_REFERENCE_PROPOSAL_ONLY":
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
        "execution_allowed": False,
        "independent_admission_gate": "HOLD_EXTERNAL_REVIEW_REQUIRED",
        "source_commit_pinned": False,
        "license_bytes_verified": False,
        "quarantine_scan": "NOT_RUN",
        "next_gate": R1_EXECUTION_BINDING_REQUIRED,
    }



def wait_for_fork(*args, **kwargs):
    raise PermissionError(R1_EXECUTION_BINDING_REQUIRED)


def put_file(*args, **kwargs):
    raise PermissionError(R1_EXECUTION_BINDING_REQUIRED)


def ensure_habitat_branch(*args, **kwargs):
    raise PermissionError(R1_EXECUTION_BINDING_REQUIRED)


def install_habitat_edge(*args, **kwargs):
    raise PermissionError(R1_EXECUTION_BINDING_REQUIRED)


def execute_fork(*args, **kwargs):
    """No executor exists in R1. Even a forged PASS and real token cannot act."""
    raise PermissionError(R1_EXECUTION_BINDING_REQUIRED)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="JANUS public metadata fork proposal; effects blocked")
    ap.add_argument("request_json", type=Path)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--destination-org")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args(argv)
    # Reject before opening a request or inspecting a candidate. Do not even
    # read JANUS_FORK_TOKEN: credentials have no purpose in this preview lane.
    if args.execute or args.destination_org is not None:
        print(R1_EXECUTION_BINDING_REQUIRED, file=sys.stderr)
        return 2
    req = json.loads(args.request_json.read_text(encoding="utf-8-sig"))
    candidate = inspect_candidate(req)
    out = {"candidate": candidate, "execution": None, "executor_ready": False,
           "execution_allowed": False, "mode": "OBSERVE_AND_PROPOSE_ONLY",
           "execution_blocker": R1_EXECUTION_BINDING_REQUIRED,
           "blocked_execution_request": req.get("execute_if_gated") is True}
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
