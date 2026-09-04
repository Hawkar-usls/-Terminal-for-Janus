from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mobile_neural_link_composer_stays_inside_chat_viewport():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    required = (
        "#view-console.neural-link-active{height:100%;min-height:0;overflow:hidden;display:flex;flex-direction:column",
        "#view-console.neural-link-active>.neural-link-v2{flex:1 1 0;min-height:0",
        ".neural-link-history{height:auto;min-height:0;min-width:0;max-width:100%;flex:1 1 auto",
        ".neural-link-compose textarea{box-sizing:border-box;width:100%;max-width:100%;min-width:0",
        "@supports(height:100dvh){.workspace{height:calc(100dvh - 64px)}}",
    )
    for token in required:
        assert token in css


def test_mobile_terminal_root_cannot_be_widened_by_a_view():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    assert "html,body{width:100%;max-width:100%;overflow:hidden}" in css
    assert ".topbar,.shell,.workspace,.view{width:100%;max-width:100%;min-width:0}" in css


def test_all_present_and_future_nav_buttons_share_one_router():
    js = (ROOT / "assets/janus-synthesis-observatory.js").read_text(encoding="utf-8")
    assert "function activateTerminalView(name)" in js
    assert "function installViewRouter()" in js
    assert "window.JANUS_TERMINAL_NAVIGATE=activateTerminalView" in js
    assert ".nav-btn[data-view]" in js
    assert ".workspace > .view" in js
    assert "view.classList.toggle('active',active)" in js
    assert "aria-hidden" in js


def test_dynamic_synthesis_tab_uses_shared_router_not_private_click_router():
    js = (ROOT / "assets/janus-synthesis-observatory.js").read_text(encoding="utf-8")
    assert "nav.addEventListener('click'" not in js
    assert "installViewRouter();installView();" in js


def test_shared_router_prevents_legacy_static_handlers_from_double_executing():
    js = (ROOT / "assets/janus-synthesis-observatory.js").read_text(encoding="utf-8")
    assert "event.stopImmediatePropagation();" in js
    assert "if(name==='memory')" in js
    assert "hrain-frame" in js
    assert "https://hawkar-usls.github.io/Hrain/memory.html" in js
