"""Adversarial and reproducible intake tests (no network, no model downloads)."""
import copy
import io
import json
import unittest
import zipfile

from tools.janus_dialogue_corpus import (
    OWNER, PEER, REPO, WORKFLOW, canonical_sha, verify_dialogue,
    verify_issue_binding, verify_workflow_run, extract_archive,
    label_dialogue, make_record, summarize
)


def fixture(council=True):
    request = {
        "schema": "janus.open_llm.request.v1",
        "mode": "council" if council else "qwen",
        "prompt": "What follows from a peer critique?",
        "issue_number": 40,
        "source_id": 123,
        "request_source": "github_issue_comment",
        "requested_by": OWNER,
        "execution_authority": "TEXT_ONLY",
    }
    request["request_sha256"] = canonical_sha(request)
    turns = [{"role": "initial", "model": "Qwen/Qwen2.5-1.5B-Instruct",
              "text": "A reviewer can flag uncertainty but cannot prove a hypothesis.", "revision": "abc"}]
    if council:
        turns += [{"role": "critique", "model": PEER, "text": "Consider external tests.", "revision": "def"},
                  {"role": "revised", "model": "Qwen/Qwen2.5-1.5B-Instruct",
                   "text": "A review is not an independent experiment.", "revision": "abc"}]
    d = {
        "schema": "janus.open_llm.dialogue.v1",
        "request": request,
        "exchanges": turns,
        "final_text": turns[-1]["text"],
        "weight_update_performed": False,
        "peer_feedback_is_ground_truth": False,
        "native_janus_model_modified": False,
        "self_evolution_verified": False,
        "classification": "EXPERIMENTAL_PEER_DIALOGUE_UNVERIFIED",
    }
    d["sha256"] = canonical_sha(d)
    run = {
        "id": 900, "name": WORKFLOW, "conclusion": "success",
        "event": "issue_comment", "head_branch": "main",
        "actor": {"login": OWNER}, "repository": {"full_name": REPO},
        "head_sha": "a" * 40, "html_url": "https://github.com/example/runs/900",
    }
    issue = {"number": 40, "user": {"login": OWNER}, "title": "[JANUS CHAT] Council", "id": 777}
    comments = [
        {"id": 123, "user": {"login": OWNER}, "body": "/council What follows from a peer critique?"},
        {"id": 124, "user": {"login": "github-actions[bot]"},
         "body": "<!-- JANUS_OPEN_LLM_CPU_ADAPTER -->\n"
                 f"Result\nReceipt SHA-256: \x60{d['sha256']}\x60",
         "html_url": "https://github.com/example/issues/40#issuecomment-124"},
    ]
    return d, run, issue, comments


class CorpusGateTests(unittest.TestCase):
    def test_verified_council(self):
        d, run, issue, comments = fixture()
        self.assertTrue(verify_dialogue(d))
        self.assertTrue(verify_workflow_run(run))
        self.assertIn("ISSUE_AND_BOT", verify_issue_binding(d, issue, comments)["kind"])
        record = make_record(run, {"id": 333}, d, issue, comments, {"labels": {}})
        self.assertEqual(record["review"]["status"], "HOLD_UNVERIFIED")
        state = summarize([record])
        self.assertEqual(state["total_source_verified"], 1)
        self.assertFalse(state["allowed_for_shadow_training"])
        self.assertEqual(state["approved_training_pairs"], 0)
        self.assertIn("HOLD_INDEPENDENT_PROSPECTIVE_CUSTODIAN_NOT_PROVIDED",
                      state["blockers"])
        self.assertTrue(state["three_node_sentinel_control_untouched"])

    def test_artifact_integrity_rejects_tampering(self):
        d, _, _, _ = fixture()
        for mutate in (
            lambda x: x.update(final_text="Faked conclusion"),
            lambda x: x["exchanges"][0].update(text="changed"),
            lambda x: x["request"].update(prompt="different"),
            lambda x: x.update(weight_update_performed=True),
        ):
            changed = copy.deepcopy(d)
            mutate(changed)
            with self.assertRaises(ValueError):
                verify_dialogue(changed)

    def test_even_resigned_malicious_model_is_not_allowed(self):
        d, _, _, _ = fixture()
        d["exchanges"][1]["model"] = "attacker/run-code"
        d["sha256"] = canonical_sha({k: v for k, v in d.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "INVALID_MODEL_TURN"):
            verify_dialogue(d)

    def test_reject_wrong_actor_or_github_metadata(self):
        d, run, issue, comments = fixture()
        for key, value in (("head_branch", "malicious"), ("conclusion", "failure"),
                           ("name", "fake-job"), ("event", "pull_request")):
            bad = dict(run, **{key: value})
            with self.assertRaises(ValueError):
                verify_workflow_run(bad)
        run["actor"] = {"login": "attacker"}
        with self.assertRaises(ValueError):
            verify_workflow_run(run)
        comments[0]["user"]["login"] = "attacker"
        with self.assertRaisesRegex(ValueError, "SOURCE_ACTOR"):
            verify_issue_binding(d, issue, comments)

    def test_refuse_spoofed_comment_or_digest(self):
        d, run, issue, comments = fixture()
        comments[1]["body"] = comments[1]["body"].replace(d["sha256"], "f" * 64)
        with self.assertRaisesRegex(ValueError, "NO_MATCHING"):
            make_record(run, {"id": 444}, d, issue, comments, {"labels": {}})

    def test_human_evidence_is_required_for_training_label(self):
        d, _, _, _ = fixture()
        for label in (
            {"status": "APPROVED_FOR_SHADOW_TRAINING"},
            {"status": "APPROVED_FOR_SHADOW_TRAINING",
             "human_review_sources": ["https://example.com/1", "https://example.com/2"]},
            {"status": "APPROVED_FOR_SHADOW_TRAINING",
             "human_review_sources": ["https://example.com/1", "https://example.com/1"],
             "independent_evidence": True},
        ):
            with self.assertRaises(ValueError):
                label_dialogue(d, {"labels": {d["sha256"]: label}})

    def test_safe_zip_only_dialogue_member(self):
        d, _, _, _ = fixture()
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("dialogue.json", json.dumps(d))
        self.assertEqual(extract_archive(out.getvalue())["sha256"], d["sha256"])
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("../dialogue.json", json.dumps(d))
            z.writestr("dialogue.json", json.dumps(d))
        with self.assertRaisesRegex(ValueError, "UNSAFE_ZIP_MEMBER"):
            extract_archive(out.getvalue())

    def test_record_integrity_blocks_modified_stored_data(self):
        d, run, issue, comments = fixture()
        record = make_record(run, {"id": 999}, d, issue, comments, {"labels": {}})
        record["review"]["status"] = "APPROVED_FOR_SHADOW_TRAINING"
        with self.assertRaisesRegex(ValueError, "RECORD_INTEGRITY"):
            summarize([record])


if __name__ == "__main__":
    unittest.main()
