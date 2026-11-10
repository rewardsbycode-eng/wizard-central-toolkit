"""godfather-wizard brain — the Grand Master, fleet dispatcher & REPL.

FATHER LAW:
  He owns no logic. He routes intents to his citizens via shell.
  Every mutation is staged through the Write Wizard consent wall; the
  'y' keystroke belongs to the Governor alone. Routing is a plain,
  deterministic keyword table — anything unmapped is out of scope.
  The REPL exposes all /slashcommands from the fleet; voice is enabled
  on all responses when VOICE_ENABLED=true. The Godfather Wizard
  governs execution and conversation.
"""

import datetime as dt
import difflib
import json
import shutil
import subprocess
import sys
import os
from collections import Counter
from importlib import metadata as importlib_metadata
from pathlib import Path

HOME = Path.home()
BIN = HOME / "bin"
BANK = HOME / ".godfather"
LEDGER = BANK / "ledger.jsonl"
ROUTER_DB = BANK / "routes.json"
STATE_FILE = BANK / "session_state.json"
VOICE_ENABLED = os.environ.get("VOICE_ENABLED", "true").lower() == "true"

FATHER_LAW = """FATHER LAW (Godfather Wizard, the Grand Master)
1. DELEGATION: re-implements nothing; invokes siblings where
   they live: the bin lane (~/bin) first, the installed package
   second; a sibling found nowhere is honestly absent.
2. TRUTH FIRST: multi-step runs anchor facts with the Godfather Wizard's own senses before acting.
3. CONSENT WALL: mutations are staged via write_wizard propose; the
   Godfather Wizard never supplies the 'y'. The commit keystroke
   belongs to the Governor.
4. DETERMINISTIC ROUTES: run dispatches via the keyword table;
   unmapped intents return 'out of scope', never improvised.
5. VERDICTS: plain [OK]/[FAIL]/out of scope, exit 0/1/2, no tracebacks.
6. The Godfather Wizard governs execution + conversation.
7. EVERY DISPATCH IS JOURNALED: all routing events recorded to ledger.
8. REPL MODE exposes all /slashcommands from the fleet under one roof.
9. VOICE ENABLED: when VOICE_ENABLED=true, every REPL response speaks.
10. BANNER ON LAUNCH: every godfather_wizard repl shows the Sovereign mural.
"""

# ------------------------------------------------------------------
# NAME FORMS — one citizen, two spellings (AVS, 2026-11-09). The
# full underscored form (godfather_wizard) is the wizard's
# name-command; the short form (godfatherwiz) is its alias. Both
# invoke the same citizen everywhere: dispatch, stored route banks
# written under either spelling, and the oracle's TOOL lines.
# ------------------------------------------------------------------

def _citizen_key(name):
    """The canonical key for a citizen name in either spelling."""
    if name.endswith("_wizard"):
        return name[: -len("_wizard")] + "wiz"
    return name


def _full_form(key):
    """The full-form command for a citizen key (the short spelling)."""
    if key != "wiz" and key.endswith("wiz"):
        return key[: -len("wiz")] + "_wizard"
    return key


def _short_form(name):
    """The short spelling for a citizen name in either spelling."""
    return _citizen_key(name)


def _ensure_bank():
    BANK.mkdir(parents=True, exist_ok=True)
    if not LEDGER.exists():
        LEDGER.touch()
    if not ROUTER_DB.exists():
        default = {
            "syntax/pycheck": ["python_wizard", "check"],
            "diff/compare": ["diff_wizard", "files"],
            "json/validate": ["json_wizard", "validate"],
            "list/listing/whatshere": ["godfather_wizard", "listing"],
            "models/ollama": ["godfather_wizard", "models"],
            "todos/tasklist": ["todo_wizard", "list"],
            "tmux/sessions": ["tmux_wizard", "list"],
            "symlinks/bins": ["godfather_wizard", "symlinks"],
            "diag/audit": ["debug_wizard", "audit"],
            "heal/repair": ["godfather_wizard", "heal"],
        }
        ROUTER_DB.write_text(json.dumps(default, indent=2))
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"session": 1, "slang": {}}, indent=2))

def load_routes():
    _ensure_bank()
    try:
        return json.loads(ROUTER_DB.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

def save_routes(routes):
    _ensure_bank()
    ROUTER_DB.write_text(json.dumps(routes, indent=2))

def _now():
    return dt.datetime.now().isoformat(timespec="seconds")

def journal(event, target, detail=""):
    _ensure_bank()
    row = {"at": _now(), "event": event, "target": str(target), "detail": detail}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")

def ledger_rows():
    if not LEDGER.exists():
        return []
    rows = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"at": "?", "event": "CORRUPT_ROW", "target": line, "detail": ""})
    return rows

def installed_sibling_names():
    """Wizard names this installation itself provides (entry points).

    A pip-installed copy of the toolkit registers its wizards as entry
    points; those names are the fleet a user of the sampler actually has.
    Returns an empty set when no distribution metadata is present (for
    example when running from a bare source tree).
    """
    dist = None
    for dist_name in ("wizard-central-toolkit", "wiz-central-toolkit"):
        try:
            dist = importlib_metadata.distribution(dist_name)
            break
        except importlib_metadata.PackageNotFoundError:
            continue
    if dist is None:
        return set()
    names = set()
    for ep in dist.entry_points:
        if ep.group in ("console_scripts", "wiz_central_toolkit"):
            names.add(ep.name)
    return names


def resolve_sibling(name):
    """Find a sibling wizard's executable, or None.

    The sovereign fleet's bin lane (~/bin) wins when the citizen is there;
    otherwise the PATH is asked, which is where a package installer puts
    the console scripts. A name that resolves nowhere is honestly absent.
    """
    exe = BIN / name
    if exe.exists():
        return exe
    found = shutil.which(name)
    return Path(found) if found else None


def call_sibling(cmd_list, stdin=None):
    exe = resolve_sibling(cmd_list[0])
    if exe is None:
        return 2, f"[FAIL] sibling not found (bin lane or PATH): {cmd_list[0]}"
    try:
        r = subprocess.run([str(exe)] + cmd_list[1:], input=stdin,
                           capture_output=True, text=True, timeout=180)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (subprocess.TimeoutExpired, OSError) as e:
        return 1, f"[FAIL] sibling call failed: {e}"

def _ollama_roster():
    """Model names a live Ollama daemon serves; [] when none serves."""
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True,
                           text=True, timeout=60)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return []
    if r.returncode != 0:
        return []
    return [ln.split()[0] for ln in r.stdout.strip().splitlines()[1:]
            if ln.strip()]

def resolve_model():
    """Honest model pick: env override if real, else first model from the live roster."""
    wanted = os.environ.get("GODFATHER_MODEL", "").strip()
    names = _ollama_roster()
    if wanted and wanted in names:
        return wanted
    if names:
        return names[0]
    return wanted or "llama3.2:1b"  # last resort; if this is a ghost the oracle will say so

def seated_model():
    """The model a chat turn may consult, or None when no seat serves.

    A seat is real only when a daemon is actually serving it — an
    env var naming an unserved model is a wish, not a seat.
    """
    names = _ollama_roster()
    if not names:
        return None
    wanted = os.environ.get("GODFATHER_MODEL", "").strip()
    return wanted if wanted in names else names[0]

