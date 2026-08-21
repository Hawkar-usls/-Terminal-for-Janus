#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Iterable

from janus_json_mirror_pass import (
    INPUT_SCHEMA,
    Segment,
    forward_pass,
    reverse_pass,
    segment_text,
    sha256,
)

OUTPUT_SCHEMA = "janus.deep_analysis_5d.output.v1"
PROTOCOL_ID = "JANUS_JSON_5D_DEEP_ANALYSIS_PROTOCOL_v1.0"
ORIGINS = {"USER", "REMOTE_AI", "LOCAL_FALLBACK", "LEGACY_UNKNOWN", "SYSTEM"}
NODE_KINDS = {
    "SOURCE_SEGMENT", "OBSERVATION", "CONSTRAINT", "QUESTION", "HYPOTHESIS",
    "COUNTERHYPOTHESIS", "ABSTRACTION", "INVARIANT", "CONTRADICTION",
    "MISSING_PREMISE", "RECOVERED_AT_ORIGIN", "GATE", "EVIDENCE_REFERENCE", "UNKNOWN",
}
EDGE_KINDS = {
    "NEXT", "PREVIOUS", "DEPENDS_ON", "CONSTRAINS", "CONTRADICTS", "SUPPORTS",
    "MIRRORS", "ABSTRACTS", "INSTANTIATES", "ASSOCIATES_WITH", "COUNTERFACTUAL_OF",
    "RECOVERS", "RESCOPES", "GATES", "DERIVED_FROM", "SAME_INTENT_AS",
    "SURVIVES_TRANSFORMATION", "CHILD_OF", "SIBLING_OF",
}
PATCH_OPS = {
    "INSERT_BEFORE", "INSERT_AFTER", "INSERT_CHILD", "INSERT_SIBLING", "SPLICE_BETWEEN",
    "FORK_BRANCH", "ANNOTATE_NODE", "ANNOTATE_EDGE", "LINK_DISTANT_NODES",
    "PROMOTE_TO_ABSTRACTION", "DEMOTE_TO_INSTANCE",
}


def _node_id(prefix: str, value: Any) -> str:
    return f"{prefix}-{sha256(value)[:16]}"


def _edge_id(source: str, target: str, kind: str) -> str:
    return _node_id("E", {"s": source, "t": target, "k": kind})


def _safe_origin(value: Any) -> str:
    return value if isinstance(value, str) and value in ORIGINS else "SYSTEM"


