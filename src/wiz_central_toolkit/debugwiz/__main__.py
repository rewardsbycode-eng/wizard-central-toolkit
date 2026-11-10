"""debugwiz — the diagnosis oracle. Ported from wizard_central's debug-wizard (with the locate-dispatch fix applied)."""
import sys
from pathlib import Path

from .debug_wizard import (
    DEBUG_LAW,
    add_ignore,
    audit_dir,
    classify_file,
    count_dir,
    hotspot,
    imports,
    load_ignored,
    locate,
    names,
    report_json,
    signatures,
    stack_digest,
    stats_fleet,
    suggest_fix,
    timeline,
    trace,
)

USAGE = """Debug Wizard — the diagnosis oracle
alias: debugwiz
usage: debug_wizard law                     print the DEBUG LAW alone
       debug_wizard trace <file>            traceback autopsy
       debug_wizard locate <dir> <pattern>  find files with error pattern
       debug_wizard classify <file>         error type breakdown
       debug_wizard stack [file]            stack digest of a traceback (file or stdin)
       debug_wizard count <dir>             errors by category
       debug_wizard hotspot <dir>           files with most errors
       debug_wizard timeline <dir>          error frequency by mtime
       debug_wizard imports <file>          missing import detection
       debug_wizard names <file>            undefined name detection
       debug_wizard signatures <file>       signature mismatch detection
       debug_wizard suggest <file>          heuristic fix suggestion
       debug_wizard propose <file>          stage fix via write_wizard
       debug_wizard preview <file>          show staged proposal
       debug_wizard explain <file>          human-readable explanation
       debug_wizard audit <dir>             full error census
       debug_wizard report <dir>            JSON report for CI/CD
       debug_wizard log <dir>               write error log (staged via write_wizard)
       debug_wizard ignore <path>           add to ignore list
       debug_wizard ignored                 show ignored paths
       debug_wizard stats                   error census of the current directory
       debug_wizard versions                law/version drift detection
exit codes: 0 ok | 1 failed | 2 out of scope"""

CMDS = ("law", "trace", "locate", "classify", "stack", "count", "hotspot",
        "timeline", "imports", "names", "signatures", "suggest", "propose",
        "preview", "explain", "audit", "report", "log", "ignore", "ignored",
        "stats", "versions")


def _fix_target(p: Path) -> Path:
    """Where a fix proposal for file p would land, if the Governor commits it."""
    return Path.home() / ".debug-wizard" / f"fix_{p.stem}.txt"


def _stage_via_writewiz(target: Path, content: str):
    """Stage content through writewiz, the fleet sibling in this same package.

    Import lane first (writewiz ships inside this toolkit); fall back to
    the resolved writewiz executable — the same two lanes the fleet
    itself uses. Staging only: the commit keystroke stays the Governor's.
    Returns (ok, detail).
    """
    try:
        from wiz_central_toolkit.writewiz.write_wizard import propose as _propose
        draft, _meta, t = _propose(str(target), content)
        return True, f"{draft.name} -> {t} ({len(content)} chars quarantined)"
    except ImportError:
        pass
    import shutil
    import subprocess
    exe = shutil.which("write_wizard") or shutil.which("writewiz")
    if exe is None:
        for home_name in ("write_wizard", "writewiz"):
            home_exe = Path.home() / "bin" / home_name
            if home_exe.exists():
                exe = str(home_exe)
                break
    if exe is None:
        return False, "write_wizard not found (package import or PATH)"
    try:
        r = subprocess.run([exe, "propose", str(target)], input=content,
                           capture_output=True, text=True, timeout=60)
    except OSError as e:
        return False, f"write_wizard unreachable: {e}"
    if r.returncode != 0:
        return False, (r.stdout + r.stderr).strip() or "write_wizard propose failed"
    return True, (r.stdout.strip() or f"staged -> {target}")


