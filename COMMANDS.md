# Wizard Central Toolkit — Command Reference

Every command the toolkit ships: the 13 primary commands — 25
entry points counting the aliases — all 147 subcommands, the
banner modes, the router's aliases, and the Godfather Wizard
REPL's slash commands — each with what it does. A wizard's
name-command is its full underscored form (`godfather_wizard`);
its short form (`godfatherwiz`) is an alias, listed once in the
README's "Names and aliases" section and working everywhere
the full form does.
Compiled from the wizards' own `--help` output, the REPL's own
`/help`, and the Banner Wizard's source (0.2.0).

## The census — how the numbers stack

- **25 entry points** are installed on the PATH: the 13 primary
  commands — `wiz` plus the 12 wizards under their full-form
  name-commands — and the 12 short alias commands beside them.
- **147 subcommands** sit under 11 of them (the Banner Wizard works
  differently — see its entry).
- **6 display modes** on the Banner Wizard (`--demo`, `--themes`,
  `--styles`, `--sizes`, `--fonts`, `--interactive`).
- **11 short aliases** through the `wiz` router.
- **39 slash command forms** inside the Godfather Wizard REPL
  (`/diff` carries both its legacy two-file comparison and the
  codegen review form).

Counted strictly as typed commands and subcommands:
13 + 147 = **160**, before banner modes, aliases, and slashes.
Counting every way to invoke the fleet on the primary surface:
160 + 6 + 11 + 39 = **216**. The aliases re-offer the same
surface under the short spellings — 12 entry points, the same
147 subcommands, and the same 6 banner modes — 165 more typed
forms, **381** in all.

---

## The Wizarding Router — `wiz`

The router's full name is the Wizarding Router; its command
is `wiz`, and the command does not change.

`wiz [--json] <tool> [args...]` — runs any fleet wizard by its
full-form name or its alias; `--json` emits the output as JSON;
`--version` prints the installed package version. It also
answers to 11 short aliases: `banner`, `codeguard`, `debug`,
`diff`, `json`, `python`, `read`, `rust`, `tmux`, `todo`,
`write` (each = the wizard of that stem).

## Godfather Wizard — `godfather_wizard`, the Grand Master (22)

Fleet dispatcher and REPL. Invokes siblings where they live;
the truth senses (brief, listing, read, head, find, du, stat,
symlinks) live in-house — absorbed from the Truth Wizard, whose office
was the Godfather Wizard's own Law 2 anchor all along.

| Command | What it does |
|---|---|
| `audit <path>` | truth anchor (internal senses) + Code Guard Wizard audit |
| `task <intent>` | Todo Wizard intake |
| `run <directive>` | deterministic keyword router — read-class and staging routes run free; a write-class route asks twice (plain ask, then a typed confirmation naming the action) before it executes; unmapped mutation intent is refused at the wall |
| `routes` | print routing table |
| `fleet` | census of installed sibling wizards |
| `law` | print FATHER LAW |
| `truth <path>` | anchor ground truth (internal senses) |
| `diagnose <dir>` | Debug Wizard audit + classify on the worst file |
| `heal <file>` | Debug Wizard audit, then propose — the fix is staged via the Write Wizard, never applied |
| `status` | fleet-wide health check |
| `repl` | launch the interactive REPL cockpit |
| `siblings` | list all registered citizens |
| `verify <wizard>` | single citizen health check |
| `consent <file>` | force the Write Wizard's commit prompt |
| `schedule <intent>` | queue task |
| `queue` | show scheduled tasks |
| `history` | run history across delegations |
| `stats` | fleet-wide execution counts |
| `versions` | law drift detection |
| `help [command]` | full usage, or usage for one subcommand |
| `census` | full fleet roster |
| `models` | show the six providers, the live Ollama roster, and the per-task assignments in `~/.godfather/models.json`; `models set <task> <seat>` and `models unset <task>` manage assignments for `default`, `brainstorm`, `build`, `debug`, `diff`, and `audit` — a seat is a bare Ollama model name, or `provider:model` for a cloud provider |

