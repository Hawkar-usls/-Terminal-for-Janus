(() => {
  'use strict';

  const BACKEND_RUNS =
    'https://api.github.com/repos/Hawkar-usls/Janus-Demiurge/actions/runs?branch=main&per_page=100';
  const SNAPSHOT = './data/keymaster-automation.json';
  const REFRESH_MS = 30000;
  const SNAPSHOT_STALE_MS = 30 * 60 * 1000;
  const RUN_STALE_MS = 90 * 60 * 1000;

  const esc = (v) => String(v ?? '—').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  const fmt = (v) => {
    if (!v) return '—';
    const d = new Date(v);
    return Number.isNaN(+d)
      ? String(v)
      : d.toISOString().replace('T', ' ').replace('.000Z', 'Z');
  };

  const hay = (r) =>
    `${r?.name || ''} ${r?.display_title || ''} ${r?.path || ''}`.toLowerCase();

  function findRun(runs, predicate) {
    return (runs || []).find((r) => predicate(hay(r)));
  }

  function stateOf(r) {
    if (!r) return 'NOT SEEN';
    return String(r.status).toLowerCase() === 'completed'
      ? String(r.conclusion || 'completed').toUpperCase()
      : String(r.status || 'unknown').toUpperCase();
  }

  function nextScheduled(minute) {
    const d = new Date();
    d.setUTCSeconds(0, 0);
    if (d.getUTCMinutes() < minute) {
      d.setUTCMinutes(minute);
    } else {
      d.setUTCHours(d.getUTCHours() + 1, minute, 0, 0);
    }
    return fmt(d.toISOString());
  }

  function statusClass(v) {
    const s = String(v || '').toUpperCase();
    if (s.includes('FAIL') || s.includes('DOWN') || s.includes('ERROR')) return 'keymaster-auto-state-down';
    if (s.includes('IDLE') || s.includes('WAIT') || s.includes('STALE') || s.includes('NO_CANDIDATE') || s.includes('DEFER')) return 'keymaster-auto-state-idle';
    if (s.includes('SUCCESS') || s.includes('LIVE') || s.includes('PASS') || s.includes('RUNNING') || s.includes('IN_PROGRESS') || s.includes('NEW_CANDIDATE')) return 'keymaster-auto-state-live';
    return '';
  }

  function ensureStyle() {
    if (document.getElementById('keymaster-automation-style')) return;
    const style = document.createElement('style');
    style.id = 'keymaster-automation-style';
    style.textContent = `
      .keymaster-automation{margin:10px 0 14px;border:1px solid rgba(93,255,197,.35);border-left:3px solid #5dffc5;background:rgba(4,18,19,.72);padding:10px 12px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
      .keymaster-auto-head{display:flex;justify-content:space-between;gap:12px;align-items:center;font-size:10px;letter-spacing:.12em;color:#7ea6b6}
      .keymaster-auto-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-top:8px}
      .keymaster-auto-cell{border:1px solid rgba(89,198,220,.22);padding:7px 8px;min-width:0}
      .keymaster-auto-cell span{display:block;font-size:9px;color:#739aaa;letter-spacing:.08em}
      .keymaster-auto-cell strong{display:block;margin-top:3px;color:#d9fbff;font-size:10px;overflow-wrap:anywhere}
      .keymaster-auto-foot{margin-top:8px;font-size:9px;color:#739aaa;letter-spacing:.06em}
      .keymaster-auto-state-live{color:#5dffc5!important}
      .keymaster-auto-state-idle{color:#ffd166!important}
      .keymaster-auto-state-stale{color:#ffd166!important}
      .keymaster-auto-state-down{color:#ff5268!important}
    `;
    document.head.appendChild(style);
  }

  function ensurePanel() {
    const host = document.querySelector('#keymaster-panel, .keymaster-observatory');
    if (!host) return null;
    let box = host.querySelector('[data-keymaster-automation]');
    if (!box) {
      box = document.createElement('section');
      box.setAttribute('data-keymaster-automation', '');
      box.className = 'keymaster-automation';
      const head = host.querySelector('.card-title-row, .keymaster-observatory-head');
      head ? head.after(box) : host.prepend(box);
    }
    return box;
  }

  async function load() {
    try {
      const r = await fetch(`${SNAPSHOT}?ts=${Date.now()}`, { cache: 'no-store' });
      if (!r.ok) throw new Error(`snapshot ${r.status}`);
      const payload = await r.json();
      if (!Array.isArray(payload.workflow_runs) || !payload.workflow_runs.length) {
        throw new Error('snapshot empty');
      }
      return { payload, source: payload.source || 'TERMINAL SNAPSHOT' };
    } catch (_) {
      const r = await fetch(BACKEND_RUNS, {
        cache: 'no-store',
        headers: { Accept: 'application/vnd.github+json' }
      });
      if (!r.ok) throw new Error(`github ${r.status}`);
      const raw = await r.json();
      return {
        payload: {
          generated_at: new Date().toISOString(),
          workflow_runs: raw.workflow_runs || []
        },
        source: 'GITHUB API FALLBACK'
      };
    }
  }

  function field(k, v, klass = '') {
    return `<div class="keymaster-auto-cell"><span>${esc(k)}</span><strong class="${klass}">${esc(v)}</strong></div>`;
  }

  async function render() {
    ensureStyle();
    const box = ensurePanel();
    if (!box) return;

    try {
      const { payload, source } = await load();
      const runs = payload.workflow_runs || [];
      const forgeSemantic = payload.forge_semantic || null;
      const materializerSemantic = payload.materializer_semantic || null;
      const attackSemantic = payload.attack_semantic || null;

      const materializer = findRun(runs, (s) => s.includes('keymaster') && s.includes('materializ'));
      const attacker = findRun(runs, (s) => s.includes('keymaster') && s.includes('attack'));
      const forge = findRun(runs, (s) => s.includes('keymaster') && (s.includes('forge') || s.includes('autonomous')));
      const latest = [materializer, attacker, forge]
        .filter(Boolean)
        .sort((a, b) => new Date(b.run_started_at || b.created_at || 0) - new Date(a.run_started_at || a.created_at || 0))[0];

      const generatedAt = payload.generated_at ? new Date(payload.generated_at).getTime() : NaN;
      const latestRunAt = latest ? new Date(latest.run_started_at || latest.created_at || 0).getTime() : NaN;
      const snapshotFresh = Number.isFinite(generatedAt) && (Date.now() - generatedAt) <= SNAPSHOT_STALE_MS;
      const runFresh = Number.isFinite(latestRunAt) && (Date.now() - latestRunAt) <= RUN_STALE_MS;
      const live = snapshotFresh || runFresh;
      const automation = live ? 'LIVE' : 'STALE';
      const automationClass = live ? 'keymaster-auto-state-live' : 'keymaster-auto-state-stale';

      const forgeState = forgeSemantic?.status || stateOf(forge);
      const materializerState = materializerSemantic?.status || stateOf(materializer);
      const attackerState = attackSemantic?.status || stateOf(attacker);
      const nextAction = attackSemantic?.next_action || forgeSemantic?.next_action || materializerSemantic?.next_action || '—';
      const candidateId = forgeSemantic?.candidate?.candidate_id || forgeSemantic?.candidate_id || materializerSemantic?.candidate_id || '—';
      const cycleCount = forgeSemantic?.cycle_count ?? '—';
      const candidateCount = forgeSemantic?.candidate_proposal_count ?? '—';
      const distinctCount = forgeSemantic?.distinct_candidate_count ?? '—';
      const deferredCount = forgeSemantic?.deferred_candidate_count ?? '—';
      const falsifiedCount = forgeSemantic?.mathematically_falsified_candidate_count ?? '—';
      const variantFalsified = forgeSemantic?.materialized_variant_falsified_count ?? '—';
      const attackAdvance = attackSemantic?.advance_forge;
      const attackAdvanceText = attackAdvance === true ? 'TRUE' : attackAdvance === false ? 'FALSE' : '—';

      box.innerHTML = `
        <div class="keymaster-auto-head">
          <b>AUTONOMY TELEMETRY · LIVE SEARCH ACTIVITY</b>
          <b class="${automationClass}">${automation}</b>
        </div>
        <div class="keymaster-auto-grid">
          ${field('AUTOMATION', automation, automationClass)}
          ${field('FORGE', forgeState, statusClass(forgeState))}
          ${field('MATERIALIZER', materializerState, statusClass(materializerState))}
          ${field('ATTACKER', attackerState, statusClass(attackerState))}
          ${field('ATTACK → ADVANCE FORGE', attackAdvanceText, statusClass(attackAdvanceText === 'TRUE' ? 'LIVE' : attackAdvanceText))}
          ${field('NEXT ACTION', nextAction, statusClass(nextAction))}
          ${field('CYCLES', cycleCount)}
          ${field('CANDIDATE PROPOSALS', candidateCount)}
          ${field('DISTINCT CANDIDATES', distinctCount)}
          ${field('DEFERRED', deferredCount)}
          ${field('MATH FALSIFIED', falsifiedCount)}
          ${field('VARIANT FALSIFIED', variantFalsified)}
          ${field('CURRENT CANDIDATE', candidateId)}
          ${field('LAST RUN', fmt(latest?.run_started_at || latest?.created_at))}
          ${field('RUN ID', latest?.id ?? '—')}
          ${field('LAST SYNC', fmt(payload.generated_at))}
          ${field('NEXT FORGE', nextScheduled(43))}
          ${field('NEXT MATERIALIZER', nextScheduled(13))}
          ${field('SOURCE', source)}
        </div>
        <div class="keymaster-auto-foot">SEARCH ACTIVITY != MATHEMATICAL PROGRESS · PROVEN Δ REMAINS SEPARATE · P_VS_NP=OPEN UNTIL PROOF-CARRYING ADMISSION</div>`;
    } catch (err) {
      box.innerHTML = `
        <div class="keymaster-auto-head"><b>AUTONOMY TELEMETRY</b><b class="keymaster-auto-state-down">DOWN</b></div>
        <div class="keymaster-auto-grid">
          ${field('AUTOMATION', 'DOWN', 'keymaster-auto-state-down')}
          ${field('ERROR', err?.message || String(err))}
        </div>`;
    }
  }

  const start = () => {
    render();
    setInterval(render, REFRESH_MS);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