def _preview_via_writewiz(target: Path):
    """(report_lines, hard_fail) for the draft staged for target, or None."""
    try:
        from wiz_central_toolkit.writewiz import write_wizard as _ww
        draft, _meta = _ww._draft_path(Path(target))
        if not draft.exists():
            return None
        return _ww.gate_and_diff(draft, Path(target))
    except ImportError:
        pass
    import shutil
    import subprocess
    exe = shutil.which("write_wizard") or shutil.which("writewiz")
    if exe is None:
        return None
    try:
        r = subprocess.run([exe, "preview", str(target)],
                           capture_output=True, text=True, timeout=60)
    except OSError:
        return None
    out = (r.stdout + r.stderr).strip()
    if "no quarantined draft" in out:
        return None
    return out.splitlines(), r.returncode != 0


def main(argv=None) -> int:
    try:
        return _dispatch(argv)
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return 1


def _dispatch(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    if not args:
        print(USAGE)
        return 0
    if args[0] not in CMDS:
        print(USAGE)
        return 2

    cmd = args[0]

    if cmd == "law":
        print(DEBUG_LAW)
        return 0
    if cmd == "versions":
        import hashlib
        print("debug_law_sha256:", hashlib.sha256(DEBUG_LAW.encode()).hexdigest())
        return 0
    if cmd == "ignored":
        ign = load_ignored()
        if not ign:
            print("(nothing ignored)")
            return 0
        for p in ign:
            print(f"[IGNORED] {p}")
        return 0
    if cmd == "ignore":
        if len(args) < 2:
            return 2
        r = add_ignore(args[1])
        if r["ok"]:
            print(f"[OK] ignored: {r['ignored']}")
            return 0
        print(f"[FAIL] {r['error']}")
        return 1
    if cmd == "stats":
        for path, r in stats_fleet().items():
            healthy = r.get("healthy", "?")
            checked = r.get("files_checked", "?")
            pct = r.get("health_pct", "?")
            print(f"{path}: {healthy}/{checked} healthy ({pct}%)")
        return 0

    # --- locate: two args (dir, pattern) ---
    if cmd == "locate":
        if len(args) < 3:
            print("[FAIL] locate requires a directory and a pattern")
            return 2
        d = Path(args[1]).expanduser()
        pattern = args[2]
        hits = locate(d, pattern)
        if not hits:
            print(f"(no files matching {pattern!r})")
            return 0
        for f in hits:
            print(f"[MATCH] {f}")
        return 1

    # --- stack: a traceback digest; file argument or stdin ---
    if cmd == "stack":
        if len(args) >= 2 and args[1] != "-":
            src = Path(args[1]).expanduser()
            try:
                text = src.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                print(f"[FAIL] cannot read {src}: {e}")
                return 1
            label = str(src)
        else:
            text = sys.stdin.read()
            label = "stdin"
        d = stack_digest(text)
        if d is None:
            print(f"[FAIL] no traceback found in {label}")
            return 1
        print(f"[OK] stack digest — {label}")
        exc = d["type"] + (f": {d['message']}" if d["message"] else "")
        print(f"  exception: {exc}")
        print(f"  frames: {len(d['frames'])}")
        for fr in d["frames"]:
            print(f"    File \"{fr['file']}\", line {fr['line']}, "
                  f"in {fr['func']} ({fr['home']})")
        deep = d["deepest"]
        print(f"  deepest frame: File \"{deep['file']}\", "
              f"line {deep['line']}, in {deep['func']}")
        dp = d["deepest_project"]
        if dp is not None:
            print(f"  deepest project frame: File \"{dp['file']}\", "
                  f"line {dp['line']}, in {dp['func']}")
        else:
            print("  deepest project frame: none — every frame is library code")
        for (ff, ln, fn), c in d["repeated"]:
            print(f"  [RECURSION?] frame repeats {c} times: "
                  f"File \"{ff}\", line {ln}, in {fn}")
        return 0

    # --- path-taking commands ---
    if len(args) < 2:
        print(f"[FAIL] {cmd} requires a path")
        return 2
    p = Path(args[1]).expanduser()

    if cmd == "trace":
        r = trace(p)
        if r["ok"]:
            print(f"[OK] {p}: no errors")
            return 0
        tb = r.get("traceback")
        if tb:
            print(f"[TRACE] {p}: {len(tb['frames'])} frame(s)")
            for fr in tb["frames"]:
                print(f"  File \"{fr['file']}\", line {fr['line']}, in {fr['func']}")
        for err in r["errors"]:
            print(f"[ERR] line {err['line']}: {err['type']} — {err['message']}")
        return 1
    if cmd == "classify":
        r = classify_file(p)
        print(f"[SUMMARY] {r['total']} errors")
        for t, c in r["classification"].items():
            print(f"  {t}: {c}")
        return 1 if r["total"] else 0
    if cmd == "count":
        r = count_dir(p)
        print(f"files={r['files_checked']} total_errors={r['totals']}")
        return 0
    if cmd == "hotspot":
        hits = hotspot(p)
        if not hits:
            print("(all files healthy)")
            return 0
        for f, cnt in hits:
            print(f"[HOT] {cnt} errors  {f}")
        return 1 if hits else 0
    if cmd == "timeline":
        data = timeline(p)
        for entry in data[:10]:
            print(f"{entry['errors']} errors  {entry['mtime']}  {entry['file']}")
        return 0
    if cmd == "imports":
        r = imports(p)
        print(f"[IMPORTS] {p}")
        if not r["likely_missing"]:
            print("(no likely missing imports)")
            return 0
        for m in r["likely_missing"]:
            print(f"  ? {m}")
        return 1 if r["likely_missing"] else 0
    if cmd == "names":
        r = names(p)
        if not r:
            print("(no undefined names)")
            return 0
        for n in r:
            print(f"  ? {n}")
        return 1
    if cmd == "signatures":
        iss = signatures(p)
        if not iss:
            print("(no signature issues)")
            return 0
        for i in iss:
            print(f"[WARN] line {i['line']}: {i['message']}")
        return 1
    if cmd == "suggest":
        print(suggest_fix(p))
        return 0
    if cmd == "explain":
        print(suggest_fix(p))
        return 0
    if cmd == "audit":
        r = audit_dir(p)
        print(f"[HEALTH] {r['healthy']}/{r['files_checked']} ({r['health_pct']}%)")
        if r["unhealthy"]:
            print(f"[FAIL] {r['unhealthy']} files with errors")
            return 1
        print("[OK] all files healthy")
        return 0
    if cmd == "report":
        print(report_json(str(p)))
        return 0
    if cmd == "log":
        r = audit_dir(p)
        lines = [f"debug_wizard error log — {p}",
                 f"files checked: {r['files_checked']}",
                 f"healthy: {r['healthy']}  unhealthy: {r['unhealthy']}  "
                 f"total errors: {r['total_errors']}"]
        for f, cnt in hotspot(p):
            lines.append(f"[HOT] {cnt} errors  {f}")
            for err in trace(Path(f))["errors"]:
                lines.append(f"  line {err['line']}: {err['type']} — {err['message']}")
        target = (p / "debug-error-log.txt") if p.is_dir() \
            else p.with_name(p.stem + "-error-log.txt")
        ok, detail = _stage_via_writewiz(target, "\n".join(lines) + "\n")
        if not ok:
            print(f"[FAIL] 'log' could not stage via write_wizard: {detail}")
            return 1
        print(f"[STAGED] error log for {p} — {detail}")
        print(f"to write it: write_wizard commit {target}   # your keystroke, Governor")
        return 0
    if cmd == "propose":
        content = suggest_fix(p)
        if not content.endswith("\n"):
            content += "\n"
        target = _fix_target(p)
        ok, detail = _stage_via_writewiz(target, content)
        if not ok:
            print(f"[FAIL] propose could not stage via write_wizard: {detail}")
            return 1
        print(f"[STAGED] fix proposal for {p} — {detail}")
        print(f"preview it: debug_wizard preview {p}")
        return 0
    if cmd == "preview":
        got = _preview_via_writewiz(_fix_target(p))
        if got is None:
            print("(no staged proposal — use debugwiz propose first)")
            return 0
        report, hard_fail = got
        for line in report:
            print(line)
        return 1 if hard_fail else 0

    print("out of scope")
    return 2


if __name__ == "__main__":
    sys.exit(main())