MODEL_TASKS = ("default", "brainstorm", "build", "debug", "diff",
               "audit")
_CODEGEN_TASKS = ("brainstorm", "build", "debug", "diff")

# ------------------------------------------------------------------
# PROVIDERS — the six seats a model can occupy. Ollama is local and
# needs no key. The five cloud providers are the user's opt-in:
# each is seated only with the user's own API key, read from the
# environment at call time. A key is never stored in the bank,
# never journaled, and never printed — displays say only whether
# one is set.
# ------------------------------------------------------------------

PROVIDERS = {
    "ollama": {
        "display": "Ollama", "kind": "local", "host": "127.0.0.1:11434",
        "url": "http://127.0.0.1:11434/api/chat", "key_envs": (),
    },
    "meta": {
        "display": "Meta (Muse)", "kind": "cloud",
        "host": "api.meta.ai",
        "url": "https://api.meta.ai/v1/chat/completions",
        "key_envs": ("MODEL_API_KEY", "META_API_KEY"),
    },
    "anthropic": {
        "display": "Anthropic", "kind": "cloud",
        "host": "api.anthropic.com",
        "url": "https://api.anthropic.com/v1/messages",
        "key_envs": ("ANTHROPIC_API_KEY",),
    },
    "openai": {
        "display": "OpenAI", "kind": "cloud", "host": "api.openai.com",
        "url": "https://api.openai.com/v1/chat/completions",
        "key_envs": ("OPENAI_API_KEY",),
    },
    "google": {
        "display": "Google", "kind": "cloud",
        "host": "generativelanguage.googleapis.com",
        "url": "https://generativelanguage.googleapis.com"
               "/v1beta/openai/chat/completions",
        "key_envs": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    },
    "deepseek": {
        "display": "DeepSeek", "kind": "cloud",
        "host": "api.deepseek.com",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "key_envs": ("DEEPSEEK_API_KEY",),
    },
}
PROVIDER_ORDER = ("ollama", "meta", "anthropic", "openai", "google",
                  "deepseek")


def parse_seat(value):
    """Split a stored seat value into (provider_id, model).

    A bare name is an Ollama model — including tagged names like
    'llama3.2:1b', whose colon belongs to the model, not to a
    provider. Only a head that names one of the six providers
    makes the value provider-qualified.
    """
    text = str(value).strip()
    head, sep, tail = text.partition(":")
    if sep and head.lower() in PROVIDERS:
        return head.lower(), tail
    return "ollama", text


def seat_label(seat):
    """'provider · model' — how a seat is named wherever it speaks."""
    provider_id, model = seat
    return f"{provider_id} · {model}"


def _provider_key(provider_id):
    """(key, env_name) for a cloud provider, read live from the env.

    env_name is the variable that supplied the key, or the
    provider's primary variable when none is set — so an honest
    line can name what is missing without ever touching a value.
    """
    envs = PROVIDERS[provider_id]["key_envs"]
    for env in envs:
        value = os.environ.get(env, "").strip()
        if value:
            return value, env
    return None, (envs[0] if envs else "")


# Ollama model tags (the part after the colon in a bare name) are
# version-shaped: they start with a digit ('7b', '1b') or are one
# of a few plain words. A 'word:rest' value whose tail is not
# tag-shaped reads as a provider attempt, and an unknown provider
# is refused honestly rather than stored as a phantom Ollama name.
_OLLAMA_TAG_WORDS = ("latest", "mini", "small", "medium", "large",
                     "instruct", "chat", "base")


def _seat_value_refusal(value):
    """None when a models.json value may be stored, else the refusal.

    Bare Ollama names always store. A provider:model value stores
    when its provider is one of the six. Anything else that looks
    like a provider attempt is refused, listing the six.
    """
    if ":" not in value:
        return None
    head, tail = value.split(":", 1)
    if head.lower() in PROVIDERS:
        return None
    if any(ch.isdigit() for ch in head) or "." in head:
        return None  # 'llama3.2:1b', 'qwen2.5-coder:7b' — model-shaped
    first = tail.split("-", 1)[0].strip().lower()
    if tail[:1].isdigit() or first in _OLLAMA_TAG_WORDS:
        return None  # 'codellama:7b', 'phi3:mini', 'mistral:latest'
    return (f"[FAIL] unknown provider '{head}' — a seat is a bare "
            f"Ollama model name, or provider:model with provider "
            f"one of: {', '.join(PROVIDER_ORDER)}")


def _models_path():
    """The per-task model store in the godfather bank."""
    return BANK / "models.json"


