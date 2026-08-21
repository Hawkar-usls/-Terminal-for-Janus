#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    return raw.decode("utf-8-sig"), sha256_bytes(raw)


def finding(fid: str, severity: str, title: str, anchors: list[str], detail: str, next_gate: str) -> dict[str, Any]:
    return {
        "finding_id": fid,
        "severity": severity,
        "title": title,
        "source_anchors": anchors,
        "detail": detail,
        "validation_status": "IMPLEMENTATION_TRACE_FINDING_NOT_WORLD_TRUTH",
        "next_gate": next_gate,
    }


def run(terminal: Path, aura: Path, demihead: Path, home: Path) -> dict[str, Any]:
    subjects = {
        "mirror_contract": terminal / "contracts/JANUS_JSON_MIRROR_PASS_PROTOCOL-v1.0.json",
        "deep_contract": terminal / "contracts/JANUS_JSON_5D_DEEP_ANALYSIS_PROTOCOL-v1.0.json",
        "self_contract": terminal / "contracts/JANUS_SELF_SPIRAL_PROTOCOL-v1.0.json",
        "terminal_5d": terminal / "tools/janus_json_5d_deep.py",
        "aura_5d": aura / "tools/aura_5d_spiral_v2.py",
        "demihead_bridge": demihead / "tools/aura_spi_habitat_spiral_bridge_v2_10.py",
        "home_spiral": home / "src/janus_spi/aura_habitat_spiral.py",
    }
    texts: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for key, path in subjects.items():
        text, digest = read(path)
        texts[key] = text
        hashes[key] = digest

    deep = json.loads(texts["deep_contract"])
    self_contract = json.loads(texts["self_contract"])
    declared = {
        "origin_prime_not_automatic_verified_return": "ORIGIN_PRIME != AUTOMATIC_VERIFIED_RETURN" in deep.get("anti_dogma", []),
        "verified_return_or_hold_or_reject_declared": "VERIFIED_RETURN_OR_HOLD_OR_REJECT" in deep.get("canonical_cycle", []),
        "zero_delta_hold_declared": "ZERO_STATE_DELTA -> HOLD_STALL_NO_PROMOTION" in self_contract.get("self_reference_laws", []),
        "self_consistency_not_world_truth": "SELF_CONSISTENCY_PASS != WORLD_TRUTH" in self_contract.get("self_reference_laws", []),
    }

    recovered: list[dict[str, Any]] = []
    aura_text = texts["aura_5d"]
    demi_text = texts["demihead_bridge"]
    home_text = texts["home_spiral"]

    if '"spiral_status": "ADVANCED_TO_ORIGIN_PRIME" if advanced' in aura_text and 'origin_prime_candidate' not in aura_text:
        recovered.append(finding(
            "SELF-R1", "HIGH", "Aura names a pre-arbitration state as ORIGIN_PRIME",
            ["aura-oracle-tg:tools/aura_5d_spiral_v2.py"],
            "The local 5D analyzer can emit ADVANCED_TO_ORIGIN_PRIME before DemiHead arbitration. This conflates a cognitive state-delta candidate with final promotion.",
            "Rename the local result to ORIGIN_PRIME_CANDIDATE / CANDIDATE_STATE_ADVANCE and reserve ORIGIN_PRIME for verified return."
        ))

    direct_verified = 'verified_eligible = decision == "PASS" and intent_authority == "DEMIHEAD_GOLDPROMPT_VERIFIED"' in demi_text
    delta_terms = all(term in demi_text for term in ["state_delta_sha256", "origin_prime_state_hash", "parent_origin_state_hash"])
    if direct_verified and not delta_terms:
        recovered.append(finding(
            "SELF-R2", "HIGH", "DemiHead verified return is not bound to non-zero state advance",
            ["Demi_Head:tools/aura_spi_habitat_spiral_bridge_v2_10.py"],
            "PASS plus verified intent is sufficient for verified_return_eligible; the bridge does not require a candidate state hash, parent binding and non-zero delta.",
            "Require advanced=true, candidate_state_hash != origin_state_hash, parent hash equality and a bound state_delta hash before verified return."
        ))

    injected_decision = "demihead_decision: str = \"HOLD\"" in home_text and 'verified_eligible = demihead_decision == "PASS"' in home_text
    real_receipt_required = "demihead_arbitration_receipt" in home_text or "arbitration_sha256" in home_text
    if injected_decision and not real_receipt_required:
        recovered.append(finding(
            "SELF-R3", "HIGH", "Home runtime accepts a decision parameter instead of requiring a real DemiHead receipt",
            ["Hawkar-usls:src/janus_spi/aura_habitat_spiral.py"],
            "The live engine labels a local parameter as DemiHead arbitration. HOLD is safe, but the positive path is not end-to-end evidence that the DemiHead bridge actually ran.",
            "Make final promotion consume and verify a DemiHead arbitration receipt hash rather than a bare PASS parameter."
        ))

    if "SELF_CONSISTENCY_PASS != WORLD_TRUTH" not in texts["self_contract"]:
        recovered.append(finding(
            "SELF-R4", "CRITICAL", "Self-test lacks truth firewall", ["Terminal:JANUS_SELF_SPIRAL_PROTOCOL"],
            "A method that can certify its own world-truth would create circular epistemic authority.",
            "Freeze SELF_CONSISTENCY_PASS != WORLD_TRUTH and require external validation for world claims."
        ))

    authority_graph = {
        "nodes": ["SOURCE", "MIRROR_2PASS", "AURA_5D", "SPI", "DEMIHEAD", "HABITAT", "ORIGIN_PRIME"],
        "edges": [
            ["SOURCE", "MIRROR_2PASS", "INPUT"],
            ["MIRROR_2PASS", "AURA_5D", "STRUCTURED_CONTEXT"],
            ["AURA_5D", "SPI", "REFLECTION_NOT_EVIDENCE"],
            ["SPI", "DEMIHEAD", "SYNTHESIS_NOT_TRUTH"],
            ["DEMIHEAD", "HABITAT", "ARBITRATION"],
            ["HABITAT", "ORIGIN_PRIME", "PROMOTION_ONLY_AFTER_VERIFIED_RETURN"],
        ],
        "circular_truth_authority_detected": False,
        "note": "Self-audit output is not fed back as truth authority."
    }

    hard = [x for x in recovered if x["severity"] in {"CRITICAL", "HIGH"}]
    status = "HOLD_SELF_DEFECTS_RECOVERED" if hard else "SELF_CONSISTENCY_PASS"
    candidate = None
    if not hard:
        candidate = {
            "kind": "METHOD_PRIME_CANDIDATE",
            "parent_subject_set_sha256": sha256_bytes(json.dumps(hashes, sort_keys=True).encode()),
            "world_truth": False,
            "requires_external_validation_for_world_claims": True,
        }

    return {
        "schema": "janus.self_spiral.audit_receipt.v1",
        "status": status,
        "world_truth": False,
        "self_consistency_is_world_truth": False,
        "source_hashes": hashes,
        "D1_FORWARD_DECLARED_RULES": declared,
        "D2_REVERSE_RUNTIME_BACKCHECK": {"recovered_count": len(recovered), "findings": recovered},
        "D3_STRUCTURAL_AUTHORITY_GRAPH": authority_graph,
        "D4_ASSOCIATIVE_COUNTERMODEL": {
            "counterexample": "PASS + VERIFIED_INTENT + ZERO_STATE_DELTA",
            "required_result": "HOLD_STALL_NO_PROMOTION",
            "current_positive_path_fully_proves_this": False if any(x["finding_id"] == "SELF-R2" for x in recovered) else True,
            "association_is_evidence": False,
        },
        "D5_META_INVARIANT": {
            "invariant": "A method may establish internal consistency of its implementation, but cannot establish world truth merely by passing its own verifier.",
            "self_test_survival_is_external_validation": False,
            "origin_prime_candidate_is_origin_prime": False,
        },
        "recovered_at_origin": recovered,
        "self_consistency_gate": {
            "high_or_critical_defects": len(hard),
            "promotion_allowed": not hard,
            "zero_delta_must_hold": True,
            "real_demihead_receipt_required": True,
        },
        "method_prime_candidate": candidate,
        "claim_ceiling": "SELF_CONSISTENCY_AND_IMPLEMENTATION_AUDIT_ONLY_NOT_WORLD_TRUTH",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply JANUS spiral reasoning to the JANUS spiral method itself")
    ap.add_argument("--terminal", type=Path, default=Path("."))
    ap.add_argument("--aura", type=Path, required=True)
    ap.add_argument("--demihead", type=Path, required=True)
    ap.add_argument("--home", type=Path, required=True)
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    out = run(args.terminal.resolve(), args.aura.resolve(), args.demihead.resolve(), args.home.resolve())
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
