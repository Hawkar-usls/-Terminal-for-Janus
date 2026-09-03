(() => {
  'use strict';

  const DEMIURGE = 'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main';
  const SELF = 'https://raw.githubusercontent.com/Hawkar-usls/janus-meta-registry/janus/native-self-memory-modular-organism-v1';
  const URLS = {
    modelState: `${DEMIURGE}/janus_model/state/JANUS_MODEL_STATE.json`,
    modelManifest: `${DEMIURGE}/janus_model/JANUS_MODEL_MANIFEST-v1.json`,
    weightTelemetry: `${DEMIURGE}/janus_model/state/JANUS_WEIGHT_TELEMETRY.json`,
    latestDecision: `${DEMIURGE}/janus_model/state/JANUS_LATEST_DECISION.json`,
    organAccess: `${DEMIURGE}/scout_swarm/JANUS_ACCUMULATIVE_ORGAN_ACCESS-v1.json`,
    moduleState: `${SELF}/JANUS/MODULES/OBSERVED-MODULE-STATE.json`,
    moduleRegistry: `${SELF}/JANUS/MODULES/JANUS-REPOSITORY-MODULE-REGISTRY-v1.0.json`,
    decisionIndex: `${SELF}/JANUS/DECISIONS/NATIVE/INDEX.json`,
  };

  const fallbackAccessLanes = new Map([
    ['Hawkar-usls/Hrain', 'BRANCH_VERIFY_ACCUMULATE'],
    ['Hawkar-usls/iNaiHR', 'BRANCH_VERIFY_ACCUMULATE'],
    ['Hawkar-usls/-Terminal-for-Janus', 'BRANCH_VERIFY_ACCUMULATE'],
    ['Hawkar-usls/Janus_Genesis', 'SANDBOX_VERIFY_ACCUMULATE'],
  ]);

  const obs = {
    model: null,
    manifest: null,
    telemetry: null,
    decision: null,
    decisionIndex: null,
    modules: null,
    registry: null,
    organAccess: null,
    refreshedAt: null,
  };

  const $ = (id) => document.getElementById(id);
  const esc = (v) => String(v ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  const short = (v, n = 12) => {
    const s = String(v || '—');
    return s.length > n ? `${s.slice(0, n)}…` : s;
  };
  const set = (id, v) => { const el = $(id); if (el) el.textContent = v ?? '—'; };
  const fmt = (v, digits = 5) => Number.isFinite(Number(v)) ? Number(v).toFixed(digits) : '—';

  async function json(url, optional = false) {
    try {
      const res = await fetch(`${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`${res.status} ${url}`);
      return await res.json();
    } catch (err) {
      if (optional) return null;
      throw err;
    }
  }

  function latestHistory() {
    const h = obs.model?.history || [];
    return h.length ? h[h.length - 1] : null;
  }

  function renderBrainBasics() {
    const m = obs.model || {};
    const cfg = m.config || {};
    const last = latestHistory() || {};
    const manifest = obs.manifest || {};
    const params = manifest?.architecture?.parameter_count;
    const loss = last.candidate_eval_loss;
    const incumbent = last.incumbent_eval_loss;
    const delta = Number.isFinite(Number(loss)) && Number.isFinite(Number(incumbent)) ? Number(incumbent) - Number(loss) : null;
    const checkpoint = m.checkpoint_sha256 || 'UNRESOLVED';

    set('brain-checkpoint', checkpoint);
    set('brain-status', m.status || 'UNRESOLVED');
    set('brain-loss', fmt(loss, 6));
    set('brain-loss-delta', delta == null ? 'bootstrap / no incumbent' : `${delta >= 0 ? '↓ improved' : '↑ regressed'} ${Math.abs(delta).toFixed(6)}`);
    set('brain-attempts', m.attempt_count ?? '—');
    set('brain-promote-reject', `${m.promotion_count ?? '—'} / ${m.rejection_count ?? '—'}`);
    set('brain-params', Number.isFinite(Number(params)) ? Number(params).toLocaleString('en-US') : '—');
    set('brain-architecture', `${manifest?.architecture?.family || 'causal_transformer'} · ${cfg.n_layers ?? '?'}L × ${cfg.n_heads ?? '?'}H × d${cfg.d_model ?? '?'}`);
    set('chat-checkpoint', short(checkpoint, 20));
    set('chat-loss', fmt(loss, 5));
    set('chat-promotions', `${m.promotion_count ?? '—'}/${m.attempt_count ?? '—'}`);
    set('side-native-checkpoint', short(checkpoint, 18));
    set('side-native-loss', fmt(loss, 6));
    set('organism-native-checkpoint', checkpoint);
    set('brain-live-status', m.status === 'NATIVE_MODEL_PROMOTED' ? 'PROMOTED / LIVE' : (m.status || 'UNRESOLVED'));

    const pill = $('brain-pill');
    if (pill) {
      pill.textContent = `BRAIN ${m.promotion_count ?? '?'} · L ${fmt(loss, 3)}`;
      pill.classList.toggle('live', m.status === 'NATIVE_MODEL_PROMOTED');
    }

    const rows = [
      ['context_length', cfg.context_length], ['d_model', cfg.d_model], ['n_heads', cfg.n_heads],
      ['n_layers', cfg.n_layers], ['ff_mult', cfg.ff_mult], ['dropout', cfg.dropout], ['vocab_size', cfg.vocab_size],
      ['checkpoint', short(checkpoint, 22)],
    ];
    const box = $('brain-config');
    if (box) box.innerHTML = rows.map(([k, v]) => `<div class="kv-row"><span>${esc(k)}</span><b>${esc(v ?? '—')}</b></div>`).join('');
  }

  function renderLossChart() {
    const history = (obs.model?.history || []).filter((x) => Number.isFinite(Number(x.candidate_eval_loss)));
    const chart = $('loss-chart');
    const axis = $('loss-axis');
    if (!chart || !history.length) return;
    const vals = history.map((x) => Number(x.candidate_eval_loss));
    let min = Math.min(...vals), max = Math.max(...vals);
    if (max === min) { max += 0.1; min -= 0.1; }
    const pad = (max - min) * 0.12;
    min -= pad; max += pad;
    const W = 1000, H = 170, left = 18, right = 12, top = 10, bottom = 14;
    const x = (i) => left + (history.length === 1 ? (W-left-right)/2 : i * (W-left-right)/(history.length-1));
    const y = (v) => top + (max-v) * (H-top-bottom)/(max-min);
    const points = vals.map((v, i) => `${x(i)},${y(v)}`).join(' ');
    const area = `${left},${H-bottom} ${points} ${x(history.length-1)},${H-bottom}`;
    const grid = [0.25,0.5,0.75].map((r) => `<line class="grid" x1="${left}" x2="${W-right}" y1="${top+r*(H-top-bottom)}" y2="${top+r*(H-top-bottom)}"/>`).join('');
    const dots = vals.map((v,i) => `<circle class="point${i===vals.length-1?' latest':''}" cx="${x(i)}" cy="${y(v)}" r="${i===vals.length-1?4.8:3.1}"><title>generation ${i+1}: ${v.toFixed(6)}</title></circle>`).join('');
    chart.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-label="JANUS evaluation loss lineage">${grid}<polygon class="area" points="${area}"/><polyline class="curve" points="${points}"/>${dots}</svg>`;
    axis.innerHTML = `<span>gen 1 · ${vals[0].toFixed(4)}</span><span>best ${Math.min(...vals).toFixed(4)}</span><span>gen ${vals.length} · ${vals[vals.length-1].toFixed(4)}</span>`;
    const improvement = vals[0] - vals[vals.length-1];
    set('brain-lineage-summary', `${history.length} promoted/attempt records · Δ ${improvement >= 0 ? '−' : '+'}${Math.abs(improvement).toFixed(5)}`);
  }

  function inferLatestDecisionFromIndex() {
    const rows = obs.decisionIndex?.decisions || [];
    if (!rows.length) return null;
    return rows[rows.length - 1];
  }

  function renderDecision() {
    const d = obs.decision || inferLatestDecisionFromIndex() || {};
    const selected = d.selected || {};
    const candidate = selected.candidate_id || d.selected_candidate_id || 'NO_ACTION / UNRESOLVED';
    const status = d.status || 'UNRESOLVED';
    const checkpoint = d.checkpoint_sha256 || obs.model?.checkpoint_sha256 || null;
    const target = selected.target || {};
    const margin = d.top_margin ?? d.action_margin_over_no_action;
    const panel = $('brain-decision');
    if (panel) panel.innerHTML = [
      `<div class="decision-name">${esc(candidate)}</div>`,
      `<div class="decision-state">${esc(status)}</div>`,
      `<div class="decision-row"><span>checkpoint</span><b>${esc(short(checkpoint,22))}</b></div>`,
      `<div class="decision-row"><span>margin</span><b>${esc(Number.isFinite(Number(margin)) ? Number(margin).toFixed(6) : '—')}</b></div>`,
      `<div class="decision-row"><span>target</span><b>${esc(target.repository || '—')}</b></div>`,
      `<div class="decision-row"><span>verification</span><b>${esc(selected.verification_profile || (status === 'NO_ACTION' ? 'NOT_REQUIRED' : 'TARGET_LOCAL_REQUIRED'))}</b></div>`,
      `<div class="decision-row"><span>authority</span><b>selection ≠ verified fix</b></div>`,
    ].join('');
    set('chat-decision', candidate);
    set('side-native-decision', `${candidate} · ${status}`);
  }

  function renderTelemetry() {
    const t = obs.telemetry;
    const box = $('tensor-telemetry');
    const status = $('weight-telemetry-status');
    if (!box) return;
    if (!t || !Array.isArray(t.tensors)) {
      box.innerHTML = '<div class="empty-state">Tensor telemetry not published yet — checkpoint SHA-256 remains the authoritative weight identity.</div>';
      if (status) status.textContent = 'CHECKPOINT DIGEST ONLY';
      return;
    }
    if (status) {
      status.textContent = `${t.tensor_count ?? t.tensors.length} TENSORS · ${Number(t.parameter_count || 0).toLocaleString('en-US')} PARAMS`;
      status.classList.add('live');
    }
    box.innerHTML = t.tensors.map((row) => `<div class="tensor-card"><strong>${esc(row.name)}</strong><span>shape ${esc(JSON.stringify(row.shape))} · n=${esc(row.numel)}</span><span>mean ${esc(fmt(row.mean,6))} · std ${esc(fmt(row.std,6))}</span><span>min ${esc(fmt(row.min,6))} · max ${esc(fmt(row.max,6))}</span><span>L2 ${esc(fmt(row.l2,6))}</span></div>`).join('');
  }

  function accessLaneFor(repository) {
    const row = (obs.organAccess?.organs || []).find((item) => item.repository === repository);
    return row?.access_lane || fallbackAccessLanes.get(repository) || 'READ_ACCUMULATE';
  }

  function laneLabel(lane) {
    if (lane === 'BRANCH_VERIFY_ACCUMULATE') return 'BRANCH + VERIFY + ACCUMULATE';
    if (lane === 'SANDBOX_VERIFY_ACCUMULATE') return 'SANDBOX + VERIFY + ACCUMULATE';
    return 'READ + ACCUMULATE';
  }

  function renderModules() {
    const state = obs.modules || {};
    const registry = obs.registry || {};
    const rows = state.modules || [];
    const observedCount = Number(state.module_count);
    const registryCount = Number(registry?.discovery?.discovered_module_count);
    const resolvedCount = Number.isInteger(observedCount) && observedCount > 0
      ? observedCount
      : Number.isInteger(registryCount) && registryCount > 0
        ? registryCount
        : rows.length;
    const observedMapStale = rows.length === 0 && resolvedCount > 0;

    set('brain-module-count', resolvedCount);
    set('modules-count', resolvedCount);
    set('modules-attempts', registry?.global_mutation_policy?.max_patch_attempts ?? 2);
    set('modules-live-status', rows.length
      ? `${rows.length} ORGANS OBSERVED · MEMORY APPEND-ONLY`
      : observedMapStale
        ? `${resolvedCount} ORGANS REGISTERED · OBSERVED MAP STALE`
        : 'UNRESOLVED');
    const box = $('module-list');
    if (!box) return;
    if (!rows.length) {
      box.innerHTML = observedMapStale
        ? `<div class="empty-state">${esc(resolvedCount)} repository organs are registered, but the persisted observed-module map is stale/empty. Registry count is shown; per-organ observation details remain unresolved.</div>`
        : '<div class="empty-state">No persisted module state resolved.</div>';
      return;
    }
    const sorted = [...rows].sort((a,b) => String(a.repository).localeCompare(String(b.repository)));
    box.innerHTML = sorted.map((m) => {
      const lane = accessLaneFor(m.repository);
      const active = lane !== 'READ_ACCUMULATE';
      return `<article class="module-card${active?' actuated':''}"><div class="module-top"><div><div class="module-name">${esc(m.repository)}</div><div class="module-role">${esc(m.scout_role || m.focus || 'typed repository organ')}</div></div><span class="module-lane">${esc(laneLabel(lane))}</span></div><div class="module-meta"><div><label>module</label><b>${esc(m.module_id || '—')}</b></div><div><label>ref</label><b>${esc(m.ref || '—')}</b></div><div><label>observed commit</label><b title="${esc(m.target_commit)}">${esc(short(m.target_commit,16))}</b></div><div><label>scout</label><b>${esc(m.agent_id || '—')}</b></div></div></article>`;
    }).join('');
  }

  function logRow(seq, type, body, verdict, cls = '') {
    return `<div class="log-row"><span class="log-seq">#${String(seq).padStart(3,'0')}</span><span class="log-type">${esc(type)}</span><span class="log-body">${esc(body)}</span><span class="log-verdict ${cls}">${esc(verdict)}</span></div>`;
  }

  function renderLogs() {
    const rows = [];
    let seq = 1;
    for (const h of obs.model?.history || []) {
      const loss = fmt(h.candidate_eval_loss, 6);
      const incumbent = Number.isFinite(Number(h.incumbent_eval_loss)) ? fmt(h.incumbent_eval_loss,6) : 'bootstrap';
      const verdict = h.status || 'UNKNOWN';
      rows.push(logRow(seq++, 'TRAIN', `run ${h.run_id} · incumbent ${incumbent} → candidate ${loss} · checkpoint ${short(h.checkpoint_sha256,16)}`, verdict, verdict==='PROMOTED'?'':'warn'));
    }
    const d = obs.decision || inferLatestDecisionFromIndex();
    if (d) {
      const selected = d.selected?.candidate_id || d.selected_candidate_id || 'NO_ACTION';
      rows.push(logRow(seq++, 'DECIDE', `${selected} · checkpoint ${short(d.checkpoint_sha256,16)} · ${d.gate_reason || 'persisted native selection'}`, d.status || 'RECORDED', d.status==='NO_ACTION'?'warn':''));
      if (d.status && d.status !== 'NO_ACTION') rows.push(logRow(seq++, 'PATCH', `${d.selected?.target?.repository || 'target'} · ${d.selected?.verification_profile || 'local verifier'} · proposal must be applied only through target-bounded write lane`, 'AWAIT VERIFY', 'warn'));
    }
    const mods = obs.modules?.modules || [];
    if (mods.length) rows.push(logRow(seq++, 'SCOUT', `${mods.length} repository organs present in SELF observed-module state`, 'OBSERVED'));
    rows.push(logRow(seq++, 'MEMORY', 'Durable evidence is append-only: supersede, quarantine or mark stale; never erase failures, negative results or counterexamples.', 'NO DELETE'));
    rows.push(logRow(seq++, 'LAW', 'No verification = no PASS. Model output is not independent evidence. Autonomous merge remains disabled.', 'ENFORCED'));
    const box = $('janus-event-log');
    if (box) box.innerHTML = rows.length ? rows.slice().reverse().join('') : '<div class="empty-state">No persisted events resolved.</div>';
  }

  async function loadAll() {
    const [model, manifest, telemetry, latestDecision, organAccess, modules, registry, decisionIndex] = await Promise.all([
      json(URLS.modelState), json(URLS.modelManifest), json(URLS.weightTelemetry, true),
      json(URLS.latestDecision, true), json(URLS.organAccess, true), json(URLS.moduleState), json(URLS.moduleRegistry), json(URLS.decisionIndex, true),
    ]);
    Object.assign(obs, { model, manifest, telemetry, decision: latestDecision, organAccess, modules, registry, decisionIndex, refreshedAt: new Date() });
  }

  function renderAll() {
    renderBrainBasics();
    renderLossChart();
    renderDecision();
    renderTelemetry();
    renderModules();
    renderLogs();
  }

  async function refreshObservatory() {
    const btn = $('logs-refresh');
    btn?.classList.add('loading-shimmer');
    try {
      await loadAll();
      renderAll();
    } catch (err) {
      console.warn('JANUS_OBSERVATORY_UNRESOLVED', err);
      set('brain-live-status', 'UNRESOLVED');
      set('modules-live-status', 'UNRESOLVED');
      const log = $('janus-event-log');
      if (log) log.innerHTML = `<div class="empty-state">Git witness unresolved: ${esc(err?.message || err)}. Silence is not negative evidence.</div>`;
    } finally {
      btn?.classList.remove('loading-shimmer');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('logs-refresh')?.addEventListener('click', refreshObservatory);
    refreshObservatory();
    window.setInterval(refreshObservatory, 60000);
  });
})();