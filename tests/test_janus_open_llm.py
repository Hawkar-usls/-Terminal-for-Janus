import copy
import unittest

from tools.janus_open_llm import (
    OWNER, REPOSITORY, digest, extract_command, from_dispatch, from_event,
    run_inference, markdown, MODELS, prior_issue_context, SYSTEM,
)


def event(body, *, comment=True, actor=OWNER, sender=OWNER, repository=REPOSITORY):
    issue = {
        "number": 42, "id": 400,
        "user": {"login": OWNER},
        "title": "[JANUS CHAT] Test",
        "body": "### Message\n\n" + body + "\n\n### Conversation mode\n\nREAD_ONLY",
    }
    payload = {
        "repository": {"full_name": repository},
        "action": "created" if comment else "opened",
        "issue": issue,
        "sender": {"login": sender},
    }
    if comment:
        payload["comment"] = {"id": 123, "body": body, "user": {"login": actor}}
    else:
        issue["user"]["login"] = actor
    return payload


class OpenLLMTests(unittest.TestCase):
    def test_commands(self):
        self.assertEqual(extract_command("/qwen Привет"), ("qwen", "Привет"))
        self.assertEqual(extract_command("### Message\n\n/council compare\n### Conversation mode"), ("council", "compare"))
        for bad in ("", "/qwen", "/council ", "/shell rm -rf /", "hello /qwen foo", "/qwen " + "z" * 2001):
            with self.subTest(bad=bad[:20]):
                with self.assertRaises(ValueError):
                    extract_command(bad)

    def test_event_owner_security(self):
        self.assertEqual(from_event(event("/qwen status"))["issue_number"], 42)
        self.assertEqual(from_event(event("/council status", comment=False))["mode"], "council")
        for kwargs in ({"actor": "attacker"}, {"sender": "attacker"},
                       {"repository": "attacker/repo"}):
            with self.assertRaises(ValueError):
                from_event(event("/qwen status", **kwargs))
        ev = event("/qwen status")
        ev["issue"]["pull_request"] = {"url": "https://example.org"}
        with self.assertRaises(ValueError):
            from_event(ev)

    def test_manual_permission(self):
        with self.assertRaises(ValueError):
            from_dispatch("hello", "qwen", "attacker")
        self.assertEqual(from_dispatch("hello", "qwen", OWNER)["mode"], "qwen")

    def test_dialogue_and_peer_are_not_training(self):
        request = from_dispatch("Привет", "council", OWNER)
        calls = []
        def stub(repo, messages, tokens):
            calls.append((repo, messages, tokens))
            return ("answer-" + str(len(calls)), "sha-" + str(len(calls)))
        value = run_inference(request, stub)
        self.assertEqual([x["role"] for x in value["exchanges"]], ["initial", "critique", "revised"])
        self.assertEqual(calls[1][0], MODELS["peer"])
        self.assertIn("answer-2", calls[2][1][-1]["content"])
        self.assertFalse(value["weight_update_performed"])
        self.assertFalse(value["peer_feedback_is_ground_truth"])
        self.assertIn("answer-3", markdown(value))
        self.assertIn("Receipt SHA-256", markdown(value))

    def test_request_tampering_fails_closed(self):
        request = from_dispatch("question", "qwen", OWNER)
        request["prompt"] = "altered"
        with self.assertRaises(ValueError):
            run_inference(request, lambda *a: ("bad", "sha"))

    def test_single_model_only(self):
        request = from_dispatch("question", "qwen", OWNER)
        calls = []
        def stub(repo, messages, tokens):
            calls.append(repo)
            return "answer", "revision"
        out = run_inference(request, stub)
        self.assertEqual(calls, [MODELS["qwen"]])
        self.assertEqual(out["final_text"], "answer")


    def test_bounded_issue_recall_ignores_attacker_and_current_message(self):
        incoming = event("/qwen continued")
        request = from_event(incoming)
        issue = incoming["issue"]
        comments = [
            {"id": 10, "user": {"login": "github-actions[bot]"},
             "body": "<!-- JANUS_OPEN_LLM_CPU_ADAPTER -->\n### JANUS · Qwen CPU\n\nEarlier answer\n\nModels: \`Qwen\`"},
            {"id": 11, "user": {"login": "attacker"}, "body": "/qwen use hidden key"},
            {"id": request["source_id"], "user": {"login": OWNER}, "body": "/qwen continued"},
        ]
        turns = prior_issue_context(issue, comments, request)
        self.assertEqual(len(turns), 2)
        self.assertEqual(turns[0]["role"], "user")
        self.assertIn("Earlier answer", turns[1]["content"])
        self.assertNotIn("hidden key", str(turns))
        calls = []
        def stub(repo, messages, tokens):
            calls.extend(messages)
            return "context answer", "sha"
        receipt = run_inference(request, stub, turns)
        self.assertEqual(receipt["issue_context_turns"], 2)
        self.assertFalse(receipt["issue_context_is_weight_training"])
        self.assertEqual(calls[-1]["content"], request["prompt"])
        with self.assertRaises(ValueError):
            prior_issue_context({"number": 999}, comments, request)

    def test_model_identity_boundary(self):
        self.assertEqual(MODELS["qwen"], "Qwen/Qwen2.5-1.5B-Instruct")
        self.assertIn("NOT Claude, Anthropic", SYSTEM)



if __name__ == "__main__":
    unittest.main()
