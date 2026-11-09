"""godfather-wizard face — the Grand Master, fleet dispatcher & REPL."""

import json
import re
import sys
import readline

from collections import Counter
from pathlib import Path
from .godfather_wizard import (
    FATHER_LAW, call_sibling, call_internal, call_ollama, speak_if_enabled,
    truth_anchor, classify_route, seated_model, seated_models, seat_for,
    seat_label, seat_unavailable_line, set_model_assignment,
    unset_model_assignment,
    brainstorm_reply, codegen_current_content, codegen_proposal,
    render_codegen_diff, confirm_codegen_write, stage_codegen_content,
    land_codegen_content, fleet_census, resolve_sibling, load_routes,
    save_routes, journal, ledger_rows, _now, schedule_task,
    queue_tasks, render_banner, list_all_slash_commands,
    fleet_invocable_names,
    session_load, session_save)

USAGE = """Godfather Wizard — the Grand Master, fleet dispatcher & REPL
alias: godfatherwiz
usage: godfather_wizard <command> [args]

CLI Commands:
  godfather_wizard audit <path>       truth anchor + codeguard_wizard audit
  godfather_wizard task <intent>      todo_wizard intake
  godfather_wizard run <directive>    deterministic keyword router
  godfather_wizard routes             print routing table
  godfather_wizard fleet              bin-lane census
  godfather_wizard law                print FATHER LAW
  godfather_wizard truth <path>       anchor ground truth (internal senses)
  godfather_wizard diagnose <dir>     debug_wizard audit + classify
  godfather_wizard heal <file>        debug_wizard propose → write_wizard wall
  godfather_wizard status             fleet-wide health check
  godfather_wizard repl               launch interactive REPL cockpit
  godfather_wizard siblings           list all registered citizens
  godfather_wizard verify <wizard>    single citizen health check
  godfather_wizard consent <file>     force write_wizard commit prompt
  godfather_wizard schedule <intent>  queue task
  godfather_wizard queue              show scheduled tasks
  godfather_wizard history            run history across delegations
  godfather_wizard stats              fleet-wide execution counts
  godfather_wizard versions           law drift detection
  godfather_wizard help [command]     full usage, or one subcommand's usage
  godfather_wizard census             full fleet roster
  godfather_wizard models             show providers, live seats + assignments
  godfather_wizard models set <task> <model>
                                  assign a seat to default, brainstorm,
                                  build, debug, diff, or audit — a bare
                                  Ollama model name, or provider:model
                                  (ollama, meta, anthropic, openai,
                                  google, deepseek)
  godfather_wizard models unset <task>
                                  remove a per-task model assignment

exit codes: 0 ok | 1 failed | 2 out of scope"""

CMDS = ("audit", "task", "run", "routes", "fleet", "law", "truth", "diagnose",
        "heal", "status", "repl", "siblings", "verify", "consent", "schedule",
        "queue", "history", "stats", "versions", "help", "census", "models")

def _fail(msg):
    print(f"[FAIL] {msg}")
    return 1

