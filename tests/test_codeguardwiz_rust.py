"""codeguardwiz rust engine: RS001–RS007, dispatch, and the
downstream consumers (explain / watch / fix) running on Rust
findings unchanged. Network is blocked for every test."""
import json
import sys
import urllib.request

import pytest

from wiz_central_toolkit.codeguardwiz import cli as cgcli
from wiz_central_toolkit.codeguardwiz import rust_engine as reng
from wiz_central_toolkit.codeguardwiz.cli import main

SECRET_VALUE = "sk-live-9f8e7d6c5b4a3210deadbeef"

FLAWED_RS = """use std::process::Command;

const API_KEY: &str = "SECRET_VALUE_HERE";

fn main() {
    let data = std::fs::read_to_string("in.txt").unwrap();
    let n: u32 = unsafe { std::mem::transmute::<f32, u32>(1.5) };
    let out = Command::new("sh").arg("-c").arg(data).output().expect("run");
    panic!("giving up");
    let v = vec![1, 2, 3];
    let x = unsafe { *v.as_ptr() };
    let s = unsafe { String::from_utf8_unchecked(vec![104, 105]) };
    // let ignored = thing.unwrap();
    todo!("finish the rest");
}
""".replace("SECRET_VALUE_HERE", SECRET_VALUE)

CLEAN_RS = """fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() {
    let total = add(2, 3);
    println!("total: {total}");
}
"""

FLAWED_TOML = """[package]
name = "fixture"
version = "0.1.0"

[dependencies]
serde = "*"
regex = { version = "*", features = ["unicode"] }
helper = { git = "https://example.com/helper.git" }
pinned = { git = "https://example.com/pinned.git", rev = "abc123" }
clap = "4"
"""


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise OSError("network blocked in tests")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    monkeypatch.delenv("CODEGUARD_AUDIT_MODEL", raising=False)
    monkeypatch.delenv("CODEGUARD_FIX_MODEL", raising=False)


@pytest.fixture
def baseline_bank(monkeypatch, tmp_path):
    monkeypatch.setattr(cgcli, "STATE_DIR", tmp_path / ".codeguard-wizard")
    monkeypatch.setattr(cgcli, "BASELINES",
                        tmp_path / ".codeguard-wizard" / "baselines.json")
    return tmp_path


def _run(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["codeguardwiz", *argv])
    return main()


