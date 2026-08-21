from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from janus_json_5d_deep import run


class Deep5DTests(unittest.TestCase):
    def payload(self) -> dict:
        return {
            "schema": "janus.mirror.input.v1",
            "message_id": "deep-test-001",
            "created_at": "2026-08-21T13:52:00+03:00",
            "source": "UNIT_TEST",
            "intent_id": "a" * 64,
            "text": (
                "Создай JSON граф для глубокого анализа. "
                "HRain должен видеть структурные зависимости. "
                "iNaiHR должен предлагать ассоциации как гипотезы. "
                "Но обязательно вернись от конца к началу и не превращай ассоциацию в доказательство."
            ),
        }

    def test_five_axes_present(self):
        out = run(self.payload())
        self.assertEqual(out["analysis_mode"], "DEEP_TRANSCEPTION_5D")
        self.assertEqual(
            set(out["axes"]),
            {"D1_FORWARD", "D2_REVERSE", "D3_STRUCTURAL", "D4_ASSOCIATIVE", "D5_SPIRAL_ABSTRACTION"},
        )
        self.assertFalse(out["provenance"]["raw_private_chain_of_thought_stored"])

    def test_splice_between_inserts_in_middle_without_source_mutation(self):
        payload = self.payload()
        original = payload["text"]
        patch = [{
            "op": "SPLICE_BETWEEN",
            "left_id": "S0001",
            "right_id": "S0002",
            "node": {
                "id": "ABSTRACT-MID-001",
                "label": "Новая абстракция, обнаруженная между исходным запросом и структурным ограничением.",
                "kind": "ABSTRACTION",
                "axis": "D5_SPIRAL_ABSTRACTION",
                "source_segment_ids": ["S0001", "S0002"],
                "abstraction_level": "L3_CROSS_DOMAIN_ABSTRACTION",
                "confidence": "MEDIUM",
                "validation_status": "HYPOTHESIS_NOT_EVIDENCE"
            },
            "reason": "Deep pass found a relation that logically belongs between the two source segments.",
            "provenance": {"strategy_owner": "UNIT_TEST", "axis": "D5_SPIRAL_ABSTRACTION"}
        }]
        out = run(payload, patch)
        order = out["graph"]["logical_order"]
        self.assertEqual(order[:3], ["S0001", "ABSTRACT-MID-001", "S0002"])
        self.assertEqual(payload["text"], original)
        self.assertEqual(out["provenance"]["patch_count"], 1)
        self.assertTrue(out["graph"]["patch_log"][0]["status"] == "APPLIED")

    def test_child_branch_does_not_need_tail_position(self):
        patch = [{
            "op": "INSERT_CHILD",
            "anchor_id": "S0002",
            "node": {
                "id": "CHILD-HYP-001",
                "label": "Контргипотеза к структурному чтению.",
                "kind": "COUNTERHYPOTHESIS",
                "axis": "D4_ASSOCIATIVE",
                "source_segment_ids": ["S0002"],
                "confidence": "LOW",
                "validation_status": "HYPOTHESIS_NOT_EVIDENCE"
            },
            "reason": "Preserve an alternative branch rather than append it as a final conclusion.",
            "provenance": {"strategy_owner": "UNIT_TEST", "axis": "D4_ASSOCIATIVE"}
        }]
        out = run(self.payload(), patch)
        self.assertNotIn("CHILD-HYP-001", out["graph"]["logical_order"])
        self.assertTrue(any(e["kind"] == "CHILD_OF" and e["source"] == "CHILD-HYP-001" and e["target"] == "S0002" for e in out["graph"]["edges"]))

    def test_hrain_and_inaihr_are_distinct_views(self):
        out = run(self.payload())
        left = out["hemisphere_views"]["hrain"]
        right = out["hemisphere_views"]["inaihr"]
        self.assertEqual(left["hemisphere"], "LEFT_HRAIN")
        self.assertEqual(right["hemisphere"], "RIGHT_INAIHR")
        self.assertFalse(left["control"]["automatic_graph_merge"])
        self.assertFalse(right["control"]["automatic_graph_merge"])
        self.assertFalse(out["hemisphere_views"]["demihead_disagreement"]["agreement_is_truth"])
        self.assertTrue(out["hemisphere_views"]["demihead_disagreement"]["disagreement_must_be_preserved"])

    def test_associative_nodes_are_not_evidence(self):
        out = run(self.payload())
        assoc = [n for n in out["graph"]["nodes"] if n["axis"] == "D4_ASSOCIATIVE"]
        for node in assoc:
            self.assertEqual(node["validation_status"], "HYPOTHESIS_NOT_EVIDENCE")

    def test_patch_requires_provenance_and_reason(self):
        with self.assertRaises(ValueError):
            run(self.payload(), [{
                "op": "INSERT_AFTER",
                "anchor_id": "S0001",
                "node": {"label": "bad", "kind": "HYPOTHESIS", "axis": "D4_ASSOCIATIVE"}
            }])


if __name__ == "__main__":
    unittest.main()
