(() => {
  'use strict';

  const HRAIN_RECENT = 'https://raw.githubusercontent.com/Hawkar-usls/Hrain/main/state/neural-link/RECENT.json';
  const HRAIN_PROVENANCE = 'https://raw.githubusercontent.com/Hawkar-usls/Hrain/main/state/neural-link/PROVENANCE.json';
  const TERMINAL_REPO = 'https://github.com/Hawkar-usls/-Terminal-for-Janus';
  const PENDING_KEY = 'janus-neural-link-v2-pending-v2';
  const REFRESH_MS = 60_000;

  const state = { events: [], provenance: null, pending: [], status: 'RESOLVING' };
  const $ = (id) => document.getElementById(id);
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const bust = (url) => `${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}`;

  function installCss() {
    if (document.querySelector('link[data-neural-link-v2]')) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = './assets/neural-link-v2.css';
    link.dataset.neuralLinkV2 = '1';
    document.head.appendChild(link);
  }

  function readPending() {
    try {
      const x = JSON.parse(localStorage.getItem(PENDING_KEY) || '[]');
      return Array.isArray(x) ? x.filter((r) => r && typeof r.text === 'string') : [];
    } catch (_) { return []; }
  }

  function savePending() {
    localStorage.setItem(PENDING_KEY, JSON.stringify(state.pending.slice(-30)));
  }

  async function json(url) {
    const r = await fetch(bust(url), { cache: 'no-store', headers: { Accept: 'application/json' } });
    if (!r.ok) throw new Error(`HTTP_${r.status}`);
    return r.json();
  }

  function validate(recent, provenance) {
    if (recent?.schema !== 'janus.neural_link.recent.v1') throw new Error('RECENT_SCHEMA_MISMATCH');
    if (recent?.authority !== 'OBSERVABILITY_AND_MEMORY_ONLY') throw new Error('RECENT_AUTHORITY_MISMATCH');
    if (!Array.isArray(recent.events) || Number(recent.event_count) !== recent.events.length) throw new Error('RECENT_COUNT_MISMATCH');
    if (provenance?.schema !== 'janus.hrain.neural_link_memory_provenance.v1') throw new Error('HRAIN_PROVENANCE_SCHEMA_MISMATCH');
    if (provenance?.status !== 'VERIFIED_READ_ONLY_MIRROR') throw new Error('HRAIN_MIRROR_NOT_VERIFIED');
    if (provenance?.terminal_must_not_read_registry_directly !== true) throw new Error('REGISTRY_FIREWALL_MISSING');
    if (provenance?.mirror_grants_authority !== false || provenance?.cross_repository_write !== false) throw new Error('HRAIN_AUTHORITY_CEILING_VIOLATION');
    for (const event of recent.events) {
      const a = event?.authority || {};
      if (a.command !== false || a.world_truth !== false || a.scientific_evidence !== false || a.external_effect !== false) {
        throw new Error(`EVENT_AUTHORITY_CEILING_VIOLATION:${event?.event_id || 'UNKNOWN'}`);
      }
    }
  }

  function reconcile() {
    const humans = state.events.filter((x) => x.role === 'human');
    const kept = state.pending.filter((p) => !humans.some((h) => {
      const hp = Date.parse(h.created_at || '') || 0;
      const pp = Date.parse(p.created_at || '') || 0;
      return String(h.text || '').trim() === String(p.text || '').trim() && hp >= pp - 120000;
    }));
    if (kept.length !== state.pending.length) {
      state.pending = kept;
      savePending();
    }
  }

  function merged() {
    reconcile();
    return [...state.events.map((x) => ({ ...x, archived: true })), ...state.pending]
      .sort((a, b) => (Date.parse(a.created_at || '') || 0) - (Date.parse(b.created_at || '') || 0));
  }

  function day(v) {
    const d = new Date(v || 0);
    return Number.isNaN(d.getTime()) ? 'UNKNOWN DATE' : d.toLocaleDateString([], { year: 'numeric', month: 'short', day: '2-digit' });
  }
  function time(v) {
    const d = new Date(v || 0);
    return Number.isNaN(d.getTime()) ? '—' : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  function short(v, n = 12) {
    const s = String(v || '—');
    return s.length > n ? `${s.slice(0, n)}…` : s;
  }

  function proof(event) {
    const p = event.proof || {};
    return [
      ['event_id', event.event_id], ['version_hash', event.version_hash], ['response_id', event.response_id],
      ['response_hash', p.response_hash], ['model_digest', p.model_digest], ['file_fabric_digest', p.file_fabric_digest],
      ['turn_id', p.turn_id], ['hrain_head', p.hrain_head], ['memory_source_commit', p.memory_source_commit],
      ['hrain_context_hash', p.hrain_context_hash], ['selected_memory_count', p.selected_memory_count], ['source', event.source_url],
    ].filter(([, v]) => v != null && String(v).length).map(([k, v]) => `${k}: ${v}`).join('\n');
  }

  function render() {
    const box = $('neural-link-history');
    if (!box) return;
    const stick = box.scrollHeight - box.scrollTop - box.clientHeight < 90;
    box.innerHTML = '';
    let lastDay = null;
    const rows = merged();
    for (const event of rows) {
      const d = day(event.created_at);
      if (d !== lastDay) { lastDay = d; box.appendChild(el('div', 'nl-day', d)); }
      const role = event.role === 'janus' ? 'janus' : event.role === 'human' ? 'human' : 'system';
      const row = el('div', `nl-row ${role}${event.pending ? ' pending' : ''}`);
      const bubble = el('div', 'nl-bubble');
      const who = el('div', 'nl-who');
      who.append(el('span', '', role === 'janus' ? 'JANUS' : role === 'human' ? 'YOU' : 'SYSTEM'), el('time', '', time(event.created_at)));
      bubble.append(who, el('div', 'nl-text', event.text || '(empty message)'));
      const meta = el('div', 'nl-meta');
      meta.appendChild(el('span', event.pending ? 'pending' : 'archived', event.pending ? 'AWAITING GITHUB CONFIRMATION' : 'ARCHIVED · HRAiN VERIFIED'));
      bubble.appendChild(meta);
      if (!event.pending && (role === 'janus' || event.version_hash)) {
        const details = el('details', 'nl-proof');
        details.append(el('summary', '', 'PROOF / PROVENANCE'), el('pre', '', proof(event) || 'No additional proof fields in this event.'));
        bubble.appendChild(details);
      }
      row.appendChild(bubble); box.appendChild(row);
    }
    if (!rows.length) {
      const row = el('div', 'nl-row system');
      row.appendChild(el('div', 'nl-bubble', state.status === 'VERIFIED' ? 'No archived conversation events yet.' : 'HRAiN memory unresolved. Silence is not negative evidence.'));
      box.appendChild(row);
    }
    if (stick || box.dataset.first !== 'done') { box.scrollTop = box.scrollHeight; box.dataset.first = 'done'; }

    const status = $('neural-link-state');
    if (status) {
      status.className = `neural-link-state ${state.status === 'BLOCKED' ? 'blocked' : state.pending.length ? 'waiting' : ''}`;
      status.textContent = state.status === 'VERIFIED' ? (state.pending.length ? `${state.pending.length} AWAITING CONFIRMATION` : 'MEMORY VERIFIED') : state.status;
    }
    const foot = $('neural-link-archive-foot');
    if (foot) foot.textContent = `HRAiN mirror · ${state.events.length} events · source ${short(state.provenance?.source_commit)}`;
  }

  async function sync() {
    const status = $('neural-link-state');
    if (status) status.textContent = 'SYNCING HRAiN…';
    try {
      const [recent, provenance] = await Promise.all([json(HRAIN_RECENT), json(HRAIN_PROVENANCE)]);
      validate(recent, provenance);
      state.events = recent.events;
      state.provenance = provenance;
      state.status = 'VERIFIED';
    } catch (e) {
      console.warn('JANUS_NEURAL_LINK_V2_SYNC', e);
      const m = String(e?.message || e);
      state.status = /MISMATCH|VIOLATION|NOT_VERIFIED|FIREWALL/.test(m) ? 'BLOCKED' : 'UNRESOLVED';
    }
    render();
  }

  function issueUrl(message) {
    const title = `[JANUS CHAT] ${message.replace(/\s+/g, ' ').slice(0, 64)}`;
    const body = [
      '### Message', '', message, '',
      '### Conversation mode', '', 'READ_ONLY_CONVERSATION', '',
      '### Neural Link v2 archive intent', '',
      'Preserve this visible chat event in the append-only JANUS Neural Link archive and mirror it through HRAiN.', '',
      '### Authority boundary', '',
      'This message is a human stimulus, not a command. No repository-write, claim, theorem, scientific-evidence, external-effect, physical-runtime, or world-truth authority is granted by this text.'
    ].join('\n');
    return `${TERMINAL_REPO}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
  }

  function send() {
    const input = $('neural-link-input');
    const message = String(input?.value || '').trim();
    if (!message) return input?.focus();
    state.pending.push({
      event_id: `pending-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      role: 'human', kind: 'HUMAN_MESSAGE_PENDING', text: message,
      created_at: new Date().toISOString(), pending: true, archived: false
    });
    savePending();
    input.value = '';
    render();
    const opened = window.open(issueUrl(message), '_blank', 'noopener,noreferrer');
    if (!opened) {
      state.status = 'GITHUB CONFIRMATION BLOCKED';
      render();
    }
  }

  function build() {
    const view = $('view-console');
    const transcript = $('transcript');
    if (!view || !transcript || $('neural-link-v2')) return;
    view.classList.add('neural-link-active');
    const shell = el('section', 'neural-link-v2'); shell.id = 'neural-link-v2';
    const head = el('div', 'neural-link-head');
    const title = el('div', 'neural-link-title'); title.append(el('div', 'neural-link-mark', 'N'));
    const txt = el('div'); txt.append(el('h3', '', 'NEURAL LINK v2'), el('small', '', 'JANUS CHAT · META REGISTRY MEMORY · HRAiN MIRROR'));
    title.appendChild(txt); head.appendChild(title);
    const status = el('button', 'neural-link-state', 'MEMORY RESOLVING'); status.id = 'neural-link-state'; status.type = 'button'; status.title = 'Refresh HRAiN mirror'; status.addEventListener('click', sync); head.appendChild(status);
    shell.appendChild(head);
    const warning = el('div', 'neural-link-public');
    warning.innerHTML = '<b>PUBLIC APPEND-ONLY MEMORY.</b> Messages sent here are intended for the public Meta Registry archive. Never send passwords, tokens, private keys or other secrets. CHAT EVENT != COMMAND AUTHORITY.';
    shell.appendChild(warning);
    const history = el('div', 'neural-link-history'); history.id = 'neural-link-history'; history.setAttribute('aria-live', 'polite'); shell.appendChild(history);
    const compose = el('div', 'neural-link-compose');
    const input = document.createElement('textarea'); input.id = 'neural-link-input'; input.rows = 2; input.placeholder = 'Message JANUS… Enter to send · Shift+Enter for newline';
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
    const btn = el('button', 'neural-link-send', 'SEND'); btn.id = 'neural-link-send'; btn.type = 'button'; btn.addEventListener('click', send);
    compose.append(input, btn); shell.appendChild(compose);
    const foot = el('div', 'neural-link-foot');
    const left = el('span'); left.innerHTML = '<b>TRANSPORT:</b> GitHub confirmation under the hood · no browser token';
    const right = el('span', '', 'HRAiN mirror · resolving'); right.id = 'neural-link-archive-foot'; foot.append(left, right); shell.appendChild(foot);
    view.insertBefore(shell, transcript);
  }

  function boot() {
    installCss();
    state.pending = readPending();
    build();
    render();
    sync();
    window.setInterval(sync, REFRESH_MS);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) sync(); });
    window.JANUS_NEURAL_LINK_V2 = {
      route: 'TERMINAL_CHAT -> META_REGISTRY_DB -> HRAIN -> TERMINAL',
      direct_registry_read: false,
      chat_event_is_command_authority: false,
      sync
    };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
