#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

RUNTIME = Path(__file__).with_name("janus_bidirectional_pulse_spiral_v2_1_1.py")
SPEC = importlib.util.spec_from_file_location("janus_v2_1_1_adversarial_target", RUNTIME)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("ADVERSARIAL_IMPORT_FAILED")
wrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wrap)
rt = wrap.mod


def mutate_contract(terminal: Path, mutator):
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "contracts").mkdir(parents=True)
    src = terminal / rt.THERMO
    value = json.loads(src.read_text(encoding="utf-8"))
    mutator(value)
    (root / rt.THERMO).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return td, root


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--terminal",type=Path,default=Path(".")); ap.add_argument("--aura",type=Path,required=True)
    ap.add_argument("--demihead",type=Path,required=True); ap.add_argument("--home",type=Path,required=True)
    ap.add_argument("--habitat",type=Path,required=True); ap.add_argument("-o","--output",type=Path,required=True)
    a=ap.parse_args(); t=a.terminal.resolve(); aura=a.aura.resolve(); demi=a.demihead.resolve(); home=a.home.resolve(); hab=a.habitat.resolve()
    results=[]

    td, fake = mutate_contract(t, lambda x: x["source_ingestion"].update({"destroy_original_after_ingest": True}))
    ok, rec, _ = wrap.safe_verify_thermo(fake, aura, demi, home, hab); td.cleanup()
    results.append({"test":"SOURCE_DESTRUCTION_REJECT","passed": (not ok and rec.get("world_truth") is False), "observed": rec})

    td, fake = mutate_contract(t, lambda x: x["entropy_graveyard_and_dreams"].update({"dream_output_may_train_predictive_head": True}))
    ok, rec, _ = wrap.safe_verify_thermo(fake, aura, demi, home, hab); td.cleanup()
    results.append({"test":"DREAM_TRAINING_REJECT","passed": (not ok and rec.get("world_truth") is False), "observed": rec})

    td, fake = mutate_contract(t, lambda x: x["ouroboros_integrity"].update({"hash_mismatch_may_autonomously_mutate_code": True}))
    ok, rec, _ = wrap.safe_verify_thermo(fake, aura, demi, home, hab); td.cleanup()
    results.append({"test":"OUROBOROS_AUTO_MUTATION_REJECT","passed": (not ok and rec.get("world_truth") is False), "observed": rec})

    with tempfile.TemporaryDirectory() as d:
        missing_aura=Path(d)/"aura"; missing_aura.mkdir(parents=True)
        ok, rec, _ = wrap.safe_verify_thermo(t, missing_aura, demi, home, hab)
        results.append({"test":"MISSING_LINK_STRUCTURED_HOLD","passed": (not ok and rec.get("negative_result_preserved") is True and bool(rec.get("preflight_error"))), "observed": rec})

    original_build = rt.base.build_tests
    def correlated_build(**kwargs):
        tests=original_build(**kwargs)
        tests=copy.deepcopy(tests)
        tests["TRUTH_FIREWALL"]["evidence"] = copy.deepcopy(tests["BASELINE"]["evidence"])
        return tests
    rt.base.build_tests = correlated_build
    try:
        rr=rt.run(t,aura,demi,home,hab)
    finally:
        rt.base.build_tests = original_build
    p0=(rr.get("pair_pulses") or [{}])[0]
    gate=p0.get("join_gate") or {}
    results.append({"test":"CORRELATED_EVIDENCE_REJECT","passed": (rr.get("status")=="HOLD_CONFLICT_NO_PROMOTION" and gate.get("evidence_diversity_pass") is False and gate.get("pass") is False), "observed":{"status":rr.get("status"),"join_gate":gate}})

    passed=all(x["passed"] for x in results)
    out={"schema":"janus.bidirectional_v2_1.adversarial_negative_suite.v1","status":"PASS_EXPECTED_NEGATIVES" if passed else "REJECT_NEGATIVE_SUITE","tests":results,"all_expected_negatives_passed":passed,"world_truth":False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"tests":len(results)},ensure_ascii=False))
    return 0 if passed else 2

if __name__=="__main__": raise SystemExit(main())
