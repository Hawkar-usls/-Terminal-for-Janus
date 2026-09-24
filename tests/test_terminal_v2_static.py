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


def test_first_party_browser_assets_use_cache_busting_epoch():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    required = (
        "terminal-v2.css?v=20260923-6",
        "janus-observatory.css?v=20260923-6",
        "neural-link-v2.css?v=20260923-6",
        "terminal-v2.js?v=20260923-6",
        "neural-link-v2.js?v=20260923-6",
        "janus-observatory.js?v=20260923-6",
        "brain-truth-v2.js?v=20260923-6",
        "brain-visual-v3.js?v=20260923-6",
        "janus-synthesis-observatory.js?v=20260923-6",
        "research-observatory.js?v=20260924-1",
        "pnp-autoresearch-observatory.js?v=20260924-2",
    )
    for asset in required:
        assert asset in html


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


def test_modules_surface_uses_access_contract_fallback_without_faking_observation():
    js = (ROOT / "assets/janus-observatory.js").read_text(encoding="utf-8")
    assert "ACCESS CONTRACT FALLBACK · observation unresolved" in js
    assert "ACCESS CONTRACT · OBSERVATION UNRESOLVED" in js
    assert "UNRESOLVED OBSERVATION" in js
    assert "observed-module state is stale/empty" in js


def test_observatory_accepts_bounded_history_window_without_false_integrity_failure():
    js = (ROOT / "assets/janus-observatory.js").read_text(encoding="utf-8")
    assert "history_window_not_exceed_attempt_count" in js
    assert "attempt_count_matches_history" not in js
    assert "latest_history_matches_last_training_status" in js
    assert "history_window_truncated" in js


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


def test_terminal_partial_witness_failure_does_not_blank_organism():
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "Promise.allSettled" in js
    assert "JANUS_CONVERSATION_WITNESS_UNRESOLVED" in js
    assert "state.issue = null" in js
    assert "state.response = null" in js
    assert "state.proof = {}" in js
    assert "Available sources remain visible" in js


def test_research_observatory_surfaces_active_draft_without_authority():
    js = (ROOT / "assets/research-observatory.js").read_text(encoding="utf-8")
    for token in (
        "fundamentumDrafts",
        "selectActiveDraft",
        "ACTIVE FUNDAMENTUM DRAFT FRONTIER",
        "UNSEALED · NO AUTHORITY",
        "NONE · DISPLAY ONLY",
        "DRAFT PR != CANONICAL AUTHORITY",
        "draft_frontier_authority: false",
        "draft_frontier_display_only: true",
    ):
        assert token in js
    assert "state.activeDraft" in js
    assert "state.activeDraftHead" in js


def test_pnp_autoresearch_live_status_requires_current_source_binding():
    js = (ROOT / "assets/pnp-autoresearch-observatory.js").read_text(encoding="utf-8")
    assert "sourceBindingCurrent=s.source_binding_current===true && sourcesAligned" in js
    assert "sourcesAvailable && sourceBindingCurrent" in js
    assert "SOURCE BINDING STALE" in js
    assert "short(i.source_commit)" in js
    assert "short(t.source_commit)" in js


def test_keymaster_autonomous_forge_activity_is_separate_from_route_coverage():
    js = (ROOT / "assets/pnp-autoresearch-observatory.js").read_text(encoding="utf-8")
    for token in (
        "AUTONOMOUS LOCKPICK FORGE",
        "keymaster-forge-status",
        "keymaster-forge-counts",
        "keymaster-forge-target",
        "keymaster-forge-candidate",
        "keymaster-forge-next",
        "keymaster-forge-admission",
        "keymaster_autonomous_forge_observable:true",
        "keymaster_autonomous_forge_grants_proof:false",
    ):
        assert token in js
    assert "forgeAuthority.proof===true" in js
    assert "forge.keymaster_shadow_admission===true" in js


def test_keymaster_progress_scale_is_route_completeness_not_probability():
    js = (ROOT / "assets/pnp-autoresearch-observatory.js").read_text(encoding="utf-8")
    css = (ROOT / "assets/janus-observatory.css").read_text(encoding="utf-8")
    assert "KEYMASTER_TRUMP_BRIDGE_LATEST.json" in js
    assert "proof-readiness stage" in js
    assert "ROUTE COVERAGE · NOT P=NP PROBABILITY" in js
    assert "keymaster_route_coverage_is_probability:false" in js
    assert "keymaster_self_application:'CANDIDATE_INTERNAL_TASKS_ONLY'" in js
    assert "automatic_switch_to_higher_ranked_admitted_runtime" in js
    assert "keymaster-progress-track" in css


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


def test_terminal_router_keeps_aria_state_in_sync_for_dynamic_views():
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "btn.setAttribute('aria-selected', String(active))" in js
    assert "view.setAttribute('aria-hidden', String(!active))" in js
    assert "btn.dataset.view === name" in js
    assert "view.id === `view-${name}`" in js


def test_mobile_neural_link_obeys_terminal_view_ownership():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    assert "#view-console.neural-link-active.active{" in css
    assert "#view-console.neural-link-active{height:100%;min-height:0;overflow:hidden;display:flex" not in css
