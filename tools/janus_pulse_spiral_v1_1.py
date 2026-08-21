#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).with_name("janus_pulse_spiral.py")
source = BASE.read_text(encoding="utf-8")
old = '''    aura_ok = all_terms(aura_runtime,["origin_prime_candidate","parent_origin_state_hash","state_delta_sha256","candidate_state_hash","final_promotion_authority"]) and "ADVANCED_TO_ORIGIN_PRIME_CANDIDATE" in aura_runtime
'''
new = '''    aura_ok = all_terms(aura_runtime,["origin_prime_candidate","parent_origin_state_hash","state_delta_sha256","candidate_state_hash","final_origin_prime_authority"]) and "CANDIDATE_STATE_ADVANCE" in aura_runtime
'''
if old not in source:
    raise RuntimeError("PULSE_RUNTIME_BASE_PATTERN_CHANGED_REVIEW_REQUIRED")
source = source.replace(old, new, 1)
namespace = {"__name__": "janus_pulse_spiral_v1_1", "__file__": str(BASE)}
exec(compile(source, str(BASE), "exec"), namespace)

if __name__ == "__main__":
    raise SystemExit(namespace["main"]())