def _confirm_write_class(pipeline):
    """The double ask (house law) for a write-class route.

    First the plain ask; then a typed confirmation naming the
    action being agreed to. Anything but the two exact answers —
    including EOF — is a no, and nothing executes.
    """
    action = " ".join(pipeline)
    try:
        first = input(f"⚠️  write-class route: {action}\n"
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

def main():
    try:
        return _dispatch()
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return 1

def _dispatch():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    if not args:
        # bare invocation = the throne room: banner, voice, chat, slash commands
        return run_repl()
    if args[0] not in CMDS:
        print(USAGE)
        return 2
    
    cmd = args[0]
    
    # === CORE DISPATCHERS ===
    if cmd == "law":
        print(FATHER_LAW)
        return 0
    
    if cmd == "versions":
        import hashlib
        print("father_law_sha256:", hashlib.sha256(FATHER_LAW.encode()).hexdigest())
        return 0
    
    if cmd == "census":
        count, names = fleet_census()
        print(f"[OK] {count} certified citizens on the fleet")
        for i, n in enumerate(names, 1):
            print(f"  #{i:02d}  {n}")
        return 0

    if cmd == "models":
        if len(args) == 1:
            rc, out = seated_models()
            print(out)
            return rc
        if args[1] == "set" and len(args) == 4:
            rc, out = set_model_assignment(args[2], args[3])
            print(out)
            return rc
        if args[1] == "unset" and len(args) == 3:
            rc, out = unset_model_assignment(args[2])
            print(out)
            return rc
        print(USAGE)
        return 2

    if cmd == "help":
        if len(args) < 2:
            print(USAGE)
            return 0
        target = args[1]
        for line in USAGE.splitlines():
            if target in line:
                print(line.strip())
        return 0
    
    if cmd == "routes":
        routes = load_routes()
        # The bank also holds scheduled-task records (task_* keys,
        # dict values) — those are the queue's business, not routes.
        # The routing table shows actual routes only.
        shown = {k: v for k, v in routes.items()
                 if not k.startswith("task_") and isinstance(v, list)}
        if not shown:
            print("(routing table empty)")
            return 0
        for k, v in shown.items():
            print(f"  {k:25s} -> {' '.join(v)}")
        return 0
    
    if cmd == "fleet":
        count, names = fleet_census()
        print(f"[OK] {count} sibling wizards installed")
        for n in names:
            print(f"  {n}")
        return 0
    
    if cmd == "siblings":
        count, names = fleet_census()
        for i, n in enumerate(names, 1):
            print(f"[{i:2d}] {n}")
        return 0
    
    if cmd == "history":
        rows = ledger_rows()
        if not rows:
            print("(ledger empty — no dispatches yet)")
            return 0
        for row in rows:
            print(f"{row['at']}  {row['event']:16s} {row['target']} {row['detail']}")
        return 0
    
    if cmd == "stats":
        counts = Counter(r["event"] for r in ledger_rows())
        print(dict(counts) if counts else "(no events recorded)")
        return 0

    if cmd == "status":
        # Probe the fleet that is actually installed — the same census
        # fleet/siblings report. Absent citizens are not probed at all.
        _count, installed = fleet_census()
        if not installed:
            print("[FAIL] no sibling wizards installed")
            return 1
        worst = 0
        for w in installed:
            if resolve_sibling(w) is None:
                print(f"[FAIL] {w} unresponsive")
                worst = 1
                continue
            rc, out = call_sibling([w, "--help"])
            # exit 2 = usage fallthrough on --help, NOT death. Death = rc 1.
            alive = rc in (0, 2)
            print(f"[{'OK' if alive else 'FAIL'}] {w} {'reachable' if alive else 'unresponsive'}")
            if not alive:
                worst = 1
        return worst

    if cmd == "repl":
        return run_repl()
    
    # === PIPELINERS ===
    if cmd == "audit":
        if len(args) < 2:
            return _fail("audit requires a path")
        rc_overall = 0
        print("--- PHASE 1: truth anchor ---")
        rc, out = truth_anchor(args[1])
        print(out or "(no output)")
        if rc != 0:
            rc_overall = 1
        print("--- PHASE 2: codeguard_wizard audit ---")
        rc, out = call_sibling(["codeguard_wizard", "audit", args[1]])
        print(out or "(no output)")
        if rc != 0:
            rc_overall = 1
        print(f"[{'OK' if rc_overall == 0 else 'FAIL'}] audit pipeline complete")
        return rc_overall
    
    if cmd == "task":
        if len(args) < 2:
            return _fail("task requires an intent")
        intent = " ".join(args[1:])
        # todowiz alone carries the task now — there is no second
        # phase, and the output must not claim one ran.
        print("--- todo_wizard intake ---")
        rc, out = call_sibling(["todo_wizard", "add", intent])
        print(out or "(no output)")
        if rc != 0:
            print("[FAIL] task pipeline complete")
            return 1
        print("[OK] task pipeline complete")
        return 0
    
    if cmd == "run":
        if len(args) < 2:
            return _fail("run requires a directive")
        directive = " ".join(args[1:])
        rc, anchor = truth_anchor(".")
        print(f"--- truth anchor (law 2) ---")
        print(anchor or "(no output)")
        
        pipeline, reason, wall = classify_route(directive, [])
        if pipeline is None and wall:
            # Unmapped mutation intent — refused at the wall, as
            # it always has been; the lawful road is writewiz.
            print(f"[CONSENT WALL] {reason}")
            print("to mutate: echo 'content' | write_wizard propose <path>")
            print("then answer the wall yourself: write_wizard commit <path>")
            journal("WALL_ROUTED", directive, "mutation detected")
            return 0
        if pipeline is None:
            print("out of scope — no route matches this directive")
            print("run 'godfather_wizard routes' to see the lawful table")
            journal("ROUTED", directive, "out of scope")
            return 2
        if wall:
            # A write-class route: there is no MCP gate in this
            # project, so the double ask is the load-bearing wall.
            print(f"[CONSENT WALL] {reason}")
            if not _confirm_write_class(pipeline):
                print("[FAIL] consent withheld — nothing executed")
                journal("WALL_ROUTED", directive, "consent withheld")
                return 0
            journal("WALL_ROUTED", directive, "consent given — executing")

        journal("ROUTED", directive, reason)
        print(f"[ROUTE] {reason}")
        print(f"--- executing: {' '.join(pipeline)} ---")
        internal = call_internal(pipeline)
        if internal is not None:
            rc, out = internal
        else:
            rc, out = call_sibling(pipeline)
        print(out or "(no output)")
        if rc == 0:
            print("[OK] pipeline complete")
        else:
            print(f"[FAIL] pipeline ended with exit {rc}")
        return rc
    
    if cmd == "truth":
        if len(args) < 2:
            return _fail("truth requires a path")
        rc, out = truth_anchor(args[1])
        print(out or "(no output)")
        return rc
    
    if cmd == "diagnose":
        if len(args) < 2:
            return _fail("diagnose requires a directory")
        print("--- PHASE 1: debug_wizard audit ---")
        rc, out = call_sibling(["debug_wizard", "audit", args[1]])
        print(out or "(no output)")
        rc_overall = 1 if rc != 0 else 0
        # Phase 2: classify the worst error file the census can name.
        # debugwiz has no 'triage' — hotspot ranks the error files and
        # classify breaks the worst one down.
        rc, out = call_sibling(["debug_wizard", "hotspot", args[1]])
        worst_file = None
        for line in out.splitlines():
            m = re.match(r"\[HOT\] \d+ errors\s+(.+)$", line.strip())
            if m:
                worst_file = m.group(1).strip()
                break
        if worst_file is None:
            print("--- PHASE 2: no error files — nothing to classify ---")
            return rc_overall
        print(f"--- PHASE 2: debug_wizard classify {worst_file} ---")
        rc, out = call_sibling(["debug_wizard", "classify", worst_file])
        print(out or "(no output)")
        if rc == 2:  # usage error — the chain itself misfired
            rc_overall = 1
        return rc_overall
    
    if cmd == "heal":
        if len(args) < 2:
            return _fail("heal requires a file path")
        target = Path(args[1]).expanduser()
        audit_root = target if target.is_dir() else target.parent
        print("--- PHASE 1: debug_wizard audit ---")
        rc, out = call_sibling(["debug_wizard", "audit", str(audit_root)])
        print(out or "(no output)")
        if rc == 0:
            print("[OK] nothing sick — nothing to heal")
            return 0
        if rc != 1:
            # Not the "sickness found" verdict — the chain itself broke
            # (usage error or a sibling that would not answer).
            return 1
        # Name the patient: the file asked for, if it is among the
        # sick — otherwise the worst file the hotspot census names.
        rc, out = call_sibling(["debug_wizard", "hotspot", str(audit_root)])
        sick = []
        for line in out.splitlines():
            m = re.match(r"\[HOT\] \d+ errors\s+(.+)$", line.strip())
            if m:
                sick.append(m.group(1).strip())
        if target.is_file():
            patient = None
            for f in sick:
                try:
                    if Path(f).resolve() == target.resolve():
                        patient = target
                        break
                except OSError:
                    continue
            if patient is None:
                print(f"[OK] {target} shows no errors — nothing to heal in it")
                return 0
        elif sick:
            patient = Path(sick[0])
        else:
            return _fail("audit reported sickness but no file could be named")
        print(f"--- PHASE 2: debug_wizard propose {patient} ---")
        rc, out = call_sibling(["debug_wizard", "propose", str(patient)])
        print(out or "(no output)")
        if rc != 0:
            return 1
        fix_target = Path.home() / ".debug-wizard" / f"fix_{patient.stem}.txt"
        print(f"handoff: write_wizard commit {fix_target}   # your keystroke, Governor")
        return 0
    
    if cmd == "verify":
        if len(args) < 2:
            return _fail("verify requires a wizard name")
        name = args[1]
        if resolve_sibling(name) is None:
            # Not installed is out of scope (Law 5: exit 2) — a different
            # fact from installed-but-unresponsive, and reported as such.
            print(f"[FAIL] {name} not installed")
            return 2
        rc, out = call_sibling([name, "--help"])
        # exit 2 = usage fallthrough on --help, NOT death. Death = rc 1.
        alive = rc in (0, 2)
        print(f"[{'OK' if alive else 'FAIL'}] {name} {'healthy' if alive else 'unresponsive'}")
        return 0 if alive else 1
    
    if cmd == "consent":
        if len(args) < 2:
            return _fail("consent requires a file path")
        print(f"write_wizard commit {args[1]}   # your keystroke, Governor")
        return 0
    
    if cmd == "schedule":
        if len(args) < 2:
            return _fail("schedule requires an intent")
        intent = " ".join(args[1:])
        task_id = schedule_task(intent)
        print(f"[OK] task scheduled: id={task_id}, intent={intent}")
        return 0

    if cmd == "queue":
        tasks = queue_tasks()
        if not tasks:
            print("(queue empty)")
            return 0
        for t in tasks:
            print(f"[{t['status']}] {t['id']} — {t['intent']}")
        return 0

    print("out of scope")
    return 2

# ============================================================================
# INTERACTIVE REPL MODE — THE COCKPIT
# ============================================================================

def _load_cfg():
    import json
    from pathlib import Path as _P
    cfgf = _P.home() / ".godfather" / "config.json"
    try:
        return json.loads(cfgf.read_text())
    except Exception:
        return {}

def _save_cfg(cfg):
    import json
    from pathlib import Path as _P
    cfgf = _P.home() / ".godfather" / "config.json"
    cfgf.parent.mkdir(parents=True, exist_ok=True)
    cfgf.write_text(json.dumps(cfg, indent=2))

def _pick_model():
    """Numbered model dropdown — picks from the LIVE Ollama roster, persists choice."""
    import os
    import subprocess
    print("\n💾 MODEL SELECTOR (live Ollama roster)")
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=60)
        names = [ln.split()[0] for ln in r.stdout.strip().splitlines()[1:] if ln.strip()]
    except (OSError, subprocess.SubprocessError):
        names = []
    if not names:
        print("[FAIL] no models found — is Ollama running?")
        return
    for i, n in enumerate(names, 1):
        print(f"  [{i}] {n}")
    try:
        idx_pick = int(input("👑 model # ").strip()) - 1
        if 0 <= idx_pick < len(names):
            chosen = names[idx_pick]
            os.environ["GODFATHER_MODEL"] = chosen
            cfg = _load_cfg()
            cfg["model"] = chosen
            _save_cfg(cfg)
            print(f"[OK] oracle set to {chosen} (persisted in ~/.godfather/config.json)")
        else:
            print("[FAIL] invalid selection")
    except ValueError:
        print("[FAIL] enter a number")
    except (KeyboardInterrupt, EOFError):
        print("\n[OK] model selection cancelled — Sovereignty preserved.")

