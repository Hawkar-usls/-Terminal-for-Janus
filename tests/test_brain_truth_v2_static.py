from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_brain_truth_runtime_is_wired_and_explicit_about_eval_context():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets/brain-truth-v2.js").read_text(encoding="utf-8")
    assert 'assets/brain-truth-v2.js' in html
    for token in (
        'adaptive loss · current source',
        'frozen anchor · active',
        'frozen anchor · candidate',
        'adaptive evaluation source',
        'evaluation_contract_sha256',
        'source_digest',
        'anchor_sha256',
        'BRAIN P${m.promotion_count',
        'ADAPT ${fmt(adaptive, 3)}',
        'ANCHOR ${fmt(anchor, 3)}',
    ):
        assert token in js


def test_history_window_is_not_mistaken_for_lifetime_history():
    js = (ROOT / "assets/brain-truth-v2.js").read_text(encoding="utf-8")
    assert 'history_window_not_exceed_attempt_count' in js
    assert 'history_window_truncated' in js
    assert 'attempts >= history.length' in js
    assert 'attemptCount - history.length + 1' in js
    assert 'shown of ${Number.isInteger(attemptCount) ? attemptCount : history.length} lifetime attempts' in js
    assert 'attempt_count_matches_history' not in js


def test_adaptive_chart_breaks_cross_source_lines_and_anchor_is_cross_epoch():
    js = (ROOT / "assets/brain-truth-v2.js").read_text(encoding="utf-8")
    for token in (
        'sourceKey(row, i)',
        'key !== previousKey',
        'if (segment.length > 1) segments.push(segment)',
        'LINES BREAK WHEN SOURCE DIGEST CHANGES',
        'FROZEN ANCHOR IS THE CROSS-EPOCH COMPARATOR',
    ):
        assert token in js


def test_brain_truth_runtime_fails_visible_and_clears_stale_telemetry_state():
    js = (ROOT / "assets/brain-truth-v2.js").read_text(encoding="utf-8")
    assert "pill.textContent = 'BRAIN UNRESOLVED'" in js
    assert "pill.classList.add('warn')" in js
    assert "status.classList.remove('live')" in js
