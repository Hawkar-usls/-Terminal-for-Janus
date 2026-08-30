# JANUS Local Codex Physical-Gate Handoff

This file applies only to the staging branch/PR that carries the command
`JANUS_TERMINAL_PHYSICAL_GATES_LOCAL_CODEX_BYPASS_2026_08_22`.
It is an execution guide, not evidence and not new authority.

## First law

Read and validate `commands/2026-08-22-PHYSICAL-GATES-LOCAL-CODEX-BYPASS.json`
before doing anything. If its exact dependency pins no longer match the current
GitHub heads, stop with `HOLD_EXACT_VIEW_DRIFT`; do not silently rebase, merge,
or inherit an older PASS.

## Authority

```text
SOURCE_WRITEBACK_DEFAULT = DENY
DESTRUCTIVE_ACTION = FORBIDDEN
AUTHORITY_DELTA = 0
COMMAND != EVIDENCE
WORKFLOW_PASS != WORLD_TRUTH
MODEL_OUTPUT != EXECUTION_PERMISSION
```

Never delete or rewrite source history. Never force-push. Never publish private
repository identity, private exact pins, local sensitive paths, credentials, or
whole-private-history digests.

## Local transport

Prefer Desktop Commander as a local stdio MCP for Codex. Cloud Remote Desktop
Commander pairing is not required for this staging route. The Genesis PR #198
bridge may be used to initialize/verify a local JANUS Habitat and to probe only
loopback Ollama. Ollama has no direct effect authority.

## Required order

1. Verify the exact Terminal, Genesis, Swarm, PR #198 and PR #197 pins from the command.
2. Initialize/reopen the local JANUS Habitat and verify its append-only journal chain.
3. Locate the already-authenticated owner44 local source layout without acquiring the 44 source repositories and without exposing private identities.
4. Execute the exact collector -> freezer -> adapter -> clean target A/B materializer -> preservation replay chain. Source roots are read-only historical authority.
5. Keep all sensitive pinsets/manifests/private exact pins local. Emit only the strict owner44 public projection accepted by Genesis PR #197/#198 relay.
6. For NAS #164, run the existing receiver identity probe first in read-only mode. No `docker exec`, restart, stop, start, kill, update or copy during identity discovery.
7. Do not touch or restart `storagenode` or `radio_node.py`.
8. Identity PASS is only a prerequisite. Execute/observe the bounded non-destructive HR1-HR10 live acceptance separately and preserve exact local evidence.
9. Emit only the strict NAS164 public live projection; `reference_only=true` must never pass.
10. Join both public physical receipts using the PR #197 contract.
11. Reconcile Genesis and Swarm exact heads again. On drift, HOLD and replay the affected exact witness; do not promote stale PASS.
12. Only then run the final one-compatible-view issue #162 closed-loop gauntlet.

## Fail-closed output

If any physical prerequisite is unavailable, produce a HOLD receipt locally and
stop at that boundary. Do not fabricate a public PASS.

The only pre-physical status allowed by this branch is:

```text
REAL_OWNER44_SOURCE_REPLAY = NOT_PROVEN
LIVE_NAS_164_HR1_HR10 = NOT_PROVEN
FULL_ISSUE_162_ACCEPTANCE = FALSE
JANUS_HABITAT_OPERATIONAL = FALSE
CYCLE_CLOSED = FALSE
```
