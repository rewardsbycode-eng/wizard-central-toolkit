"""Codegen suite — brainstorm / build / debug / diff (AVS, 2026-11-09).

The model authors complete content; the person sees the diff and
answers the double ask; only then does writewiz land the text.
Brainstorm is hands-off: a TOOL: line there is text, never an act.
"""

import json
import sys

import pytest

from wiz_central_toolkit.godfatherwiz.lib import cli as gf_cli
from wiz_central_toolkit.godfatherwiz.lib import godfather_wizard as gw
from wiz_central_toolkit.writewiz import write_wizard as ww


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    bank = home / ".godfather"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(gw, "HOME", home)
    monkeypatch.setattr(gw, "BANK", bank)
    monkeypatch.setattr(gw, "LEDGER", bank / "ledger.jsonl")
    monkeypatch.setattr(gw, "ROUTER_DB", bank / "routes.json")
    monkeypatch.setattr(gw, "STATE_FILE", bank / "session_state.json")
    monkeypatch.setattr(gw, "BIN", home / "bin")
    monkeypatch.delenv("GODFATHER_MODEL", raising=False)
    monkeypatch.setattr(gf_cli, "speak_if_enabled", lambda text: None)

    write_bank = home / ".write-wizard"
    monkeypatch.setattr(ww, "HOME", home)
    monkeypatch.setattr(ww, "BANK", write_bank)
    monkeypatch.setattr(ww, "QUARANTINE", write_bank / "pending")
    monkeypatch.setattr(ww, "BACKUPS", write_bank / "backups")
    monkeypatch.setattr(ww, "LEDGER", write_bank / "ledger.jsonl")
    monkeypatch.setattr(ww, "PROTECTED", write_bank / "protected.json")
    return home


def _drive(monkeypatch, lines):
    answers = iter(lines)
    monkeypatch.setattr(
        "builtins.input", lambda prompt="": next(answers))
    gf_cli.run_repl()


def _seat(monkeypatch, reply, roster=("seat-model",)):
    calls = []

    def fake_chat(messages, model):
        calls.append((messages, model))
        if callable(reply):
            return reply(messages, model)
        return reply

    monkeypatch.setattr(gw, "_ollama_roster", lambda: list(roster))
    monkeypatch.setattr(gw, "_ollama_chat_api", fake_chat)
    return calls


# ---------------------------------------------------------------- seats

def test_seat_for_task_default_then_roster(home, monkeypatch):
    monkeypatch.setattr(
        gw, "_ollama_roster",
        lambda: ["roster-model", "default-model", "build-model"])
    assert gw.set_model_assignment("default", "default-model")[0] == 0
    assert gw.set_model_assignment("build", "build-model")[0] == 0
    assert json.loads((home / ".godfather" / "models.json").read_text()) == {
        "default": "default-model", "build": "build-model"}

    # seat_for returns (provider, model); a bare stored name is an
    # Ollama seat (provider layer, 2026-11-09).
    assert gw.seat_for("build") == ("ollama", "build-model")   # task entry
    assert gw.seat_for("debug") == ("ollama", "default-model")  # default
    assert gw.seat_for("diff") == ("ollama", "default-model")

    assert gw.unset_model_assignment("default")[0] == 0
    assert gw.seat_for("debug") == ("ollama", "roster-model")  # roster pick
    monkeypatch.setenv("GODFATHER_MODEL", "build-model")
    assert gw.seat_for("debug") == ("ollama", "build-model")   # env pick


def test_seat_for_assigned_but_not_serving_is_none(home, monkeypatch):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: ["other-model"])
    assert gw.set_model_assignment("build", "ghost-model")[0] == 0
    assert gw.seat_for("build") is None
    assert "assigned model 'ghost-model'" in gw.seat_unavailable_line("build")
    assert "not in the live Ollama roster" in \
        gw.seat_unavailable_line("build")


def test_models_cli_set_show_unset(home, monkeypatch, capsys):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: ["build-model"])
    monkeypatch.setattr(sys, "argv",
                        ["godfatherwiz", "models", "set", "build",
                         "build-model"])
    assert gf_cli.main() == 0
    assert "build model set to build-model" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["godfatherwiz", "models"])
    assert gf_cli.main() == 0
    out = capsys.readouterr().out
    assert "build: build-model (serving)" in out
    assert "model assignments" in out

    monkeypatch.setattr(sys, "argv",
                        ["godfatherwiz", "models", "unset", "build"])
    assert gf_cli.main() == 0
    assert json.loads((home / ".godfather" / "models.json").read_text()) == {}


# ------------------------------------------------------------- brainstorm

def test_brainstorm_tool_line_executes_nothing(home, monkeypatch, capsys):
    _seat(monkeypatch, "TOOL: writewiz commit /tmp/x\njust an idea")
    executed = []
    monkeypatch.setattr(
        gw, "call_sibling",
        lambda parts, stdin=None: executed.append(parts) or (0, "ran"))
    _drive(monkeypatch, ["/brainstorm plan the heist", "/exit"])
    out = capsys.readouterr().out
    assert "hands off" in out
    assert "treated as text; nothing executed" in out
    assert executed == []


