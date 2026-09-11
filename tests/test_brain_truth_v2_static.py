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
    assert '${history.length} shown / ${Number.isInteger(attemptCount) ? attemptCount : history.length} lifetime' in js
    assert 'attempt_count_matches_history' not in js


def test_discrete_truth_layer_uses_same_attempt_relative_margin_not_cross_source_absolute_line():
    js = (ROOT / "assets/brain-truth-v2.js").read_text(encoding="utf-8")
    for token in (
        'DISCRETE DECISION MARGIN · CANDIDATE VS INCUMBENT',
        'function adaptiveMarginPct(row)',
        '100 * (incumbent - candidate) / denom',
        'EACH BAR IS A SAME-ATTEMPT COMPARISON',
        'NO LINE CONNECTS DIFFERENT SOURCES',
        'FROZEN ANCHOR REMAINS THE CROSS-EPOCH COMPARATOR',
        'decision-stem',
        'decision-zero',
        '+% = candidate better',
        '−% = candidate worse',
    ):
        assert token in js
    assert 'active-curve' not in js
    assert '<polyline class="active-curve"' not in js


def test_brain_visual_v3_is_wired_and_readable_without_reintroducing_absolute_loss_claim():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets/brain-visual-v3.js").read_text(encoding="utf-8")
    assert 'assets/brain-visual-v3.js?v=' in html
    for token in (
        'DECISION ADVANTAGE · CANDIDATE VS INCUMBENT',
        'ADAPTIVE_TOLERANCE_PCT = 0.2',
        '100 * (incumbent - candidate)',
        'v3-trend',
        'v3-stem',
        'v3-status',
        'BETTER THAN INCUMBENT ↑',
        'WORSE THAN INCUMBENT ↓',
        'SAME-ATTEMPT RELATIVE ADVANTAGE',
        'FROZEN ANCHOR',
        'ResizeObserver',
        'MutationObserver',
        'JANUS decision advantage chart',
    ):
        assert token in js
    assert 'candidate_eval_loss - incumbent_eval_loss' not in js


def test_brain_visual_v3_keeps_exact_hover_provenance_and_real_attempt_numbers():
    js = (ROOT / "assets/brain-visual-v3.js").read_text(encoding="utf-8")
    for token in (
        'candidate ${candidate.toFixed(6)}',
        'incumbent ${incumbent.toFixed(6)}',
        'row.status',
        'source ${short(sourceKey(row,i),18)}',
        'startAttempt + i',
        'sourceChanges',
        'LATEST #${startAttempt+latestIndex}',
    ):
        assert token in js


def test_brain_truth_runtime_fails_visible_and_clears_stale_telemetry_state():
    js = (ROOT / "assets/brain-truth-v2.js").read_text(encoding="utf-8")
    assert "pill.textContent = 'BRAIN UNRESOLVED'" in js
    assert "pill.classList.add('warn')" in js
    assert "status.classList.remove('live')" in js
