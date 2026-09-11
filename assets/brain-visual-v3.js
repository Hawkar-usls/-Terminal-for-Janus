(() => {
  'use strict';

  const BUILD = 'BRAIN_VISUAL_V3_2026_09_11';
  const MODEL_URL = 'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/janus_model/state/JANUS_MODEL_STATE.json';
  const REFRESH_MS = 60000;
  const ADAPTIVE_TOLERANCE_PCT = 0.2;
  const state = { model: null, rendering: false };
  const $ = (id) => document.getElementById(id);
  const finite = (v) => Number.isFinite(Number(v));
  const promoted = (row) => row?.status === 'PROMOTED';
  const sourceKey = (row, i) => row?.source_digest || `UNKNOWN_SOURCE_${i}`;
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function marginPct(row) {
    if (!finite(row?.candidate_eval_loss) || !finite(row?.incumbent_eval_loss)) return null;
    const candidate = Number(row.candidate_eval_loss);
    const incumbent = Number(row.incumbent_eval_loss);
    return 100 * (incumbent - candidate) / Math.max(Math.abs(incumbent), 1e-12);
  }

  function short(s, n = 12) {
    s = String(s || '—');
    return s.length > n ? `${s.slice(0, n)}…` : s;
  }

  function fmtPct(v) {
    if (!finite(v)) return '—';
    const n = Number(v);
    const digits = Math.abs(n) >= 10 ? 1 : Math.abs(n) >= 1 ? 2 : 3;
    return `${n > 0 ? '+' : ''}${n.toFixed(digits)}%`;
  }

  async function fetchModel() {
    const res = await fetch(`${MODEL_URL}?v=${Date.now()}`, { cache: 'no-store', headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error(`MODEL_STATE_HTTP_${res.status}`);
    return res.json();
  }

  function ensureStyle() {
    if ($('brain-visual-v3-style')) return;
    const style = document.createElement('style');
    style.id = 'brain-visual-v3-style';
    style.textContent = `
      #loss-chart{min-height:300px;position:relative;overflow:hidden;border-radius:12px;background:linear-gradient(180deg,rgba(12,28,25,.22),rgba(4,8,10,.04))}
      #loss-chart svg{display:block;width:100%;height:300px;overflow:visible}
      #loss-chart .v3-grid{stroke:rgba(135,160,158,.14);stroke-width:1;vector-effect:non-scaling-stroke}
      #loss-chart .v3-zero{stroke:rgba(236,247,245,.48);stroke-width:1.4;vector-effect:non-scaling-stroke}
      #loss-chart .v3-tolerance{fill:rgba(68,232,182,.055);stroke:rgba(68,232,182,.18);stroke-width:1;vector-effect:non-scaling-stroke}
      #loss-chart .v3-trend{fill:none;stroke:rgba(89,236,191,.55);stroke-width:1.7;vector-effect:non-scaling-stroke}
      #loss-chart .v3-stem{stroke-width:1.35;opacity:.78;vector-effect:non-scaling-stroke}
      #loss-chart .v3-stem.promoted{stroke:var(--green,#55eeb6)}
      #loss-chart .v3-stem.rejected{stroke:var(--amber,#f4be5b)}
      #loss-chart .v3-dot{vector-effect:non-scaling-stroke;stroke-width:1.7}
      #loss-chart .v3-dot.promoted{fill:rgba(7,18,15,.92);stroke:var(--green,#55eeb6)}
      #loss-chart .v3-dot.rejected{fill:rgba(18,14,7,.92);stroke:var(--amber,#f4be5b)}
      #loss-chart .v3-dot.latest{stroke-width:2.6;filter:drop-shadow(0 0 4px currentColor)}
      #loss-chart .v3-status.promoted{fill:var(--green,#55eeb6);opacity:.82}
      #loss-chart .v3-status.rejected{fill:var(--amber,#f4be5b);opacity:.72}
      #loss-chart .v3-axis{font:500 10px "IBM Plex Mono",monospace;fill:rgba(173,195,192,.72)}
      #loss-chart .v3-axis.zero{fill:rgba(235,248,245,.9)}
      #loss-chart .v3-zone{font:600 10px "IBM Plex Mono",monospace;letter-spacing:.08em}
      #loss-chart .v3-zone.good{fill:rgba(85,238,182,.84)}
      #loss-chart .v3-zone.bad{fill:rgba(244,190,91,.82)}
      #loss-chart .v3-latest-box{fill:rgba(7,15,15,.88);stroke:rgba(116,207,180,.32);stroke-width:1;vector-effect:non-scaling-stroke}
      #loss-chart .v3-latest-title{font:600 10px "IBM Plex Mono",monospace;fill:rgba(221,245,237,.9)}
      #loss-chart .v3-latest-value{font:600 13px "IBM Plex Mono",monospace;fill:var(--green,#55eeb6)}
      #loss-chart .v3-latest-value.rejected{fill:var(--amber,#f4be5b)}
      .chart-legend .v3-legend-note{color:var(--muted,#76918d)}
      .chart-card[data-brain-visual="v3"] .chart-truth{line-height:1.45}
    `;
    document.head.appendChild(style);
  }

  function installLabels() {
    const card = $('loss-chart')?.closest('.chart-card');
    if (!card) return;
    card.dataset.brainVisual = 'v3';
    const h3 = card.querySelector('.card-title-row h3');
    if (h3) h3.textContent = 'DECISION ADVANTAGE · CANDIDATE VS INCUMBENT';
    const legend = card.querySelector('.chart-legend');
    if (legend) legend.innerHTML = '<span class="legend-promoted">PROMOTED</span><span class="legend-rejected">REJECTED</span><span class="v3-legend-note">0% = incumbent · shaded band = ±0.2% adaptive tolerance</span>';
    const truth = card.querySelector('.chart-truth');
    if (truth) truth.textContent = 'THIS GRAPH SHOWS SAME-ATTEMPT RELATIVE ADVANTAGE, NOT ABSOLUTE INTELLIGENCE. ABOVE 0 = LOWER ADAPTIVE LOSS THAN THE INCUMBENT; BELOW 0 = HIGHER LOSS. COLOR IS THE PERSISTED FINAL GATE VERDICT, WHICH ALSO DEPENDS ON THE FROZEN ANCHOR.';
  }

  function niceScale(values) {
    const maxAbs = Math.max(ADAPTIVE_TOLERANCE_PCT * 1.8, ...values.map((v) => Math.abs(v)));
    const rough = maxAbs * 1.12;
    const powers = [0.05,0.1,0.2,0.5,1,2,5,10,20,50,100];
    return powers.find((p) => p >= rough) || Math.ceil(rough / 100) * 100;
  }

  function render() {
    if (state.rendering) return;
    const chart = $('loss-chart');
    const m = state.model;
    if (!chart || !m) return;
    const history = (Array.isArray(m.history) ? m.history : []).filter((row) => finite(marginPct(row)));
    if (!history.length) return;

    state.rendering = true;
    try {
      ensureStyle();
      installLabels();

      const margins = history.map(marginPct);
      const scale = niceScale(margins);
      const W = Math.max(900, Math.round(chart.clientWidth || 1200));
      const H = 300, left = 62, right = 24, top = 24, bottom = 46;
      const plotBottom = H - bottom;
      const plotH = plotBottom - top;
      const x = (i) => left + (history.length === 1 ? (W-left-right)/2 : i * (W-left-right)/(history.length-1));
      const y = (v) => top + (scale - v) * plotH / (2 * scale);
      const zeroY = y(0);
      const attemptCount = Number(m.attempt_count);
      const startAttempt = Number.isInteger(attemptCount) && attemptCount >= history.length ? attemptCount - history.length + 1 : 1;
      const sourceChanges = history.reduce((n,row,i) => n + (i > 0 && sourceKey(row,i) !== sourceKey(history[i-1],i-1) ? 1 : 0), 0);

      const tolTop = y(ADAPTIVE_TOLERANCE_PCT);
      const tolBottom = y(-ADAPTIVE_TOLERANCE_PCT);
      const tolerance = `<rect class="v3-tolerance" x="${left}" y="${tolTop}" width="${W-left-right}" height="${Math.max(1,tolBottom-tolTop)}" rx="4"/>`;

      const gridVals = [scale, scale/2, 0, -scale/2, -scale];
      const grid = gridVals.map((v) => {
        const cls = v === 0 ? 'v3-zero' : 'v3-grid';
        return `<line class="${cls}" x1="${left}" x2="${W-right}" y1="${y(v)}" y2="${y(v)}"/><text class="v3-axis${v===0?' zero':''}" x="${left-10}" y="${y(v)+3}" text-anchor="end">${esc(fmtPct(v))}</text>`;
      }).join('');

      const trendPts = margins.map((v,i) => `${x(i)},${y(v)}`).join(' ');
      const trend = `<polyline class="v3-trend" points="${trendPts}"/>`;

      const stemsAndDots = margins.map((margin,i) => {
        const row = history[i];
        const cls = promoted(row) ? 'promoted' : 'rejected';
        const latest = i === history.length - 1 ? ' latest' : '';
        const attempt = startAttempt + i;
        const candidate = Number(row.candidate_eval_loss);
        const incumbent = Number(row.incumbent_eval_loss);
        const title = `attempt ${attempt} · adaptive edge ${fmtPct(margin)} · candidate ${candidate.toFixed(6)} · incumbent ${incumbent.toFixed(6)} · ${row.status || 'UNKNOWN'} · source ${short(sourceKey(row,i),18)}`;
        return `<line class="v3-stem ${cls}" x1="${x(i)}" x2="${x(i)}" y1="${zeroY}" y2="${y(margin)}"><title>${esc(title)}</title></line><circle class="v3-dot ${cls}${latest}" cx="${x(i)}" cy="${y(margin)}" r="${i===history.length-1?5.2:3.4}"><title>${esc(title)}</title></circle>`;
      }).join('');

      const statusY = H - 19;
      const statusW = Math.max(2.2, Math.min(8, (W-left-right)/history.length * 0.58));
      const statusStrip = history.map((row,i) => `<rect class="v3-status ${promoted(row)?'promoted':'rejected'}" x="${x(i)-statusW/2}" y="${statusY}" width="${statusW}" height="6" rx="2"><title>attempt ${startAttempt+i} · ${esc(row.status || 'UNKNOWN')}</title></rect>`).join('');

      const tickEvery = history.length <= 20 ? 2 : history.length <= 40 ? 4 : 8;
      const tickSet = new Set([0, history.length - 1]);
      for (let i = 0; i < history.length; i += tickEvery) tickSet.add(i);
      const ticks = [...tickSet].sort((a,b)=>a-b).map((i) => `<line class="v3-grid" x1="${x(i)}" x2="${x(i)}" y1="${plotBottom+2}" y2="${plotBottom+7}"/><text class="v3-axis" x="${x(i)}" y="${plotBottom+20}" text-anchor="middle">${startAttempt+i}</text>`).join('');

      const latestIndex = history.length - 1;
      const latestRow = history[latestIndex];
      const latestMargin = margins[latestIndex];
      const latestCls = promoted(latestRow) ? '' : ' rejected';
      const boxW = 252, boxH = 47, boxX = Math.max(left+8, W-right-boxW-8), boxY = top+8;
      const latestBox = `<rect class="v3-latest-box" x="${boxX}" y="${boxY}" width="${boxW}" height="${boxH}" rx="8"/><text class="v3-latest-title" x="${boxX+12}" y="${boxY+17}">LATEST #${startAttempt+latestIndex} · ${esc(latestRow.status || 'UNKNOWN')}</text><text class="v3-latest-value${latestCls}" x="${boxX+12}" y="${boxY+36}">${esc(fmtPct(latestMargin))} adaptive edge</text>`;

      const zones = `<text class="v3-zone good" x="${left+8}" y="${top+13}">BETTER THAN INCUMBENT ↑</text><text class="v3-zone bad" x="${left+8}" y="${plotBottom-8}">WORSE THAN INCUMBENT ↓</text>`;
      const labels = `<text class="v3-axis" x="${W-right}" y="${tolTop-5}" text-anchor="end">+0.2% adaptive tolerance</text><text class="v3-axis" x="${W-right}" y="${H-7}" text-anchor="end">final gate verdict strip</text>`;

      chart.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" aria-label="JANUS decision advantage chart">${tolerance}${grid}${zones}${trend}${stemsAndDots}${ticks}${statusStrip}${latestBox}${labels}</svg>`;
      chart.dataset.visualOwner = BUILD;

      const axis = $('loss-axis');
      if (axis) axis.innerHTML = `<span>↑ positive = candidate adaptive loss lower</span><span>attempts ${startAttempt}–${startAttempt+history.length-1} · ${history.length} recent / ${Number.isInteger(attemptCount)?attemptCount:history.length} lifetime</span><span>↓ negative = candidate adaptive loss higher</span>`;
      const summary = $('brain-lineage-summary');
      if (summary) summary.textContent = `${history.length} recent · ${m.promotion_count ?? '?'} promoted lifetime · ${m.rejection_count ?? '?'} rejected lifetime · ${sourceChanges} source changes`;
    } finally {
      state.rendering = false;
    }
  }

  async function refresh() {
    try {
      state.model = await fetchModel();
      render();
    } catch (err) {
      console.warn('JANUS_BRAIN_VISUAL_V3_UNRESOLVED', err);
    }
  }

  function boot() {
    ensureStyle();
    installLabels();
    setTimeout(refresh, 100);
    setInterval(refresh, REFRESH_MS);

    const chart = $('loss-chart');
    if (chart) {
      const observer = new MutationObserver(() => {
        if (state.rendering || !state.model) return;
        const svg = chart.querySelector('svg');
        if (!svg || svg.getAttribute('aria-label') !== 'JANUS decision advantage chart') setTimeout(render, 0);
      });
      observer.observe(chart, { childList: true, subtree: true });
    }

    if ('ResizeObserver' in window && chart) {
      let timer = null;
      new ResizeObserver(() => {
        clearTimeout(timer);
        timer = setTimeout(render, 100);
      }).observe(chart);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
