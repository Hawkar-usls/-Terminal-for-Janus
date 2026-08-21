#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TEXT_EXTENSIONS = {
    ".json", ".jsonl", ".ndjson", ".md", ".py", ".yml", ".yaml", ".toml",
    ".txt", ".js", ".ts", ".html", ".sh", ".ini", ".cfg", ".c", ".cpp", ".h", ".hpp"
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".pytest_cache"}
FROZEN_PARTS = {"receipts", "archive", "archives", "legacy", "historical", "snapshots"}
SAFE_LOOP_HINTS = (
    "heartbeat", "retry", "poll", "watcher", "event loop", "device loop", "training epoch",
    "for epoch", "while true", "while(true)", "serve_forever", "poll_seconds", "retry_after"
)

HARD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("CYCLE_MODEL_TRUE", re.compile(r'["\']cycle_model["\']\s*:\s*true', re.I)),
    ("RETURN_IS_RESET_TRUE", re.compile(r'["\']return_is_reset["\']\s*:\s*true', re.I)),
    ("STATE_MUST_ADVANCE_FALSE", re.compile(r'["\']state_must_advance["\']\s*:\s*false', re.I)),
    ("SEMANTIC_CLOSED_RING_ALLOWED", re.compile(r'["\']semantic_closed_ring_allowed["\']\s*:\s*true', re.I)),
    ("PREDICTION_CYCLE_ROUTE", re.compile(r'["\']prediction_cycle["\']\s*:', re.I)),
]
LEGACY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("STANDARD_CYCLE_NAME", re.compile(r'["\']standard_cycle["\']\s*:', re.I)),
    ("CYCLE_METHOD_NAME", re.compile(r'^\s*def\s+cycle\s*\(', re.I)),
]
REVIEW_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("RESET_STATE_LANGUAGE", re.compile(r'\breset\b.{0,80}\b(state|origin|memory|generation)\b|\b(state|origin|memory|generation)\b.{0,80}\breset\b', re.I)),
    ("CLOSED_LOOP_LANGUAGE", re.compile(r'closed[- ]loop|замкнут(?:ый|ого|ом)?\s+(?:круг|цикл)|кольцев', re.I)),
    ("CYCLE_LANGUAGE", re.compile(r'\bcycle\b|\bcyclic\b|\bцикл\b|\bкруг\b', re.I)),
]


def norm_rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def is_frozen_path(rel: str) -> bool:
    parts = {p.lower() for p in Path(rel).parts}
    if parts & FROZEN_PARTS:
        return True
    # Meta Registry data is append/frozen provenance, not active runtime.
    return rel.startswith("data/")


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > 4 * 1024 * 1024:
            return None
        raw = path.read_bytes()
        if b"\x00" in raw[:4096]:
            return None
        return raw.decode("utf-8-sig", errors="replace")
    except Exception:
        return None


def classify_line(repo: str, rel: str, line: str, line_no: int) -> list[dict[str, Any]]:
    stripped = line.strip()
    low = stripped.lower()
    historical = is_frozen_path(rel)
    findings: list[dict[str, Any]] = []

    def add(kind: str, code: str, pattern: str) -> None:
        findings.append({
            "repository": repo,
            "path": rel,
            "line": line_no,
            "classification": "HISTORICAL_FROZEN" if historical and kind in {"HARD_RING", "LEGACY_COMPAT", "REVIEW"} else kind,
            "code": code,
            "pattern": pattern,
            "excerpt": stripped[:500],
            "active_surface": not historical,
        })

    for code, pat in HARD_PATTERNS:
        if pat.search(line):
            add("HARD_RING", code, pat.pattern)

    # Active v1 Aura peer is hard only when it is not explicitly marked legacy/fallback.
    if "aura_habitat_spiral_peer_v1.py" in line:
        if any(x in low for x in ("legacy", "fallback", "compat")):
            add("LEGACY_COMPAT", "AURA_V1_EXPLICIT_FALLBACK", "aura_habitat_spiral_peer_v1.py")
        elif ".github/workflows/" in rel or rel.startswith("config/") or rel.startswith("spec/"):
            add("HARD_RING", "ACTIVE_AURA_V1_PATH", "aura_habitat_spiral_peer_v1.py")
        else:
            add("LEGACY_COMPAT", "AURA_V1_REFERENCE", "aura_habitat_spiral_peer_v1.py")

    for code, pat in LEGACY_PATTERNS:
        if pat.search(line):
            add("LEGACY_COMPAT", code, pat.pattern)

    # Only one generic review hit per line; technical loops are explicitly safe.
    if any(hint in low for hint in SAFE_LOOP_HINTS):
        if any(tok in low for tok in ("loop", "while", "poll", "retry", "heartbeat", "epoch", "watcher", "serve_forever")):
            add("SAFE_INFRA_LOOP", "INFRASTRUCTURE_LOOP", "safe_loop_hint")
    else:
        for code, pat in REVIEW_PATTERNS:
            if pat.search(line):
                # Avoid repeating a generic cycle hit if the line already has a stronger hard/legacy classification.
                if not any(f["classification"] in {"HARD_RING", "LEGACY_COMPAT", "HISTORICAL_FROZEN"} for f in findings):
                    add("REVIEW", code, pat.pattern)
                break
    return findings