def load_model_assignments():
    """Task -> model assignments from ~/.godfather/models.json.

    Only the six known task keys and non-empty string values are
    honored; a missing or malformed store is simply no assignments.
    Reading never creates the bank.
    """
    try:
        data = json.loads(_models_path().read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {task: str(data[task]).strip() for task in MODEL_TASKS
            if isinstance(data.get(task), str) and data[task].strip()}


def save_model_assignments(assignments):
    """Persist known task assignments to the godfather bank."""
    _ensure_bank()
    clean = {task: str(assignments[task]).strip()
             for task in MODEL_TASKS
             if isinstance(assignments.get(task), str)
             and assignments[task].strip()}
    _models_path().write_text(json.dumps(clean, indent=2) + "\n",
                              encoding="utf-8")
    return clean


def set_model_assignment(task, model):
    """Assign one task's model. Returns (rc, text)."""
    if task not in MODEL_TASKS:
        return 2, (f"[FAIL] unknown model task: {task} "
                   f"(choose one of: {', '.join(MODEL_TASKS)})")
    model = str(model).strip()
    if not model:
        return 2, "[FAIL] model assignment requires a model name"
    refusal = _seat_value_refusal(model)
    if refusal:
        return 2, refusal
    assignments = load_model_assignments()
    assignments[task] = model
    save_model_assignments(assignments)
    journal("MODEL_SET", task, model)
    return 0, f"[OK] {task} model set to {model}"


def unset_model_assignment(task):
    """Remove one task's model assignment. Returns (rc, text)."""
    if task not in MODEL_TASKS:
        return 2, (f"[FAIL] unknown model task: {task} "
                   f"(choose one of: {', '.join(MODEL_TASKS)})")
    assignments = load_model_assignments()
    old = assignments.pop(task, None)
    save_model_assignments(assignments)
    journal("MODEL_UNSET", task, old or "no assignment was set")
    if old is None:
        return 0, f"[OK] no {task} model assignment was set"
    return 0, f"[OK] {task} model assignment removed ({old})"


def _assigned_model(task, assignments=None):
    """The explicit assignment seat_for would use, before fallback."""
    assignments = load_model_assignments() if assignments is None \
        else assignments
    if task != "default":
        return assignments.get(task) or assignments.get("default")
    return assignments.get("default")


def seat_for(task):
    """The live seat for one task as (provider, model), or None.

    Resolution is assignment first (the task's own entry, then
    the store's default), then the existing live-roster pick. A
    bare assignment is an Ollama model and must be in the live
    roster; a provider:model assignment is a cloud seat and is
    configured when the provider's key is in the environment —
    the first real call is the proof of it, and its errors are
    honest. An explicit assignment that does not serve is NOT
    silently replaced: the seat is absent until that model
    serves (or its key is set).
    """
    if task not in MODEL_TASKS:
        return None
    assigned = _assigned_model(task)
    if assigned:
        provider_id, model = parse_seat(assigned)
        if provider_id == "ollama":
            return ("ollama", model) if model in _ollama_roster() else None
        key, _env = _provider_key(provider_id)
        return (provider_id, model) if key else None
    active = seated_model()
    return ("ollama", active) if active else None


def seat_unavailable_line(task):
    """One plain, factual line explaining why a task has no seat."""
    assigned = _assigned_model(task)
    if assigned:
        provider_id, model = parse_seat(assigned)
        if provider_id != "ollama":
            _key, primary = _provider_key(provider_id)
            return (f"no {task} model seat is serving — seat "
                    f"{provider_id}:{model} assigned but {primary} "
                    f"is not set")
        names = _ollama_roster()
        if names:
            return (f"no {task} model seat is serving — assigned model "
                    f"'{assigned}' is not in the live Ollama roster")
        return (f"no {task} model seat is serving — assigned model "
                f"'{assigned}' is not serving")
    return ("no model seat is configured or serving — "
            f"the {task} feature needs a live model")


def seated_models():
    """The seats answer (/models): providers, roster, assignments."""
    names = _ollama_roster()
    assignments = load_model_assignments()
    lines = []
    any_seat = any(seat_for(task) is not None for task in MODEL_TASKS)
    if not names and not any_seat:
        lines.append("no model seat is configured or serving — "
                     "the fleet runs seatless")
    elif names:
        active = seated_model()
        lines.append("[OK] model seats — Ollama is serving:")
        for n in names:
            lines.append(f"  {n}  <- seated" if n == active else f"  {n}")
    else:
        lines.append("Ollama is not serving — no local roster "
                     "(a configured cloud seat may still serve)")
    lines.append("providers:")
    for provider_id in PROVIDER_ORDER:
        spec = PROVIDERS[provider_id]
        if provider_id == "ollama":
            status = (f"serving — {len(names)} model(s)" if names
                      else "not serving")
        else:
            key, _env = _provider_key(provider_id)
            status = "key set" if key else "key not set"
        lines.append(f"  {spec['display']} ({spec['kind']} — "
                     f"{spec['host']}): {status}")
    lines.append("model assignments (~/.godfather/models.json):")
    for task in MODEL_TASKS:
        assigned = assignments.get(task)
        if assigned:
            provider_id, model = parse_seat(assigned)
            if provider_id == "ollama":
                state = "serving" if model in names else "not serving"
            else:
                key, _env = _provider_key(provider_id)
                state = "key set" if key else "key not set"
            lines.append(f"  {task}: {assigned} ({state})")
        else:
            effective = seat_for(task)
            detail = (f"effective seat: {seat_label(effective)}"
                      if effective else "no effective seat")
            lines.append(f"  {task}: (not set — {detail})")
    lines.append("guide: PROVIDERS.md — where to get each provider's "
                 "key, and how to set up local models with Ollama")
    return 0, "\n".join(lines)

def call_ollama(prompt, model=None):
    """Consult the oracle: ollamawiz first when it exists, Ollama
    binary as honest fallback. When ollamawiz resolves nowhere, the
    doomed sibling call is skipped silently — same destination,
    one less corpse on the road."""
    actual_model = model or resolve_model()
    if resolve_sibling("ollamawiz") is not None:
        rc, out = call_sibling(["ollamawiz", "ask", actual_model, prompt])
        if rc == 0 and out and not out.startswith("[FAIL]"):
            return rc, out
    try:
        r = subprocess.run(["ollama", "run", actual_model, prompt],
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and r.stdout.strip():
            return 0, r.stdout.strip()
        return 1, (r.stderr or "[FAIL] oracle returned nothing").strip()
    except FileNotFoundError:
        return 1, "[FAIL] neither ollamawiz ask nor ollama binary available"
    except subprocess.TimeoutExpired:
        return 1, "[FAIL] oracle timed out"

def speak_if_enabled(text):
    """Speak text if VOICE_ENABLED=true, otherwise silent."""
    if not VOICE_ENABLED:
        return
    rc, out = call_sibling(["voicewiz", "speak", text])  # the whole word, uncut
    # Silent success expected

# ------------------------------------------------------------------
# INTERNAL SENSES — truthwiz's office, absorbed into godfatherwiz
# (R2 ruling: absorb where the purpose lives — Law 2's anchor is
# godfather's own duty, so its senses live here now). Every sense
# is read-only, returns call_sibling's (rc, text) shape, and a
# missing path is a plain [FAIL], exit 1 — never a traceback.
# ------------------------------------------------------------------

_READ_CAP = 20000  # chars a single `read` will show before truncating

def _human_bytes(n):
    if n < 1024:
        return f"{n} bytes"
    if n < 1024 ** 2:
        return f"{n} bytes ({n / 1024:.1f} KB)"
    if n < 1024 ** 3:
        return f"{n} bytes ({n / 1024 ** 2:.1f} MB)"
    return f"{n} bytes ({n / 1024 ** 3:.1f} GB)"

def _sense_target(raw):
    return Path(str(raw)).expanduser()

def _read_text_guarded(p):
    """(text, None) for a readable text file, else (None, fail_line).

    A NUL byte marks the file binary even when its bytes happen to
    decode — control bytes are not text a person can read.
    """
    try:
        data = p.read_bytes()
    except OSError as e:
        return None, f"[FAIL] cannot read {p}: {e.strerror or e}"
    if b"\x00" in data:
        return None, f"[FAIL] not a text file: {p}"
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, f"[FAIL] not a text file: {p}"

def _walk_sizes(root):
    """(total_bytes, file_count) under root, symlinks not followed."""
    total, count = 0, 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            try:
                total += os.lstat(os.path.join(dirpath, name)).st_size
                count += 1
            except OSError:
                continue
    return total, count

def sense_brief(raw_path):
    """Ground truth: what the path is, its size, and its shape."""
    p = _sense_target(raw_path)
    if not p.exists() and not p.is_symlink():
        return 1, f"[FAIL] no such path: {p}"
    lines = [f"[BRIEF] {p}"]
    if p.is_symlink():
        lines.append(f"link: symlink -> {os.readlink(p)}")
    if p.is_dir():
        try:
            entries = sorted(p.iterdir(), key=lambda e: e.name)
        except OSError as e:
            return 1, f"[FAIL] cannot list {p}: {e.strerror or e}"
        dirs = sum(1 for e in entries if e.is_dir() and not e.is_symlink())
        links = sum(1 for e in entries if e.is_symlink())
        files = len(entries) - dirs - links
        total, deep_files = _walk_sizes(p)
        lines.append("type: directory")
        lines.append(f"entries: {len(entries)} "
                     f"({dirs} dirs, {files} files, {links} symlinks)")
        lines.append(f"size: {_human_bytes(total)} across {deep_files} files")
        lines.append("listing:")
        for err in entries[:20]:
            if err.is_symlink():
                lines.append(f"  {err.name} -> {os.readlink(err)}")
            elif err.is_dir():
                lines.append(f"  {err.name}/")
            else:
                lines.append(f"  {err.name}")
        if len(entries) > 20:
            lines.append(f"  ... (+{len(entries) - 20} more)")
        return 0, "\n".join(lines)
    st = p.stat()
    lines.append("type: file")
    lines.append(f"size: {_human_bytes(st.st_size)}")
    text, _err = _read_text_guarded(p)
    if text is not None:
        lines.append(f"lines: {len(text.splitlines())}")
    else:
        lines.append("lines: (binary — not counted)")
    return 0, "\n".join(lines)

def sense_listing(raw_path):
    """The directory's entries, one per line, dirs marked."""
    p = _sense_target(raw_path)
    if not p.exists() and not p.is_symlink():
        return 1, f"[FAIL] no such path: {p}"
    if not p.is_dir():
        return 0, p.name
    try:
        entries = sorted(p.iterdir(), key=lambda e: e.name)
    except OSError as e:
        return 1, f"[FAIL] cannot list {p}: {e.strerror or e}"
    if not entries:
        return 0, "(empty directory)"
    out = []
    for err in entries:
        if err.is_symlink():
            out.append(f"{err.name} -> {os.readlink(err)}")
        elif err.is_dir():
            out.append(f"{err.name}/")
        else:
            out.append(err.name)
    return 0, "\n".join(out)

def sense_read(raw_path):
    """A file's text, capped — truncation is stated, never silent."""
    p = _sense_target(raw_path)
    if not p.exists() and not p.is_symlink():
        return 1, f"[FAIL] no such path: {p}"
    if p.is_dir():
        return 1, f"[FAIL] {p} is a directory — use listing for directories"
    text, err = _read_text_guarded(p)
    if text is None:
        return 1, err
    if len(text) > _READ_CAP:
        return 0, text[:_READ_CAP] + \
            f"\n... [truncated: showing first {_READ_CAP} of {len(text)} chars]"
    return 0, text

def sense_head(raw_path, n=20):
    """The first n lines of a text file."""
    p = _sense_target(raw_path)
    if not p.exists() and not p.is_symlink():
        return 1, f"[FAIL] no such path: {p}"
    if p.is_dir():
        return 1, f"[FAIL] {p} is a directory — use listing for directories"
    text, err = _read_text_guarded(p)
    if text is None:
        return 1, err
    all_lines = text.splitlines()
    shown = all_lines[:n]
    if len(all_lines) > n:
        shown.append(f"... (first {n} of {len(all_lines)} lines)")
    return 0, "\n".join(shown)

def sense_find(root, name_part):
    """Paths under root whose name contains name_part (case-insensitive)."""
    p = _sense_target(root)
    if not p.exists() and not p.is_symlink():
        return 1, f"[FAIL] no such path: {p}"
    needle = str(name_part).lower()
    hits = []
    if p.is_dir():
        for dirpath, dirnames, filenames in os.walk(p):
            for name in dirnames + filenames:
                if needle in name.lower():
                    hits.append(os.path.join(dirpath, name))
    elif needle in p.name.lower():
        hits.append(str(p))
    hits.sort()
    if not hits:
        return 0, f"(no matches for '{name_part}' under {p})"
    if len(hits) > 200:
        return 0, "\n".join(hits[:200]) + \
            f"\n... (+{len(hits) - 200} more matches)"
    return 0, "\n".join(hits)

def sense_du(raw_path):
    """Disk usage, in human terms."""
    p = _sense_target(raw_path)
    if not p.exists() and not p.is_symlink():
        return 1, f"[FAIL] no such path: {p}"
    if p.is_dir():
        total, count = _walk_sizes(p)
        return 0, f"{_human_bytes(total)} across {count} files — {p}"
    return 0, f"{_human_bytes(os.lstat(p).st_size)} — {p}"

def sense_stat(raw_path):
    """Type, size, and modification time."""
    p = _sense_target(raw_path)
    if not p.exists() and not p.is_symlink():
        return 1, f"[FAIL] no such path: {p}"
    st = os.lstat(p)
    if p.is_symlink():
        kind = "symlink"
    elif p.is_dir():
        kind = "directory"
    elif p.is_file():
        kind = "file"
    else:
        kind = "other"
    lines = [f"[STAT] {p}",
             f"type: {kind}",
             f"size: {_human_bytes(st.st_size)}",
             "modified: " + dt.datetime.fromtimestamp(st.st_mtime)
             .isoformat(timespec="seconds")]
    if p.is_symlink():
        lines.append(f"target: {os.readlink(p)}")
    return 0, "\n".join(lines)

def sense_symlinks(raw_path):
    """Symlinks at or under the path, each with its target."""
    p = _sense_target(raw_path)
    if not p.exists() and not p.is_symlink():
        return 1, f"[FAIL] no such path: {p}"
    found = []
    if p.is_symlink():
        found.append(p)
    elif p.is_dir():
        for dirpath, dirnames, filenames in os.walk(p):
            for name in dirnames + filenames:
                e = Path(dirpath) / name
                if e.is_symlink():
                    found.append(e)
    if not found:
        return 0, f"(no symlinks at {p})"
    return 0, "\n".join(f"{e} -> {os.readlink(e)}" for e in sorted(found))

SENSE_VERBS = ("brief", "listing", "read", "head", "find", "du", "stat",
               "symlinks")
_PATH_SENSES = ("brief", "listing", "read", "du", "stat", "symlinks")

def call_sense(verb, args):
    """Dispatch one absorbed sense. args are raw string tokens.

    Path senses default to '.' when no path is given — the anchor's
    home ground, the same default truth_anchor has always used.
    Returns (rc, text), call_sibling's shape.
    """
    args = [str(a) for a in args]
    if verb in _PATH_SENSES:
        raw = args[0] if args else "."
        fn = {"brief": sense_brief, "listing": sense_listing,
              "read": sense_read, "du": sense_du, "stat": sense_stat,
              "symlinks": sense_symlinks}[verb]
        return fn(raw)
    if verb == "head":
        if not args:
            return 2, "[FAIL] head requires a file"
        n = 20
        if len(args) > 1:
            try:
                n = int(args[1])
            except ValueError:
                return 2, "[FAIL] head line count must be a number"
        return sense_head(args[0], n)
    if verb == "find":
        if len(args) < 2:
            return 2, "[FAIL] find requires a root and a name part"
        return sense_find(args[0], args[1])
    return 2, f"out of scope - unknown sense: {verb}"

def call_internal(parts):
    """Serve an in-house capability, or return None.

    parts = ['godfather_wizard', <verb>, <args...>] where <verb> is
    one of the absorbed truth office's senses, or 'models' (the
    seats answer); anything else is not internal and the caller
    falls back to call_sibling. The alias spelling 'godfatherwiz'
    names the same in-house citizen and is served identically.
    """
    if len(parts) >= 2 and parts[0] in ("godfatherwiz", "godfather_wizard"):
        if parts[1] in SENSE_VERBS:
            return call_sense(parts[1], parts[2:])
        if parts[1] == "models":
            return seated_models()
    return None

def truth_anchor(path="."):
    """Law 2: anchor ground truth before multi-step action.

    Served by the absorbed senses — godfatherwiz's own brief, in-house.
    """
    return sense_brief(str(Path(path).expanduser()))

_MUTATION_WORDS = {"write", "fix", "create", "delete", "remove",
                   "modify", "edit", "rm", "heal", "repair"}

# writewiz verbs that change files when executed. propose stages a
# draft — a suggestion, behind no wall; the rest of the read/inspect
# family changes nothing. commit lands the write; discard, rollback
# and purge-old destroy or restore; protect/unprotect rewrite the
# protection record itself.
_WRITEWIZ_WRITE_VERBS = {"commit", "discard", "rollback", "purge-old",
                         "protect", "unprotect"}

def pipeline_is_write_class(pipeline):
    """True when executing this pipeline would change files.

    The wall's true scope (house law): read-only routes run free,
    staging routes are suggestions and run free, and only a route
    that would actually land a change is write-class.
    """
    if not pipeline:
        return False
    head = _short_form(pipeline[0])
    sub = pipeline[1] if len(pipeline) > 1 else ""
    if head == "writewiz":
        return sub in _WRITEWIZ_WRITE_VERBS
    if head == "codeguardwiz" and sub == "fix":
        # fix stages through writewiz by default; only its explicit
        # --write lane lands a change directly.
        return "--write" in pipeline[2:]
    if head == "repairwiz" and sub in ("commit", "apply"):
        return True
    return False

def _path_tokens(directive, keys):
    """Directive tokens that name existing paths ride as arguments."""
    out = []
    for tok in directive.split():
        if tok.lower() in keys:
            continue
        if Path(tok).expanduser().exists():
            out.append(tok)
    return out

def classify_route(directive, args):
    """Resolve a directive. Returns (pipeline, reason, wall).

    - (None, reason, False): no route matches — out of scope.
    - (None, reason, True): unmapped mutation intent — refused at
      the wall, as it always has been.
    - (pipeline, reason, False): a read-class or staging route —
      runs free, whatever words the sentence carried.
    - (pipeline, reason, True): a write-class route — the caller
      asks twice before anything executes.
    Explicit args win; otherwise directive tokens naming existing
    paths ride along as the pipeline's arguments.
    """
    d = directive.lower()
    routes = load_routes()
    for keywords, pipeline in routes.items():
        keys = keywords.split("/")
        if any(k in d for k in keys):
            ride = list(args) if args else _path_tokens(directive, keys)
            full = list(pipeline) + ride
            if pipeline_is_write_class(full):
                return full, f"write-class route: {keywords}", True
            return full, f"matched route: {keywords}", False
    if any(w in d for w in _MUTATION_WORDS):
        return None, "mutation intent detected — route through write_wizard", True
    return None, "no route matches this intent", False

def route_directive(directive, args):
    """Deterministic dispatch. Returns (pipeline, reason) or None."""
    pipeline, reason, wall = classify_route(directive, args)
    if wall:
        return ("WALL", reason)
    return (pipeline, reason)

def fleet_census():
    """Health sweep: the siblings that can actually be invoked.

    Counts the bin lane's executables plus every wizard this
    installation provides (its entry points) that resolves to a real
    executable. One citizen under two spellings (godfatherwiz /
    godfather_wizard) is ONE citizen, listed by its full-form
    command when that spelling invokes, else by the spelling that
    does. One meaning of 'present', shared by fleet, siblings,
    census and status: installed and invocable.
    """
    raw = {w.name for w in BIN.glob("*wiz")}
    raw |= {w.name for w in BIN.glob("*_wizard")}
    raw |= {n for n in installed_sibling_names()
            if (n.endswith("wiz") or n.endswith("_wizard"))
            and resolve_sibling(n) is not None}
    spellings = {}
    for name in raw:
        spellings.setdefault(_citizen_key(name), set()).add(name)
    names = []
    for key in sorted(spellings):
        full = _full_form(key)
        names.append(full if full in spellings[key] else key)
    return len(names), names


def fleet_invocable_names():
    """Every spelling that invokes a citizen — the census names
    plus their alias spellings. The oracle's whitelist and the
    REPL's /wiz matching accept either spelling of a citizen."""
    _count, names = fleet_census()
    out = set(names)
    for n in names:
        out.add(_citizen_key(n))
        out.add(_full_form(_citizen_key(n)))
    return out

def list_all_slash_commands():
    """Return mapping of /slash -> wizard command.

    One key per slash. The values are dispatch pipelines in
    full-form commands (the REPL splits them into argv). /diff
    carries ONE entry — the Diff Wizard's two-file comparison;
    the codegen review sense of /diff is dispatched by argument
    shape in the REPL before this table is consulted, and /help
    names it on its own line.
    """
    # Consolidated fleet-wide slash-command registry
    slash_map = {
        "/truth": "godfather_wizard brief",
        "/ls": "godfather_wizard listing",
        "/read": "godfather_wizard read",
        "/pycheck": "python_wizard check",
        "/fix": "godfather_wizard heal",
        "/heal": "godfather_wizard heal",
        "/todo": "todo_wizard add",
        "/todos": "todo_wizard list",
        "/diff": "diff_wizard files",
        "/models": "godfather_wizard models",
        "/brainstorm": "godfather_wizard brainstorm (model seat; hands off)",
        "/build": "godfather_wizard build (proposal -> diff -> double ask -> write_wizard)",
        "/debug": "godfather_wizard debug (proposal -> diff -> double ask -> write_wizard)",
        "/banner": "banner_wizard",
        "/codeguard": "codeguard_wizard",
        "/json": "json_wizard",
        "/rust": "rust_wizard",
        "/tmux": "tmux_wizard",
        "/write": "write_wizard",
        "/verbs": "read_wizard verbs",
        "/tasks": "todo_wizard list",
        "/audit": "debug_wizard audit",
        "/diag": "debug_wizard classify",
        "/bins": "godfather_wizard symlinks",
        "/history": "godfather_wizard history",
        "/stats": "godfather_wizard stats",
        "/routes": "godfather_wizard routes",
        "/fleet": "godfather_wizard fleet",
        "/law": "godfather_wizard law",
        "/help": "godfather_wizard help",
        "/status": "godfather_wizard status",
        "/census": "godfather_wizard census",
    }
    return slash_map

def session_load():
    _ensure_bank()
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"session": 1}

def session_save(state):
    _ensure_bank()
    STATE_FILE.write_text(json.dumps(state, indent=2))

def schedule_task(intent, delay_secs=0):
    """Queue a task with timestamp."""
    _ensure_bank()
    task_id = hash(f"{intent}{_now()}") % 100000
    task = {"id": task_id, "intent": intent, "scheduled_at": _now(),
            "delay_sec": delay_secs, "status": "queued"}
    tasks = load_routes()
    tasks[f"task_{task_id}"] = task
    save_routes(tasks)
    journal("SCHEDULED", str(task_id), intent)
    return task_id

def queue_tasks():
    """Show scheduled tasks."""
    _ensure_bank()
    tasks = load_routes()
    return [v for k, v in tasks.items() if k.startswith("task_")]

def render_banner():
    """Sovereign mural: figlet + rich 16-color, guaranteed to fit the terminal."""
    import shutil
    try:
        from pyfiglet import Figlet
        from rich.console import Console
        from rich.text import Text
    except ImportError:
        print("=== GODFATHER — GRAND MASTER OF THE SOVEREIGN FLEET ===")
        return

    width = shutil.get_terminal_size((100, 24)).columns
    text = "GODFATHER"
    subtitle = "G R A N D   M A S T E R   O F   T H E   S O V E R E I G N   F L E E T"

    # Width-fit: walk fonts until the art fits with a 2-col margin
    art = None
    for font in ("slant", "smslant", "small", "term", "digital"):
        candidate = Figlet(font=font, width=width).renderText(text).rstrip("\n")
        longest = max((len(ln) for ln in candidate.splitlines()), default=0)
        if longest <= width - 2:
            art = candidate
            break
    if art is None:  # terminal too narrow for any font — plain, clean, honest
        print("=== GODFATHER — GRAND MASTER OF THE SOVEREIGN FLEET ===")
        return

    console = Console(highlight=False)
    console.print(Text(art, style="bright_magenta bold"))
    if len(subtitle) <= width - 2:
        console.print(Text(subtitle, style="bright_yellow"))
    else:
        console.print(Text("GRAND MASTER", style="bright_yellow"))
    _, _census_names = fleet_census()
    console.print(Text(f"{width} cols | Sovereign Fleet: {len(_census_names)} citizens, zero lies",
                       style="bright_cyan"))

# ------------------------------------------------------------------
# ORACLE WITH HANDS — the Governor's tool channel for the cockpit
# ------------------------------------------------------------------

ORACLE_SPINE = """You command the Sovereign Fleet — check AVAILABLE TOOLS below for the live citizen count and capacity.
You act as the central dispatcher and reasoning engine for all interactive wizard queries.
You command the real CLI wizards listed below on this machine. You have NO eyes and NO hands
of your own. Your only way to act or observe is the TOOL channel.

TOOL CHANNEL — to request one real action, reply with a single line, exactly:
TOOL: <command>
where <command> is a real wizard invocation from the AVAILABLE TOOLS list.

Your eyes are godfather_wizard's own senses — brief, listing, read, head,
find, du, stat, symlinks — invoked as pipelines, e.g.
"godfather_wizard listing <path>". They are read-only and always lawful.

LAWS:
- ONE tool call per reply. Then STOP and wait for the true result.
- NEVER invent output, file names, or states you have not been shown.
- NEVER use shell commands (ls, cat, rm, pwd...) — they are forbidden and rejected.
- When you have enough truth, drop the channel and answer plainly.
- If no tool fits, answer plainly and say so.

WORKED EXAMPLE — if the user asks "what files are in ~/wizard_central?",
your ENTIRE reply must be exactly this one line:
TOOL: godfather_wizard listing __HOME__/wizard_central

Then stop. The true result will be given to you, and you summarize it.
"""

import os as _os_home
ORACLE_SPINE = ORACLE_SPINE.replace("__HOME__", _os_home.path.expanduser("~"))

def _oracle_write_consent(tool_line, parts):
    """The double ask (house law) for a write-class TOOL line.

    Staging and read lanes never reach here — pipeline_is_write_class
    has already cleared them to run free. First the plain ask; then a
    typed confirmation naming the pipeline. Anything but the two
    exact answers — including EOF — is a no.
    """
    action = " ".join(parts)
    try:
        first = input(f"\n⚠️  oracle wants to WRITE: {tool_line}\n"
                      "this changes files. proceed? [y/N] ")
    except (KeyboardInterrupt, EOFError):
        return False
    if first.strip().lower() != "y":
        return False
    try:
        typed = input(f"confirm by typing: yes, {action}\n> ")
    except (KeyboardInterrupt, EOFError):
        return False
    return typed.strip() == f"yes, {action}"

def _ollama_chat_api(messages, model):
    """Direct stdlib chat call — no external deps, honest failures."""
    import json as _j
    import urllib.request
    import urllib.error
    payload = _j.dumps({"model": model, "messages": messages,
                        "stream": False}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=payload, headers={"Content-Type": "application/json"})
    import os as _os
    _timeout = int(_os.environ.get("WIZ_OLLAMA_TIMEOUT", "600"))
    with urllib.request.urlopen(req, timeout=_timeout) as r:
        data = _j.loads(r.read().decode())
    return data.get("message", {}).get("content", "")

# ------------------------------------------------------------------
# SEAT CHAT — the one door every model turn walks through. A seat
# is (provider, model): Ollama underneath is the local call above;
# the cloud providers are stdlib-urllib calls to their own APIs
# with the user's own key. Failures raise RuntimeError carrying a
# clean line — status and the provider's own message, trimmed;
# never a traceback, and never the key.
# ------------------------------------------------------------------

def _cloud_timeout():
    try:
        return int(os.environ.get("WIZ_CLOUD_TIMEOUT", "120"))
    except ValueError:
        return 120


def _post_json(url, payload, headers, provider_id):
    """POST one JSON body and return the parsed JSON reply."""
    import urllib.request
    import urllib.error
    display = PROVIDERS[provider_id]["display"]
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_cloud_timeout()) as r:
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            parsed = json.loads(e.read().decode("utf-8", "replace"))
            err = parsed.get("error")
            if isinstance(err, dict):
                detail = str(err.get("message") or "")
            elif isinstance(err, str):
                detail = err
        except Exception:
            detail = ""
        detail = " ".join(detail.split())[:200]
        raise RuntimeError(
            f"{display} seat returned HTTP {e.code}"
            + (f": {detail}" if detail else "")) from None
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(f"{display} seat unreachable ({e})") from None
    try:
        return json.loads(raw)
    except ValueError:
        raise RuntimeError(
            f"{display} seat returned an unreadable response") from None


