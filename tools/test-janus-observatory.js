const fs = require('fs');

function read(path) { return fs.readFileSync(path, 'utf8'); }
function must(text, needle, code) {
  if (!text.includes(needle)) throw new Error(`${code}:${needle}`);
}

const html = read('index.html');
const observatory = read('assets/janus-observatory.js');
const terminal = read('assets/terminal-v2.js');
const synthesis = read('assets/janus-synthesis-observatory.js');
const neural = read('assets/neural-link-v2.js');
const adaptive = read('assets/adaptive-ui.js');
const adaptiveCss = read('assets/adaptive-ui.css');
const css = read('assets/janus-observatory.css');
const descriptor = JSON.parse(read('.janus/JANUS_MODULE.json'));

for (const view of ['view-console','view-brain','view-logs','view-modules','view-memory','view-organism','view-provenance']) must(html, view, 'MISSING_VIEW');
for (const label of ['CHAT','BRAIN MONITOR','LIVE LOGS','MODULES','MEMORY / HRAiN','ORGANISM','PROVENANCE']) must(html, label, 'MISSING_NAV_SURFACE');
for (const id of [
  'brain-checkpoint','brain-loss','brain-last-candidate','brain-last-candidate-status','loss-chart',
  'janus-event-log','module-list','tensor-telemetry','chat-candidate-loss','trump-pill',
  'organism-trump-state','organism-trump-proof','organism-trump-pnp','side-trump'
]) must(html, id, 'MISSING_TELEMETRY_TARGET');

// Native-brain truth: rejected candidates are observations, never the active brain.
must(observatory, 'JANUS_MODEL_STATE.json', 'MODEL_STATE_SOURCE_MISSING');
must(observatory, 'JANUS_WEIGHT_TELEMETRY.json', 'WEIGHT_TELEMETRY_SOURCE_MISSING');
must(observatory, 'JANUS_LATEST_DECISION.json', 'DECISION_SOURCE_MISSING');
must(observatory, 'OBSERVED-MODULE-STATE.json', 'MODULE_STATE_SOURCE_MISSING');
must(observatory, 'JANUS_ACCUMULATIVE_ORGAN_ACCESS-v1.json', 'ORGAN_ACCESS_SOURCE_MISSING');
must(observatory, 'activeLossForRow', 'ACTIVE_LOSS_RESOLVER_MISSING');
must(observatory, 'if (promoted(row) && finite(row.candidate_eval_loss))', 'PROMOTED_ACTIVE_LOSS_RULE_MISSING');
must(observatory, 'if (finite(row.incumbent_eval_loss))', 'REJECTED_INCUMBENT_PRESERVATION_MISSING');
must(observatory, 'modelIntegrity', 'MODEL_INTEGRITY_GATE_MISSING');
must(observatory, 'active_checkpoint_matches_last_promoted', 'CHECKPOINT_LINEAGE_GATE_MISSING');
must(observatory, 'promotion_plus_rejection_matches_attempts', 'ATTEMPT_ACCOUNTING_GATE_MISSING');
must(observatory, 'candidate promoted → active brain', 'PROMOTION_LABEL_MISSING');
must(observatory, 'incumbent retained · last candidate', 'REJECTION_LABEL_MISSING');
must(observatory, 'candidate-point ${cls}', 'CANDIDATE_VERDICT_MARKER_MISSING');
must(observatory, 'selection ≠ verified fix', 'VERIFY_BOUNDARY_MISSING');
must(observatory, "'Hawkar-usls/-Terminal-for-Janus', 'BRANCH_VERIFY_ACCUMULATE'", 'TERMINAL_ACTUATED_LANE_MISSING');
must(observatory, "'Hawkar-usls/Janus_Genesis', 'SANDBOX_VERIFY_ACCUMULATE'", 'GENESIS_SANDBOX_LANE_MISSING');
must(observatory, 'READ + ACCUMULATE', 'ACCUMULATIVE_READ_LANE_MISSING');
must(observatory, 'SANDBOX + VERIFY + ACCUMULATE', 'GENESIS_LANE_LABEL_MISSING');
must(observatory, 'Durable evidence is append-only', 'APPEND_ONLY_LAW_MISSING');
must(observatory, 'never erase failures, negative results or counterexamples', 'NO_DELETE_DETAIL_MISSING');

