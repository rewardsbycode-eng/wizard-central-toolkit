"""codeguardwiz static engine — the built-in, seatless audit.

Standard library only. Real rules over Python source: `ast` where the
tree can see, text patterns where it cannot (comments and markers).
This is the always-available half of codeguardwiz (AVS's R1 ruling:
both engines, the user's choice). It never calls a model, never
writes a file, and everything it produces is labelled as its own.

Findings are plain dicts:
  {"path", "line", "rule", "name", "severity", "detail"}
with severity one of "high" | "medium" | "low".
"""
import ast
import re
from pathlib import Path

ENGINE_LABEL = "static (built-in rules)"

# ---------------------------------------------------------------- rules

_RULE_DEFS = [
    ("CG001", "syntax-error", "high",
     "The file does not parse as Python at all, so nothing in it can "
     "run. Every other check is blind until this is fixed: a file "
     "that cannot compile cannot be trusted to do what it says."),
    ("CG002", "hardcoded-secret", "high",
     "A password, token, or key written as a string literal directly "
     "in the source. Anyone who can read the code owns the secret, "
     "and the secret travels with every copy of the file. Move it to "
     "the environment or a config the code reads at runtime."),
    ("CG003", "eval-exec", "high",
     "eval() or exec() runs a string as code. If any part of that "
     "string can be influenced from outside, the caller can run "
     "anything. Parse the data instead (ast.literal_eval for "
     "literals), or dispatch to named functions."),
    ("CG004", "shell-execution", "high",
     "A shell interprets this command (os.system, os.popen, or a "
     "subprocess call with shell=True), so metacharacters in the "
     "arguments become commands. Pass an argument list with "
     "shell=False and let the program, not a shell, run."),
    ("CG005", "pickle-load", "medium",
     "pickle.load/loads rebuilds objects from bytes and will run "
     "whatever the bytes say. Never unpickle data that crossed a "
     "trust boundary; use a data format (JSON) for anything "
     "untrusted."),
    ("CG006", "weak-hash", "medium",
     "MD5 and SHA-1 are broken for security use: collisions are "
     "cheap to manufacture. For integrity or password work use "
     "SHA-256 or better (hashlib.sha256, or a password KDF such as "
     "hashlib.pbkdf2_hmac)."),
    ("CG007", "bare-except", "medium",
     "A bare `except:` catches everything — including "
     "KeyboardInterrupt, SystemExit, and the very bugs you are "
     "hunting — and hides them all alike. Name the exceptions you "
     "expect (`except Exception:` at the widest). This is the one "
     "finding the static engine can rewrite deterministically."),
    ("CG008", "swallowed-exception", "low",
     "An except block whose whole body is `pass` (or `...`) makes "
     "the failure vanish silently: the program continues as if "
     "nothing happened, in a state nobody checked. Log it, count "
     "it, or let it propagate — but decide on purpose."),
    ("CG009", "todo-marker", "low",
     "A TODO or FIXME comment is a promise the code has not kept "
     "yet. Not a defect by itself — it is listed so the promise "
     "stays visible instead of sinking into the file."),
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
    """Look a rule up by id (CG002), exact name, or name fragment."""
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

_SECRET_NAME = re.compile(
    r"(password|passwd|pwd|secret|api[_-]?key|access[_-]?token"
    r"|auth[_-]?token|private[_-]?key)", re.IGNORECASE)
_TODO = re.compile(r"#\s*(TODO|FIXME)\b")
_BARE_EXCEPT = re.compile(r"^(\s*)except\s*:\s*(#.*)?$")

_KNOWN_MODULES = ("os", "subprocess", "pickle", "hashlib")


def _finding(path, line, rule, detail):
    return {"path": str(path), "line": line, "rule": rule.id,
            "name": rule.name, "severity": rule.severity,
            "detail": detail}


def _is_secret_name(name):
    return bool(_SECRET_NAME.search(name)) or name.lower() == "token" \
        or name.lower().endswith("_token")


def _imports(tree):
    """Map local names back to the modules they came from."""
    modules = {}   # local name -> top module ("pickle", "os", ...)
    funcs = {}     # local func name -> (module, attr)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                modules[a.asname or top] = top
        elif isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            for a in node.names:
                funcs[a.asname or a.name] = (top, a.name)
    return modules, funcs


def _call_target(func, modules, funcs):
    """Resolve a call's func to (module, attr) where determinable."""
    if isinstance(func, ast.Attribute):
        base = func.value
        if isinstance(base, ast.Name):
            mod = modules.get(base.id, base.id)
            return mod, func.attr
        return None, func.attr
    if isinstance(func, ast.Name):
        if func.id in funcs:
            return funcs[func.id]
        return None, func.id
    return None, None


def scan_source(source, path="<source>"):
    """All findings in one Python source string, sorted by line."""
    findings = []
    lines = source.splitlines()

    # text lane: markers live in comments, which the AST drops
    for i, text in enumerate(lines, 1):
        m = _TODO.search(text)
        if m:
            findings.append(_finding(
                path, i, RULE_BY_ID["CG009"],
                f"{m.group(1)} marker left in the code"))

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        findings.append(_finding(
            path, e.lineno or 1, RULE_BY_ID["CG001"],
            f"{e.msg} (line {e.lineno or 1})"))
        findings.sort(key=lambda f: (f["line"], f["rule"]))
        return findings

    modules, funcs = _imports(tree)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) \
                else [node.target]
            if isinstance(value, ast.Constant) \
                    and isinstance(value.value, str) and value.value:
                for t in targets:
                    if isinstance(t, ast.Name) and _is_secret_name(t.id):
                        findings.append(_finding(
                            path, node.lineno, RULE_BY_ID["CG002"],
                            f"string literal assigned to '{t.id}'"))
        elif isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str) \
                        and _is_secret_name(k.value) \
                        and isinstance(v, ast.Constant) \
                        and isinstance(v.value, str) and v.value:
                    findings.append(_finding(
                        path, v.lineno, RULE_BY_ID["CG002"],
                        f"string literal under key '{k.value}'"))
        elif isinstance(node, ast.Call):
            mod, attr = _call_target(node.func, modules, funcs)
            bare = node.func.id if isinstance(node.func, ast.Name) else None
            if bare in ("eval", "exec"):
                findings.append(_finding(
                    path, node.lineno, RULE_BY_ID["CG003"],
                    f"{bare}() executes a string as code"))
            if mod == "os" and attr in ("system", "popen"):
                findings.append(_finding(
                    path, node.lineno, RULE_BY_ID["CG004"],
                    f"os.{attr}() always runs through a shell"))
            if mod == "subprocess":
                for kw in node.keywords:
                    if kw.arg == "shell" \
                            and isinstance(kw.value, ast.Constant) \
                            and kw.value.value is True:
                        findings.append(_finding(
                            path, node.lineno, RULE_BY_ID["CG004"],
                            "subprocess call with shell=True"))
            if mod == "pickle" and attr in ("load", "loads"):
                findings.append(_finding(
                    path, node.lineno, RULE_BY_ID["CG005"],
                    f"pickle.{attr}() deserializes arbitrary objects"))
            if mod == "hashlib" and attr in ("md5", "sha1"):
                findings.append(_finding(
                    path, node.lineno, RULE_BY_ID["CG006"],
                    f"hashlib.{attr}() is a broken hash for security use"))
            if mod == "hashlib" and attr == "new" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) \
                        and isinstance(first.value, str) \
                        and first.value.lower().replace("-", "") \
                        in ("md5", "sha1"):
                    findings.append(_finding(
                        path, node.lineno, RULE_BY_ID["CG006"],
                        f"hashlib.new({first.value!r}) is a broken hash "
                        "for security use"))
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                findings.append(_finding(
                    path, node.lineno, RULE_BY_ID["CG007"],
                    "bare except: catches everything, names nothing"))
            elif len(node.body) == 1 and (
                    isinstance(node.body[0], ast.Pass) or (
                        isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and node.body[0].value.value is Ellipsis)):
                findings.append(_finding(
                    path, node.lineno, RULE_BY_ID["CG008"],
                    "except block swallows the exception silently"))

    findings.sort(key=lambda f: (f["line"], f["rule"]))
    return findings


