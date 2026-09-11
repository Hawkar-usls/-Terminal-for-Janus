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

    const title = document.querySelector('#view-brain .chart-card h3');
    if (title) title.textContent = 'DISCRETE DECISION MARGIN · CANDIDATE VS INCUMBENT';
    const activeLegend = document.querySelector('.chart-legend .legend-active');
    const promotedLegend = document.querySelector('.chart-legend .legend-promoted');
    const rejectedLegend = document.querySelector('.chart-legend .legend-rejected');
    if (activeLegend) activeLegend.textContent = '0% = SAME-ATTEMPT INCUMBENT';
    if (promotedLegend) promotedLegend.textContent = 'PROMOTED CANDIDATE';
    if (rejectedLegend) rejectedLegend.textContent = 'REJECTED CANDIDATE';
    const truth = document.querySelector('.chart-truth');
    if (truth) truth.textContent = 'EACH BAR IS A SAME-ATTEMPT COMPARISON: +% = CANDIDATE LOWER ADAPTIVE LOSS, -% = HIGHER. NO LINE CONNECTS DIFFERENT SOURCES. COLOR IS THE FINAL GATE VERDICT; FROZEN ANCHOR REMAINS THE CROSS-EPOCH COMPARATOR.';

    if (!$('brain-truth-v2-style')) {
      const style = document.createElement('style');
      style.id = 'brain-truth-v2-style';
      style.textContent = '.loss-chart{height:220px}.loss-chart .decision-zero{stroke:#42606a;stroke-width:1.6;vector-effect:non-scaling-stroke}.loss-chart .decision-grid{stroke:#17242c;stroke-width:1;vector-effect:non-scaling-stroke}.loss-chart .decision-stem{stroke-width:4;stroke-linecap:round;vector-effect:non-scaling-stroke;opacity:.92}.loss-chart .decision-stem.promoted{stroke:var(--green)}.loss-chart .decision-stem.rejected{stroke:var(--amber)}.loss-chart .decision-dot{fill:#07100c;stroke-width:2.2;vector-effect:non-scaling-stroke}.loss-chart .decision-dot.promoted{stroke:var(--green)}.loss-chart .decision-dot.rejected{stroke:var(--amber)}.loss-chart .decision-dot.latest{stroke-width:4}.loss-chart .decision-label{fill:#6f858b;font:9px "IBM Plex Mono",monospace}.loss-chart .decision-label.zero{fill:#9db0b4}.chat-brain-strip>div[data-brain-truth-v2="1"] strong{color:var(--green)}';
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

  function adaptiveMarginPct(row) {
    if (!finite(row?.candidate_eval_loss) || !finite(row?.incumbent_eval_loss)) return null;
    const candidate = Number(row.candidate_eval_loss);
    const incumbent = Number(row.incumbent_eval_loss);
    const denom = Math.max(Math.abs(incumbent), 1e-12);
    return 100 * (incumbent - candidate) / denom;
  }

  function renderChart() {
    const m = state.model || {};
    const history = (Array.isArray(m.history) ? m.history : []).filter((row) => Number.isFinite(adaptiveMarginPct(row)));
    const chart = $('loss-chart');
    const axis = $('loss-axis');
    if (!chart || !history.length) return;

    const margins = history.map(adaptiveMarginPct);
    const observedMax = Math.max(...margins.map((v) => Math.abs(v)));
    const scale = Math.max(0.05, observedMax * 1.15);
    const W = Math.max(720, Math.round(chart.clientWidth || 1000)), H = 220, left = 52, right = 18, top = 18, bottom = 24;
    const plotH = H - top - bottom;
    const x = (i) => left + (history.length === 1 ? (W-left-right)/2 : i * (W-left-right)/(history.length-1));
    const y = (v) => top + (scale - v) * plotH / (2 * scale);
    const zeroY = y(0);
    const attemptCount = Number(m.attempt_count);
    const startAttempt = Number.isInteger(attemptCount) && attemptCount >= history.length ? attemptCount - history.length + 1 : 1;
    const sourceChanges = history.reduce((count, row, i) => i > 0 && sourceKey(row, i) !== sourceKey(history[i-1], i-1) ? count + 1 : count, 0);

    const gridValues = [scale, scale / 2, 0, -scale / 2, -scale];
    const grid = gridValues.map((v) => {
      const cls = v === 0 ? 'decision-zero' : 'decision-grid';
      const label = `${v > 0 ? '+' : ''}${v.toFixed(scale >= 10 ? 1 : scale >= 1 ? 2 : 3)}%`;
      return `<line class="${cls}" x1="${left}" x2="${W-right}" y1="${y(v)}" y2="${y(v)}"/><text class="decision-label${v===0?' zero':''}" x="${left-7}" y="${y(v)+3}" text-anchor="end">${label}</text>`;
    }).join('');

    const stems = margins.map((margin, i) => {
      const row = history[i];
      const cls = promoted(row) ? 'promoted' : 'rejected';
      const latest = i === history.length - 1 ? ' latest' : '';
      const candidate = Number(row.candidate_eval_loss);
      const incumbent = Number(row.incumbent_eval_loss);
      const attempt = startAttempt + i;
      const sign = margin >= 0 ? '+' : '';
      const title = `attempt ${attempt}: ${sign}${margin.toFixed(4)}% adaptive margin · candidate ${candidate.toFixed(6)} vs incumbent ${incumbent.toFixed(6)} · ${row.status || 'UNKNOWN'} · source ${short(sourceKey(row,i),16)}`;
      return `<line class="decision-stem ${cls}" x1="${x(i)}" x2="${x(i)}" y1="${zeroY}" y2="${y(margin)}"><title>${title}</title></line><circle class="decision-dot ${cls}${latest}" cx="${x(i)}" cy="${y(margin)}" r="${i===history.length-1?4.6:3.0}"><title>${title}</title></circle>`;
    }).join('');

    const tickStep = history.length <= 24 ? 4 : 8;
    const tickIndexes = new Set([0, history.length - 1]);
    for (let i = tickStep - 1; i < history.length - 1; i += tickStep) tickIndexes.add(i);
    const ticks = [...tickIndexes].sort((a,b) => a-b).map((i) => `<text class="decision-label" x="${x(i)}" y="${H-5}" text-anchor="middle">${startAttempt+i}</text>`).join('');

    chart.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-label="JANUS discrete same-attempt adaptive decision margins">${grid}${stems}${ticks}</svg>`;
    if (axis) axis.innerHTML = `<span>+% = candidate better</span><span>attempt number · ${history.length} shown / ${Number.isInteger(attemptCount) ? attemptCount : history.length} lifetime</span><span>−% = candidate worse</span>`;
    if ($('brain-lineage-summary')) $('brain-lineage-summary').textContent = `${history.length} discrete attempts / ${Number.isInteger(attemptCount) ? attemptCount : history.length} lifetime · ${m.promotion_count ?? '?'} promoted · ${m.rejection_count ?? '?'} rejected · ${sourceChanges} source changes`;
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
  let resizeTimer = null;
  function queueRefresh() {
    clearTimeout(eventTimer);
    eventTimer = setTimeout(refresh, 150);
  }

  function queueChartResize() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (state.model) renderChart();
    }, 100);
  }

  function boot() {
    installSurface();
    setTimeout(refresh, 250);
    setInterval(refresh, REFRESH_MS);
    document.addEventListener('janus:logs-rendered', queueRefresh);
    window.addEventListener('resize', queueChartResize, { passive: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
