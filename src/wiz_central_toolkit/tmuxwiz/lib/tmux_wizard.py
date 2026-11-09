import sys
"""tmux_wizard - sovereign tmux session manager (stdlib only)."""
import subprocess

SUBCOMMANDS = ("new", "attach", "kill", "list", "census", "rename",
               "capture", "detach", "law", "version")

LAW_TEXT = """TMUX LAW (Tmux Wizard, the session keeper)
1. The Tmux Wizard manages sessions; the truth about them comes
   from tmux itself, never from memory or invention.
2. tmux is always called with an argument list, never through
   a shell.
3. capture reads a pane; it changes nothing.
4. detach frees the client; the session and its work keep
   running.
5. kill is the only destroyer, and it names its session.
"""


def package_version():
    try:
        from importlib import metadata
        for _n in ("wizard-central-toolkit", "wiz-central-toolkit"):
            try:
                return metadata.version(_n)
            except metadata.PackageNotFoundError:
                continue
    except Exception:
        pass
    try:
        from wiz_central_toolkit import __version__
        return __version__
    except Exception:
        return "unknown"


def _run(args):
    """Run tmux with an arg list. Never shell=True (injection law)."""
    try:
        proc = subprocess.run(
            ["tmux"] + args, capture_output=True, text=True, timeout=10
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "tmux not installed"
    except subprocess.TimeoutExpired:
        return 124, "", "tmux timed out"


def _sessions():
    """Live session names. Ground truth from tmux itself, zero fabrication."""
    rc, out, _ = _run(["ls", "-F", "#{session_name}"])
    if rc != 0:
        return []
    return [line for line in out.splitlines() if line]


def cmd_new(name, start_dir):
    if not name or "/" in name or ":" in name:
        print("[FAIL] invalid session name")
        return 1
    if name in _sessions():
        print("[FAIL] session '%s' already exists" % name)
        return 1
    rc, _, err = _run(["new-session", "-d", "-s", name, "-c", start_dir])
    if rc == 0:
        print("[OK] session '%s' created" % name)
    else:
        print("[FAIL] %s" % err)
    return rc


def cmd_attach(name):
    if name not in _sessions():
        print("[FAIL] no session '%s'" % name)
        return 1
    rc, _, err = _run(["attach-session", "-t", name])
    if rc == 0:
        print("[OK] attached to '%s'" % name)
    else:
        print("[FAIL] attach to '%s' failed%s" % (name, (": " + err) if err else ""))
    return rc


def cmd_kill(name):
    if name not in _sessions():
        print("[FAIL] no session '%s'" % name)
        return 1
    rc, _, _ = _run(["kill-session", "-t", name])
    print("[OK] session '%s' killed" % name if rc == 0 else "[FAIL] kill failed")
    return rc


def cmd_list():
    sessions = _sessions()
    if not sessions:
        print("no sessions running")
        return 0
    for s in sessions:
        print(s)
    return 0


def cmd_census():
    """Fleet-style census: every session, window count, attach state."""
    sessions = _sessions()
    total = len(sessions)
    print("sessions total: %d" % total)
    ok = 0
    for s in sessions:
        rc, out, _ = _run(
            ["list-windows", "-t", s, "-F", "#{window_index}:#{window_name}"]
        )
        windows = out.splitlines() if rc == 0 else []
        rc2, out2, _ = _run(["display-message", "-p", "-t", s, "#{session_attached}"])
        attached = "ATTACHED" if out2 == "1" else "detached"
        print("%s %-20s windows=%2d %s" % ("[OK]" if rc == 0 else "[FAIL]", s, len(windows), attached))
        if rc == 0:
            ok += 1
    print("census verdict: %d/%d healthy" % (ok, total))
    return 0 if ok == total else 1


def cmd_capture(name, lines=200):
    if name not in _sessions():
        print("[FAIL] no session '%s'" % name)
        return 1
    rc, out, err = _run(["capture-pane", "-t", name, "-p", "-S", "-%d" % lines])
    if rc == 0:
        print(out)
    else:
        print("[FAIL] capture from '%s' failed%s" % (name, (": " + err) if err else ""))
    return rc


def cmd_detach(name):
    if name not in _sessions():
        print("[FAIL] no session '%s'" % name)
        return 1
    rc, _, err = _run(["detach-client", "-s", name])
    if rc == 0:
        print("[OK] clients detached from '%s' (session keeps running)" % name)
    else:
        print("[FAIL] detach from '%s' failed%s" % (name, (": " + err) if err else ""))
    return rc


def cmd_rename(old, new):
    if old not in _sessions():
        print("[FAIL] no session '%s'" % old)
        return 1
    if not new or "/" in new or ":" in new:
        print("[FAIL] invalid new name")
        return 1
    rc, _, err = _run(["rename-session", "-t", old, new])
    print("[OK] '%s' -> '%s'" % (old, new) if rc == 0 else "[FAIL] %s" % err)
    return rc


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print("Tmux Wizard — sovereign tmux session manager")
        print("alias: tmuxwiz")
        print("usage: tmux_wizard <new|attach|kill|list|census|rename|capture|detach|law|version> [args]")
        print("  new <name> [dir]    create session (default cwd)")
        print("  attach <name>       join session")
        print("  kill <name>         destroy session")
        print("  list                names of live sessions")
        print("  census              health of every session")
        print("  rename <old> <new>  rename session")
        print("  capture <name> [lines]  print a pane's recent output (read-only)")
        print("  detach <name>       detach clients; the session keeps running")
        print("  law                 print the TMUX LAW alone")
        print("  version             print the version")
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "law":
        print(LAW_TEXT)
        return 0
    if cmd == "version":
        print("tmux_wizard %s" % package_version())
        return 0
    if cmd not in SUBCOMMANDS:
        print("out of scope - unknown command: %s" % cmd)
        return 2
    if cmd == "new":
        if not rest:
            print("[FAIL] new requires a session name")
            return 2
        return cmd_new(rest[0], rest[1] if len(rest) > 1 else ".")
    if cmd == "attach":
        if not rest:
            print("[FAIL] attach requires a name")
            return 2
        return cmd_attach(rest[0])
    if cmd == "kill":
        if not rest:
            print("[FAIL] kill requires a name")
            return 2
        return cmd_kill(rest[0])
    if cmd == "rename":
        if len(rest) < 2:
            print("[FAIL] rename requires old and new names")
            return 2
        return cmd_rename(rest[0], rest[1])
    if cmd == "capture":
        if not rest:
            print("[FAIL] capture requires a session name")
            return 2
        lines = 200
        if len(rest) > 1:
            try:
                lines = int(rest[1])
            except ValueError:
                print("[FAIL] capture lines must be a number")
                return 2
        return cmd_capture(rest[0], lines)
    if cmd == "detach":
        if not rest:
            print("[FAIL] detach requires a name")
            return 2
        return cmd_detach(rest[0])
    if cmd == "list":
        return cmd_list()
    return cmd_census()


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))