def _pick_voice():
    """Universal voice picker — direct disk discovery, no device assumptions.
    Scans every plausible Piper root on THIS machine + env overrides.
    Pairing law: a voice is real only with its .onnx.json config beside it."""
    import os
    from pathlib import Path as _P
    print("\n🎙️  VOICE SELECTOR (universal disk discovery)")

    home = _P.home()
    roots = []
    for var in ("VOICE_ROOT", "PAPER_VOICE_ROOT", "PIPER_VOICE_PATH"):
        val = os.environ.get(var)
        if val:
            roots.append(_P(val))
    roots.extend([
        home / "piper" / "voices",
        home / ".local" / "share" / "piper" / "voices",
        home / "piper-voices",
        _P("/usr/share/piper/voices"),
        _P("/usr/local/share/piper/voices"),
        home / ".config" / "piper" / "voices",
    ])

    found = {}  # name -> root it lives in
    for root in roots:
        if not root.is_dir():
            continue
        for onnx in root.glob("*.onnx"):
            if (root / (onnx.name + ".json")).exists() or onnx.with_suffix(".onnx.json").exists():
                found.setdefault(onnx.stem, root)

    if not found:
        print("[FAIL] no paired Piper voices found on this machine")
        print("roots scanned:")
        for r in roots:
            print(f"    {r}  {'(exists)' if r.is_dir() else ''}")
        print("hint: export VOICE_ROOT=<your voices dir> and retry")
        return

    # active voice: first .active found in any root
    active = ""
    for r in roots:
        af = r / ".active"
        if af.is_file():
            active = af.read_text().strip()
            break

    names = sorted(found)
    print(f"found {len(names)} voice(s):")
    for i, v in enumerate(names, 1):
        mark = "  <-- active" if v == active else ""
        print(f"  [{i:2d}] {v}{mark}")

    try:
        pick = input("👑 voice # ").strip()
        idx = int(pick) - 1
    except ValueError:
        print("[FAIL] enter a number")
        return
    except (KeyboardInterrupt, EOFError):
        print("\n[OK] voice selection cancelled — Sovereignty preserved.")
        return
    if not (0 <= idx < len(names)):
        print(f"[FAIL] pick 1-{len(names)}")
        return

    chosen = names[idx]
    root = found[chosen]
    (root / ".active").write_text(chosen)
    cfg = _load_cfg()
    cfg["voice"] = chosen
    cfg["voice_root"] = str(root)
    _save_cfg(cfg)
    # offer immediate ear test
    try:
        rc, out = call_sibling(["voicewiz", "speak", "voice set to " + chosen])
        if rc != 0:
            print(f"[OK] voice set to {chosen} (no ear test — voicewiz speak unavailable)")
        else:
            print(f"[OK] voice set to {chosen} — did you hear it?")
    except Exception:
        print(f"[OK] voice set to {chosen}")

