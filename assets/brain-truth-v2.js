(() => {
  'use strict';

  const DEMIURGE = 'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main';
  const MODEL_URL = `${DEMIURGE}/janus_model/state/JANUS_MODEL_STATE.json`;
  const REFRESH_MS = 60000;
  const state = { model: null, receipt: null, inFlight: false };
  const $ = (id) => document.getElementById(id);
  const finite = (v) => Number.isFinite(Number(v));
  const fmt = (v, digits = 3) => finite(v) ? Number(v).toFixed(digits) : '—';
  const short = (v, n = 12) => {
    const s = String(v || '—');
    return s.length > n ? `${s.slice(0, n)}…` : s;
  };
  const promoted = (row) => row?.status === 'PROMOTED';

  async function json(url) {
    const res = await fetch(`${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}`, {
      cache: 'no-store', headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
  }

  function receiptUrl(model) {
    const path = String(model?.last_training_receipt || '');
    if (!/^janus_model\/receipts\/training-\d+\.json$/.test(path)) return null;
    return `${DEMIURGE}/${path}`;
  }

  function latestHistory(model) {
    const rows = Array.isArray(model?.history) ? model.history : [];
    return rows.length ? rows[rows.length - 1] : null;
  }

  function activeAdaptive(row) {
    if (!row) return null;
    if (promoted(row) && finite(row.candidate_eval_loss)) return Number(row.candidate_eval_loss);
    if (finite(row.incumbent_eval_loss)) return Number(row.incumbent_eval_loss);
    return finite(row.candidate_eval_loss) ? Number(row.candidate_eval_loss) : null;
  }

  function activeAnchor(receipt) {
    if (!receipt) return null;
    if (promoted(receipt) && finite(receipt.candidate_anchor_eval_loss)) return Number(receipt.candidate_anchor_eval_loss);
    if (finite(receipt.incumbent_anchor_eval_loss)) return Number(receipt.incumbent_anchor_eval_loss);
    return finite(receipt.candidate_anchor_eval_loss) ? Number(receipt.candidate_anchor_eval_loss) : null;
  }

  function integrity(model) {
    const history = Array.isArray(model?.history) ? model.history : [];
    const attempts = Number(model?.attempt_count);
    const promotedRows = history.filter(promoted);
    const latestPromoted = promotedRows.length ? promotedRows[promotedRows.length - 1] : null;
    const last = history.length ? history[history.length - 1] : null;
    const checks = {
      history_window_not_exceed_attempt_count: Number.isInteger(attempts) && attempts >= history.length,
      promotion_plus_rejection_matches_attempts:
        Number(model?.promotion_count) + Number(model?.rejection_count) === attempts,
      active_checkpoint_matches_last_promoted:
        !latestPromoted || !model?.checkpoint_sha256 || latestPromoted.checkpoint_sha256 === model.checkpoint_sha256,
      latest_history_matches_last_training_status:
        !last || !model?.last_training_status || last.status === model.last_training_status,
    };
    return {
      pass: Object.values(checks).every(Boolean), checks,
      history_window_truncated: Number.isInteger(attempts) && attempts > history.length,
    };
  }

  function setLabel(valueId, text) {
    const value = $(valueId);
    const label = value?.parentElement?.querySelector('label');
    if (label) label.textContent = text;
  }

  function ensureMetricCard(id, label, noteId, afterId) {
    if ($(id)) return;
    const grid = document.querySelector('#view-brain .metrics-grid');
    if (!grid) return;
    const card = document.createElement('article');
    card.className = 'metric-card';
    card.dataset.brainTruthV2 = '1';
    card.innerHTML = `<label>${label}</label><strong id="${id}">—</strong><small id="${noteId}">—</small>`;
    const after = $(afterId)?.closest('.metric-card');
    if (after?.parentElement === grid) after.insertAdjacentElement('afterend', card);
    else grid.appendChild(card);
  }

  function ensureCompactDatum(containerSelector, id, label, afterId) {
    if ($(id)) return;
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const row = document.createElement('div');
    row.dataset.brainTruthV2 = '1';
    row.innerHTML = `<label>${label}</label><strong id="${id}">—</strong>`;
    const after = $(afterId)?.parentElement;
    if (after?.parentElement === container) after.insertAdjacentElement('afterend', row);
    else container.appendChild(row);
  }

  function ensureInspectorDatum(id, label, afterId) {
    if ($(id)) return;
    const inspector = document.querySelector('.inspector');
    if (!inspector) return;
    const row = document.createElement('div');
    row.className = 'metric';
    row.dataset.brainTruthV2 = '1';
    row.innerHTML = `<label>${label}</label><div id="${id}">—</div>`;
    const after = $(afterId)?.closest('.metric');
    if (after?.parentElement === inspector) after.insertAdjacentElement('afterend', row);
    else inspector.appendChild(row);
  }

  function installSurface() {
    setLabel('chat-loss', 'adaptive loss · current source');
    setLabel('brain-loss', 'active adaptive loss · current source');
    setLabel('brain-last-candidate', 'last candidate adaptive loss');
    setLabel('side-native-loss', 'active adaptive loss');

    ensureCompactDatum('.chat-brain-strip', 'chat-anchor-loss', 'frozen anchor loss', 'chat-loss');
    ensureMetricCard('brain-anchor-loss', 'frozen anchor · active', 'brain-anchor-note', 'brain-loss');
    ensureMetricCard('brain-anchor-candidate', 'frozen anchor · candidate', 'brain-anchor-candidate-status', 'brain-last-candidate');
    ensureMetricCard('brain-eval-source', 'adaptive evaluation source', 'brain-eval-contract', 'brain-anchor-candidate');
    ensureInspectorDatum('side-native-anchor', 'frozen anchor loss', 'side-native-loss');
    ensureInspectorDatum('side-native-source', 'adaptive source digest', 'side-native-anchor');

    const legend = document.querySelector('.chart-legend .legend-active');
    if (legend) legend.textContent = 'ACTIVE / INCUMBENT · SAME SOURCE ONLY';
    const truth = document.querySelector('.chart-truth');
    if (truth) truth.textContent = 'ADAPTIVE LOSS IS CURRENT-CORPUS CONTEXT. LINES BREAK WHEN SOURCE DIGEST CHANGES. FROZEN ANCHOR IS THE CROSS-EPOCH COMPARATOR.';

    if (!$('brain-truth-v2-style')) {
      const style = document.createElement('style');
      style.id = 'brain-truth-v2-style';
      style.textContent = '.loss-chart .active-point{fill:#07100c;stroke:var(--green);stroke-width:1.5;vector-effect:non-scaling-stroke}.eval-epoch-note{font-family:"IBM Plex Mono",monospace}.chat-brain-strip>div[data-brain-truth-v2="1"] strong{color:var(--green)}';
      document.head.appendChild(style);
    }
  }

  function renderBasics() {
    installSurface();
    const m = state.model || {};
    const r = state.receipt || {};
    const last = latestHistory(m) || {};
    const adaptive = activeAdaptive(last);
    const anchor = activeAnchor(r);
    const candidateAdaptive = finite(last.candidate_eval_loss) ? Number(last.candidate_eval_loss) : null;
    const candidateAnchor = finite(r.candidate_anchor_eval_loss) ? Number(r.candidate_anchor_eval_loss) : null;
    const source = r.source_digest || last.source_digest || m.last_source_digest || null;
    const contract = r.evaluation_contract_sha256 || r.evaluation_contract?.contract_sha256 || null;
    const anchorSha = r.anchor_sha256 || r.evaluation_contract?.anchor?.sha256 || null;
    const verdict = last.status || m.last_training_status || 'UNRESOLVED';
    const check = integrity(m);

    if ($('brain-loss')) $('brain-loss').textContent = fmt(adaptive, 6);
    if ($('chat-loss')) $('chat-loss').textContent = `${fmt(adaptive, 5)} · CURRENT`;
    if ($('side-native-loss')) $('side-native-loss').textContent = `${fmt(adaptive, 6)} · CURRENT SOURCE`;
    if ($('brain-anchor-loss')) $('brain-anchor-loss').textContent = fmt(anchor, 6);
    if ($('brain-anchor-note')) $('brain-anchor-note').textContent = `frozen benchmark · lower is better · ${anchorSha ? `sha ${short(anchorSha, 16)}` : 'digest unresolved'}`;
    if ($('chat-anchor-loss')) $('chat-anchor-loss').textContent = `${fmt(anchor, 5)} · FROZEN`;
    if ($('side-native-anchor')) $('side-native-anchor').textContent = `${fmt(anchor, 6)} · FROZEN`;
    if ($('brain-anchor-candidate')) $('brain-anchor-candidate').textContent = fmt(candidateAnchor, 6);
    if ($('brain-anchor-candidate-status')) $('brain-anchor-candidate-status').textContent = `${verdict} · candidate anchor for latest run`;
    if ($('brain-eval-source')) $('brain-eval-source').textContent = short(source, 22);
    if ($('brain-eval-contract')) $('brain-eval-contract').textContent = `adaptive values compare only inside this source · contract ${short(contract, 16)}`;
    if ($('side-native-source')) $('side-native-source').textContent = source || '—';

    const delta = candidateAdaptive != null && adaptive != null ? candidateAdaptive - adaptive : null;
    if ($('brain-last-candidate-status') && delta != null) {
      $('brain-last-candidate-status').textContent = `${verdict} · candidate ${delta <= 0 ? 'better/equal' : 'worse'} than active adaptive by ${Math.abs(delta).toFixed(6)} in the same latest source context`;
    }

    const brainStatus = $('brain-status');
    if (brainStatus) {
      brainStatus.textContent = check.pass
        ? `${m.status || 'UNRESOLVED'} · history ${check.history_window_truncated ? `window ${m.history?.length || 0}/${m.attempt_count}` : 'complete'}`
        : `STATE INTEGRITY WARNING · ${m.status || 'UNRESOLVED'}`;
    }
    const live = $('brain-live-status');
    if (live) live.textContent = check.pass && m.status === 'NATIVE_MODEL_PROMOTED' ? 'ACTIVE CHECKPOINT VERIFIED' : (check.pass ? (m.status || 'UNRESOLVED') : 'STATE INTEGRITY WARNING');

    const pill = $('brain-pill');
    if (pill) {
      pill.textContent = `BRAIN P${m.promotion_count ?? '?'}/A${m.attempt_count ?? '?'} · ADAPT ${fmt(adaptive, 3)} · ANCHOR ${fmt(anchor, 3)}`;
      pill.classList.toggle('live', check.pass && m.status === 'NATIVE_MODEL_PROMOTED');
      pill.classList.toggle('warn', !check.pass);
      pill.title = `P=promotions, A=training attempts. ADAPT=current source only (${source || 'unresolved'}). ANCHOR=frozen cross-epoch benchmark (${anchorSha || 'unresolved'}). Last candidate ${fmt(candidateAdaptive, 6)} ${verdict}.`;
    }
  }

  function sourceKey(row, i) {
    return row?.source_digest || `UNKNOWN_SOURCE_${i}`;
  }

  function renderChart() {
    const m = state.model || {};
    const history = (Array.isArray(m.history) ? m.history : []).filter((x) => finite(x.candidate_eval_loss));
    const chart = $('loss-chart');
    const axis = $('loss-axis');
    if (!chart || !history.length) return;

    const candidates = history.map((row) => Number(row.candidate_eval_loss));
    const active = history.map(activeAdaptive);
    const all = [...candidates, ...active.filter(finite)].map(Number);
    let min = Math.min(...all), max = Math.max(...all);
    if (max === min) { min -= 0.1; max += 0.1; }
    const pad = (max - min) * 0.12;
    min -= pad; max += pad;
    const W = 1000, H = 170, left = 18, right = 12, top = 10, bottom = 14;
    const x = (i) => left + (history.length === 1 ? (W-left-right)/2 : i * (W-left-right)/(history.length-1));
    const y = (v) => top + (max-v) * (H-top-bottom)/(max-min);
    const attemptCount = Number(m.attempt_count);
    const startAttempt = Number.isInteger(attemptCount) && attemptCount >= history.length ? attemptCount - history.length + 1 : 1;

    const segments = [];
    let segment = [];
    let previousKey = null;
    history.forEach((row, i) => {
      const key = sourceKey(row, i);
      if (previousKey !== null && key !== previousKey) {
        if (segment.length > 1) segments.push(segment);
        segment = [];
      }
      segment.push([x(i), y(active[i])]);
      previousKey = key;
    });
    if (segment.length > 1) segments.push(segment);

    const grid = [0.25,0.5,0.75].map((ratio) => `<line class="grid" x1="${left}" x2="${W-right}" y1="${top+ratio*(H-top-bottom)}" y2="${top+ratio*(H-top-bottom)}"/>`).join('');
    const lines = segments.map((points) => `<polyline class="active-curve" points="${points.map(([px,py]) => `${px},${py}`).join(' ')}"/>`).join('');
    const activeDots = active.map((v, i) => `<circle class="active-point" cx="${x(i)}" cy="${y(v)}" r="2.2"><title>attempt ${startAttempt+i}: active ${fmt(v,6)} · source ${short(sourceKey(history[i],i),16)}</title></circle>`).join('');
    const candidateDots = candidates.map((v, i) => {
      const cls = promoted(history[i]) ? 'promoted' : 'rejected';
      const latest = i === history.length - 1 ? ' latest' : '';
      return `<circle class="candidate-point ${cls}${latest}" cx="${x(i)}" cy="${y(v)}" r="${i===history.length-1?4.8:3.1}"><title>attempt ${startAttempt+i}: candidate ${v.toFixed(6)} · ${history[i].status || 'UNKNOWN'} · active ${fmt(active[i],6)} · source ${short(sourceKey(history[i],i),16)}</title></circle>`;
    }).join('');
    chart.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-label="JANUS adaptive evaluation trace segmented by source digest">${grid}${lines}${activeDots}${candidateDots}</svg>`;
    if (axis) axis.innerHTML = `<span>attempt ${startAttempt} shown</span><span>${history.length} shown of ${Number.isInteger(attemptCount) ? attemptCount : history.length} lifetime attempts</span><span>attempt ${startAttempt+history.length-1} shown</span>`;
    if ($('brain-lineage-summary')) $('brain-lineage-summary').textContent = `${history.length} shown / ${Number.isInteger(attemptCount) ? attemptCount : history.length} lifetime · ${m.promotion_count ?? '?'} promoted · ${m.rejection_count ?? '?'} rejected · source breaks not connected`;
  }

  function clearStaleTelemetryClass() {
    const status = $('weight-telemetry-status');
    if (status?.textContent?.includes('CHECKPOINT DIGEST ONLY')) status.classList.remove('live');
  }

  async function refresh() {
    if (state.inFlight) return;
    state.inFlight = true;
    try {
      const model = await json(MODEL_URL);
      const url = receiptUrl(model);
      const receipt = url ? await json(url).catch(() => null) : null;
      state.model = model;
      state.receipt = receipt;
      renderBasics();
      renderChart();
      clearStaleTelemetryClass();
    } catch (err) {
      console.warn('JANUS_BRAIN_TRUTH_V2_UNRESOLVED', err);
      const pill = $('brain-pill');
      if (pill) {
        pill.textContent = 'BRAIN UNRESOLVED';
        pill.classList.remove('live');
        pill.classList.add('warn');
        pill.title = `Brain truth witness unresolved: ${err?.message || err}`;
      }
    } finally {
      state.inFlight = false;
    }
  }

  let eventTimer = null;
  function queueRefresh() {
    clearTimeout(eventTimer);
    eventTimer = setTimeout(refresh, 150);
  }

  function boot() {
    installSurface();
    setTimeout(refresh, 250);
    setInterval(refresh, REFRESH_MS);
    document.addEventListener('janus:logs-rendered', queueRefresh);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
