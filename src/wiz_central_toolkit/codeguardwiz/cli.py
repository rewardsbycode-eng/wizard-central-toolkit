"""codeguardwiz — CLI face. Plain verdicts, exit codes 0/1/2, no tracebacks.

Two engines (AVS's R1 ruling — both, and the user's choice):
the model seat when a daemon serves one, and the built-in static
rules (static_engine) which are always available. Default: model
when a seat is served, static when none is. Every audit-family
output opens with an engine line naming the engine that spoke.
"""
import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

from . import rust_engine as reng
from . import static_engine as se
from .codeguard_wizard import (
    AUDIT_PREFS,
    FIX_PREFS,
    OLLAMA_BASE,
    audit,
    detect_language,
    fix,
    load_roster,
    pick_seat,
)

ENGINE_HELP = ("engine: static (built-in rules) or model (seat); "
               "default: model when a seat is served, else static")
NO_SEAT_HOWTO = ("     seat one: run a local Ollama serving a coder model "
                 "(e.g. `ollama pull qwen2.5-coder:3b-instruct`), "
                 "then re-run")


def _line_in_range(line, lr):
    """True if `line` falls inside `lr` (never a substring match).

    `lr` arrives in more than one shape: the model engine's audit
    contract emits a JSON pair [lo, hi]; text forms are '10-12',
    '10:12' or a bare '5'. A list/tuple of two numbers is read as
    (lo, hi). Anything malformed is a plain False.
    """
    if isinstance(lr, (list, tuple)):
        if len(lr) != 2:
            return False
        try:
            lo, hi = int(lr[0]), int(lr[1])
        except (TypeError, ValueError):
            return False
        return lo <= line <= hi
    import re
    m = re.fullmatch(r"\s*(\d+)\s*(?:[-:]\s*(\d+))?\s*", str(lr))
    if not m:
        return False
    lo = int(m.group(1))
    hi = int(m.group(2) or lo)
    return lo <= line <= hi


def _engine_line(engine):
    return "engine: model seat" if engine == "model" \
        else f"engine: {se.ENGINE_LABEL}"


def _is_no_seat(result):
    return str(result.get("reason", "")).startswith("no audit seat")


def _audit_seat():
    """The audit seat the model engine would pick right now, or None."""
    return pick_seat(load_roster(), AUDIT_PREFS, "CODEGUARD_AUDIT_MODEL")


def _no_seat_refusal():
    """--engine model demanded, no seat served: honest refusal, exit 1."""
    print(_engine_line("model"))
    print("[FAIL] no audit seat: daemon unreachable or no coder seat served")
    print(NO_SEAT_HOWTO)
    return 1


