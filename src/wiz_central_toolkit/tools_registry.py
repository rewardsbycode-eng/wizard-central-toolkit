"""Shared tool registry — both `wiz` and `godfatherwiz` dispatch through this.
Add a new tool by adding one line here; nothing else needs to know about it.

Name law (AVS, 2026-11-09): a wizard's name-command is its full
underscored form (`godfather_wizard`); the short form (`godfatherwiz`)
is an alias — installed, working, and listed as an alias, never the
name. CITIZENS is keyed by the full form; TOOLS resolves both
spellings to the same main.
"""
import importlib

CITIZENS = {
    "banner_wizard": "wiz_central_toolkit.bannerwiz.__main__",
    "codeguard_wizard": "wiz_central_toolkit.codeguardwiz.__main__",
    "debug_wizard": "wiz_central_toolkit.debugwiz.__main__",
    "godfather_wizard": "wiz_central_toolkit.godfatherwiz.__main__",
    "diff_wizard": "wiz_central_toolkit.diffwiz.__main__",
    "json_wizard": "wiz_central_toolkit.jsonwiz.__main__",
    "python_wizard": "wiz_central_toolkit.pythonwiz.__main__",
    "read_wizard": "wiz_central_toolkit.readwiz.__main__",
    "rust_wizard": "wiz_central_toolkit.rustwiz.__main__",
    "tmux_wizard": "wiz_central_toolkit.tmuxwiz.__main__",
    "todo_wizard": "wiz_central_toolkit.todowiz.__main__",
    "write_wizard": "wiz_central_toolkit.writewiz.__main__",
}

ALIAS_OF = {
    "bannerwiz": "banner_wizard",
    "codeguardwiz": "codeguard_wizard",
    "debugwiz": "debug_wizard",
    "godfatherwiz": "godfather_wizard",
    "diffwiz": "diff_wizard",
    "jsonwiz": "json_wizard",
    "pythonwiz": "python_wizard",
    "readwiz": "read_wizard",
    "rustwiz": "rust_wizard",
    "tmuxwiz": "tmux_wizard",
    "todowiz": "todo_wizard",
    "writewiz": "write_wizard",
}


def full_form(name: str):
    """The wizard's name-command for either spelling, else None."""
    if name in CITIZENS:
        return name
    return ALIAS_OF.get(name)


# Both spellings resolve — dual activation, one main per citizen.
TOOLS = dict(CITIZENS)
TOOLS.update({alias: CITIZENS[full] for alias, full in ALIAS_OF.items()})


def get_tool_main(name: str):
    """Import a tool's main() lazily by name (either spelling).
    Returns None if unknown."""
    module_path = TOOLS.get(name)
    if module_path is None:
        return None
    module = importlib.import_module(module_path)
    return module.main
