from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from janus_json_mirror_pass import run
from janus_json_router import route


class MirrorPassTests(unittest.TestCase):
    def payload(self, text: str) -> dict:
        return {
            "schema": "janus.mirror.input.v1",
            "message_id": "test-001",
            "created_at": "2026-08-21T13:52:00+03:00",
            "source": "UNIT_TEST",
            "text": text,
        }

    def test_late_requirement_is_recovered_at_origin(self):
        result = run(self.payload(
            "Создай логику общения Януса через JSON. "
            "Она должна сначала пройти текст от начала к концу. "
            "Но обязательно перед ответом пройди тот же текст обратно и в начале покажи то, что обнаружилось только на обратном проходе."
        ))
        self.assertEqual(result["schema"], "janus.mirror.output.v1")
        self.assertTrue(result["integrity"]["source_unchanged"])
        self.assertGreaterEqual(len(result["recovered_at_origin"]), 1)
        self.assertTrue(any(item["kind"] == "BACKWARD_SCOPE" for item in result["recovered_at_origin"]))
        recovery = next(item for item in result["recovered_at_origin"] if item["kind"] == "BACKWARD_SCOPE")
        self.assertGreaterEqual(len(recovery["source_segment_ids"]), 2)
        self.assertIn(recovery["confidence"], {"HIGH", "MEDIUM"})

    def test_output_order_places_recovery_before_answer(self):
        result = run(self.payload("Сделай анализ. Но обязательно сохрани ограничения."))
        keys = list(result.keys())
        self.assertLess(keys.index("recovered_at_origin"), keys.index("answer"))
        self.assertLess(keys.index("answer"), keys.index("forward_pass"))
        self.assertLess(keys.index("forward_pass"), keys.index("reverse_pass"))

    def test_router_emits_json_with_recovery_before_authoritative_text(self):
        result = route(self.payload(
            "Подключи модель к JSON протоколу. Но обязательно сначала проверь обратный проход перед ответом."
        ))
        keys = list(result.keys())
        self.assertEqual(result["schema"], "janus.interagent.mirror_message.v1")
        self.assertLess(keys.index("recovered_at_origin"), keys.index("authoritative_text"))
        self.assertEqual(result["response_contract"]["primary_format"], "JSON")
        self.assertTrue(result["response_contract"]["must_recheck_input_reverse"])
        self.assertTrue(result["message_sha256"])

    def test_empty_delta_is_valid(self):
        result = run(self.payload("Наблюдение фиксируется."))
        self.assertIsInstance(result["recovered_at_origin"], list)
        self.assertEqual(result["answer"]["status"], "READY_FOR_AGENT_ANSWER")

    def test_non_json_schema_fails_closed(self):
        bad = self.payload("Тест")
        bad["schema"] = "wrong"
        with self.assertRaises(ValueError):
            run(bad)

    def test_source_integrity_hashes_match(self):
        result = run(self.payload("Проверь текст. Потом обязательно вернись к началу."))
        integrity = result["integrity"]
        self.assertEqual(integrity["source_sha256_before"], integrity["source_sha256_after"])


if __name__ == "__main__":
    unittest.main()
