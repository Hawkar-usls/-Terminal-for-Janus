import copy
import unittest

from tools.janus_open_llm import (
    OWNER, REPOSITORY, digest, extract_command, from_dispatch, from_event,
    run_inference, markdown, MODELS,
)


def event(body, *, comment=True, actor=OWNER, sender=OWNER, repository=REPOSITORY):
    issue = {
        "number": 42, "id": 400,
        "user": {"login": OWNER},
        "title": "[JANUS CHAT] Test",
        "body": "### Message\\n\\n" + body + "\\n\\n### Conversation mode\\n\\nREAD_ONLY",
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
        self.assertEqual(extract_command("### Message\\n\\n/council compare\\n### Conversation mode"), ("council", "compare"))
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


if __name__ == "__main__":
    unittest.main()
