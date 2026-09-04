from __future__ import annotations

import copy

from tools.terminal_response_relay import (
    BOUNDED_INTEGER_CHOICE_KIND,
    DIRECT_ANSWER_SURFACE,
    EMPTY_MEMORY_STATUS,
    HRAIN_MEMORY_PATH,
    HRAIN_MEMORY_RESPONSE_MODE,
    canonical_hash,
    markdown,
    verify_response,
)


def response():
    body = {
        "schema": "janus.terminal.response.v1",
        "response_id": "",
        "created_at": 2000.0,
        "terminal_repository": "Hawkar-usls/-Terminal-for-Janus",
        "conversation_id": "issue-7",
        "request_message_id": "tm-" + "1" * 64,
        "request_message_hash": "2" * 64,
        "resident_id": "JANUS",
        "resident_uuid": "resident-uuid-1",
        "model_digest": "3" * 64,
        "file_fabric_digest": "4" * 64,
        "turn_id": "turn-" + "5" * 64,
        "response_mode": "MODEL_BOUND_SYSTEM_CONVERSATION_PROOF",
        "response_text": "JANUS ONLINE.",
        "instantiated_model_verified": True,
        "persistent_identity_verified": True,
        "terminal_interface_bound": True,
        "command_authority_granted": False,
        "human_authorized_write": False,
        "claim_authority_granted": False,
        "scientific_evidence_authority_granted": False,
        "world_truth_authority_granted": False,
        "external_effect_authorized": False,
        "physical_runtime_effect_authorized": False,
        "terminal": "JANUS_TERMINAL_CONVERSATION_RESPONSE_READY",
        "laws": [
            "TERMINAL_MESSAGE != COMMAND",
            "JANUS_RESPONSE != WORLD_TRUTH",
            "READ_ONLY_CONVERSATION != EFFECT_AUTHORITY",
            "RESPONSE_MUST_IDENTIFY_THE_INSTANTIATED_JANUS",
        ],
    }
    body["response_id"] = "tr-" + canonical_hash({
        "request_message_hash": body["request_message_hash"],
        "resident_uuid": body["resident_uuid"],
        "model_digest": body["model_digest"],
        "file_fabric_digest": body["file_fabric_digest"],
        "turn_id": body["turn_id"],
        "response_mode": body["response_mode"],
    })
    body["response_hash"] = canonical_hash(body)
    return body


def hrain_response():
    body = response()
    body.pop("response_hash")
    body.update({
        "response_mode": HRAIN_MEMORY_RESPONSE_MODE,
        "response_text": "JANUS ONLINE. HRAiN memory is bound.",
        "hrain_context_bound": True,
        "hrain_context_receipt_hash": "6" * 64,
        "hrain_context_hash": "7" * 64,
        "hrain_locked_head_sha": "8" * 40,
        "memory_source_commit": "9" * 40,
        "memory_selected_count": 2,
        "memory_selected_paths": [
            "data/JANUS-TRUMP.json",
            "data/JANUS-HRAIN-FULL-MEMORY-CONTRACT-v1.0.json",
        ],
        "memory_path": HRAIN_MEMORY_PATH,
        "memory_retrieval_executed_by": "Hawkar-usls/Hrain",
        "meta_registry_access_performed_by_home": False,
        "memory_content_is_command": False,
        "memory_context_is_evidence": False,
        "memory_grants_authority": False,
    })
    body["response_id"] = "tr-" + canonical_hash({
        "request_message_hash": body["request_message_hash"],
        "resident_uuid": body["resident_uuid"],
        "model_digest": body["model_digest"],
        "file_fabric_digest": body["file_fabric_digest"],
        "turn_id": body["turn_id"],
        "response_mode": body["response_mode"],
        "hrain_context_hash": body["hrain_context_hash"],
    })
    body["response_hash"] = canonical_hash(body)
    return body