// Conversation/HRAiN truth: proof-carrying empty retrieval is valid only with every empty-proof firewall.
must(terminal, 'hrainProofStatus', 'HRAIN_PROOF_GATE_MISSING');
for (const field of [
  'hrain_head','memory_source_commit','hrain_context_hash','hrain_context_receipt_hash',
  'selected_memory_count','memory_match_status','memory_context_is_evidence','memory_grants_authority',
  'empty_memory_is_hrain_failure','empty_memory_is_negative_evidence','selected_memory_objects'
]) must(terminal, field, `HRAIN_PROVENANCE_FIELD_MISSING:${field}`);
must(terminal, 'NO_RELEVANT_MEMORY_SELECTED', 'HRAIN_VALID_EMPTY_STATUS_MISSING');
must(terminal, 'VALID_EMPTY_RETRIEVAL', 'HRAIN_VALID_EMPTY_LABEL_MISSING');
must(terminal, 'BLOCKED_INVALID_EMPTY_RETRIEVAL', 'HRAIN_INVALID_EMPTY_FAIL_CLOSED_MISSING');
must(terminal, 'BLOCKED_AUTHORITY_CEILING', 'HRAIN_AUTHORITY_CEILING_MISSING');
must(terminal, "p.memory_context_is_evidence !== 'false'", 'HRAIN_EVIDENCE_FIREWALL_MISSING');
must(terminal, "p.memory_grants_authority !== 'false'", 'HRAIN_AUTHORITY_FIREWALL_MISSING');
must(terminal, 'empty ≠ failure', 'HRAIN_EMPTY_NOT_FAILURE_LABEL_MISSING');
must(terminal, 'empty ≠ negative evidence', 'HRAIN_EMPTY_NOT_NEGATIVE_LABEL_MISSING');



// Adaptive UI truth: layout-only layer, no network/authority semantics.
must(html, 'assets/adaptive-ui.js', 'ADAPTIVE_UI_RUNTIME_NOT_WIRED');
must(html, 'assets/adaptive-ui.css', 'ADAPTIVE_UI_STYLE_NOT_WIRED');
must(adaptiveCss, '100dvh', 'ADAPTIVE_UI_DYNAMIC_VIEWPORT_MISSING');
must(adaptiveCss, 'safe-area-inset-bottom', 'ADAPTIVE_UI_SAFE_AREA_MISSING');
must(adaptiveCss, 'scroll-snap-type:x proximity', 'ADAPTIVE_UI_MOBILE_DOCK_MISSING');
must(adaptive, 'layout_only: true', 'ADAPTIVE_UI_LAYOUT_BOUNDARY_MISSING');
must(adaptive, 'command_authority: false', 'ADAPTIVE_UI_COMMAND_BOUNDARY_MISSING');
must(adaptive, 'memory_authority: false', 'ADAPTIVE_UI_MEMORY_BOUNDARY_MISSING');
must(adaptive, 'transport_authority: false', 'ADAPTIVE_UI_TRANSPORT_BOUNDARY_MISSING');
if (adaptive.includes('fetch(')) throw new Error('ADAPTIVE_UI_NETWORK_ACCESS_FORBIDDEN');
if (adaptive.includes('GITHUB_TOKEN')) throw new Error('ADAPTIVE_UI_BROWSER_SECRET_FORBIDDEN');