def make_node(
    node_id: str,
    label: str,
    *,
    kind: str,
    axis: str,
    origin: str = "SYSTEM",
    source_segment_ids: Iterable[str] = (),
    abstraction_level: str = "L1_LOCAL_RELATION",
    confidence: str = "HIGH",
    validation_status: str = "STRUCTURED_TRACE_ONLY",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if kind not in NODE_KINDS:
        kind = "UNKNOWN"
    return {
        "id": node_id,
        "label": label,
        "kind": kind,
        "axis": axis,
        "origin": _safe_origin(origin),
        "source_segment_ids": list(source_segment_ids),
        "abstraction_level": abstraction_level,
        "confidence": confidence,
        "validation_status": validation_status,
        "metadata": metadata or {},
    }


def make_edge(source: str, target: str, kind: str, *, axis: str, confidence: str = "HIGH", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if kind not in EDGE_KINDS:
        raise ValueError(f"UNKNOWN_EDGE_KIND:{kind}")
    return {
        "id": _edge_id(source, target, kind),
        "source": source,
        "target": target,
        "kind": kind,
        "axis": axis,
        "confidence": confidence,
        "metadata": metadata or {},
    }


def _tag_kind(tag: str) -> str:
    return {
        "QUESTION": "QUESTION",
        "REQUIREMENT": "CONSTRAINT",
        "CONSTRAINT": "CONSTRAINT",
        "NEGATION": "CONSTRAINT",
        "EXCEPTION": "CONSTRAINT",
        "DIRECTIVE": "OBSERVATION",
        "CONCLUSION": "OBSERVATION",
        "CONTRAST": "OBSERVATION",
    }.get(tag, "OBSERVATION")


def build_base_graph(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    text = payload.get("text")
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"INPUT_SCHEMA_REQUIRED:{INPUT_SCHEMA}")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("NONEMPTY_TEXT_REQUIRED")

    segments = segment_text(text)
    forward = forward_pass(segments)
    reverse, recovered = reverse_pass(segments, forward)

    graph: dict[str, Any] = {
        "nodes": [],
        "edges": [],
        "logical_order": [s.id for s in segments],
        "patch_log": [],
        "source_segment_ids": [s.id for s in segments],
    }
    node_ids: set[str] = set()
    edge_ids: set[str] = set()

    def add_node(node: dict[str, Any]) -> None:
        if node["id"] in node_ids:
            return
        graph["nodes"].append(node)
        node_ids.add(node["id"])

    def add_edge(edge: dict[str, Any]) -> None:
        if edge["id"] in edge_ids:
            return
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            raise ValueError(f"DANGLING_EDGE:{edge['source']}->{edge['target']}")
        graph["edges"].append(edge)
        edge_ids.add(edge["id"])

    # D1: source and explicit forward observations.
    for seg in segments:
        add_node(make_node(
            seg.id, seg.text, kind="SOURCE_SEGMENT", axis="D1_FORWARD", origin="USER",
            source_segment_ids=[seg.id], abstraction_level="L0_LITERAL_SOURCE",
            metadata={"index": seg.index, "tags": list(seg.tags), "keywords": list(seg.keywords)},
        ))
    for left, right in zip(segments, segments[1:]):
        add_edge(make_edge(left.id, right.id, "NEXT", axis="D1_FORWARD"))
        add_edge(make_edge(right.id, left.id, "PREVIOUS", axis="D2_REVERSE"))

    for obs in forward["observations"]:
        oid = f"D1-{obs['observation_id']}"
        add_node(make_node(
            oid, obs["finding"], kind=_tag_kind(obs["kind"]), axis="D1_FORWARD",
            source_segment_ids=obs["source_segment_ids"], confidence="HIGH",
            metadata={"forward_observation_id": obs["observation_id"], "keywords": obs.get("keywords", [])},
        ))
        for sid in obs["source_segment_ids"]:
            add_edge(make_edge(oid, sid, "DERIVED_FROM", axis="D1_FORWARD"))

    # D2: reverse-only recoveries become first-class graph nodes.
    recovered_nodes: list[dict[str, Any]] = []
    for item in recovered:
        rid = f"D2-{item['recovery_id']}"
        kind = "MISSING_PREMISE" if item["kind"] == "OUTCOME_TO_PREMISE" else "RECOVERED_AT_ORIGIN"
        node = make_node(
            rid, item["finding"], kind=kind, axis="D2_REVERSE",
            source_segment_ids=item["source_segment_ids"], confidence=item["confidence"],
            validation_status="SUPPORTED_BY_SOURCE_TRACE_NOT_WORLD_TRUTH",
            metadata={"recovery_kind": item["kind"], "reason_forward_missed_it": item["reason_forward_missed_it"]},
        )
        add_node(node)
        recovered_nodes.append(node)
        edge_kind = "RESCOPES" if item["kind"] in {"BACKWARD_SCOPE", "NEGATION_BACKPROPAGATION"} else "RECOVERS"
        for sid in item["source_segment_ids"]:
            add_edge(make_edge(rid, sid, edge_kind, axis="D2_REVERSE", confidence=item["confidence"]))

    # D3: HRain-style structural topology. Shared explicit tags create typed structural relations.
    for i, a in enumerate(segments):
        for b in segments[i + 1:]:
            shared_tags = sorted(set(a.tags) & set(b.tags))
            shared_words = sorted(set(a.keywords) & set(b.keywords))
            if shared_tags:
                add_edge(make_edge(a.id, b.id, "MIRRORS", axis="D3_STRUCTURAL", confidence="MEDIUM", metadata={"shared_tags": shared_tags}))
            if shared_words and abs(a.index - b.index) > 1:
                add_edge(make_edge(a.id, b.id, "DEPENDS_ON", axis="D3_STRUCTURAL", confidence="LOW", metadata={"shared_keywords": shared_words, "hypothesis": True}))

    # Structural hub abstraction is auditable and label-independent enough for the reference engine.
    degree: dict[str, int] = {s.id: 0 for s in segments}
    for edge in graph["edges"]:
        if edge["axis"] == "D3_STRUCTURAL":
            degree[edge["source"]] = degree.get(edge["source"], 0) + 1
            degree[edge["target"]] = degree.get(edge["target"], 0) + 1
    if degree and max(degree.values(), default=0) > 0:
        hub = max(degree, key=degree.get)
        hid = _node_id("D3-HUB", {"hub": hub, "degree": degree[hub]})
        add_node(make_node(
            hid, f"Structural hub candidate around {hub} (degree={degree[hub]}).",
            kind="ABSTRACTION", axis="D3_STRUCTURAL", source_segment_ids=[hub],
            abstraction_level="L2_STRUCTURAL_PATTERN", confidence="MEDIUM",
            validation_status="GRAPH_TOPOLOGY_CANDIDATE",
        ))
        add_edge(make_edge(hid, hub, "ABSTRACTS", axis="D3_STRUCTURAL", confidence="MEDIUM"))

    # D4: iNaiHR-style associative candidates from non-adjacent shared concepts.
    # These are explicitly hypotheses, never evidence.
    seen_assoc: set[tuple[str, str, tuple[str, ...]]] = set()
    for i, a in enumerate(segments):
        for b in segments[i + 2:]:
            shared = tuple(sorted(set(a.keywords) & set(b.keywords)))
            if not shared:
                continue
            key = (a.id, b.id, shared)
            if key in seen_assoc:
                continue
            seen_assoc.add(key)
            aid = _node_id("D4-ASSOC", key)
            add_node(make_node(
                aid,
                f"Associative candidate: {a.id} <-> {b.id} via {', '.join(shared)}.",
                kind="HYPOTHESIS", axis="D4_ASSOCIATIVE", source_segment_ids=[a.id, b.id],
                abstraction_level="L3_CROSS_DOMAIN_ABSTRACTION", confidence="LOW",
                validation_status="HYPOTHESIS_NOT_EVIDENCE",
                metadata={"shared_keywords": list(shared)},
            ))
            add_edge(make_edge(aid, a.id, "ASSOCIATES_WITH", axis="D4_ASSOCIATIVE", confidence="LOW"))
            add_edge(make_edge(aid, b.id, "ASSOCIATES_WITH", axis="D4_ASSOCIATIVE", confidence="LOW"))

    # D5: invariants that survive all reference passes without semantic invention.
    invariant = _node_id("D5-INVARIANT", {"message": payload.get("message_id"), "source": sha256(text)})
    add_node(make_node(
        invariant,
        "Invariant: authoritative source identity is preserved across all passes; graph expansion may add interpretation but may not silently rewrite the source.",
        kind="INVARIANT", axis="D5_SPIRAL_ABSTRACTION", source_segment_ids=[s.id for s in segments],
        abstraction_level="L4_META_INVARIANT", confidence="HIGH",
        validation_status="PROTOCOL_INVARIANT",
    ))
    for sid in graph["source_segment_ids"]:
        add_edge(make_edge(invariant, sid, "SURVIVES_TRANSFORMATION", axis="D5_SPIRAL_ABSTRACTION"))

    return graph, forward, reverse, recovered


def _node_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(n["id"]): n for n in graph["nodes"]}


def _edge_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(e["id"]): e for e in graph["edges"]}