def _classify_repl_input(user_input):
    """Return the action and arguments for one REPL line."""
    text = user_input.strip()

    if not text:
        return ("empty", [])

    if text in ("/quit", "/exit"):
        return ("quit", [])

    if text == "/help":
        return ("help", [])

    if text == "/voices":
        return ("voices", [])

    if text == "/model":
        return ("model", [])

    if text == "/more-commands":
        return ("more-commands", [])

    if text.startswith("/wiz"):
        tokens = text.split()
        return ("wiz", tokens[1:])

    if text.startswith("/"):
        parts = text.split()
        return ("slash", parts)

    return ("chat", [text])

def _codegen_path_key(path):
    return str(Path(path).expanduser().resolve())


def _prepare_codegen(task, target_token, instruction, last_proposal,
                     effective_instruction=None):
    """Current truth + a proposal for one codegen command.

    Returns (proposal, current, reused, error_line). A reviewed
    /diff proposal is reused only for the same path and instruction
    and only while the file still matches the reviewed base.
    """
    target = Path(target_token).expanduser()
    current, error = codegen_current_content(target)
    if error:
        return None, None, False, error
    if task == "debug" and not target.is_file():
        return None, None, False, f"[FAIL] debug requires a file: {target}"
    if last_proposal \
            and _codegen_path_key(last_proposal.get("path", "")) \
            == _codegen_path_key(target) \
            and last_proposal.get("instruction") == instruction \
            and last_proposal.get("base_content") == current:
        proposal = dict(last_proposal)
        proposal["task"] = task
        return proposal, current, True, None
    extra = ""
    if task == "debug":
        notes = instruction or "no user notes"
        if target.suffix == ".py":
            rc, out = call_sibling(["python_wizard", "check", str(target)])
            extra = (f"User notes: {notes}\n"
                     f"python_wizard check exit {rc}:\n{out or '(no output)'}")
        else:
            extra = f"User notes: {notes}"
    proposal, error = codegen_proposal(
        task, target, effective_instruction or instruction, current,
        extra_context=extra)
    if error:
        return None, current, False, error
    proposal["instruction"] = instruction
    return proposal, current, False, None


