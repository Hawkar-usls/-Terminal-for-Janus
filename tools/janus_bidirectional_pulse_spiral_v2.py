#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

PAIR_QUEUE = [
    ("BASELINE", "TRUTH_FIREWALL"),
    ("ZERO_DELTA", "FORK_FIREWALL"),
    ("AURA_CANDIDATE", "HOME_RECEIPT"),
    ("DEMIHEAD_BINDING", "DEMIHEAD_BINDING"),
]
MAX_PAIR_PULSES = 4


def hbytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hjson(value: Any) -> str:
    return hbytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    return raw.decode("utf-8-sig"), hbytes(raw)


def read_json(path: Path) -> tuple[dict[str, Any], str]:
    text, digest = read_text(path)
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON_OBJECT_REQUIRED")
    return value, digest


def all_terms(text: str, terms: list[str]) -> bool:
    return all(t in text for t in terms)


def build_tests(*, pulse_contract: dict[str, Any], pulse_receipt: dict[str, Any], self_contract: dict[str, Any], fork_contract: dict[str, Any], fork_runtime: str, aura_runtime: str, demi_runtime: str, home_runtime: str, hashes: dict[str, str]) -> dict[str, dict[str, Any]]:
    tests: dict[str, dict[str, Any]] = {}

    baseline_ok = (
        pulse_receipt.get("status") == "PULSE_TRAIN_PASS_INTERNAL"
        and pulse_receipt.get("all_declared_pulses_passed") is True
        and pulse_receipt.get("world_truth") is False
    )
    tests["BASELINE"] = {
        "purpose": "Start bidirectional firing only from a passed fail-closed pulse baseline.",
        "evidence": {"pulse_receipt_sha256": hashes["pulse_receipt"], "status": pulse_receipt.get("status")},
        "passed": baseline_ok,
        "expected": "PULSE_TRAIN_PASS_INTERNAL + all_declared_pulses_passed=true + world_truth=false",
        "observed": str(pulse_receipt.get("status")),
    }

    zero_ok = (
        "ZERO_STATE_DELTA -> HOLD_STALL_NO_PROMOTION" in pulse_contract.get("laws", [])
        and "ZERO_STATE_DELTA -> HOLD_STALL_NO_PROMOTION" in self_contract.get("self_reference_laws", [])
        and pulse_contract.get("promotion_gate", {}).get("every_advanced_pulse_must_change_state_hash") is True
    )
    tests["ZERO_DELTA"] = {
        "purpose": "A forward or reverse lane with no state delta must not promote.",
        "evidence": {"pulse_contract_sha256": hashes["pulse_contract"], "self_contract_sha256": hashes["self_contract"]},
        "passed": zero_ok,
        "expected": "ZERO_DELTA => HOLD_STALL_NO_PROMOTION",
        "observed": "gate present" if zero_ok else "gate missing",
    }

    aura_ok = all_terms(aura_runtime, [
        "origin_prime_candidate", "parent_origin_state_hash", "state_delta_sha256",
        "candidate_state_hash", "final_origin_prime_authority", "CANDIDATE_STATE_ADVANCE",
    ])
    tests["AURA_CANDIDATE"] = {
        "purpose": "Forward construction remains candidate-only while reverse inspection can trace it to its parent.",
        "evidence": {"aura_sha256": hashes["aura_runtime"]},
        "passed": aura_ok,
        "expected": "candidate-only + parent/delta/hash binding",
        "observed": "firewall present" if aura_ok else "firewall incomplete",
    }

    demi_ok = all_terms(demi_runtime, [
        "candidate_state_hash", "origin_state_hash", "state_delta_sha256",
        "parent_origin_state_hash", "candidate_valid", "verified_return_eligible",
    ])
    tests["DEMIHEAD_BINDING"] = {
        "purpose": "The center gate must validate the same transition from both directional readings.",
        "evidence": {"demihead_sha256": hashes["demihead_runtime"]},
        "passed": demi_ok,
        "expected": "candidate/hash/parent/delta gate",
        "observed": "binding present" if demi_ok else "binding missing",
    }

    home_ok = all_terms(home_runtime, [
        "demihead_arbitration_receipt", "arbitration_sha256",
        "DEMIHEAD_ARBITRATION_HASH_MISMATCH", "candidate_valid",
        "NO_DEMIHEAD_ARBITRATION_RECEIPT_FAIL_CLOSED",
    ])
    tests["HOME_RECEIPT"] = {
        "purpose": "Reverse traversal must not accept a bare historical PASS as a valid parent transition.",
        "evidence": {"home_sha256": hashes["home_runtime"]},
        "passed": home_ok,
        "expected": "real hash-valid receipt required",
        "observed": "receipt firewall present" if home_ok else "receipt firewall incomplete",
    }

    fork_ok = (
        fork_contract.get("fork_habitat_install", {}).get("automatic_upstream_pr") is False
        and fork_contract.get("fork_habitat_install", {}).get("automatic_upstream_issue") is False
        and fork_contract.get("budgets", {}).get("mass_upstream_effect_budget") == 0
        and all_terms(fork_runtime, [
            '"upstream_writeback_authorized": False',
            '"automatic_upstream_pr": False',
            '"mass_upstream_effect_budget": 0',
        ])
    )
    tests["FORK_FIREWALL"] = {
        "purpose": "Backward propagation across Habitat satellites must remain provenance-only and never become upstream authority.",
        "evidence": {"fork_contract_sha256": hashes["fork_contract"], "fork_runtime_sha256": hashes["fork_runtime"]},
        "passed": fork_ok,
        "expected": "upstream authority=0 in both directions",
        "observed": "firewall present" if fork_ok else "firewall incomplete",
    }

    truth_ok = (
        pulse_contract.get("truth_firewall", {}).get("pulse_train_pass_is_world_truth") is False
        and pulse_receipt.get("world_truth") is False
        and pulse_receipt.get("truth_firewall", {}).get("bidirectional_pass_is_world_truth", False) is False
    )
    tests["TRUTH_FIREWALL"] = {
        "purpose": "Agreement between forward and reverse lanes cannot manufacture world truth.",
        "evidence": {"pulse_contract_sha256": hashes["pulse_contract"], "baseline_world_truth": pulse_receipt.get("world_truth")},
        "passed": truth_ok,
        "expected": "BIDIRECTIONAL_AGREEMENT != WORLD_TRUTH",
        "observed": "firewall present" if truth_ok else "firewall incomplete",
    }
    return tests