def _validate_new_node(node: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(node, dict):
        raise ValueError("PATCH_NEW_NODE_OBJECT_REQUIRED")
    node_id = str(node.get("id") or f"P-{uuid.uuid4().hex[:16]}")
    label = str(node.get("label") or "").strip()
    if not label:
        raise ValueError("PATCH_NODE_LABEL_REQUIRED")
    kind = str(node.get("kind") or "HYPOTHESIS")
    axis = str(node.get("axis") or "D5_SPIRAL_ABSTRACTION")
    return make_node(
        node_id, label, kind=kind, axis=axis, origin=str(node.get("origin") or "SYSTEM"),
        source_segment_ids=node.get("source_segment_ids") or [],
        abstraction_level=str(node.get("abstraction_level") or "L3_CROSS_DOMAIN_ABSTRACTION"),
        confidence=str(node.get("confidence") or "LOW"),
        validation_status=str(node.get("validation_status") or "HYPOTHESIS_NOT_EVIDENCE"),
        metadata=copy.deepcopy(node.get("metadata") or {}),
    )


def apply_patch_operations(graph: dict[str, Any], operations: list[dict[str, Any]]) -> dict[str, Any]:
    out = copy.deepcopy(graph)
    for ordinal, op in enumerate(operations, 1):
        if not isinstance(op, dict):
            raise ValueError("PATCH_OPERATION_OBJECT_REQUIRED")
        kind = str(op.get("op") or "")
        if kind not in PATCH_OPS:
            raise ValueError(f"PATCH_OPERATION_NOT_ALLOWED:{kind}")
        reason = str(op.get("reason") or "").strip()
        provenance = op.get("provenance")
        if not reason or not isinstance(provenance, dict):
            raise ValueError("PATCH_REASON_AND_PROVENANCE_REQUIRED")

        nodes = _node_map(out)
        edges = _edge_map(out)
        receipt: dict[str, Any] = {
            "patch_id": _node_id("PATCH", {"ordinal": ordinal, "op": op}),
            "ordinal": ordinal,
            "op": kind,
            "reason": reason,
            "provenance": copy.deepcopy(provenance),
            "status": "APPLIED",
        }

        if kind in {"INSERT_BEFORE", "INSERT_AFTER", "INSERT_CHILD", "INSERT_SIBLING", "SPLICE_BETWEEN", "FORK_BRANCH", "PROMOTE_TO_ABSTRACTION", "DEMOTE_TO_INSTANCE"}:
            new_node = _validate_new_node(op.get("node") or {})
            if new_node["id"] in nodes:
                raise ValueError(f"PATCH_NODE_ID_EXISTS:{new_node['id']}")
            out["nodes"].append(new_node)
            nodes[new_node["id"]] = new_node
            receipt["node_id"] = new_node["id"]

        if kind in {"INSERT_BEFORE", "INSERT_AFTER"}:
            anchor = str(op.get("anchor_id") or "")
            if anchor not in nodes:
                raise ValueError(f"PATCH_ANCHOR_NOT_FOUND:{anchor}")
            order = out["logical_order"]
            if anchor not in order:
                raise ValueError(f"PATCH_ANCHOR_NOT_IN_LOGICAL_ORDER:{anchor}")
            pos = order.index(anchor) + (1 if kind == "INSERT_AFTER" else 0)
            order.insert(pos, receipt["node_id"])
            ekind = "PREVIOUS" if kind == "INSERT_BEFORE" else "NEXT"
            source, target = (anchor, receipt["node_id"]) if kind == "INSERT_AFTER" else (receipt["node_id"], anchor)
            out["edges"].append(make_edge(source, target, ekind, axis=nodes[receipt["node_id"]]["axis"], confidence=nodes[receipt["node_id"]]["confidence"]))
            receipt["anchor_id"] = anchor

        elif kind == "SPLICE_BETWEEN":
            left, right = str(op.get("left_id") or ""), str(op.get("right_id") or "")
            order = out["logical_order"]
            if left not in nodes or right not in nodes:
                raise ValueError("PATCH_SPLICE_ANCHOR_NOT_FOUND")
            if left not in order or right not in order or order.index(right) != order.index(left) + 1:
                raise ValueError("PATCH_SPLICE_REQUIRES_ADJACENT_LOGICAL_NODES")
            order.insert(order.index(right), receipt["node_id"])
            out["edges"].append(make_edge(left, receipt["node_id"], "NEXT", axis=nodes[receipt["node_id"]]["axis"]))
            out["edges"].append(make_edge(receipt["node_id"], right, "NEXT", axis=nodes[receipt["node_id"]]["axis"]))
            receipt.update({"left_id": left, "right_id": right})

        elif kind == "INSERT_CHILD":
            anchor = str(op.get("anchor_id") or "")
            if anchor not in nodes:
                raise ValueError(f"PATCH_ANCHOR_NOT_FOUND:{anchor}")
            out["edges"].append(make_edge(receipt["node_id"], anchor, "CHILD_OF", axis=nodes[receipt["node_id"]]["axis"]))
            receipt["anchor_id"] = anchor

        elif kind == "INSERT_SIBLING":
            anchor = str(op.get("anchor_id") or "")
            if anchor not in nodes:
                raise ValueError(f"PATCH_ANCHOR_NOT_FOUND:{anchor}")
            out["edges"].append(make_edge(receipt["node_id"], anchor, "SIBLING_OF", axis=nodes[receipt["node_id"]]["axis"]))
            receipt["anchor_id"] = anchor

        elif kind in {"FORK_BRANCH", "PROMOTE_TO_ABSTRACTION", "DEMOTE_TO_INSTANCE"}:
            anchor = str(op.get("anchor_id") or "")
            if anchor not in nodes:
                raise ValueError(f"PATCH_ANCHOR_NOT_FOUND:{anchor}")
            ekind = {
                "FORK_BRANCH": "DERIVED_FROM",
                "PROMOTE_TO_ABSTRACTION": "ABSTRACTS",
                "DEMOTE_TO_INSTANCE": "INSTANTIATES",
            }[kind]
            out["edges"].append(make_edge(receipt["node_id"], anchor, ekind, axis=nodes[receipt["node_id"]]["axis"], confidence=nodes[receipt["node_id"]]["confidence"]))
            receipt["anchor_id"] = anchor

        elif kind == "LINK_DISTANT_NODES":
            source, target = str(op.get("source_id") or ""), str(op.get("target_id") or "")
            if source not in nodes or target not in nodes:
                raise ValueError("PATCH_LINK_NODE_NOT_FOUND")
            ekind = str(op.get("edge_kind") or "ASSOCIATES_WITH")
            edge = make_edge(source, target, ekind, axis=str(op.get("axis") or "D4_ASSOCIATIVE"), confidence=str(op.get("confidence") or "LOW"), metadata=copy.deepcopy(op.get("metadata") or {}))
            if edge["id"] not in edges:
                out["edges"].append(edge)
            receipt["edge_id"] = edge["id"]

        elif kind == "ANNOTATE_NODE":
            target = str(op.get("target_id") or "")
            if target not in nodes:
                raise ValueError(f"PATCH_NODE_NOT_FOUND:{target}")
            annotation = copy.deepcopy(op.get("annotation") or {})
            nodes[target].setdefault("metadata", {}).setdefault("annotations", []).append(annotation)
            receipt["target_id"] = target

        elif kind == "ANNOTATE_EDGE":
            target = str(op.get("target_id") or "")
            if target not in edges:
                raise ValueError(f"PATCH_EDGE_NOT_FOUND:{target}")
            annotation = copy.deepcopy(op.get("annotation") or {})
            edges[target].setdefault("metadata", {}).setdefault("annotations", []).append(annotation)
            receipt["target_id"] = target

        out["patch_log"].append(receipt)

    return out


def hemisphere_view(graph: dict[str, Any], hemisphere: str) -> dict[str, Any]:
    if hemisphere == "LEFT_HRAIN":
        allowed_axes = {"D1_FORWARD", "D2_REVERSE", "D3_STRUCTURAL", "D5_SPIRAL_ABSTRACTION"}
        role = "STRUCTURAL_CONTEXT"
    elif hemisphere == "RIGHT_INAIHR":
        allowed_axes = {"D1_FORWARD", "D2_REVERSE", "D4_ASSOCIATIVE", "D5_SPIRAL_ABSTRACTION"}
        role = "ASSOCIATIVE_CONTEXT"
    else:
        raise ValueError("UNKNOWN_HEMISPHERE")

    selected = [n for n in graph["nodes"] if n["axis"] in allowed_axes]
    ids = {n["id"] for n in selected}
    nodes = [
        {"id": n["id"], "label": n["label"], "origin": n["origin"], "type": n["kind"]}
        for n in selected
    ]
    links = [
        {"source": e["source"], "target": e["target"]}
        for e in graph["edges"] if e["source"] in ids and e["target"] in ids
    ]
    return {
        "hemisphere": hemisphere,
        "role": role,
        "workspace": {"nodes": nodes, "links": links},
        "control": {
            "read_only_transfer": True,
            "direct_cross_hemisphere_mutation": False,
            "automatic_graph_merge": False,
            "authority_delta": 0,
            "mass_effect_budget_delta": 0,
        },
    }


def disagreement_view(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_ids = {n["id"] for n in left["workspace"]["nodes"]}
    right_ids = {n["id"] for n in right["workspace"]["nodes"]}
    return {
        "schema": "janus.deep_analysis_5d.disagreement.v1",
        "shared_node_ids": sorted(left_ids & right_ids),
        "left_only_node_ids": sorted(left_ids - right_ids),
        "right_only_node_ids": sorted(right_ids - left_ids),
        "agreement_is_truth": False,
        "disagreement_must_be_preserved": True,
        "automatic_merge": False,
    }


def run(payload: dict[str, Any], patch_operations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    graph, forward, reverse, recovered = build_base_graph(payload)
    if patch_operations:
        graph = apply_patch_operations(graph, patch_operations)

    left = hemisphere_view(graph, "LEFT_HRAIN")
    right = hemisphere_view(graph, "RIGHT_INAIHR")
    disagreement = disagreement_view(left, right)

    recovered_at_origin = [
        {
            "recovery_id": item["recovery_id"],
            "finding": item["finding"],
            "source_segment_ids": item["source_segment_ids"],
            "confidence": item["confidence"],
            "discovery_axis": "D2_REVERSE",
            "validation_status": "SUPPORTED_BY_SOURCE_TRACE_NOT_WORLD_TRUTH",
        }
        for item in recovered
    ]
    # Patches may explicitly mark a new node as RECOVERED_AT_ORIGIN.
    for node in graph["nodes"]:
        if node["kind"] == "RECOVERED_AT_ORIGIN" and node["axis"] != "D2_REVERSE":
            recovered_at_origin.append({
                "recovery_id": node["id"],
                "finding": node["label"],
                "source_segment_ids": node["source_segment_ids"],
                "confidence": node["confidence"],
                "discovery_axis": node["axis"],
                "validation_status": node["validation_status"],
            })

    output: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "message_id": payload.get("message_id"),
        "analysis_mode": "DEEP_TRANSCEPTION_5D",
        "recovered_at_origin": recovered_at_origin,
        "answer": {
            "status": "READY_FOR_AGENT_ANSWER",
            "instruction": "Consume the five-axis structured graph and render recovered_at_origin before the main answer. Do not expose private free-form chain-of-thought; cite graph nodes/relations and evidence instead.",
        },
        "axes": {
            "D1_FORWARD": forward,
            "D2_REVERSE": reverse,
            "D3_STRUCTURAL": {"hemisphere": "LEFT_HRAIN", "graph_projection": "hemisphere_views.hrain"},
            "D4_ASSOCIATIVE": {"hemisphere": "RIGHT_INAIHR", "graph_projection": "hemisphere_views.inaihr", "association_is_evidence": False},
            "D5_SPIRAL_ABSTRACTION": {"origin_prime_requires_gate": True, "state_must_advance": True, "return_is_reset": False},
        },
        "graph": graph,
        "hemisphere_views": {
            "hrain": left,
            "inaihr": right,
            "demihead_disagreement": disagreement,
        },
        "provenance": {
            "protocol_id": PROTOCOL_ID,
            "parent_protocol": "JANUS_JSON_MIRROR_PASS_PROTOCOL_v1.0",
            "source": payload.get("source"),
            "intent_id": payload.get("intent_id"),
            "session_id": payload.get("session_id"),
            "generation": payload.get("generation"),
            "patch_count": len(graph["patch_log"]),
            "raw_private_chain_of_thought_stored": False,
        },
        "integrity": {
            "authoritative_text_sha256": sha256(payload["text"]),
            "graph_sha256": sha256(graph),
        },
    }
    output["integrity"]["output_sha256_without_self"] = sha256(output)
    return output


def _load_json(path: str | None) -> Any:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="JANUS 5D deep-analysis graph reference engine")
    parser.add_argument("input", nargs="?", help="janus.mirror.input.v1 JSON; stdin when omitted")
    parser.add_argument("--patch", help="Optional JSON file containing an array of graph patch operations")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    try:
        payload = _load_json(args.input)
        if not isinstance(payload, dict):
            raise ValueError("INPUT_JSON_OBJECT_REQUIRED")
        patches = _load_json(args.patch) if args.patch else None
        if patches is not None and not isinstance(patches, list):
            raise ValueError("PATCH_JSON_ARRAY_REQUIRED")
        result = run(payload, patches)
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    except Exception as exc:
        sys.stderr.write(f"janus_json_5d_deep: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
