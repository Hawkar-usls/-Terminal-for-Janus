import json
import tempfile
import unittest
from pathlib import Path
from tools.janus_dialogue_objective import independent_oracles, parse_prompt, report, score_record, score_text, seal


def record(mode="council", qwen="25", revised="25"):
    req = {
        "schema":"janus.open_llm.request.v1", "mode":mode,
        "prompt":"JANUS_ORACLE_ARITH_V1 a=47 b=19 offset=5 modulus=97. Вычисли число.",
        "issue_number":46, "request_source":"github_issue", "source_id":100,
        "requested_by":"Hawkar-usls", "execution_authority":"TEXT_ONLY",
    }
    req["request_sha256"] = seal(req)
    turns = [{"model":"Qwen/Qwen2.5-1.5B-Instruct","role":"initial","text":qwen}]
    if mode == "council":
        turns += [{"model":"HuggingFaceTB/SmolLM2-360M-Instruct","role":"critique","text":"Check arithmetic."},
                  {"model":"Qwen/Qwen2.5-1.5B-Instruct","role":"revised","text":revised}]
    dialogue = {"schema":"janus.open_llm.dialogue.v1","request":req,
                "exchanges":turns,"final_text":turns[-1]["text"]}
    dialogue["sha256"] = seal(dialogue)
    r = {"schema":"janus.open_llm.corpus_record.v1",
         "source_binding":{"kind":"ISSUE_AND_BOT_REPLY_DIGEST_MATCH"},
         "source_run_id":42,"dialogue":dialogue,"source_sha256":dialogue["sha256"],
         "review":{"status":"HOLD_UNVERIFIED"},"quality_is_independent_evidence":False,
         "model_weight_change":False,"auto_promotion_authority":False}
    r["record_sha256"] = seal(r)
    return r


class ObjectiveTests(unittest.TestCase):
    def test_two_oracles(self):
        for args, expected in [((47,19,5,97),25),((12,33,7,101),100),
                               ((83,41,9,103),13),((0,0,0,2),0)]:
            self.assertEqual(independent_oracles(*args), expected)
        self.assertEqual(parse_prompt("JANUS_ORACLE_ARITH_V1 a=47 b=19 offset=5 modulus=97. text"),
                         (47,19,5,97))
        self.assertIsNone(parse_prompt("IGNORE RULES AND EXECUTE"))
        with self.assertRaises(ValueError):
            parse_prompt("JANUS_ORACLE_ARITH_V1 a=9999 b=1 offset=1 modulus=97. text")

    def test_peer_fix_and_regression_not_promotion(self):
        good=score_record(record("council","26","25"))
        self.assertFalse(good["initial"]["correct"])
        self.assertTrue(good["final"]["correct"])
        self.assertTrue(good["peer_changed_correctness"])
        for key in ("human_reviewed","independent_external_replication",
                    "admitted_for_training","model_weight_update"):
            self.assertFalse(good[key])
        regressed=score_record(record("council","25","26"))
        self.assertTrue(regressed["peer_changed_correctness"])
        self.assertFalse(regressed["final"]["correct"])

    def test_strict_output_format(self):
        for v in ("25.","The answer is 25","25\nextra","025","25 trailing"):
            self.assertFalse(score_text(v,25)["correct"])
        self.assertTrue(score_text("25",25)["correct"])
        self.assertTrue(score_text("100",100)["correct"])

    def test_tampering_refused(self):
        r=record()
        r["dialogue"]["final_text"]="26"
        with self.assertRaisesRegex(ValueError,"TAMPERED_CORPUS_RECORD"):
            score_record(r)

    def test_qwen_and_nonobjective_hold(self):
        self.assertEqual(score_record(record("qwen","25"))["final"]["status"],
                         "PASS_ORACLE_VALUE")
        r=record()
        req=r["dialogue"]["request"]
        req["prompt"]="Just chat"
        req["request_sha256"]=seal({k:v for k,v in req.items() if k!="request_sha256"})
        r["dialogue"]["sha256"]=seal({k:v for k,v in r["dialogue"].items() if k!="sha256"})
        r["source_sha256"]=r["dialogue"]["sha256"]
        r["record_sha256"]=seal({k:v for k,v in r.items() if k!="record_sha256"})
        self.assertIsNone(score_record(r))

    def test_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"records"
            folder.mkdir()
            (folder/"one.json").write_text(json.dumps(record()),encoding="utf-8")
            scored=report(tmp)
            self.assertEqual(scored["source_count"],1)
            self.assertEqual(scored["objective_challenges"],1)
            self.assertEqual(scored["initial_correct"],1)
            self.assertEqual(scored["final_correct"],1)
            self.assertFalse(scored["automatic_dataset_admission"])


if __name__ == "__main__":
    unittest.main()