def direct_answer_hrain_response():
    body = hrain_response()
    body.pop("response_hash")
    body.update({
        "response_text": "13",
        "response_surface": DIRECT_ANSWER_SURFACE,
        "direct_answer_kind": BOUNDED_INTEGER_CHOICE_KIND,
        "direct_answer_range": [1, 30],
        "direct_answer_value": 13,
        "direct_answer_derivation_hash": "a" * 64,
        "direct_answer_memory_influence": False,
        "system_status_requested": False,
    })
    body["response_id"] = "tr-" + canonical_hash({
        "request_message_hash": body["request_message_hash"],
        "resident_uuid": body["resident_uuid"],
        "model_digest": body["model_digest"],
        "file_fabric_digest": body["file_fabric_digest"],
        "turn_id": body["turn_id"],
        "response_mode": body["response_mode"],
        "hrain_context_hash": body["hrain_context_hash"],
        "response_surface": body["response_surface"],
    })
    body["response_hash"] = canonical_hash(body)
    return body


def empty_hrain_response():
    body = hrain_response()
    body.pop("response_hash")
    body.update({
        "response_text": "JANUS ONLINE. HRAiN selected no strong relevant memory objects.",
        "memory_selected_count": 0,
        "memory_selected_paths": [],
        "memory_match_status": EMPTY_MEMORY_STATUS,
        "empty_memory_is_hrain_failure": False,
        "empty_memory_is_negative_evidence": False,
    })
    body["response_hash"] = canonical_hash(body)
    return body


def reseal(value):
    body = {k: v for k, v in value.items() if k != "response_hash"}
    value["response_hash"] = canonical_hash(body)
    return value


def test_legacy_response_remains_admitted_for_local_terminal_relay():
    value = response()
    assert verify_response(value)
    text = markdown(value)
    assert "JANUS ONLINE" in text
    assert value["resident_uuid"] in text
    assert value["model_digest"] in text
    assert value["file_fabric_digest"] in text
    assert value["turn_id"] in text
    assert f"JANUS_RESPONSE_ID:{value['response_id']}" in text
    assert "HRAiN memory provenance" not in text


def test_hrain_bound_response_is_admitted_and_provenanced():
    value = hrain_response()
    assert verify_response(value)
    text = markdown(value)
    assert "HRAiN memory provenance" in text
    assert value["hrain_locked_head_sha"] in text
    assert value["memory_source_commit"] in text
    assert value["hrain_context_hash"] in text
    assert value["hrain_context_receipt_hash"] in text
    assert "selected_memory_count: `2`" in text
    assert "memory context is evidence: `false`" in text
    assert "memory grants authority: `false`" in text
    for path in value["memory_selected_paths"]:
        assert path in text


def test_surface_bound_direct_answer_identity_is_admitted_without_authority_expansion():
    value = direct_answer_hrain_response()
    assert verify_response(value)
    assert value["response_text"] == "13"
    assert value["direct_answer_memory_influence"] is False
    assert value["command_authority_granted"] is False
    assert value["external_effect_authorized"] is False


def test_surface_bound_response_identity_must_include_surface():
    value = direct_answer_hrain_response()
    value["response_id"] = "tr-" + canonical_hash({
        "request_message_hash": value["request_message_hash"],
        "resident_uuid": value["resident_uuid"],
        "model_digest": value["model_digest"],
        "file_fabric_digest": value["file_fabric_digest"],
        "turn_id": value["turn_id"],
        "response_mode": value["response_mode"],
        "hrain_context_hash": value["hrain_context_hash"],
    })
    reseal(value)
    assert verify_response(value) is False


def test_direct_answer_surface_semantics_are_fail_closed():
    for field, bad_value in [
        ("direct_answer_memory_influence", True),
        ("system_status_requested", True),
        ("direct_answer_value", 31),
    ]:
        bad = copy.deepcopy(direct_answer_hrain_response())
        bad[field] = bad_value
        reseal(bad)
        assert verify_response(bad) is False