def _openai_style_chat(provider_id, model, messages):
    """Chat completions in the OpenAI shape (meta/openai/google/deepseek)."""
    spec = PROVIDERS[provider_id]
    key, env = _provider_key(provider_id)
    if not key:
        raise RuntimeError(
            f"{spec['display']} seat is not configured — {env} is not set")
    data = _post_json(
        spec["url"], {"model": model, "messages": messages},
        {"Authorization": f"Bearer {key}",
         "Content-Type": "application/json"}, provider_id)
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        content = None
    if not isinstance(content, str):
        raise RuntimeError(
            f"{spec['display']} seat returned an unexpected "
            "response shape")
    return content


def _anthropic_chat(model, messages):
    """Anthropic messages API: system text travels out-of-band,
    and the reply's content is a list of blocks — text blocks join."""
    spec = PROVIDERS["anthropic"]
    key, env = _provider_key("anthropic")
    if not key:
        raise RuntimeError(
            f"{spec['display']} seat is not configured — {env} is not set")
    system = "\n\n".join(str(m.get("content", "")) for m in messages
                         if m.get("role") == "system")
    convo = [{"role": m.get("role"), "content": m.get("content")}
             for m in messages if m.get("role") != "system"]
    payload = {"model": model, "max_tokens": 4096, "messages": convo}
    if system:
        payload["system"] = system
    data = _post_json(
        spec["url"], payload,
        {"x-api-key": key, "anthropic-version": "2023-06-01",
         "Content-Type": "application/json"}, "anthropic")
    blocks = data.get("content")
    if not isinstance(blocks, list):
        raise RuntimeError(
            "Anthropic seat returned an unexpected response shape")
    return "".join(b.get("text", "") for b in blocks
                   if isinstance(b, dict) and b.get("type") == "text")


