"""R3 + R4 + R5 — AVS-concluded 2026-11-09.

R3: every in-box citizen has a REPL slash; /fix and /heal run
godfatherwiz's own heal chain; /models answers from the configured
seats. R4: plain REPL text routes deterministically first, the
oracle speaks only when a seat serves, the oracle's spine teaches
the Godfather Wizard's own senses, and sense TOOL lines execute
in-process.
R5: the consent wall covers write-class routes only — reads and
staging run free — and a write-class route asks twice before it
executes.
"""

import sys

import pytest

from wiz_central_toolkit.godfatherwiz.lib import cli as gf_cli
from wiz_central_toolkit.godfatherwiz.lib import godfather_wizard as gw


# ---------------------------------------------------------------- R3

def test_new_slashes_dispatch_in_box():
    m = gw.list_all_slash_commands()
    assert m["/banner"] == "banner_wizard"
    assert m["/codeguard"] == "codeguard_wizard"
    assert m["/json"] == "json_wizard"
    assert m["/rust"] == "rust_wizard"
    assert m["/tmux"] == "tmux_wizard"
    assert m["/write"] == "write_wizard"
    assert m["/verbs"] == "read_wizard verbs"


def test_repointed_slashes_stay_in_box():
    m = gw.list_all_slash_commands()
    assert m["/fix"] == "godfather_wizard heal"
    assert m["/heal"] == "godfather_wizard heal"
    assert m["/models"] == "godfather_wizard models"
    assert not any("repairwiz" in v or "ollamawiz" in v
                   for v in m.values())
    assert len(m) == 32


# ---------------------------------------------------------------- R5

@pytest.fixture
def routes(monkeypatch):
    table = {
        "list/listing": ["godfatherwiz", "listing"],
        "deploy": ["writewiz", "commit"],
        "stage": ["debugwiz", "propose"],
    }
    monkeypatch.setattr(gw, "load_routes", lambda: table)
    return table


def test_read_class_route_free_despite_scary_word(routes, tmp_path):
    pipeline, reason, wall = gw.classify_route(
        f"delete the listing of {tmp_path}", [])
    assert pipeline[:2] == ["godfatherwiz", "listing"]
    assert str(tmp_path) in pipeline
    assert wall is False


def test_write_class_route_walls_with_pipeline(routes):
    pipeline, reason, wall = gw.classify_route("deploy", [])
    assert pipeline == ["writewiz", "commit"]
    assert wall is True


def test_staging_route_is_free(routes):
    pipeline, reason, wall = gw.classify_route("stage", [])
    assert pipeline == ["debugwiz", "propose"]
    assert wall is False


def test_unmapped_mutation_intent_refused(routes):
    pipeline, reason, wall = gw.classify_route("delete everything", [])
    assert pipeline is None and wall is True


def test_unmapped_plain_text_out_of_scope(routes):
    pipeline, reason, wall = gw.classify_route("zanzibar quux", [])
    assert pipeline is None and wall is False


def test_route_directive_back_compat(routes):
    assert gw.route_directive("delete everything", [])[0] == "WALL"
    assert gw.route_directive("deploy", [])[0] == "WALL"
    pipeline, _reason = gw.route_directive("stage", [])
    assert pipeline == ["debugwiz", "propose"]


@pytest.mark.parametrize("pipeline,expected", [
    (["writewiz", "commit", "x"], True),
    (["writewiz", "discard", "x"], True),
    (["writewiz", "rollback", "x"], True),
    (["writewiz", "purge-old", "3"], True),
    (["writewiz", "protect", "x"], True),
    (["writewiz", "propose", "x"], False),
    (["writewiz", "pending"], False),
    (["writewiz", "preview", "x"], False),
    (["codeguardwiz", "fix", "--write", "x"], True),
    (["codeguardwiz", "fix", "x"], False),
    (["codeguardwiz", "audit", "x"], False),
    (["debugwiz", "propose", "x"], False),
    (["godfatherwiz", "heal", "x"], False),
    (["godfatherwiz", "listing", "x"], False),
    ([], False),
])
def test_pipeline_is_write_class(pipeline, expected):
    assert gw.pipeline_is_write_class(pipeline) is expected


