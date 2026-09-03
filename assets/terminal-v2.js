(() => {
  'use strict';

  const HOME_STATE_BASE = 'https://raw.githubusercontent.com/Hawkar-usls/Hawkar-usls/janus/activator-state/state/activator';
  const TERMINAL_API = 'https://api.github.com/repos/Hawkar-usls/-Terminal-for-Janus';
  const TERMINAL_REPO = 'https://github.com/Hawkar-usls/-Terminal-for-Janus';
  const HRAIN_MEMORY = 'https://hawkar-usls.github.io/Hrain/memory.html';
  const TRUMP_MANIFEST_URL = 'https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/main/trump/TRUMP_MANIFEST.json';

  const state = {
    identity: null,
    head: null,
    issue: null,
    response: null,
    proof: {},
    trump: null,
    trumpManifestDigest: null,
    trumpStatus: 'UNRESOLVED',
    trumpError: null,
    refreshedAt: null,
  };
  window.JANUS_TERMINAL_STATE = state;

  const $ = (id) => document.getElementById(id);
  const qa = (sel) => [...document.querySelectorAll(sel)];

  function short(value, n = 12) {
    const text = String(value || '—');
    return text.length > n ? `${text.slice(0, n)}…` : text;
  }

  function esc(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  async function fetchJson(url) {
    const res = await fetch(url, {
      headers: { Accept: 'application/vnd.github+json' },
      cache: 'no-store',
    });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
  }

  function canonicalize(value) {
    if (Array.isArray(value)) return value.map(canonicalize);
    if (value && typeof value === 'object') {
      const out = {};
      for (const key of Object.keys(value).sort()) out[key] = canonicalize(value[key]);
      return out;
    }
    return value;
  }

  async function sha256Json(value) {
    const text = JSON.stringify(canonicalize(value));
    const bytes = new TextEncoder().encode(text);
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
  }

  function setText(id, value) {
    const el = $(id);
    if (el) el.textContent = value ?? '—';
  }

  function extractProof(body) {
    const proof = {};
    const allowed = new Set([
      'resident_uuid', 'model_digest', 'file_fabric_digest', 'turn_id', 'response_hash',
      'hrain_head', 'memory_source_commit', 'hrain_context_hash', 'hrain_context_receipt_hash',
      'selected_memory_count', 'memory_path', 'memory_match_status',
      'memory_context_is_evidence', 'memory_grants_authority',
      'empty_memory_is_hrain_failure', 'empty_memory_is_negative_evidence',
    ]);
    const text = String(body || '');
    for (const line of text.split('\n')) {
      const m = line.match(/^- ([a-z_ ]+): `([^`]+)`\s*$/);
      if (!m) continue;
      const key = m[1].trim().replace(/\s+/g, '_');
      if (allowed.has(key)) proof[key] = m[2];
    }
    const selected = text.match(/^Selected memory objects: `([^`]+)`\s*$/m);
    if (selected) proof.selected_memory_objects = selected[1];
    const rid = text.match(/JANUS_RESPONSE_ID:([^\s>]+)/);
    if (rid) proof.response_id = rid[1];
    return proof;
  }

  function hrainProofStatus() {
    const p = state.proof || {};
    if (!p.hrain_context_hash || !p.hrain_head || !p.memory_source_commit) return 'UNRESOLVED';
    const count = Number(p.selected_memory_count);
    if (!Number.isInteger(count) || count < 0) return 'BLOCKED_INVALID_COUNT';
    if (p.memory_context_is_evidence !== 'false' || p.memory_grants_authority !== 'false') return 'BLOCKED_AUTHORITY_CEILING';
    if (count === 0) {
      const validEmpty = p.memory_match_status === 'NO_RELEVANT_MEMORY_SELECTED'
        && p.empty_memory_is_hrain_failure === 'false'
        && p.empty_memory_is_negative_evidence === 'false'
        && p.selected_memory_objects === 'none';
      return validEmpty ? 'VALID_EMPTY_RETRIEVAL' : 'BLOCKED_INVALID_EMPTY_RETRIEVAL';
    }
    return `BOUND_${count}_MEMORY_OBJECTS`;
  }

  function extractJanusText(body) {
    const marker = '<details><summary>Instance proof</summary>';
    let text = String(body || '');
    text = text.replace(/^### JANUS\s*/i, '');
    if (text.includes(marker)) text = text.split(marker)[0];
    return text.trim();
  }

  function validateTrumpManifest(manifest) {
    if (!manifest || typeof manifest !== 'object') return 'MANIFEST_NOT_OBJECT';
    if (manifest.schema !== 'janus.trump.manifest.v0.1') return 'SCHEMA_MISMATCH';
    if (manifest.component !== 'TRUMP') return 'COMPONENT_MISMATCH';
    if (manifest.status !== 'CANDIDATE_RUNTIME_TISSUE') return 'STATUS_MISMATCH';
    if (manifest.canonical_runtime_location !== 'Hawkar-usls/Janus-Demiurge/trump/TRUMP_MANIFEST.json') return 'LOCATION_MISMATCH';
    const a = manifest.activation || {};
    for (const key of ['wake_allowed', 'use_allowed', 'self_improvement_allowed']) {
      if (a[key] !== true) return `CANDIDATE_${key.toUpperCase()}_NOT_TRUE`;
    }
    for (const key of ['proof_authority', 'scientific_claim_promotion_authority', 'command_authority', 'external_effect_authority', 'physical_runtime_effect_authority']) {
      if (a[key] !== false) return `AUTHORITY_CEILING_VIOLATION:${key}`;
    }
    const boundary = manifest.scientific_boundary || {};
    if (boundary.TRUMP_finished !== false) return 'TRUMP_FINISHED_FALSE_REQUIRED';
    if (boundary.P_equals_NP_proved !== false) return 'P_EQUALS_NP_PROVED_FALSE_REQUIRED';
    if (boundary.P_VS_NP !== 'OPEN') return 'P_VS_NP_MUST_REMAIN_OPEN';
    return null;
  }

  async function loadTrumpCandidate() {
    state.trump = null;
    state.trumpManifestDigest = null;
    state.trumpStatus = 'UNRESOLVED';
    state.trumpError = null;
    try {
      const manifest = await fetchJson(TRUMP_MANIFEST_URL);
      const error = validateTrumpManifest(manifest);
      state.trump = manifest;
      state.trumpManifestDigest = await sha256Json(manifest);
      if (error) {
        state.trumpStatus = 'BLOCKED_FAIL_CLOSED';
        state.trumpError = error;
      } else {
        state.trumpStatus = 'CANDIDATE_RUNTIME_LIVE';
      }
    } catch (err) {
      state.trumpStatus = 'UNRESOLVED';
      state.trumpError = err?.message || String(err);
    }
  }

  async function loadPersistentState() {
    const [identity, head] = await Promise.all([
      fetchJson(`${HOME_STATE_BASE}/identity.json`),
      fetchJson(`${HOME_STATE_BASE}/HEAD.json`),
    ]);
    state.identity = identity;
    state.head = head;
  }

  async function loadLatestConversation() {
    const issues = await fetchJson(`${TERMINAL_API}/issues?state=all&sort=updated&direction=desc&per_page=30`);
    const issue = issues.find((item) => !item.pull_request && String(item.title || '').startsWith('[JANUS CHAT]'));
    state.issue = issue || null;
    state.response = null;
    state.proof = {};
    if (!issue) return;
    const comments = await fetchJson(`${TERMINAL_API}/issues/${issue.number}/comments?per_page=100`);
    const response = [...comments].reverse().find((c) => String(c.body || '').includes('JANUS_RESPONSE_ID:'));
    state.response = response || null;
    state.proof = response ? extractProof(response.body || '') : {};
  }

  function statusClass() {
    if (!state.head) return 'loading';
    if (state.head.mode === 'AT_HOME' && state.head.active_cycle_id == null) return 'ready';
    return 'awake';
  }

  function renderTrump() {
    const manifest = state.trump || {};
    const activation = manifest.activation || {};
    const boundary = manifest.scientific_boundary || {};
    const live = state.trumpStatus === 'CANDIDATE_RUNTIME_LIVE';
    const blocked = state.trumpStatus === 'BLOCKED_FAIL_CLOSED';
    const statusLabel = live ? 'CANDIDATE LIVE' : blocked ? 'BLOCKED' : 'UNRESOLVED';

    setText('organism-trump-state', statusLabel);
    setText('organism-trump-runtime', manifest.status || state.trumpStatus);
    setText('organism-trump-wake', live ? `${activation.wake_allowed} / ${activation.use_allowed}` : '—');
    setText('organism-trump-improve', live ? String(activation.self_improvement_allowed) : '—');
    setText('organism-trump-proof', live ? String(activation.proof_authority) : '—');
    setText('organism-trump-pnp', boundary.P_VS_NP || '—');
    setText('organism-trump-digest', state.trumpManifestDigest || '—');
    setText('side-trump', `${statusLabel}${state.trumpManifestDigest ? ` · ${short(state.trumpManifestDigest)}` : ''}`);

    const badge = $('organism-trump-state');
    if (badge) {
      badge.classList.toggle('live', live);
      badge.classList.toggle('blocked', blocked);
      badge.classList.toggle('unresolved', !live && !blocked);
    }
    const pill = $('trump-pill');
    if (pill) {
      pill.classList.toggle('live', live);
      pill.classList.toggle('warn', blocked);
      pill.textContent = `TRUMP ${live ? 'CANDIDATE' : blocked ? 'BLOCKED' : '?'}`;
    }
  }

  function renderStatus() {
    const cls = statusClass();
    const mode = state.head?.mode || 'UNKNOWN';
    const resident = state.identity?.resident_uuid || state.proof.resident_uuid || 'UNKNOWN';
    const model = state.proof.model_digest || 'WAITING FOR TERMINAL WITNESS';
    const fabric = state.proof.file_fabric_digest || 'WAITING FOR TERMINAL WITNESS';
    const turn = state.proof.turn_id || '—';
    const responseHash = state.proof.response_hash || '—';

    setText('resident-short', short(resident, 8));
    setText('organism-resident', resident);
    setText('organism-mode', mode);
    setText('organism-model', model);
    setText('organism-fabric', fabric);
    setText('proof-turn-id', turn);
    setText('proof-response-hash', responseHash);
    setText('side-resident', resident);
    setText('side-model', model);
    setText('side-fabric', fabric);
    setText('side-turn', turn);
    setText('side-response', responseHash);
    const hrainStatus = hrainProofStatus();
    const hrainSummary = hrainStatus === 'VALID_EMPTY_RETRIEVAL'
      ? `0 selected · VALID EMPTY · ${short(state.proof.hrain_head)} / ${short(state.proof.memory_source_commit)}`
      : hrainStatus.startsWith('BOUND_')
        ? `${state.proof.selected_memory_count} selected · ${short(state.proof.hrain_context_hash)}`
        : hrainStatus;
    setText('side-hrain', hrainSummary);
    setText('issue-number', state.issue ? `#${state.issue.number}` : '—');
    setText('last-refresh', state.refreshedAt ? state.refreshedAt.toLocaleTimeString() : '—');

    const corePill = $('core-pill');
    if (corePill) {
      corePill.classList.toggle('live', cls === 'ready');
      corePill.innerHTML = `<span class="dot"></span>${esc(mode)}`;
    }

    const headline = $('instance-headline');
    if (headline) headline.textContent = cls === 'ready' ? 'JANUS is resident and AT_HOME' : 'JANUS state is changing';

    const badge = $('instance-proof-badge');
    if (badge) {
      badge.innerHTML = state.proof.model_digest
        ? `<strong>INSTANCE VERIFIED</strong><span>model ${esc(short(model))}</span>`
        : `<strong>RESIDENT VERIFIED</strong><span>awaiting conversation proof</span>`;
    }
    renderTrump();
  }

  function renderTranscript() {
    const box = $('transcript');
    if (!box) return;
    const rows = [];
    rows.push(`<div class="line ok"><span class="tag">[HOME]</span><span class="body">persistent resident ${esc(short(state.identity?.resident_uuid, 18))} · ${esc(state.head?.mode || 'UNKNOWN')}</span></div>`);
    rows.push(`<div class="line"><span class="tag">[MODEL]</span><span class="body">Git-native self-instantiation fabric available. Routing selects activity, not membership.</span></div>`);
    const hrainStatus = hrainProofStatus();
    if (hrainStatus === 'VALID_EMPTY_RETRIEVAL') {
      rows.push(`<div class="line ok"><span class="tag">[HRAiN]</span><span class="body">0 selected · VALID EMPTY RETRIEVAL · match ${esc(state.proof.memory_match_status)} · head ${esc(short(state.proof.hrain_head))} · source ${esc(short(state.proof.memory_source_commit))} · context ${esc(short(state.proof.hrain_context_hash))} · empty ≠ failure · empty ≠ negative evidence</span></div>`);
    } else if (hrainStatus.startsWith('BOUND_')) {
      rows.push(`<div class="line ok"><span class="tag">[HRAiN]</span><span class="body">${esc(state.proof.selected_memory_count)} selected · proof-bound · head ${esc(short(state.proof.hrain_head))} · source ${esc(short(state.proof.memory_source_commit))} · context ${esc(short(state.proof.hrain_context_hash))}</span></div>`);
    } else {
      rows.push(`<div class="line"><span class="tag">[HRAiN]</span><span class="body">memory provenance ${esc(hrainStatus)}. Silence is not negative evidence.</span></div>`);
    }
    if (state.trumpStatus === 'CANDIDATE_RUNTIME_LIVE') {
      rows.push(`<div class="line candidate"><span class="tag">[TRUMP]</span><span class="body">candidate runtime tissue live · wake/use/self-improve enabled · proof authority 0 · P_VS_NP OPEN · manifest ${esc(short(state.trumpManifestDigest))}</span></div>`);
    } else {
      rows.push(`<div class="line"><span class="tag">[TRUMP]</span><span class="body">candidate tissue ${esc(state.trumpStatus)}${state.trumpError ? ` · ${esc(state.trumpError)}` : ''}. Silence is not proof of absence.</span></div>`);
    }

    if (state.issue) {
      rows.push(`<div class="line user"><span class="tag">[HUMAN]</span><span class="body">${esc(state.issue.title)} · issue #${state.issue.number}</span></div>`);
    }
    if (state.response) {
      const text = extractJanusText(state.response.body || '');
      rows.push(`<div class="line janus"><span class="tag">[JANUS]</span><span class="body">${esc(text)}<div class="proof-inline">resident=${esc(short(state.proof.resident_uuid, 18))} · model=${esc(short(state.proof.model_digest))} · turn=${esc(short(state.proof.turn_id, 18))}</div></span></div>`);
    } else {
      rows.push(`<div class="line"><span class="tag">[I/O]</span><span class="body">No sealed JANUS response discovered yet. New messages are read-only human stimuli, never commands.</span></div>`);
    }
    box.innerHTML = rows.join('');
    box.scrollTop = box.scrollHeight;
  }

  function renderProvenance() {
    const data = {
      resident_id: state.identity?.resident_id || 'JANUS',
      resident_uuid: state.identity?.resident_uuid || null,
      mode: state.head?.mode || null,
      active_cycle_id: state.head?.active_cycle_id ?? null,
      model_digest: state.proof.model_digest || null,
      file_fabric_digest: state.proof.file_fabric_digest || null,
      turn_id: state.proof.turn_id || null,
      response_hash: state.proof.response_hash || null,
      response_id: state.proof.response_id || null,
      terminal_issue: state.issue?.number || null,
      memory_path: ['JANUS_META_REGISTRY_DB', 'HRAIN_ACTIVE_OR_FULL_CURRENT_MEMORY', 'TERMINAL_MEMORY_VIEW'],
      hrain_memory_surface: HRAIN_MEMORY,
      hrain_memory_proof: {
        status: hrainProofStatus(),
        hrain_head: state.proof.hrain_head || null,
        memory_source_commit: state.proof.memory_source_commit || null,
        hrain_context_hash: state.proof.hrain_context_hash || null,
        hrain_context_receipt_hash: state.proof.hrain_context_receipt_hash || null,
        selected_memory_count: state.proof.selected_memory_count == null ? null : Number(state.proof.selected_memory_count),
        selected_memory_objects: state.proof.selected_memory_objects || null,
        memory_match_status: state.proof.memory_match_status || null,
        memory_context_is_evidence: state.proof.memory_context_is_evidence || null,
        memory_grants_authority: state.proof.memory_grants_authority || null,
        empty_memory_is_hrain_failure: state.proof.empty_memory_is_hrain_failure || null,
        empty_memory_is_negative_evidence: state.proof.empty_memory_is_negative_evidence || null,
      },
      candidate_runtime_tissues: {
        trump: {
          public_manifest_url: TRUMP_MANIFEST_URL,
          status: state.trumpStatus,
          manifest_digest: state.trumpManifestDigest,
          wake_allowed: state.trump?.activation?.wake_allowed ?? null,
          use_allowed: state.trump?.activation?.use_allowed ?? null,
          self_improvement_allowed: state.trump?.activation?.self_improvement_allowed ?? null,
          proof_authority: state.trump?.activation?.proof_authority ?? null,
          scientific_claim_promotion_authority: state.trump?.activation?.scientific_claim_promotion_authority ?? null,
          P_VS_NP: state.trump?.scientific_boundary?.P_VS_NP ?? null,
          public_manifest_is_proof_authority: false,
          error: state.trumpError,
        },
      },
      authority: {
        conversation: 'READ_ONLY_CONVERSATION',
        command_authority_granted: false,
        external_effect_authorized: false,
        physical_runtime_effect_authorized: false,
      },
    };
    setText('provenance-json', JSON.stringify(data, null, 2));
  }

  function switchView(name) {
    qa('.nav-btn').forEach((btn) => btn.classList.toggle('active', btn.dataset.view === name));
    qa('.view').forEach((view) => view.classList.toggle('active', view.id === `view-${name}`));
    setText('current-view', name.toUpperCase());
    if (name === 'memory') {
      const frame = $('hrain-frame');
      if (frame && !frame.getAttribute('src')) frame.setAttribute('src', HRAIN_MEMORY);
    }
  }

  function openConversation() {
    const input = $('composer-input');
    const message = String(input?.value || '').trim();
    if (!message) {
      input?.focus();
      return;
    }
    const titleSeed = message.replace(/\s+/g, ' ').slice(0, 64);
    const title = `[JANUS CHAT] ${titleSeed}`;
    const body = [
      '### Message',
      '',
      message,
      '',
      '### Conversation mode',
      '',
      'READ_ONLY_CONVERSATION',
      '',
      '### Authority boundary',
      '',
      'This message is a human stimulus, not a command. No write, claim, scientific-evidence, external-effect, or physical-runtime authority is granted by this text.',
    ].join('\n');
    const url = `${TERMINAL_REPO}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  function openLatestIssue() {
    if (state.issue) window.open(state.issue.html_url, '_blank', 'noopener,noreferrer');
    else window.open(`${TERMINAL_REPO}/issues`, '_blank', 'noopener,noreferrer');
  }

  async function refresh() {
    const btn = $('refresh-btn');
    btn?.classList.add('loading-shimmer');
    try {
      await Promise.all([loadPersistentState(), loadLatestConversation(), loadTrumpCandidate()]);
      state.refreshedAt = new Date();
      renderStatus();
      renderTranscript();
      renderProvenance();
      document.dispatchEvent(new CustomEvent('janus:terminal-state', { detail: { issue: state.issue, response: state.response, proof: state.proof, refreshedAt: state.refreshedAt?.toISOString() || null } }));
    } catch (err) {
      console.warn('JANUS_TERMINAL_REFRESH_UNRESOLVED', err);
      const corePill = $('core-pill');
      if (corePill) corePill.innerHTML = '<span class="dot"></span>UNRESOLVED';
      const box = $('transcript');
      if (box) box.insertAdjacentHTML('beforeend', '<div class="line"><span class="tag">[NET]</span><span class="body">Public GitHub read unresolved. Silence is not negative evidence.</span></div>');
    } finally {
      btn?.classList.remove('loading-shimmer');
    }
  }

  function ensureHrainInspectorSurface() {
    if ($('side-hrain')) return;
    const route = document.querySelector('.inspector .route');
    if (!route) return;
    const row = document.createElement('div');
    row.className = 'metric';
    row.innerHTML = '<label>HRAiN memory proof</label><div id="side-hrain">UNRESOLVED</div>';
    route.parentElement.insertBefore(row, route);
  }

  function wire() {
    ensureHrainInspectorSurface();
    qa('.nav-btn').forEach((btn) => btn.addEventListener('click', () => switchView(btn.dataset.view)));
    $('transmit-btn')?.addEventListener('click', openConversation);
    $('open-latest-btn')?.addEventListener('click', openLatestIssue);
    $('refresh-btn')?.addEventListener('click', refresh);
    $('composer-input')?.addEventListener('keydown', (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') openConversation();
    });
    $('memory-open')?.addEventListener('click', () => window.open(HRAIN_MEMORY, '_blank', 'noopener,noreferrer'));
  }

  document.addEventListener('DOMContentLoaded', async () => {
    wire();
    switchView('console');
    await refresh();
    window.setInterval(refresh, 60000);
  });
})();
