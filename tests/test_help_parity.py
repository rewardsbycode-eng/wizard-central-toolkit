"""Help parity gate (AVS direction, 2026-11-09; full-form names
per AVS's ruling later that day).

Every wizard's help shows that wizard's commands, individually,
in both forms: `<wizard> help` and `<wizard> --help` both exit 0
and print the wizard's full command listing. A wizard's
name-command is its full underscored form (godfather_wizard);
the short form (godfatherwiz) is its alias and must answer
byte-identically — dual activation, proven here against the
installed console scripts.

The expected command names are read from COMMANDS.md — the
document, independent of the help output itself — so if a
wizard's help ever drops a documented command, or a form
regresses to an error, this suite goes red. Running the suite
requires the venv bin on PATH (the alias proof shells out to
the installed entry points).
"""

import importlib
import re
import subprocess
from pathlib import Path

import pytest

from wiz_central_toolkit.tools_registry import ALIAS_OF, CITIZENS

FULL_FORMS = tuple(sorted(CITIZENS))
ENTRY_POINTS = ("wiz",) + FULL_FORMS

# Full-form command -> the package that implements it (package
# directory names are the short forms; they are not commands).
PACKAGE = {full: full[: -len("_wizard")] + "wiz" for full in FULL_FORMS}

COMMANDS_MD = Path(__file__).resolve().parent.parent / "COMMANDS.md"
PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _documented_names():
    """Wizard name -> command names, parsed from COMMANDS.md.

    Section headings lead with the wizard's display name and
    carry the typed command in backticks (e.g. "## Godfather
    Wizard — `godfather_wizard`, ..."); the wizard is the first
    backticked entry point in the heading, falling back to the
    heading's first word. Table sections contribute the first
    word of each row's backticked first cell; the `wiz` and
    `banner_wizard` sections (prose, no table) contribute the
    first word of every backticked token they contain.
    """
    text = COMMANDS_MD.read_text(encoding="utf-8")
    names = {}
    for section in re.split(r"^## ", text, flags=re.M)[1:]:
        heading = section.splitlines()[0] if section.splitlines() else ""
        wizard = None
        for token in re.findall(r"`([^`]+)`", heading):
            if token.split()[0] in ENTRY_POINTS:
                wizard = token.split()[0]
                break
        if wizard is None:
            wizard = heading.split(" ", 1)[0].strip()
        if wizard not in ENTRY_POINTS:
            continue
        found = []
        for line in section.splitlines():
            m = re.match(r"\| `([^`]+)`", line)
            if m:
                found.append(m.group(1).split()[0])
        if not found:
            for token in re.findall(r"`([^`]+)`", section):
                found.append(token.split()[0])
        names[wizard] = found
    return names


DOCUMENTED = _documented_names()


def _run_help(wizard, form, capsys):
    """Invoke the wizard's entry main with one help-form argument.

    Returns (exit_code, stdout). Argparse-based faces raise
    SystemExit(0) on --help; that is an exit 0, not a failure.
    """
    if wizard == "wiz":
        module = importlib.import_module(
            "wiz_central_toolkit.wiz.__main__")
    else:
        module = importlib.import_module(
            f"wiz_central_toolkit.{PACKAGE[wizard]}.__main__")
    try:
        rc = module.main([form])
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 0
    out = capsys.readouterr().out
    return (0 if rc is None else rc), out


@pytest.mark.parametrize("wizard", ENTRY_POINTS)
def test_both_help_forms_exit_zero_and_agree(wizard, capsys):
    rc_bare, out_bare = _run_help(wizard, "help", capsys)
    rc_flag, out_flag = _run_help(wizard, "--help", capsys)
    assert rc_bare == 0, f"{wizard} help exited {rc_bare}"
    assert rc_flag == 0, f"{wizard} --help exited {rc_flag}"
    assert out_bare.strip(), f"{wizard} help printed nothing"
    assert out_bare == out_flag, (
        f"{wizard}: `help` and `--help` print different listings")


@pytest.mark.parametrize("wizard", ENTRY_POINTS)
def test_help_lists_every_documented_command(wizard, capsys):
    expected = DOCUMENTED[wizard]
    assert expected, f"no commands parsed from COMMANDS.md for {wizard}"
    for form in ("help", "--help"):
        rc, out = _run_help(wizard, form, capsys)
        assert rc == 0
        missing = [name for name in expected if name not in out]
        assert not missing, (
            f"{wizard} {form} omits documented commands: {missing}")


def test_pyproject_registers_both_name_forms():
    text = PYPROJECT.read_text(encoding="utf-8")
    for full in FULL_FORMS:
        assert re.search(rf"^{re.escape(full)} = ", text, re.M), full
    for alias in ALIAS_OF:
        assert re.search(rf"^{re.escape(alias)} = ", text, re.M), alias


@pytest.mark.parametrize("full", FULL_FORMS)
def test_alias_script_answers_identically(full):
    """Dual activation at the installed surface: the short alias
    and the full-form command print byte-identical help, rc 0,
    in both help forms."""
    alias = [a for a, f in ALIAS_OF.items() if f == full][0]
    outs = {}
    for exe in (full, alias):
        for form in ("help", "--help"):
            r = subprocess.run([exe, form], capture_output=True,
                               text=True, timeout=60)
            assert r.returncode == 0, (exe, form, r.returncode,
                                       r.stderr[:200])
            outs[(exe, form)] = r.stdout
    assert outs[(full, "help")] == outs[(full, "--help")]
    assert outs[(alias, "help")] == outs[(full, "help")]
    assert outs[(alias, "--help")] == outs[(full, "help")]