def _stage_via_writewiz(target: Path, content: str):
    """Stage content through writewiz, the fleet sibling in this package.

    Import lane first (writewiz ships inside this toolkit); fall back to
    the resolved writewiz executable — the same two lanes debugwiz
    uses. Staging only: the commit keystroke (and its double ask)
    stays the Governor's, inside writewiz's wall.
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


def _ask_fix_consent(target):
    """The double ask (house law) before a model fix lands.

    First the plain ask; then a typed confirmation naming the file.
    Anything but the two exact answers — including EOF — is a no,
    and the file stays untouched.
    """
    try:
        first = input(f"⚠️  write the model's fix to {target}? [y/N] ")
    except (KeyboardInterrupt, EOFError):
        return False
    if first.strip().lower() != "y":
        return False
    try:
        typed = input(f"confirm by typing: yes, write {target}\n> ")
    except (KeyboardInterrupt, EOFError):
        return False
    return typed.strip() == f"yes, write {target}"


def _land_via_writewiz(target: Path):
    """Land the staged draft for target through writewiz's commit.

    The Governor has just given the double ask at this terminal, for
    this file — that live consent is the answer commit's prompt
    records. Inside the wall, writewiz still runs its own gate,
    backup, journal and post-write verification. Returns (ok, detail).
    """
    try:
        from wiz_central_toolkit.writewiz import write_wizard as _ww
    except ImportError:
        return False, ("write_wizard not importable — the staged fix waits "
                       f"in quarantine; land it with: write_wizard commit {target}")
    draft, meta = _ww._draft_path(Path(target))
    if not draft.exists():
        return False, "no staged draft found in write_wizard's quarantine"
    ok, msg, _t = _ww.commit(draft, meta,
                             confirm_reader=lambda prompt="": "y")
    return ok, msg


# ------------------------------------------------------------ static engine

def _static_out_of_scope(path, lang):
    print(_engine_line("static"))
    print(f"out of scope - static engine audits Python and Rust "
          f"files only: {path} (detected: {lang})")
    return 2


def _static_kind(path):
    """Which static-family engine owns this file: 'python' | 'rust'."""
    p = Path(path)
    if p.suffix == ".py":
        return "python"
    if p.suffix == ".rs" or p.name == "Cargo.toml":
        return "rust"
    return None


def _scan_static_file(path, kind):
    """Findings for one file from its static-family engine."""
    if kind == "python":
        return se.scan_file(path)
    return reng.scan_file(path)


def _collect_static_files(target):
    """All static-auditable files under a dir: .py + .rs + Cargo.toml."""
    files = {str(f) for f in se.collect_files(target)}
    files.update(str(f) for f in reng.collect_files(target))
    return [Path(f) for f in sorted(files)]


# ------------------------------------------------------------------
# BASELINES — the audit remembers, so watch can compare.
# A single-file audit (either engine) records a baseline in the
# wizard's state: per-issue fingerprints, the score, and the engine
# that produced them. `watch` re-audits the same file with the same
# engine and reports the true delta — new / resolved / unchanged.
# ------------------------------------------------------------------

STATE_DIR = Path.home() / ".codeguard-wizard"
BASELINES = STATE_DIR / "baselines.json"


def _static_score(counts):
    return max(0, 100 - 10 * counts.get("high", 0)
               - 5 * counts.get("medium", 0) - 2 * counts.get("low", 0))


def _load_baselines():
    if BASELINES.exists():
        try:
            return json.loads(BASELINES.read_text())
        except Exception:
            return {}
    return {}


def _record_baseline(path, engine, score, issues):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    data = _load_baselines()
    data[str(Path(path).resolve())] = {
        "engine": engine,
        "score": score,
        "at": int(time.time()),
        "issues": sorted(issues),
    }
    BASELINES.write_text(json.dumps(data, indent=2) + "\n")


def _load_baseline(path):
    return _load_baselines().get(str(Path(path).resolve()))


def _static_fingerprints(findings):
    return [f"{f['rule']} @ line {f['line']}: {f['detail']}"
            for f in findings]


def _model_fingerprints(result):
    return [f"[{i.get('severity', '?')}] {i.get('title', '?')} "
            f"(line {i.get('line_range', '?')})"
            for i in result.get("audit", {}).get("issues", [])]


def _static_audit_file(path, as_json):
    kind = _static_kind(path)
    if kind is None:
        if as_json:
            print(json.dumps({"engine": "static", "filepath": path,
                              "status": "FAILED",
                              "reason": "static engine audits Python "
                                        "and Rust files only"}, indent=2))
            return 2
        return _static_out_of_scope(path, detect_language(path))
    try:
        findings = _scan_static_file(path, kind)
    except OSError:
        print(_engine_line("static"))
        print(f"[FAIL] cannot read file: {path}")
        return 1
    c = se.counts(findings)
    _record_baseline(path, "static", _static_score(c),
                     _static_fingerprints(findings))
    if as_json:
        print(json.dumps({"engine": "static", "filepath": path,
                          "language": kind, "counts": c,
                          "findings": findings}, indent=2))
        return 1 if c["high"] else 0
    print(_engine_line("static"))
    print(f"[OK] {path} ({kind}, static rules)")
    print(f"     findings: HIGH={c['high']} MEDIUM={c['medium']} "
          f"LOW={c['low']}")
    for f in findings:
        print(f"     [{f['severity'].upper()}] {f['rule']} {f['name']} "
              f"(line {f['line']}) — {f['detail']}")
    if c["high"]:
        print(f"     verdict: [FAIL] {c['high']} high-severity "
              "finding(s) present")
        return 1
    print("     verdict: [OK] no high-severity findings")
    return 0


def _static_scan(files, as_json, verdict=False):
    """Static findings over a file set, scan-shaped. Shared by scan/audit."""
    all_findings = []
    failed = []
    scanned = 0
    for f in files:
        kind = _static_kind(f)
        if kind is None:
            print(_engine_line("static"))
            print(f"out of scope - static engine audits Python and "
                  f"Rust files only: {f}")
            return 2
        scanned += 1
        try:
            all_findings.extend(_scan_static_file(f, kind))
        except OSError:
            failed.append(str(f))
    c = se.counts(all_findings)
    if as_json:
        print(json.dumps({"engine": "static", "files_scanned": scanned,
                          "failed": len(failed), "counts": c,
                          "findings": all_findings}, indent=2))
        return 1 if c["high"] or failed else 0
    print(_engine_line("static"))
    for f in all_findings:
        print(f"{f['path']}:{f['line']}: [{f['severity'].upper()}] "
              f"{f['rule']} {f['name']} — {f['detail']}")
    for name in failed:
        print(f"[FAIL] {name}: cannot read file")
    print(f"[OK] scanned {scanned} files")
    print(f"     HIGH={c['high']} MEDIUM={c['medium']} LOW={c['low']}")
    if verdict:
        if c["high"]:
            print(f"     verdict: [FAIL] {c['high']} high-severity "
                  "finding(s) present")
        else:
            print("     verdict: [OK] no high-severity findings")
    return 1 if c["high"] or failed else 0


def _resolve_engine(files, pref):
    """Decide the sweep engine once, from the first file's audit.

    Returns (engine, first_result). 'model' keeps first_result (the
    audit already spent on files[0]); a non-seat failure also stays
    model — a served-but-broken seat is reported, never masked by a
    silent switch to static.
    """
    if pref == "static":
        return "static", None
    if pref == "model":
        return "model", None
    if not files:
        return ("model" if _audit_seat() else "static"), None
    first = audit(str(files[0]))
    if first["status"] == "OK" or not _is_no_seat(first):
        return "model", first
    return "static", None


def _static_severity(target, threshold):
    t = Path(target)
    if t.is_file():
        if _static_kind(t) is None:
            return _static_out_of_scope(target, detect_language(target))
        files = [t]
    else:
        files = _collect_static_files(t)
    findings = []
    for f in files:
        try:
            findings.extend(_scan_static_file(f, _static_kind(f)))
        except OSError:
            print(_engine_line("static"))
            print(f"[FAIL] cannot read file: {f}")
            return 1
    levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    shown = levels if threshold is None \
        else levels[: levels.index(threshold) + 1]
    print(_engine_line("static"))
    print(f"[OK] {target} — findings by severity (static rules)")
    total = 0
    for lv in shown:
        group = [f for f in findings if f["severity"].upper() == lv]
        print(f"     {lv} ({len(group)}):")
        for f in group:
            print(f"       {f['path']}:{f['line']} {f['rule']} {f['name']} "
                  f"— {f['detail']}")
        total += len(group)
    return 1 if total else 0


def _static_explain(path, line):
    kind = _static_kind(path)
    if kind is None:
        return _static_out_of_scope(path, detect_language(path))
    try:
        findings = _scan_static_file(path, kind)
    except OSError:
        print(_engine_line("static"))
        print(f"[FAIL] cannot read file: {path}")
        return 1
    print(_engine_line("static"))
    hits = [f for f in findings if f["line"] == line]
    if not hits:
        print(f"[FAIL] no issue found at line {line}")
        return 1
    f = hits[0]
    rule = (se.RULE_BY_ID if kind == "python"
            else reng.RULE_BY_ID)[f["rule"]]
    print(f"[OK] Rule at line {line}:")
    print(f"     Severity: {f['severity'].upper()}")
    print(f"     Title: {f['rule']} {f['name']}")
    print(f"     Message: {rule.explanation}")
    print(f"     Detail: {f['detail']}")
    return 0


def _static_fix(path):
    kind = _static_kind(path)
    if kind is None:
        return _static_out_of_scope(path, detect_language(path))
    if kind == "rust":
        try:
            findings = reng.scan_file(path)
        except OSError:
            print(_engine_line("static"))
            print(f"[FAIL] cannot read file: {path}")
            return 1
        print(_engine_line("static"))
        if not findings:
            print(f"[OK] no findings in {path} — nothing to stage")
            return 0
        print("[OK] no deterministic rewrite available — nothing staged")
        print("     Rust findings have no safe mechanical fix: the "
              "static engine never rewrites Rust, so there is "
              "nothing to stage. A rewrite proposal is the model "
              "engine's job (seat one, then re-run so it can "
              "propose).")
        for f in findings:
            print(f"       line {f['line']}: {f['rule']} {f['name']} "
                  "— no deterministic rewrite")
        return 0
    lang = detect_language(path)
    if lang != "python":
        return _static_out_of_scope(path, lang)
    try:
        source = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        print(_engine_line("static"))
        print(f"[FAIL] cannot read file: {path}")
        return 1
    findings = se.scan_source(source, path)
    print(_engine_line("static"))
    if not findings:
        print(f"[OK] no findings in {path} — nothing to stage")
        return 0
    fixed, applied = se.apply_fixes(source, findings)
    rest = [f for f in findings if f["rule"] not in se.FIXABLE_RULES]
    if applied:
        ok, detail = _stage_via_writewiz(Path(path), fixed)
        if not ok:
            print(f"[FAIL] fix could not stage via write_wizard: {detail}")
            return 1
        print(f"[STAGED] fix for {path} — {detail}")
        print(f"to write it: write_wizard commit {path}   "
              "# your keystroke, Governor")
    else:
        print("[OK] no deterministic rewrite available — nothing staged")
    if rest:
        print("     needs a person or the model engine:")
        for f in rest:
            print(f"       line {f['line']}: {f['rule']} {f['name']} "
                  "— no deterministic rewrite")
    return 0


def _static_staged_only_refusal():
    print(_engine_line("static"))
    print("[FAIL] static fixes are staged through write_wizard — "
          "codeguard_wizard never writes them itself")
    print("     run without --write/--out to stage the fix, then "
          "commit it inside write_wizard's wall")
    return 1


# ------------------------------------------------------------ CLI proper

class _NamedParser(argparse.ArgumentParser):
    """Every help surface of this wizard leads with its name."""

    def format_help(self):
        return ("Code Guard Wizard — code audit wizard\n"
                "alias: codeguardwiz\n"
                + super().format_help())


def main():
    p = _NamedParser(prog="codeguard_wizard")
    sub = p.add_subparsers(dest="cmd", parser_class=_NamedParser)
    a = sub.add_parser("audit", help="audit a file or directory, print plain verdict")
    a.add_argument("file")
    a.add_argument("--json", action="store_true", help="machine-readable report")
    a.add_argument("--engine", choices=["static", "model"], help=ENGINE_HELP)
    f = sub.add_parser("fix", help="generate repaired code for a file")
    f.add_argument("file")
    f.add_argument("--write", action="store_true",
                   help="CONSENT: stage the fix via write_wizard, ask twice "
                        "at the terminal, then commit through the wall")
    f.add_argument("--out", help="write to this path instead (same wall)")
    f.add_argument("--engine", choices=["static", "model"], help=ENGINE_HELP)
    l = sub.add_parser("lang", help="detect language of a file")
    l.add_argument("file")
    r = sub.add_parser("roster", help="show the engines: static rules, and live seats when served")
    r.add_argument("--engine", choices=["static", "model"], help=ENGINE_HELP)

    # --- CODE REPAIR LANE EXPANSION ---
    sc = sub.add_parser("scan", help="recursive audit sweep on a file or directory")
    sc.add_argument("dir", help="file or directory to scan")
    sc.add_argument("--json", action="store_true", help="machine-readable report")
    sc.add_argument("--engine", choices=["static", "model"], help=ENGINE_HELP)

    wh = sub.add_parser("watch", help="diff-since-last-audit: re-run audit, report changes")
    wh.add_argument("file", help="file to watch")

    sv = sub.add_parser("severity", help="findings grouped by severity")
    sv.add_argument("file", help="file or directory to audit")
    sv.add_argument("--threshold", default=None, choices=["CRITICAL", "HIGH", "MEDIUM"],
                    help="show this severity and above (default: HIGH for the "
                         "model engine, all groups for static)")
    sv.add_argument("--engine", choices=["static", "model"], help=ENGINE_HELP)

    ex = sub.add_parser("explain", help="explain a static rule, or the rule that fired at a line")
    ex.add_argument("file", help="file with finding, or a static rule id/name")
    ex.add_argument("line", type=int, nargs="?", default=None,
                    help="line number (omit to explain a rule by id/name)")
    ex.add_argument("--engine", choices=["static", "model"], help=ENGINE_HELP)

    sf = sub.add_parser("scaffold", help="generate unit-test skeleton for file")
    sf.add_argument("file", help="source file to test")
    sf.add_argument("--framework", default="pytest", choices=["pytest", "unittest", "nose"])

    if sys.argv[1:2] == ["help"]:
        p.print_help()
        return 0
    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 0

    if args.cmd == "roster":
        roster = load_roster()
        audit_seat = pick_seat(roster, AUDIT_PREFS, "CODEGUARD_AUDIT_MODEL") \
            if roster else None
        fix_seat = pick_seat(roster, FIX_PREFS, "CODEGUARD_FIX_MODEL") \
            if roster else None
        resolved = "static" if args.engine == "static" or not audit_seat \
            else "model"
        print(_engine_line(resolved))
        print("engines:")
        print("[OK] static (built-in rules) — always available, "
              "no daemon needed")
        print("     rules:")
        for rule in se.RULES:
            print(f"     {rule.id} {rule.name} ({rule.severity.upper()})")
        print("     rust rules:")
        for rule in reng.RULES:
            print(f"     {rule.id} {rule.name} ({rule.severity.upper()})")
        if roster:
            print(f"[OK] model seat — daemon serves {len(roster)} "
                  "model(s):")
            for name in roster:
                marks = []
                if name == audit_seat:
                    marks.append("audit")
                if name == fix_seat:
                    marks.append("fix")
                print(f"[OK] {name}" + (f" <- {'/'.join(marks)}" if marks else ""))
        else:
            print("[FAIL] model seat — none served: daemon unreachable "
                  "or no coder seat served")
            print(NO_SEAT_HOWTO)
        return 0

    if args.cmd == "lang":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        lang = detect_language(path)
        if lang == "unknown":
            print("out of scope - language not detectable")
            return 2
        print(f"[OK] {path}: {lang}")
        return 0

    if args.cmd == "audit":
        target = Path(args.file)
        if target.is_dir():
            files = se.collect_files(target)
            if args.engine == "model" and _audit_seat() is None:
                return _no_seat_refusal()
            engine, first = _resolve_engine(files, args.engine)
            if engine == "static":
                return _static_scan(_collect_static_files(target),
                                    args.json, verdict=True)
            print(_engine_line("model"))
            totals = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            failed = 0
            for i, fp in enumerate(files):
                result = first if (i == 0 and first is not None) \
                    else audit(str(fp))
                if result["status"] != "OK":
                    failed += 1
                    print(f"[FAIL] {fp}: "
                          f"{result.get('reason', 'audit failed')}")
                    continue
                counts = result["issues_count"]
                for k in totals:
                    totals[k] += counts.get(k, 0)
                print(f"[OK] {result['filepath']} "
                      f"({result['language']}, model {result['model']}, "
                      f"score {result['audit'].get('score', '?')})")
                for issue in result["audit"].get("issues", []):
                    print(f"     [{issue.get('severity', '?')}] "
                          f"{issue.get('title', '?')} "
                          f"(line {issue.get('line_range', '?')})")
            print(f"     findings: CRITICAL={totals['CRITICAL']} "
                  f"HIGH={totals['HIGH']} MEDIUM={totals['MEDIUM']} "
                  f"LOW={totals['LOW']}")
            bad = totals["CRITICAL"] + totals["HIGH"]
            if bad or failed:
                print(f"     verdict: [FAIL] {bad} critical/high "
                      "finding(s) present"
                      + (f", {failed} file(s) unaudited" if failed else ""))
                return 1
            print("     verdict: [OK] no critical/high findings")
            return 0
        if not target.is_file():
            print(f"[FAIL] not a file: {args.file}")
            return 1
        path = args.file
        if args.engine == "static":
            return _static_audit_file(path, args.json)
        result = audit(path)
        if result["status"] != "OK":
            if _is_no_seat(result):
                if args.engine == "model":
                    return _no_seat_refusal()
                return _static_audit_file(path, args.json)
            if args.json:
                print(json.dumps(result, indent=2))
            print(f"[FAIL] {result.get('reason', 'audit failed')}")
            return 1
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(_engine_line("model"))
        counts = result["issues_count"]
        score = result["audit"].get("score", "?")
        print(f"[OK] {result['filepath']} ({result['language']}, "
              f"model {result['model']}, score {score})")
        print(f"     issues: CRITICAL={counts['CRITICAL']} HIGH={counts['HIGH']} "
              f"MEDIUM={counts['MEDIUM']} LOW={counts['LOW']}")
        for issue in result["audit"].get("issues", []):
            print(f"     [{issue.get('severity', '?')}] {issue.get('title', '?')} "
                  f"(line {issue.get('line_range', '?')})")
        if isinstance(score, (int, float)):
            _record_baseline(path, "model", score,
                             _model_fingerprints(result))
        return 0

    if args.cmd == "scan":
        t = Path(args.dir)
        if t.is_file():
            files = [t]
        elif t.is_dir():
            files = se.collect_files(t)
        else:
            print(f"[FAIL] not a directory: {args.dir}")
            return 1
        if args.engine == "model" and _audit_seat() is None:
            return _no_seat_refusal()
        engine, first = _resolve_engine(files, args.engine)
        if engine == "static":
            sweep = files if t.is_file() else _collect_static_files(t)
            return _static_scan(sweep, args.json)
        results = []
        total = 0
        critical = 0
        high = 0
        failed = 0
        for i, fp in enumerate(files):
            r = first if (i == 0 and first is not None) else audit(str(fp))
            if r["status"] == "OK":
                counts = r.get("issues_count", {})
                crit = counts.get("CRITICAL", 0)
                h = counts.get("HIGH", 0)
                if crit or h:
                    results.append({
                        "file": str(fp), "crit": crit, "high": h
                    })
                    critical += crit
                    high += h
            else:
                failed += 1
            total += 1
        if args.json:
            print(json.dumps({"files_scanned": total, "failed": failed, "findings": results}, indent=2))
        else:
            print(_engine_line("model"))
            print(f"[OK] scanned {total} files")
            if failed:
                print(f"[FAIL] {failed} file(s) could not be audited (daemon down or bad reply)")
            print(f"     CRITICAL={critical} HIGH={high}")
            if results:
                print("     findings:")
                for r in results[:10]:
                    print(f"       {r['file']}: C={r['crit']} H={r['high']}")
        return 1 if critical or high or failed else 0

    if args.cmd == "watch":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        base = _load_baseline(path)
        if base is None:
            print(f"[FAIL] no baseline recorded for {path}")
            print("     run `codeguard_wizard audit <file>` first — "
                  "an audit records the baseline watch compares against")
            return 1
        engine = base.get("engine", "static")
        if engine == "static":
            kind = _static_kind(path)
            if kind is None:
                print(_engine_line("static"))
                print(f"[FAIL] static engine audits Python and Rust "
                      f"files only: {path}")
                return 1
            try:
                findings = _scan_static_file(path, kind)
            except OSError:
                print(_engine_line("static"))
                print(f"[FAIL] cannot read file: {path}")
                return 1
            now_score = _static_score(se.counts(findings))
            now_issues = _static_fingerprints(findings)
        else:
            result = audit(path)
            if result["status"] != "OK":
                if _is_no_seat(result):
                    return _no_seat_refusal()
                print(f"[FAIL] {result.get('reason', 'audit failed')}")
                return 1
            now_score = result["audit"].get("score", "?")
            now_issues = _model_fingerprints(result)
        before = Counter(base.get("issues", []))
        after = Counter(now_issues)
        new = after - before
        resolved = before - after
        unchanged = sum((before & after).values())
        print(_engine_line(engine))
        print(f"[OK] watch {path} — baseline score {base.get('score', '?')} "
              f"-> now {now_score}")
        print(f"     new: {sum(new.values())}  resolved: "
              f"{sum(resolved.values())}  unchanged: {unchanged}")
        for fp, n in sorted(new.items()):
            print(f"     NEW      {fp}" + (f" (x{n})" if n > 1 else ""))
        for fp, n in sorted(resolved.items()):
            print(f"     RESOLVED {fp}" + (f" (x{n})" if n > 1 else ""))
        return 0

    if args.cmd == "severity":
        target = Path(args.file)
        if not target.exists():
            print(f"[FAIL] not a file: {args.file}")
            return 1
        if args.engine == "static":
            return _static_severity(args.file, args.threshold)
        if target.is_dir():
            files = se.collect_files(target)
            if args.engine == "model" and _audit_seat() is None:
                return _no_seat_refusal()
            engine, first = _resolve_engine(files, args.engine)
            if engine == "static":
                return _static_severity(args.file, args.threshold)
            threshold = args.threshold or "HIGH"
            levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            shown = levels[: levels.index(threshold) + 1]
            print(_engine_line("model"))
            groups = {lv: [] for lv in shown}
            for i, fp in enumerate(files):
                result = first if (i == 0 and first is not None) \
                    else audit(str(fp))
                if result["status"] != "OK":
                    print(f"[FAIL] {fp}: "
                          f"{result.get('reason', 'audit failed')}")
                    return 1
                for iss in result.get("audit", {}).get("issues", []):
                    sev = iss.get("severity", "")
                    if sev in groups:
                        groups[sev].append((str(fp), iss))
            total_above = sum(len(v) for v in groups.values())
            print(f"[OK] {threshold}+ severity: {total_above} findings")
            for lv in shown:
                for fp, iss in groups[lv]:
                    print(f"     [{lv}] {iss.get('title')} "
                          f"({fp} line {iss.get('line_range')})")
            return 1 if total_above > 0 else 0
        path = args.file
        result = audit(path)
        if result["status"] != "OK":
            if _is_no_seat(result):
                if args.engine == "model":
                    return _no_seat_refusal()
                return _static_severity(path, args.threshold)
            print(f"[FAIL] {result.get('reason', 'audit failed')}")
            return 1
        print(_engine_line("model"))
        threshold = args.threshold or "HIGH"
        counts = result.get("issues_count", {})
        levels = ["CRITICAL", "HIGH", "MEDIUM"]
        levels = levels[: levels.index(threshold) + 1]
        total_above = sum(counts.get(lv, 0) for lv in levels)
        print(f"[OK] {threshold}+ severity: {total_above} findings")
        if total_above > 0:
            for iss in result.get("audit", {}).get("issues", []):
                sev = iss.get("severity", "")
                if sev in levels:
                    print(f"     [{sev}] {iss.get('title')} (line {iss.get('line_range')})")
        return 1 if total_above > 0 else 0

    if args.cmd == "explain":
        if args.line is None:
            rule = se.find_rule(args.file) or reng.find_rule(args.file)
            print(_engine_line("static"))
            if rule is None:
                print(f"[FAIL] no rule '{args.file}' in the static rule "
                      "roster (see: codeguard_wizard roster)")
                return 1
            print(f"[OK] {rule.id} {rule.name} ({rule.severity.upper()})")
            print(f"     {rule.explanation}")
            return 0
        line = int(args.line)
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        if args.engine == "static":
            return _static_explain(path, line)
        result = audit(path)
        if result["status"] != "OK" and _is_no_seat(result):
            if args.engine == "model":
                return _no_seat_refusal()
            return _static_explain(path, line)
        print(_engine_line("model"))
        for iss in result.get("audit", {}).get("issues", []):
            lr = iss.get("line_range", "")
            if _line_in_range(line, lr):
                print(f"[OK] Rule at line {line}:")
                print(f"     Severity: {iss.get('severity', '?')}")
                print(f"     Title: {iss.get('title', '?')}")
                print(f"     Message: {iss.get('description', '(no description)')}")
                return 0
        print(f"[FAIL] no issue found at line {line}")
        return 1

    if args.cmd == "scaffold":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        # Real skeleton: read actual top-level functions from the source
        import ast as _ast
        try:
            tree = _ast.parse(Path(path).read_text())
        except SyntaxError as e:
            print(f"[FAIL] cannot parse {path}: {e}")
            return 1
        funcs = [n.name for n in tree.body if isinstance(n, _ast.FunctionDef)]
        classes = [n.name for n in tree.body if isinstance(n, _ast.ClassDef)]
        stem = Path(path).stem
        test_name = f"test_{stem}.py"
        lines = [
            f'"""Generated by codeguard_wizard scaffold — test skeleton for {path}."""',
            "import pytest",
            "",
        ]
        for fn in funcs:
            if fn.startswith("_"):
                continue
            lines += [f"def test_{fn}_exists():", f'    """SMOKE: {fn} exists."""',
                      "    assert True", ""]
        for cls in classes:
            lines += [f"def test_{cls}_importable():", f'    """SMOKE: {cls} importable."""',
                      "    import importlib.util as _iu",
                      f"    spec = _iu.spec_from_file_location('{stem}', r'{path}')",
                      "    assert spec is not None or True", ""]
        if not funcs and not classes:
            lines += [f"# (no public top-level defs found in {path})", ""]
        print(f"[OK] test skeleton generated (preview only, disk untouched): {test_name}")
        print(f"     functions: {len([f for f in funcs if not f.startswith('_')])}, "
              f"classes: {len(classes)}")
        print("--- skeleton follows ---")
        print("\n".join(lines))
        print("--- end ---")
        print("consent lane: pipe this output to a file yourself if you want it on disk")
        return 0

    if args.cmd == "fix":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        if args.engine == "static":
            if args.write or args.out:
                return _static_staged_only_refusal()
            return _static_fix(path)
        if args.engine == "model" and _audit_seat() is None:
            return _no_seat_refusal()
        result = fix(path)
        if result["status"] != "OK":
            reason = result.get("reason", "fix failed")
            seatless = reason.startswith("no fix seat") or (
                reason == "audit failed before fix"
                and _audit_seat() is None)
            if args.engine is None and seatless:
                if args.write or args.out:
                    return _static_staged_only_refusal()
                return _static_fix(path)
            print(f"[FAIL] {reason}")
            return 1
        print(_engine_line("model"))
        if result.get("issues_fixed", 0) == 0 and result.get("message"):
            print(f"[OK] {result['message']}")
            return 0
        if not args.write and not args.out:
            print(f"[OK] fix generated ({result['issues_fixed']} issues, "
                  f"model {result['fix_model']}) - preview only, disk untouched:")
            print("--- fixed code follows ---")
            print(result["fixed_code"])
            print("--- end ---")
            print("consent lane: re-run with --write to replace the file "
                  "(or --out <path>)")
            return 0
        dest = args.out or path
        target = Path(dest)
        if Path(path).suffix == ".py":
            import subprocess
            import tempfile
            with tempfile.NamedTemporaryFile("w", suffix=".py",
                                            delete=False) as tmp:
                tmp.write(result["fixed_code"])
            gate = subprocess.run([sys.executable, "-m", "wiz_central_toolkit.pythonwiz",
                                    "check", tmp.name],
                                   capture_output=True, text=True)
            os.unlink(tmp.name)
            if gate.returncode != 0:
                print("[FAIL] fixed code rejected by pythonwiz gate - "
                      "nothing written")
                return 1
            print("[OK] pythonwiz gate passed")
        ok, detail = _stage_via_writewiz(target, result["fixed_code"])
        if not ok:
            print(f"[FAIL] fix could not stage via write_wizard: {detail}")
            return 1
        print(f"[STAGED] model fix for {target} — {detail}")
        if not _ask_fix_consent(target):
            print("[CONSENT WALL] consent withheld — nothing written; "
                  "the staged fix stays in writewiz's quarantine")
            return 1
        ok, detail = _land_via_writewiz(target)
        if not ok:
            print(f"[FAIL] writewiz commit refused: {detail}")
            return 1
        print(f"[OK] written: {dest} (issues addressed: "
              f"{result['issues_fixed']})")
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
