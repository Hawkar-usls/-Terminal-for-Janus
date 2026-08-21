#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

INPUT_SCHEMA = "janus.mirror.input.v1"
OUTPUT_SCHEMA = "janus.mirror.output.v1"
PROTOCOL_ID = "JANUS_JSON_MIRROR_PASS_PROTOCOL_v1.0"

SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+|\n+")
WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9_𓀀-𓿿]+", re.UNICODE)

LEX = {
    "question": ("?", "почему", "как ", "что ", "where ", "why ", "how ", "what "),
    "requirement": ("нужно", "надо", "должен", "должна", "должно", "обязательно", "must", "need", "required", "shall"),
    "constraint": ("только", "лишь", "не больше", "не меньше", "огранич", "only", "unless", "within", "at most", "at least"),
    "negation": (" не ", "нельзя", "никогда", "без ", "not ", "never", "without ", "!=", "false"),
    "exception": ("кроме", "исключ", "за исключ", "except", "excluding", "unless"),
    "contrast": ("но ", "однако", "зато", "при этом", "but ", "however", "yet "),
    "conclusion": ("следовательно", "значит", "итого", "поэтому", "therefore", "thus", "hence", "so "),
    "directive": ("сделай", "создай", "добавь", "внеси", "запусти", "подключи", "проверь", "используй", "make ", "create ", "add ", "run ", "connect ", "check ", "use "),
}

STOP = {
    "это", "как", "что", "для", "или", "при", "она", "они", "его", "так", "все", "всё", "the", "and", "for", "with", "that", "this", "from", "into", "then", "will"
}