def _file(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def _rules(findings):
    return [f["rule"] for f in findings]


# ---------- the rules ----------

def test_rs001_unsafe_block_and_fn():
    src = "fn a() { let x = unsafe { 1 }; }\nunsafe fn b() {}\n"
    hits = [f for f in reng.scan_source(src) if f["rule"] == "RS001"]
    assert len(hits) == 2
    assert all(f["severity"] == "medium" for f in hits)


def test_rs002_unwrap_and_expect():
    src = "let a = x.unwrap();\nlet b = y.expect(\"why\");\n"
    hits = [f for f in reng.scan_source(src) if f["rule"] == "RS002"]
    assert len(hits) == 2
    assert ".unwrap()" in hits[0]["detail"]
    assert ".expect()" in hits[1]["detail"]


def test_rs003_panic_markers():
    src = 'panic!("a");\ntodo!("b");\nunimplemented!("c");\n'
    hits = [f for f in reng.scan_source(src) if f["rule"] == "RS003"]
    assert len(hits) == 3
    assert all(f["severity"] == "low" for f in hits)


def test_rs004_shell_construction_shapes():
    src = ('let a = Command::new("sh");\n'
           'let b = Command::new("bash").arg("-c");\n'
           'let c = Command::new(format!("{prog}"));\n'
           'let d = Command::new("ls").arg("-la");\n')
    hits = [f for f in reng.scan_source(src) if f["rule"] == "RS004"]
    # shell spawn, shell spawn + -c flag, format!-assembled program;
    # the plain `ls` invocation with inert args must not fire
    assert len(hits) == 4
    assert all(f["severity"] == "high" for f in hits)


def test_rs005_transmute_and_unchecked():
    src = ("let a = unsafe { std::mem::transmute::<f32, u32>(1.5) };\n"
           "let b = v.get_unchecked(0);\n"
           "let c = String::from_utf8_unchecked(bytes);\n"
           "let d = v.get(0);\n")
    hits = [f for f in reng.scan_source(src) if f["rule"] == "RS005"]
    assert len(hits) == 3
    assert all(f["severity"] == "high" for f in hits)


def test_rs006_secret_fires_and_value_never_printed():
    findings = reng.scan_source(FLAWED_RS)
    hits = [f for f in findings if f["rule"] == "RS006"]
    assert len(hits) == 1
    assert hits[0]["line"] == 3
    assert hits[0]["severity"] == "high"
    # the value itself appears nowhere in any finding, of any rule
    assert SECRET_VALUE not in json.dumps(findings)
    assert SECRET_VALUE not in reng.RULE_BY_ID["RS006"].explanation


def test_rs006_let_and_field_shapes():
    src = ('let password = "hunter2";\n'
           'let cfg = Config { api_key: "abc123" };\n'
           'let key = std::env::var("API_KEY");\n')
    hits = [f for f in reng.scan_source(src) if f["rule"] == "RS006"]
    assert len(hits) == 2  # the env lookup is not a literal


def test_rs007_cargo_toml():
    findings = reng.scan_toml_source(FLAWED_TOML)
    hits = [f for f in findings if f["rule"] == "RS007"]
    assert len(hits) == 3  # serde "*", regex "*", helper git w/o rev
    assert all(f["severity"] == "medium" for f in hits)
    names = " ".join(f["detail"] for f in hits)
    assert "'serde'" in names and "'regex'" in names and "'helper'" in names
    assert "'pinned'" not in names and "'clap'" not in names


def test_rs007_ignores_non_dependency_sections():
    src = '[package]\nname = "x"\nversion = "*"\n'
    assert reng.scan_toml_source(src) == []


def test_clean_rust_file_scores_clean():
    assert reng.scan_source(CLEAN_RS) == []


def test_comment_lines_do_not_fire_code_rules():
    src = "// let x = thing.unwrap();\n// panic!(\"no\")\nfn f() {}\n"
    assert reng.scan_source(src) == []


def test_finding_shape_matches_static_engine():
    for f in reng.scan_source(FLAWED_RS):
        assert set(f) == {"path", "line", "rule", "name", "severity",
                          "detail"}
        assert f["severity"] in ("high", "medium", "low")


def test_flawed_fixture_counts():
    c = reng.counts(reng.scan_source(FLAWED_RS))
    assert c == {"high": 5, "medium": 5, "low": 2}


def test_no_mechanical_fix_for_rust():
    assert reng.FIXABLE_RULES == ()
    out, applied = reng.apply_fixes(FLAWED_RS, reng.scan_source(FLAWED_RS))
    assert applied == 0 and out == FLAWED_RS


def test_collect_files_rust_side(tmp_path):
    _file(tmp_path, "a.rs", CLEAN_RS)
    _file(tmp_path, "Cargo.toml", FLAWED_TOML)
    _file(tmp_path, "b.py", "x = 1\n")
    names = sorted(p.name for p in reng.collect_files(tmp_path))
    assert names == ["Cargo.toml", "a.rs"]


# ---------- CLI dispatch ----------

def test_audit_static_rust_file(monkeypatch, capsys, tmp_path, baseline_bank):
    p = _file(tmp_path, "flawed.rs", FLAWED_RS)
    assert _run(monkeypatch, "audit", "--engine", "static", str(p)) == 1
    out = capsys.readouterr().out
    assert out.startswith("engine: static (built-in rules)")
    assert "(rust, static rules)" in out
    for rid in ("RS001", "RS002", "RS003", "RS004", "RS005", "RS006"):
        assert rid in out
    assert SECRET_VALUE not in out


def test_audit_seatless_rust_falls_back_to_static(monkeypatch, capsys,
                                                  tmp_path, baseline_bank):
    p = _file(tmp_path, "flawed.rs", FLAWED_RS)
    assert _run(monkeypatch, "audit", str(p)) == 1
    out = capsys.readouterr().out
    assert "engine: static (built-in rules)" in out
    assert "RS006" in out


def test_audit_static_cargo_toml(monkeypatch, capsys, tmp_path,
                                 baseline_bank):
    p = _file(tmp_path, "Cargo.toml", FLAWED_TOML)
    assert _run(monkeypatch, "audit", "--engine", "static", str(p)) == 0
    out = capsys.readouterr().out
    assert "(rust, static rules)" in out
    assert out.count("RS007") == 3


def test_audit_static_clean_rust_passes(monkeypatch, capsys, tmp_path,
                                        baseline_bank):
    p = _file(tmp_path, "clean.rs", CLEAN_RS)
    assert _run(monkeypatch, "audit", "--engine", "static", str(p)) == 0
    assert "verdict: [OK]" in capsys.readouterr().out


def test_audit_json_rust_language(monkeypatch, capsys, tmp_path,
                                  baseline_bank):
    p = _file(tmp_path, "flawed.rs", FLAWED_RS)
    assert _run(monkeypatch, "audit", "--engine", "static",
                "--json", str(p)) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["language"] == "rust"
    assert {f["rule"] for f in report["findings"]} >= {"RS004", "RS006"}


def test_mixed_directory_one_audit(monkeypatch, capsys, tmp_path,
                                   baseline_bank):
    _file(tmp_path, "bad.py", "import subprocess\n"
                              "subprocess.run('ls', shell=True)\n")
    _file(tmp_path, "flawed.rs", FLAWED_RS)
    _file(tmp_path, "Cargo.toml", FLAWED_TOML)
    assert _run(monkeypatch, "audit", "--engine", "static",
                str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert out.count("engine: static (built-in rules)") == 1
    assert "CG004" in out  # Python finding
    assert "RS006" in out  # Rust finding
    assert "RS007" in out  # Cargo.toml finding
    assert "scanned 3 files" in out


def test_scan_mixed_directory(monkeypatch, capsys, tmp_path, baseline_bank):
    _file(tmp_path, "bad.py", "eval('x')\n")
    _file(tmp_path, "flawed.rs", FLAWED_RS)
    assert _run(monkeypatch, "scan", "--engine", "static",
                str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "CG003" in out and "RS004" in out
    assert "scanned 2 files" in out


def test_severity_static_rust(monkeypatch, capsys, tmp_path, baseline_bank):
    p = _file(tmp_path, "flawed.rs", FLAWED_RS)
    assert _run(monkeypatch, "severity", "--engine", "static",
                str(p)) == 1
    out = capsys.readouterr().out
    assert "RS006" in out and "HIGH (5)" in out


def test_explain_rust_finding_at_line(monkeypatch, capsys, tmp_path,
                                      baseline_bank):
    p = _file(tmp_path, "flawed.rs", FLAWED_RS)
    assert _run(monkeypatch, "explain", "--engine", "static",
                str(p), "3") == 0
    out = capsys.readouterr().out
    assert "Rule at line 3" in out and "RS006" in out
    assert SECRET_VALUE not in out
    assert _run(monkeypatch, "explain", "--engine", "static",
                str(p), "1") == 1
    assert "no issue found at line 1" in capsys.readouterr().out


def test_explain_rust_rule_by_id(monkeypatch, capsys):
    assert _run(monkeypatch, "explain", "RS004") == 0
    out = capsys.readouterr().out
    assert "RS004 shell-construction (HIGH)" in out


def test_watch_rust_flow_end_to_end(monkeypatch, capsys, tmp_path,
                                    baseline_bank):
    p = _file(tmp_path, "watched.rs", CLEAN_RS)
    assert _run(monkeypatch, "audit", "--engine", "static", str(p)) == 0
    capsys.readouterr()
    assert _run(monkeypatch, "watch", str(p)) == 0
    out = capsys.readouterr().out
    assert "baseline score 100 -> now 100" in out
    p.write_text(CLEAN_RS + "\nfn boom() {\n"
                 "    let v = std::fs::read_to_string(\"x\").unwrap();\n}\n")
    assert _run(monkeypatch, "watch", str(p)) == 0
    out = capsys.readouterr().out
    assert "baseline score 100 -> now 95" in out
    assert "new: 1" in out and "RS002" in out


def test_fix_static_rust_stages_nothing(monkeypatch, capsys, tmp_path,
                                        baseline_bank):
    p = _file(tmp_path, "flawed.rs", FLAWED_RS)
    before = p.read_bytes()
    assert _run(monkeypatch, "fix", "--engine", "static", str(p)) == 0
    out = capsys.readouterr().out
    assert "nothing staged" in out
    assert "no safe mechanical fix" in out
    assert "model engine's job" in out
    assert "[STAGED]" not in out
    assert p.read_bytes() == before


def test_fix_static_clean_rust(monkeypatch, capsys, tmp_path, baseline_bank):
    p = _file(tmp_path, "clean.rs", CLEAN_RS)
    assert _run(monkeypatch, "fix", "--engine", "static", str(p)) == 0
    assert "no findings" in capsys.readouterr().out


def test_roster_lists_rust_rules(monkeypatch, capsys):
    assert _run(monkeypatch, "roster") == 0
    out = capsys.readouterr().out
    assert "RS001 unsafe-block (MEDIUM)" in out
    assert "RS007 unpinned-dependency (MEDIUM)" in out
    assert "CG007 bare-except (MEDIUM)" in out