def _review_codegen_diff(target, proposal, current):
    if target.exists():
        print(f"[NOTE] {target} exists — this is a full-content revision")
    seat = proposal.get("seat")
    byline = (f"seat: {seat_label(seat)}" if seat
              else proposal["model"])
    print(f"--- {proposal['task']} proposal by {byline} "
          f"for {target} ---")
    print(render_codegen_diff(target, current, proposal["content"]))


def _diff_codegen(args, last_proposal):
    if len(args) < 3:
        print("[FAIL] /diff requires a path and an instruction")
        return last_proposal
    target = Path(args[1]).expanduser()
    instruction = " ".join(args[2:])
    proposal, current, reused, error = _prepare_codegen(
        "diff", args[1], instruction, last_proposal)
    if error:
        print(error)
        return last_proposal
    if reused:
        print("the proposal you reviewed — no new seat call")
    _review_codegen_diff(target, proposal, current)
    proposal["base_content"] = current
    return proposal


def _write_codegen(task, args, last_proposal):
    if task == "build" and len(args) < 3:
        print("[FAIL] /build requires a path and an instruction")
        return
    if task == "debug" and len(args) < 2:
        print("[FAIL] /debug requires a file path")
        return
    target = Path(args[1]).expanduser()
    instruction = " ".join(args[2:])
    effective = instruction or "Repair the errors in this file."
    proposal, current, reused, error = _prepare_codegen(
        task, args[1], instruction, last_proposal,
        effective_instruction=effective)
    if error:
        print(error)
        return
    if reused:
        print("the proposal you reviewed — no new seat call")
    _review_codegen_diff(target, proposal, current)
    if proposal["content"] == current:
        print("[OK] no changes — nothing staged, nothing written")
        return
    ok, detail = stage_codegen_content(target, proposal["content"])
    if not ok:
        print(f"[FAIL] proposal could not stage via write_wizard: {detail}")
        return
    print(f"[STAGED] {task} proposal for {target} — {detail}")
    if not confirm_codegen_write(target):
        print("[CONSENT WALL] consent withheld — nothing written; "
              "the staged proposal stays in write_wizard's quarantine")
        return
    ok, detail = land_codegen_content(target)
    if not ok:
        print(f"[FAIL] write_wizard commit refused: {detail}")
        return
    journal("CODEGEN", target,
            f"task={task} model={proposal['model']} "
            f"instruction={effective}")
    print(f"[OK] {task} proposal written to {target} through write_wizard")


