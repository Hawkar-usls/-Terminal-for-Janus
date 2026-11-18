#!/usr/bin/env python3
"""Bounded public research council feed; never a training corpus or execution channel."""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from janus_open_llm import digest, run_inference, MODELS, SCHEMA

FEED_SCHEMA = "janus.scheduled_dialogue.feed.v1"
SOURCE = "JANUS_SCHEDULED_COUNCIL"
LABEL = "JANUS · автоматический совет моделей"
MAX_RECORDS = 48
TOPICS = (
    "Как провести независимую проверку математической гипотезы? Назови один контроль и одно ограничение.",
    "Предложи один способ отличить слабый радиосигнал от случайного шума. Укажи риск ложной тревоги.",
    "Как проверить, что алгоритм ускорился на новых данных, а не на обучающей выборке?",
    "Назови один способ измерить потерю старых навыков при обучении модели и объясни ограничение.",
    "Как отличить результат физического измерения от предположения модели? Приведи один пример.",
    "Что означает воспроизводимость вычислительного эксперимента? Назови минимальный набор данных.",
    "Почему совпадение ответов двух ИИ не заменяет независимое доказательство?",
    "Как проверить устойчивость алгоритма к перестановке входных данных?",
    "Что такое контрольная группа? Приведи пример для обнаружения радиосигналов.",
    "Как оценить полную вычислительную стоимость алгоритма? Укажи две составляющие.",
    "Как обнаружить утечку тестовых данных при обучении? Назови один способ и его ограничение.",
    "Как сформулировать фальсифицируемую гипотезу? Дай один конкретный пример.",
)

def slot_now():
    return int(datetime.now(timezone.utc).timestamp()) // 3600

def request_for(slot, run_id):
    if type(slot) is not int or slot <= 0 or type(run_id) is not int or run_id <= 0:
        raise ValueError("INVALID_SLOT_OR_RUN")
    topic = TOPICS[slot % len(TOPICS)]
    request = {
        "schema": SCHEMA, "mode": "council",
        "prompt": f"Автоматический исследовательский диалог JANUS. {topic} Ответь по-русски, кратко. Не заявляй о выполненных экспериментах.",
        "issue_number": None, "request_source": "scheduled_council",
        "source_id": run_id, "requested_by": SOURCE, "slot_utc_hour": slot,
        "execution_authority": "TEXT_ONLY",
    }
    request["request_sha256"] = digest(request)
    return request

def validate_dialogue(dialogue, run_id):
    if not isinstance(dialogue, dict) or dialogue.get("schema") != "janus.open_llm.dialogue.v1":
        raise ValueError("WRONG_SCHEMA")
    if digest({k: v for k, v in dialogue.items() if k != "sha256"}) != dialogue.get("sha256"):
        raise ValueError("DIALOGUE_DIGEST_MISMATCH")
    req = dialogue.get("request", {})
    if req != request_for(req.get("slot_utc_hour"), run_id):
        raise ValueError("WRONG_SCHEDULED_REQUEST")
    if dialogue.get("issue_context_turns") != 0 or dialogue.get("issue_context_is_weight_training") is not False:
        raise ValueError("UNEXPECTED_HISTORY")
    for field in ("weight_update_performed", "peer_feedback_is_ground_truth",
                  "native_janus_model_modified", "self_evolution_verified"):
        if dialogue.get(field) is not False:
            raise ValueError("UNSAFE_DIALOGUE")
    if dialogue.get("classification") != "EXPERIMENTAL_PEER_DIALOGUE_UNVERIFIED":
        raise ValueError("INVALID_CLASSIFICATION")
    turns = dialogue.get("exchanges")
    if not isinstance(turns, list) or len(turns) != 3:
        raise ValueError("WRONG_TURN_COUNT")
    for turn, role, model in zip(turns, ("initial", "critique", "revised"),
                                 (MODELS["qwen"], MODELS["peer"], MODELS["qwen"])):
        if (not isinstance(turn, dict) or turn.get("role") != role or turn.get("model") != model
                or not isinstance(turn.get("text"), str) or not 1 <= len(turn["text"]) <= 2000
                or not re.fullmatch(r"[0-9a-f]{40}", str(turn.get("revision", "")))):
            raise ValueError("INVALID_TURN")
    if dialogue.get("final_text") != turns[-1]["text"]:
        raise ValueError("FINAL_TURN_MISMATCH")
    return req

def wrap(dialogue, run_id):
    req = validate_dialogue(dialogue, run_id)
    return {"source_run_id": run_id, "slot_utc_hour": req["slot_utc_hour"],
            "origin_kind": SOURCE, "display_label": LABEL,
            "human_authorship_verified": False, "training_allowed": False,
            "source_url": f"https://github.com/Hawkar-usls/-Terminal-for-Janus/actions/runs/{run_id}",
            "dialogue": dialogue}

def append(feed, dialogue, run_id):
    if feed.get("schema") != FEED_SCHEMA or not isinstance(feed.get("records"), list):
        raise ValueError("WRONG_FEED")
    old = feed["records"]
    if len(old) > MAX_RECORDS:
        raise ValueError("UNBOUNDED_FEED")
    slots = set()
    for entry in old:
        if entry != wrap(entry["dialogue"], entry["source_run_id"]):
            raise ValueError("INVALID_STORED_ENTRY")
        slot = entry["slot_utc_hour"]
        if slot in slots:
            raise ValueError("DUPLICATE_STORED_SLOT")
        slots.add(slot)
    entry = wrap(dialogue, run_id)
    if entry["slot_utc_hour"] not in slots:
        old = old + [entry]
    rows = sorted(old, key=lambda r: r["slot_utc_hour"], reverse=True)[:MAX_RECORDS]
    return {"schema": FEED_SCHEMA, "records": rows, "retention_records": MAX_RECORDS,
            "training_allowed": False, "execution_authority": "TEXT_ONLY"}

def read_json(path, limit):
    p = Path(path)
    if not p.is_file() or p.is_symlink() or p.stat().st_size > limit:
        raise ValueError("INVALID_JSON_FILE")
    return json.loads(p.read_text(encoding="utf-8"))

def write_json(path, obj):
    p = Path(path)
    if p.is_symlink():
        raise ValueError("SYMLINK_OUTPUT")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("generate", "publish"))
    p.add_argument("--run-id", required=True, type=int)
    p.add_argument("--dialogue", required=True)
    p.add_argument("--feed")
    args = p.parse_args()
    if args.command == "generate":
        value = run_inference(request_for(slot_now(), args.run_id))
        validate_dialogue(value, args.run_id)
        write_json(args.dialogue, value)
    else:
        if not args.feed:
            p.error("--feed required")
        value = read_json(args.dialogue, 45000)
        feed = (read_json(args.feed, 2_500_000) if Path(args.feed).exists()
                else {"schema": FEED_SCHEMA, "records": []})
        write_json(args.feed, append(feed, value, args.run_id))

if __name__ == "__main__":
    main()