def test_brainstorm_plain_text_stays_in_mode(home, monkeypatch, capsys):
    calls = _seat(monkeypatch, "a calm answer")
    _drive(monkeypatch, [
        "/brainstorm", "what if we used queues?", "/brainstorm end",
        "/exit"])
    out = capsys.readouterr().out
    assert "a calm answer" in out
    assert "brainstorm mode ended" in out
    assert len(calls) == 1
    assert calls[0][1] == "seat-model"


# ----------------------------------------------------------------- build

def test_build_double_yes_lands_exact_bytes_and_journals(
        home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "made.py"
    calls = _seat(monkeypatch, "print('new')\n")
    _drive(monkeypatch, [
        f"/build {target} create a greeting",
        "y", f"yes, write {target}", "/exit"])
    out = capsys.readouterr().out
    assert target.read_bytes() == b"print('new')\n"
    assert "--- build proposal by seat: ollama · seat-model" in out
    assert "+print('new')" in out
    assert len(calls) == 1
    rows = [r for r in gw.ledger_rows() if r["event"] == "CODEGEN"]
    assert len(rows) == 1
    assert rows[0]["target"] == str(target)
    assert "task=build" in rows[0]["detail"]
    assert "model=seat-model" in rows[0]["detail"]


def test_build_no_at_second_ask_stages_only(
        home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "made.py"
    _seat(monkeypatch, "print('new')\n")
    _drive(monkeypatch, [
        f"/build {target} create a greeting",
        "y", "no", "/exit"])
    out = capsys.readouterr().out
    assert not target.exists()
    assert "consent withheld" in out
    draft, _meta = ww._draft_path(target)
    assert draft.exists()
    assert draft.read_text() == "print('new')\n"
    assert not [r for r in gw.ledger_rows() if r["event"] == "CODEGEN"]


# ------------------------------------------------------------------ diff

def test_diff_stages_nothing_and_asks_nothing(
        home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "old.py"
    target.write_text("print('old')\n")
    _seat(monkeypatch, "print('reviewed')\n")

    def forbidden(*args, **kwargs):
        raise AssertionError("diff must not stage or ask")

    monkeypatch.setattr(gf_cli, "stage_codegen_content", forbidden)
    monkeypatch.setattr(gf_cli, "confirm_codegen_write", forbidden)
    _drive(monkeypatch, [f"/diff {target} replace the greeting", "/exit"])
    out = capsys.readouterr().out
    assert "full-content revision" in out
    assert "-print('old')" in out
    assert "+print('reviewed')" in out
    assert target.read_text() == "print('old')\n"


def test_build_reuses_reviewed_diff_proposal(
        home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "made.py"
    calls = _seat(monkeypatch, "print('reviewed')\n")
    _drive(monkeypatch, [
        f"/diff {target} create the greeting",
        f"/build {target} create the greeting",
        "y", f"yes, write {target}", "/exit"])
    out = capsys.readouterr().out
    assert "the proposal you reviewed" in out
    assert len(calls) == 1
    assert target.read_text() == "print('reviewed')\n"


# ----------------------------------------------------------------- debug

def test_debug_uses_pythonwiz_context_and_lands_fix(
        home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "sick.py"
    target.write_text("def broken(:\n    pass\n")
    seen = {}

    def reply(messages, model):
        seen["messages"] = messages
        return "def fixed():\n    return 1\n"

    _seat(monkeypatch, reply)
    _drive(monkeypatch, [
        f"/debug {target} repair it",
        "y", f"yes, write {target}", "/exit"])
    out = capsys.readouterr().out
    assert target.read_text() == "def fixed():\n    return 1\n"
    prompt = seen["messages"][-1]["content"]
    assert "python_wizard check exit 1" in prompt
    assert "def broken" in prompt
    assert "repair it" in prompt
    assert "--- debug proposal by seat: ollama · seat-model" in out


# --------------------------------------------------------------- seatless

def test_all_four_modes_seatless_are_plain_lines(
        home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "x.py"
    target.write_text("x = 1\n")
    monkeypatch.setattr(gw, "_ollama_roster", lambda: [])
    _drive(monkeypatch, [
        "/brainstorm hello",
        f"/build {target} create more",
        f"/debug {target}",
        f"/diff {target} change it",
        "/exit"])
    out = capsys.readouterr().out
    assert "no model seat is configured or serving" in out
    assert "the brainstorm feature needs a live model" in out
    assert "the build feature needs a live model" in out
    assert "the debug feature needs a live model" in out
    assert "the diff feature needs a live model" in out
    assert target.read_text() == "x = 1\n"


def test_assigned_but_not_serving_build_is_honest(
        home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "x.py"
    assert gw.set_model_assignment("build", "ghost-model")[0] == 0
    calls = _seat(monkeypatch, "x = 2\n", roster=("other-model",))
    _drive(monkeypatch, [f"/build {target} change it", "/exit"])
    out = capsys.readouterr().out
    assert "assigned model 'ghost-model'" in out
    assert "not in the live Ollama roster" in out
    assert calls == []
    assert not target.exists()
