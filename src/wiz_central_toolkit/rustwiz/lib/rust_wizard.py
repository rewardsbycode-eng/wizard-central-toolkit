"""rust-wizard: honest Rust validator. No tracebacks, verdicts only."""
import subprocess
import tempfile
from pathlib import Path

LAW_TEXT = """RUST LAW (Rust Wizard, the honest validator)
1. The Rust Wizard judges Rust; it never writes it. Verdicts only.
2. Every verdict comes from the real toolchain (rustc, cargo).
   No toolchain, no verdict: a plain message, exit 2.
3. fmt speaks in --check: it reports drift, it never reformats.
4. clean is the one delete the Rust Wizard performs: a crate's
   own target/ directory, and nothing else, ever.
5. Mortal and stateless: one command, one verdict, then death.
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


class RustWizard:
    NAME = "rustwiz"

    def check(self, targets):
        files = []
        for target in targets:
            t = Path(target).expanduser()
            if t.is_dir():
                files.extend(sorted(t.rglob("*.rs")))
            elif t.suffix == ".rs" and t.is_file():
                files.append(t)
            else:
                print(f"out of scope - not a .rs file or directory: {target}")
                return 2
        if not files:
            print("[FAIL] no .rs files found")
            return 1
        bad = 0
        for f in files:
            with tempfile.TemporaryDirectory() as tmp:
                try:
                    r = subprocess.run(
                        ["rustc", "--edition", "2021", "-A", "warnings",
                         "--crate-type", "lib", "--emit=metadata",
                         "--out-dir", tmp, str(f)],
                        capture_output=True, text=True, timeout=120)
                except (FileNotFoundError, OSError):
                    print("[FAIL] rustc not found — install Rust to use rust_wizard check")
                    return 2
            if r.returncode == 0:
                print(f"[OK]   {f}")
            else:
                bad += 1
                print(f"[FAIL] {f}")
                first = (r.stderr or "").strip().splitlines()
                for line in first[:5]:
                    print(f"       {line}")
        print(f"{len(files) - bad}/{len(files)} valid, {bad} invalid")
        return 1 if bad else 0

    def _cargo(self, crate_dir, args, verb, show_stdout=False):
        """Run one cargo verb against a crate. One verdict shape for all."""
        d = Path(crate_dir).expanduser()
        if not (d / "Cargo.toml").is_file():
            print(f"[FAIL] no Cargo.toml in {d}")
            return 1
        try:
            r = subprocess.run(["cargo"] + args, cwd=str(d),
                               capture_output=True, text=True, timeout=600)
        except (FileNotFoundError, OSError):
            print(f"[FAIL] cargo not found — install Rust to use rust_wizard {verb}")
            return 2
        if r.returncode == 0:
            print(f"[OK]   cargo {args[0]} passed: {d}")
            return 0
        print(f"[FAIL] cargo {args[0]} failed: {d}")
        stream = (r.stdout if show_stdout else r.stderr) or ""
        for line in stream.strip().splitlines()[:8]:
            print(f"       {line}")
        return 1

    def build(self, crate_dir):
        return self._cargo(crate_dir, ["check", "--quiet"], "build")

    def test(self, crate_dir):
        return self._cargo(crate_dir, ["test", "--quiet"], "test")

    def clippy(self, crate_dir):
        return self._cargo(crate_dir, ["clippy", "--quiet"], "clippy")

    def doc(self, crate_dir):
        return self._cargo(crate_dir, ["doc", "--no-deps"], "doc")

    def fmt(self, crate_dir):
        # --check only: fmt reports drift, it never reformats (RUST LAW 3).
        return self._cargo(crate_dir, ["fmt", "--check"], "fmt",
                           show_stdout=True)

    def clean(self, crate_dir):
        # The one delete (RUST LAW 4): cargo clean removes target/ only.
        return self._cargo(crate_dir, ["clean"], "clean")

    def run(self, crate_dir):
        d = Path(crate_dir).expanduser()
        if not (d / "Cargo.toml").is_file():
            print(f"[FAIL] no Cargo.toml in {d}")
            return 1
        try:
            # No capture: the program's own output belongs on the terminal.
            r = subprocess.run(["cargo", "run", "--quiet"], cwd=str(d),
                               timeout=600)
        except (FileNotFoundError, OSError):
            print("[FAIL] cargo not found — install Rust to use rust_wizard run")
            return 2
        return r.returncode