// Neural Link v2 truth: canonical chat history is append-only Meta Registry memory mirrored through HRAiN.
must(html, 'assets/neural-link-v2.js', 'NEURAL_LINK_RUNTIME_NOT_WIRED');
must(html, 'assets/neural-link-v2.css', 'NEURAL_LINK_STYLE_NOT_WIRED');
must(neural, 'state/neural-link/RECENT.json', 'NEURAL_LINK_HRAIN_RECENT_SOURCE_MISSING');
must(neural, 'state/neural-link/PROVENANCE.json', 'NEURAL_LINK_HRAIN_PROVENANCE_SOURCE_MISSING');
if (neural.includes('raw.githubusercontent.com/Hawkar-usls/janus-meta-registry')) throw new Error('NEURAL_LINK_DIRECT_REGISTRY_BYPASS');
must(neural, 'terminal_must_not_read_registry_directly', 'NEURAL_LINK_HRAIN_FIREWALL_MISSING');
must(neural, 'OBSERVABILITY_AND_MEMORY_ONLY', 'NEURAL_LINK_AUTHORITY_CEILING_MISSING');
must(neural, 'PUBLIC APPEND-ONLY MEMORY', 'NEURAL_LINK_PUBLIC_MEMORY_WARNING_MISSING');
must(neural, 'AWAITING GITHUB CONFIRMATION', 'NEURAL_LINK_PENDING_SEND_SEMANTICS_MISSING');
must(neural, 'CHAT MESSAGE != COMMAND AUTHORITY', 'NEURAL_LINK_COMMAND_FIREWALL_MISSING');
if (neural.includes('GITHUB_TOKEN')) throw new Error('NEURAL_LINK_BROWSER_SECRET_FORBIDDEN');
must(terminal, 'window.JANUS_TERMINAL_STATE = state', 'NEURAL_LINK_SHARED_TRANSPORT_STATE_MISSING');
must(terminal, "new CustomEvent('janus:terminal-state'", 'NEURAL_LINK_SHARED_TRANSPORT_EVENT_MISSING');
// TRUMP truth: current public manifest is candidate runtime tissue, never proof authority.
must(terminal, 'TRUMP_MANIFEST_URL', 'TRUMP_MANIFEST_SOURCE_MISSING');
must(terminal, 'validateTrumpManifest', 'TRUMP_VALIDATOR_MISSING');
must(terminal, "manifest.status !== 'CANDIDATE_RUNTIME_TISSUE'", 'TRUMP_CANDIDATE_STATUS_GATE_MISSING');
for (const authority of ['proof_authority','scientific_claim_promotion_authority','command_authority','external_effect_authority','physical_runtime_effect_authority']) {
  must(terminal, authority, `TRUMP_AUTHORITY_GATE_MISSING:${authority}`);
}
must(terminal, "boundary.TRUMP_finished !== false", 'TRUMP_FINISHED_FALSE_GATE_MISSING');
must(terminal, "boundary.P_equals_NP_proved !== false", 'TRUMP_PNP_PROOF_FALSE_GATE_MISSING');
must(terminal, "boundary.P_VS_NP !== 'OPEN'", 'TRUMP_PNP_OPEN_GATE_MISSING');
must(terminal, 'BLOCKED_FAIL_CLOSED', 'TRUMP_FAIL_CLOSED_STATUS_MISSING');

