"""codeguardwiz CLI: watch / severity / explain / scaffold / fix / scan.
Network is blocked for every test; audit/fix results are canned where needed."""
import json
import subprocess
import sys
import types
import urllib.request

import pytest

from wiz_central_toolkit.codeguardwiz import cli as cgcli
from wiz_central_toolkit.codeguardwiz.cli import main


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise OSError("network blocked in tests")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    monkeypatch.delenv("CODEGUARD_AUDIT_MODEL", raising=False)
    monkeypatch.delenv("CODEGUARD_FIX_MODEL", raising=False)


def _run(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["codeguardwiz", *argv])
    return main()


def _file(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def _issue(sev, title="T", lines="1-2"):
    return {"severity": sev, "title": title, "line_range": lines,
            "description": "because"}


def _result(*issues):
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for i in issues:
        counts[i["severity"]] += 1
    return {"status": "OK", "filepath": "f", "language": "python", "model": "m",
            "issues_count": counts, "audit": {"score": 70, "issues": list(issues)}}


FAILED = {"status": "FAILED", "reason": "daemon down"}


# ---------- watch ----------

@pytest.fixture
def baseline_bank(monkeypatch, tmp_path):
    """Point the wizard's baseline state at a scratch dir."""
    monkeypatch.setattr(cgcli, "STATE_DIR", tmp_path / ".codeguard-wizard")
    monkeypatch.setattr(cgcli, "BASELINES",
                        tmp_path / ".codeguard-wizard" / "baselines.json")
    return tmp_path


def test_watch_ok(monkeypatch, capsys, tmp_path, baseline_bank):
    # A baseline from a prior audit; watch re-audits and compares.
    p = _file(tmp_path, "a.py", "x = 1\n")
    cgcli._record_baseline(str(p), "model", 70,
                           ["[HIGH] T (line 1-2)"])
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH")))
    assert _run(monkeypatch, "watch", str(p)) == 0
    out = capsys.readouterr().out
    assert "baseline score 70 -> now 70" in out
    assert "unchanged: 1" in out


def test_watch_no_baseline(monkeypatch, capsys, tmp_path, baseline_bank):
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "watch", str(p)) == 1
    out = capsys.readouterr().out
    assert "no baseline recorded" in out
    assert "codeguard_wizard audit" in out


def test_watch_new_issue_appears(monkeypatch, capsys, tmp_path,
                                 baseline_bank):
    p = _file(tmp_path, "a.py", "x = 1\n")
    cgcli._record_baseline(str(p), "model", 100, [])
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH")))
    assert _run(monkeypatch, "watch", str(p)) == 0
    out = capsys.readouterr().out
    assert "new: 1" in out
    assert "NEW" in out


def test_watch_static_flow_end_to_end(monkeypatch, capsys, tmp_path,
                                      baseline_bank):
    # Real static engine: audit records the baseline, watch reports
    # unchanged, then a planted issue shows up as NEW.
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "audit", "--engine", "static", str(p)) == 0
    capsys.readouterr()
    assert _run(monkeypatch, "watch", str(p)) == 0
    out = capsys.readouterr().out
    assert "unchanged: 0" in out and "new: 0" in out
    p.write_text("x = 1\neval('boom')\n")
    assert _run(monkeypatch, "watch", str(p)) == 0
    out = capsys.readouterr().out
    assert "new: 1" in out and "CG003" in out


def test_watch_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "watch", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


def test_watch_audit_failed(monkeypatch, tmp_path, baseline_bank):
    p = _file(tmp_path, "a.py", "x = 1\n")
    cgcli._record_baseline(str(p), "model", 70, [])
    monkeypatch.setattr(cgcli, "audit", lambda p: FAILED)
    assert _run(monkeypatch, "watch", str(p)) == 1


# ---------- severity ----------

def _sev_issues():
    return _result(_issue("CRITICAL", "Crit"), _issue("HIGH", "Hi"),
                   _issue("MEDIUM", "Med"), _issue("LOW", "Lo"))


def test_severity_default_high_includes_critical(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _sev_issues())
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p)) == 1
    out = capsys.readouterr().out
    assert "HIGH+ severity: 2 findings" in out
    assert "Crit" in out and "Hi" in out
    assert "Med" not in out


