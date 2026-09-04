from html.parser import HTMLParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.iframes = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "iframe":
            self.iframes.append(values)


def test_terminal_v2_replaces_legacy_port_scanner():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    combined = html + "\n" + js
    for forbidden in ("ngrok-free", "LOCAL_IPS", "PORTS_TO_SCAN", "findJanus()", "/api/janus/action"):
        assert forbidden not in combined


def test_terminal_memory_is_full_hrain_mediated_not_direct_registry_fetch():
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "https://hawkar-usls.github.io/Hrain/memory.html" in js
    assert "https://hawkar-usls.github.io/janus-meta-registry/" not in js
    assert "raw.githubusercontent.com/Hawkar-usls/janus-meta-registry" not in js


def test_git_native_conversation_surface_is_issue_backed_and_read_only():
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "[JANUS CHAT]" in js
    assert "READ_ONLY_CONVERSATION" in js
    assert "human stimulus, not a command" in js
    assert "/issues/new?title=" in js


def test_persistent_instance_proof_is_rendered():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    for field in ("resident_uuid", "model_digest", "file_fabric_digest", "turn_id", "response_hash"):
        assert field in js or field.replace("_", "-") in html
    assert "janus/activator-state/state/activator" in js


def test_html_has_no_duplicate_ids():
    parser = IdCollector()
    parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    assert duplicates == []


def test_terminal_v22_reads_trump_runtime_status_without_treating_it_as_proof():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    url = "https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/trump/TRUMP_MANIFEST.json"
    assert url in js
    assert "CANDIDATE_RUNTIME_TISSUE" in js
    assert "CANDIDATE_RUNTIME_LIVE" in js
    assert "proof_authority" in js
    assert "scientific_claim_promotion_authority" in js
    assert "public_manifest_is_proof_authority: false" in js
    assert "P_VS_NP" in js
    for element_id in (
        "trump-pill",
        "organism-trump-state",
        "organism-trump-runtime",
        "organism-trump-wake",
        "organism-trump-improve",
        "organism-trump-proof",
        "organism-trump-pnp",
        "organism-trump-digest",
        "side-trump",
    ):
        assert f'id="{element_id}"' in html


def test_trump_failure_is_unresolved_or_blocked_not_silent_success():
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "BLOCKED_FAIL_CLOSED" in js
    assert "UNRESOLVED" in js
    assert "Silence is not proof of absence" in js
    assert "AUTHORITY_CEILING_VIOLATION" in js