@dataclass(frozen=True)
class Segment:
    id: str
    index: int
    text: str
    tags: tuple[str, ...]
    keywords: tuple[str, ...]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def words(text: str) -> list[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def keywords(text: str) -> tuple[str, ...]:
    out: list[str] = []
    for w in words(text):
        if len(w) < 3 or w in STOP:
            continue
        if w not in out:
            out.append(w)
    return tuple(out[:12])


def tags(text: str) -> tuple[str, ...]:
    low = f" {text.lower().strip()} "
    found: list[str] = []
    for tag, needles in LEX.items():
        if any(n in low for n in needles):
            found.append(tag)
    return tuple(found)


def segment_text(text: str) -> list[Segment]:
    raw = [p.strip() for p in SENTENCE_SPLIT.split(text.strip()) if p.strip()]
    return [Segment(f"S{i:04d}", i, part, tags(part), keywords(part)) for i, part in enumerate(raw, 1)]


def observation_id(kind: str, source_ids: Iterable[str], finding: str) -> str:
    return sha256({"kind": kind, "source": list(source_ids), "finding": finding})[:20]


def forward_pass(segments: list[Segment]) -> dict[str, Any]:
    obs: list[dict[str, Any]] = []
    for seg in segments:
        for tag in seg.tags:
            finding = f"{tag.upper()}: {seg.text}"
            obs.append({
                "observation_id": observation_id(tag, [seg.id], finding),
                "kind": tag.upper(),
                "finding": finding,
                "source_segment_ids": [seg.id],
                "keywords": list(seg.keywords),
            })
    return {
        "direction": "0_TO_N",
        "segment_order": [s.id for s in segments],
        "observations": obs,
    }


def overlap(a: Segment, b: Segment) -> list[str]:
    aset, bset = set(a.keywords), set(b.keywords)
    return sorted(aset & bset)


def nearest_earlier(segments: list[Segment], current: Segment, wanted: set[str]) -> Segment | None:
    for cand in reversed(segments[: current.index - 1]):
        if wanted.intersection(cand.tags):
            return cand
    return None


def add_recovery(items: list[dict[str, Any]], *, kind: str, finding: str, source: list[str], confidence: str, reason: str) -> None:
    rid = observation_id(kind, source, finding)
    if any(x["recovery_id"] == rid for x in items):
        return
    items.append({
        "recovery_id": rid,
        "kind": kind,
        "finding": finding,
        "source_segment_ids": source,
        "confidence": confidence,
        "reason_forward_missed_it": reason,
        "hypothesis": confidence == "LOW",
    })


def reverse_pass(segments: list[Segment], forward: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rev_obs: list[dict[str, Any]] = []
    recovered: list[dict[str, Any]] = []

    for seg in reversed(segments):
        rev_obs.append({
            "segment_id": seg.id,
            "tags": list(seg.tags),
            "keywords": list(seg.keywords),
            "text": seg.text,
        })

        # Late qualifier/constraint can alter an earlier request even if the forward pass
        # recorded both statements independently.
        if {"constraint", "requirement", "exception", "contrast"}.intersection(seg.tags):
            earlier = nearest_earlier(segments, seg, {"directive", "question", "requirement"})
            if earlier:
                add_recovery(
                    recovered,
                    kind="BACKWARD_SCOPE",
                    finding=f"Late segment {seg.id} may rescope earlier intent {earlier.id}: '{seg.text}' applies back to '{earlier.text}'.",
                    source=[earlier.id, seg.id],
                    confidence="HIGH" if {"constraint", "requirement"}.intersection(seg.tags) else "MEDIUM",
                    reason="The forward pass can record both segments without explicitly binding the later qualifier back to the earlier request.",
                )

        # A conclusion seen first on the reverse walk invites reconstruction of its premise.
        if "conclusion" in seg.tags:
            earlier = nearest_earlier(segments, seg, {"question", "directive", "requirement"})
            if earlier:
                add_recovery(
                    recovered,
                    kind="OUTCOME_TO_PREMISE",
                    finding=f"Reading from outcome {seg.id} backward exposes {earlier.id} as a premise/goal that should be checked against the conclusion.",
                    source=[earlier.id, seg.id],
                    confidence="MEDIUM",
                    reason="The relation becomes salient when the conclusion is encountered before its setup.",
                )

        # A late negation/exception sharing terms with an earlier segment can invalidate a
        # naive forward assumption.
        if {"negation", "exception"}.intersection(seg.tags):
            best: tuple[Segment, list[str]] | None = None
            for earlier in segments[: seg.index - 1]:
                common = overlap(earlier, seg)
                if common and (best is None or len(common) > len(best[1])):
                    best = (earlier, common)
            if best:
                earlier, common = best
                add_recovery(
                    recovered,
                    kind="NEGATION_BACKPROPAGATION",
                    finding=f"Late negation/exception {seg.id} shares [{', '.join(common)}] with {earlier.id}; re-check the earlier interpretation under the later restriction.",
                    source=[earlier.id, seg.id],
                    confidence="MEDIUM",
                    reason="The reverse walk propagates a later restriction toward earlier related material.",
                )

    return {
        "direction": "N_TO_0",
        "segment_order": [s.id for s in reversed(segments)],
        "observations": rev_obs,
        "recovered_count": len(recovered),
    }, recovered


def run(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"INPUT_SCHEMA_REQUIRED:{INPUT_SCHEMA}")
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("NONEMPTY_TEXT_REQUIRED")
    if not isinstance(payload.get("message_id"), str) or not payload["message_id"]:
        raise ValueError("MESSAGE_ID_REQUIRED")

    source_hash_before = hashlib.sha256(text.encode("utf-8")).hexdigest()
    segments = segment_text(text)
    if not segments:
        raise ValueError("NO_SOURCE_SEGMENTS")

    forward = forward_pass(segments)
    reverse, recovered = reverse_pass(segments, forward)
    source_hash_after = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if source_hash_before != source_hash_after:
        raise ValueError("SOURCE_CHANGED_BETWEEN_PASSES")

    # This reference engine does not fabricate a semantic answer. It prepares the
    # evidence-bearing two-pass context that an LLM or other agent must consume.
    answer = {
        "status": "READY_FOR_AGENT_ANSWER",
        "instruction": "Generate the human/agent answer only after consuming recovered_at_origin, forward_pass and reverse_pass. Render recovered_at_origin before the main answer.",
    }
    output: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "message_id": payload["message_id"],
        "recovered_at_origin": recovered,
        "answer": answer,
        "forward_pass": forward,
        "reverse_pass": reverse,
        "provenance": {
            "protocol_id": PROTOCOL_ID,
            "source": payload.get("source"),
            "intent_id": payload.get("intent_id"),
            "session_id": payload.get("session_id"),
            "generation": payload.get("generation"),
            "segment_count": len(segments),
            "engine": "tools/janus_json_mirror_pass.py",
            "deterministic_reference_engine": True,
        },
        "integrity": {
            "source_sha256_before": source_hash_before,
            "source_sha256_after": source_hash_after,
            "source_unchanged": source_hash_before == source_hash_after,
        },
    }
    output["integrity"]["output_sha256_without_self"] = sha256(output)
    return output


def load_payload(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="JANUS JSON forward/reverse mirror-pass reference engine")
    parser.add_argument("input", nargs="?", help="Input JSON file; stdin when omitted")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args()
    try:
        result = run(load_payload(args.input))
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    except Exception as exc:
        sys.stderr.write(f"janus_json_mirror_pass: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
