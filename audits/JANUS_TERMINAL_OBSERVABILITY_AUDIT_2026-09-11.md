# JANUS Terminal observability audit — 2026-09-11

Scope: `index.html`, Terminal v2 browser runtime, Brain Observatory, Neural Link v2, Synthesis view, Terminal v2 CI/static tests, and the live Janus-Demiurge model state/training receipt consumed by the UI. This audit does **not** claim a physical NAS/device audit.

## Truth invariants

- `ACTIVE CHECKPOINT != LAST CANDIDATE`.
- Adaptive eval loss is meaningful only inside its current source/corpus context.
- Frozen anchor loss is the cross-epoch comparator.
- A bounded history window is not the lifetime attempt ledger.
- UI availability or absence is not scientific evidence.
- Model output or selection is not a verified fix.

## Fixed in this change

1. **Ambiguous top-bar score — HIGH.** `BRAIN 53/126 · L 0.768` looked like one lifetime intelligence score. The truth layer now renders `P<pm>/A<attempts> · ADAPT <current> · ANCHOR <frozen>` and explains both metrics.
2. **False state-integrity warning — HIGH.** The model state retains a bounded recent history window while `attempt_count` is lifetime. Equality between those values therefore produced a false warning. Integrity now requires `history.length <= attempt_count`, while lifetime promotion/rejection accounting remains exact.
3. **Cross-epoch chart implication — HIGH.** The adaptive graph visually connected values from different `source_digest` epochs. The truth layer breaks the active line when the source digest changes and names the frozen anchor as the cross-epoch comparator.
4. **Wrong chart attempt numbering — MEDIUM.** A 64-row retained history was labelled as attempts `1..64` even when lifetime attempts were greater. The chart now calculates the visible window from lifetime `attempt_count` and says `shown / lifetime` explicitly.
5. **Frozen anchor invisible — HIGH.** The current and candidate anchor values, anchor digest, adaptive source digest, and evaluation-contract digest are now visible in Brain Monitor/compact readouts.
6. **Stale telemetry styling — LOW.** If tensor telemetry disappears after previously being live, `CHECKPOINT DIGEST ONLY` now clears the stale live class.
7. **Fail-visible brain truth fetch — MEDIUM.** If the authoritative model-state fetch fails, the truth pill becomes `BRAIN UNRESOLVED` instead of silently leaving a fresh-looking score.

## Live state verified during audit

At audit time the active checkpoint remained `00097377871cdd9111c01cdf07d7f8dd0d8d2a9c968f3d8cded7e7ac1a4a0d74`. Lifetime state was 126 attempts, 53 promotions, 73 rejections. The latest run `34540803530` rejected candidate adaptive loss `0.8158998340` against incumbent `0.7678602785`; frozen-anchor values were candidate `1.8205470840` vs incumbent `1.8127593795`. The rejected candidate did not replace the active checkpoint.

## Follow-up work found by the audit

### P1 — fold the compatibility truth layer into the core observatory

`assets/brain-truth-v2.js` intentionally corrects the current display without rewriting the established observatory/verifier in the same change. After this patch has live replay evidence, fold these semantics into `assets/janus-observatory.js` and retire duplicate calculation paths. One authoritative renderer is preferable long-term.

### P1 — decouple Terminal refresh lanes

`assets/terminal-v2.js` currently refreshes persistent identity, latest conversation, and TRUMP candidate state through one `Promise.all`. A transient conversation/API failure can therefore make the overall Terminal surface look unresolved even when resident identity is healthy. Fetch/render identity, conversation, and candidate tissue as independent fail-closed lanes.

### P1 — unify view routing

Core Terminal navigation and the dynamically installed Synthesis view have separate routing implementations and slightly different accessibility/event semantics. Move all views behind one canonical `JANUS_TERMINAL_NAVIGATE` router with consistent `aria-selected`, `aria-hidden`, focus, and `janus:view-changed` behavior.

### P1 — decide the upstream model-promotion law explicitly

Janus-Demiurge currently allows bounded regression tolerance in its dual evaluation gate (adaptive and frozen anchor tolerances). That is not a Terminal bug, but it is weaker than a strict `never worse on either frozen comparator` interpretation. Treat this as a separate model-governance change: either retain documented tolerances, or adopt a Pareto/no-regression promotion rule and test it explicitly. Do not call either policy a universal intelligence proof.

### P2 — make observatory auxiliary reads independently resilient

The legacy core Brain Observatory still treats the model manifest as mandatory even though the authoritative model state can remain available. Make architecture/telemetry/module/decision reads auxiliary so a missing non-authoritative panel cannot blank the core checkpoint readout.

### P2 — preserve a dedicated lifetime evaluation ledger

`JANUS_MODEL_STATE.json` intentionally keeps only a bounded recent history window. If the UI should support a true lifetime graph, publish an append-only compact evaluation ledger rather than inferring lifetime history from the bounded state file.

### P2 — refresh project metadata

`PROJECT_STATUS.json` still carries an older `last_reviewed` date and predates the current Brain Monitor / Neural Link v2 / Synthesis observability surfaces. Refresh it after the UI patch is sealed so project metadata does not lag the executable interface.

### P3 — browser provenance for fetched readouts

The browser shows source/checkpoint digests from persisted data, but the page could additionally expose fetch timestamp, resolved raw path, and response identity/ETag where available. This would make stale-cache/network diagnosis easier without granting any new authority.

## CI contract added

The Terminal v2 workflow now syntax-checks `assets/brain-truth-v2.js` and runs a dedicated static test that locks: adaptive-vs-anchor terminology, bounded-history semantics, true attempt-window numbering, cross-source line breaks, fail-visible unresolved state, and telemetry live-class cleanup.

## Claim ceiling

This audit improves observability correctness and operator interpretation. It does not prove general intelligence, production readiness, scientific truth, or physical-device runtime correctness.