def test_severity_medium_includes_high_and_critical(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _sev_issues())
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p), "--threshold", "MEDIUM") == 1
    out = capsys.readouterr().out
    assert "MEDIUM+ severity: 3 findings" in out
    assert "Lo" not in out.replace("Lo\n", "", 0) or "[LOW]" not in out


def test_severity_critical_only(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _sev_issues())
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p), "--threshold", "CRITICAL") == 1
    assert "CRITICAL+ severity: 1 findings" in capsys.readouterr().out


def test_severity_clean_returns_zero(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("LOW")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p)) == 0
    assert "0 findings" in capsys.readouterr().out


def test_severity_failed_audit_is_not_reported_clean(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: FAILED)
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p)) == 1
    assert "[FAIL]" in capsys.readouterr().out


def test_severity_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "severity", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


# ---------- explain ----------

def test_explain_line_inside_range(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH", "Bad", "10-12")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "11") == 0
    out = capsys.readouterr().out
    assert "Title: Bad" in out and "Message: because" in out


def test_explain_single_line_range(monkeypatch, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH", "Bad", "5")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "5") == 0


def test_explain_does_not_match_by_substring(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH", "Bad", "10-12")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "1") == 1
    assert "no issue found at line 1" in capsys.readouterr().out


def test_explain_no_issues(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result())
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "3") == 1


def test_explain_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "explain", str(tmp_path / "nope.py"), "3") == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


def test_explain_model_list_line_range(monkeypatch, capsys, tmp_path):
    # The model engine's contract emits line_range as a JSON pair
    # [lo, hi] (see codeguard_wizard.py's audit format). Explain must
    # find the issue — before the fix it never could (F1).
    monkeypatch.setattr(cgcli, "audit",
                        lambda p: _result(_issue("HIGH", "Bad", [10, 12])))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "11") == 0
    out = capsys.readouterr().out
    assert "Title: Bad" in out and "Message: because" in out


def test_explain_model_list_line_range_single_line_pair(monkeypatch, tmp_path):
    # The exact demo shape: the eval issue reported as [19, 19].
    monkeypatch.setattr(cgcli, "audit",
                        lambda p: _result(_issue("CRITICAL", "Eval", [19, 19])))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "19") == 0


def test_explain_model_list_line_range_outside(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit",
                        lambda p: _result(_issue("HIGH", "Bad", [10, 12])))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "13") == 1
    assert "no issue found at line 13" in capsys.readouterr().out


def test_line_in_range_shapes():
    from wiz_central_toolkit.codeguardwiz.cli import _line_in_range
    # list / tuple pairs (the model contract's shape)
    assert _line_in_range(19, [19, 19]) is True
    assert _line_in_range(10, [10, 12]) is True
    assert _line_in_range(12, (10, 12)) is True
    assert _line_in_range(9, [10, 12]) is False
    # text forms, unchanged
    assert _line_in_range(11, "10-12") is True
    assert _line_in_range(11, "10:12") is True
    assert _line_in_range(5, "5") is True
    assert _line_in_range(1, "10-12") is False
    # malformed values are a plain False, never an exception
    for bad in ([10], [10, 12, 14], ["a", "b"], [None, 5], None, "",
                "x-y", {}, ["10-12"]):
        assert _line_in_range(10, bad) is False


# ---------- scaffold ----------

def test_scaffold_lists_public_defs_and_writes_nothing(monkeypatch, capsys, tmp_path):
    src = "def public():\n    pass\n\ndef _private():\n    pass\n\nclass Thing:\n    pass\n"
    p = _file(tmp_path, "a.py", src)
    assert _run(monkeypatch, "scaffold", str(p)) == 0
    out = capsys.readouterr().out
    assert "def test_public_exists" in out
    assert "def test_Thing_importable" in out
    assert "test__private" not in out
    assert "functions: 1, classes: 1" in out
    assert sorted(x.name for x in tmp_path.iterdir()) == ["a.py"]


def test_scaffold_empty_file(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "a.py", "")
    assert _run(monkeypatch, "scaffold", str(p)) == 0
    assert "no public top-level defs" in capsys.readouterr().out


