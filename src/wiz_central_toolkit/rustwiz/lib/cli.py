import sys
try:
    from .rust_wizard import LAW_TEXT, RustWizard, package_version
except ImportError:  # run directly as a script, outside the package
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from rust_wizard import LAW_TEXT, RustWizard, package_version

USAGE = """Rust Wizard — Rust project checker
alias: rustwiz
usage: rust_wizard check <file.rs|dir> ...
       rust_wizard build <crate-dir>    cargo check the crate
       rust_wizard run <crate-dir>      build and run the crate's binary
       rust_wizard test <crate-dir>     cargo test
       rust_wizard clippy <crate-dir>   cargo clippy lints
       rust_wizard fmt <crate-dir>      cargo fmt --check (reports drift only)
       rust_wizard doc <crate-dir>      cargo doc --no-deps
       rust_wizard clean <crate-dir>    cargo clean (removes target/ only)
       rust_wizard law                  print the RUST LAW alone
       rust_wizard version              print the version
       rust_wizard --help | --version"""

CRATE_COMMANDS = ("build", "run", "test", "clippy", "fmt", "doc", "clean")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    if argv and argv[0] == "--version":
        print(f"rust_wizard {package_version()}")
        return 0
    if not argv:
        print(f"out of scope - usage:\n{USAGE}")
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "law":
        print(LAW_TEXT)
        return 0
    if cmd == "version":
        print(f"rust_wizard {package_version()}")
        return 0
    wz = RustWizard()
    if cmd == "check" and args:
        return wz.check(args)
    if cmd in CRATE_COMMANDS and args:
        return getattr(wz, cmd)(args[0])
    print(f"out of scope - unknown or incomplete command: {' '.join(argv)}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