def call_seat_chat(seat, messages):
    """One chat turn for a seat (provider, model). Returns the reply
    text; failures raise with a clean, honest line."""
    provider_id, model = seat
    if provider_id == "ollama":
        return _ollama_chat_api(messages, model)
    if provider_id == "anthropic":
        return _anthropic_chat(model, messages)
    if provider_id in PROVIDERS:
        return _openai_style_chat(provider_id, model, messages)
    raise RuntimeError(f"unknown seat provider: {provider_id}")

# ------------------------------------------------------------------
# CODEGEN SUITE — devrepl's modes, rebuilt on the fleet consent wall
# ------------------------------------------------------------------

CODEGEN_SYSTEM_PROMPTS = {
    "brainstorm": (
        "You are the brainstorm seat in godfather_wizard. Converse plainly "
        "and help the person think. You have no tools and no hands in "
        "this mode: do not claim to read, write, run, or change "
        "anything."
    ),
    "build": (
        "You are the build seat in godfather_wizard. Create the complete "
        "content requested for one file. Reply with only the complete "
        "file content, with no explanation and no markdown fence."
    ),
    "debug": (
        "You are the debug seat in godfather_wizard. Repair the file "
        "using the supplied file content and error context. Reply "
        "with only the complete repaired file content, with no "
        "explanation and no markdown fence."
    ),
    "diff": (
        "You are the diff-review seat in godfather_wizard. Propose the "
        "complete revised content for one file so the person can "
        "review a diff. Reply with only the complete file content, "
        "with no explanation and no markdown fence."
    ),
}


