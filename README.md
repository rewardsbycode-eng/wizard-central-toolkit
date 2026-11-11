# Wizard Central Toolkit (`wizard-central-toolkit`)

> **The Sovereign Developer Utilities Fleet & AI Router**  
> Fast, local-first CLI tools built on the Python standard library, plus two small display libraries, designed for Linux development, system orchestration, and deterministic safety policy execution.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Validation Suite](https://img.shields.io/badge/Validation-13%2F13_Passed-brightgreen.svg)](#validation--testing)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

`wizard-central-toolkit` is a production-grade suite of 12 developer utilities that run locally with minimal overhead and deterministic output. Designed to operate standalone as individual CLI binaries or orchestrated through the **Godfather Wizard** and the **Wizarding Router** (`wiz`), every tool in this repository is fully functional, disk-verified, and CI-tested.

**Every command, documented:** [COMMANDS.md](COMMANDS.md) lists all 13 primary commands — 25 entry points counting the 12 aliases — and 147 subcommands, each with what it does.

**See it run:** [DEMO.md](DEMO.md) is the demo section — every feature tested live and documented from the real runs, from install check through the consent wall to the model codegen suite.

## 📋 Release history

Full changelog is in [CHANGELOG.md](https://github.com/rewardsbycode-eng/wizard-central-toolkit/blob/main/CHANGELOG.md).

### 0.2.8 — 2026-11-10

- **Docs:** this release history completed (0.2.4—0.2.7 added); CHANGELOG duplicate 0.2.5 entry removed; tagline corrected — the toolkit builds on the Python standard library plus two small display libraries; sampler roster count clarified (12 wizards ship here, 10 of them from the roster of 41).

- *No behavior changes.*

### 0.2.7 — 2026-11-10

- **Godfather Wizard:** `generate_text()` — generation intents (poems, stories) take a lightweight model call and answer in seconds on CPU-only hardware, instead of riding the full tool-loop prompt.

- **REPL:** `/stream_on` and `/stream_off` toggles.

### 0.2.6 — 2026-11-10

- **Godfather Wizard:** the consent wall now reads verb + object — composing text ("write a poem", "delete the second stanza") passes free; mutating real files ("delete ~/x.py") still asks twice.

- **Fixed:** path-bearing read intents (`list /tmp`) route to the directory lister, not the oracle.

### 0.2.5 — 2026-11-10

- **Godfather Wizard:** the seat parser checks the live Ollama roster first — a colon-tagged local model (`better-tools:v4-cpu`) seats as a local model instead of being misread as a cloud provider.

- **REPL:** dynamic banner, fitted to the terminal on every launch.

### 0.2.4 — 2026-11-10

- **Docs:** detailed CHANGELOG; this release-history section added.

- *No behavior changes.*

### 0.2.3 — 2026-11-10
- **Fixed:** Godfather Wizard — renamed a misleading variable in directory listing.
- **Changed:** Banner Wizard — removed duplicated mypy header and unused import.
- **Docs:** backfilled the missing 0.2.1 and 0.2.2 changelog entries.
- *No behavior changes.*

### 0.2.2 — 2026-11-10
- **CI only:** bumped GitHub Actions (`checkout@v5`, `setup-python@v6`), pinned `ubuntu-24.04`. No package code changes.

### 0.2.1 — 2026-11-10
- **Code Guard Wizard:** JSON output from model audits, real Ollama errors surfaced, timeout raised to 300 s.
- **mypy:** all 71 source files type-clean (19 errors fixed).
- **Tests:** 560 passed.

### 0.2.0 — earlier
- Initial public release baseline. See git history.
---

## 🌟 Fleet Inventory & Command Mapping

All 12 wizard modules on disk are active, registered, and disk-verified:

| Wizard | Direct Executable | Central Alias | Primary Functionality & Subcommands |
| :--- | :--- | :--- | :--- |
| **The Wizarding Router** | `wiz` | `wiz` | Central dispatcher & alias router (`banner`, `codeguard`, `debug`, `diff`, `json`, `python`, `read`, `rust`, `tmux`, `todo`, `write`) |
| **Godfather Wizard** | `godfather_wizard` | `wiz godfather_wizard` | Grand Master fleet supervisor, deterministic task routing, interactive REPL cockpit, and the model codegen suite (`/brainstorm`, `/build`, `/debug`, `/diff`) |
| **Code Guard Wizard** | `codeguard_wizard` | `wiz codeguard` | Static security scanner (`audit`, `fix`, `lang`, `roster`, `scan`, `watch`, `severity`, `explain`, `scaffold`) |
| **Debug Wizard** | `debug_wizard` | `wiz debug` | Diagnosis oracle (`trace`, `locate`, `classify`, `hotspot`, `timeline`, `imports`, `suggest`, `audit`, `report`) |
| **Diff Wizard** | `diff_wizard` | `wiz diff` | Change-truth doctor (`files`, `dirs`, `context`, `summary`, `word`, `same`, `reverse`) |
| **JSON Wizard** | `json_wizard` | `wiz json` | Standalone JSON doctor (`validate`, `pretty`, `compact`, `inspect`, `keys`, `get`, `diff`, `stats`, `merge`) |
| **Python Wizard** | `python_wizard` | `wiz python` | Standalone Python parser & health auditor (`check`, `outline`, `imports`, `complexity`, `loc`, `secrets`, `score`) |
| **Read Wizard** | `read_wizard` | `wiz read` | Read-only policy verb gate (`check`, `verbs`, `law`) |
| **Rust Wizard** | `rust_wizard` | `wiz rust` | Rust project checker (`check`, `build`, `run`, `test`, `clippy`, `fmt`, `doc`, `clean`, `law`, `version`) |
| **Tmux Wizard** | `tmux_wizard` | `wiz tmux` | Sovereign tmux session manager (`new`, `attach`, `kill`, `list`, `census`, `rename`, `capture`, `detach`, `law`, `version`) |
| **Todo Wizard** | `todo_wizard` | `wiz todo` | Task management wizard (`add`, `list`, `done`, `undo`, `note`, `oldest`, `overdue`, `stats`, `export`) |
| **Write Wizard** | `write_wizard` | `wiz write` | Consent wall for file writes (`propose`, `preview`, `commit`, `verify`, `rollback`, `protect`, `backups`) |

---

## 🛠 Usage Examples

### 1. The Wizarding Router (`wiz`) and the Godfather Wizard (`godfather_wizard`)
Execute sub-tools via `wiz` or inspect fleet state with `godfather_wizard`:
```bash
# Execute sub-tools via alias
wiz todo add "Refactor logger module"
wiz json validate config.json

# Godfather Wizard fleet supervision
godfather_wizard census
godfather_wizard status
godfather_wizard repl
```

Inside the REPL, the model-only codegen suite offers
`/brainstorm` (hands-off conversation), `/build` and `/debug`
(complete-content proposals shown as diffs and landed only
after the double ask, through the Write Wizard), and `/diff`
(review-only proposals). Per-task models are optional:
`godfather_wizard models` shows the roster and assignments, and
`godfather_wizard models set <task> <model>` stores them in
`~/.godfather/models.json`.

Six providers can seat a model. Ollama is the local seat —
no key, nothing leaves your machine. The other five (Meta
(Muse), Anthropic, OpenAI, Google, and DeepSeek) are cloud
seats you opt into with your own API key, read from your
environment at call time; a seat is assigned as
`provider:model` (for example `anthropic:claude-sonnet-4-5`).
The toolkit stays local-first: nothing is sent anywhere unless
you seat a cloud provider — and when you do, the prompts and,
for `/build`, `/debug`, and `/diff`, the file contents
involved go to that provider over HTTPS. Keys are never
stored in the toolkit, never journaled, and never printed;
`godfather_wizard models` reports only whether a key is set.
[PROVIDERS.md](PROVIDERS.md) is the setup guide: where to get
each provider's key, and how to install Ollama and pull your
first local models.

---

## Wizard Central Pro AI Modes Toolkit — still in the making

This free toolkit is the sampler: twelve local-first wizards
under Apache 2.0, yours to use and build on.

Not in the sampler: the Truth Wizard, the Repair Wizard,
the Ollama Wizard, the Whiteboard Wizard, the Manual
Wizard, and the Boot Wizard. They are part of the
**Wizard Central Pro AI Modes Toolkit**, still in the making:
a fleet growing toward 41 wizards; 70 AI modes that advise;
23 guard modes that bind; seat cards that cast; creations of
nine kinds — wizards, AI modes, tools, skills, tasks, guard
modes, scripts, seat cards, and projects; a sealed locker
(CVLT Arbiter) for a person's own creations; and a gated
bridge that opens only by a person's yes, asked twice — and
every crossing generates a receipt.

Pro is not released, and there is no signup yet. When it is
ready, this page will say where to find it.

## The full roster — all 41 wizards

Wizard Central's fleet counts 41 wizards. This sampler ships 12 wizards - 10 of them from that roster; the other 31 roster wizards live in the Wizard Central Pro AI Modes Toolkit, and the Tmux and Rust Wizards live only here.

| # | Wizard | Command | Where it lives |
| :--- | :--- | :--- | :--- |
| 1 | Banner Wizard | `banner_wizard` | **In this version** |
| 2 | Bash Wizard | `bashwiz` | Not in this version — only in Pro |
| 3 | Bootstrap Wizard | `bootstrapwiz` | Not in this version — only in Pro |
| 4 | Calendar Wizard | `calendarwiz` | Not in this version — only in Pro |
| 5 | Code Guard Wizard | `codeguard_wizard` | **In this version** |
| 6 | Command Line Wizard | `commandlinewiz` | Not in this version — only in Pro |
| 7 | Daemon Wizard | `daemonwiz` | Not in this version — only in Pro |
| 8 | Debug Wizard | `debug_wizard` | **In this version** |
| 9 | Diff Wizard | `diff_wizard` | **In this version** |
| 10 | Doc Wizard | `docwiz` | Not in this version — only in Pro |
| 11 | Dotfile Wizard | `dotfilewiz` | Not in this version — only in Pro |
| 12 | Exam Wizard | `examwiz` | Not in this version — only in Pro |
| 13 | Git Wizard | `gitwiz` | Not in this version — only in Pro |
| 14 | Grant Wizard | `grantwiz` | Not in this version — only in Pro |
| 15 | Help Wizard | `helpwiz` | Not in this version — only in Pro |
| 16 | JSON Wizard | `json_wizard` | **In this version** |
| 17 | Knowledge Wizard | `knowledgewiz` | Not in this version — only in Pro |
| 18 | Manual Wizard | `manualwiz` | Not in this version — only in Pro |
| 19 | Mapping Wizard | `mappingwiz` | Not in this version — only in Pro |
| 20 | MCP Wizard | `mcpwiz` | Not in this version — only in Pro |
| 21 | Mode-Manifesting Wizard | `mode-manifestingwiz` | Not in this version — only in Pro |
| 22 | Modelfile Wizard | `modelfilewiz` | Not in this version — only in Pro |
| 23 | Ollama Wizard | `ollamawiz` | Not in this version — only in Pro |
| 24 | Privacy Wizard | `privacywiz` | Not in this version — only in Pro |
| 25 | Python Wizard | `python_wizard` | **In this version** |
| 26 | Read Wizard | `read_wizard` | **In this version** |
| 27 | Repair Wizard | `repairwiz` | Not in this version — only in Pro |
| 28 | REPL Manager Wizard | `repl-managerwiz` | Not in this version — only in Pro |
| 29 | Requirements Wizard | `requirementswiz` | Not in this version — only in Pro |
| 30 | SQL Wizard | `sqlwiz` | Not in this version — only in Pro |
| 31 | Supreme Wizard | `supremewiz` | Not in this version — only in Pro |
| 32 | Test-Admission Wizard | `test-admissionwiz` | Not in this version — only in Pro |
| 33 | Todo Wizard | `todo_wizard` | **In this version** |
| 34 | Truthdwiz Wizard | `truthdwiz` | Not in this version — only in Pro |
| 35 | Truth Wizard | `truthwiz` | Not in this version — only in Pro |
| 36 | Voice Wizard | `voicewiz` | Not in this version — only in Pro |
| 37 | Whiteboard Wizard | `whiteboardwiz` | Not in this version — only in Pro |
| 38 | Write Wizard | `write_wizard` | **In this version** |
| 39 | Godfather Wizard | `godfather_wizard` | **In this version** |
| 40 | Bonus Wizard (planned) | `bonuswiz` | Not in this version — only in Pro |
| 41 | Keep Wizard (planned) | `keepwiz` | Not in this version — only in Pro |

Two of this sampler's own citizens do not appear on the
roster. **Tmux Wizard** (`tmux_wizard`) — in Pro, its session features
are absorbed into the Daemon Wizard's family, as an opt-in
feature. **Rust Wizard** (`rust_wizard`) — discontinued in the
Pro version; it ships in this free toolkit only.

## Names and aliases

A wizard's name-command is its full underscored form — that
is how each wizard is called by its whole name. The short
form is an alias: installed, fully working, and interchangeable
with the full form in every surface (same output, same exit
codes). The router's full name is the Wizarding Router; its
command is `wiz`.

| Wizard | Name-command | Alias |
| :--- | :--- | :--- |
| Godfather Wizard | `godfather_wizard` | `godfatherwiz` |
| Banner Wizard | `banner_wizard` | `bannerwiz` |
| Code Guard Wizard | `codeguard_wizard` | `codeguardwiz` |
| Debug Wizard | `debug_wizard` | `debugwiz` |
| Diff Wizard | `diff_wizard` | `diffwiz` |
| JSON Wizard | `json_wizard` | `jsonwiz` |
| Python Wizard | `python_wizard` | `pythonwiz` |
| Read Wizard | `read_wizard` | `readwiz` |
| Rust Wizard | `rust_wizard` | `rustwiz` |
| Tmux Wizard | `tmux_wizard` | `tmuxwiz` |
| Todo Wizard | `todo_wizard` | `todowiz` |
| Write Wizard | `write_wizard` | `writewiz` |

*A command is what you type. The name is what the project is.*