def scan_file(path):
    """Findings for one file on disk. Raises OSError if unreadable."""
    source = Path(path).read_text(encoding="utf-8", errors="ignore")
    return scan_source(source, str(path))


def collect_files(target):
    """The .py files a file-or-dir target names (model scan's own set)."""
    p = Path(target)
    if p.is_file():
        return [p] if p.suffix == ".py" else []
    if p.is_dir():
        return sorted(f for f in p.rglob("*.py")
                      if "__pycache__" not in str(f)
                      and ".venv" not in str(f))
    return []


def counts(findings):
    out = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        out[f["severity"]] += 1
    return out


# ---------------------------------------------------------------- fixing

FIXABLE_RULES = ("CG007",)


def apply_fixes(source, findings):
    """Deterministically rewrite what has a defensible rewrite.

    CG007 only: a line that is exactly a bare `except:` (plus optional
    trailing comment) becomes `except Exception:` with the same
    indentation. Line count never changes. Returns (new_source, n).
    """
    lines = source.splitlines(keepends=True)
    applied = 0
    for f in findings:
        if f["rule"] not in FIXABLE_RULES:
            continue
        idx = f["line"] - 1
        if not (0 <= idx < len(lines)):
            continue
        raw = lines[idx]
        body = raw.rstrip("\r\n")
        ending = raw[len(body):]
        m = _BARE_EXCEPT.match(body)
        if not m:
            continue
        comment = f"  {m.group(2)}" if m.group(2) else ""
        lines[idx] = f"{m.group(1)}except Exception:{comment}{ending}"
        applied += 1
    return "".join(lines), applied