def _clean_codegen_reply(reply):
    """Deterministic reply parsing for a complete-content seat.

    Only a fence that surrounds the whole reply is removed. All
    other text — including its final newline — is the seat's exact
    proposed content.
    """
    if not isinstance(reply, str) or not reply.strip():
        return ""
    lines = reply.splitlines(True)
    if len(lines) >= 2 and lines[0].strip().startswith("```") \
            and lines[-1].strip() == "```":
        return "".join(lines[1:-1])
    return reply


def brainstorm_reply(text, memory):
    """One hands-off brainstorm turn. Returns (rc, reply, memory).

    This path deliberately never inspects TOOL: lines and never
    calls the oracle/tool machinery. A seat's words remain words.
    """
    seat = seat_for("brainstorm")
    if seat is None:
        return 1, seat_unavailable_line("brainstorm"), memory
    work = list(memory or [])
    if not work:
        work.append({"role": "system",
                     "content": CODEGEN_SYSTEM_PROMPTS["brainstorm"]})
    work.append({"role": "user", "content": text})
    try:
        reply = call_seat_chat(seat, work)
    except Exception as e:
        return 1, (f"[FAIL] brainstorm seat unreachable "
                   f"({type(e).__name__}: {e})"), memory
    if not isinstance(reply, str) or not reply.strip():
        return 1, "[FAIL] brainstorm seat returned nothing", memory
    reply = reply.strip()
    work.append({"role": "assistant", "content": reply})
    return 0, reply, work


