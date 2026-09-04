(() => {
  'use strict';

  const ROOT = document.documentElement;
  const MOBILE_BREAKPOINT = 720;
  const SHEET_BREAKPOINT = 920;
  const MOBILE_NAV_LABELS = Object.freeze({
    console: 'CHAT',
    brain: 'BRAIN',
    logs: 'LOGS',
    modules: 'MODULES',
    memory: 'MEMORY',
    organism: 'ORGANISM',
    provenance: 'PROOF',
  });
  let sheetOpen = false;
  let toggle = null;
  let backdrop = null;
  let inspector = null;
  let activeObserver = null;

  const $ = (id) => document.getElementById(id);

  function updateViewportHeight() {
    const h = Math.round(window.visualViewport?.height || window.innerHeight || document.documentElement.clientHeight || 0);
    if (h > 0) ROOT.style.setProperty('--terminal-viewport-height', `${h}px`);
  }

  function setDeviceClasses() {
    const coarse = window.matchMedia('(pointer: coarse)').matches;
    const hoverless = window.matchMedia('(hover: none)').matches;
    ROOT.classList.toggle('adaptive-coarse', coarse);
    ROOT.classList.toggle('adaptive-hoverless', hoverless);
    ROOT.classList.toggle('adaptive-phone', window.innerWidth <= MOBILE_BREAKPOINT);
    ROOT.classList.toggle('adaptive-sheet-layout', window.innerWidth <= SHEET_BREAKPOINT);
  }

  function adaptNavigationLabels() {
    const mobile = window.innerWidth <= MOBILE_BREAKPOINT;
    document.querySelectorAll('.sidebar .nav-btn').forEach((button) => {
      const label = button.querySelector('span:last-child');
      if (!label) return;
      const original = button.dataset.fullLabel || label.textContent.trim();
      button.dataset.fullLabel = original;
      button.setAttribute('aria-label', original);
      label.textContent = mobile ? (MOBILE_NAV_LABELS[button.dataset.view] || original) : original;
      label.title = original;
    });
  }

  function closeSheet({ restoreFocus = false } = {}) {
    if (!inspector || !toggle || !backdrop) return;
    sheetOpen = false;
    inspector.classList.remove('adaptive-open');
    backdrop.classList.remove('adaptive-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.textContent = 'INFO';
    document.body.classList.remove('adaptive-sheet-open');
    if (restoreFocus) toggle.focus({ preventScroll: true });
  }

  function openSheet() {
    if (!inspector || !toggle || !backdrop || window.innerWidth > SHEET_BREAKPOINT) return;
    sheetOpen = true;
    inspector.classList.add('adaptive-open');
    backdrop.classList.add('adaptive-open');
    toggle.setAttribute('aria-expanded', 'true');
    toggle.textContent = 'CLOSE';
    document.body.classList.add('adaptive-sheet-open');
    requestAnimationFrame(() => {
      inspector.querySelector('button,a,[tabindex]:not([tabindex="-1"])')?.focus({ preventScroll: true });
    });
  }

  function toggleSheet() {
    if (sheetOpen) closeSheet({ restoreFocus: true });
    else openSheet();
  }

  function installInspectorSheet() {
    inspector = document.querySelector('.inspector');
    const topProof = document.querySelector('.top-proof');
    if (!inspector || !topProof) return;

    inspector.id ||= 'janus-inspector';
    toggle = $('adaptive-inspector-toggle');
    if (!toggle) {
      toggle = document.createElement('button');
      toggle.id = 'adaptive-inspector-toggle';
      toggle.type = 'button';
      toggle.className = 'pill adaptive-inspector-toggle';
      toggle.textContent = 'INFO';
      toggle.setAttribute('aria-controls', inspector.id);
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open JANUS inspector');
      topProof.appendChild(toggle);
    }

    backdrop = $('adaptive-inspector-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.id = 'adaptive-inspector-backdrop';
      backdrop.className = 'adaptive-inspector-backdrop';
      backdrop.setAttribute('aria-hidden', 'true');
      document.body.appendChild(backdrop);
    }

    toggle.addEventListener('click', toggleSheet);
    backdrop.addEventListener('click', () => closeSheet({ restoreFocus: true }));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && sheetOpen) closeSheet({ restoreFocus: true });
    });
  }

  function centerActiveNav() {
    if (window.innerWidth > MOBILE_BREAKPOINT) return;
    const active = document.querySelector('.sidebar .nav-btn.active');
    if (!active) return;
    active.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  }

  function watchNavigation() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    sidebar.addEventListener('click', (event) => {
      if (event.target.closest('.nav-btn')) {
        closeSheet();
        window.setTimeout(centerActiveNav, 30);
      }
    });

    activeObserver?.disconnect();
    activeObserver = new MutationObserver((records) => {
      if (records.some((record) => record.attributeName === 'class')) centerActiveNav();
    });
    sidebar.querySelectorAll('.nav-btn').forEach((button) => {
      activeObserver.observe(button, { attributes: true, attributeFilter: ['class'] });
    });
  }

  function improveScrollableRegions() {
    const selectors = [
      '.sidebar', '.chat-brain-strip', '.module-flow', '.neural-link-history',
      '.event-log', '.cards-view', '.console', '.inspector', '.transcript',
    ];
    document.querySelectorAll(selectors.join(',')).forEach((el) => {
      el.style.webkitOverflowScrolling = 'touch';
    });
  }

  function installKeyboardHints() {
    const input = $('neural-link-input');
    if (!input) return;
    input.setAttribute('enterkeyhint', 'send');
    input.setAttribute('autocapitalize', 'sentences');
  }

  function reactToResize() {
    updateViewportHeight();
    setDeviceClasses();
    adaptNavigationLabels();
    if (window.innerWidth > SHEET_BREAKPOINT && sheetOpen) closeSheet();
    if (window.innerWidth <= MOBILE_BREAKPOINT) centerActiveNav();
  }

  function boot() {
    updateViewportHeight();
    setDeviceClasses();
    adaptNavigationLabels();
    installInspectorSheet();
    watchNavigation();
    improveScrollableRegions();
    installKeyboardHints();
    centerActiveNav();

    window.addEventListener('resize', reactToResize, { passive: true });
    window.addEventListener('orientationchange', () => window.setTimeout(reactToResize, 80), { passive: true });
    window.visualViewport?.addEventListener('resize', updateViewportHeight, { passive: true });
    window.visualViewport?.addEventListener('scroll', updateViewportHeight, { passive: true });
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) reactToResize();
    });
    document.addEventListener('janus:terminal-state', installKeyboardHints);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();

  window.JANUS_ADAPTIVE_UI = Object.freeze({
    layout_only: true,
    command_authority: false,
    memory_authority: false,
    transport_authority: false,
    breakpoints: { phone: MOBILE_BREAKPOINT, sheet: SHEET_BREAKPOINT },
  });
})();
