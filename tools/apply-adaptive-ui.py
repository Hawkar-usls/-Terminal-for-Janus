#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch_once(path: str, old: str, new: str, label: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if new in text:
        return
    if old not in text:
        raise SystemExit(f'ADAPTIVE_PATCH_ANCHOR_MISSING:{label}')
    if text.count(old) != 1:
        raise SystemExit(f'ADAPTIVE_PATCH_ANCHOR_NONUNIQUE:{label}:{text.count(old)}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


patch_once(
    'index.html',
    '  <link rel="stylesheet" href="./assets/neural-link-v2.css">\n',
    '  <link rel="stylesheet" href="./assets/neural-link-v2.css">\n  <link rel="stylesheet" href="./assets/adaptive-ui.css">\n',
    'adaptive-css',
)
patch_once(
    'index.html',
    '<script src="./assets/neural-link-v2.js" defer></script>\n',
    '<script src="./assets/neural-link-v2.js" defer></script>\n<script src="./assets/adaptive-ui.js" defer></script>\n',
    'adaptive-js',
)

# Regression tests: adaptive layer is wired, mobile-aware and authority-free.
tests = ROOT / 'tests/test_terminal_v2_static.py'
s = tests.read_text(encoding='utf-8')
marker = 'def test_adaptive_ui_layer_is_wired_and_layout_only():'
if marker not in s:
    s += '''\n\n\ndef test_adaptive_ui_layer_is_wired_and_layout_only():\n    html = (ROOT / "index.html").read_text(encoding="utf-8")\n    css = (ROOT / "assets/adaptive-ui.css").read_text(encoding="utf-8")\n    js = (ROOT / "assets/adaptive-ui.js").read_text(encoding="utf-8")\n    assert 'viewport-fit=cover' in html\n    assert 'assets/adaptive-ui.css' in html\n    assert 'assets/adaptive-ui.js' in html\n    assert '100dvh' in css\n    assert 'safe-area-inset-bottom' in css\n    assert 'scroll-snap-type:x proximity' in css\n    assert '.inspector.adaptive-open' in css\n    assert 'visualViewport' in js\n    assert 'adaptive-inspector-toggle' in js\n    assert 'scrollIntoView' in js\n    assert 'layout_only: true' in js\n    assert 'command_authority: false' in js\n    assert 'memory_authority: false' in js\n    assert 'transport_authority: false' in js\n    assert 'fetch(' not in js\n    assert 'GITHUB_TOKEN' not in js\n\n\ndef test_mobile_navigation_is_scrollable_not_seven_way_squeezed():\n    css = (ROOT / "assets/adaptive-ui.css").read_text(encoding="utf-8")\n    assert '.sidebar::-webkit-scrollbar{display:none}' in css\n    assert 'overflow-x:auto' in css\n    assert 'flex:0 0 72px' in css\n    assert 'padding-bottom:calc(var(--terminal-dock-h) + var(--terminal-safe-bottom))' in css\n\n\ndef test_neural_link_mobile_composer_remains_keyboard_safe():\n    css = (ROOT / "assets/adaptive-ui.css").read_text(encoding="utf-8")\n    js = (ROOT / "assets/adaptive-ui.js").read_text(encoding="utf-8")\n    assert '.neural-link-history{height:auto!important;min-height:0!important;flex:1' in css\n    assert '.neural-link-compose textarea{font-size:16px' in css\n    assert "input.setAttribute('enterkeyhint', 'send')" in js\n'''
    tests.write_text(s, encoding='utf-8')

# Immutable local verifier: keep responsive code outside authority surfaces.
verifier = ROOT / 'tools/test-janus-observatory.js'
s = verifier.read_text(encoding='utf-8')
if "const adaptive = read('assets/adaptive-ui.js');" not in s:
    anchor = "const neural = read('assets/neural-link-v2.js');\n"
    if anchor not in s:
        raise SystemExit('ADAPTIVE_PATCH_ANCHOR_MISSING:verifier-read')
    s = s.replace(
        anchor,
        anchor + "const adaptive = read('assets/adaptive-ui.js');\nconst adaptiveCss = read('assets/adaptive-ui.css');\n",
        1,
    )
if 'ADAPTIVE_UI_RUNTIME_NOT_WIRED' not in s:
    block = '''\n// Adaptive UI truth: layout-only layer, no network/authority semantics.\nmust(html, 'assets/adaptive-ui.js', 'ADAPTIVE_UI_RUNTIME_NOT_WIRED');\nmust(html, 'assets/adaptive-ui.css', 'ADAPTIVE_UI_STYLE_NOT_WIRED');\nmust(adaptiveCss, '100dvh', 'ADAPTIVE_UI_DYNAMIC_VIEWPORT_MISSING');\nmust(adaptiveCss, 'safe-area-inset-bottom', 'ADAPTIVE_UI_SAFE_AREA_MISSING');\nmust(adaptiveCss, 'scroll-snap-type:x proximity', 'ADAPTIVE_UI_MOBILE_DOCK_MISSING');\nmust(adaptive, 'layout_only: true', 'ADAPTIVE_UI_LAYOUT_BOUNDARY_MISSING');\nmust(adaptive, 'command_authority: false', 'ADAPTIVE_UI_COMMAND_BOUNDARY_MISSING');\nmust(adaptive, 'memory_authority: false', 'ADAPTIVE_UI_MEMORY_BOUNDARY_MISSING');\nmust(adaptive, 'transport_authority: false', 'ADAPTIVE_UI_TRANSPORT_BOUNDARY_MISSING');\nif (adaptive.includes('fetch(')) throw new Error('ADAPTIVE_UI_NETWORK_ACCESS_FORBIDDEN');\nif (adaptive.includes('GITHUB_TOKEN')) throw new Error('ADAPTIVE_UI_BROWSER_SECRET_FORBIDDEN');\n\n'''
    anchor = '// Neural Link v2 truth:'
    if anchor not in s:
        raise SystemExit('ADAPTIVE_PATCH_ANCHOR_MISSING:verifier-position')
    s = s.replace(anchor, block + anchor, 1)
if 'adaptive_ui: true' not in s:
    anchor = '  neural_link_v2: true,\n'
    if anchor not in s:
        raise SystemExit('ADAPTIVE_PATCH_ANCHOR_MISSING:verifier-report')
    s = s.replace(
        anchor,
        anchor + '  adaptive_ui: true,\n  adaptive_ui_network_access: false,\n  adaptive_ui_authority: false,\n',
        1,
    )
verifier.write_text(s, encoding='utf-8')

print('JANUS_ADAPTIVE_UI_PATCH=APPLIED')
