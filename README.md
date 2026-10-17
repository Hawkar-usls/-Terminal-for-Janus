<div align="center">

# Terminal for Janus
### Human-authorized operator control plane for the JANUS constellation

![Status](https://img.shields.io/badge/status-active%20prototype-2ea043)
![Role](https://img.shields.io/badge/role-operator%20control%20plane-8250df)

`HAWKAR → TERMINAL COMMAND → TARGET → GATE → EXECUTOR → RECEIPT → HABITAT`

</div>

## Role

Terminal is the operator-facing entry point for JANUS repository orchestration. It is intended to coordinate reads, human-authorized writes, tests, workflow launches, deployment requests, Habitat handoffs and cross-repository receipts.

It is **not** a truth authority and it does not turn interface access into autonomous control.

```text
TERMINAL_ACCESS != TRUTH_AUTHORITY
COMMAND != EVIDENCE
WRITE != VERIFIED_RETURN
WORKFLOW_PASS != WORLD_TRUTH
HUMAN_AUTHORIZED_WRITE != UNBOUNDED_AUTONOMY
```

## Connected constellation

The machine-readable map is [`config/JANUS_CONSTELLATION.json`](config/JANUS_CONSTELLATION.json).

The **public ecosystem observer** is intentionally separate from that executable
constellation. It checks the full public repository list, accounts for upstream
working copies, and tracks proposed read-only integrations without auto-enrolling
new projects in the live scanner. This matters because membership in
`JANUS_CONSTELLATION.json` causes scheduled cross-repository clone/audit work.

- Candidate contracts: [`config/JANUS_ECOSYSTEM_OBSERVER.json`](config/JANUS_ECOSYSTEM_OBSERVER.json)
- Read-only observer: [`tools/janus_ecosystem_observer.py`](tools/janus_ecosystem_observer.py)
- Weekly/manual workflow: [`.github/workflows/janus-ecosystem-observer.yml`](.github/workflows/janus-ecosystem-observer.yml)
- Persistent receipt: branch `janus/ecosystem-observations`, file
  `receipts/JANUS_ECOSYSTEM_OBSERVATION_LATEST.json`

The observation carries a SHA-256 integrity digest and a monotonic predecessor
link. A missing API response or tampered previous receipt fails closed and does
not overwrite the last good state. The workflow reads only public repository
metadata and writes only its own receipt branch. A discovered repository is not
thereby running, authorized, tested, trustworthy, or scientific evidence.

Run locally (public GitHub API required):

```bash
python tools/janus_ecosystem_observer.py --live --output /tmp/janus-ecosystem-observation.json
python tools/janus_ecosystem_observer.py --verify /tmp/janus-ecosystem-observation.json
```

Primary control path:

```text
Terminal
  ├─ JANUS-SPI / Hawkar-usls
  ├─ Habitat / Janus_Genesis@janus/habitat
  ├─ DemiHead arbiter
  ├─ Aura Oracle reflection peer
  ├─ HRain / iNaiHR
  ├─ Janus-Fundamentum / AIFC
  ├─ Janus-Cosmos / janus-io-public
  ├─ Swarm / Fast-CAT-SHAiTan
  ├─ SCOBY-D0 / janus-lapis
  └─ janus-meta-registry
```

## Command model

A Terminal-managed operation should leave a machine-readable command receipt under `commands/`.

Each command records:

- who requested it;
- target repositories;
- intended operation;
- authority mode;
- expected outputs;
- forbidden promotions;
- resulting workflow/commit/receipt evidence.

Default authority is `READ_ONLY`. Writes require explicit human authorization.

Canonical control-plane contract:
[`contracts/JANUS_TERMINAL_CONTROL_PLANE-v1.0.json`](contracts/JANUS_TERMINAL_CONTROL_PLANE-v1.0.json)

## First bound operation

The first Terminal-managed integration is:

**Aura Oracle ↔ JANUS Semantic-Predictive Intelligence ↔ DemiHead ↔ Habitat**

Command receipt:
[`commands/2026-08-21-FIRST_LIVE_SPIRAL.json`](commands/2026-08-21-FIRST_LIVE_SPIRAL.json)

Workflow:
[`.github/workflows/janus-terminal-first-live-spiral.yml`](.github/workflows/janus-terminal-first-live-spiral.yml)

The first reference run is deliberately fail-closed: `DemiHead = HOLD`, Aura cannot become a predictive label, and a workflow success cannot become `VERIFIED_RETURN` or scientific truth.

## Executors

Terminal may be used with multiple execution surfaces:

- connected ChatGPT GitHub executor;
- GitHub Actions;
- optional local `gh`/git tooling;
- optional NAS/PC runtime after a real persistent executor is connected.

Credentials must never be committed into this repository.

## Habitat

The original `.janus/HABITAT_LINK.json` remains authoritative for the repository-to-Habitat safety boundary: repository source history stays authoritative, write-back is denied by default, and explicit human authorization is required for writes.

## Status

This is an **active prototype**, not a production-grade remote-administration system. Persistent NAS execution and production security hardening remain separate gates.

→ [`PROJECT_STATUS.json`](PROJECT_STATUS.json)

---

<div align="center">

**Hawkar / JANUS**

</div>