def lane_receipt(*, direction: str, test_id: str, test: dict[str, Any], parent_state_hash: str, pair_index: int, barrier: threading.Barrier, launch: dict[str, Any]) -> dict[str, Any]:
    ready_ns = time.time_ns()
    barrier.wait()
    start_ns = time.time_ns()
    evidence_hash = hjson(test["evidence"])
    deterministic_delta = {
        "pair_index": pair_index,
        "direction": direction,
        "test_id": test_id,
        "verdict": "PASS" if test["passed"] else "FAIL",
        "evidence_sha256": evidence_hash,
        "parent_state_hash": parent_state_hash,
    }
    delta_hash = hjson(deterministic_delta)
    candidate_hash = hjson({
        "kind": "DIRECTIONAL_CANDIDATE",
        "parent_state_hash": parent_state_hash,
        "direction": direction,
        "test_id": test_id,
        "state_delta_sha256": delta_hash,
    })
    end_ns = time.time_ns()
    core = {
        "schema": "janus.bidirectional_pulse_spiral.lane_receipt.v2",
        "pair_index": pair_index,
        "direction": direction,
        "test_id": test_id,
        "parent_state_hash": parent_state_hash,
        "launch_barrier_id": launch["launch_barrier_id"],
        "launch_epoch_ns": launch["launch_epoch_ns"],
        "ready_epoch_ns": ready_ns,
        "start_epoch_ns": start_ns,
        "end_epoch_ns": end_ns,
        "purpose": test["purpose"],
        "expected": test["expected"],
        "observed": test["observed"],
        "pass": bool(test["passed"]),
        "evidence_sha256": evidence_hash,
        "state_delta_sha256": delta_hash,
        "candidate_state_hash": candidate_hash,
        "world_truth": False,
        "automatic_external_effect": False,
    }
    deterministic_receipt = {k: v for k, v in core.items() if not k.endswith("epoch_ns")}
    core["lane_receipt_sha256"] = hjson(deterministic_receipt)
    return core


