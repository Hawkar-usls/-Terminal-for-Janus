from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Permanent regression gate: iPhone safe-area overlap must never be reintroduced.


def test_mobile_neural_link_composer_stays_inside_active_chat_viewport():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    required = (
        "#view-console.neural-link-active.active{height:100%;min-height:0;overflow:hidden;display:flex;flex-direction:column",
        "#view-console.neural-link-active>.neural-link-v2{flex:1 1 0;min-height:0",
        ".neural-link-history{height:auto;min-height:0;min-width:0;max-width:100%;flex:1 1 auto",
        ".neural-link-compose textarea{box-sizing:border-box;width:100%;max-width:100%;min-width:0",
        ".workspace{height:100%;min-height:0;overflow:hidden;padding-bottom:58px}",
    )
    for token in required:
        assert token in css
    assert "#view-console.neural-link-active{height:100%;min-height:0;overflow:hidden;display:flex;flex-direction:column" not in css


def test_mobile_terminal_root_cannot_be_widened_by_a_view():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    assert "html,body{width:100%;max-width:100%;overflow:hidden}" in css
    assert ".topbar,.shell,.workspace,.view{width:100%;max-width:100%;min-width:0}" in css


def test_mobile_chat_header_is_compact_and_has_no_horizontal_metric_carousel():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    assert "#view-console.neural-link-active>.instance-banner .kicker{display:none}" in css
    assert "#view-console.neural-link-active>.instance-banner h2{font-size:14px" in css
    assert "grid-template-columns:minmax(0,1.55fr) repeat(5,minmax(0,1fr))" in css
    assert "#view-console.neural-link-active>.chat-brain-strip>div{min-width:0" in css
    assert "overflow-x:auto" not in css
    assert "flex:0 0 138px" not in css


def test_mobile_neural_header_status_wraps_instead_of_expanding_viewport():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    assert ".neural-link-state{font-size:6.5px" in css
    assert "max-width:42%;white-space:normal;text-align:center" in css
    assert ".neural-link-public{padding:6px 10px;font-size:6.5px" in css


def test_iphone_top_telemetry_respects_safe_area_and_does_not_require_zoom():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    required = (
        "grid-template-rows:48px minmax(0,1fr);padding-top:max(env(safe-area-inset-top), 6px)",
        ".topbar{position:relative;top:auto;min-height:48px;height:48px",
        ".shell{height:100%;min-height:0;overflow:hidden}",
        "@media(max-width:430px)",
        ".brand>div:last-child{display:none}",
        "#brain-pill{display:block;flex:1 1 auto;max-width:none;text-align:center}",
        "#core-pill{display:block;flex:0 0 auto;max-width:72px}",
    )
    for token in required:
        assert token in css
    assert ".topbar{position:sticky" not in css


def test_synthesis_programmatic_navigation_delegates_to_core_click_router():
    synth = (ROOT / "assets/janus-synthesis-observatory.js").read_text(encoding="utf-8")
    terminal = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "function activateTerminalView(name)" in synth
    assert "window.JANUS_TERMINAL_NAVIGATE=activateTerminalView" in synth
    assert "btn.click();" in synth
    assert "function switchView(name)" in terminal
    assert "btn.addEventListener('click', () => switchView(btn.dataset.view))" in terminal
    assert "view.classList.toggle('active',active)" not in synth
    assert "document.querySelectorAll('.workspace > .view')" not in synth


def test_dynamic_synthesis_tab_exists_before_core_domcontentloaded_wiring():
    synth = (ROOT / "assets/janus-synthesis-observatory.js").read_text(encoding="utf-8")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "installView();\ninstallViewRouter();\nif(document.readyState==='loading')" in synth
    assert "nav.addEventListener('click',loadSynth);" in synth
    terminal_tag = '<script src="./assets/terminal-v2.js" defer></script>'
    synthesis_tag = '<script src="./assets/janus-synthesis-observatory.js" defer></script>'
    assert html.count(terminal_tag) == 1
    assert html.count(synthesis_tag) == 1
    assert html.index(terminal_tag) < html.index(synthesis_tag)


def test_synthesis_does_not_own_terminal_view_state_or_memory_routing():
    synth = (ROOT / "assets/janus-synthesis-observatory.js").read_text(encoding="utf-8")
    terminal = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "event.stopImmediatePropagation();" not in synth
    assert "event.stopPropagation();" not in synth
    assert "classList.toggle('active'" not in synth
    assert "if(name==='memory')" not in synth
    assert "if (name === 'memory')" in terminal
    assert "hrain-frame" in terminal
    assert "https://hawkar-usls.github.io/Hrain/memory.html" in terminal
