"""codeguardwiz rust engine — the Rust half of the seatless audit.

Standard library only. The static engine's sibling: same finding
shape, same severity scale, same score inputs, so audit / explain /
watch / fix consume Rust findings with no downstream changes. It
never calls a model, never writes a file, and — by design — never
executes anything in the project it audits: no cargo, no rustc, no
subprocess against the target at all. An audit tool must not run
the code it is auditing (a `cargo check` would execute build
scripts), so there is deliberately no toolchain pass.

Findings are plain dicts, exactly the static engine's shape:
  {"path", "line", "rule", "name", "severity", "detail"}
with severity one of "high" | "medium" | "low".

Severity mapping (the design's words onto this scale): the
critical-class rules (shell construction, hardcoded secrets) sit at
"high" beside their Python twins CG004/CG002; transmute/unchecked
is "high" too — undefined behaviour outranks a warning. The
warning-class rules (unsafe regions, unwrap/expect, unpinned
dependencies) sit at "medium", where the Python scale keeps its
conditional risks (pickle, weak hash, bare except). The marker
rule is "low", beside CG009's TODO markers.

Scanning honesty: Rust has no standard-library AST, so this engine
is a line scanner, not a parser. Full-line `//` comments are
skipped for the code rules (the Python side's code rules read the
AST, where comments never fire). Patterns inside string literals
or /* */ block comments can still fire — the same honesty level as
the Python side's text lane, and the reason every finding names
its line for a human to judge.
"""
import re
from pathlib import Path

ENGINE_LABEL = "static (built-in rules)"

# ---------------------------------------------------------------- rules

_RULE_DEFS = [
    ("RS001", "unsafe-block", "medium",
     "An unsafe block (or unsafe fn) is where Rust's memory-safety "
     "guarantees stop being checked by the compiler and become the "
     "programmer's promise instead. Unsafe is sometimes necessary — "
     "FFI, low-level data structures — but every unsafe region is a "
     "place a reviewer should be able to find and question, so the "
     "audit keeps them all visible."),
    ("RS002", "unwrap-expect", "medium",
     "unwrap() and expect() turn a missing value (None) or a "
     "failure (Err) into a panic that unwinds the program. Where "
     "the value genuinely cannot be absent they are merely terse; "
     "anywhere input, files, or the network are involved they are "
     "crash sites waiting for the one case nobody tested. Handle "
     "the None/Err, or use `?` and let the caller decide."),
    ("RS003", "panic-marker", "low",
     "panic!, todo!, and unimplemented! announce in the source "
     "that a path crashes by design or is not finished yet. Like "
     "a TODO comment (CG009) they are promises the code has not "
     "kept — listed so they stay visible instead of being "
     "discovered at runtime."),
    ("RS004", "shell-construction", "high",
     "A command handed to a shell (sh, bash, cmd) is interpreted "
     "as text: metacharacters in any part of it become commands "
     "in their own right, and a command string assembled with "
     "format! has the same shape — what runs is decided by data "
     "at runtime. Run the program directly with an argument list "
     "(Command::new(\"prog\").arg(...)) so arguments stay "
     "arguments."),
    ("RS005", "unchecked-conversion", "high",
     "transmute and the *_unchecked family switch off the safety "
     "checks on a conversion: transmute reinterprets bytes as "
     "another type with no validity guarantee, and get_unchecked "
     "/ from_utf8_unchecked / unwrap_unchecked assume conditions "
     "the compiler no longer verifies. When the assumption is "
     "wrong the result is undefined behaviour, not an error "
     "message. Prefer the checked conversion."),
    ("RS006", "hardcoded-secret", "high",
     "A password, token, or key written as a string literal "
     "directly in the source. Anyone who can read the code owns "
     "the secret, and the secret travels with every copy of the "
     "file. Move it to the environment or a config the code reads "
     "at runtime. The audit names the variable and the pattern "
     "kind only — never the value."),
    ("RS007", "unpinned-dependency", "medium",
     "A dependency that can silently change under the build: a "
     "\"*\" version accepts whatever is newest on the day of the "
     "build, and a git dependency with no rev tracks a moving "
     "branch. Either way the same source can build against "
     "different code tomorrow — including code nobody reviewed. "
     "Pin a version, or pin a rev."),
]


class Rule:
    __slots__ = ("id", "name", "severity", "explanation")

    def __init__(self, rid, name, severity, explanation):
        self.id = rid
        self.name = name
        self.severity = severity
        self.explanation = explanation


