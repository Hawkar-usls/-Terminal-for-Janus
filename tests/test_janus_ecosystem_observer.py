import json
import tempfile
import unittest
from pathlib import Path

from tools.janus_ecosystem_observer import (
    build_observation,
    read_policy,
    verify_receipt,
)


ROOT = Path(__file__).resolve().parents[1]


def public(repo):
    return {"full_name": f"Hawkar-usls/{repo}", "private": False, "visibility": "public"}


class TestEcosystemObserver(unittest.TestCase):
    def setUp(self):
        self.policy, self.active = read_policy(
            ROOT / "config/JANUS_ECOSYSTEM_OBSERVER.json",
            ROOT / "config/JANUS_CONSTELLATION.json",
        )
        self.rows = [
            public("-Terminal-for-Janus"), public("Janus_Genesis"), public("Hrain"),
            public("Janus-Demiurge"), public("TOPA"), public("Janus-HELIOS"),
            public("RadioPlayerV3"), public("brand-new-janus-organ"),
            {"full_name": "Hawkar-usls/SkinGPT", "private": True, "visibility": "private"},
            {"full_name": "Hawkar-usls/other-secret", "private": True, "visibility": "private"},
        ]

    def build(self, **kwargs):
        return build_observation(
            self.policy, self.active, self.rows, source="OFFLINE_FIXTURE_NOT_LIVE_EVIDENCE",
            pages=1, observed_at="2026-10-17T12:00:00+00:00", **kwargs,
        )

    def test_public_only_and_classification(self):
        result = self.build()
        self.assertTrue(verify_receipt(result))
        self.assertEqual(result["public_repository_count"], 8)
        self.assertEqual(result["counts"], {
            "active_visible": 3, "candidates_visible": 3,
            "excluded_visible": 1, "unclassified_visible": 1,
        })
        self.assertEqual(result["unclassified_public"], ["Hawkar-usls/brand-new-janus-organ"])
        flat = json.dumps(result)
        self.assertNotIn("SkinGPT", flat)
        self.assertNotIn("other-secret", flat)
        self.assertFalse(result["authority"]["repository_code_executed"])
        self.assertFalse(result["authority"]["external_effect_authorized"])
        self.assertFalse(result["authority"]["live_constellation_modified"])
        self.assertIn("NOT_AUTO_ENROLLED", result["discovery_candidates"][0]["status"])

    def test_monotonic_hash_chain(self):
        previous = self.build()
        newer = self.build(previous=previous)
        self.assertEqual(newer["sequence"], 2)
        self.assertEqual(newer["predecessor_sha256"], previous["observation_sha256"])
        self.assertTrue(verify_receipt(newer))
        newer["counts"]["active_visible"] += 1
        self.assertFalse(verify_receipt(newer))

    def test_tampered_prior_state_fail_closed(self):
        previous = self.build()
        previous["sequence"] = 404
        with self.assertRaisesRegex(ValueError, "INTEGRITY"):
            self.build(previous=previous)

    def test_malformed_policy_fail_closed(self):
        altered = json.loads(json.dumps(self.policy))
        altered["auto_run_repositories"] = True
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "policy.json"
            path.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError, "POLICY_AUTHORITY"):
                read_policy(path, ROOT / "config/JANUS_CONSTELLATION.json")

    def test_duplicate_categories_fail_closed(self):
        altered = json.loads(json.dumps(self.policy))
        altered["discovery_candidates"].append(altered["discovery_candidates"][0])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "policy.json"
            path.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError, "DUPLICATE"):
                read_policy(path, ROOT / "config/JANUS_CONSTELLATION.json")

    def test_empty_listing_never_promotes(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE"):
            build_observation(self.policy, self.active, [], source="API", pages=1)

    def test_public_visibility_requires_two_independent_markers(self):
        rows = [public("Janus"), {"full_name": "Hawkar-usls/ambiguous"},
                {"full_name": "Hawkar-usls/private", "private": True, "visibility": "public"}]
        result = build_observation(self.policy, self.active, rows, source="OFFLINE", pages=1)
        self.assertEqual(result["public_repository_names"], ["Hawkar-usls/Janus"])


if __name__ == "__main__":
    unittest.main()
