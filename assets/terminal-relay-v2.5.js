(() => {
  'use strict';

  const QUEUE_KEY = 'janus-terminal-relay-v2.5-queue';
  const CONFIG_URL = './assets/terminal-relay-v2.5.json';
  let config = { mode: 'UNBOUND', endpoint: null };
  let sending = false;

  function loadQueue() {
    try {
      const value = JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
      return Array.isArray(value) ? value : [];
    } catch (_) {
      return [];
    }
  }

  function saveQueue(rows) {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(rows));
  }

  function statusEl() {
    return document.getElementById('relay-status');
  }

  function setStatus(text, kind = '') {
    const el = statusEl();
    if (!el) return;
    el.textContent = text;
    el.className = kind;
  }

  async function digest(text) {
    const bytes = new TextEncoder().encode(text);
    const hash = await crypto.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(hash)).map(x => x.toString(16).padStart(2, '0')).join('');
  }

  function appendLocalEcho(text, state) {
    const transcript = document.getElementById('transcript');
    if (!transcript) return;
    const line = document.createElement('div');
    line.className = 'line user';
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = '[YOU]';
    const body = document.createElement('span');
    body.className = 'body';
    body.textContent = text;
    const tail = document.createElement('span');
    tail.className = 'mono';
    tail.style.marginLeft = '10px';
    tail.style.opacity = '.55';
    tail.textContent = state;
    line.append(tag, body, tail);
    transcript.appendChild(line);
    transcript.scrollTop = transcript.scrollHeight;
  }

  async function readConfig() {
    try {
      const response = await fetch(`${CONFIG_URL}?t=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) return;
      const value = await response.json();
      if (value && typeof value === 'object') config = value;
    } catch (_) {}
  }

  async function adapterTransmit(row) {
    // Preferred future boundary: an authenticated relay adapter may be injected
    // by a trusted same-origin shell. The static Page never receives repo tokens.
    if (window.JANUS_TERMINAL_RELAY && typeof window.JANUS_TERMINAL_RELAY.transmit === 'function') {
      return window.JANUS_TERMINAL_RELAY.transmit(row);
    }

    // A configured endpoint must establish authentication server-side or with
    // an approved browser identity session. No bearer token is accepted here.
    if (config.mode === 'IDENTITY_BOUND_RELAY' && config.endpoint) {
      const response = await fetch(config.endpoint, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(row),
      });
      if (!response.ok) throw new Error(`RELAY_HTTP_${response.status}`);
      return response.json();
    }
    throw new Error('SECURE_RELAY_NOT_BOUND');
  }

  async function flushQueue() {
    if (sending) return;
    const rows = loadQueue();
    if (!rows.length) {
      if (config.mode === 'IDENTITY_BOUND_RELAY') setStatus('RELAY READY · DIRECT TRANSMIT · NO PAGE REDIRECT', 'ready');
      return;
    }
    sending = true;
    try {
      const pending = [];
      for (const row of rows) {
        try {
          const receipt = await adapterTransmit(row);
          row.relay_receipt = receipt || null;
        } catch (error) {
          pending.push(row);
          if (String(error && error.message) === 'SECURE_RELAY_NOT_BOUND') {
            setStatus(`QUEUED ${pending.length} · SECURE RELAY BOUNDARY NOT YET CONNECTED · NO REDIRECT`, 'queued');
          } else {
            setStatus(`QUEUED ${pending.length} · RELAY ERROR ${String(error && error.message || error)}`, 'error');
          }
        }
      }
      saveQueue(pending);
      if (!pending.length) setStatus('TRANSMITTED · JANUS RELAY ACCEPTED MESSAGE · NO PAGE REDIRECT', 'ready');
    } finally {
      sending = false;
    }
  }

  async function transmit() {
    const input = document.getElementById('composer-input');
    const text = (input && input.value || '').trim();
    if (!text) {
      setStatus('TYPE A MESSAGE BEFORE TRANSMIT', 'error');
      return;
    }
    const createdAt = new Date().toISOString();
    const body = JSON.stringify({ text, created_at: createdAt, source: 'JANUS_TERMINAL_PAGES_V2_5' });
    const messageHash = await digest(body);
    const row = {
      schema: 'janus.terminal.browser_relay_request.v2.5',
      local_message_id: `tm-web-${messageHash}`,
      message_hash: messageHash,
      text,
      created_at: createdAt,
      authority_mode: 'READ_ONLY_CONVERSATION',
      command_authority: false,
      effect_authorized: false,
    };
    const queue = loadQueue();
    if (!queue.some(x => x.message_hash === row.message_hash)) queue.push(row);
    saveQueue(queue);
    appendLocalEcho(text, '· QUEUED');
    input.value = '';
    setStatus(`QUEUED ${queue.length} · RELAY ATTEMPT`, 'queued');
    await flushQueue();
  }

  function intercept(event) {
    const button = event.target && event.target.closest && event.target.closest('#transmit-btn');
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    transmit().catch(error => setStatus(`TRANSMIT ERROR · ${String(error && error.message || error)}`, 'error'));
  }

  document.addEventListener('click', intercept, true);
  document.addEventListener('keydown', event => {
    const input = document.getElementById('composer-input');
    if (event.target !== input || event.key !== 'Enter' || !(event.ctrlKey || event.metaKey)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    transmit().catch(error => setStatus(`TRANSMIT ERROR · ${String(error && error.message || error)}`, 'error'));
  }, true);

  document.addEventListener('DOMContentLoaded', async () => {
    await readConfig();
    const queue = loadQueue();
    if (queue.length) setStatus(`QUEUED ${queue.length} · WAITING FOR SECURE RELAY`, 'queued');
    else if (config.mode === 'IDENTITY_BOUND_RELAY') setStatus('RELAY READY · DIRECT TRANSMIT · NO PAGE REDIRECT', 'ready');
    else setStatus('DIRECT TRANSMIT UI READY · SECURE RELAY BOUNDARY PENDING', 'queued');
    flushQueue();
    setInterval(flushQueue, 10000);
  });
})();
