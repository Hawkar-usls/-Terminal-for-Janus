from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"PATCH_ANCHOR_{label}:{text.count(old)}")
    return text.replace(old, new, 1)


p = Path("assets/terminal-v2.js")
s = p.read_text(encoding="utf-8")

s = replace_once(
    s,
    """  function extractProof(body) {
    const proof = {};
    const allowed = new Set(['resident_uuid', 'model_digest', 'file_fabric_digest', 'turn_id', 'response_hash']);
    for (const line of String(body || '').split('\\n')) {
      const m = line.match(/^- ([a-z_]+): `([^`]+)`\\s*$/);
      if (m && allowed.has(m[1])) proof[m[1]] = m[2];
    }
    const rid = String(body || '').match(/JANUS_RESPONSE_ID:([^\\s>]+)/);
    if (rid) proof.response_id = rid[1];
    return proof;
  }
""",
    """  function extractProof(body) {
    const proof = {};
    const allowed = new Set([
      'resident_uuid', 'model_digest', 'file_fabric_digest', 'turn_id', 'response_hash',
      'hrain_head', 'memory_source_commit', 'hrain_context_hash', 'hrain_context_receipt_hash',
      'selected_memory_count', 'memory_path', 'memory_match_status',
      'memory_context_is_evidence', 'memory_grants_authority',
      'empty_memory_is_hrain_failure', 'empty_memory_is_negative_evidence',
    ]);
    const text = String(body || '');
    for (const line of text.split('\\n')) {
      const m = line.match(/^- ([a-z_ ]+): `([^`]+)`\\s*$/);
      if (!m) continue;
      const key = m[1].trim().replace(/\\s+/g, '_');
      if (allowed.has(key)) proof[key] = m[2];
    }
    const selected = text.match(/^Selected memory objects: `([^`]+)`\\s*$/m);
    if (selected) proof.selected_memory_objects = selected[1];
    const rid = text.match(/JANUS_RESPONSE_ID:([^\\s>]+)/);
    if (rid) proof.response_id = rid[1];
    return proof;
  }

  function hrainProofStatus() {
    const p = state.proof || {};
    if (!p.hrain_context_hash || !p.hrain_head || !p.memory_source_commit) return 'UNRESOLVED';
    const count = Number(p.selected_memory_count);
    if (!Number.isInteger(count) || count < 0) return 'BLOCKED_INVALID_COUNT';
    if (p.memory_context_is_evidence !== 'false' || p.memory_grants_authority !== 'false') return 'BLOCKED_AUTHORITY_CEILING';
    if (count === 0) {
      const validEmpty = p.memory_match_status === 'NO_RELEVANT_MEMORY_SELECTED'
        && p.empty_memory_is_hrain_failure === 'false'
        && p.empty_memory_is_negative_evidence === 'false'
        && p.selected_memory_objects === 'none';
      return validEmpty ? 'VALID_EMPTY_RETRIEVAL' : 'BLOCKED_INVALID_EMPTY_RETRIEVAL';
    }
    return `BOUND_${count}_MEMORY_OBJECTS`;
  }
""",
    "extract_proof",
)

s = replace_once(
    s,
    """    setText('side-response', responseHash);
    setText('issue-number', state.issue ? `#${state.issue.number}` : '—');
""",
    """    setText('side-response', responseHash);
    const hrainStatus = hrainProofStatus();
    const hrainSummary = hrainStatus === 'VALID_EMPTY_RETRIEVAL'
      ? `0 selected · VALID EMPTY · ${short(state.proof.hrain_head)} / ${short(state.proof.memory_source_commit)}`
      : hrainStatus.startsWith('BOUND_')
        ? `${state.proof.selected_memory_count} selected · ${short(state.proof.hrain_context_hash)}`
        : hrainStatus;
    setText('side-hrain', hrainSummary);
    setText('issue-number', state.issue ? `#${state.issue.number}` : '—');
""",
    "render_status",
)

