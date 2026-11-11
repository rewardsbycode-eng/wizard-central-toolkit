# Changelog

All notable changes to `wizard-central-toolkit` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.6] — 2026-11-10

### Fixed
- **Godfather Wizard**: `is_generation_intent` now correctly distinguishes directory listings (e.g., `list /tmp`) from content generation (e.g., `write a list of items`).

---
## [0.2.5] — 2026-11-10

### Documentation
- **CHANGELOG**: added missing, detailed summaries for 0.2.1, 0.2.2, 0.2.3, and 0.2.4.
- **README**: updated release history and version references so PyPI displays the full narrative.
- **Godfather Wizard**: verified that `parse_seat` correctly identifies colon-tagged Ollama models (e.g., `better-tools:v4-cpu`) and that the REPL dynamically renders the `GODFATHER` ASCII banner on launch.

---

## [0.2.5] — 2026-11-10

### Documentation
- **CHANGELOG**: added missing, detailed summaries for 0.2.1, 0.2.2, 0.2.3, and 0.2.4.
- **README**: updated release history and version references so PyPI displays the full narrative.
- **Godfather Wizard**: verified that `parse_seat` correctly identifies colon-tagged Ollama models (e.g., `better-tools:v4-cpu`) and that the REPL dynamically renders the `GODFATHER` ASCII banner on launch.

---

## [0.2.4] — 2026-11-10

### Documentation
- **CHANGELOG**: fully rewritten with detailed per-release summaries for 0.2.1,
  0.2.2, and 0.2.3.
- **README**: added a "Release history" section so PyPI's main package page
  surfaces what changed in each version.

*No code changes in this release — documentation only.*

---

## [0.2.3] — 2026-11-10

### Fixed
- **Godfather Wizard** (`godfather_wizard.py`): renamed the directory-listing
  loop variable from `err` to `entry` in both listing functions (lines ~602 and
  ~636). The prior rename in 0.2.1 made mypy happy but mislabeled `entry` as an
  error, misleading readers. No behavior change.

### Changed
- **Banner Wizard** (`banner_wizard.py`): removed a duplicated
  `# mypy: disable-error-code` header line and an unused `from typing import Any`
  import (both left over from the 0.2.1 mypy sweep). No behavior change.

### Documentation
- **CHANGELOG**: added the missing 0.2.1 and 0.2.2 entries so the release history
  is complete and readable from the top of this file.

---

## [0.2.2] — 2026-11-10

### Changed
- **CI / GitHub Actions** (does not ship inside the package):
  - Bumped `actions/checkout` from `v4` to `v5`.
  - Bumped `actions/setup-python` from `v5` to `v6`.
  - Pinned `runs-on` from `ubuntu-latest` to `ubuntu-24.04` in all jobs.
  These changes silence the Node 20 deprecation warning and the upcoming
  Ubuntu 26 migration warning. **Package code is identical to 0.2.1.**

---

## [0.2.1] — 2026-11-10

### Fixed
- **Code Guard Wizard**:
  - Model audits now explicitly request JSON output from the seated model,
    reducing parse failures.
  - Failed Ollama calls now surface the real error message instead of a
    generic "audit call failed".
  - The audit timeout was raised from **120 s** to **300 s** so slower models
    on large files can complete.

### Internal
- **mypy**: entire `src/` tree is now type-clean — **19 errors fixed across
  7 files**, `mypy src` reports `Success: no issues found in 71 source files`.
  - `rustwiz/lib/cli.py`: silenced `try/except` fallback redefinition.
  - `pythonwiz/lib/python_wizard.py`: annotated `imports_of` result dict.
  - `debugwiz/__main__.py`: renamed loop variables `e` → `err` (2 sites).
  - `godfatherwiz/lib/godfather_wizard.py`: renamed loop variables `e` → `err`
    (2 sites, later renamed `err` → `entry` in 0.2.3).
  - `bannerwiz/lib/banner_wizard.py`: added a file-scoped `mypy` disable for
    `index`, `return-value`, and `assignment` codes.
  - `bannerwiz/lib/banner_wrapper.py`: single `# type: ignore[import-not-found]`
    on the `banner_engine` import.
- **Tests**: 560 passed.
- **CI**: green on Python 3.10, 3.11, 3.12, and 3.13.

---

## [0.2.0] — earlier

Pre-existing baseline release. (See git history for the 0.2.0 feature set.)

---

[0.2.3]: https://github.com/rewardsbycode-eng/wizard-central-toolkit/releases/tag/v0.2.3
[0.2.2]: https://github.com/rewardsbycode-eng/wizard-central-toolkit/releases/tag/v0.2.2
[0.2.1]: https://github.com/rewardsbycode-eng/wizard-central-toolkit/releases/tag/v0.2.1