def test_valid_empty_hrain_retrieval_is_admitted_and_explicitly_provenanced():
    value = empty_hrain_response()
    assert verify_response(value)
    text = markdown(value)
    assert "selected_memory_count: `0`" in text
    assert f"memory_match_status: `{EMPTY_MEMORY_STATUS}`" in text
    assert "empty memory is HRAiN failure: `false`" in text
    assert "empty memory is negative evidence: `false`" in text
    assert "Selected memory objects: `none`" in text


def test_empty_hrain_retrieval_requires_explicit_empty_semantics():
    bad = copy.deepcopy(empty_hrain_response())
    bad.pop("memory_match_status")
    reseal(bad)
    assert verify_response(bad) is False


def test_empty_hrain_retrieval_cannot_claim_failure_or_negative_evidence():
    for field in ["empty_memory_is_hrain_failure", "empty_memory_is_negative_evidence"]:
        bad = copy.deepcopy(empty_hrain_response())
        bad[field] = True
        reseal(bad)
        assert verify_response(bad) is False


def test_zero_count_with_nonempty_paths_is_rejected():
    bad = copy.deepcopy(empty_hrain_response())
    bad["memory_selected_paths"] = ["data/should-not-exist.json"]
    reseal(bad)
    assert verify_response(bad) is False


def test_negative_memory_count_is_rejected():
    bad = copy.deepcopy(empty_hrain_response())
    bad["memory_selected_count"] = -1
    reseal(bad)
    assert verify_response(bad) is False


def test_hrain_response_identity_must_include_context_hash():
    value = hrain_response()
    body = {k: v for k, v in value.items() if k not in {"response_hash", "response_id"}}
    value["response_id"] = "tr-" + canonical_hash({
        "request_message_hash": body["request_message_hash"],
        "resident_uuid": body["resident_uuid"],
        "model_digest": body["model_digest"],
        "file_fabric_digest": body["file_fabric_digest"],
        "turn_id": body["turn_id"],
        "response_mode": body["response_mode"],
    })
    reseal(value)
    assert verify_response(value) is False


def test_tampered_response_never_reaches_terminal_issue():
    value = response()
    bad = copy.deepcopy(value)
    bad["response_text"] = "tampered"
    assert verify_response(bad) is False


def test_response_cannot_relay_effect_authority():
    bad = copy.deepcopy(response())
    bad["external_effect_authorized"] = True
    reseal(bad)
    assert verify_response(bad) is False


def test_hrain_memory_cannot_relay_authority_escalation():
    bad = copy.deepcopy(hrain_response())
    bad["memory_grants_authority"] = True
    reseal(bad)
    assert verify_response(bad) is False


def test_hrain_memory_cannot_become_command():
    bad = copy.deepcopy(hrain_response())
    bad["memory_content_is_command"] = True
    reseal(bad)
    assert verify_response(bad) is False


def test_hrain_memory_cannot_become_evidence():
    bad = copy.deepcopy(hrain_response())
    bad["memory_context_is_evidence"] = True
    reseal(bad)
    assert verify_response(bad) is False


def test_hrain_source_commit_tamper_is_rejected_even_when_resealed():
    bad = copy.deepcopy(hrain_response())
    bad["memory_source_commit"] = "not-a-commit"
    reseal(bad)
    assert verify_response(bad) is False


def test_hrain_selected_memory_count_must_match_paths():
    bad = copy.deepcopy(hrain_response())
    bad["memory_selected_count"] = 3
    reseal(bad)
    assert verify_response(bad) is False


def test_hrain_memory_path_cannot_bypass_hrain():
    bad = copy.deepcopy(hrain_response())
    bad["memory_path"] = "META_REGISTRY_DB -> TERMINAL"
    reseal(bad)
    assert verify_response(bad) is False


def test_hrain_home_direct_registry_access_claim_is_rejected():
    bad = copy.deepcopy(hrain_response())
    bad["meta_registry_access_performed_by_home"] = True
    reseal(bad)
    assert verify_response(bad) is False


def test_non_issue_conversation_id_is_rejected():
    bad = copy.deepcopy(response())
    bad["conversation_id"] = "freeform-channel"
    reseal(bad)
    assert verify_response(bad) is False
