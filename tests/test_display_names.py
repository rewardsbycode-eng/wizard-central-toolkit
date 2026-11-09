"""Display-name gate (AVS ruling, 2026-11-09 — the pre-publish pass).

House line 1, enforced: everywhere a user SEES A NAME, the
wizard is spelled in full — "Wizard", never "wiz". Everywhere
a user TYPES A COMMAND, nothing changes. This gate asserts:

(a) each in-box wizard's help output names it in full;
(b) the README roster carries all 41 display names;
(c) no COMMANDS.md section heading leads with a bare command
    name (headings lead with the display name; the typed
    command follows in backticks).
"""

import importlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README_MD = ROOT / "README.md"
COMMANDS_MD = ROOT / "COMMANDS.md"

# command -> display name, for the 12 wizards in the box
# (`wiz` is the router command; it has no wizard name).
DISPLAY_NAMES = {
    "godfatherwiz": "Godfather Wizard",
    "bannerwiz": "Banner Wizard",
    "codeguardwiz": "Code Guard Wizard",
    "debugwiz": "Debug Wizard",
    "diffwiz": "Diff Wizard",
    "jsonwiz": "JSON Wizard",
    "pythonwiz": "Python Wizard",
    "readwiz": "Read Wizard",
    "rustwiz": "Rust Wizard",
    "tmuxwiz": "Tmux Wizard",
    "todowiz": "Todo Wizard",
    "writewiz": "Write Wizard",
}

ENTRY_POINTS = ("wiz",) + tuple(DISPLAY_NAMES)

# short command (package) -> full-form name-command (AVS ruling,
# 2026-11-09: the full underscored form is the wizard's name;
# the short form is its alias).
FULL_FORM = {short: short[: -len("wiz")] + "_wizard"
             for short in DISPLAY_NAMES}
ENTRY_POINTS_ALL = ENTRY_POINTS + tuple(FULL_FORM.values())

# All 41 roster display names, in roster order.
ROSTER_NAMES = [
    "Banner Wizard", "Bash Wizard", "Bootstrap Wizard",
    "Calendar Wizard", "Code Guard Wizard", "Command Line Wizard",
    "Daemon Wizard", "Debug Wizard", "Diff Wizard", "Doc Wizard",
    "Dotfile Wizard", "Exam Wizard", "Git Wizard", "Grant Wizard",
    "Help Wizard", "JSON Wizard", "Knowledge Wizard",
    "Manual Wizard", "Mapping Wizard", "MCP Wizard",
    "Mode-Manifesting Wizard", "Modelfile Wizard", "Ollama Wizard",
    "Privacy Wizard", "Python Wizard", "Read Wizard",
    "Repair Wizard", "REPL Manager Wizard", "Requirements Wizard",
    "SQL Wizard", "Supreme Wizard", "Test-Admission Wizard",
    "Todo Wizard", "Truthdwiz Wizard", "Truth Wizard",
    "Voice Wizard", "Whiteboard Wizard", "Write Wizard",
    "Godfather Wizard", "Bonus Wizard", "Keep Wizard",
]


def _run_help(wizard, capsys):
    module = importlib.import_module(
        f"wiz_central_toolkit.{wizard}.__main__")
    try:
        module.main(["--help"])
    except SystemExit as e:
        assert e.code in (0, None), f"{wizard} --help exited {e.code}"
    return capsys.readouterr().out


@pytest.mark.parametrize("wizard", sorted(DISPLAY_NAMES))
def test_help_names_the_wizard_in_full(wizard, capsys):
    out = _run_help(wizard, capsys)
    assert DISPLAY_NAMES[wizard] in out, (
        f"{wizard} help never names it in full "
        f"({DISPLAY_NAMES[wizard]!r})")


def test_readme_roster_carries_all_41_display_names():
    text = README_MD.read_text(encoding="utf-8")
    missing = [name for name in ROSTER_NAMES if name not in text]
    assert not missing, f"README roster omits display names: {missing}"


def test_commands_md_headings_lead_with_display_names():
    offenders = []
    for line in COMMANDS_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            heading = line[3:]
            for cmd in ENTRY_POINTS_ALL:
                if heading == cmd or heading.startswith(cmd + " ") \
                        or heading.startswith(cmd + "—") \
                        or heading.startswith(cmd + " —"):
                    offenders.append(line)
    assert not offenders, (
        f"COMMANDS.md headings leading with a bare command: {offenders}")


# ------------------------------------------- full-form name-command

@pytest.mark.parametrize("wizard", sorted(DISPLAY_NAMES))
def test_help_usage_leads_with_full_form_and_notes_alias(wizard, capsys):
    out = _run_help(wizard, capsys)
    full = FULL_FORM[wizard]
    assert f"usage: {full}" in out, (
        f"{wizard} help does not lead its usage with {full}")
    assert f"alias: {wizard}" in out, (
        f"{wizard} help does not note its alias")


def test_codeguard_help_leads_with_its_name(capsys):
    out = _run_help("codeguardwiz", capsys)
    assert out.splitlines()[0] == "Code Guard Wizard — code audit wizard"


def test_router_help_names_the_wizarding_router(capsys):
    from wiz_central_toolkit.wiz import __main__ as wiz_main
    rc = wiz_main.main(["--help"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.splitlines()[0].startswith("The Wizarding Router")


def test_readme_carries_one_aliases_list():
    text = README_MD.read_text(encoding="utf-8")
    assert "## Names and aliases" in text
    section = text.split("## Names and aliases", 1)[1]
    for short, display in DISPLAY_NAMES.items():
        assert display in section, display
        assert f"`{FULL_FORM[short]}`" in section, FULL_FORM[short]
        assert f"`{short}`" in section, short