def test_scaffold_syntax_error(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "a.py", "def broken(:\n")
    assert _run(monkeypatch, "scaffold", str(p)) == 1
    assert "[FAIL] cannot parse" in capsys.readouterr().out


def test_scaffold_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "scaffold", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


# ---------- fix ----------

FIXED = {"status": "OK", "issues_fixed": 1, "fix_model": "m", "fixed_code": "NEW\n"}


def test_fix_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "fix", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


def test_fix_failure_is_reported(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: {"status": "FAILED", "reason": "nope"})
    p = _file(tmp_path, "a.js", "OLD\n")
    assert _run(monkeypatch, "fix", str(p)) == 1
    assert "[FAIL] nope" in capsys.readouterr().out


def test_fix_nothing_to_fix(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: {
        "status": "OK", "issues_fixed": 0, "message": "no issues to fix"})
    p = _file(tmp_path, "a.js", "OLD\n")
    assert _run(monkeypatch, "fix", str(p)) == 0
    assert "[OK] no issues to fix" in capsys.readouterr().out


def test_fix_preview_leaves_disk_untouched(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")
    assert _run(monkeypatch, "fix", str(p)) == 0
    out = capsys.readouterr().out
    assert "preview only" in out and "NEW" in out
    assert p.read_text() == "OLD\n"


@pytest.fixture
def writewiz_bank(tmp_path, monkeypatch):
    """Isolate writewiz's quarantine/bank to tmp — the wall's state
    must never touch the real ~/.write-wizard in tests."""
    from wiz_central_toolkit.writewiz import write_wizard as ww
    bank = tmp_path / ".write-wizard"
    monkeypatch.setattr(ww, "BANK", bank)
    monkeypatch.setattr(ww, "QUARANTINE", bank / "pending")
    monkeypatch.setattr(ww, "BACKUPS", bank / "backups")
    monkeypatch.setattr(ww, "LEDGER", bank / "ledger.jsonl")
    monkeypatch.setattr(ww, "PROTECTED", bank / "protected.json")
    return bank


def _double_yes(monkeypatch, target):
    answers = iter(["y", f"yes, write {target}"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))


def test_fix_write_non_python(monkeypatch, capsys, tmp_path, writewiz_bank):
    """--write lands through the wall now: staged via writewiz, the
    double ask, then commit — never a direct write."""
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")
    _double_yes(monkeypatch, p)
    assert _run(monkeypatch, "fix", str(p), "--write") == 0
    assert p.read_text() == "NEW\n"
    out = capsys.readouterr().out
    assert "[STAGED] model fix" in out
    assert "[OK] written" in out


def test_fix_out_path_keeps_original(monkeypatch, tmp_path, writewiz_bank):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")
    out = tmp_path / "b.js"
    _double_yes(monkeypatch, out)
    assert _run(monkeypatch, "fix", str(p), "--out", str(out)) == 0
    assert out.read_text() == "NEW\n"
    assert p.read_text() == "OLD\n"


def test_fix_write_denied_at_first_ask(monkeypatch, capsys, tmp_path,
                                       writewiz_bank):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert _run(monkeypatch, "fix", str(p), "--write") == 1
    assert p.read_text() == "OLD\n"
    out = capsys.readouterr().out
    assert "[CONSENT WALL] consent withheld" in out
    # the staged draft survives the refusal, in quarantine
    from wiz_central_toolkit.writewiz import write_wizard as ww
    draft, _meta = ww._draft_path(p)
    assert draft.exists()


def test_fix_write_denied_at_typed_ask(monkeypatch, capsys, tmp_path,
                                       writewiz_bank):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")
    answers = iter(["y", "yes"])  # the typed phrase must name the file
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    assert _run(monkeypatch, "fix", str(p), "--write") == 1
    assert p.read_text() == "OLD\n"
    assert "[CONSENT WALL] consent withheld" in capsys.readouterr().out


def test_fix_write_eof_is_a_no(monkeypatch, capsys, tmp_path, writewiz_bank):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")

    def boom(prompt=""):
        raise EOFError
    monkeypatch.setattr("builtins.input", boom)
    assert _run(monkeypatch, "fix", str(p), "--write") == 1
    assert p.read_text() == "OLD\n"
    assert "[CONSENT WALL] consent withheld" in capsys.readouterr().out


def test_fix_python_gate_passes_and_uses_this_interpreter(
        monkeypatch, capsys, tmp_path, writewiz_bank):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    seen = []

    def fake_run(cmd, **kw):
        seen.append(list(cmd))
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    p = _file(tmp_path, "a.py", "OLD\n")
    _double_yes(monkeypatch, p)
    assert _run(monkeypatch, "fix", str(p), "--write") == 0
    gate = [c for c in seen if "wiz_central_toolkit.pythonwiz" in c]
    assert gate and gate[0][0] == sys.executable
    assert "-m" in gate[0]
    assert p.read_text() == "NEW\n"
    assert "gate passed" in capsys.readouterr().out


def test_fix_python_gate_rejection_writes_nothing(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    monkeypatch.setattr(subprocess, "run",
                        lambda cmd, **kw: types.SimpleNamespace(
                            returncode=1, stdout="", stderr=""))
    p = _file(tmp_path, "a.py", "OLD\n")
    assert _run(monkeypatch, "fix", str(p), "--write") == 1
    assert p.read_text() == "OLD\n"
    assert "rejected" in capsys.readouterr().out


# ---------- scan ----------

def test_scan_seatless_falls_back_to_static_engine(monkeypatch, capsys, tmp_path):
    """R1: with no daemon, scan does not die — the built-in static
    engine audits instead, and its findings fail the scan."""
    _file(tmp_path, "bad.py", "password = 'hunter2'\n")
    _file(tmp_path, "ok.py", "x = 1\n")
    assert _run(monkeypatch, "scan", str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "engine: static (built-in rules)" in out
    assert "CG002" in out and "hardcoded-secret" in out
    assert "could not be audited" not in out


def test_scan_seatless_clean_dir_returns_zero(monkeypatch, capsys, tmp_path):
    _file(tmp_path, "ok.py", "x = 1\n")
    assert _run(monkeypatch, "scan", str(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "engine: static (built-in rules)" in out
    assert "scanned 1 files" in out


def test_scan_lists_findings_and_fails(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH")))
    _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "scan", str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "HIGH=1" in out and "a.py: C=0 H=1" in out


def test_scan_json_output(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result())
    _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "scan", str(tmp_path), "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data == {"files_scanned": 1, "failed": 0, "findings": []}


def test_python_gate_really_rejects_broken_code(monkeypatch, capsys, tmp_path):
    """No subprocess mock: the real pythonwiz gate must reject a syntax error."""
    monkeypatch.setattr(cgcli, "fix", lambda p: {
        "status": "OK", "issues_fixed": 1, "fix_model": "m",
        "fixed_code": "def broken(:\n"})
    p = _file(tmp_path, "a.py", "OLD\n")
    assert _run(monkeypatch, "fix", str(p), "--write") == 1
    assert p.read_text() == "OLD\n"


# ---------- R1: static engine (network blocked => seatless) ----------

from wiz_central_toolkit.codeguardwiz import static_engine as se

DIRTY = (
    "import subprocess\n"
    "password = 'hunter2'\n"
    "eval('1+1')\n"
    "try:\n"
    "    risky()\n"
    "except:\n"
    "    pass\n"
    "subprocess.run('ls', shell=True)\n"
)
CLEAN = "def add(a, b):\n    return a + b\n"
BROKEN = "def broken(:\n"


def test_static_engine_finds_the_dirty_set():
    ids = {f["rule"] for f in se.scan_source(DIRTY)}
    assert {"CG002", "CG003", "CG004", "CG007"} <= ids


def test_static_engine_ignores_env_secret_and_try_except():
    src = ("import os\n"
           "password = os.environ['PW']\n"
           "try:\n"
           "    x()\n"
           "except ValueError:\n"
           "    raise\n")
    assert se.scan_source(src) == []


def test_static_engine_syntax_and_swallow_and_weak_hash():
    ids = {f["rule"] for f in se.scan_source(BROKEN)}
    assert ids == {"CG001"}
    ids = {f["rule"] for f in se.scan_source(
        "import hashlib\n"
        "try:\n"
        "    x()\n"
        "except ValueError:\n"
        "    pass\n"
        "hashlib.md5(b'x')\n")}
    assert {"CG006", "CG008"} <= ids


def test_audit_seatless_uses_static_engine(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "dirty.py", DIRTY)
    assert _run(monkeypatch, "audit", str(p)) == 1
    out = capsys.readouterr().out
    assert "engine: static (built-in rules)" in out
    assert "CG002" in out and "CG003" in out and "CG007" in out
    assert "no audit seat" not in out


def test_audit_seatless_clean_file_passes(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "clean.py", CLEAN)
    assert _run(monkeypatch, "audit", str(p)) == 0
    out = capsys.readouterr().out
    assert "verdict: [OK] no high-severity findings" in out


def test_audit_seatless_broken_file_reports_syntax(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "broken.py", BROKEN)
    assert _run(monkeypatch, "audit", str(p)) == 1
    out = capsys.readouterr().out
    assert "CG001" in out and "syntax-error" in out


def test_audit_engine_model_seatless_is_an_honest_refusal(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "dirty.py", DIRTY)
    assert _run(monkeypatch, "audit", str(p), "--engine", "model") == 1
    out = capsys.readouterr().out
    assert "no audit seat" in out and "seat one" in out
    assert "CG002" not in out  # no silent fallback to static


def test_severity_seatless_groups_findings(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "dirty.py", DIRTY)
    assert _run(monkeypatch, "severity", str(p)) == 1
    out = capsys.readouterr().out
    assert "engine: static (built-in rules)" in out
    assert "HIGH (" in out and "CG002" in out
    assert "MEDIUM (" in out and "CG007" in out


def test_explain_rule_by_id_and_name(monkeypatch, capsys):
    assert _run(monkeypatch, "explain", "CG002") == 0
    out = capsys.readouterr().out
    assert "CG002 hardcoded-secret (HIGH)" in out
    assert _run(monkeypatch, "explain", "hardcoded-secret") == 0
    assert "CG002" in capsys.readouterr().out
    assert _run(monkeypatch, "explain", "CG999") == 1


def test_explain_file_line_seatless(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "dirty.py", DIRTY)
    assert _run(monkeypatch, "explain", str(p), "2") == 0
    out = capsys.readouterr().out
    assert "Rule at line 2" in out and "CG002" in out
    assert _run(monkeypatch, "explain", str(p), "1") == 1
    assert "no issue found at line 1" in capsys.readouterr().out


def test_roster_seatless_lists_both_engines(monkeypatch, capsys):
    assert _run(monkeypatch, "roster") == 0
    out = capsys.readouterr().out
    assert "[OK] static (built-in rules)" in out
    assert "model seat — none served" in out
    assert "CG007 bare-except (MEDIUM)" in out


def test_fix_seatless_stages_via_writewiz(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    src = "try:\n    risky()\nexcept:\n    raise SystemExit\n"
    p = _file(tmp_path, "a.py", src)
    before = p.read_bytes()
    assert _run(monkeypatch, "fix", str(p)) == 0
    out = capsys.readouterr().out
    assert "[STAGED] fix for" in out
    assert "write_wizard commit" in out
    assert p.read_bytes() == before  # fix never writes the file itself
    from wiz_central_toolkit.writewiz import write_wizard as ww
    draft, _meta = ww._draft_path(p)
    assert draft.exists()
    assert "except Exception:" in draft.read_text()


def test_fix_seatless_lists_unfixable_findings(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    p = _file(tmp_path, "dirty.py", DIRTY)
    assert _run(monkeypatch, "fix", str(p)) == 0
    out = capsys.readouterr().out
    assert "[STAGED]" in out  # the bare except is staged
    assert "needs a person or the model engine" in out
    assert "CG002" in out and "CG003" in out


def test_fix_static_write_flag_is_refused(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    src = "try:\n    risky()\nexcept:\n    pass\n"
    p = _file(tmp_path, "a.py", src)
    rc = _run(monkeypatch, "fix", str(p), "--engine", "static", "--write")
    assert rc == 1
    out = capsys.readouterr().out
    assert "staged through write_wizard" in out
    assert p.read_text() == src


def test_fix_seatless_clean_file_stages_nothing(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    p = _file(tmp_path, "clean.py", CLEAN)
    assert _run(monkeypatch, "fix", str(p)) == 0
    assert "nothing to stage" in capsys.readouterr().out
