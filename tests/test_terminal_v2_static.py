from html.parser import HTMLParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.iframes = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "iframe":
            self.iframes.append(values)


def test_terminal_v2_replaces_legacy_port_scanner():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    combined = html + "\n" + js
    for forbidden in ("ngrok-free", "LOCAL_IPS", "PORTS_TO_SCAN", "findJanus()", "/api/janus/action"):
        assert forbidden not in combined


def test_terminal_memory_is_hrain_mediated_not_direct_registry_fetch():
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "https://hawkar-usls.github.io/Hrain/janus.html" in js
    assert "https://hawkar-usls.github.io/janus-meta-registry/" not in js
    assert "raw.githubusercontent.com/Hawkar-usls/janus-meta-registry" not in js


def test_git_native_conversation_surface_is_issue_backed_and_read_only():
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    assert "[JANUS CHAT]" in js
    assert "READ_ONLY_CONVERSATION" in js
    assert "human stimulus, not a command" in js
    assert "/issues/new?title=" in js


def test_persistent_instance_proof_is_rendered():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "assets/terminal-v2.js").read_text(encoding="utf-8")
    for field in ("resident_uuid", "model_digest", "file_fabric_digest", "turn_id", "response_hash"):
        assert field in js or field.replace("_", "-") in html
    assert "janus/activator-state/state/activator" in js


def test_html_has_no_duplicate_ids():
    parser = IdCollector()
    parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    assert duplicates == []


def test_terminal_v2_contract_is_fail_closed():
    contract = json.loads((ROOT / ".janus/TERMINAL_V2_HRAIN_MEMORY_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["memory_dataflow"]["source_database"] == "Hawkar-usls/janus-meta-registry"
    assert contract["memory_dataflow"]["structural_memory_organ"] == "Hawkar-usls/Hrain"
    assert contract["memory_dataflow"]["terminal_consumes_registry_directly"] is False
    assert contract["conversation"]["browser_secret_required"] is False
    assert contract["conversation"]["local_network_scan_required"] is False
    assert contract["conversation"]["command_authority_granted_by_message"] is False
    assert "CANDIDATE_TRUMP != PROOF_AUTHORIZED_TRUMP" in contract["laws"]
