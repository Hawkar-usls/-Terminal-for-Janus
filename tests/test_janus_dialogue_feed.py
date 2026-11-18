import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import janus_dialogue_feed as feed
from janus_open_llm import run_inference, digest

def stub(model, messages, max_tokens):
    return "Synthetic response for offline contract only.", "a" * 40

def dialogue(slot, run):
    return run_inference(feed.request_for(slot, run), generator=stub)

class DialogueFeedContract(unittest.TestCase):
    def test_distinct_machine_origin(self):
        d = dialogue(100, 123)
        row = feed.wrap(d, 123)
        self.assertEqual(row["origin_kind"], "JANUS_SCHEDULED_COUNCIL")
        self.assertFalse(row["human_authorship_verified"])
        self.assertFalse(row["training_allowed"])
        self.assertEqual(len(d["exchanges"]), 3)
        self.assertIsNone(d["request"]["issue_number"])

    def test_same_slot_is_not_duplicated(self):
        start = {"schema": feed.FEED_SCHEMA, "records": []}
        first = feed.append(start, dialogue(100, 123), 123)
        second = feed.append(first, dialogue(100, 124), 124)
        self.assertEqual(first, second)

    def test_bounded_window(self):
        state = {"schema": feed.FEED_SCHEMA, "records": []}
        for i in range(55):
            state = feed.append(state, dialogue(100+i, 1000+i), 1000+i)
        self.assertEqual(len(state["records"]), 48)
        self.assertEqual(state["records"][0]["slot_utc_hour"], 154)
        self.assertEqual(state["records"][-1]["slot_utc_hour"], 107)

    def test_wrong_run_and_tampered_origin_rejected(self):
        d = dialogue(100, 123)
        with self.assertRaises(ValueError):
            feed.wrap(d, 124)
        d["request"]["requested_by"] = "Hawkar-usls"
        d["request"]["request_sha256"] = digest({k:v for k,v in d["request"].items() if k != "request_sha256"})
        d["sha256"] = digest({k:v for k,v in d.items() if k != "sha256"})
        with self.assertRaises(ValueError):
            feed.wrap(d, 123)

    def test_authority_escalation_rejected(self):
        d = dialogue(100, 123)
        d["weight_update_performed"] = True
        d["sha256"] = digest({k:v for k,v in d.items() if k != "sha256"})
        with self.assertRaises(ValueError):
            feed.wrap(d, 123)

if __name__ == "__main__":
    unittest.main()
