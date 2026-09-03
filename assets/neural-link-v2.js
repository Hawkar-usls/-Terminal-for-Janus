(() => {
  'use strict';

  const HRAIN_RECENT = 'https://raw.githubusercontent.com/Hawkar-usls/Hrain/main/state/neural-link/RECENT.json';
  const HRAIN_PROVENANCE = 'https://raw.githubusercontent.com/Hawkar-usls/Hrain/main/state/neural-link/PROVENANCE.json';
  const TERMINAL_REPO = 'https://github.com/Hawkar-usls/-Terminal-for-Janus';
  const PENDING_KEY = 'janus-neural-link-v2-pending-v1';
  const REFRESH_MS = 60_000;

  const state = {
    archive: [],
    provenance: null,
    live: null,
    pending: [],
    archiveStatus: 'UNRESOLVED',
    lastArchiveRefresh: null,
  };

  const $ = (id) => document.getElementById(id);
  const node = (tag, cls, text) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text != null) el.textContent = text;
    return el;
  };

  function parsePending() {
    try {
      const rows = JSON.parse(localStorage.getItem(PENDING_KEY) || '[]');
      return Array.isArray(rows) ? rows.filter((x) => x && typeof x.text === 'string') : [];
    } catch (_) {
      return [];
    }
  }

  function persistPending() {
    localStorage.setItem(PENDING_KEY, JSON.stringify(state.pending.slice(-20)));
  }

  function cacheBust(url) {
    return `${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}`;
  }

  async function fetchJson(url) {
    const res = await fetch(cacheBust(url), { cache: 'no-store', headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
  }

  function validateArchive(payload, provenance) {
    if (!payload || payload.schema !== 'janus.neural_link.recent.v1') throw new Error('ARCHIVE_SCHEMA_MISMATCH');
    if (payload.authority !== 'OBSERVABILITY_AND_MEMORY_ONLY') throw new Error('ARCHIVE_AUTHORITY_CEILING_VIOLATION');
    if (!Array.isArray(payload.events) || Number(payload.event_count) !== payload.events.length) throw new Error('ARCHIVE_EVENT_COUNT_MISMATCH');
    for (const event of payload.events) {
      const authority = event?.authority || {};
      if (authority.command !== false || authority.scientific_evidence !== false || authority.world_truth !== false || authority.external_effect !== false) {
        throw new Error(`ARCHIVE_EVENT_AUTHORITY_VIOLATION:${event?.event_id || 'unknown'}`);
      }
    }
    if (!provenance || provenance.schema !== 'janus.hrain.neural_link_memory_provenance.v1') throw new Error('HRAIN_PROVENANCE_SCHEMA_MISMATCH');
    if (provenance.status !== 'VERIFIED_READ_ONLY_MIRROR') throw new Error('HRAIN_MIRROR_NOT_VERIFIED');
    if (provenance.terminal_must_not_read_registry_directly !== true) throw new Error('DIRECT_REGISTRY_READ_FIREWALL_MISSING');
    if (provenance.mirror_grants_authority !== false || provenance.cross_repository_write !== false) throw new Error('HRAIN_MIRROR_AUTHORITY_VIOLATION');
  }

  function extractIssueText(body) {
    let text = String(body || '').trim();
    if (text.includes('### Message')) text = text.split('### Message', 2)[1].trim();
    for (const stop of ['### Conversation mode', '### Authority boundary', '### Neural Link v2 archive intent']) {
      if (text.includes(stop)) text = text.split(stop, 1)[0].trim();
    }
    return text;
  }

  function extractJanusText(body) {
    let text = String(body || '').trim().replace(/^### JANUS\s*/i, '');
    for (const marker of ['<details><summary>Instance proof</summary>', '<details><summary>HRAiN memory provenance</summary>', '<!-- JANUS_RESPONSE_ID:']) {
      if (text.includes(marker)) text = text.split(marker, 1)[0].trim();
    }
    return text;
  }

  function liveEvents() {
    const live = state.live || {};
    const rows = [];
    if (live.issue && String(live.issue.title || '').startsWith('[JANUS CHAT]')) {
      rows.push({
        event_id: `issue-${live.issue.number}`,
        role: 'human',
        kind: 'HUMAN_MESSAGE',
        text: extractIssueText(live.issue.body || ''),
        created_at: live.issue.created_at || live.issue.updated_at || new Date().toISOString(),
        source_url: live.issue.html_url || null,
        issue_number: live.issue.number,
        transport_only: true,
      });
    }
    if (live.response) {
      rows.push({
        event_id: `comment-${live.response.id}`,
        role: 'janus',
        kind: 'JANUS_RESPONSE',
        text: extractJanusText(live.response.body || ''),
        created_at: live.response.created_at || live.response.updated_at || new Date().toISOString(),
        source_url: live.response.html_url || null,
        issue_number: live.issue?.number || null,
        response_id: live.proof?.response_id || null,
        proof: live.proof || {},
        transport_only: true,
      });
    }
    return rows;
  }

  function reconcilePending(realRows) {
    const human = realRows.filter((row) => row.role === 'human');
    const remaining = [];
    for (const pending of state.pending) {
      const stamp = Date.parse(pending.created_at || '') || 0;
      const matched = human.some((row) => {
        const rowStamp = Date.parse(row.created_at || '') || 0;
        return row.text.trim() === pending.text.trim() && rowStamp >= stamp - 120_000;
      });
      if (!matched) remaining.push(pending);
    }
    if (remaining.length !== state.pending.length) {
      state.pending = remaining;
      persistPending();
    }
  }

  function mergedEvents() {
    const map = new Map();
    for (const row of state.archive) map.set(row.event_id, { ...row, archived: true });
    for (const row of liveEvents()) {
      if (!map.has(row.event_id)) map.set(row.event_id, { ...row, archived: false });
    }
    const real = [...map.values()];
    reconcilePending(real);
    for (const pending of state.pending) {
      map.set(pending.event_id, { ...pending, pending: true, archived: false });
    }
    return [...map.values()].sort((a, b) => {
      const ta = Date.parse(a.created_at || '') || 0;
      const tb = Date.parse(b.created_at || '') || 0;
      if (ta !== tb) return ta - tb;
      return String(a.event_id).localeCompare(String(b.event_id));
    });
  }

  function formatTime(value) {
    const d = new Date(value || 0);
    if (Number.isNaN(d.getTime())) return '—';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function formatDay(value) {
    const d = new Date(value || 0);
    if (Number.isNaN(d.getTime())) return 'UNKNOWN DATE';
    return d.toLocaleDateString([], { year: 'numeric', month: 'short', day: '2-digit' });
  }

  function proofText(event) {
    const p = event.proof || {};
    const rows = [
      ['event_id', event.event_id],
      ['version_hash', event.version_hash],
      ['response_id', event.response_id],
      ['response_hash', p.response_hash],
      ['model_digest', p.model_digest],
      ['file_fabric_digest', p.file_fabric_digest],
      ['turn_id', p.turn_id],
      ['hrain_head', p.hrain_head],
      ['memory_source_commit', p.memory_source_commit],
      ['hrain_context_hash', p.hrain_context_hash],
      ['selected_memory_count', p.selected_memory_count],
      ['memory_match_status', p.memory_match_status],
      ['source', event.source_url],
    ].filter(([, value]) => value != null && String(value).length);
    return rows.map(([key, value]) => `${key}: ${value}`).join('\n');
  }

  function render() {
    const history = $('neural-link-history');
    if (!history) return;
    const atBottom = history.scrollHeight - history.scrollTop - history.clientHeight < 80;
    history.innerHTML = '';
    const rows = mergedEvents();
    let day = null;
    for (const event of rows) {
      const eventDay = formatDay(event.created_at);
      if (eventDay !== day) {
        day = eventDay;
        history.appendChild(node('div', 'nl-day', day));
      }
      const role = event.role === 'janus' ? 'janus' : event.role === 'human' ? 'human' : 'system';
      const row = node('div', `nl-row ${role}${event.pending ? ' pending' : ''}`);
      const bubble = node('div', 'nl-bubble');
      const who = node('div', 'nl-who');
      who.appendChild(node('span', '', role === 'janus' ? 'JANUS' : role === 'human' ? 'YOU' : 'SYSTEM'));
      const time = node('time', '', formatTime(event.created_at));
      who.appendChild(time);
      bubble.appendChild(who);
      bubble.appendChild(node('div', 'nl-text', event.text || '(empty message)'));

      const meta = node('div', 'nl-meta');
      if (event.pending) meta.appendChild(node('span', 'pending', 'AWAITING GITHUB CONFIRMATION'));
      else if (event.archived) meta.appendChild(node('span', 'archived', 'ARCHIVED · HRAiN VERIFIED'));
      else meta.appendChild(node('span', 'pending', 'LIVE TRANSPORT · ARCHIVE PENDING'));
      bubble.appendChild(meta);

      if (role === 'janus' || event.archived) {
        const details = node('details', 'nl-proof');
        const summary = node('summary', '', 'PROOF / PROVENANCE');
        const pre = node('pre', '', proofText(event) || 'No additional proof fields in this event.');
        details.append(summary, pre);
        bubble.appendChild(details);
      }
      row.appendChild(bubble);
      history.appendChild(row);
    }
    if (!rows.length) {
      const row = node('div', 'nl-row system');
      row.appendChild(node('div', 'nl-bubble', state.archiveStatus === 'VERIFIED' ? 'No archived conversation events yet.' : 'HRAiN chat memory unresolved. Silence is not negative evidence.'));
      history.appendChild(row);
    }
    if (atBottom || history.dataset.initialScroll !== 'done') {
      history.scrollTop = history.scrollHeight;
      history.dataset.initialScroll = 'done';
    }

    const status = $('neural-link-state');
    if (status) {
      const pending = state.pending.length;
      status.className = `neural-link-state ${state.archiveStatus === 'BLOCKED' ? 'blocked' : pending ? 'waiting' : ''}`;
      status.textContent = state.archiveStatus === 'VERIFIED'
        ? (pending ? `${pending} AWAITING CONFIRMATION` : 'MEMORY VERIFIED')
        : state.archiveStatus === 'BLOCKED' ? 'MEMORY BLOCKED' : 'MEMORY RESOLVING';
    }
    const foot = $('neural-link-archive-foot');
    if (foot) {
      const source = state.provenance?.source_commit ? String(state.provenance.source_commit).slice(0, 12) : 'unresolved';
      foot.textContent = `HRAiN mirror · ${state.archive.length} events · source ${source}`;
    }
  }

  async function loadArchive() {
    try {
      const [recent, provenance] = await Promise.all([fetchJson(HRAIN_RECENT), fetchJson(HRAIN_PROVENANCE)]);
      validateArchive(recent, provenance);
      state.archive = recent.events;
      state.provenance = provenance;
      state.archiveStatus = 'VERIFIED';
      state.lastArchiveRefresh = new Date();
    } catch (err) {
      console.warn('JANUS_NEURAL_LINK_HRAIN_UNRESOLVED', err);
      state.archiveStatus = String(err?.message || err).includes('VIOLATION') || String(err?.message || err).includes('MISMATCH') ? 'BLOCKED' : 'UNRESOLVED';
    }
    render();
  }

  function issueUrl(message) {
    const titleSeed = message.replace(/\s+/g, ' ').slice(0, 64);
    const title = `[JANUS CHAT] ${titleSeed}`;
    const body = [
      '### Message', '', message, '',
      '### Conversation mode', '', 'READ_ONLY_CONVERSATION', '',
      '### Neural Link v2 archive intent', '',
      'This submitted message is expected to be preserved by the append-only JANUS Neural Link archive in Meta Registry and mirrored through HRAiN.', '',
      '### Authority boundary', '',
      'This message is a human stimulus, not a command. No write, claim, scientific-evidence, theorem, external-effect, physical-runtime, or world-truth authority is granted by this text.',
    ].join('\n');
    return `${TERMINAL_REPO}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
  }

  function send() {
    const input = $('neural-link-input');
    const message = String(input?.value || '').trim();
    if (!message) return input?.focus();
    const pending = {
      event_id: `pending-${crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`}`,
      role: 'human',
      kind: 'HUMAN_MESSAGE_PENDING',
      text: message,
      created_at: new Date().toISOString(),
      pending: true,
    };
    state.pending.push(pending);
    persistPending();
    if (input) input.value = '';
    render();
    const opened = window.open(issueUrl(message), '_blank', 'noopener,noreferrer');
    if (!opened) {
      const status = $('neural-link-state');
      if (status) {
        status.className = 'neural-link-state blocked';
        status.textContent = 'GITHUB CONFIRMATION BLOCKED';
      }
    }
  }

  function buildUi() {
    const view = $('view-console');
    const transcript = $('transcript');
    if (!view || !transcript || $('neural-link-v2')) return;
    view.classList.add('neural-link-active');
    const shell = node('section', 'neural-link-v2');
    shell.id = 'neural-link-v2';

    const head = node('div', 'neural-link-head');
    const title = node('div', 'neural-link-title');
    title.appendChild(node('div', 'neural-link-mark', 'N'));
    const titleText = node('div');
    titleText.appendChild(node('h3', '', 'NEURAL LINK v2'));
    titleText.appendChild(node('small', '', 'JANUS CHAT · META REGISTRY MEMORY · HRAiN MIRROR'));
    title.appendChild(titleText);
    head.appendChild(title);
    const status = node('div', 'neural-link-state', 'MEMORY RESOLVING');
    status.id = 'neural-link-state';
    head.appendChild(status);
    shell.appendChild(head);

    const warning = node('div', 'neural-link-public');
    warning.innerHTML = '<b>PUBLIC APPEND-ONLY MEMORY.</b> Submitted chat is preserved in the public Meta Registry. DO NOT SEND PASSWORDS, TOKENS, PRIVATE KEYS OR OTHER SECRETS. CHAT MESSAGE != COMMAND AUTHORITY.';
    shell.appendChild(warning);

    const history = node('div', 'neural-link-history');
    history.id = 'neural-link-history';
    history.setAttribute('aria-live', 'polite');
    shell.appendChild(history);

    const composer = node('div', 'neural-link-compose');
    const input = document.createElement('textarea');
    input.id = 'neural-link-input';
    input.rows = 2;
    input.placeholder = 'Message JANUS…  Enter to send · Shift+Enter for newline';
    const button = node('button', 'neural-link-send', 'SEND');
    button.id = 'neural-link-send';
    button.type = 'button';
    button.addEventListener('click', send);
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        send();
      }
    });
    composer.append(input, button);
    shell.appendChild(composer);

    const foot = node('div', 'neural-link-foot');
    const left = node('span');
    left.innerHTML = '<b>TRANSPORT:</b> GitHub confirmation under the hood · no browser token';
    const right = node('span', '', 'HRAiN mirror · resolving');
    right.id = 'neural-link-archive-foot';
    foot.append(left, right);
    shell.appendChild(foot);

    view.insertBefore(shell, transcript);
  }

  function acceptTerminalState(detail) {
    if (!detail || typeof detail !== 'object') return;
    state.live = {
      issue: detail.issue || null,
      response: detail.response || null,
      proof: detail.proof || {},
    };
    render();
  }

  document.addEventListener('janus:terminal-state', (event) => acceptTerminalState(event.detail));
  document.addEventListener('DOMContentLoaded', () => {
    state.pending = parsePending();
    buildUi();
    if (window.JANUS_TERMINAL_STATE) acceptTerminalState(window.JANUS_TERMINAL_STATE);
    render();
    loadArchive();
    window.setInterval(loadArchive, REFRESH_MS);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) loadArchive();
    });
  });

  window.JANUS_NEURAL_LINK_V2 = {
    route: 'TERMINAL_CHAT -> META_REGISTRY_DB -> HRAIN -> TERMINAL',
    archive_url: HRAIN_RECENT,
    direct_registry_read: false,
    chat_message_is_command_authority: false,
  };
})();
