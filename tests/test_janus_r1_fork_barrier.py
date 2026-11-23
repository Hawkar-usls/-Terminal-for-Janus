"""Offline negative controls. No fork, remote code, credentials or exam data."""
import contextlib
import copy
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import janus_habitat_fork_expansion as fork


ROOT = Path(__file__).resolve().parents[1]


def request():
    return {"request_id": "r1-preview", "upstream_full_name": "upstream/library",
            "purpose": "Inspect a bounded public reference", "need_class": "REFERENCE",
            "expected_gain": "Independent metadata review", "source_ref": "OFFLINE_UNIT_CONTROL",
            "requested_mode": "REFERENCE_FORK", "execute_if_gated": True,
            "policy_grant_id": "HAWKAR_JANUS_FORK_POLICY_2026_08_21"}


def metadata():
    return {"full_name": "upstream/library", "private": False, "visibility": "public",
            "disabled": False, "archived": False, "allow_forking": True,
            "default_branch": "main", "license": {"spdx_id": "MIT", "name": "MIT License"}}


class ForkBarrierTests(unittest.TestCase):
    def test_forged_pass_token_and_environment_never_reach_transport(self):
        candidate = {"status": "FORK_CANDIDATE_PASS", "execution_allowed": True,
                     "independent_admission_gate": "PASS", "request": request()}
        with patch.dict(os.environ, {"JANUS_FORK_TOKEN": "offline-not-a-real-token",
                                     "JANUS_R1_EXECUTE": "1", "JANUS_ALLOW_WRITES": "1"}), \
                patch.object(fork, "api_request") as api:
            with self.assertRaisesRegex(PermissionError, fork.R1_EXECUTION_BINDING_REQUIRED):
                fork.execute_fork(candidate, token="offline-not-a-real-token", destination_org="Hawkar-usls")
            api.assert_not_called()

    def test_every_legacy_mutator_is_inert(self):
        with patch.object(fork, "api_request") as api:
            for name in ("wait_for_fork", "put_file", "ensure_habitat_branch", "install_habitat_edge"):
                with self.subTest(name=name), self.assertRaisesRegex(PermissionError, "R1_EXECUTION_BINDING_REQUIRED"):
                    getattr(fork, name)({"status": "PASS"}, token="fake")
            api.assert_not_called()

    def test_transport_rejects_mutations_credentials_and_noncanonical_routes(self):
        with patch.object(fork.urllib.request, "build_opener") as network:
            for kwargs in ({"method": "POST"}, {"method": "PUT"}, {"method": "DELETE"},
                           {"body": {}}, {"token": "fake"}):
                with self.subTest(kwargs=kwargs), self.assertRaises(PermissionError):
                    fork.api_request("/repos/upstream/library", **kwargs)
            for path in ("/user", "https://example.com", "/repos/a/b/contents/file", "/repos/a/../b"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    fork.api_request(path)
            network.assert_not_called()

    def test_execute_cli_fails_before_request_read_or_get(self):
        with patch.object(fork, "inspect_candidate") as inspect, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fork.main(["does-not-exist.json", "--execute"]), 2)
            inspect.assert_not_called()

    def test_public_preview_cannot_promote_and_ignores_secret_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "request.json"; out = Path(directory) / "result.json"
            src.write_text(json.dumps(request()))
            with patch.dict(os.environ, {"JANUS_FORK_TOKEN": "offline-not-a-real-token"}), \
                    patch.object(fork, "api_request", return_value=metadata()) as api:
                self.assertEqual(fork.main([str(src), "-o", str(out)]), 0)
                api.assert_called_once_with("/repos/upstream/library")
            result = json.loads(out.read_text())
            self.assertFalse(result["executor_ready"])
            self.assertFalse(result["execution_allowed"])
            self.assertIsNone(result["execution"])
            self.assertTrue(result["blocked_execution_request"])
            self.assertEqual(result["candidate"]["independent_admission_gate"], "HOLD_EXTERNAL_REVIEW_REQUIRED")
            self.assertNotIn("offline-not-a-real-token", out.read_text())
            with patch.object(fork, "api_request", return_value=metadata()), self.assertRaises(FileExistsError):
                fork.main([str(src), "-o", str(out)])

    def test_private_foreign_identity_and_unknown_rights_remain_held(self):
        for changes in ({"private": True, "visibility": "private"}, {"private": None},
                        {"full_name": "other/library"}):
            item = metadata(); item.update(changes)
            with patch.object(fork, "api_request", return_value=item), self.assertRaises(ValueError):
                fork.inspect_candidate(request())
        item = metadata(); item["license"] = {}
        with patch.object(fork, "api_request", return_value=item):
            self.assertTrue(fork.inspect_candidate(request())["status"].startswith("HOLD"))

    def test_binding_drift_cannot_enable_execution(self):
        binding = fork.load_r1_binding()
        self.assertEqual(binding["mode"], "OBSERVE_AND_PROPOSE_ONLY")
        for key, value in (("execution_allowed", True), ("mode", "EXECUTE"), ("authority_delta", True)):
            altered = copy.deepcopy(binding); altered[key] = value
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "binding.json"; path.write_text(json.dumps(altered))
                with patch.object(fork, "R1_BINDING", path), self.assertRaises(PermissionError):
                    fork.load_r1_binding()

    def test_preview_workflow_has_no_write_scope_secret_or_execution(self):
        source = (ROOT / ".github/workflows/janus-habitat-fork-expansion.yml").read_text()
        for forbidden in ("contents: write", "secrets.", "git push", "--execute", "JANUS_FORK_TOKEN:"):
            self.assertNotIn(forbidden, source)
        self.assertIn("contents: read", source)
        self.assertIn("persist-credentials: false", source)
        self.assertIn("R1_EXECUTION_BINDING_REQUIRED", source)


if __name__ == "__main__":
    unittest.main()