Exit codes: 0 ok · 1 failed · 2 out of scope.

## Banner Wizard — `banner_wizard`, ASCII banner wizard

`banner_wizard <words...>` renders the words as a large ASCII
banner (pyfiglet; fonts auto-discovered at runtime — typically
571+, with 18 style presets). `--subtitle TEXT` adds a subtitle
line under the banner. Modes: `--demo` (demonstration),
`--themes` (theme gallery), `--styles` (the 18 presets),
`--sizes` (size behaviour), `--fonts` (font list),
`--interactive` (guided interactive mode).

## Code Guard Wizard — `codeguard_wizard`, code audit wizard (9)

| Command | What it does |
|---|---|
| `audit` | audit a file or directory, print plain verdict — two engines: the model seat when one is served, the built-in static rules otherwise; the static rules cover Python (CG001–CG009) and Rust (RS001–RS007, `.rs` files and `Cargo.toml`), dispatched by extension in a single mixed audit; `--engine static\|model` chooses, and the output opens with the engine line |
| `fix` | model engine: generate repaired code for a file (preview; `--write`/`--out` stage the fix via the Write Wizard, ask twice at the terminal — plain yes, then a typed confirmation naming the file — and land only through the Write Wizard's commit). static engine: stage the one deterministic rewrite (bare `except:` → `except Exception:`) through the Write Wizard — it never writes a file itself; every other finding is listed as needing a person or the model engine |
| `lang` | detect language of a file |
| `roster` | show the engines: the static rule roster (always available) and the live model seats when a daemon serves them |
| `scan` | audit sweep on a file or directory (static engine: findings one per line) |
| `watch` | diff-since-last-audit: re-run audit, report changes |
| `severity` | the findings grouped by severity |
| `explain` | explain a static rule (`explain CG002`) or the finding at a line (`explain <file> <line>`) |
| `scaffold` | generate unit-test skeleton for file |

## Debug Wizard — `debug_wizard`, the diagnosis oracle (22)

| Command | What it does |
|---|---|
| `law` | print the DEBUG LAW alone |
| `trace <file>` | traceback autopsy |
| `locate <dir> <pattern>` | find files with error pattern |
| `classify <file>` | error type breakdown |
| `stack [file]` | stack digest of a traceback (file or stdin): exception, frame chain with project/library marks, deepest project frame, repeated frames flagged as suspected recursion |
| `count <dir>` | errors by category |
| `hotspot <dir>` | files with most errors |
| `timeline <dir>` | error frequency by mtime |
| `imports <file>` | missing import detection |
| `names <file>` | undefined name detection |
| `signatures <file>` | signature mismatch detection |
| `suggest <file>` | heuristic fix suggestion |
| `propose <file>` | stage fix via the Write Wizard |
| `preview <file>` | show staged proposal |
| `explain <file>` | human-readable explanation |
| `audit <dir>` | full error census |
| `report <dir>` | JSON report for CI/CD |
| `log <dir>` | write error log (staged via the Write Wizard) |
| `ignore <path>` | add to ignore list |
| `ignored` | show ignored paths |
| `stats` | error census of the current directory |
| `versions` | law/version drift detection |

## Diff Wizard — `diff_wizard`, change-truth doctor (7)

| Command | What it does |
|---|---|
| `files <a> <b>` | unified diff of two files |
| `dirs <a> <b>` | compare directory trees |
| `context <N> <a> <b>` | unified diff with N context lines |
| `summary <a> <b>` | diff statistics without full output |
| `word <a> <b>` | word-level diff |
| `same <a> <b>` | exit 0 if identical, 1 if different (silent) |
| `reverse <a> <b>` | diff b → a (swap sides) |

## JSON Wizard — `json_wizard`, JSON doctor (9)

| Command | What it does |
|---|---|
| `validate <file\|->` | check JSON validity, line/col on failure |
| `pretty <file\|->` | pretty-print to stdout |
| `compact <file\|->` | minify to one line |
| `inspect <file\|->` | structural summary |
| `keys <file\|->` | top-level keys |
| `get <file\|-> <path>` | dotted-path value lookup (a.b.0.c) |
| `diff <a> <b>` | structural diff of two JSON docs |
| `stats <file\|->` | type census: depths, counts |
| `merge <a> <b>` | deep merge (b wins) to stdout |

## Python Wizard — `python_wizard`, Python doctor (22)

Parse only — never executes the code it reads.

| Command | What it does |
|---|---|
| `check <file\|dir>` | syntax validation (the fleet gate) |
| `entry <file>` | shebang + interpreter validation |
| `outline <file>` | symbol map: classes/functions + line numbers |
| `imports <file>` | stdlib/third_party/local/relative inventory |
| `todos <file>` | TODO/FIXME/XXX/BUG/HACK markers |
| `deadcode <file>` | defined-but-unreferenced candidates (heuristic) |
| `complexity <file>` | branch count per function, hottest first |
| `loc <file>` | lines/code/blank/comment/function stats |
| `docstrings <file>` | defs missing docstrings |
| `explain <file>` | syntax error with source lines shown |
| `shebangs <dir>` | sweep tree, validate every shebang |
| `deps <file>` | third-party imports as requirements list |
| `callmap <file>` | who-calls-whom per function |
| `longest <file>` | functions ranked by length |
| `excepts <file>` | bare/broad except handlers + swallows |
| `secrets <file>` | hardcoded credential patterns — file, line and pattern kind reported, values redacted by default; `--show-secrets` prints the values (deliberate opt-in) |
| `mainguard <file>` | has `__main__` guard? |
| `globals <file>` | module-level mutable state audit |
| `magic <file>` | suspicious numeric literals |
| `compare <a> <b>` | structural symbol diff of two files |
| `tree <dir>` | directory aggregate summary |
| `score <file>` | composite health score 0–100 |

## Read Wizard — `read_wizard`, read-only mode policy engine (3)

| Command | What it does |
|---|---|
| `check "<raw shell command>"` | verdict on a shell command: ALLOW / DENIED |
| `verbs` | dump the allow/deny tables |
| `law` | print the READ LAW alone |

Exit: 0 = allow · 1 = denied · 2 = usage error.

## Rust Wizard — `rust_wizard`, Rust project checker (10)

| Command | What it does |
|---|---|
| `check <file.rs\|dir>` | check a Rust file or project directory |
| `build <crate-dir>` | cargo check a crate directory |
| `run <crate-dir>` | build and run the crate's binary |
| `test <crate-dir>` | cargo test |
| `clippy <crate-dir>` | cargo clippy lints |
| `fmt <crate-dir>` | cargo fmt --check (reports drift only, never reformats) |
| `doc <crate-dir>` | cargo doc --no-deps |
| `clean <crate-dir>` | cargo clean (removes the crate's target/ only) |
| `law` | print the RUST LAW alone |
| `version` | print the version |

## Tmux Wizard — `tmux_wizard`, tmux session manager (10)

| Command | What it does |
|---|---|
| `new <name> [dir]` | create session (default cwd) |
| `attach <name>` | join session |
| `kill <name>` | destroy session |
| `list` | names of live sessions |
| `census` | health of every session |
| `rename <old> <new>` | rename session |
| `capture <name> [lines]` | print a pane's recent output (read-only) |
| `detach <name>` | detach clients; the session keeps running |
| `law` | print the TMUX LAW alone |
| `version` | print the version |

## Todo Wizard — `todo_wizard`, todo wizard (11)

| Command | What it does |
|---|---|
| `add <text>` | add a task (default priority normal) |
| `list` | list all tasks |
| `done <id>` | complete a task |
| `undo <id>` | reopen a completed task |
| `note <id> <text>` | append a progress note to a task |
| `oldest` | show the stalest pending task |
| `overdue [days]` | pending tasks older than N days (default 7) |
| `archive-done` | move completed tasks to archive |
| `rm <id>` | remove a task |
| `stats` | JSON summary |
| `export` | full JSON dump |

## Write Wizard — `write_wizard`, the consent wall for file writes (22)

| Command | What it does |
|---|---|
| `propose <path>` | stage content (reads stdin) in quarantine |
| `preview <path>` | gate + diff the staged draft vs disk |
| `commit <path>` | ask Governor consent, write, verify |
| `pending` | list quarantined drafts |
| `law` | print the WRITE LAW alone |
| `status <path>` | draft state: bytes, age, target |
| `diff <path>` | disk vs draft diff alone |
| `verify <path>` | gate + verification, zero consent |
| `explain <path>` | would-commit verdict with reasons |
| `discard <path>` | burn a draft ('y'-gated, journaled) |
| `guard` | gate sweep over every pending draft |
| `audit` | quarantine census: drafts, orphans |
| `ledger` | full write journal |
| `history <path>` | journal filtered to one target |
| `stats` | counts: staged, written, refused |
| `protect <path>` | forbid writes — absolute refusal |
| `unprotect <path>` | lift a protection (Governor only) |
| `protected` | list protected paths |
| `backups` | list pre-write safety copies |
| `rollback <path>` | restore from backup ('y'-gated) |
| `purge-old <days>` | burn drafts older than N days ('y'-gated) |
| `law-digest` | sha256 of WRITE LAW (drift detection) |

Exit codes: 0 ok · 1 refused/failed · 2 usage error.

---

## Inside the Godfather Wizard's REPL — 39 slash command forms

From the REPL's own `/help`. Every slash dispatches inside the
box: the truth slashes are served by the Godfather Wizard's absorbed
senses, in-house; `/fix` and `/heal` run the Godfather Wizard's own heal
chain (staging only); `/models` answers from the configured
seats. Plain (non-slash) text tries the deterministic router
first — read-class and staging routes run free, a write-class
route asks twice before executing — and reaches the model
oracle only when unmapped and a seat is actually serving;
seatless unmapped text is answered "out of scope".

### The codegen suite — model proposals, human consent

Four model-only modes inherit devrepl's per-mode shape: each
mode has its own system prompt and may have its own model.
Assignments live in `~/.godfather/models.json` under `default`,
`brainstorm`, `build`, `debug`, `diff`, and `audit`; a task uses
its own assignment first, then `default`, then the live roster
pick. One model can therefore run everything, or the user can
assign a different model per task. An assigned model that is
not serving is reported honestly and is never silently replaced.
With no live seat, each codegen slash gives one plain line and
changes nothing.

An assignment is a seat. A bare name (`llama3.2:1b`) is an
Ollama model and must be in the live roster. A `provider:model`
name (`anthropic:claude-sonnet-4-5`) seats that model at one of
the five cloud providers below, and is configured when the
provider's key is in the environment. A cloud seat whose key is
missing is no seat at all, and the answer names the missing
variable. Every model-authored proposal names its seat:
`seat: <provider> · <model>`.

The model authors complete content, but it never acts on its
own. `/build` and `/debug` show the full unified diff, stage the
exact proposal through the Write Wizard, ask twice — a plain yes, then
a typed confirmation naming the file — and only then land it
through the Write Wizard's commit and journal a `CODEGEN` event. There is
no auto mode. `/diff` is review-only: it stages nothing and asks
nothing, and remembers the proposal for a later `/build` or
`/debug` with the same path and instruction. `/brainstorm` is
conversation only — its tool channel is off, and a `TOOL:` line
from the seat is treated as text.

The `/diff` token has two forms. `/diff <file-a> <file-b>` —
where the second argument is another file — remains the Diff Wizard's
comparison. The codegen review form is `/diff <path>
<instruction...>`: longer instructions are always codegen, and
a one-word instruction is codegen when it does not name a
second file.

### Providers — six seats

The toolkit is local-first, and Ollama is the seat that ships
in the box: a model on your own machine, no key, nothing
leaving it. The five cloud providers are your opt-in — each is
seated only with your own API key, read from your environment
at call time:

| Provider id | Display name | Key environment variable | Endpoint host |
|---|---|---|---|
| `ollama` | Ollama | — (local, no key) | `127.0.0.1:11434` |
| `meta` | Meta (Muse) | `MODEL_API_KEY` (fallback `META_API_KEY`) | `api.meta.ai` |
| `anthropic` | Anthropic | `ANTHROPIC_API_KEY` | `api.anthropic.com` |
| `openai` | OpenAI | `OPENAI_API_KEY` | `api.openai.com` |
| `google` | Google | `GEMINI_API_KEY` (fallback `GOOGLE_API_KEY`) | `generativelanguage.googleapis.com` |
| `deepseek` | DeepSeek | `DEEPSEEK_API_KEY` | `api.deepseek.com` |

The mechanism, stated plainly: when a cloud seat is used, the
prompts — and, for `/build`, `/debug`, and `/diff`, the file
contents involved — are sent to that provider over HTTPS.
That is what a cloud seat *is*; nothing is sent when the seat
is Ollama, and no cloud call happens until you assign one.
Keys live only in your environment: they are never stored in
the Godfather Wizard's bank, never journaled, and never printed —
`godfather_wizard models` reports only whether a key is set.
For a cloud seat, "configured" means the key is present; the
first real call is the proof the seat works, and its errors
come back as honest lines (status and the provider's message),
never tracebacks. [PROVIDERS.md](PROVIDERS.md) is the setup
guide: where each key comes from, and how to set up local
models with Ollama.

| Slash | Dispatches to |
|---|---|
| `/truth` | `godfather_wizard` brief (internal senses) |
| `/ls` | `godfather_wizard` listing (internal senses) |
| `/read` | `godfather_wizard` read (internal senses) |
| `/pycheck` | `python_wizard` check |
| `/fix` | `godfather_wizard` heal (`debug_wizard` audit → propose, staging only) |
| `/heal` | `godfather_wizard` heal (`debug_wizard` audit → propose, staging only) |
| `/todo` | `todo_wizard` add |
| `/todos` | `todo_wizard` list |
| `/tasks` | `todo_wizard` list |
| `/diff <file-a> <file-b>` | `diff_wizard` files (legacy two-file comparison form) |
| `/models` | `godfather_wizard` models (live roster + per-task assignments) |
| `/brainstorm [words]` | codegen brainstorm mode — model conversation with the tool channel off; `/brainstorm end` leaves |
| `/build <path> <instruction...>` | codegen build — the seat proposes complete content; diff → `write_wizard` staging → double ask → `write_wizard` commit |
| `/debug <path> [words]` | codegen debug — the seat receives the file plus `python_wizard` check context for Python files; same diff and double-ask landing as `/build` |
| `/diff <path> <instruction...>` | codegen review — show the seat's proposed diff only; stage nothing, ask nothing, remember the proposal |
| `/banner` | `banner_wizard` |
| `/codeguard` | `codeguard_wizard` |
| `/json` | `json_wizard` |
| `/rust` | `rust_wizard` |
| `/tmux` | `tmux_wizard` |
| `/write` | `write_wizard` |
| `/verbs` | `read_wizard` verbs |
| `/audit` | `debug_wizard` audit |
| `/diag` | `debug_wizard` classify |
| `/bins` | `godfather_wizard` symlinks (internal senses) |
| `/history` | `godfather_wizard` history |
| `/stats` | `godfather_wizard` stats |
| `/routes` | `godfather_wizard` routes |
| `/fleet` | `godfather_wizard` fleet |
| `/law` | `godfather_wizard` law |
| `/help` | `godfather_wizard` help |
| `/status` | `godfather_wizard` status |
| `/census` | `godfather_wizard` census |
| `/voices` | pick voice (numbered dropdown) |
| `/model` | pick model (numbered dropdown) |
| `/more-commands` | full fleet arsenal (all citizens) |
| `/wiz <name> [args]` | run any installed wizard by name |
| `/quit`, `/exit` | leave the REPL |

---

*If a wizard's help and this page ever disagree, the help is
the authority — run `<wizard> --help` and trust it.*
