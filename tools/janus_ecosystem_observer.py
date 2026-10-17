#!/usr/bin/env python3
"""Read-only public JANUS repository discovery with hash-chained durable receipts.

This is a topology observer, not a repository dispatcher or an evidence grader.
In particular it never executes discovered code or auto-enrolls a new node into
the separate, executable JANUS_CONSTELLATION workflow.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "janus.terminal.ecosystem_observation.v1"
REPO_PATTERN = re.compile(r"^Hawkar-usls/[A-Za-z0-9_.-]+$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_PUBLIC_REPOS = 2000


def digest(value: dict[str, Any]) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def verify_receipt(receipt: Any) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        return False
    recorded = receipt.get("observation_sha256")
    if not isinstance(recorded, str) or not HEX64.fullmatch(recorded):
        return False
    unbound = {k: v for k, v in receipt.items() if k != "observation_sha256"}
    return digest(unbound) == recorded


def _repo_name(value: Any) -> str:
    if not isinstance(value, str) or not REPO_PATTERN.fullmatch(value):
        raise ValueError("INVALID_OR_FOREIGN_REPOSITORY_NAME")
    return value


def read_policy(policy_path: Path, constellation_path: Path) -> tuple[dict[str, Any], set[str]]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    constellation = json.loads(constellation_path.read_text(encoding="utf-8"))
    if policy.get("schema") != "janus.terminal.ecosystem_observer.v1":
        raise ValueError("INVALID_OBSERVER_POLICY_SCHEMA")
    for key, required in (
        ("owner", "Hawkar-usls"), ("public_only", True),
        ("private_content_publication", False), ("source_text_is_command", False),
        ("observation_grants_execution_authority", False),
        ("observation_grants_scientific_authority", False),
        ("auto_enroll_into_live_constellation", False), ("auto_run_repositories", False),
        ("auto_merge", False),
    ):
        if policy.get(key) != required:
            raise ValueError(f"POLICY_AUTHORITY_VIOLATION:{key}")
    if constellation.get("schema") != "janus.terminal.constellation.v1":
        raise ValueError("INVALID_CONSTELLATION_SCHEMA")
    active = {_repo_name(x["repository"]) for x in constellation["nodes"]}
    # The live scanner handles these two independently of `nodes`.
    active.update({"Hawkar-usls/-Terminal-for-Janus", "Hawkar-usls/Janus_Genesis"})
    candidates = [_repo_name(x["repository"]) for x in policy["discovery_candidates"]]
    excluded = [_repo_name(x["repository"]) for x in policy["excluded_public_repositories"]]
    if len(candidates) != len(set(candidates)) or len(excluded) != len(set(excluded)):
        raise ValueError("DUPLICATE_OBSERVER_REPOSITORY")
    if (set(candidates) & set(excluded)) or (active & set(candidates + excluded)):
        raise ValueError("OBSERVER_LIVE_OR_CANDIDATE_COLLISION")
    for candidate in policy["discovery_candidates"]:
        if not all(isinstance(candidate.get(k), str) and candidate[k] for k in ("route", "stage", "boundary")):
            raise ValueError("INCOMPLETE_DISCOVERY_CANDIDATE")
    return policy, active


def fetch_public_repositories(*, token: str | None = None) -> tuple[list[dict[str, Any]], int]:
    """GitHub /users public endpoint; `private=true` is never used downstream."""
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, 22):
        if page == 21:
            raise RuntimeError("GITHUB_PUBLIC_REPOSITORY_PAGE_LIMIT")
        url = f"https://api.github.com/users/Hawkar-usls/repos?per_page=100&page={page}&type=owner"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "JANUS-Ecosystem-Observer/1.0"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                rows = json.load(response)
        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError("PUBLIC_GITHUB_DISCOVERY_UNAVAILABLE") from exc
        if not isinstance(rows, list):
            raise RuntimeError("PUBLIC_GITHUB_DISCOVERY_INVALID_PAGE")
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError("PUBLIC_GITHUB_DISCOVERY_INVALID_ROW")
            # Fail closed on ambiguous visibility; never expose private metadata.
            if row.get("private") is not False:
                continue
            full_name = _repo_name(row.get("full_name"))
            if full_name in seen:
                raise RuntimeError("PUBLIC_GITHUB_DISCOVERY_DUPLICATE")
            seen.add(full_name)
            records.append({"full_name": full_name, "private": False, "visibility": "public"})
            if len(records) > MAX_PUBLIC_REPOS:
                raise RuntimeError("PUBLIC_GITHUB_DISCOVERY_SIZE_LIMIT")
        if len(rows) < 100:
            if not records:
                raise RuntimeError("PUBLIC_GITHUB_DISCOVERY_EMPTY")
            return records, page
    raise RuntimeError("PUBLIC_GITHUB_DISCOVERY_INCOMPLETE")


def build_observation(
    policy: dict[str, Any], active: set[str], rows: list[dict[str, Any]],
    *, source: str, pages: int, previous: dict[str, Any] | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    if previous is not None and not verify_receipt(previous):
        raise ValueError("PREVIOUS_OBSERVATION_INTEGRITY_FAILURE")
    if not rows or pages < 1:
        raise ValueError("INCOMPLETE_PUBLIC_DISCOVERY")
    # Fail closed: even a malformed, mislabeled fixture is not an excuse to
    # publish a private repository. Require both public markers explicitly.
    public_names = sorted({
        _repo_name(x["full_name"]) for x in rows
        if isinstance(x, dict) and x.get("private") is False
        and x.get("visibility") == "public"
    })
    if not public_names or len(public_names) > MAX_PUBLIC_REPOS:
        raise ValueError("INVALID_PUBLIC_DISCOVERY_SIZE")
    visible = set(public_names)
    candidates = policy["discovery_candidates"]
    excluded = policy["excluded_public_repositories"]
    candidate_names = {row["repository"] for row in candidates}
    excluded_names = {row["repository"] for row in excluded}
    coverage = active | candidate_names | excluded_names
    observation = {
        "schema": SCHEMA,
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sequence": (previous["sequence"] + 1) if previous else 1,
        "predecessor_sha256": previous["observation_sha256"] if previous else None,
        "source": source,
        "source_pages_complete": pages,
        "public_repository_count": len(public_names),
        "public_repository_names": public_names,
        "active_constellation_public": sorted(active & visible),
        "discovery_candidates": [
            {"repository": row["repository"], "route": row["route"],
             "next_gate": row["stage"], "boundary": row["boundary"],
             "status": "PRESENT_NOT_AUTO_ENROLLED" if row["repository"] in visible else "NOT_FOUND_IN_PUBLIC_DISCOVERY"}
            for row in candidates
        ],
        "excluded_public": sorted(row["repository"] for row in excluded if row["repository"] in visible),
        "unclassified_public": sorted(visible - coverage),
        "counts": {
            "active_visible": len(active & visible),
            "candidates_visible": len(candidate_names & visible),
            "excluded_visible": len(excluded_names & visible),
            "unclassified_visible": len(visible - coverage),
        },
        "authority": {
            "github_listing_proves_runtime": False,
            "repository_code_executed": False,
            "live_constellation_modified": False,
            "science_or_medical_truth_promoted": False,
            "external_effect_authorized": False,
            "human_review_required_before_activation": True,
        },
    }
    observation["observation_sha256"] = digest(observation)
    return observation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="Read public GitHub API")
    mode.add_argument("--fixture", type=Path, help="Offline public GitHub-style listing")
    mode.add_argument("--verify", type=Path, help="Check a stored observation digest")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--policy", type=Path, default=Path("config/JANUS_ECOSYSTEM_OBSERVER.json"))
    parser.add_argument("--constellation", type=Path, default=Path("config/JANUS_CONSTELLATION.json"))
    args = parser.parse_args()
    try:
        if args.verify:
            if not verify_receipt(json.loads(args.verify.read_text(encoding="utf-8"))):
                raise ValueError("OBSERVATION_INTEGRITY_FAILURE")
            print("JANUS_ECOSYSTEM_OBSERVATION_INTEGRITY=PASS")
            return 0
        if not args.output:
            raise ValueError("OUTPUT_PATH_REQUIRED")
        policy, active = read_policy(args.policy, args.constellation)
        if args.live:
            import os
            rows, pages = fetch_public_repositories(token=os.getenv("GITHUB_TOKEN"))
            source = "GITHUB_REST_PUBLIC_API"
        else:
            rows = json.loads(args.fixture.read_text(encoding="utf-8"))
            pages, source = 1, "OFFLINE_FIXTURE_NOT_LIVE_EVIDENCE"
        previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
        observation = build_observation(policy, active, rows, source=source, pages=pages, previous=previous)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(observation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"JANUS_ECOSYSTEM_OBSERVATION=PASS public={observation['public_repository_count']} "
              f"candidates={observation['counts']['candidates_visible']} "
              f"unclassified={observation['counts']['unclassified_visible']} "
              f"sequence={observation['sequence']}")
        return 0
    except (ValueError, KeyError, TypeError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"JANUS_ECOSYSTEM_OBSERVATION=FAIL_CLOSED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
