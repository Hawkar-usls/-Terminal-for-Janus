const fs = require('fs');

function read(path) { return fs.readFileSync(path, 'utf8'); }
function must(text, needle, code) {
  if (!text.includes(needle)) throw new Error(`${code}:${needle}`);
}

const html = read('index.html');
const js = read('assets/janus-observatory.js');
const css = read('assets/janus-observatory.css');
const descriptor = JSON.parse(read('.janus/JANUS_MODULE.json'));

for (const view of ['view-console','view-brain','view-logs','view-modules']) must(html, view, 'MISSING_VIEW');
for (const label of ['CHAT','BRAIN MONITOR','LIVE LOGS','MODULES']) must(html, label, 'MISSING_NAV_SURFACE');
for (const id of ['brain-checkpoint','brain-loss','loss-chart','janus-event-log','module-list','tensor-telemetry']) must(html, id, 'MISSING_TELEMETRY_TARGET');

must(js, 'JANUS_MODEL_STATE.json', 'MODEL_STATE_SOURCE_MISSING');
must(js, 'JANUS_WEIGHT_TELEMETRY.json', 'WEIGHT_TELEMETRY_SOURCE_MISSING');
must(js, 'JANUS_LATEST_DECISION.json', 'DECISION_SOURCE_MISSING');
must(js, 'OBSERVED-MODULE-STATE.json', 'MODULE_STATE_SOURCE_MISSING');
must(js, 'JANUS_ACCUMULATIVE_ORGAN_ACCESS-v1.json', 'ORGAN_ACCESS_SOURCE_MISSING');
must(js, 'selection ≠ verified fix', 'VERIFY_BOUNDARY_MISSING');
must(js, "'Hawkar-usls/-Terminal-for-Janus', 'BRANCH_VERIFY_ACCUMULATE'", 'TERMINAL_ACTUATED_LANE_MISSING');
must(js, "'Hawkar-usls/Janus_Genesis', 'SANDBOX_VERIFY_ACCUMULATE'", 'GENESIS_SANDBOX_LANE_MISSING');
must(js, 'READ + ACCUMULATE', 'ACCUMULATIVE_READ_LANE_MISSING');
must(js, 'SANDBOX + VERIFY + ACCUMULATE', 'GENESIS_LANE_LABEL_MISSING');
must(js, 'Durable evidence is append-only', 'APPEND_ONLY_LAW_MISSING');
must(js, 'never erase failures, negative results or counterexamples', 'NO_DELETE_DETAIL_MISSING');

must(css, '.loss-chart', 'LOSS_CHART_STYLE_MISSING');
must(css, '.event-log', 'EVENT_LOG_STYLE_MISSING');
must(css, '.module-card.actuated', 'ACTUATED_MODULE_STYLE_MISSING');

if (descriptor.repository !== 'Hawkar-usls/-Terminal-for-Janus') throw new Error('DESCRIPTOR_REPOSITORY_MISMATCH');
if (descriptor.actuator?.enabled !== true) throw new Error('ACTUATOR_NOT_ENABLED');
if (descriptor.actuator?.direct_main_write !== false || descriptor.actuator?.autonomous_merge !== false) throw new Error('AUTHORITY_CEILING_VIOLATION');
if (!descriptor.actuator?.create_new_module_files) throw new Error('SELF_EXTENSION_CREATE_NOT_ALLOWED');
for (const forbidden of ['.github/workflows/','.janus/JANUS_MODULE.json','secrets/','credentials/']) {
  if (!descriptor.forbidden_paths.includes(forbidden)) throw new Error(`FORBIDDEN_PATH_MISSING:${forbidden}`);
}
if (!descriptor.verification_profiles?.TERMINAL_OBSERVATORY_STATIC_TEST) throw new Error('VERIFICATION_PROFILE_MISSING');

console.log(JSON.stringify({
  status: 'PASS',
  chat: true,
  brain_monitor: true,
  live_logs: true,
  repository_modules: true,
  accumulative_access_visible: true,
  genesis_sandbox_visible: true,
  durable_delete_authority: false,
  bounded_self_extension: true,
  autonomous_merge: false,
}, null, 2));