RULES = [Rule(*d) for d in _RULE_DEFS]
RULE_BY_ID = {r.id: r for r in RULES}


def find_rule(query):
    """Look a rule up by id (RS002), exact name, or name fragment."""
    q = str(query).strip()
    if not q:
        return None
    if q.upper() in RULE_BY_ID:
        return RULE_BY_ID[q.upper()]
    ql = q.lower()
    for r in RULES:
        if r.name == ql:
            return r
    for r in RULES:
        if ql in r.name:
            return r
    return None


# ---------------------------------------------------------------- scanning

_UNSAFE = re.compile(r"\bunsafe\s*(\{|fn\b)")
_UNWRAP = re.compile(r"\.(unwrap|expect)\s*\(")
_PANIC = re.compile(r"\b(panic|todo|unimplemented)!\s*[\(\[\{]")
_SHELL_NEW = re.compile(r"Command::new\s*\(\s*\"(sh|bash|cmd)\"")
_SHELL_FMT = re.compile(r"Command::new\s*\(\s*format!\s*\(")
_SHELL_ARGC = re.compile(r"\.arg\s*\(\s*\"(-c|/C)\"\s*\)")
_TRANSMUTE = re.compile(r"\btransmute(_copy)?\b")
_UNCHECKED = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*_unchecked)\s*\(")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# The same secret-name vocabulary the static engine uses for CG002.
_SECRET_NAME = re.compile(
    r"(password|passwd|pwd|secret|api[_-]?key|access[_-]?token"
    r"|auth[_-]?token|private[_-]?key)", re.IGNORECASE)


def _finding(path, line, rule, detail):
    return {"path": str(path), "line": line, "rule": rule.id,
            "name": rule.name, "severity": rule.severity,
            "detail": detail}


def _is_secret_name(name):
    return bool(_SECRET_NAME.search(name)) or name.lower() == "token" \
        or name.lower().endswith("_token")


def _secret_literal_on_line(text):
    """Name of a secret-shaped variable given a string literal here.

    Mirrors CG002's two shapes in Rust dress: `let NAME = "..."`,
    `const NAME: Type = "..."`, and the struct-field form
    `name: "..."`. Returns the variable name only — the literal
    itself never leaves this function, so no finding can carry it.
    """
    for m in _IDENT.finditer(text):
        name = m.group(0)
        if not _is_secret_name(name):
            continue
        tail = text[m.end():].lstrip()
        if tail.startswith(":"):
            tail = tail[1:].lstrip()
            if not tail.startswith('"'):
                eq = tail.find("=")
                if eq == -1:
                    continue
                tail = tail[eq + 1:].lstrip()
        elif tail.startswith("="):
            if tail.startswith("=="):
                continue
            tail = tail[1:].lstrip()
        else:
            continue
        # a non-empty string literal: opening quote, then a character
        # that is not the closing quote
        if len(tail) >= 2 and tail[0] == '"' and tail[1] != '"':
            return name
    return None


def scan_source(source, path="<source>"):
    """All findings in one Rust source string, sorted by line."""
    findings = []
    for i, text in enumerate(source.splitlines(), 1):
        if text.strip().startswith("//"):
            continue  # full-line comment: the code rules do not fire
        m = _UNSAFE.search(text)
        if m:
            what = "unsafe fn" if m.group(1) == "fn" else "unsafe block"
            findings.append(_finding(
                path, i, RULE_BY_ID["RS001"],
                f"{what}: the compiler's memory-safety checks are "
                "suspended here"))
        for m in _UNWRAP.finditer(text):
            findings.append(_finding(
                path, i, RULE_BY_ID["RS002"],
                f".{m.group(1)}() panics when the value is None "
                "or Err"))
        for m in _PANIC.finditer(text):
            findings.append(_finding(
                path, i, RULE_BY_ID["RS003"],
                f"{m.group(1)}! left in the code — an explicit "
                "panic/unfinished marker"))
        m = _SHELL_NEW.search(text)
        if m:
            findings.append(_finding(
                path, i, RULE_BY_ID["RS004"],
                f"Command::new(\"{m.group(1)}\") spawns a shell: "
                "the string it is handed will be interpreted, "
                "not just run"))
        elif _SHELL_FMT.search(text):
            findings.append(_finding(
                path, i, RULE_BY_ID["RS004"],
                "the program to run is assembled with format!: a "
                "string built at runtime decides what executes"))
        m = _SHELL_ARGC.search(text)
        if m:
            findings.append(_finding(
                path, i, RULE_BY_ID["RS004"],
                f"shell flag \"{m.group(1)}\" passed as an argument: "
                "a shell will interpret the command string "
                "that follows"))
        m = _TRANSMUTE.search(text)
        if m:
            findings.append(_finding(
                path, i, RULE_BY_ID["RS005"],
                f"'{m.group(0)}' reinterprets bytes as another "
                "type with no validity check"))
        else:
            m = _UNCHECKED.search(text)
            if m:
                findings.append(_finding(
                    path, i, RULE_BY_ID["RS005"],
                    f"'{m.group(1)}' skips the checked conversion: "
                    "a wrong assumption is undefined behaviour"))
        name = _secret_literal_on_line(text)
        if name:
            findings.append(_finding(
                path, i, RULE_BY_ID["RS006"],
                f"string literal assigned to '{name}'"))
    findings.sort(key=lambda f: (f["line"], f["rule"]))
    return findings


# ---------------------------------------------------------------- Cargo.toml

_SECTION = re.compile(r"^\s*\[([^\]]+)\]")
_DEP_WILD = re.compile(r"^([A-Za-z0-9_-]+)\s*=\s*\"\*\"")
_DEP_NAME = re.compile(r"^([A-Za-z0-9_-]+)\s*=\s*\{(.*)\}\s*$")
_VERSION_WILD = re.compile(r"version\s*=\s*\"\*\"")
_GIT_DEP = re.compile(r"\bgit\s*=")
_REV_PIN = re.compile(r"\brev\s*=")


def scan_toml_source(source, path="<source>"):
    """RS007 findings in one Cargo.toml source string."""
    findings = []
    in_deps = False
    for i, text in enumerate(source.splitlines(), 1):
        stripped = text.strip()
        if stripped.startswith("#"):
            continue
        m = _SECTION.match(text)
        if m:
            in_deps = "dependencies" in m.group(1)
            continue
        if not in_deps or not stripped:
            continue
        m = _DEP_WILD.match(stripped)
        if m:
            findings.append(_finding(
                path, i, RULE_BY_ID["RS007"],
                f"dependency '{m.group(1)}' has version \"*\": it "
                "accepts whatever is newest on build day"))
            continue
        m = _DEP_NAME.match(stripped)
        if m:
            name, body = m.group(1), m.group(2)
            if _VERSION_WILD.search(body):
                findings.append(_finding(
                    path, i, RULE_BY_ID["RS007"],
                    f"dependency '{name}' has version \"*\": it "
                    "accepts whatever is newest on build day"))
            elif _GIT_DEP.search(body) and not _REV_PIN.search(body):
                findings.append(_finding(
                    path, i, RULE_BY_ID["RS007"],
                    f"git dependency '{name}' has no pinned rev: "
                    "it tracks whatever the branch points at"))
    findings.sort(key=lambda f: (f["line"], f["rule"]))
    return findings


def scan_file(path):
    """Findings for one file on disk. Raises OSError if unreadable."""
    source = Path(path).read_text(encoding="utf-8", errors="ignore")
    if Path(path).name == "Cargo.toml":
        return scan_toml_source(source, str(path))
    return scan_source(source, str(path))


def scan_toml_file(path):
    """RS007 findings for one Cargo.toml on disk."""
    source = Path(path).read_text(encoding="utf-8", errors="ignore")
    return scan_toml_source(source, str(path))


def collect_files(target):
    """The .rs files and Cargo.toml manifests a file-or-dir target names."""
    p = Path(target)
    if p.is_file():
        return [p] if p.suffix == ".rs" or p.name == "Cargo.toml" else []
    if p.is_dir():
        out = [f for f in p.rglob("*.rs")
               if "__pycache__" not in str(f) and ".venv" not in str(f)]
        out += [f for f in p.rglob("Cargo.toml")
                if "__pycache__" not in str(f) and ".venv" not in str(f)]
        return sorted(out)
    return []


def counts(findings):
    out = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        out[f["severity"]] += 1
    return out


# ---------------------------------------------------------------- fixing

FIXABLE_RULES = ()


def apply_fixes(source, findings):
    """No Rust finding has a defensible deterministic rewrite.

    The static engine stages exactly one mechanical rewrite
    (CG007, the bare `except:`); there is no Rust equivalent —
    nobody's `unwrap()` gets rewritten by a pattern. Rust findings
    are reported and explained; a rewrite proposal is the model
    engine's job. Returns (source, 0), unchanged, always.
    """
    return source, 0
