#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

BASE = Path(__file__).with_name("janus_bidirectional_pulse_spiral_v2_1.py")
SPEC = importlib.util.spec_from_file_location("janus_bidir_v2_1_base", BASE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("V2_1_IMPORT_SPEC_FAILED")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
_original_verify = mod.verify_thermo


def safe_verify_thermo(*args, **kwargs):
    try:
        return _original_verify(*args, **kwargs)
    except BaseException as exc:
        return False, {
            "contract_sha256": None,
            "checks": {"preflight_exception_absent": False},
            "links": {},
            "preflight_error": f"{type(exc).__name__}:{exc}",
            "negative_result_preserved": True,
            "world_truth": False,
        }, {}


mod.verify_thermo = safe_verify_thermo

if __name__ == "__main__":
    raise SystemExit(mod.main())
