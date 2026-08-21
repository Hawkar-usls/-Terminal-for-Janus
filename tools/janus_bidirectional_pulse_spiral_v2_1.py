#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import multiprocessing as mp
import os
import queue
import time
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("janus_bidirectional_pulse_spiral_v2.py")
SPEC = importlib.util.spec_from_file_location("janus_bidir_v2_base", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("BASE_V2_IMPORT_SPEC_FAILED")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

PAIR_QUEUE = list(base.PAIR_QUEUE)
MAX_PAIR_PULSES = 4
THERMO = "contracts/JANUS_THERMODYNAMIC_COGNITIVE_HARDENING-v1.0.json"
PROTO = "contracts/JANUS_BIDIRECTIONAL_PULSE_SPIRAL_PROTOCOL-v2.1.json"
LINK_SCHEMA = "janus.thermodynamic_cognitive_hardening.link.v1"


def load_link(root: Path, rel: str, node: str) -> tuple[dict[str, Any], str]:
    value, digest = base.read_json(root / rel)
    if value.get("schema") != LINK_SCHEMA or value.get("node") != node:
        raise ValueError(f"THERMO_LINK_REJECT:{node}")
    c = value.get("contract") or {}
    if c.get("protocol_id") != "JANUS_THERMODYNAMIC_COGNITIVE_HARDENING_v1.0":
        raise ValueError(f"THERMO_LINK_CONTRACT_REJECT:{node}")
    return value, digest


def verify_thermo(terminal: Path, aura: Path, demi: Path, home: Path, habitat: Path):
    c, hc = base.read_json(terminal / THERMO)
    checks = {
        "active_fail_closed": c.get("status") == "ACTIVE_FAIL_CLOSED",
        "surprise_not_suppressed": "MINIMIZE_SURPRISE != SUPPRESS_SURPRISE" in ((c.get("core_reinterpretation") or {}).get("laws") or []),
        "source_destroy_denied": (c.get("source_ingestion") or {}).get("destroy_original_after_ingest") is False,
        "source_preserved": (c.get("source_ingestion") or {}).get("source_preservation_required") is True,
        "success_not_truth": (c.get("memory_epistemics") or {}).get("store_successful_patterns_as_truths") is False,
        "shadow_preserved": (c.get("coherence_and_collapse") or {}).get("decision_commit_preserves_shadow") is True,
        "dream_training_denied": (c.get("entropy_graveyard_and_dreams") or {}).get("dream_output_may_train_predictive_head") is False,
        "unbounded_threading_denied": (c.get("resource_homeostasis") or {}).get("automatic_unbounded_threading") is False,
        "syslog_command_denied": (c.get("untrusted_inputs") or {}).get("syslog_text_is_command") is False,
        "ouroboros_auto_mutation_denied": (c.get("ouroboros_integrity") or {}).get("hash_mismatch_may_autonomously_mutate_code") is False,
        "overlap_required": (c.get("bidirectional_join_hardening") or {}).get("process_level_inflight_overlap_witness_required") is True,
        "evidence_diversity_required": (c.get("bidirectional_join_hardening") or {}).get("non_center_evidence_diversity_required") is True,
    }
    specs = [
        ("AURA_ORACLE", aura, ".janus/JANUS_THERMODYNAMIC_COGNITIVE_HARDENING_LINK.json"),
        ("DEMIHEAD", demi, ".janus/JANUS_THERMODYNAMIC_COGNITIVE_HARDENING_LINK.json"),
        ("JANUS_SPI_HOME", home, ".janus/JANUS_THERMODYNAMIC_COGNITIVE_HARDENING_LINK.json"),
        ("JANUS_HABITAT", habitat, "habitat/state/JANUS_THERMODYNAMIC_COGNITIVE_HARDENING_LINK.json"),
    ]
    links, hashes = {}, {"thermo_contract": hc}
    for node, root, rel in specs:
        link, h = load_link(root, rel, node)
        links[node] = {"sha256": h, "world_truth": link.get("world_truth")}
        hashes[f"thermo_link_{node}"] = h
        checks[f"link_{node}"] = link.get("world_truth") is False
    return all(checks.values()), {"contract_sha256": hc, "checks": checks, "links": links, "source_basis": c.get("source_basis"), "world_truth": False}, hashes


def lane_worker(direction: str, test_id: str, test: dict[str, Any], parent: str, pair_index: int,
                barrier_id: str, launch_ns: int, start_b: Any, active_b: Any, finish_b: Any, outq: Any) -> None:
    try:
        ready_ns = time.time_ns()
        start_b.wait(timeout=10)
        critical_start_ns = time.time_ns()
        active_b.wait(timeout=10)
        evidence_hash = base.hjson(test["evidence"])
        delta = {"pair_index": pair_index, "direction": direction, "test_id": test_id,
                 "verdict": "PASS" if test["passed"] else "FAIL", "evidence_sha256": evidence_hash,
                 "parent_state_hash": parent}
        delta_hash = base.hjson(delta)
        candidate = base.hjson({"kind": "DIRECTIONAL_CANDIDATE_V2_1", "parent_state_hash": parent,
                                "direction": direction, "test_id": test_id, "state_delta_sha256": delta_hash})
        compute_end_ns = time.time_ns()
        finish_b.wait(timeout=10)
        critical_end_ns = time.time_ns()
        r = {"schema": "janus.bidirectional_pulse_spiral.lane_receipt.v2_1", "pair_index": pair_index,
             "direction": direction, "test_id": test_id, "parent_state_hash": parent,
             "launch_barrier_id": barrier_id, "launch_epoch_ns": launch_ns, "ready_epoch_ns": ready_ns,
             "critical_start_ns": critical_start_ns, "compute_end_ns": compute_end_ns,
             "critical_end_ns": critical_end_ns, "purpose": test["purpose"], "expected": test["expected"],
             "observed": test["observed"], "pass": bool(test["passed"]), "evidence_sha256": evidence_hash,
             "state_delta_sha256": delta_hash, "candidate_state_hash": candidate, "world_truth": False,
             "automatic_external_effect": False, "instruction_level_simultaneity_claimed": False}
        deterministic = {k: v for k, v in r.items() if not k.endswith("_ns")}
        r["lane_receipt_sha256"] = base.hjson(deterministic)
        outq.put(r)
    except BaseException as exc:
        outq.put({"schema": "janus.bidirectional_pulse_spiral.lane_error.v2_1", "direction": direction,
                  "test_id": test_id, "pair_index": pair_index, "error": f"{type(exc).__name__}:{exc}"})


def run(terminal: Path, aura: Path, demi: Path, home: Path, habitat: Path) -> dict[str, Any]:
    proto, hp = base.read_json(terminal / PROTO)
    thermo_ok, thermo_receipt, thermo_hashes = verify_thermo(terminal, aura, demi, home, habitat)
    if not thermo_ok:
        return {"schema": "janus.bidirectional_pulse_spiral.train.v2_1", "mode": "BIDIRECTIONAL_PULSE_SPIRAL_V2_1",
                "status": "HOLD_THERMODYNAMIC_HARDENING_INCOMPLETE", "thermodynamic_hardening": thermo_receipt,
                "world_truth": False}

    pc, hpc = base.read_json(terminal / "contracts/JANUS_PULSE_SPIRAL_PROTOCOL-v1.0.json")
    pr, hpr = base.read_json(terminal / "receipts/JANUS_PULSE_SPIRAL_LATEST.json")
    sc, hsc = base.read_json(terminal / "contracts/JANUS_SELF_SPIRAL_PROTOCOL-v1.0.json")
    fc, hfc = base.read_json(terminal / "contracts/JANUS_HABITAT_FORK_EXPANSION-v1.0.json")
    fr, hfr = base.read_text(terminal / "tools/janus_habitat_fork_expansion.py")
    ar, har = base.read_text(aura / "tools/aura_5d_spiral_v2.py")
    dr, hdr = base.read_text(demi / "tools/aura_spi_habitat_spiral_bridge_v2_10.py")
    hr, hhr = base.read_text(home / "src/janus_spi/aura_habitat_spiral.py")
    hashes = {"protocol_v2_1": hp, "pulse_contract": hpc, "pulse_receipt": hpr, "self_contract": hsc,
              "fork_contract": hfc, "fork_runtime": hfr, "aura_runtime": har, "demihead_runtime": hdr,
              "home_runtime": hhr, **thermo_hashes}
    tests = base.build_tests(pulse_contract=pc, pulse_receipt=pr, self_contract=sc, fork_contract=fc,
                             fork_runtime=fr, aura_runtime=ar, demi_runtime=dr, home_runtime=hr, hashes=hashes)
    if proto.get("base_pairing") != [list(p) for p in PAIR_QUEUE]:
        raise RuntimeError("PROTOCOL_V2_1_PAIRING_MISMATCH_REVIEW_REQUIRED")
    if os.name != "posix":
        return {"schema": "janus.bidirectional_pulse_spiral.train.v2_1", "mode": "BIDIRECTIONAL_PULSE_SPIRAL_V2_1",
                "status": "HOLD_PROCESS_OVERLAP_WITNESS_REQUIRES_POSIX", "world_truth": False}

    ctx = mp.get_context("fork")
    origin = base.hjson({"kind": "BIDIRECTIONAL_PULSE_ORIGIN_V2_1", "source_hashes": hashes})
    state, seen, pairs = origin, {origin}, []
    status = "BIDIRECTIONAL_PULSE_TRAIN_V2_1_PASS_INTERNAL"

    for i, (fid, rid) in enumerate(PAIR_QUEUE):
        barrier_id = base.hjson({"origin": state, "pair_index": i, "forward": fid, "reverse": rid})[:24]
        launch_ns = time.time_ns()
        start_b, active_b, finish_b = ctx.Barrier(2), ctx.Barrier(2), ctx.Barrier(2)
        outq = ctx.Queue()
        common = (state, i, barrier_id, launch_ns, start_b, active_b, finish_b, outq)
        fp = ctx.Process(target=lane_worker, args=("FORWARD", fid, tests[fid], *common), name=f"janus-forward-{i}")
        rp = ctx.Process(target=lane_worker, args=("REVERSE", rid, tests[rid], *common), name=f"janus-reverse-{i}")
        fp.start(); rp.start()
        vals = []
        try:
            vals = [outq.get(timeout=20), outq.get(timeout=20)]
        except queue.Empty:
            status = "HOLD_DIRECTIONAL_PROCESS_TIMEOUT"
        finally:
            fp.join(timeout=5); rp.join(timeout=5)
            for p in (fp, rp):
                if p.is_alive(): p.terminate(); p.join(timeout=2)
        if status == "HOLD_DIRECTIONAL_PROCESS_TIMEOUT": break
        if any("error" in x for x in vals):
            pairs.append({"schema": "janus.bidirectional_pulse_spiral.pair_receipt.v2_1", "pair_index": i,
                          "parent_state_hash": state, "lane_errors": vals,
                          "join_gate": {"pass": False, "conflict_policy": "HOLD_CONFLICT_NO_PROMOTION"},
                          "world_truth": False})
            status = "HOLD_DIRECTIONAL_PROCESS_ERROR"; break
        lanes = {x["direction"]: x for x in vals}; f, r = lanes["FORWARD"], lanes["REVERSE"]
        same_parent = f["parent_state_hash"] == r["parent_state_hash"] == state
        same_barrier = f["launch_barrier_id"] == r["launch_barrier_id"] == barrier_id
        both_pass = f["pass"] and r["pass"]
        center = fid == rid
        center_consistent = (not center) or f["evidence_sha256"] == r["evidence_sha256"]
        evidence_diverse = center or f["evidence_sha256"] != r["evidence_sha256"]
        overlap_start = max(f["critical_start_ns"], r["critical_start_ns"])
        overlap_end = min(f["critical_end_ns"], r["critical_end_ns"])
        overlap = overlap_start <= overlap_end
        shadows = bool(f.get("candidate_state_hash") and r.get("candidate_state_hash"))
        join = bool(thermo_ok and same_parent and same_barrier and both_pass and center_consistent and evidence_diverse and overlap and shadows)
        md = {"pair_index": i, "parent_state_hash": state, "forward_test_id": fid, "reverse_test_id": rid,
              "forward_lane_receipt_sha256": f["lane_receipt_sha256"], "reverse_lane_receipt_sha256": r["lane_receipt_sha256"],
              "center_pair": center, "evidence_diversity_pass": evidence_diverse,
              "process_level_inflight_overlap": overlap, "directional_shadows_preserved": shadows,
              "thermodynamic_hardening_pass": thermo_ok, "join_pass": join}
        mdh = base.hjson(md)
        candidate = base.hjson({"kind": "BIDIRECTIONAL_MERGED_CANDIDATE_V2_1", "parent_state_hash": state,
                               "state_delta_sha256": mdh, "pair_index": i})
        pair = {"schema": "janus.bidirectional_pulse_spiral.pair_receipt.v2_1", "pair_index": i,
                "parent_state_hash": state, "forward": f, "reverse": r,
                "join_gate": {"same_parent_hash": same_parent, "same_launch_barrier": same_barrier,
                              "both_lanes_pass": both_pass, "center_pair": center,
                              "center_evidence_consistent": center_consistent, "evidence_diversity_pass": evidence_diverse,
                              "evidence_diversity_is_independence_proof": False, "process_level_inflight_overlap": overlap,
                              "overlap_window_ns": max(0, overlap_end-overlap_start),
                              "instruction_level_simultaneity_claimed": False, "directional_shadows_preserved": shadows,
                              "thermodynamic_hardening_pass": thermo_ok, "pass": join,
                              "conflict_policy": "HOLD_CONFLICT_NO_PROMOTION"},
                "shadow_archive": {"forward_candidate_state_hash": f["candidate_state_hash"],
                                   "reverse_candidate_state_hash": r["candidate_state_hash"],
                                   "preserved_even_on_conflict": True, "reactivation_allowed_with_new_evidence": True},
                "merged_state_delta_sha256": mdh, "merged_candidate_state_hash": candidate,
                "return": {"advance_allowed": join, "next_origin_state_hash": candidate if join else state,
                           "return_is_reset": False}, "world_truth": False}
        pair["pair_receipt_sha256"] = base.hjson({k:v for k,v in pair.items() if k != "pair_receipt_sha256"})
        pairs.append(pair)
        if not join: status = "HOLD_CONFLICT_NO_PROMOTION"; break
        if candidate == state: status = "HOLD_STALL_NO_STATE_DELTA"; break
        if candidate in seen: status = "HOLD_REPEAT_STATE_RESONANCE"; break
        seen.add(candidate); state = candidate

    result = {"schema": "janus.bidirectional_pulse_spiral.train.v2_1", "mode": "BIDIRECTIONAL_PULSE_SPIRAL_V2_1",
              "execution_model": "MULTIPROCESS_CONCURRENT_INFLIGHT_FORWARD_AND_REVERSE_WITH_FAIL_CLOSED_JOIN",
              "simultaneity_claim_ceiling": "PROCESS_LEVEL_CONCURRENT_IN_FLIGHT_OVERLAP_NOT_INSTRUCTION_LEVEL_SIMULTANEITY",
              "origin_state_hash": origin, "final_state_hash": state, "pair_pulse_budget": MAX_PAIR_PULSES,
              "pair_pulse_count": len(pairs), "passed_pair_pulses": sum(1 for p in pairs if (p.get("join_gate") or {}).get("pass")),
              "all_pair_pulses_passed": len(pairs)==len(PAIR_QUEUE) and all((p.get("join_gate") or {}).get("pass") for p in pairs),
              "status": status, "thermodynamic_hardening": thermo_receipt, "pair_pulses": pairs,
              "source_hashes": hashes,
              "anti_runaway": {"max_pair_pulses": MAX_PAIR_PULSES, "worker_count_per_pair": 2,
                               "automatic_unbounded_process_spawn": False, "autonomous_unbounded_recursion": False,
                               "automatic_external_effect": False, "first_pair_failure_stops_train": True,
                               "zero_delta_stops_train": True, "repeated_state_stops_train": True},
              "truth_firewall": {"bidirectional_pass_is_world_truth": False,
                                  "thermodynamic_homeostasis_is_world_truth": False,
                                  "evidence_diversity_is_independence_proof": False,
                                  "process_overlap_is_causal_proof": False,
                                  "world_claim_requires_external_validation": True},
              "next_gate": "FRESH_EVIDENCE_OR_EXTERNAL_VALIDATION" if status=="BIDIRECTIONAL_PULSE_TRAIN_V2_1_PASS_INTERNAL" else "REPAIR_FAILED_GATE_AND_RESTART_FROM_NEW_ORIGIN",
              "world_truth": False}
    result["train_receipt_sha256"] = base.hjson(result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="JANUS bidirectional pulse spiral v2.1 hardening runtime")
    ap.add_argument("--terminal", type=Path, default=Path(".")); ap.add_argument("--aura", type=Path, required=True)
    ap.add_argument("--demihead", type=Path, required=True); ap.add_argument("--home", type=Path, required=True)
    ap.add_argument("--habitat", type=Path, required=True)
    ap.add_argument("-o", "--output", type=Path, default=Path("receipts/JANUS_BIDIRECTIONAL_PULSE_SPIRAL_V2_1_LATEST.json"))
    a = ap.parse_args(); result = run(a.terminal.resolve(), a.aura.resolve(), a.demihead.resolve(), a.home.resolve(), a.habitat.resolve())
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    pd = a.output.parent / "bidirectional_pulse_v2_1"; pd.mkdir(parents=True, exist_ok=True)
    for p in result.get("pair_pulses", []):
        i=int(p.get("pair_index",0)); (pd/f"{i:02d}-PAIR_{i:02d}.json").write_text(json.dumps(p, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"status":result.get("status"),"pair_pulse_count":result.get("pair_pulse_count"),"passed_pair_pulses":result.get("passed_pair_pulses"),"all_pair_pulses_passed":result.get("all_pair_pulses_passed"),"final_state_hash":result.get("final_state_hash"),"next_gate":result.get("next_gate")}, ensure_ascii=False))
    return 0 if result.get("status")=="BIDIRECTIONAL_PULSE_TRAIN_V2_1_PASS_INTERNAL" else 2

if __name__ == "__main__": raise SystemExit(main())