def test_confirm_write_class_needs_both_answers(monkeypatch):
    answers = iter(["y", "yes, writewiz commit x"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    assert gf_cli._confirm_write_class(["writewiz", "commit", "x"]) is True


def test_confirm_write_class_second_no_aborts(monkeypatch):
    answers = iter(["y", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    assert gf_cli._confirm_write_class(["writewiz", "commit", "x"]) is False


def test_confirm_write_class_eof_is_no(monkeypatch):
    def boom(prompt=""):
        raise EOFError
    monkeypatch.setattr("builtins.input", boom)
    assert gf_cli._confirm_write_class(["writewiz", "commit", "x"]) is False


@pytest.fixture
def bank(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    bank_dir = home / ".godfather"
    monkeypatch.setattr(gw, "HOME", home)
    monkeypatch.setattr(gw, "BANK", bank_dir)
    monkeypatch.setattr(gw, "LEDGER", bank_dir / "ledger.jsonl")
    monkeypatch.setattr(gw, "ROUTER_DB", bank_dir / "routes.json")
    monkeypatch.setattr(gw, "STATE_FILE", bank_dir / "session_state.json")
    return home


def test_run_write_class_denied_at_second_ask(
        bank, monkeypatch, capsys):
    monkeypatch.setattr(
        gw, "load_routes", lambda: {"deploy": ["writewiz", "commit", "x"]})
    executed = []
    monkeypatch.setattr(
        gf_cli, "call_sibling",
        lambda parts, stdin=None: executed.append(parts) or (0, "ran"))
    answers = iter(["y", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(sys, "argv", ["godfatherwiz", "run", "deploy"])
    rc = gf_cli.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "[CONSENT WALL]" in out
    assert "consent withheld — nothing executed" in out
    assert executed == []


def test_run_write_class_executes_after_double_yes(
        bank, monkeypatch, capsys):
    monkeypatch.setattr(
        gw, "load_routes", lambda: {"deploy": ["writewiz", "commit", "x"]})
    executed = []
    monkeypatch.setattr(
        gf_cli, "call_sibling",
        lambda parts, stdin=None: executed.append(parts) or (0, "ran"))
    answers = iter(["y", "yes, writewiz commit x"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(sys, "argv", ["godfatherwiz", "run", "deploy"])
    rc = gf_cli.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert executed == [["writewiz", "commit", "x"]]
    assert "[OK] pipeline complete" in out


# ---------------------------------------------------------------- R4

def test_oracle_spine_teaches_godfatherwiz_senses():
    assert "TOOL: godfather_wizard listing" in gw.ORACLE_SPINE
    assert "truthwiz" not in gw.ORACLE_SPINE


def test_oracle_senses_execute_in_process(monkeypatch, tmp_path):
    (tmp_path / "alpha.txt").write_text("a")
    (tmp_path / "beta.txt").write_text("b")
    calls = {"n": 0}

    def fake_chat(messages, model):
        calls["n"] += 1
        if calls["n"] == 1:
            return f"TOOL: godfatherwiz listing {tmp_path}"
        return "those are the files"

    monkeypatch.setattr(gw, "_ollama_chat_api", fake_chat)
    monkeypatch.delenv("WIZ_AI_PROVIDER", raising=False)
    for attr in ("_last_calls", "_dup_count", "_last_result"):
        if hasattr(gw.oracle_tool_loop, attr):
            delattr(gw.oracle_tool_loop, attr)
    reply, memory = gw.oracle_tool_loop("what files are here?", "m", [])
    assert reply == "those are the files"
    fed_back = "\n".join(m.get("content", "") for m in memory)
    assert "TOOL RESULT" in fed_back
    assert "alpha.txt" in fed_back and "beta.txt" in fed_back
    # the run passed through the duplicate shield's bookkeeping —
    # the line that used to raise NameError on undefined seen_calls
    assert f"godfatherwiz listing {tmp_path}" in \
        gw.oracle_tool_loop._last_calls


def test_seated_models_seatless(monkeypatch):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: [])
    rc, out = gw.seated_models()
    assert rc == 0 and "no model seat" in out
    assert gw.seated_model() is None


def test_seated_models_lists_roster(monkeypatch):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: ["m1", "m2"])
    monkeypatch.setenv("GODFATHER_MODEL", "m2")
    rc, out = gw.seated_models()
    assert rc == 0
    assert "m1" in out and "m2  <- seated" in out
    assert gw.seated_model() == "m2"
    rc, out = gw.call_internal(["godfatherwiz", "models"])
    assert rc == 0 and "m1" in out


@pytest.fixture
def repl_home(bank, monkeypatch):
    monkeypatch.setenv("HOME", str(bank))
    monkeypatch.setattr(gw, "BIN", bank / "bin")
    return bank


def _drive_repl(monkeypatch, lines):
    it = iter(lines)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(it))
    gf_cli.run_repl()


def test_repl_plain_text_routes_without_a_seat(
        repl_home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "room"
    target.mkdir()
    (target / "chair.txt").write_text("x")
    # the REPL resolves its chat seat via seat_for since the
    # provider layer; patch the seat away at that door.
    monkeypatch.setattr(gf_cli, "seat_for", lambda *a, **k: None)
    _drive_repl(monkeypatch, [f"list {target}", "/exit"])
    out = capsys.readouterr().out
    assert "chair.txt" in out
    assert "out of scope" not in out


def test_repl_unmapped_text_seatless_is_out_of_scope(
        repl_home, monkeypatch, capsys):
    monkeypatch.setattr(gf_cli, "seat_for", lambda *a, **k: None)
    _drive_repl(monkeypatch, ["zanzibar quux", "/exit"])
    out = capsys.readouterr().out
    assert "out of scope" in out
    assert "stub reply" not in out


# ------------------------------------------------- name-form fix batch

def test_repl_legacy_diff_two_files_live_loop(
        repl_home, monkeypatch, capsys, tmp_path):
    """The legacy /diff <a> <b> form must diff the two files through
    the live REPL input loop — the gap that let the duplicate-key
    defect ship was that no test ever drove this form end to end."""
    a = tmp_path / "a.txt"
    a.write_text("alpha\nbeta\n")
    b = tmp_path / "b.txt"
    b.write_text("alpha\ngamma\n")
    monkeypatch.setattr(gf_cli, "seat_for", lambda *x, **k: None)
    monkeypatch.setattr(gw, "seat_for", lambda *x, **k: None)
    _drive_repl(monkeypatch, [f"/diff {a} {b}", "/exit"])
    out = capsys.readouterr().out
    assert "files differ" in out
    assert "gamma" in out
    # the pre-fix failure mode: the godfather usage text, because the
    # form dispatched to a nonexistent subcommand
    assert "CLI Commands:" not in out


def test_repl_codegen_diff_form_still_seatless_honest(
        repl_home, monkeypatch, capsys, tmp_path):
    """The proposal form of /diff (file + instruction words) still
    reaches the review flow and answers honestly without a seat."""
    a = tmp_path / "a.txt"
    a.write_text("alpha\n")
    monkeypatch.setattr(gf_cli, "seat_for", lambda *x, **k: None)
    monkeypatch.setattr(gw, "seat_for", lambda *x, **k: None)
    _drive_repl(monkeypatch,
                [f"/diff {a} make it louder please", "/exit"])
    out = capsys.readouterr().out
    assert "no model seat" in out


def test_routes_display_hides_scheduled_tasks(monkeypatch, capsys):
    """After a schedule, the routes display shows routes only —
    scheduled-task records live in the queue's views, not here."""
    from unittest.mock import patch
    bank = {
        "diff/compare": ["diff_wizard", "files"],
        "task_63475": {"id": "t1", "intent": "later",
                       "scheduled_at": 0, "delay_sec": 5,
                       "status": "pending"},
    }
    monkeypatch.setattr(gf_cli, "load_routes", lambda: bank)
    with patch("sys.argv", ["godfather_wizard", "routes"]):
        rc = gf_cli._dispatch()
    out = capsys.readouterr().out
    assert rc == 0
    assert "diff/compare" in out and "diff_wizard files" in out
    assert "task_63475" not in out
    assert "scheduled_at" not in out

# --- 0.2.5: Verb + Object Generation Classifier ---
from wiz_central_toolkit.godfatherwiz.lib.godfather_wizard import is_generation_intent

def test_generation_classifier():
    assert is_generation_intent("create a poem") is True
    assert is_generation_intent("write a poem") is True
    assert is_generation_intent("create a script") is True
    assert is_generation_intent("delete the second stanza") is True
    assert is_generation_intent("delete ~/x.py") is False
    assert is_generation_intent("kill the tmux session") is False
