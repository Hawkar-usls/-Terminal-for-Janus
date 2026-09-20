(() => {
  'use strict';

  const FUNDAMENTUM_RAW = 'https://raw.githubusercontent.com/Hawkar-usls/Janus-Fundamentum/main';
  const FUNDAMENTUM_API = 'https://api.github.com/repos/Hawkar-usls/Janus-Fundamentum';
  const DEMIURGE_RAW = 'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main';
  const TERMINAL_RAW = 'https://raw.githubusercontent.com/Hawkar-usls/-Terminal-for-Janus/main';
  const REFRESH_MS = 60_000;

  const URLS = {
    contract: `${TERMINAL_RAW}/config/JANUS_RESEARCH_LANES.json`,
    fundamentumStatus: `${FUNDAMENTUM_RAW}/docs/CURRENT_RESEARCH_STATUS.md`,
    fundamentumBranch: `${FUNDAMENTUM_API}/branches/main`,
    researchSpine: `${DEMIURGE_RAW}/janus_model/state/JANUS_RESEARCH_SPINE.json`,
    latestDecision: `${DEMIURGE_RAW}/janus_model/state/JANUS_LATEST_DECISION.json`,
  };

  const state = {
    contract: null,
    fundamentumText: null,
    fundamentumHead: null,
    spine: null,
    decision: null,
    refreshedAt: null,
    status: 'UNRESOLVED',
    error: null,
    inFlight: false,
  };

  const $ = (id) => document.getElementById(id);
  const esc = (v) => String(v ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  const short = (v, n = 14) => {
    const s = String(v || '—');
    return s.length > n ? `${s.slice(0, n)}…` : s;
  };
  const set = (id, v) => { const el = $(id); if (el) el.textContent = v ?? '—'; };

  function cacheBust(url) {
    return `${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}`;
  }

  async function fetchJson(url, optional = false) {
    try {
      const res = await fetch(cacheBust(url), {
        cache: 'no-store',
        headers: { Accept: 'application/json, application/vnd.github+json' },
      });
      if (!res.ok) throw new Error(`${res.status} ${url}`);
      return await res.json();
    } catch (err) {
      if (optional) return null;
      throw err;
    }
  }

  async function fetchText(url) {
    const res = await fetch(cacheBust(url), { cache: 'no-store' });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return await res.text();
  }

  function validateContract(x) {
    if (!x || x.schema !== 'janus.terminal.research_lanes.v1') throw new Error('RESEARCH_LANE_CONTRACT_SCHEMA_MISMATCH');
    const f = x.lanes?.fundamentum_mirror || {};
    const j = x.lanes?.janus_independent || {};
    if (f.mode !== 'SOURCE_BOUND_READ_ONLY') throw new Error('FUNDAMENTUM_MIRROR_MODE_REJECTED');
    if (f.inherits_into_janus_claims !== false || f.direct_mutation !== false) throw new Error('FUNDAMENTUM_MIRROR_AUTHORITY_VIOLATION');
    if (j.mode !== 'INDEPENDENT_CANDIDATE_RESEARCH') throw new Error('JANUS_RESEARCH_MODE_REJECTED');
    if (j.truth_authority !== false || j.proof_authority !== false || j.direct_target_mutation !== false) throw new Error('JANUS_RESEARCH_AUTHORITY_VIOLATION');
    return x;
  }

  function validateSpine(x) {
    if (!x || x.schema !== 'janus.research_spine.v1') throw new Error('RESEARCH_SPINE_SCHEMA_MISMATCH');
    const policy = x.improvement_policy || {};
    if (policy.autonomous_merge !== false || policy.direct_target_main_write !== false) throw new Error('RESEARCH_SPINE_MUTATION_CEILING_VIOLATION');
    if (x.claim_ceiling?.model_selection_is_verified_fix !== false) throw new Error('RESEARCH_SPINE_VERIFICATION_CEILING_VIOLATION');
    return x;
  }

  function capture(text, name, fallback = 'UNRESOLVED') {
    const pattern = new RegExp(`${name}\\s*=\\s*([^\\n\\r]+)`, 'm');
    const m = String(text || '').match(pattern);
    return m ? m[1].trim().replace(/^`|`$/g, '') : fallback;
  }

  function currentFundamentumSummary() {
    const text = state.fundamentumText || '';
    return {
      pVsNp: capture(text, 'P_VS_NP'),
      a3Replication: capture(text, 'A3_EXTERNAL_REPLICATION'),
      a3Novelty: capture(text, 'A3_WORLD_NOVELTY_N4'),
      c023LowerBound: capture(text, 'C023_ASYMPTOTIC_LOWER_BOUND'),
      c023Baseline: capture(text, 'C023_RESEARCH_BASELINE'),
    };
  }

  function boundFundamentum() {
    return state.spine?.research_spine?.fundamentum || null;
  }

  function bindingStatus() {
    const live = state.fundamentumHead;
    const bound = boundFundamentum()?.commit;
    if (!live || !bound) return 'UNRESOLVED';
    return live === bound ? 'CURRENT' : 'STALE_BINDING';
  }

  function sourceStatusClass(status) {
    if (status === 'CURRENT') return 'live';
    if (status === 'STALE_BINDING') return 'warn';
    return '';
  }

  function renderFundamentum() {
    const summary = currentFundamentumSummary();
    const bound = boundFundamentum() || {};
    const bind = bindingStatus();
    set('research-fundamentum-head', short(state.fundamentumHead, 20));
    set('research-fundamentum-bound', short(bound.commit, 20));
    set('research-fundamentum-binding', bind);
    set('research-fundamentum-pnp', summary.pVsNp);
    set('research-fundamentum-a3', `${summary.a3Replication} · novelty ${summary.a3Novelty}`);
    set('research-fundamentum-c023', `${summary.c023LowerBound} · ${short(summary.c023Baseline, 14)}`);

    const badge = $('research-fundamentum-binding');
    if (badge) {
      badge.classList.remove('live', 'warn');
      const cls = sourceStatusClass(bind);
      if (cls) badge.classList.add(cls);
    }

    const keyFiles = Array.isArray(bound.key_files) ? bound.key_files : [];
    const box = $('research-fundamentum-files');
    if (box) {
      box.innerHTML = keyFiles.length
        ? keyFiles.map((f) => `<div class="kv-row"><span>${esc(f.path || '—')}</span><b>${esc(f.status || 'BOUND')} · ${esc(short(f.sha256, 16))}</b></div>`).join('')
        : '<div class="empty-state">No persisted Fundamentum key-file binding in the current Demiurge research spine.</div>';
    }
  }

  function renderIndependent() {
    const spine = state.spine || {};
    const decision = state.decision || {};
    const routes = Array.isArray(spine.hypothesis_routes) ? spine.hypothesis_routes : [];
    const rs = spine.research_spine || {};
    const arxiv = rs.arxiv || {};
    const wiki = rs.wikipedia || {};
    const synthCount = spine.external_context?.semantic_synthesis_candidate_count;
    const selected = decision.selected || {};

    set('research-janus-status', spine.status || 'UNRESOLVED');
    set('research-janus-context', short(spine.context_sha256, 20));
    set('research-janus-routes', routes.length);
    set('research-janus-arxiv', arxiv.status || 'UNRESOLVED');
    set('research-janus-wikipedia', wiki.status || 'UNRESOLVED');
    set('research-janus-synth', Number.isFinite(Number(synthCount)) ? String(synthCount) : '—');
    set('research-janus-decision', `${selected.candidate_id || 'NO_ACTION'} · ${decision.status || 'UNRESOLVED'}`);

    const box = $('research-janus-route-list');
    if (box) {
      const recent = routes.slice(-8).reverse();
      box.innerHTML = recent.length
        ? recent.map((r, i) => `<div class="log-row"><span class="log-seq">#R${String(i + 1).padStart(2, '0')}</span><span class="log-type">OWN</span><span class="log-body">${esc(r)}</span><span class="log-verdict warn">CANDIDATE</span></div>`).join('')
        : '<div class="empty-state">No independent hypothesis routes persisted. Silence is not negative evidence.</div>';
    }
  }

  function renderBoundary() {
    const bind = bindingStatus();
    set('research-live-status', bind === 'STALE_BINDING' ? 'LIVE SOURCE · SPINE STALE' : bind === 'CURRENT' ? 'SOURCE + OWN LANES CURRENT' : 'PARTIAL / UNRESOLVED');
    set('research-refresh-time', state.refreshedAt ? state.refreshedAt.toLocaleTimeString() : '—');
    const boundary = $('research-boundary');
    if (boundary) {
      boundary.innerHTML = [
        '<div class="law">FUNDAMENTUM MIRROR = SOURCE-BOUND RESEARCH STATE, NOT JANUS OWN DISCOVERY.</div>',
        '<div class="law">JANUS INDEPENDENT RESEARCH = CANDIDATE QUESTIONS / LITERATURE CONTEXT / MODEL SELECTION, NOT FUNDAMENTUM THEOREM AUTHORITY.</div>',
        '<div class="law">FUNDAMENTUM → JANUS = CONTEXT WITH PROVENANCE ONLY.</div>',
        '<div class="law">JANUS → FUNDAMENTUM = PROPOSAL ONLY; TARGET LOCAL VERIFY REQUIRED BEFORE PASS.</div>',
        '<div class="law">STALE SOURCE BINDING MUST BE SHOWN, NEVER SILENTLY TREATED AS CURRENT.</div>',
      ].join('');
    }
  }

  function renderAll() {
    renderFundamentum();
    renderIndependent();
    renderBoundary();
  }

  async function loadAll() {
    const [contract, statusText, branch, spine, decision] = await Promise.all([
      fetchJson(URLS.contract),
      fetchText(URLS.fundamentumStatus),
      fetchJson(URLS.fundamentumBranch, true),
      fetchJson(URLS.researchSpine),
      fetchJson(URLS.latestDecision, true),
    ]);
    state.contract = validateContract(contract);
    state.fundamentumText = statusText;
    state.fundamentumHead = branch?.commit?.sha || null;
    state.spine = validateSpine(spine);
    state.decision = decision;
    state.refreshedAt = new Date();
    state.status = 'READY';
    state.error = null;
  }

  async function refresh() {
    if (state.inFlight) return;
    state.inFlight = true;
    const btn = $('research-refresh');
    btn?.classList.add('loading-shimmer');
    try {
      await loadAll();
      renderAll();
    } catch (err) {
      state.status = 'UNRESOLVED';
      state.error = err?.message || String(err);
      console.warn('JANUS_RESEARCH_OBSERVATORY_UNRESOLVED', err);
      set('research-live-status', 'UNRESOLVED · NO CLAIM');
      const own = $('research-janus-route-list');
      if (own) own.innerHTML = `<div class="empty-state">Research observatory unresolved: ${esc(state.error)}. Silence is not negative evidence.</div>`;
    } finally {
      state.inFlight = false;
      btn?.classList.remove('loading-shimmer');
    }
  }

  function installView() {
    if ($('view-research')) return;
    const nav = document.querySelector('.sidebar');
    const memoryButton = nav?.querySelector('[data-view="memory"]');
    if (nav && memoryButton) {
      const button = document.createElement('button');
      button.className = 'nav-btn';
      button.dataset.view = 'research';
      button.type = 'button';
      button.innerHTML = '<span class="nav-icon">⌬</span><span>RESEARCH</span>';
      nav.insertBefore(button, memoryButton);
    }

    const workspace = document.querySelector('.workspace');
    if (!workspace) return;
    const section = document.createElement('section');
    section.id = 'view-research';
    section.className = 'view cards-view observatory-view';
    section.innerHTML = `
      <div class="observatory-head">
        <div><div class="kicker">Two-lane research provenance</div><h2>Research Observatory</h2><p>Live Fundamentum source state and JANUS independent research are displayed separately. Cross-feed is contextual only and never transfers theorem or truth authority.</p></div>
        <div class="live-badge"><span class="dot"></span><span id="research-live-status">RESOLVING</span></div>
      </div>
      <div class="metrics-grid compact">
        <article class="metric-card"><label>Fundamentum live head</label><strong id="research-fundamentum-head">—</strong><small>GitHub main branch</small></article>
        <article class="metric-card"><label>Demiurge bound source</label><strong id="research-fundamentum-bound">—</strong><small>persisted research-spine binding</small></article>
        <article class="metric-card"><label>binding freshness</label><strong id="research-fundamentum-binding">—</strong><small>stale is surfaced, never hidden</small></article>
        <article class="metric-card"><label>last refresh</label><strong id="research-refresh-time">—</strong><small>60s public witness refresh</small></article>
      </div>
      <div class="cards-grid">
        <article class="card wide">
          <div class="card-title-row"><h3>FUNDAMENTUM MIRROR · SOURCE LANE</h3><span class="pill">READ ONLY</span></div>
          <div class="kv-stack">
            <div class="kv-row"><span>P vs NP</span><b id="research-fundamentum-pnp">—</b></div>
            <div class="kv-row"><span>A3 publication track</span><b id="research-fundamentum-a3">—</b></div>
            <div class="kv-row"><span>C023 active mainline</span><b id="research-fundamentum-c023">—</b></div>
          </div>
          <div id="research-fundamentum-files" class="kv-stack"><div class="empty-state">Resolving source binding…</div></div>
        </article>
        <article class="card wide">
          <div class="card-title-row"><h3>JANUS INDEPENDENT RESEARCH · OWN LANE</h3><span class="pill">CANDIDATE ONLY</span></div>
          <div class="kv-stack">
            <div class="kv-row"><span>research spine</span><b id="research-janus-status">—</b></div>
            <div class="kv-row"><span>context digest</span><b id="research-janus-context">—</b></div>
            <div class="kv-row"><span>hypothesis routes</span><b id="research-janus-routes">—</b></div>
            <div class="kv-row"><span>arXiv lane</span><b id="research-janus-arxiv">—</b></div>
            <div class="kv-row"><span>Wikipedia lane</span><b id="research-janus-wikipedia">—</b></div>
            <div class="kv-row"><span>semantic candidates</span><b id="research-janus-synth">—</b></div>
            <div class="kv-row"><span>latest native decision</span><b id="research-janus-decision">—</b></div>
          </div>
        </article>
        <article class="card wide"><div class="card-title-row"><h3>LATEST OWN HYPOTHESIS ROUTES</h3><button id="research-refresh" class="btn" type="button">REFRESH RESEARCH</button></div><div id="research-janus-route-list" class="event-log"><div class="empty-state">Resolving JANUS independent research…</div></div></article>
        <article class="card wide"><h3>RESEARCH FIREWALL</h3><div id="research-boundary"></div></article>
      </div>`;
    workspace.appendChild(section);
  }

  function boot() {
    $('research-refresh')?.addEventListener('click', refresh);
    refresh();
    window.setInterval(refresh, REFRESH_MS);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  }

  installView();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();

  window.JANUS_RESEARCH_OBSERVATORY = {
    contract: 'config/JANUS_RESEARCH_LANES.json',
    fundamentum_lane: 'SOURCE_BOUND_READ_ONLY',
    janus_lane: 'INDEPENDENT_CANDIDATE_RESEARCH',
    stale_binding_is_visible: true,
    cross_lane_authority_inheritance: false,
  };
})();
