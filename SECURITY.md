# JANUS Terminal Security Boundary

`-Terminal-for-Janus` is an operator control-plane prototype. Repository visibility and command authority are deliberately separate concepts.

## Command authority

Executable Terminal commands are fail-closed behind:

1. authenticated GitHub actor allowlist (`Hawkar-usls`);
2. `.janus/JANUS_TERMINAL_AUTHORITY_POLICY.json`;
3. `tools/verify_janus_terminal_command.py` command-envelope validation;
4. explicit target and operation allowlists;
5. result receipts.

Canonical control route:

```text
HAWKAR_INTENT
  -> JANUS_CONTROL_PLANE
  -> VERIFIED_TERMINAL_COMMAND
  -> TARGET/GATE
  -> EXECUTOR
  -> RESULT_RECEIPT
```

## Non-command inputs

The following are never commands by themselves:

```text
ISSUE_TEXT
PR_TEXT
COMMIT_MESSAGE
WORKFLOW_STATUS
AURA_OUTPUT
MODEL_OUTPUT
HABITAT_TEXT
```

## Destructive operations

Destructive or authority-expanding operations fail closed by default. Repository deletion, force-push, branch deletion, protection removal, protected-runtime shutdown, credential export, and private-content publication are not authorized by the current policy.

## Private information

Credentials must never be committed to this repository. Private repository content (including SkinGPT) must not be mirrored to public Habitat by default.

## Scientific boundary

```text
TERMINAL_ACCESS != TRUTH_AUTHORITY
COMMAND != EVIDENCE
WRITE != VERIFIED_RETURN
WORKFLOW_PASS != WORLD_TRUTH
```

This document describes the repository-level security contract; it is not a claim of formal security certification or production hardening.