def scan_repo(repo: str, root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    files_scanned = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = norm_rel(path, root)
        text = read_text(path)
        if text is None:
            continue
        files_scanned += 1
        for line_no, line in enumerate(text.splitlines(), 1):
            findings.extend(classify_line(repo, rel, line, line_no))
    return {"repository": repo, "root": str(root), "files_scanned": files_scanned, "findings": findings}


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit JANUS repositories for obsolete semantic ring constraints")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--manifest", required=True, help="JSON list with repository/root/status entries")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    workspace = Path(args.workspace).resolve()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    results = []
    inaccessible = []
    all_findings: list[dict[str, Any]] = []

    for item in manifest:
        repo = item["repository"]
        status = item.get("status", "SCANNABLE")
        if status != "SCANNABLE":
            inaccessible.append({"repository": repo, "status": status, "reason": item.get("reason")})
            continue
        root = workspace / item["root"]
        if not root.exists():
            inaccessible.append({"repository": repo, "status": "MISSING_LOCAL_CHECKOUT"})
            continue
        result = scan_repo(repo, root)
        results.append({k: v for k, v in result.items() if k != "findings"})
        all_findings.extend(result["findings"])

    counts = {k: 0 for k in ("HARD_RING", "LEGACY_COMPAT", "REVIEW", "SAFE_INFRA_LOOP", "HISTORICAL_FROZEN")}
    for f in all_findings:
        counts[f["classification"]] = counts.get(f["classification"], 0) + 1

    active_hard = [f for f in all_findings if f["classification"] == "HARD_RING" and f["active_surface"]]
    receipt = {
        "schema": "janus.system_spiral_migration.audit_receipt.v1",
        "status": "PASS_NO_ACTIVE_HARD_RING" if not active_hard else "REVIEW_REQUIRED_ACTIVE_HARD_RING",
        "workspace": str(workspace),
        "repositories_targeted": len(manifest),
        "repositories_scanned": len(results),
        "repositories_inaccessible_or_skipped": inaccessible,
        "files_scanned": sum(r["files_scanned"] for r in results),
        "counts": counts,
        "active_hard_ring_count": len(active_hard),
        "active_hard_rings": active_hard[:200],
        "legacy_compat_findings": [f for f in all_findings if f["classification"] == "LEGACY_COMPAT"][:300],
        "review_findings": [f for f in all_findings if f["classification"] == "REVIEW"][:300],
        "safe_infrastructure_loop_sample": [f for f in all_findings if f["classification"] == "SAFE_INFRA_LOOP"][:100],
        "historical_frozen_sample": [f for f in all_findings if f["classification"] == "HISTORICAL_FROZEN"][:100],
        "laws": [
            "POSITION_MAY_REPEAT_BUT_STATE_MUST_ADVANCE",
            "RETURN != RESET",
            "INFRASTRUCTURE_LOOP != COGNITIVE_RING",
            "HISTORICAL_FROZEN != ACTIVE_RUNTIME",
            "LEGACY_API_NAME != LEGACY_SEMANTICS",
        ],
        "migration_policy": {
            "rewrite_frozen_history": False,
            "rewrite_active_same_state_semantic_rings": True,
            "preserve_safe_infrastructure_loops": True,
            "legacy_api_aliases_may_remain_when_behavior_is_state_advancing": True,
        },
        "world_truth": False,
    }
    Path(args.output).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "repositories_scanned": receipt["repositories_scanned"],
        "files_scanned": receipt["files_scanned"],
        "counts": counts,
        "active_hard_ring_count": len(active_hard),
    }, ensure_ascii=False, indent=2))
    return 0 if not active_hard else 4


if __name__ == "__main__":
    raise SystemExit(main())