def run_repl():
    """Launch interactive REPL with banner, voice, ollama chat, slash-commands."""
    import os
    render_banner()
    slash_map = list_all_slash_commands()
    session = session_load()
    session["session"] = session.get("session", 0) + 1
    session_save(session)
    cfg = _load_cfg()
    if cfg.get("model"):
        os.environ["GODFATHER_MODEL"] = cfg["model"]  # restore persisted choice
    print(f"\n👁️  SESSION {session['session']} — Sovereign Fleet Cockpit\n")
    print("Type /help for slash commands, /quit to exit.\n")
    chat_memory = []
    brainstorm_mode = False
    brainstorm_memory = []
    brainstorm_tool_noted = False
    last_proposal = None

    while True:
        try:
            raw_input = input("👑 godfather> ")
            action, args = _classify_repl_input(raw_input)
        except (EOFError, KeyboardInterrupt):
            print("\n[OK] Godfather bows out. Sovereignty preserved.")
            break

        if not raw_input:
            continue

        if raw_input in ("/quit", "/exit"):
            print("[OK] Godfather bows out. Sovereignty preserved.")
            break

        if brainstorm_mode and raw_input.startswith("/") \
                and raw_input.split()[0] != "/brainstorm":
            # Any other slash leaves brainstorm mode.
            brainstorm_mode = False
            brainstorm_memory = []
            brainstorm_tool_noted = False

        if raw_input.split()[0:1] == ["/brainstorm"]:
            parts = raw_input.split()
            if parts == ["/brainstorm", "end"]:
                brainstorm_mode = False
                brainstorm_memory = []
                brainstorm_tool_noted = False
                print("[OK] brainstorm mode ended — hands remain off")
                continue
            if not brainstorm_mode:
                brainstorm_mode = True
                brainstorm_memory = []
                brainstorm_tool_noted = False
                print("[OK] brainstorm mode — hands off: the seat can "
                      "talk only; no tools run and no files change. "
                      "Use /brainstorm end to leave.")
            if len(parts) > 1:
                text = raw_input[len("/brainstorm"):].strip()
                rc, reply, brainstorm_memory = brainstorm_reply(
                    text, brainstorm_memory)
                print(f"\n👑 godfather: {reply}\n" if rc == 0 else reply)
                if rc == 0:
                    if any(line.strip().upper().startswith("TOOL:")
                           for line in reply.splitlines()) \
                            and not brainstorm_tool_noted:
                        print("[NOTE] brainstorm is hands-off: a TOOL: "
                              "line was treated as text; nothing executed.")
                        brainstorm_tool_noted = True
                    speak_if_enabled(reply)
            continue

        if raw_input.split()[0:1] == ["/build"]:
            _write_codegen("build", raw_input.split(), last_proposal)
            continue

        if raw_input.split()[0:1] == ["/debug"]:
            _write_codegen("debug", raw_input.split(), last_proposal)
            continue

        if raw_input.split()[0:1] == ["/diff"]:
            # /diff already names diffwiz's two-file comparison. The
            # codegen form is /diff <path> <instruction...>. Longer
            # forms are unambiguously codegen; a three-token form is
            # codegen when its last token is not a second file.
            parts = raw_input.split()
            if len(parts) > 3 or (len(parts) == 3 and not Path(
                    parts[2]).expanduser().is_file()):
                last_proposal = _diff_codegen(parts, last_proposal)
                continue

        if raw_input == "/help":
            print("📜 AVAILABLE SLASH COMMANDS:")
            for cmd, desc in slash_map.items():
                print(f"  {cmd:15s} → {desc}")
            print("  /diff <file> <instruction>  → godfather_wizard diff review"
                  " (proposal form; the two-file form above compares two files)")
            print("  /voices         → pick voice (numbered dropdown)")
            print("  /model          → pick model (numbered dropdown)")
            print("  /more-commands  → full fleet arsenal (all citizens)")
            continue

        if raw_input == "/voices":
            _pick_voice()
            continue

        if raw_input == "/model":
            _pick_model()
            continue

        if raw_input == "/more-commands":
            count, names = fleet_census()
            print(f"\n📚 FLEET ARSENAL — {count} citizens")
            print("=" * 60)
            for w in names:
                rc, out = call_sibling([w, "--help"])
                lines = out.splitlines()
                print(f"\n{w.upper()} ({'★' if rc == 0 else '✗'}):")
                for line in lines[:10]:
                    print(f"    {line}")
                if len(lines) > 10:
                    print(f"    ... ({len(lines) - 10} more, run '{w} --help')")
            print("\n" + "=" * 60)
            continue

        if raw_input.startswith("/"):
            cmd = raw_input.split()[0]
            if cmd in slash_map:
                # ARG LAW: keep the full pipeline (cmd + subcommand),
                # and split user args into proper argv tokens. Passing the
                # whole arg string as ONE element made citizens receive
                # 'FLEET-STATE.md' as an unknown subcommand.
                pipeline = slash_map[cmd].split()
                args = raw_input[len(cmd):].strip().split()
                internal = call_internal(pipeline + args)
                if internal is not None:
                    rc, out = internal
                else:
                    rc, out = call_sibling(pipeline + args)
                print(out or "(no output)")
            elif cmd == "/wiz" and len(raw_input.split()) > 1:
                # UNIVERSAL DELEGATION: /wiz <citizen> [args...]
                # Resolves against the installed fleet — a citizen that
                # does not exist on disk cannot be invoked. Zero fabrication.
                parts = raw_input.split()
                target = parts[1]
                wiz_args = parts[2:]
                real = resolve_sibling(target)
                if real is None:
                    candidates = [n for n in fleet_invocable_names()
                                  if n.startswith(target)]
                    if not candidates:
                        print(f"out of scope — no citizen named '{target}' installed")
                        continue
                    if len(candidates) == 1:
                        real = resolve_sibling(candidates[0])
                    else:
                        print(f"[FAIL] ambiguous citizen '{target}': {candidates}")
                        continue
                print(f"[ROUTE] universal delegation -> {real.name} {' '.join(wiz_args)}".rstrip())
                rc, out = call_sibling([real.name] + wiz_args)
                print(out or "(no output)")
            else:
                print(f"[FAIL] unknown slash command: {cmd}")
                print("run /help to see available commands, or /wiz <citizen> [args]")
            continue

        if brainstorm_mode:
            rc, reply, brainstorm_memory = brainstorm_reply(
                raw_input, brainstorm_memory)
            print(f"\n👑 godfather: {reply}\n" if rc == 0 else reply)
            if rc == 0:
                if any(line.strip().upper().startswith("TOOL:")
                       for line in reply.splitlines()) \
                        and not brainstorm_tool_noted:
                    print("[NOTE] brainstorm is hands-off: a TOOL: "
                          "line was treated as text; nothing executed.")
                    brainstorm_tool_noted = True
                speak_if_enabled(reply)
            continue

        # Plain text: the deterministic router answers FIRST (R4).
        # Only unmapped text reaches the oracle, and only when a
        # model seat is actually serving — seatless unmapped text
        # is plainly out of scope, never an oracle error.
        pipeline, reason, wall = classify_route(raw_input, [])
        if pipeline is None and wall:
            print(f"[CONSENT WALL] {reason}")
            print("to mutate: echo 'content' | write_wizard propose <path>")
            print("then answer the wall yourself: write_wizard commit <path>")
            journal("WALL_ROUTED", raw_input, "mutation detected")
            continue
        if pipeline is not None:
            if wall and not _confirm_write_class(pipeline):
                print("[FAIL] consent withheld — nothing executed")
                journal("WALL_ROUTED", raw_input, "consent withheld")
                continue
            if wall:
                journal("WALL_ROUTED", raw_input, "consent given — executing")
            journal("ROUTED", raw_input, reason)
            print(f"[ROUTE] {reason}")
            internal = call_internal(pipeline)
            if internal is not None:
                rc, out = internal
            else:
                rc, out = call_sibling(pipeline)
            print(out or "(no output)")
            continue

        seat = seat_for("default")
        if seat is None:
            print("out of scope — no route matches this text, "
                  "and no model seat is serving")
            continue
        # Unmapped text + a live seat → chat WITH HANDS: the oracle
        # may request real tools; it only ever suggests.
        print(f"🤖 consulting oracle (seat: {seat_label(seat)})...",
              flush=True)
        from .godfather_wizard import oracle_tool_loop
        reply, chat_memory = oracle_tool_loop(raw_input, seat, chat_memory)
        print(f"\n👑 godfather: {reply}\n")
        speak_if_enabled(reply)  # the whole word, uncut

if __name__ == "__main__":
    sys.exit(main())
