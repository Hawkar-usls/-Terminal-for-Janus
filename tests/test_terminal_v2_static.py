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
