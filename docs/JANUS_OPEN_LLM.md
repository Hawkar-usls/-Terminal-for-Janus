# JANUS Open LLM · GitHub Actions CPU text dialogue

## Purpose and actual identity

A separate **CPU inference adapter**, not a replacement for JANUS native weights and not a claim of verified autonomous cognition. It augments the existing Terminal Git-native conversation plane. The legacy ingress/egress, HRAiN proof, and native model remain unchanged.

| Role | Model | Source | License |
|---|---|---|---|
| JANUS text adapter | `Qwen/Qwen2.5-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | Apache-2.0 |
| Peer critic (opt-in) | `HuggingFaceTB/SmolLM2-360M-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct | Apache-2.0 |
| Clawdbot reference | `Hawkar-usls/clawdbot` | https://github.com/Hawkar-usls/clawdbot | upstream-derived copy; no live Claude session |

No service tokens or paid inference APIs are needed for Qwen/SmolLM. The model weights are downloaded during each job from public Hugging Face. The model repo revision is reported as metadata when available; the repository's own code is reviewed separately.

## How to talk

1. Open the existing Terminal [web UI](https://github.com/Hawkar-usls/-Terminal-for-Janus/blob/main/index.html) and send a message starting with **`/qwen Привет, Янус!`** or **`/council Сравни две гипотезы...`**. Confirm the GitHub **new issue** page it opens.
2. The new `JANUS Open LLM CPU Chat` workflow sees an owner-created `[JANUS CHAT]` issue, runs bounded inference on `ubuntu-24.04`, and writes a distinct comment into that issue.
3. For continued conversation, add a new comment starting with `/qwen ` or `/council ` to the same issue. Each invocation is independently bounded. On comments within one issue, up to four preceding owner/model turns are recalled as prompt context (not weight training); the runner is not always on.
4. Alternatively open the repository's **Actions → JANUS Open LLM CPU Chat → Run workflow** and supply prompt + mode. See the run summary and downloadable receipt artifacts. These messages are not private: the repository and Actions artifacts are public.

A slash-command not matching the exact prefixes is **not** treated as an instruction. The new Actions workflow only accepts requests from `Hawkar-usls`; GitHub bot replies are never interpreted as fresh prompts.

### Peer council

`/council` implements a capped three-turn exchange:

```
Human prompt → Qwen answer → SmolLM critique → Qwen revision
```

The output includes a visible caveat that the peer critique is **not independent verification**. The saved `dialogue.json` contains the prompt, individual answers, local model identities, revisions (when exposed), request digest and final receipt SHA-256. GitHub Actions retains the artifact for 14 days; comments in GitHub Issues provide a persistent operator-visible transcript.

## Safety, cost and learning boundary

- Inference is **CPU only**, max 2,000 input characters, bounded generation tokens, 35-minute ceiling; no shell, tool, browsing, registry access or GitHub mutations delegated to generated text.
- The only permitted automated write is a workflow-authored GitHub **comment in the same Terminal issue**, not a generated action. Model output is passed as a text file, never into a command line.
- No issue response permits cross-repository Actions dispatch, Sentinel CAS lease, merge, production deployment or remote peer code execution. No secrets are needed.
- Prior issue-turn recall is limited to the same public issue, at most four turns of 700 characters each. It is temporary context, not persistent weight training.
- **The model does not update weights during chat.** Peer dialogue receipts are *candidate training data*, not labels or independent truth. Future LoRA/finetuning needs deduplication, manual or independently validated labels, frozen unseen test tasks, cost-inclusive paired tests, explicit admission, and a rollback proof.
- The named `clawdbot` repository is an upstream-derived working copy, not a live Claude model. A future optional connector needs its own provider authorization and security review. This implementation does not install/execute the Clawdbot gateway or impersonate Claude.
- The new workflow does not add a timer, cron, self-triggering recursion or always-on CPU runner. Every normal dialogue is initiated by an explicit owner action. The one-time Qwen smoke runs on merge to main and records an actual inference artifact.

## Verification plan

1. Pull request CI: Python syntax, JSON parse, pure-Python security/adversarial tests. No downloads, no inference claims.
2. After merge to `main`: the `push`-triggered `qwen-smoke` job downloads the actual weights and generates a small reply. **Only a successful job with artifact establishes GitHub-hosted CPU inference.**
3. Owner starts `/qwen` issue → verify exact comment and SHA receipt; owner starts `/council` → verify both model identities and the three sequential exchanges.
4. Leave `CLAUDE_PROVIDER_HOLD` and `WEIGHT_TRAINING_HOLD` until separately proved.

Reference manifest: [`config/JANUS_MODEL_PEERS.json`](../config/JANUS_MODEL_PEERS.json).


## Quality audit · 2026-11-15

The first 0.5B model produced a factually false statement attributing JANUS to Anthropic in [issue #39](https://github.com/Hawkar-usls/-Terminal-for-Janus/issues/39). This is explicit negative evidence, not a PASS on factual accuracy. A stronger Qwen2.5-1.5B candidate, explicit model-origin system instruction, and token attention mask are proposed. The stronger model's real smoke must pass separately; no claim of accuracy improvement without prospective paired examples.