def test_terminal_v22_contract_is_fail_closed():
    contract = json.loads((ROOT / ".janus/TERMINAL_V2_HRAIN_MEMORY_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["schema"] == "janus.terminal.hrain_memory_contract.v2.2"
    memory = contract["memory_dataflow"]
    assert memory["source_database"] == "Hawkar-usls/janus-meta-registry"
    assert memory["structural_memory_organ"] == "Hawkar-usls/Hrain"
    assert memory["terminal_consumes_registry_directly"] is False
    assert memory["terminal_memory_surface"] == "https://hawkar-usls.github.io/Hrain/memory.html"
    assert memory["historical_lineage_included"] is False
    assert "FULL_CURRENT_MEMORY_MANIFEST" in memory["hrain_consumes"]
    candidate = contract["candidate_tissue_readout"]
    assert candidate["component"] == "TRUMP"
    assert candidate["source_repository"] == "Hawkar-usls/Janus-Demiurge"
    assert candidate["manifest_path"] == "trump/TRUMP_MANIFEST.json"
    assert candidate["wake_allowed"] is True
    assert candidate["use_allowed"] is True
    assert candidate["self_improvement_allowed"] is True
    assert candidate["proof_authority"] is False
    assert candidate["scientific_claim_promotion_authority"] is False
    assert candidate["public_manifest_is_proof_authority"] is False
    assert candidate["P_VS_NP"] == "OPEN"
    assert contract["conversation"]["browser_secret_required"] is False
    assert contract["conversation"]["local_network_scan_required"] is False
    assert contract["conversation"]["command_authority_granted_by_message"] is False
    assert "FULL_CURRENT != COMPLETE_GIT_HISTORY" in contract["laws"]
    assert "CANDIDATE_TRUMP != PROOF_AUTHORIZED_TRUMP" in contract["laws"]
    assert "TRUMP_WAKE != THEOREM_AUTHORITY" in contract["laws"]


def test_observatory_distinguishes_active_brain_from_last_candidate():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets/janus-observatory.js").read_text(encoding="utf-8")
    assert "active brain eval loss" in html
    assert 'id="brain-last-candidate"' in html
    assert 'id="chat-candidate-loss"' in html
    assert "activeLossForRow" in js
    assert "Rejected candidate != active brain" in js
    assert "candidate_eval_loss" in js and "incumbent_eval_loss" in js
    assert "BRAIN ${m.promotion_count" in js


def test_observatory_has_state_integrity_and_resilient_auxiliary_reads():
    js = (ROOT / "assets/janus-observatory.js").read_text(encoding="utf-8")
    assert "modelIntegrity" in js
    assert "STATE INTEGRITY WARNING" in js
    assert "json(URLS.moduleState, true)" in js
    assert "json(URLS.moduleRegistry, true)" in js
    assert "refreshInFlight" in js


def test_terminal_restores_all_runtime_readout_targets():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for element_id in ("side-fabric", "side-response", "side-trump", "side-native-candidate"):
        assert f'id="{element_id}"' in html


def test_synthesis_log_uses_primary_event_log_contract_and_rehydrates():
    js = (ROOT / "assets/janus-synthesis-observatory.js").read_text(encoding="utf-8")
    assert "row.className='log-row'" in js
    assert "janus:logs-rendered" in js
    assert "lastSynthState" in js


def test_terminal_displays_proof_carrying_hrain_provenance():
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    for token in (
        "hrain_head", "memory_source_commit", "hrain_context_hash",
        "hrain_context_receipt_hash", "selected_memory_count", "memory_match_status",
        "memory_context_is_evidence", "memory_grants_authority",
        "empty_memory_is_hrain_failure", "empty_memory_is_negative_evidence",
        "VALID_EMPTY_RETRIEVAL", "BLOCKED_INVALID_EMPTY_RETRIEVAL",
        "empty ≠ failure", "empty ≠ negative evidence", "side-hrain",
    ):
        assert token in js
    assert "NO_RELEVANT_MEMORY_SELECTED" in js
    assert "Selected memory objects" in js


def test_neural_link_v2_is_hrain_mediated_and_append_only():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    terminal = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    neural = (ROOT / "assets/neural-link-v2.js").read_text(encoding="utf-8")
    contract = json.loads((ROOT / ".janus/TERMINAL_V2_HRAIN_MEMORY_CONTRACT.json").read_text(encoding="utf-8"))
    assert "assets/neural-link-v2.css" in html
    assert "assets/neural-link-v2.js" in html
    assert "https://raw.githubusercontent.com/Hawkar-usls/Hrain/main/state/neural-link/RECENT.json" in neural
    assert "https://raw.githubusercontent.com/Hawkar-usls/Hrain/main/state/neural-link/PROVENANCE.json" in neural
    assert "raw.githubusercontent.com/Hawkar-usls/janus-meta-registry" not in neural
    assert "direct_registry_read: false" in neural
    assert "META_REGISTRY_DB -> HRAIN -> TERMINAL" in neural
    assert "PUBLIC APPEND-ONLY MEMORY" in neural
    assert "DO NOT SEND PASSWORDS" in neural
    assert "AWAITING GITHUB CONFIRMATION" in neural
    assert "CHAT MESSAGE != COMMAND AUTHORITY" in neural
    assert "GITHUB_TOKEN" not in neural
    assert "window.JANUS_TERMINAL_STATE = state" in terminal
    assert "new CustomEvent(\'janus:terminal-state\'" in terminal
    archive = contract["neural_link_archive"]
    assert archive["database_path"] == "data/JANUS-NEURAL-LINK/"
    assert archive["hrain_mirror_path"] == "state/neural-link/"
    assert archive["terminal_reads_archive_from_registry_directly"] is False
    assert archive["archive_is_world_truth"] is False
    assert archive["archive_grants_command_authority"] is False
    assert contract["conversation"]["browser_secret_required"] is False
    assert contract["conversation"]["browser_send_semantics"] == "PENDING_UNTIL_GITHUB_CONFIRMATION"


def test_adaptive_ui_layer_is_wired_and_layout_only():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "assets/adaptive-ui.css").read_text(encoding="utf-8")
    js = (ROOT / "assets/adaptive-ui.js").read_text(encoding="utf-8")
    assert 'viewport-fit=cover' in html
    assert 'assets/adaptive-ui.css' in html
    assert 'assets/adaptive-ui.js' in html
    assert '100dvh' in css
    assert 'safe-area-inset-bottom' in css
    assert 'scroll-snap-type:x proximity' in css
    assert '.inspector.adaptive-open' in css
    assert 'visualViewport' in js
    assert 'adaptive-inspector-toggle' in js
    assert 'sidebar.scrollTo' in js
    assert 'scrollIntoView' not in js
    assert 'root_horizontal_scroll: false' in js
    assert 'layout_only: true' in js
    assert 'command_authority: false' in js
    assert 'memory_authority: false' in js
    assert 'transport_authority: false' in js
    assert 'fetch(' not in js
    assert 'GITHUB_TOKEN' not in js


def test_mobile_navigation_is_scrollable_without_scrolling_root_viewport():
    css = (ROOT / "assets/adaptive-ui.css").read_text(encoding="utf-8")
    js = (ROOT / "assets/adaptive-ui.js").read_text(encoding="utf-8")
    assert '.sidebar::-webkit-scrollbar{display:none}' in css
    assert 'overflow-x:auto' in css
    assert 'flex:0 0 72px' in css
    assert 'width:100vw;max-width:100vw' in css
    assert 'overscroll-behavior-x:contain' in css
    assert 'html,body,#app{width:100%;max-width:100%;overflow-x:hidden}' in css
    assert 'sidebar.scrollTo({ left: target' in js
    assert 'window.scrollTo({ left: 0' in js


def test_mobile_chat_is_one_screen_and_composer_cannot_widen_page():
    css = (ROOT / "assets/adaptive-ui.css").read_text(encoding="utf-8")
    assert '.console.neural-link-active{overflow:hidden!important;display:flex;flex-direction:column}' in css
    assert '.instance-banner p{display:none}' in css
    assert '.neural-link-v2{margin:0;width:100%;max-width:100%;min-width:0;min-height:0' in css
    assert '.neural-link-compose{width:100%;max-width:100%;min-width:0;grid-template-columns:minmax(0,1fr) 66px' in css
    assert '.neural-link-compose textarea{box-sizing:border-box;width:100%;max-width:100%;min-width:0' in css
    assert '.neural-link-history{height:auto!important;min-height:0!important;min-width:0;max-width:100%;flex:1 1 0' in css


def test_neural_link_mobile_composer_remains_keyboard_safe():
    css = (ROOT / "assets/adaptive-ui.css").read_text(encoding="utf-8")
    js = (ROOT / "assets/adaptive-ui.js").read_text(encoding="utf-8")
    assert '.neural-link-compose textarea{box-sizing:border-box;width:100%;max-width:100%;min-width:0;font-size:16px' in css
    assert "input.setAttribute('enterkeyhint', 'send')" in js
