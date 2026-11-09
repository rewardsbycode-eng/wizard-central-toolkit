"""Small batch (AVS conclusions, 2026-11-09):
- oracle consent parity: staging/read TOOL lines run free and never
  prompt; write-class TOOL lines ask twice, and a no at either ask
  executes nothing and tells the model the Governor denied it.
- call_ollama skips the doomed ollamawiz call when it resolves nowhere.
- FATHER LAW 2 names the Godfather Wizard's own senses (corrected to
  the proper name form by the 2026-11-09 law-text pass; originally
  pinned with the short form); the sampler's flavor no longer
  borrows Pro's 33.
"""
import types

import pytest

from wiz_central_toolkit.godfatherwiz.lib import godfather_wizard as gw
from wiz_central_toolkit.godfatherwiz.lib import cli as gf_cli


def _drive_oracle(monkeypatch, tool_lines):
    seq = iter(tool_lines + ["all done"])
    monkeypatch.setattr(gw, "_ollama_chat_api",
                        lambda messages, model: next(seq))
    monkeypatch.delenv("WIZ_AI_PROVIDER", raising=False)
    for attr in ("_last_calls", "_dup_count", "_last_result"):
        if hasattr(gw.oracle_tool_loop, attr):
            delattr(gw.oracle_tool_loop, attr)


def _fleet(monkeypatch, executed):
    monkeypatch.setattr(gw, "fleet_census", lambda: (1, ["writewiz"]))
    monkeypatch.setattr(
        gw, "call_sibling",
        lambda parts, stdin=None: executed.append(parts) or (0, "ran"))


def test_oracle_propose_line_runs_free_and_never_prompts(monkeypatch):
    executed = []
    _fleet(monkeypatch, executed)
    _drive_oracle(monkeypatch, ["TOOL: writewiz propose /tmp/x"])

    def boom(prompt=""):
        raise AssertionError("staging must never prompt")
    monkeypatch.setattr("builtins.input", boom)
    reply, _memory = gw.oracle_tool_loop("stage it", "m", [])
    assert reply == "all done"
    assert executed == [["writewiz", "propose", "/tmp/x"]]


def test_oracle_commit_line_asks_twice_and_executes_on_double_yes(
        monkeypatch):
    executed = []
    _fleet(monkeypatch, executed)
    _drive_oracle(monkeypatch, ["TOOL: writewiz commit /tmp/x"])
    answers = iter(["y", "yes, writewiz commit /tmp/x"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    reply, memory = gw.oracle_tool_loop("commit it", "m", [])
    assert reply == "all done"
    assert executed == [["writewiz", "commit", "/tmp/x"]]
    assert "TOOL RESULT" in "\n".join(m.get("content", "") for m in memory)


def test_oracle_commit_line_denied_at_second_ask_executes_nothing(
        monkeypatch):
    executed = []
    _fleet(monkeypatch, executed)
    _drive_oracle(monkeypatch, ["TOOL: writewiz commit /tmp/x"])
    answers = iter(["y", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    reply, memory = gw.oracle_tool_loop("commit it", "m", [])
    assert reply == "all done"
    assert executed == []
    assert "GOVERNOR DENIED" in "\n".join(
        m.get("content", "") for m in memory)


def test_oracle_commit_line_denied_at_first_ask_executes_nothing(
        monkeypatch):
    executed = []
    _fleet(monkeypatch, executed)
    _drive_oracle(monkeypatch, ["TOOL: writewiz commit /tmp/x"])
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    reply, memory = gw.oracle_tool_loop("commit it", "m", [])
    assert reply == "all done"
    assert executed == []
    assert "GOVERNOR DENIED" in "\n".join(
        m.get("content", "") for m in memory)


# ------------------------------------------------------------ call_ollama

def test_call_ollama_skips_absent_ollamawiz(monkeypatch):
    monkeypatch.setattr(gw, "resolve_sibling", lambda name: None)

    def no_sibling(cmd, stdin=None):
        raise AssertionError("ollamawiz call must be skipped")
    monkeypatch.setattr(gw, "call_sibling", no_sibling)
    monkeypatch.setattr(
        gw.subprocess, "run",
        lambda *a, **k: types.SimpleNamespace(
            returncode=1, stdout="", stderr="no daemon"))
    rc, out = gw.call_ollama("hello", model="m")
    assert rc == 1
    assert out == "no daemon"


def test_call_ollama_uses_ollamawiz_when_present(monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(gw, "resolve_sibling", lambda name: Path("/x/ollamawiz"))
    monkeypatch.setattr(gw, "call_sibling",
                        lambda cmd, stdin=None: (0, "the answer"))

    def no_binary(*a, **k):
        raise AssertionError("binary must not run when the sibling answers")
    monkeypatch.setattr(gw.subprocess, "run", no_binary)
    rc, out = gw.call_ollama("hello", model="m")
    assert (rc, out) == (0, "the answer")


# ------------------------------------------------------- law and flavor

def test_father_law_2_names_the_godfather_wizards_own_senses():
    # Pin moved 2026-11-09 (law-text correction pass): LAW 2's meaning
    # is unchanged; its name form is now the proper one.
    assert ("anchor facts with the Godfather Wizard's own senses "
            "before acting" in gw.FATHER_LAW)
    assert "truthwiz" not in gw.FATHER_LAW


def test_no_borrowed_33_in_flavor():
    assert "Citizen #33" not in gf_cli.USAGE
    assert "33 children" not in (gw.__doc__ or "")
