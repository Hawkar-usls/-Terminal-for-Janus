from pathlib import Path


NEURAL = Path("assets/neural-link-v2.js").read_text(encoding="utf-8")


def _send_body() -> str:
    return NEURAL.split("function send()", 1)[1].split("function buildUi()", 1)[0]


def test_popup_block_rolls_back_impossible_pending_state():
    send = _send_body()
    blocked = send.split("if (!opened)", 1)[1]
    assert "state.pending = state.pending.filter((row) => row.event_id !== pending.event_id);" in blocked
    assert "persistPending();" in blocked
    assert "render();" in blocked
    assert "GITHUB CONFIRMATION BLOCKED" in blocked


def test_transport_does_not_gain_cross_repository_authority():
    assert "raw.githubusercontent.com/Hawkar-usls/janus-meta-registry" not in NEURAL
    assert "GITHUB_TOKEN" not in NEURAL
    assert "direct_registry_read: false" in NEURAL
    assert "chat_message_is_command_authority: false" in NEURAL