def run(terminal: Path, aura: Path, demihead: Path, home: Path) -> dict[str, Any]:
    protocol, h_protocol = read_json(terminal / "contracts/JANUS_BIDIRECTIONAL_PULSE_SPIRAL_PROTOCOL-v2.0.json")
    pulse_contract, h_pc = read_json(terminal / "contracts/JANUS_PULSE_SPIRAL_PROTOCOL-v1.0.json")
    pulse_receipt, h_pr = read_json(terminal / "receipts/JANUS_PULSE_SPIRAL_LATEST.json")
    self_contract, h_sc = read_json(terminal / "contracts/JANUS_SELF_SPIRAL_PROTOCOL-v1.0.json")
    fork_contract, h_fc = read_json(terminal / "contracts/JANUS_HABITAT_FORK_EXPANSION-v1.0.json")
    fork_runtime, h_fr = read_text(terminal / "tools/janus_habitat_fork_expansion.py")
    aura_runtime, h_ar = read_text(aura / "tools/aura_5d_spiral_v2.py")
    demi_runtime, h_dr = read_text(demihead / "tools/aura_spi_habitat_spiral_bridge_v2_10.py")
    home_runtime, h_hr = read_text(home / "src/janus_spi/aura_habitat_spiral.py")

    hashes = {
        "protocol": h_protocol,
        "pulse_contract": h_pc,
        "pulse_receipt": h_pr,
        "self_contract": h_sc,
        "fork_contract": h_fc,
        "fork_runtime": h_fr,
        "aura_runtime": h_ar,
        "demihead_runtime": h_dr,
        "home_runtime": h_hr,
    }
    tests = build_tests(
        pulse_contract=pulse_contract, pulse_receipt=pulse_receipt, self_contract=self_contract,
        fork_contract=fork_contract, fork_runtime=fork_runtime, aura_runtime=aura_runtime,
        demi_runtime=demi_runtime, home_runtime=home_runtime, hashes=hashes,
    )

    if protocol.get("pairing") != [list(p) for p in PAIR_QUEUE]:
        raise RuntimeError("PROTOCOL_PAIRING_MISMATCH_REVIEW_REQUIRED")

    origin = hjson({"kind": "BIDIRECTIONAL_PULSE_ORIGIN", "source_hashes": hashes})
    state = origin
    seen = {origin}
    pair_receipts: list[dict[str, Any]] = []
    status = "BIDIRECTIONAL_PULSE_TRAIN_PASS_INTERNAL"

    for pair_index, (forward_id, reverse_id) in enumerate(PAIR_QUEUE):
        launch: dict[str, Any] = {
            "launch_barrier_id": hjson({"origin": state, "pair_index": pair_index, "forward": forward_id, "reverse": reverse_id})[:24],
            "launch_epoch_ns": None,
        }

        def barrier_action() -> None:
            launch["launch_epoch_ns"] = time.time_ns()

        barrier = threading.Barrier(2, action=barrier_action)
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"janus-bi-{pair_index}") as pool:
            f_future = pool.submit(
                lane_receipt, direction="FORWARD", test_id=forward_id, test=tests[forward_id],
                parent_state_hash=state, pair_index=pair_index, barrier=barrier, launch=launch,
            )
            r_future = pool.submit(
                lane_receipt, direction="REVERSE", test_id=reverse_id, test=tests[reverse_id],
                parent_state_hash=state, pair_index=pair_index, barrier=barrier, launch=launch,
            )
            forward = f_future.result()
            reverse = r_future.result()

        same_parent = forward["parent_state_hash"] == reverse["parent_state_hash"] == state
        same_barrier = forward["launch_barrier_id"] == reverse["launch_barrier_id"]
        both_pass = forward["pass"] and reverse["pass"]
        center_pair = forward_id == reverse_id
        center_consistent = (not center_pair) or (forward["evidence_sha256"] == reverse["evidence_sha256"])
        join_pass = bool(same_parent and same_barrier and both_pass and center_consistent)

        merged_delta = {
            "pair_index": pair_index,
            "parent_state_hash": state,
            "forward_test_id": forward_id,
            "reverse_test_id": reverse_id,
            "forward_lane_receipt_sha256": forward["lane_receipt_sha256"],
            "reverse_lane_receipt_sha256": reverse["lane_receipt_sha256"],
            "center_pair": center_pair,
            "join_pass": join_pass,
        }
        merged_delta_hash = hjson(merged_delta)
        merged_candidate = hjson({
            "kind": "BIDIRECTIONAL_MERGED_CANDIDATE",
            "parent_state_hash": state,
            "state_delta_sha256": merged_delta_hash,
            "pair_index": pair_index,
        })

        pair_receipt = {
            "schema": "janus.bidirectional_pulse_spiral.pair_receipt.v2",
            "pair_index": pair_index,
            "parent_state_hash": state,
            "forward": forward,
            "reverse": reverse,
            "join_gate": {
                "same_parent_hash": same_parent,
                "same_launch_barrier": same_barrier,
                "both_lanes_pass": both_pass,
                "center_pair": center_pair,
                "center_evidence_consistent": center_consistent,
                "pass": join_pass,
                "conflict_policy": "HOLD_CONFLICT_NO_PROMOTION",
            },
            "merged_state_delta_sha256": merged_delta_hash,
            "merged_candidate_state_hash": merged_candidate,
            "return": {
                "advance_allowed": join_pass,
                "next_origin_state_hash": merged_candidate if join_pass else state,
                "return_is_reset": False,
            },
            "world_truth": False,
        }
        pair_receipt["pair_receipt_sha256"] = hjson({k: v for k, v in pair_receipt.items() if k != "pair_receipt_sha256"})
        pair_receipts.append(pair_receipt)

        if not join_pass:
            status = "HOLD_CONFLICT_NO_PROMOTION"
            break
        if merged_candidate == state:
            status = "HOLD_STALL_NO_STATE_DELTA"
            break
        if merged_candidate in seen:
            status = "HOLD_REPEAT_STATE_RESONANCE"
            break
        seen.add(merged_candidate)
        state = merged_candidate

    result = {
        "schema": "janus.bidirectional_pulse_spiral.train.v2",
        "mode": "BIDIRECTIONAL_PULSE_SPIRAL",
        "execution_model": "CONCURRENT_FORWARD_AND_REVERSE_FROM_SHARED_PARENT_WITH_FAIL_CLOSED_JOIN",
        "origin_state_hash": origin,
        "final_state_hash": state,
        "pair_pulse_budget": MAX_PAIR_PULSES,
        "pair_pulse_count": len(pair_receipts),
        "passed_pair_pulses": sum(1 for p in pair_receipts if p["join_gate"]["pass"]),
        "all_pair_pulses_passed": len(pair_receipts) == len(PAIR_QUEUE) and all(p["join_gate"]["pass"] for p in pair_receipts),
        "status": status,
        "pair_pulses": pair_receipts,
        "source_hashes": hashes,
        "anti_runaway": {
            "max_pair_pulses": MAX_PAIR_PULSES,
            "autonomous_unbounded_recursion": False,
            "automatic_external_effect": False,
            "first_pair_failure_stops_train": True,
            "zero_delta_stops_train": True,
            "repeated_state_stops_train": True,
        },
        "truth_firewall": {
            "bidirectional_pass_is_world_truth": False,
            "agreement_between_lanes_is_external_validation": False,
            "reverse_consistency_is_causal_proof": False,
            "world_claim_requires_external_validation": True,
        },
        "next_gate": "FRESH_EVIDENCE_OR_EXTERNAL_VALIDATION" if status == "BIDIRECTIONAL_PULSE_TRAIN_PASS_INTERNAL" else "RECOVER_CONFLICT_AT_ORIGIN",
        "world_truth": False,
    }
    result["train_receipt_sha256"] = hjson({k: v for k, v in result.items() if k != "train_receipt_sha256"})
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="JANUS concurrent bidirectional pulse spiral v2")
    ap.add_argument("--terminal", type=Path, default=Path("."))
    ap.add_argument("--aura", type=Path, required=True)
    ap.add_argument("--demihead", type=Path, required=True)
    ap.add_argument("--home", type=Path, required=True)
    ap.add_argument("-o", "--output", type=Path, default=Path("receipts/JANUS_BIDIRECTIONAL_PULSE_SPIRAL_LATEST.json"))
    args = ap.parse_args()
    result = run(args.terminal.resolve(), args.aura.resolve(), args.demihead.resolve(), args.home.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pair_dir = args.output.parent / "bidirectional_pulse"
    pair_dir.mkdir(parents=True, exist_ok=True)
    for p in result["pair_pulses"]:
        (pair_dir / f"{p['pair_index']:02d}-PAIR.json").write_text(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "pair_pulse_count": result["pair_pulse_count"],
        "passed_pair_pulses": result["passed_pair_pulses"],
        "final_state_hash": result["final_state_hash"],
        "next_gate": result["next_gate"],
    }, ensure_ascii=False))
    return 0 if result["status"] == "BIDIRECTIONAL_PULSE_TRAIN_PASS_INTERNAL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