s = replace_once(
    s,
    """    rows.push(`<div class=\"line\"><span class=\"tag\">[MEMORY]</span><span class=\"body\">Meta Registry DB → HRAiN ACTIVE/FULL_CURRENT structural memory → Terminal MEMORY.</span></div>`);
""",
    """    const hrainStatus = hrainProofStatus();
    if (hrainStatus === 'VALID_EMPTY_RETRIEVAL') {
      rows.push(`<div class=\"line ok\"><span class=\"tag\">[HRAiN]</span><span class=\"body\">0 selected · VALID EMPTY RETRIEVAL · match ${esc(state.proof.memory_match_status)} · head ${esc(short(state.proof.hrain_head))} · source ${esc(short(state.proof.memory_source_commit))} · context ${esc(short(state.proof.hrain_context_hash))} · empty ≠ failure · empty ≠ negative evidence</span></div>`);
    } else if (hrainStatus.startsWith('BOUND_')) {
      rows.push(`<div class=\"line ok\"><span class=\"tag\">[HRAiN]</span><span class=\"body\">${esc(state.proof.selected_memory_count)} selected · proof-bound · head ${esc(short(state.proof.hrain_head))} · source ${esc(short(state.proof.memory_source_commit))} · context ${esc(short(state.proof.hrain_context_hash))}</span></div>`);
    } else {
      rows.push(`<div class=\"line\"><span class=\"tag\">[HRAiN]</span><span class=\"body\">memory provenance ${esc(hrainStatus)}. Silence is not negative evidence.</span></div>`);
    }
""",
    "transcript_hrain",
)

s = replace_once(
    s,
    """      hrain_memory_surface: HRAIN_MEMORY,
      candidate_runtime_tissues: {
""",
    """      hrain_memory_surface: HRAIN_MEMORY,
      hrain_memory_proof: {
        status: hrainProofStatus(),
        hrain_head: state.proof.hrain_head || null,
        memory_source_commit: state.proof.memory_source_commit || null,
        hrain_context_hash: state.proof.hrain_context_hash || null,
        hrain_context_receipt_hash: state.proof.hrain_context_receipt_hash || null,
        selected_memory_count: state.proof.selected_memory_count == null ? null : Number(state.proof.selected_memory_count),
        selected_memory_objects: state.proof.selected_memory_objects || null,
        memory_match_status: state.proof.memory_match_status || null,
        memory_context_is_evidence: state.proof.memory_context_is_evidence || null,
        memory_grants_authority: state.proof.memory_grants_authority || null,
        empty_memory_is_hrain_failure: state.proof.empty_memory_is_hrain_failure || null,
        empty_memory_is_negative_evidence: state.proof.empty_memory_is_negative_evidence || null,
      },
      candidate_runtime_tissues: {
""",
    "provenance",
)

s = replace_once(
    s,
    """  function wire() {
""",
    """  function ensureHrainInspectorSurface() {
    if ($('side-hrain')) return;
    const route = document.querySelector('.inspector .route');
    if (!route) return;
    const row = document.createElement('div');
    row.className = 'metric';
    row.innerHTML = '<label>HRAiN memory proof</label><div id=\"side-hrain\">UNRESOLVED</div>';
    route.parentElement.insertBefore(row, route);
  }

  function wire() {
    ensureHrainInspectorSurface();
""",
    "inspector",
)

p.write_text(s, encoding="utf-8")

test = Path("tests/test_terminal_v2_static.py")
t = test.read_text(encoding="utf-8")
if "def test_terminal_displays_proof_carrying_hrain_provenance():" not in t:
    t += '''\n\n\ndef test_terminal_displays_proof_carrying_hrain_provenance():\n    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")\n    for token in (\n        "hrain_head", "memory_source_commit", "hrain_context_hash",\n        "hrain_context_receipt_hash", "selected_memory_count", "memory_match_status",\n        "memory_context_is_evidence", "memory_grants_authority",\n        "empty_memory_is_hrain_failure", "empty_memory_is_negative_evidence",\n        "VALID_EMPTY_RETRIEVAL", "BLOCKED_INVALID_EMPTY_RETRIEVAL",\n        "empty ≠ failure", "empty ≠ negative evidence", "side-hrain",\n    ):\n        assert token in js\n    assert "NO_RELEVANT_MEMORY_SELECTED" in js\n    assert "Selected memory objects" in js\n'''
    test.write_text(t, encoding="utf-8")

print("HRAIN_PROVENANCE_UI_PATCH=APPLIED")
