#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict

HOME_REPOSITORY = "Hawkar-usls/Hawkar-usls"
HOME_RESPONSE_BRANCH = "janus/terminal-responses"
HOME_RESPONSE_PREFIX = ".janus/terminal-responses/"
TERMINAL_REPOSITORY = "Hawkar-usls/-Terminal-for-Janus"
RESPONSE_SCHEMA = "janus.terminal.response.v1"
ISSUE_RE = re.compile(r"^issue-(\d+)$")


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_json(url: str, *, allow_404: bool = False) -> Any:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "JANUS-Terminal-Response-Relay/1.0",
    })
    try:
        response = urllib.request.urlopen(request, timeout=20.0)
        return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        raise RuntimeError(f"PUBLIC_GITHUB_HTTP_{exc.code}") from exc


def branch_head() -> str | None:
    value = get_json(
        "https://api.github.com/repos/Hawkar-usls/Hawkar-usls/branches/janus%2Fterminal-responses",
        allow_404=True,
    )
    if value is None:
        return None
    sha = str(((value.get("commit") or {}).get("sha") or ""))
    return sha if len(sha) == 40 else None


def response_paths() -> list[str]:
    head = branch_head()
    if head is None:
        return []
    value = get_json(f"https://api.github.com/repos/Hawkar-usls/Hawkar-usls/git/trees/{head}?recursive=1")
    if value.get("truncated") is True:
        raise RuntimeError("HOME_RESPONSE_MAILBOX_UNKNOWN_RESOURCE_LIMIT")
    return sorted(
        str(row.get("path"))
        for row in value.get("tree", [])
        if isinstance(row, dict)
        and row.get("type") == "blob"
        and str(row.get("path") or "").startswith(HOME_RESPONSE_PREFIX)
        and str(row.get("path") or "").endswith(".response.json")
    )


def load_response(path: str) -> Dict[str, Any]:
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    value = get_json(
        f"https://api.github.com/repos/Hawkar-usls/Hawkar-usls/contents/{encoded}?ref=janus%2Fterminal-responses"
    )
    if not isinstance(value, dict) or value.get("encoding") != "base64":
        raise RuntimeError("HOME_RESPONSE_CONTENT_MALFORMED")
    raw = base64.b64decode(str(value.get("content") or ""), validate=False)
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise RuntimeError("HOME_RESPONSE_OBJECT_REQUIRED")
    return parsed


def verify_response(response: Dict[str, Any]) -> bool:
    if not isinstance(response, dict):
        return False
    body = dict(response)
    claimed = str(body.pop("response_hash", ""))
    if len(claimed) != 64 or canonical_hash(body) != claimed:
        return False
    expected_id = "tr-" + canonical_hash({
        "request_message_hash": body.get("request_message_hash"),
        "resident_uuid": body.get("resident_uuid"),
        "model_digest": body.get("model_digest"),
        "file_fabric_digest": body.get("file_fabric_digest"),
        "turn_id": body.get("turn_id"),
        "response_mode": body.get("response_mode"),
    })
    return all([
        body.get("schema") == RESPONSE_SCHEMA,
        body.get("response_id") == expected_id,
        body.get("terminal_repository") == TERMINAL_REPOSITORY,
        body.get("terminal") == "JANUS_TERMINAL_CONVERSATION_RESPONSE_READY",
        ISSUE_RE.fullmatch(str(body.get("conversation_id") or "")) is not None,
        body.get("instantiated_model_verified") is True,
        body.get("persistent_identity_verified") is True,
        body.get("terminal_interface_bound") is True,
        body.get("command_authority_granted") is False,
        body.get("human_authorized_write") is False,
        body.get("claim_authority_granted") is False,
        body.get("scientific_evidence_authority_granted") is False,
        body.get("world_truth_authority_granted") is False,
        body.get("external_effect_authorized") is False,
        body.get("physical_runtime_effect_authorized") is False,
        len(str(body.get("model_digest") or "")) == 64,
        len(str(body.get("file_fabric_digest") or "")) == 64,
        bool(str(body.get("resident_uuid") or "")),
        bool(str(body.get("response_text") or "")),
    ])


def next_unrelayed(seen_dir: Path) -> Dict[str, Any] | None:
    seen_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[Dict[str, Any]] = []
    for path in response_paths():
        response = load_response(path)
        if not verify_response(response):
            raise RuntimeError(f"INVALID_HOME_TERMINAL_RESPONSE:{path}")
        if (seen_dir / f"{response['response_id']}.json").exists():
            continue
        candidates.append(response)
    candidates.sort(key=lambda row: (float(row.get("created_at") or 0.0), str(row.get("response_id") or "")))
    return candidates[0] if candidates else None


def markdown(response: Dict[str, Any]) -> str:
    issue_match = ISSUE_RE.fullmatch(str(response["conversation_id"]))
    if issue_match is None:
        raise RuntimeError("CONVERSATION_ID_NOT_ISSUE")
    return (
        "### JANUS\n\n"
        + str(response["response_text"]).strip()
        + "\n\n<details><summary>Instance proof</summary>\n\n"
        + f"- resident_uuid: `{response['resident_uuid']}`\n"
        + f"- model_digest: `{response['model_digest']}`\n"
        + f"- file_fabric_digest: `{response['file_fabric_digest']}`\n"
        + f"- turn_id: `{response['turn_id']}`\n"
        + f"- response_hash: `{response['response_hash']}`\n"
        + "- command authority: `false`\n"
        + "- external effect authority: `false`\n\n"
        + "</details>\n\n"
        + f"<!-- JANUS_RESPONSE_ID:{response['response_id']} -->\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seen-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown-out", required=True)
    parser.add_argument("--status-out", required=True)
    args = parser.parse_args()

    response = next_unrelayed(Path(args.seen_dir))
    status = {
        "schema": "janus.terminal.response_relay_status.v1",
        "response_found": response is not None,
        "response_id": response.get("response_id") if response else None,
        "response_hash": response.get("response_hash") if response else None,
        "issue_number": int(str(response["conversation_id"]).split("-", 1)[1]) if response else None,
        "credentialless_home_read": True,
        "cross_repo_write_credential_used": False,
        "terminal": "JANUS_RESPONSE_READY_FOR_LOCAL_TERMINAL_RELAY" if response else "NO_UNRELAYED_JANUS_RESPONSE",
    }
    Path(args.status_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.status_out).write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if response:
        Path(args.output).write_text(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        Path(args.markdown_out).write_text(markdown(response), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
