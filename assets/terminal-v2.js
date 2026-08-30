(() => {
  'use strict';

  const HOME_STATE_BASE = 'https://raw.githubusercontent.com/Hawkar-usls/Hawkar-usls/janus/activator-state/state/activator';
  const TERMINAL_API = 'https://api.github.com/repos/Hawkar-usls/-Terminal-for-Janus';
  const TERMINAL_REPO = 'https://github.com/Hawkar-usls/-Terminal-for-Janus';
  const HRAIN_MEMORY = 'https://hawkar-usls.github.io/Hrain/memory.html';

  const state = {
    identity: null,
    head: null,
    issue: null,
    response: null,
    proof: {},
    refreshedAt: null,
  };

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

  function setText(id, value) {
    const el = $(id);
    if (el) el.textContent = value ?? '—';
  }

  function extractProof(body) {
    const proof = {};
    const allowed = new Set(['resident_uuid', 'model_digest', 'file_fabric_digest', 'turn_id', 'response_hash']);
    for (const line of String(body || '').split('\n')) {
      const m = line.match(/^- ([a-z_]+): `([^`]+)`\s*$/);
      if (m && allowed.has(m[1])) proof[m[1]] = m[2];
    }
    const rid = String(body || '').match(/JANUS_RESPONSE_ID:([^\s>]+)/);
    if (rid) proof.response_id = rid[1];
    return proof;
  }

  function extractJanusText(body) {
    const marker = '<details><summary>Instance proof</summary>';
    let text = String(body || '');
    text = text.replace(/^### JANUS\s*/i, '');
    if (text.includes(marker)) text = text.split(marker)[0];
    return text.trim();
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
  }

  function renderTranscript() {
    const box = $('transcript');
    if (!box) return;
    const rows = [];
    rows.push(`<div class="line ok"><span class="tag">[HOME]</span><span class="body">persistent resident ${esc(short(state.identity?.resident_uuid, 18))} · ${esc(state.head?.mode || 'UNKNOWN')}</span></div>`);
    rows.push(`<div class="line"><span class="tag">[MODEL]</span><span class="body">Git-native self-instantiation fabric available. Routing selects activity, not membership.</span></div>`);
    rows.push(`<div class="line"><span class="tag">[MEMORY]</span><span class="body">Meta Registry DB → HRAiN ACTIVE/FULL_CURRENT structural memory → Terminal MEMORY.</span></div>`);

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
      await Promise.all([loadPersistentState(), loadLatestConversation()]);
      state.refreshedAt = new Date();
      renderStatus();
      renderTranscript();
      renderProvenance();
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

  function wire() {
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