def codegen_current_content(path):
    """(content, error_line) for build/debug/diff's current truth."""
    if not path.exists():
        return "", None
    if not path.is_file():
        return None, f"[FAIL] not a file: {path}"
    return _read_text_guarded(path)


def codegen_proposal(task, path, instruction, current, extra_context=""):
    """Ask one codegen seat for complete content.

    Returns (proposal, error_line). A proposal is inert data —
    path, instruction, exact content, task, and model — until a
    person approves its diff at the writewiz wall.
    """
    if task not in ("build", "debug", "diff"):
        return None, f"[FAIL] unknown codegen task: {task}"
    seat = seat_for(task)
    if seat is None:
        return None, seat_unavailable_line(task)
    user = [f"Path: {path}", f"Instruction: {instruction}"]
    if extra_context:
        user += ["", "Error context:", extra_context]
    user += ["", "Current complete content:",
             current if current else "(the file does not exist yet)"]
    messages = [
        {"role": "system", "content": CODEGEN_SYSTEM_PROMPTS[task]},
        {"role": "user", "content": "\n".join(user)},
    ]
    try:
        reply = call_seat_chat(seat, messages)
    except Exception as e:
        return None, (f"[FAIL] {task} seat unreachable "
                      f"({type(e).__name__}: {e})")
    content = _clean_codegen_reply(reply)
    if not content:
        return None, f"[FAIL] {task} seat returned no usable content"
    return {
        "task": task,
        "path": str(path),
        "instruction": instruction,
        "content": content,
        "model": seat[1],
        "seat": seat,
    }, None


def render_codegen_diff(path, current, proposed):
    """A unified diff for display. Colour never enters staged data."""
    diff = difflib.unified_diff(
        current.splitlines(True), proposed.splitlines(True),
        fromfile=f"{path} (current)",
        tofile=f"{path} (model proposal)")
    lines = list(diff)
    if not lines:
        return "(no changes — the proposal matches the current file)"
    use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    if not use_color:
        return "".join(lines).rstrip("\n")
    colored = []
    for line in lines:
        stripped = line.rstrip("\n")
        if stripped.startswith("+") and not stripped.startswith("+++"):
            colored.append(f"\033[32m{stripped}\033[0m")
        elif stripped.startswith("-") and not stripped.startswith("---"):
            colored.append(f"\033[31m{stripped}\033[0m")
        elif stripped.startswith("@@"):
            colored.append(f"\033[36m{stripped}\033[0m")
        else:
            colored.append(stripped)
    return "\n".join(colored)


def confirm_codegen_write(target):
    """Codegen's double ask: plain yes, then name the file in type."""
    try:
        first = input(
            f"⚠️  write the model's proposal to {target}? [y/N] ")
    except (KeyboardInterrupt, EOFError):
        return False
    if first.strip().lower() != "y":
        return False
    try:
        typed = input(f"confirm by typing: yes, write {target}\n> ")
    except (KeyboardInterrupt, EOFError):
        return False
    return typed.strip() == f"yes, write {target}"


def stage_codegen_content(target, content):
    """Stage exact content through writewiz. Returns (ok, detail)."""
    try:
        from wiz_central_toolkit.writewiz.write_wizard import \
            propose as _propose
        draft, _meta, t = _propose(str(target), content)
        return True, f"{draft.name} -> {t} ({len(content)} chars quarantined)"
    except ImportError:
        pass
    except OSError as e:
        return False, f"write_wizard propose failed: {e}"
    rc, out = call_sibling(["write_wizard", "propose", str(target)],
                           stdin=content)
    if rc != 0:
        return False, out or "write_wizard propose failed"
    return True, out


