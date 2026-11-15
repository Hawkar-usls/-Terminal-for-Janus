# JANUS dialogue learning · verification before training

The canonical public conversational source remains
[`-Terminal-for-Janus`](https://github.com/Hawkar-usls/-Terminal-for-Janus).
This stage builds a **durable evidence archive**, not an autonomous self-training permission.

## Evidence chain

```
Human GitHub issue/comment (owner authenticated by GitHub)
   ↓
JANUS Open LLM CPU Chat (run_id / head SHA / model identities)
   ↓
Artifact ZIP: dialogue.json + request SHA + dialogue SHA
   ↓
GitHub bot issue comment carrying the exact same dialogue SHA
   ↓
Independent corpus workflow (no model inference or generated code execution)
   ↓
janus/open-llm-corpus: records/<run-id>-<dialogue-sha256>.json
   ↓
CORPUS_GATE.json (always HOLD without independent prospective custodian)
```

The corpus workflow runs when `JANUS Open LLM CPU Chat` completes, can be launched manually, and has a daily catch-up because GitHub event/schedule delivery is not guaranteed. It reads up to 80 recent successful runs per catch-up; retains only those with the expected small artifact and no bad provenance. Each record is create-only and tamper-detected by SHA-256. The branch is **data only**, not `main` and not model checkpoints.

The snapshot counts verified **origin**, not accuracy. It rejects malformed ZIPs, changed JSON, unexpected model IDs, run/issue actor mismatch, missing matching bot response, or a result claiming to have changed neural weights. Historical artifacts have limited retention (14 days); after expiry they cannot be reconstructed from comments without losing some intermediate model turns, so the routine must run early. The audit records unverified/invalid runs as HOLD.

## Initial negative and unproven cases

- [Qwen 0.5B #39](https://github.com/Hawkar-usls/-Terminal-for-Janus/issues/39): **REJECT_FACTUAL_ERROR**. It incorrectly attributed JANUS to Anthropic.
- [Qwen ↔ SmolLM #40](https://github.com/Hawkar-usls/-Terminal-for-Janus/issues/40): **HOLD_UNVERIFIED**. The peer reiterated an answer but did not independently check it.
- [Qwen 1.5B follow-up #40](https://github.com/Hawkar-usls/-Terminal-for-Janus/issues/40#issuecomment-6897593903): **REJECT_TRUNCATED**. An earlier generation exhausted its token allowance.

Signed/canonical receipts and review dispositions are indexed in `config/JANUS_DIALOGUE_REVIEW_LABELS.json`. Unknown dialogues are held, never silently admitted. A positive training label requires two separate human review references and independent evidence. Those references are not by themselves external validation: an external custodian must be verified separately.

## Five executable gates

| Gate | Admission criteria | Now |
|---|---|---|
| G1 archive | Original artifact SHA + request SHA, owner-authored GitHub stimulus, run metadata, bot SHA comment | Collector implementation, execution evidence required |
| G2 labels | Factual checks, no corrupted/truncated content, independent source-based labels and de-duplication | HOLD — no approved examples |
| G3 shadow training | At least 32 admissible unique examples from at least 8 separate issues including peer review; training code and checkpoints in isolated experimental artifact | HOLD |
| G4 blind examination | Custodian seals new unseen tasks **before** observing descendant outputs; parent/child paired with identical compute and full training cost; unchanged test set and independent source | HOLD |
| G5 admission and rollback | Prospective gains replicated, security gates, actual isolated service switch/rollback, explicit owner approval | HOLD |

No AI-to-AI conversation, model preference score, internal CI success, or matching response from peers can replace external ground truth. Corpus/weights never grant permissions to Sentinel A/B/C.

## Next step: shadow descendant, separate from existing JANUS

Choose a trainable **experimental** adapter with identical parent/child evaluation protocol. Freeze base weights and training data hashes. Train only on approved labels. Save adapter tensors, parent SHA, optimizer/seed, elapsed time and compute budget to a separate artifacts namespace. Do not upload those tensors into native `janus_model` nor have a workflow read and promote them automatically.

Only after training is actually executed and a held-out, prospective paired test shows improvement may it be called a candidate descendant. The first trial cannot prove production advantage or external scientific replication. A genuinely independently replicated improvement requires a custodian who was not involved in training/evaluation design.

## Operational boundaries

- The workflow uses only its own repository token; scoped to `contents:write`, `issues:read` and `actions:read` on the **Terminal** repository.
- It makes **no cross-repository dispatch**, no deployment, no GitHub issue action, no native checkpoint modification and no service replacement.
- `janus/open-llm-corpus` contains public conversation text: do not submit secrets or private records to Terminal.
- The current `CORPUS_GATE.json` is a data-readiness signal. It is never authority to change other repositories. External review and the closed benchmark remain separate.

Evidence page: <https://github.com/Hawkar-usls/-Terminal-for-Janus/actions/workflows/janus-dialogue-corpus.yml>.
