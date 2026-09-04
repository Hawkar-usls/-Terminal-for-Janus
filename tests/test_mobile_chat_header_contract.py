from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mobile_chat_header_fits_viewport_without_horizontal_carousel():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    assert "#view-console.neural-link-active>.instance-banner .kicker{display:none}" in css
    assert "#view-console.neural-link-active>.instance-banner h2{font-size:14px" in css
    assert "grid-template-columns:minmax(0,1.55fr) repeat(4,minmax(0,1fr))" in css
    assert "width:100%;max-width:100%;overflow:hidden" in css
    assert "overflow-x:auto" not in css
    assert "flex:0 0 138px" not in css


def test_mobile_neural_header_can_wrap_status_without_expanding_viewport():
    css = (ROOT / "assets/neural-link-v2.css").read_text(encoding="utf-8")
    assert ".neural-link-state{font-size:6.5px" in css
    assert "max-width:42%;white-space:normal;text-align:center" in css
    assert ".neural-link-public{padding:6px 10px;font-size:6.5px" in css