def land_codegen_content(target):
    """Land a staged draft through writewiz commit. Returns (ok, detail).

    The person's live double ask has just named this file; that is
    the consent commit records. Writewiz still runs its own gate,
    backup, journal, and post-write verification inside the wall.
    """
    try:
        from wiz_central_toolkit.writewiz import write_wizard as _ww
    except ImportError:
        return False, ("write_wizard not importable — the staged proposal "
                       f"waits in quarantine; land it with: "
                       f"write_wizard commit {target}")
    draft, meta = _ww._draft_path(Path(target))
    if not draft.exists():
        return False, "no staged draft found in write_wizard's quarantine"
    ok, msg, _t = _ww.commit(
        draft, meta, confirm_reader=lambda prompt="": "y")
    return ok, msg


def build_tool_manifest():
    """Real fleet roster from disk — no fabricated commands."""
    _, names = fleet_census()
    # names only — probe hints bloated the context; the oracle doesn't need them
    return ", ".join(names)

def oracle_tool_loop(question, model, memory, max_rounds=5):
    """Chat with hands: tool calls execute REAL wizards, results feed back in.
    Returns (final_reply, memory). Memory is this session's conversation.
    `model` is a seat (provider, model); a bare name still works and
    means that Ollama model."""
    import os as _os
    if _os.environ.get("WIZ_AI_PROVIDER", "").strip().lower() == "none":
        return ("[FAIL] AI disabled (WIZ_AI_PROVIDER=none)", memory)
    seat = model if isinstance(model, tuple) else ("ollama", model)
    if not memory:
        memory.append({"role": "system",
                       "content": ORACLE_SPINE + "\nAVAILABLE TOOLS:\n" + build_tool_manifest()})
    memory.append({"role": "user", "content": question})

    for round_i in range(max_rounds):
        try:
            reply = call_seat_chat(seat, memory)
        except Exception as e:
            return (f"[FAIL] oracle unreachable ({type(e).__name__}: {e})", memory)
        memory.append({"role": "assistant", "content": reply})

        tool_line = None
        for line in reply.splitlines():
            if line.strip().upper().startswith("TOOL:"):
                tool_line = line.strip()[5:].strip()
                break
        if not tool_line:
            return reply, memory  # a plain answer — done

        parts = [word.replace("~", __import__("os").path.expanduser("~"))
                 if word.startswith("~") else word
                 for word in tool_line.split()]
        if not parts:
            continue

        # consent wall, at its true scope: staging and read lanes
        # run free and never prompt; a write-class lane asks twice
        # (the same test godfatherwiz run lives by).
        if pipeline_is_write_class(parts):
            if not _oracle_write_consent(tool_line, parts):
                memory.append({"role": "user", "content":
                               "GOVERNOR DENIED this action. Proceed without it."})
                continue

        print(f"🔧 {tool_line}")

        # INTERNAL FIRST — godfatherwiz's own in-house hands (the
        # senses, the seats answer) execute in-process. They are
        # always lawful: the fleet census must never be able to
        # reject godfatherwiz himself.
        internal = call_internal(parts)

        # FLEET WHITELIST — only real citizens may act. No shell reach-arounds.
        # Common shell verbs are TRANSLATED to their lawful fleet equivalents.
        SHELL_TRANSLATIONS = {
            "ls": ["godfather_wizard", "listing"],
            "dir": ["godfather_wizard", "listing"],
            "cat": ["godfather_wizard", "read"],
            "head": ["godfather_wizard", "head"],
            "pwd": ["godfather_wizard", "brief"],
            "find": ["godfather_wizard", "find"],
            "du": ["godfather_wizard", "du"],
            "stat": ["godfather_wizard", "stat"],
            "grep": ["godfather_wizard", "read"],
        }
        if internal is None:
            fleet_names = fleet_invocable_names()
            if parts[0] not in fleet_names:
                if parts[0] in SHELL_TRANSLATIONS:
                    new_parts = SHELL_TRANSLATIONS[parts[0]] + parts[1:]
                    print(f"[TRANSLATE] '{parts[0]}' → '{' '.join(new_parts[:2])}' (lawful fleet equivalent)")
                    parts = new_parts
                    internal = call_internal(parts)
                else:
                    memory.append({"role": "user", "content":
                        f"REJECTED: '{parts[0]}' is NOT a fleet tool. Shell commands are "
                        f"forbidden. Your ONLY way to see files is exactly this line:\n"
                        f"TOOL: godfather_wizard listing <path>\n"
                        f"Emit that line now with the real path, or answer plainly."})
                    print(f"[REJECT] '{parts[0]}' is not a citizen — bouncing back")
                    continue
            if parts[0] not in fleet_names:
                memory.append({"role": "user", "content":
                    f"REJECTED: '{parts[0]}' is not a fleet tool. Answer plainly instead."})
                print(f"[REJECT] '{parts[0]}' is not a citizen — bouncing back")
                continue

        # DUPLICATE SHIELD — same command twice = answer from what we already have
        sig = " ".join(parts)
        if not hasattr(oracle_tool_loop, "_last_calls"):
            oracle_tool_loop._last_calls = set()
        if sig in oracle_tool_loop._last_calls:
            oracle_tool_loop._dup_count = getattr(oracle_tool_loop, "_dup_count", 0) + 1
            if oracle_tool_loop._dup_count >= 2:
                # small brains can't pivot — present the truth ourselves, honestly
                last_result = getattr(oracle_tool_loop, "_last_result", "(none)")
                print("[FORCED SUMMARY] oracle won't stop repeating — presenting raw truth")
                return ("[RAW TRUTH — oracle could not summarize, presented verbatim]\n"
                        + last_result, memory)
            memory.append({"role": "user", "content":
                f"DUPLICATE: you already ran '{sig}'. STOP calling tools. Your next "
                f"reply must be a PLAIN ANSWER with no TOOL: line. Summarize the "
                f"result you already received. Nothing else."})
            print("[DEDUP] identical tool call suppressed — final warning issued")
            continue
        oracle_tool_loop._last_calls.add(sig)

        if internal is not None:
            rc, out = internal
        else:
            rc, out = call_sibling(parts)
        result = (out or "").strip() or "(no output)"
        oracle_tool_loop._last_result = result

        # CONTEXT DIET — small seats have 4096-token windows; feed a digest,
        # not the raw firehose. Tell the oracle it was truncated.
        MAX_RESULT_LINES = 60
        lines = result.splitlines()
        truncated_note = ""
        if len(lines) > MAX_RESULT_LINES:
            result = "\n".join(lines[:MAX_RESULT_LINES])
            truncated_note = ("\n(result truncated to first "
                              f"{MAX_RESULT_LINES} of {len(lines)} lines)")

        memory.append({"role": "user", "content":
                       f"TOOL RESULT ({tool_line}, exit {rc}):\n{result}"
                       + truncated_note})

    return ("[FAIL] oracle exhausted tool rounds without a plain answer "
            "(run /model to pick a stronger seat)", memory)
