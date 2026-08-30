from __future__ import annotations

import copy

from tools.terminal_response_relay import canonical_hash, markdown, verify_response


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


def test_valid_response_is_admitted_for_local_terminal_relay():
    value = response()
    assert verify_response(value)
    text = markdown(value)
    assert "JANUS ONLINE" in text
    assert value["resident_uuid"] in text
    assert value["model_digest"] in text
    assert value["file_fabric_digest"] in text
    assert value["turn_id"] in text
    assert f"JANUS_RESPONSE_ID:{value['response_id']}" in text


def test_tampered_response_never_reaches_terminal_issue():
    value = response()
    bad = copy.deepcopy(value)
    bad["response_text"] = "tampered"
    assert verify_response(bad) is False


def test_response_cannot_relay_effect_authority():
    value = response()
    bad = copy.deepcopy(value)
    bad["external_effect_authorized"] = True
    bad["response_hash"] = canonical_hash({k: v for k, v in bad.items() if k != "response_hash"})
    assert verify_response(bad) is False


def test_non_issue_conversation_id_is_rejected():
    value = response()
    bad = copy.deepcopy(value)
    bad["conversation_id"] = "freeform-channel"
    bad["response_hash"] = canonical_hash({k: v for k, v in bad.items() if k != "response_hash"})
    assert verify_response(bad) is False