// Semantic synthesis truth: candidate meaning cannot silently acquire causal/truth/proof/promotion authority.
must(synthesis, "EXPECTED_SCHEMA='janus.inaihr.semantic_evolution.v2'", 'SYNTH_SCHEMA_GATE_MISSING');
must(synthesis, 'SYNTH_COUNT_MISMATCH', 'SYNTH_COUNT_GATE_MISSING');
must(synthesis, "a.truth!==false||a.proof!==false||a.causal!==false||a.mutation!==false||a.automatic_promotion!==false", 'SYNTH_AUTHORITY_CEILING_MISSING');
must(synthesis, 'SYNTH_BOUNDARY_MISSING', 'SYNTH_BOUNDARY_GATE_MISSING');
for (const law of ['SYNTHESIS != TRUTH','ATTENTION_WEIGHT != EVIDENCE_WEIGHT','CANDIDATE_EDGE != CAUSAL_EDGE']) {
  must(synthesis, law, `SYNTH_LAW_MISSING:${law}`);
}
must(synthesis, 'CANDIDATE_AWAITING_CORROBORATION', 'SYNTH_CANDIDATE_STATUS_MISSING');
must(synthesis, 'DEGRADED · NO CLAIM', 'SYNTH_FAIL_CLOSED_DISPLAY_MISSING');
must(synthesis, 'SYNTH state unavailable. This is not negative evidence.', 'SYNTH_SILENCE_FIREWALL_MISSING');

must(css, '.loss-chart', 'LOSS_CHART_STYLE_MISSING');
must(css, '.active-curve', 'ACTIVE_CURVE_STYLE_MISSING');
must(css, '.candidate-point.rejected', 'REJECTED_CANDIDATE_STYLE_MISSING');
must(css, '.event-log', 'EVENT_LOG_STYLE_MISSING');
must(css, '.module-card.actuated', 'ACTUATED_MODULE_STYLE_MISSING');

if (descriptor.repository !== 'Hawkar-usls/-Terminal-for-Janus') throw new Error('DESCRIPTOR_REPOSITORY_MISMATCH');
if (descriptor.actuator?.enabled !== true) throw new Error('ACTUATOR_NOT_ENABLED');
if (descriptor.actuator?.direct_main_write !== false || descriptor.actuator?.autonomous_merge !== false) throw new Error('AUTHORITY_CEILING_VIOLATION');
if (!descriptor.actuator?.create_new_module_files) throw new Error('SELF_EXTENSION_CREATE_NOT_ALLOWED');
for (const forbidden of ['.github/workflows/','.janus/JANUS_MODULE.json','tools/test-janus-observatory.js','secrets/','credentials/']) {
  if (!descriptor.forbidden_paths.includes(forbidden)) throw new Error(`FORBIDDEN_PATH_MISSING:${forbidden}`);
}
if (!descriptor.epistemic_firewalls.includes('VERIFIER != ORDINARY_SELF_EXTENSION_TARGET')) throw new Error('VERIFIER_IMMUTABILITY_LAW_MISSING');
if (!descriptor.epistemic_firewalls.includes('ACTIVE_BRAIN != REJECTED_CANDIDATE')) throw new Error('ACTIVE_BRAIN_TRUTH_LAW_MISSING');
if (!descriptor.epistemic_firewalls.includes('EMPTY_HRAIN_RETRIEVAL != HRAIN_FAILURE')) throw new Error('HRAIN_EMPTY_TRUTH_LAW_MISSING');
if (!descriptor.verification_profiles?.TERMINAL_OBSERVATORY_STATIC_TEST) throw new Error('VERIFICATION_PROFILE_MISSING');

console.log(JSON.stringify({
  status: 'PASS',
  chat: true,
  brain_monitor: true,
  active_brain_separated_from_candidate: true,
  model_integrity_gate: true,
  hrain_proof_provenance: true,
  valid_empty_hrain_retrieval: true,
  neural_link_v2: true,
  adaptive_ui: true,
  adaptive_ui_network_access: false,
  adaptive_ui_authority: false,
  neural_link_direct_registry_read: false,
  neural_link_browser_secret: false,
  trump_candidate_authority_ceiling: true,
  synthesis_candidate_only: true,
  synthesis_causal_authority: false,
  live_logs: true,
  repository_modules: true,
  accumulative_access_visible: true,
  genesis_sandbox_visible: true,
  verifier_self_mutation_allowed: false,
  durable_delete_authority: false,
  bounded_self_extension: true,
  autonomous_merge: false,
}, null, 2));
