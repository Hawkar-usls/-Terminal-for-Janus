#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PHASES = ["INTAKE","COMPRESSION","IGNITION","EXPANSION","EXHAUST","RETURN"]
MAX_PULSES = 8

def hbytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hjson(value: Any) -> str:
    return hbytes(json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode("utf-8"))

def read_text(path: Path):
    raw = path.read_bytes()
    return raw.decode("utf-8-sig"), hbytes(raw)

def read_json(path: Path):
    text, digest = read_text(path)
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON_OBJECT_REQUIRED")
    return value, digest

def all_terms(text: str, terms: list[str]) -> bool:
    return all(t in text for t in terms)

def pulse(index: int, test_id: str, purpose: str, parent: str, evidence: dict, passed: bool, expected: str, observed: str):
    evidence_hash = hjson(evidence)
    delta = {"test_id": test_id, "verdict": "PASS" if passed else "FAIL", "evidence_sha256": evidence_hash}
    delta_hash = hjson(delta)
    candidate = hjson({"parent_state_hash": parent, "pulse_index": index, "state_delta_sha256": delta_hash, "test_id": test_id})
    out = {
        "schema": "janus.pulse_spiral.pulse_receipt.v1",
        "pulse_index": index,
        "pulse_id": f"PULSE_{index:02d}_{test_id}",
        "phases": PHASES,
        "INTAKE": {"parent_state_hash": parent, "fresh_pulse_id": True},
        "COMPRESSION": {"test_id": test_id, "purpose": purpose, "evidence_sha256": evidence_hash},
        "IGNITION": {"bounded_test_executed": True, "expected": expected, "observed": observed, "pass": passed, "world_truth": False},
        "EXPANSION": {"state_delta": delta, "state_delta_sha256": delta_hash, "candidate_state_hash": candidate, "candidate_is_origin_prime": False},
        "EXHAUST": {"status": "PULSE_PASS" if passed else "PULSE_REJECT", "receipt_is_world_truth": False, "automatic_external_effect": False},
        "RETURN": {"next_origin_state_hash": candidate if passed else parent, "advance_allowed": passed, "return_is_reset": False},
    }
    out["pulse_receipt_sha256"] = hjson(out)
    return out

def run(terminal: Path, aura: Path, demihead: Path, home: Path):
    self_contract, hs = read_json(terminal / "contracts/JANUS_SELF_SPIRAL_PROTOCOL-v1.0.json")
    pulse_contract, hp = read_json(terminal / "contracts/JANUS_PULSE_SPIRAL_PROTOCOL-v1.0.json")
    self_receipt, hr = read_json(terminal / "receipts/JANUS_SELF_SPIRAL_LATEST.json")
    fork_contract, hfc = read_json(terminal / "contracts/JANUS_HABITAT_FORK_EXPANSION-v1.0.json")
    fork_runtime, hfr = read_text(terminal / "tools/janus_habitat_fork_expansion.py")
    aura_runtime, ha = read_text(aura / "tools/aura_5d_spiral_v2.py")
    demi_runtime, hd = read_text(demihead / "tools/aura_spi_habitat_spiral_bridge_v2_10.py")
    home_runtime, hh = read_text(home / "src/janus_spi/aura_habitat_spiral.py")

    source_hashes = {
        "self_contract": hs, "pulse_contract": hp, "self_receipt": hr,
        "fork_contract": hfc, "fork_runtime": hfr,
        "aura_runtime": ha, "demihead_runtime": hd, "home_runtime": hh,
    }

    tests = []
    baseline_ok = self_receipt.get("status") == "SELF_CONSISTENCY_PASS" and self_receipt.get("self_consistency_gate",{}).get("high_or_critical_defects") == 0 and self_receipt.get("world_truth") is False
    tests.append(("BASELINE","Start only from fail-closed self-consistency.",{"status":self_receipt.get("status"),"gate":self_receipt.get("self_consistency_gate")},baseline_ok,"SELF_CONSISTENCY_PASS + 0 hard defects + world_truth=false",str(self_receipt.get("status"))))

    zero_ok = "ZERO_STATE_DELTA -> HOLD_STALL_NO_PROMOTION" in self_contract.get("self_reference_laws",[]) and self_receipt.get("D4_ASSOCIATIVE_COUNTERMODEL",{}).get("required_result") == "HOLD_STALL_NO_PROMOTION" and self_receipt.get("self_consistency_gate",{}).get("zero_delta_must_hold") is True
    tests.append(("ZERO_DELTA","No delta must exhaust into HOLD.",{"law":self_contract.get("self_reference_laws",[]),"countermodel":self_receipt.get("D4_ASSOCIATIVE_COUNTERMODEL")},zero_ok,"ZERO_DELTA => HOLD_STALL_NO_PROMOTION","gate present" if zero_ok else "gate missing"))

    aura_ok = all_terms(aura_runtime,["origin_prime_candidate","parent_origin_state_hash","state_delta_sha256","candidate_state_hash","final_promotion_authority"]) and "ADVANCED_TO_ORIGIN_PRIME_CANDIDATE" in aura_runtime
    tests.append(("AURA_CANDIDATE","Aura may create a candidate but not final promotion.",{"aura_sha256":ha},aura_ok,"candidate-only + parent/delta/hash binding","firewall present" if aura_ok else "firewall incomplete"))

    demi_ok = all_terms(demi_runtime,["candidate_state_hash","origin_state_hash","state_delta_sha256","parent_origin_state_hash","candidate_valid","verified_return_eligible"])
    tests.append(("DEMIHEAD_BINDING","DemiHead must bind nonzero candidate to exact parent.",{"demihead_sha256":hd},demi_ok,"candidate/hash/parent/delta gate","binding present" if demi_ok else "binding missing"))

    home_ok = all_terms(home_runtime,["demihead_arbitration_receipt","arbitration_sha256","DEMIHEAD_ARBITRATION_HASH_MISMATCH","candidate_valid","NO_DEMIHEAD_ARBITRATION_RECEIPT_FAIL_CLOSED"])
    tests.append(("HOME_RECEIPT","Bare PASS cannot sustain next pulse.",{"home_sha256":hh},home_ok,"real hash-valid receipt required","receipt firewall present" if home_ok else "receipt firewall incomplete"))

    fork_ok = fork_contract.get("fork_habitat_install",{}).get("automatic_upstream_pr") is False and fork_contract.get("fork_habitat_install",{}).get("automatic_upstream_issue") is False and fork_contract.get("budgets",{}).get("mass_upstream_effect_budget") == 0 and all_terms(fork_runtime,['"upstream_writeback_authorized": False','"automatic_upstream_pr": False','"mass_upstream_effect_budget": 0'])
    tests.append(("FORK_FIREWALL","Pulse propagation to fork satellites must not become upstream propagation.",{"fork_contract_sha256":hfc,"fork_runtime_sha256":hfr},fork_ok,"upstream authority=0","firewall present" if fork_ok else "firewall incomplete"))

    truth_ok = "SELF_CONSISTENCY_PASS != WORLD_TRUTH" in self_contract.get("self_reference_laws",[]) and self_receipt.get("world_truth") is False and self_receipt.get("self_consistency_is_world_truth") is False and pulse_contract.get("truth_firewall",{}).get("pulse_train_pass_is_world_truth") is False
    tests.append(("TRUTH_FIREWALL","Repeated pulse success cannot manufacture world truth.",{"pulse_truth_firewall":pulse_contract.get("truth_firewall"),"self_world_truth":self_receipt.get("world_truth")},truth_ok,"PULSE_TRAIN_PASS != WORLD_TRUTH","firewall present" if truth_ok else "firewall incomplete"))

    if len(tests) > MAX_PULSES:
        raise RuntimeError("PULSE_BUDGET_EXCEEDED")

    origin = hjson({"kind":"PULSE_SPIRAL_ORIGIN","source_hashes":source_hashes,"baseline_receipt_sha256":hr})
    state = origin
    seen = {origin}
    receipts = []
    status = "PULSE_TRAIN_PASS_INTERNAL"

    for i,(tid,purpose,evidence,passed,expected,observed) in enumerate(tests):
        pr = pulse(i,tid,purpose,state,evidence,passed,expected,observed)
        nxt = pr["RETURN"]["next_origin_state_hash"]
        if passed and nxt == state:
            pr["EXHAUST"]["status"] = "HOLD_STALL_NO_STATE_DELTA"
            pr["RETURN"]["advance_allowed"] = False
            receipts.append(pr)
            status = "HOLD_STALL_NO_STATE_DELTA"
            break
        if nxt in seen and nxt != state:
            pr["EXHAUST"]["status"] = "HOLD_REPEAT_STATE_RESONANCE"
            pr["RETURN"]["advance_allowed"] = False
            receipts.append(pr)
            status = "HOLD_REPEAT_STATE_RESONANCE"
            break
        receipts.append(pr)
        if not passed:
            status = "PULSE_TRAIN_REJECT"
            break
        seen.add(nxt)
        state = nxt

    result = {
        "schema":"janus.pulse_spiral.train.v1",
        "mode":"PULSE_SPIRAL",
        "analogy":"pulsejet-inspired discrete reasoning pulses; software control metaphor only",
        "phases":PHASES,
        "origin_state_hash":origin,
        "final_state_hash":state,
        "pulse_budget":MAX_PULSES,
        "pulse_count":len(receipts),
        "passed_pulses":sum(1 for p in receipts if p["IGNITION"]["pass"]),
        "all_declared_pulses_passed":len(receipts)==len(tests) and all(p["IGNITION"]["pass"] for p in receipts),
        "status":status,
        "pulses":receipts,
        "source_hashes":source_hashes,
        "anti_runaway":{"bounded_test_queue":True,"max_pulses":MAX_PULSES,"fresh_pulse_id_required":True,"zero_delta_stops_train":True,"repeated_state_hash_stops_train":True,"first_failed_pulse_stops_train":True,"autonomous_unbounded_recursion":False,"automatic_external_effect":False},
        "truth_firewall":{"pulse_train_pass_is_world_truth":False,"repetition_is_external_validation":False,"world_claim_requires_external_validation":True},
        "next_gate":"EXTERNAL_VALIDATION_OR_FRESH_EVIDENCE_REQUIRED" if status=="PULSE_TRAIN_PASS_INTERNAL" else "REPAIR_FAILED_PULSE_THEN_RESTART_FROM_NEW_ORIGIN",
        "world_truth":False,
    }
    result["train_receipt_sha256"] = hjson(result)
    return result

def main():
    ap = argparse.ArgumentParser(description="JANUS bounded pulse spiral")
    ap.add_argument("--terminal",type=Path,default=Path("."))
    ap.add_argument("--aura",type=Path,required=True)
    ap.add_argument("--demihead",type=Path,required=True)
    ap.add_argument("--home",type=Path,required=True)
    ap.add_argument("-o","--output",type=Path,default=Path("receipts/JANUS_PULSE_SPIRAL_LATEST.json"))
    args = ap.parse_args()
    result = run(args.terminal.resolve(),args.aura.resolve(),args.demihead.resolve(),args.home.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    pulse_dir = args.output.parent / "pulse"
    pulse_dir.mkdir(parents=True,exist_ok=True)
    for p in result["pulses"]:
        (pulse_dir / f"{p['pulse_index']:02d}-{p['pulse_id']}.json").write_text(json.dumps(p,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"pulse_count":result["pulse_count"],"passed_pulses":result["passed_pulses"],"final_state_hash":result["final_state_hash"],"next_gate":result["next_gate"]},ensure_ascii=False))
    return 0 if result["status"]=="PULSE_TRAIN_PASS_INTERNAL" else 2

if __name__ == "__main__":
    raise SystemExit(main())
