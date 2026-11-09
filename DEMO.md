# Wizard Central Toolkit — Demo

This is the toolkit's demo section: every feature below was **run
live** and is **documented as it ran** — the exact commands, and the
real output they produced, as guidance for using the toolkit well.

A command is what you type. The name is what the project is. Each
wizard is presented by its full name — Godfather Wizard, Code Guard
Wizard, and so on — and called by its full-form command
(`godfather_wizard`, `codeguard_wizard`, …). The short forms
(`godfatherwiz`, `codeguardwiz`, …) are aliases: they exist, they
work, and they are listed once, as aliases, in the router section
below.

## How this demo was run — and what it does not claim

- **Fresh install.** The toolkit was installed into a brand-new
  virtual environment from the package source (non-editable
  install), the environment's `bin` directory was put on `PATH`,
  and every command below was run from that install — not from a
  source checkout.
- **Sandbox home.** All runs used a throwaway `HOME`, so every
  bank, journal, and quarantine you see was created fresh by the
  commands themselves. Paths in the output are the demo machine's;
  on your machine they will be your own home directory.
- **A fixture workspace.** The runs work on a small prepared
  directory: `flawed.py` (a module with deliberate flaws — a
  hardcoded key, `shell=True`, an `eval()`, a bare `except`),
  `syntax.py` (which does not compile), `crasher.py` and its real
  traceback in `trace.txt`, two JSON files and one broken one, a
  pair of text files that differ, two directories that differ, a
  small Rust crate, and copies of the flawed module for the runs
  that change files.
- **No live model seat on the demo machine.** This machine has no
  Ollama daemon and no cloud API keys, and this demo does not
  pretend otherwise. Where a feature needs no seat, you see it run
  for real. Where a feature needs a seat, you see two things: the
  **seatless behavior, as-run** (the toolkit says plainly that no
  seat is serving — that is real behavior, not a gap in the demo),
  and, in the "Seats at work" chapter near the end, the same
  features run against a **stub seat** — a small local test server
  that answers in Ollama's shape with pre-written replies. Stub
  sections are labelled wherever they appear. Nothing produced by
  the stub is presented as a live model's work.
- **The completing proof is yours.** The seat-dependent features
  are proven end-to-end here against the stub; the run that
  completes the proof is the same commands on your machine, with
  your local model seated — see [PROVIDERS.md](PROVIDERS.md) for
  seating one. The full command reference is
  [COMMANDS.md](COMMANDS.md).

Outputs are shown verbatim, trimmed only for length (marked with
`[…]` where a long listing is shortened). Exit codes appear in
brackets after each run. Colour is stripped: the toolkit colours
the display, never the payload, and this document is payload.

---

## 1. Install check

After installing (`pip install wizard-central-toolkit`), the first
two things to verify are that the router answers and that all 25
entry points — 13 primary commands and 12 short aliases — landed
on your `PATH`:

```
$ wiz --version
wiz 0.2.0
[exit 0]

$ ls ~/workspace/ds/venv/bin | grep -E "wiz"
banner_wizard
bannerwiz
codeguard_wizard
codeguardwiz
debug_wizard
debugwiz
diff_wizard
diffwiz
godfather_wizard
godfatherwiz
json_wizard
jsonwiz
python_wizard
pythonwiz
read_wizard
readwiz
rust_wizard
rustwiz
tmux_wizard
tmuxwiz
todo_wizard
todowiz
wiz
write_wizard
writewiz
[count: 25 entry points]
```

Every entry point answers `help` and `--help` with the same full
listing, at exit code 0. The Godfather Wizard's is the longest —
it is the fleet's dispatcher:

```
$ godfather_wizard help
Godfather Wizard — the Grand Master, fleet dispatcher & REPL
alias: godfatherwiz
usage: godfather_wizard <command> [args]

CLI Commands:
  godfather_wizard audit <path>       truth anchor + codeguard_wizard audit
  godfather_wizard task <intent>      todo_wizard intake
  godfather_wizard run <directive>    deterministic keyword router
  godfather_wizard routes             print routing table
  godfather_wizard fleet              bin-lane census
  godfather_wizard law                print FATHER LAW
  godfather_wizard truth <path>       anchor ground truth (internal senses)
  godfather_wizard diagnose <dir>     debug_wizard audit + classify
  godfather_wizard heal <file>        debug_wizard propose → write_wizard wall
  godfather_wizard status             fleet-wide health check
  godfather_wizard repl               launch interactive REPL cockpit
  godfather_wizard siblings           list all registered citizens
  godfather_wizard verify <wizard>    single citizen health check
  godfather_wizard consent <file>     force write_wizard commit prompt
  godfather_wizard schedule <intent>  queue task
  godfather_wizard queue              show scheduled tasks
  godfather_wizard history            run history across delegations
  godfather_wizard stats              fleet-wide execution counts
  godfather_wizard versions           law drift detection
  godfather_wizard help [command]     full usage, or one subcommand's usage
  godfather_wizard census             full fleet roster
  godfather_wizard models             show providers, live seats + assignments
  godfather_wizard models set <task> <model>
                                  assign a seat to default, brainstorm,
                                  build, debug, diff, or audit — a bare
                                  Ollama model name, or provider:model
                                  (ollama, meta, anthropic, openai,
                                  google, deepseek)
  godfather_wizard models unset <task>
                                  remove a per-task model assignment

exit codes: 0 ok | 1 failed | 2 out of scope
[exit 0]
```

---

## 2. The Wizarding Router — `wiz`

The router's name is the **Wizarding Router**. It is not a wizard;
it routes. `wiz <wizard> [args...]` dispatches to any fleet member
by its full-form command, by its short alias, or by the router's
own short names — and with `--json` it wraps the result as JSON
for other programs. Run it bare to see the whole map:

```
$ wiz
The Wizarding Router — the fleet's dispatcher
usage: wiz [--json] <tool> [args...]

options:
  -h, --help       show this help message
  --version        show the installed version
  --json           emit command output as JSON

available tools: banner_wizard, codeguard_wizard, debug_wizard, diff_wizard, godfather_wizard, json_wizard, python_wizard, read_wizard, rust_wizard, tmux_wizard, todo_wizard, write_wizard

aliases (short forms — the same wizards, shorter typing):
  bannerwiz    alias of banner_wizard
  codeguardwiz alias of codeguard_wizard
  debugwiz     alias of debug_wizard
  diffwiz      alias of diff_wizard
  godfatherwiz alias of godfather_wizard
  jsonwiz      alias of json_wizard
  pythonwiz    alias of python_wizard
  readwiz      alias of read_wizard
  rustwiz      alias of rust_wizard
  tmuxwiz      alias of tmux_wizard
  todowiz      alias of todo_wizard
  writewiz     alias of write_wizard

router aliases:
  banner       banner_wizard
  codeguard    codeguard_wizard
  debug        debug_wizard
  diff         diff_wizard
  json         json_wizard
  python       python_wizard
  read         read_wizard
  rust         rust_wizard
  tmux         tmux_wizard
  todo         todo_wizard
  write        write_wizard
[exit 0]
```

That aliases list is the one place the short forms are presented:
they are typing shortcuts, never the wizards' names. The full
name map:

| Wizard | Full-form command | Short alias |
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

Routing, three ways to reach the same wizard, and the JSON form:

```
$ wiz python_wizard check flawed.py
[OK] flawed.py
[exit 0]

$ wiz python check flawed.py
[OK] flawed.py
[exit 0]

$ wiz --json json_wizard validate data.json
{
  "tool": "json_wizard",
  "args": [
    "validate",
    "data.json"
  ],
  "exit_code": 0,
  "stdout": "[OK] valid JSON (root type: dict)\n",
  "stderr": ""
}
[exit 0]

$ wiz todo_wizard list
[exit 0]

$ wiz write_wizard law-digest
{
  "law_sha256": "e07d0d0a27352ecd5838522f78937e94fee3829794e86ef5bdadc2ae55c6b726",
  "law_chars": 800,
  "law_lines": 12
}
[exit 0]
```

(The Todo Wizard's list is empty here because nothing has been
added yet — the Godfather Wizard's task intake, next, is what
puts the first item on it.)

---

## 3. Godfather Wizard — `godfather_wizard`

The fleet's dispatcher and supervisor. It re-implements nothing:
it anchors facts with its own senses, then delegates to the
sibling wizard that owns the work, and every dispatch is
journaled. Reach for it when you want the fleet checked as a
whole, a directory understood before anyone touches it, or a
multi-step job (diagnose → propose → consent) run as one chain.

### The fleet, four ways

```
$ godfather_wizard fleet
[OK] 13 sibling wizards installed
  banner_wizard
  codeguard_wizard
  debug_wizard
  diff_wizard
  godfather_wizard
  json_wizard
  python_wizard
  read_wizard
  rust_wizard
  tmux_wizard
  todo_wizard
  wiz
  write_wizard
[exit 0]

$ godfather_wizard census
[OK] 13 certified citizens on the fleet
  #01  banner_wizard
  #02  codeguard_wizard
  #03  debug_wizard
  #04  diff_wizard
  #05  godfather_wizard
  #06  json_wizard
  #07  python_wizard
  #08  read_wizard
  #09  rust_wizard
  #10  tmux_wizard
  #11  todo_wizard
  #12  wiz
  #13  write_wizard
[exit 0]

$ godfather_wizard status
[OK] banner_wizard reachable
[OK] codeguard_wizard reachable
[OK] debug_wizard reachable
[OK] diff_wizard reachable
[OK] godfather_wizard reachable
[OK] json_wizard reachable
[OK] python_wizard reachable
[OK] read_wizard reachable
[OK] rust_wizard reachable
[OK] tmux_wizard reachable
[OK] todo_wizard reachable
[OK] wiz reachable
[OK] write_wizard reachable
[exit 0]

$ godfather_wizard verify python_wizard
[OK] python_wizard healthy
[exit 0]
```

(`siblings` prints the same thirteen names as a numbered list.)

### Truth first: the senses

Before any chain acts, the Godfather Wizard anchors ground truth
with its own built-in senses — brief, listing, head, find, du,
stat, symlinks. `truth` on a directory and on a file:

```
$ godfather_wizard truth .
[BRIEF] .
type: directory
entries: 15 (3 dirs, 12 files, 0 symlinks)
size: 3649 bytes (3.6 KB) across 20 files
listing:
  after.txt
  before.txt
  broken.json
  crasher.py
  crate/
  data.json
  data2.json
  dirA/
  dirB/
  flawed.py
  hello.rs
  legacy.py
  modelcheck.py
  syntax.py
  trace.txt
[exit 0]

$ godfather_wizard truth flawed.py
[BRIEF] flawed.py
type: file
size: 696 bytes
lines: 34
[exit 0]
```

### The routing table

Plain-language work in the REPL (section 15) is routed by this
deterministic keyword table — no model involved in the choice:

```
$ godfather_wizard routes
  syntax/pycheck            -> python_wizard check
  diff/compare              -> diff_wizard files
  json/validate             -> json_wizard validate
  list/listing/whatshere    -> godfather_wizard listing
  models/ollama             -> godfather_wizard models
  todos/tasklist            -> todo_wizard list
  tmux/sessions             -> tmux_wizard list
  symlinks/bins             -> godfather_wizard symlinks
  diag/audit                -> debug_wizard audit
  heal/repair               -> godfather_wizard heal
[exit 0]
```

### Diagnose and heal

`diagnose` runs the Debug Wizard's audit over a directory and
classifies the worst file it finds. `syntax.py` does not compile,
so the workspace is 4/5 healthy:

```
$ godfather_wizard diagnose .
--- PHASE 1: debug_wizard audit ---
[HEALTH] 4/5 (80.0%)
[FAIL] 1 files with errors
--- PHASE 2: debug_wizard classify syntax.py ---
[SUMMARY] 1 errors
  SyntaxError: 1
[exit 1]
```

`heal` chains audit → proposal. It is precise about its patient:
asked to heal a file that has no compile errors, it says so and
stages nothing —

```
$ godfather_wizard heal flawed.py
--- PHASE 1: debug_wizard audit ---
[HEALTH] 4/5 (80.0%)
[FAIL] 1 files with errors
[OK] flawed.py shows no errors — nothing to heal in it
[exit 0]
```

— and asked to heal the file that *is* sick, it stages the Debug
Wizard's fix proposal into the Write Wizard's quarantine. The
file itself is untouched; the commit keystroke is never the
Godfather Wizard's to give:

```
$ godfather_wizard heal syntax.py
--- PHASE 1: debug_wizard audit ---
[HEALTH] 4/5 (80.0%)
[FAIL] 1 files with errors
--- PHASE 2: debug_wizard propose syntax.py ---
[STAGED] fix proposal for syntax.py — 482886e03d950512.draft -> /home/hatch/workspace/ds/home/.debug-wizard/fix_syntax.txt (55 chars quarantined)
preview it: debug_wizard preview syntax.py
handoff: write_wizard commit /home/hatch/workspace/ds/home/.debug-wizard/fix_syntax.txt   # your keystroke, Governor
[exit 0]
```

`consent` exists to force the Write Wizard's commit prompt for a
staged file. With nothing staged for `flawed.py`, it does not
invent a prompt — it prints the keystroke that would be yours:

```
$ printf "n\n" | godfather_wizard consent flawed.py
write_wizard commit flawed.py   # your keystroke, Governor
[exit 0]
```

### The audit chain

`audit` anchors the truth brief first, then delegates to the Code
Guard Wizard (its static engine here — section 5; the model
engine is section 18):

```
$ godfather_wizard audit flawed.py
--- PHASE 1: truth anchor ---
[BRIEF] flawed.py
type: file
size: 696 bytes
lines: 34
--- PHASE 2: codeguard_wizard audit ---
engine: static (built-in rules)
[OK] flawed.py (python, static rules)
     findings: HIGH=3 MEDIUM=1 LOW=2
     [HIGH] CG002 hardcoded-secret (line 7) — string literal assigned to 'API_KEY'
     [LOW] CG009 todo-marker (line 9) — TODO marker left in the code
     [LOW] CG009 todo-marker (line 13) — TODO marker left in the code
     [HIGH] CG004 shell-execution (line 14) — subprocess call with shell=True
     [HIGH] CG003 eval-exec (line 19) — eval() executes a string as code
     [MEDIUM] CG007 bare-except (line 25) — bare except: catches everything, names nothing
     verdict: [FAIL] 3 high-severity finding(s) present
[FAIL] audit pipeline complete
[exit 1]
```

### Tasks, schedule, journal

`task` is the Todo Wizard's intake door; `schedule` queues an
intent for later; `history` and `stats` read the journal every
dispatch writes to:

```
$ godfather_wizard task "water the demo plants"
--- todo_wizard intake ---
[+] #1 water the demo plants
[OK] task pipeline complete
[exit 0]

$ godfather_wizard schedule "write the demo report"
[OK] task scheduled: id=66945, intent=write the demo report
[exit 0]

$ godfather_wizard queue
[queued] 66945 — write the demo report
[exit 0]

$ godfather_wizard history
2026-11-09T12:35:11  SCHEDULED        66945 write the demo report
[exit 0]

$ godfather_wizard stats
{'SCHEDULED': 1}
[exit 0]

$ godfather_wizard versions
father_law_sha256: 72a4b122bb8c69b9775139037bd344d91cf580f4197f06a6c8857dcc06a1fe2c
[exit 0]
```

### The law it runs under

Every wizard carries its law in the open. The Godfather Wizard's
is the fleet's constitution — delegation, truth first, the
consent wall, deterministic routes:

```
$ godfather_wizard law
FATHER LAW (Godfather Wizard, the Grand Master)
1. DELEGATION: re-implements nothing; invokes siblings where
   they live: the bin lane (~/bin) first, the installed package
   second; a sibling found nowhere is honestly absent.
2. TRUTH FIRST: multi-step runs anchor facts with the Godfather Wizard's own senses before acting.
3. CONSENT WALL: mutations are staged via write_wizard propose; the
   Godfather Wizard never supplies the 'y'. The commit keystroke
   belongs to the Governor.
4. DETERMINISTIC ROUTES: run dispatches via the keyword table;
   unmapped intents return 'out of scope', never improvised.
5. VERDICTS: plain [OK]/[FAIL]/out of scope, exit 0/1/2, no tracebacks.
6. The Godfather Wizard governs execution + conversation.
7. EVERY DISPATCH IS JOURNALED: all routing events recorded to ledger.
8. REPL MODE exposes all /slashcommands from the fleet under one roof.
9. VOICE ENABLED: when VOICE_ENABLED=true, every REPL response speaks.
10. BANNER ON LAUNCH: every godfather_wizard repl shows the Sovereign mural.
[exit 0]
```

---

## 4. Banner Wizard — `banner_wizard`

ASCII banners for terminals, READMEs, and launch screens: 576
fonts, 18 style presets, and a size manager that fits the art to
the terminal it will live in. A wide banner needs a wide
terminal — the first run below was made at 200 columns so the art
fits on one line per row:

```
$ COLUMNS=200 banner_wizard "Wizard Central"
██     ██ ██ ███████  █████  ██████  ██████       ██████ ███████ ███    ██ ████████ ██████   █████  ██
██     ██ ██    ███  ██   ██ ██   ██ ██   ██     ██      ██      ████   ██    ██    ██   ██ ██   ██ ██
██  █  ██ ██   ███   ███████ ██████  ██   ██     ██      █████   ██ ██  ██    ██    ██████  ███████ ██
██ ███ ██ ██  ███    ██   ██ ██   ██ ██   ██     ██      ██      ██  ██ ██    ██    ██   ██ ██   ██ ██
 ███ ███  ██ ███████ ██   ██ ██   ██ ██████       ██████ ███████ ██   ████    ██    ██   ██ ██   ██ ███████
[exit 0]

$ banner_wizard --subtitle "local first, always" "Toolkit"
████████  ██████   ██████  ██      ██   ██ ██ ████████
   ██    ██    ██ ██    ██ ██      ██  ██  ██    ██
   ██    ██    ██ ██    ██ ██      █████   ██    ██
   ██    ██    ██ ██    ██ ██      ██  ██  ██    ██
   ██     ██████   ██████  ███████ ██   ██ ██    ██
L O C A L   F I R S T ,   A L W A Y S
[exit 0]
```

The catalog commands — `--styles` lists the presets and previews
each; `--sizes` reports how the size manager fits a long string
to the terminal; `--fonts` lists all 576 fonts (counted here, not
printed — the listing is 590 lines):

```
$ banner_wizard --styles

+-----------------------------------------------------------+
|                                                           |
|   ASCII BANNER ENGINE v1.0                                |
|                                                           |
|   576 fonts auto-loaded | 18 style presets | SizeManager  |
|                                                           |
+-----------------------------------------------------------+


=== STYLE PRESETS ===

                       Style Presets
╔═════╦═════════════╦════════════════╦════════════╦════════╗
║  ID ║ Preset Name ║     Color      ║   Border   ║ Align  ║
╠═════╬═════════════╬════════════════╬════════════╬════════╣
║   0 ║ arcade      ║  bright_cyan   ║   Double   ║ center ║
║   1 ║ bare        ║     white      ║    None    ║  left  ║
║   2 ║ bare-center ║      cyan      ║    None    ║ center ║
║   3 ║ boxed       ║     yellow     ║   Double   ║  left  ║
║   4 ║ clean       ║      cyan      ║   Square   ║  left  ║
║   5 ║ comic       ║   bright_red   ║  Rounded   ║ center ║
║   6 ║ cyber       ║      blue      ║ ASCII-Dbl  ║ center ║
║   7 ║ default     ║     white      ║  Rounded   ║  left  ║
║   8 ║ elegant     ║    magenta     ║  Rounded   ║ center ║
║   9 ║ heavy       ║      red       ║   Heavy    ║  left  ║
║  10 ║ matrix      ║     green      ║ Min-Double ║  left  ║
║  11 ║ minimal     ║      dim       ║  Minimal   ║  left  ║
║  12 ║ neon-blue   ║  bright_blue   ║  Dbl-Edge  ║ center ║
║  13 ║ neon-green  ║  bright_green  ║  Dbl-Edge  ║ center ║
║  14 ║ neon-pink   ║ bright_magenta ║  Dbl-Edge  ║ center ║
║  15 ║ retro       ║ bright_yellow  ║   ASCII    ║ center ║
║  16 ║ royal       ║      blue      ║   Double   ║ center ║
║  17 ║ shadow      ║  bright_black  ║ Simple-Hd  ║  left  ║
╚═════╩═════════════╩════════════════╩════════════╩════════╝
[…one preview banner per preset omitted…]
[exit 0]

$ banner_wizard --sizes
[…engine header, same as above…]

=== SIZE MANAGER REPORT ===
  Terminal: 80 cols | Usable: 74 cols | Min: 40 | Max: 80

Testing text: 'AUTOFIT_TESTING_WIDE_BANNERS'
Auto-fit selected: 'small'
[…fitted preview omitted…]
[exit 0]

$ banner_wizard --fonts | wc -l
590
[exit 0]
```

---

## 5. Code Guard Wizard — the static engine

The Code Guard Wizard audits code with two engines. The **static
engine** is built in — sixteen deterministic rules, nine for
Python and seven for Rust, always available, no daemon, no model.
(The **model engine**, which asks a seated model to audit, is
section 18.) Every command opens by naming its engine, so you
always know which one answered.

`roster` shows both engines and their state. On this seatless
machine the model seat reports exactly what is missing and how
to seat one:

```
$ codeguard_wizard roster
engine: static (built-in rules)
engines:
[OK] static (built-in rules) — always available, no daemon needed
     rules:
     CG001 syntax-error (HIGH)
     CG002 hardcoded-secret (HIGH)
     CG003 eval-exec (HIGH)
     CG004 shell-execution (HIGH)
     CG005 pickle-load (MEDIUM)
     CG006 weak-hash (MEDIUM)
     CG007 bare-except (MEDIUM)
     CG008 swallowed-exception (LOW)
     CG009 todo-marker (LOW)
     rust rules:
     RS001 unsafe-block (MEDIUM)
     RS002 unwrap-expect (MEDIUM)
     RS003 panic-marker (LOW)
     RS004 shell-construction (HIGH)
     RS005 unchecked-conversion (HIGH)
     RS006 hardcoded-secret (HIGH)
     RS007 unpinned-dependency (MEDIUM)
[FAIL] model seat — none served: daemon unreachable or no coder seat served
     seat one: run a local Ollama serving a coder model (e.g. `ollama pull qwen2.5-coder:3b-instruct`), then re-run
[exit 0]
```

The audit of the deliberately flawed fixture — every rule that
fires, named, with its line:

```
$ codeguard_wizard lang flawed.py
[OK] flawed.py: python
[exit 0]

$ codeguard_wizard audit flawed.py
engine: static (built-in rules)
[OK] flawed.py (python, static rules)
     findings: HIGH=3 MEDIUM=1 LOW=2
     [HIGH] CG002 hardcoded-secret (line 7) — string literal assigned to 'API_KEY'
     [LOW] CG009 todo-marker (line 9) — TODO marker left in the code
     [LOW] CG009 todo-marker (line 13) — TODO marker left in the code
     [HIGH] CG004 shell-execution (line 14) — subprocess call with shell=True
     [HIGH] CG003 eval-exec (line 19) — eval() executes a string as code
     [MEDIUM] CG007 bare-except (line 25) — bare except: catches everything, names nothing
     verdict: [FAIL] 3 high-severity finding(s) present
[exit 1]
```

(The default engine is static; `--engine static` gives the
identical report.) The same findings, in scanner and severity
shapes:

```
$ codeguard_wizard scan flawed.py
engine: static (built-in rules)
flawed.py:7: [HIGH] CG002 hardcoded-secret — string literal assigned to 'API_KEY'
flawed.py:9: [LOW] CG009 todo-marker — TODO marker left in the code
flawed.py:13: [LOW] CG009 todo-marker — TODO marker left in the code
flawed.py:14: [HIGH] CG004 shell-execution — subprocess call with shell=True
flawed.py:19: [HIGH] CG003 eval-exec — eval() executes a string as code
flawed.py:25: [MEDIUM] CG007 bare-except — bare except: catches everything, names nothing
[OK] scanned 1 files
     HIGH=3 MEDIUM=1 LOW=2
[exit 1]

$ codeguard_wizard severity flawed.py
engine: static (built-in rules)
[OK] flawed.py — findings by severity (static rules)
     CRITICAL (0):
     HIGH (3):
       flawed.py:7 CG002 hardcoded-secret — string literal assigned to 'API_KEY'
       flawed.py:14 CG004 shell-execution — subprocess call with shell=True
       flawed.py:19 CG003 eval-exec — eval() executes a string as code
     MEDIUM (1):
       flawed.py:25 CG007 bare-except — bare except: catches everything, names nothing
     LOW (2):
       flawed.py:9 CG009 todo-marker — TODO marker left in the code
       flawed.py:13 CG009 todo-marker — TODO marker left in the code
[exit 1]
```

`explain` answers two ways — by rule id, or by file and line:

```
$ codeguard_wizard explain CG002
engine: static (built-in rules)
[OK] CG002 hardcoded-secret (HIGH)
     A password, token, or key written as a string literal directly in the source. Anyone who can read the code owns the secret, and the secret travels with every copy of the file. Move it to the environment or a config the code reads at runtime.
[exit 0]

$ codeguard_wizard explain --engine static flawed.py 19
engine: static (built-in rules)
[OK] Rule at line 19:
     Severity: HIGH
     Title: CG003 eval-exec
     Message: eval() or exec() runs a string as code. If any part of that string can be influenced from outside, the caller can run anything. Parse the data instead (ast.literal_eval for literals), or dispatch to named functions.
     Detail: eval() executes a string as code
[exit 0]
```

`scaffold` drafts a test skeleton from the file's real functions
— preview only, disk untouched:

```
$ codeguard_wizard scaffold flawed.py
[OK] test skeleton generated (preview only, disk untouched): test_flawed.py
     functions: 4, classes: 0
--- skeleton follows ---
"""Generated by codeguard_wizard scaffold — test skeleton for flawed.py."""
import pytest

def test_run_report_exists():
    """SMOKE: run_report exists."""
    assert True

def test_evaluate_exists():
    """SMOKE: evaluate exists."""
    assert True

def test_divide_exists():
    """SMOKE: divide exists."""
    assert True

def test_greet_exists():
    """SMOKE: greet exists."""
    assert True

--- end ---
consent lane: pipe this output to a file yourself if you want it on disk
[exit 0]
```

And the static `fix`: only the one rule with a deterministic
rewrite (CG007, the bare `except`) is staged — through the Write
Wizard, never written directly — while the findings that need
judgment are handed back to a person or the model engine:

```
$ codeguard_wizard fix --engine static flawed.py
engine: static (built-in rules)
[STAGED] fix for flawed.py — a940135f5a4b3ea2.draft -> flawed.py (706 chars quarantined)
to write it: write_wizard commit flawed.py   # your keystroke, Governor
     needs a person or the model engine:
       line 7: CG002 hardcoded-secret — no deterministic rewrite
       line 9: CG009 todo-marker — no deterministic rewrite
       line 13: CG009 todo-marker — no deterministic rewrite
       line 14: CG004 shell-execution — no deterministic rewrite
       line 19: CG003 eval-exec — no deterministic rewrite
[exit 0]
```

### Watch: the before/after proof

An `audit` also records a baseline — per-file issue fingerprints
and a score. `watch` re-audits and reports the true delta against
that baseline. On `legacy.py` (a copy of the flawed module),
first unchanged, then after one finding is fixed by hand:

```
$ codeguard_wizard audit legacy.py
[…same six findings as flawed.py above; baseline recorded…]
[exit 1]

$ codeguard_wizard watch legacy.py
engine: static (built-in rules)
[OK] watch legacy.py — baseline score 61 -> now 61
     new: 0  resolved: 0  unchanged: 6
[exit 0]

# the person fixes the bare except by hand:
$ sed -i "s/^    except:$/    except ZeroDivisionError:/" legacy.py
$ grep -n "except" legacy.py
25:    except ZeroDivisionError:

$ codeguard_wizard watch legacy.py
engine: static (built-in rules)
[OK] watch legacy.py — baseline score 61 -> now 66
     new: 0  resolved: 1  unchanged: 5
     RESOLVED CG007 @ line 25: bare except: catches everything, names nothing
[exit 0]
```

That is the loop the wizard is for: audit, fix one thing, and let
`watch` prove the delta — score up, the resolved finding named,
nothing else moved.

### Rust: the static engine's second language

The static engine speaks Rust too. A sibling module scans `.rs`
files and `Cargo.toml` manifests under seven rules, RS001–RS007,
in the same finding shape and on the same severity scale as the
Python rules — so `audit`, `explain`, `watch`, and `fix` consume
Rust findings unchanged, and a directory audit dispatches by
extension into one report. The engine is a scanner, never a
toolchain: it runs no `cargo`, no `rustc`, nothing in the project
it audits — an audit must not execute the code it is auditing.
No Rust toolchain exists on this machine, and none is needed for
anything in this section.

The fixture, `flawed.rs` — every RS rule that has a shape here is
planted in it, including a dummy secret on line 3 (planted for
this demo; watch whether any output below ever prints its value):

```
use std::process::Command;

const API_KEY: &str = "sk-demo-DUMMY-secret-value";

fn main() {
    let data = std::fs::read_to_string("in.txt").unwrap();
    let n: u32 = unsafe { std::mem::transmute::<f32, u32>(1.5) };
    let out = Command::new("sh").arg("-c").arg(data).output().expect("run");
    panic!("giving up");
    let v = vec![1, 2, 3];
    let x = unsafe { *v.as_ptr() };
    let s = unsafe { String::from_utf8_unchecked(vec![104, 105]) };
    // let ignored = thing.unwrap();
    todo!("finish the rest");
}
```

```
$ codeguard_wizard lang flawed.rs
[OK] flawed.rs: rust
[exit 0]

$ codeguard_wizard audit flawed.rs
engine: static (built-in rules)
[OK] flawed.rs (rust, static rules)
     findings: HIGH=5 MEDIUM=5 LOW=2
     [HIGH] RS006 hardcoded-secret (line 3) — string literal assigned to 'API_KEY'
     [MEDIUM] RS002 unwrap-expect (line 6) — .unwrap() panics when the value is None or Err
     [MEDIUM] RS001 unsafe-block (line 7) — unsafe block: the compiler's memory-safety checks are suspended here
     [HIGH] RS005 unchecked-conversion (line 7) — 'transmute' reinterprets bytes as another type with no validity check
     [MEDIUM] RS002 unwrap-expect (line 8) — .expect() panics when the value is None or Err
     [HIGH] RS004 shell-construction (line 8) — Command::new("sh") spawns a shell: the string it is handed will be interpreted, not just run
     [HIGH] RS004 shell-construction (line 8) — shell flag "-c" passed as an argument: a shell will interpret the command string that follows
     [LOW] RS003 panic-marker (line 9) — panic! left in the code — an explicit panic/unfinished marker
     [MEDIUM] RS001 unsafe-block (line 11) — unsafe block: the compiler's memory-safety checks are suspended here
     [MEDIUM] RS001 unsafe-block (line 12) — unsafe block: the compiler's memory-safety checks are suspended here
     [HIGH] RS005 unchecked-conversion (line 12) — 'from_utf8_unchecked' skips the checked conversion: a wrong assumption is undefined behaviour
     [LOW] RS003 panic-marker (line 14) — todo! left in the code — an explicit panic/unfinished marker
     verdict: [FAIL] 5 high-severity finding(s) present
[exit 1]
```

Note what did not fire: the commented-out `.unwrap()` on line
13. Full-line `//` comments are not code, and the engine does
not pretend otherwise. And RS006 names the variable and the
pattern — the dummy value itself appears in no output, here or
in `explain`:

```
$ codeguard_wizard explain flawed.rs 3
engine: static (built-in rules)
[OK] Rule at line 3:
     Severity: HIGH
     Title: RS006 hardcoded-secret
     Message: A password, token, or key written as a string literal directly in the source. Anyone who can read the code owns the secret, and the secret travels with every copy of the file. Move it to the environment or a config the code reads at runtime. The audit names the variable and the pattern kind only — never the value.
     Detail: string literal assigned to 'API_KEY'
[exit 0]
```

The manifest is audited too — RS007 reads the dependency
sections of `Cargo.toml` for versions pinned to nothing:

```
$ codeguard_wizard audit Cargo.toml
engine: static (built-in rules)
[OK] Cargo.toml (rust, static rules)
     findings: HIGH=0 MEDIUM=3 LOW=0
     [MEDIUM] RS007 unpinned-dependency (line 6) — dependency 'serde' has version "*": it accepts whatever is newest on build day
     [MEDIUM] RS007 unpinned-dependency (line 7) — dependency 'regex' has version "*": it accepts whatever is newest on build day
     [MEDIUM] RS007 unpinned-dependency (line 8) — git dependency 'helper' has no pinned rev: it tracks whatever the branch points at
     verdict: [OK] no high-severity findings
[exit 0]
```

(The `pinned` git dependency — the one carrying a `rev` — and
`clap = "4"` are correctly silent.) A mixed tree is one sweep:
the same directory also holds `bad.py`, a one-line Python file
with an `eval`, and `watched.rs`, still clean at this point —
CG and RS findings land in a single report under one engine
line:

```
$ codeguard_wizard scan .
engine: static (built-in rules)
Cargo.toml:6: [MEDIUM] RS007 unpinned-dependency — dependency 'serde' has version "*": it accepts whatever is newest on build day
Cargo.toml:7: [MEDIUM] RS007 unpinned-dependency — dependency 'regex' has version "*": it accepts whatever is newest on build day
Cargo.toml:8: [MEDIUM] RS007 unpinned-dependency — git dependency 'helper' has no pinned rev: it tracks whatever the branch points at
bad.py:1: [HIGH] CG003 eval-exec — eval() executes a string as code
flawed.rs:3: [HIGH] RS006 hardcoded-secret — string literal assigned to 'API_KEY'
flawed.rs:6: [MEDIUM] RS002 unwrap-expect — .unwrap() panics when the value is None or Err
flawed.rs:7: [MEDIUM] RS001 unsafe-block — unsafe block: the compiler's memory-safety checks are suspended here
flawed.rs:7: [HIGH] RS005 unchecked-conversion — 'transmute' reinterprets bytes as another type with no validity check
flawed.rs:8: [MEDIUM] RS002 unwrap-expect — .expect() panics when the value is None or Err
flawed.rs:8: [HIGH] RS004 shell-construction — Command::new("sh") spawns a shell: the string it is handed will be interpreted, not just run
flawed.rs:8: [HIGH] RS004 shell-construction — shell flag "-c" passed as an argument: a shell will interpret the command string that follows
flawed.rs:9: [LOW] RS003 panic-marker — panic! left in the code — an explicit panic/unfinished marker
flawed.rs:11: [MEDIUM] RS001 unsafe-block — unsafe block: the compiler's memory-safety checks are suspended here
flawed.rs:12: [MEDIUM] RS001 unsafe-block — unsafe block: the compiler's memory-safety checks are suspended here
flawed.rs:12: [HIGH] RS005 unchecked-conversion — 'from_utf8_unchecked' skips the checked conversion: a wrong assumption is undefined behaviour
flawed.rs:14: [LOW] RS003 panic-marker — todo! left in the code — an explicit panic/unfinished marker
[OK] scanned 4 files
     HIGH=6 MEDIUM=8 LOW=2
[exit 1]
```

And `watch` keeps the same loop for Rust — audit the clean
`watched.rs`, then a function with an `.unwrap()` is added, and
the baseline tells the truth about it:

```
$ codeguard_wizard audit watched.rs
engine: static (built-in rules)
[OK] watched.rs (rust, static rules)
     findings: HIGH=0 MEDIUM=0 LOW=0
     verdict: [OK] no high-severity findings
[exit 0]

$ codeguard_wizard watch watched.rs
engine: static (built-in rules)
[OK] watch watched.rs — baseline score 100 -> now 100
     new: 0  resolved: 0  unchanged: 0
[exit 0]

# a new function is added to watched.rs, with an .unwrap() at line 11:
$ codeguard_wizard watch watched.rs
engine: static (built-in rules)
[OK] watch watched.rs — baseline score 100 -> now 95
     new: 1  resolved: 0  unchanged: 0
     NEW      RS002 @ line 11: .unwrap() panics when the value is None or Err
[exit 0]
```

One limit, stated plainly: static `fix` stages **nothing** for a
Rust finding. There is no safe mechanical rewrite for an
`unwrap()` — the static engine never rewrites Rust, and a
rewrite proposal is the model engine's job, when a seat serves.

---

## 6. Debug Wizard — `debug_wizard`

The diagnosis oracle. It autopsies tracebacks, classifies
errors, and counts a directory's compile health — and it never
mutates anything: its one fix-shaped act is staging a proposal
at the Write Wizard's wall, exactly as the Godfather Wizard's
`heal` showed. Its "errors" are files that fail to compile, plus
real tracebacks it can parse.

The demo's traceback is genuine — `crasher.py` was run and its
stderr saved to `trace.txt`:

```
$ debug_wizard trace trace.txt
[TRACE] trace.txt: 3 frame(s)
  File "/home/hatch/workspace/ds/work/crasher.py", line 13, in <module>
  File "/home/hatch/workspace/ds/work/crasher.py", line 9, in middle
  File "/home/hatch/workspace/ds/work/crasher.py", line 5, in inner
[ERR] line 5: ZeroDivisionError — division by zero
[exit 1]

$ debug_wizard stack trace.txt
[OK] stack digest — trace.txt
  exception: ZeroDivisionError: division by zero
  frames: 3
    File "/home/hatch/workspace/ds/work/crasher.py", line 13, in <module> (project)
    File "/home/hatch/workspace/ds/work/crasher.py", line 9, in middle (project)
    File "/home/hatch/workspace/ds/work/crasher.py", line 5, in inner (project)
  deepest frame: File "/home/hatch/workspace/ds/work/crasher.py", line 5, in inner
  deepest project frame: File "/home/hatch/workspace/ds/work/crasher.py", line 5, in inner
[exit 0]
```

`classify` reads either kind of evidence. Note the contrast:
`crasher.py` compiles fine (its error only happens at runtime),
while the traceback file classifies at once:

```
$ debug_wizard classify crasher.py
[SUMMARY] 0 errors
[exit 0]

$ debug_wizard classify trace.txt
[SUMMARY] 1 errors
  ZeroDivisionError: 1
[exit 1]
```

The directory census — one file of five does not compile:

```
$ debug_wizard audit .
[HEALTH] 4/5 (80.0%)
[FAIL] 1 files with errors
[exit 1]

$ debug_wizard count .
files=5 total_errors={'SyntaxError': 1}
[exit 0]

$ debug_wizard hotspot .
[HOT] 1 errors  syntax.py
[exit 1]

$ debug_wizard timeline .
1 errors  1794227567.7432303  syntax.py
[exit 0]

$ debug_wizard locate . "SyntaxError"
[MATCH] syntax.py
[exit 1]
```

Static cross-checks on a healthy file, and the diagnosis of the
sick one — plus the staged proposal from the heal chain, which
turns out to be the diagnosis itself, written as a note for the
person (the Debug Wizard proposes; it does not patch):

```
$ debug_wizard imports flawed.py
[IMPORTS] flawed.py
(no likely missing imports)
[exit 0]

$ debug_wizard names flawed.py
(no undefined names)
[exit 0]

$ debug_wizard suggest syntax.py
[ISSUE] syntax.py
  Line 4: SyntaxError — expected ':'
[exit 0]

$ debug_wizard explain syntax.py
[ISSUE] syntax.py
  Line 4: SyntaxError — expected ':'
[exit 0]

$ debug_wizard preview syntax.py
[OK] non-python target: syntax gate waived
[NOTE] new file: /home/hatch/workspace/ds/home/.debug-wizard/fix_syntax.txt does not exist yet
--- proposed (first 800 chars) ---
[ISSUE] syntax.py
  Line 4: SyntaxError — expected ':'

[exit 0]
```

The machine-readable report, fleet stats, and the law:

```
$ debug_wizard report .
{
  "timestamp": "2026-11-09T12:35:16",
  "root": ".",
  "audit": {
    "healthy": 4,
    "unhealthy": 1,
    "total_errors": 1,
    "files_checked": 5,
    "health_pct": 80.0
  },
  "hotspots": [
    {
      "file": "syntax.py",
      "errors": 1
    }
  ]
}
[exit 0]

$ debug_wizard stats
/home/hatch/workspace/ds/work: 4/5 healthy (80.0%)
[exit 0]

$ debug_wizard versions
debug_law_sha256: 4d3b59bd0ba45e4e3ff70ff7dea8c780aacc854ac323f32292ca8ff07d6e5d01
[exit 0]

$ debug_wizard law
DEBUG LAW (Debug Wizard, the diagnosis oracle)
1. Diagnose freely: autopsy tracebacks, classify errors, count hotspots, report facts.
2. Never mutate: no writes, no patches, no fixes applied — only proposals staged for the Write Wizard.
3. Consent wall: any fix suggestion goes through write_wizard propose; Governor consents.
4. Plain verdicts: [OK]/[FAIL]/out of scope, exit 0/1/2, no tracebacks.
5. Truth first: run python_wizard check or python -m py_compile before analysis.
6. Ignore list amends only by Governor decree; protected paths stay ignored.
[exit 0]
```

---

## 7. Diff Wizard — `diff_wizard`

Change-truth, in five shapes: unified diff, counts, context
control, word-level, and reverse — plus a same/different verdict
whose answer is the exit code, and a directory comparison.
Differing files exit 1; that is the verdict doing its job.

```
$ diff_wizard files before.txt after.txt
--- before.txt
+++ after.txt
@@ -1,4 +1,5 @@
 Wizard Central Toolkit demo notes.
-The fleet has twelve wizards.
+The fleet has twelve wizards and one router.
 Every write crosses the consent wall.
 Local first, always.
+Receipts for every crossing.

[FAIL] files differ
[exit 1]

$ diff_wizard summary before.txt after.txt
added=2 removed=1 hunks=1
[exit 1]

$ diff_wizard word before.txt after.txt
Wizard Central Toolkit demo notes. The fleet has twelve
<del>wizards.</del><ins>wizards and one router.</ins>
Every write crosses the consent wall. Local first, always.
<ins>Receipts for every crossing.</ins>
[exit 0]

$ diff_wizard same before.txt before.txt
[exit 0]

$ diff_wizard same before.txt after.txt
[exit 1]

$ diff_wizard dirs dirA dirB
only in dirA: only_a.txt
only in dirB: only_b.txt
differing: two.txt
[FAIL] 3 differences
[exit 1]
```

(`context 1` re-runs the unified diff with one line of context;
`reverse` prints the same diff with the files swapped. Both ran
in this demo with the expected output.)

---

## 8. JSON Wizard — `json_wizard`

The JSON doctor: validate, reformat, inspect, query by dotted
path, diff two documents structurally, merge them. It reads and
reports; it never rewrites your files.

```
$ json_wizard validate data.json
[OK] valid JSON (root type: dict)
[exit 0]

$ json_wizard validate broken.json
[FAIL] invalid JSON at line 1, col 27: Expecting value: line 1 column 27 (char 26)
[exit 1]

$ json_wizard pretty data.json
{
  "fleet": {
    "router": "wiz",
    "wizards": 12
  },
  "name": "demo-workspace",
  "nested": {
    "deep": {
      "deeper": true
    }
  },
  "tags": [
    "demo",
    "local-first"
  ],
  "version": 1
}
[exit 0]

$ json_wizard compact data.json
{"fleet":{"router":"wiz","wizards":12},"name":"demo-workspace","nested":{"deep":{"deeper":true}},"tags":["demo","local-first"],"version":1}
[exit 0]

$ json_wizard inspect data.json
{
  "fleet": {
    "router": "wiz",
    "wizards": 12
  },
  "name": "demo-workspace",
  "nested": {
    "deep": {
      "deeper": true
    }
  },
  "tags": {
    "_list_len": 2
  },
  "version": 1
}
[exit 0]

$ json_wizard keys data.json
fleet
name
nested
tags
version
[exit 0]

$ json_wizard get data.json fleet.wizards
12
[exit 0]

$ json_wizard get data.json nested.deep.deeper
true
[exit 0]

$ json_wizard diff data.json data2.json
[DIFF] added at extra
       b: "added in the second file"
[DIFF] removed at nested
       a: {"deep": {"deeper": true}}
[DIFF] added at tags.2
       b: "revised"
[DIFF] changed at version
       a: 1
       b: 2
[exit 1]

$ json_wizard stats data.json
{
  "root_type": "dict",
  "root_keys": 5,
  "max_depth": 3,
  "dict": 4,
  "list": 1,
  "str": 4,
  "number": 2,
  "bool": 1,
  "null": 0
}
[exit 0]

$ json_wizard merge data.json data2.json
{
  "fleet": {
    "router": "wiz",
    "wizards": 12
  },
  "name": "demo-workspace",
  "nested": {
    "deep": {
      "deeper": true
    }
  },
  "tags": [
    "demo",
    "local-first",
    "revised"
  ],
  "version": 2,
  "extra": "added in the second file"
}
[exit 0]
```

---

## 9. Python Wizard — `python_wizard`

A Python file's health, read twenty-three ways: syntax first,
then structure, metrics, and smells. Most reports are JSON for
programs; the findings that need a person (secrets, bare
excepts, TODOs, missing docstrings) exit 1 and print for eyes.
The `secrets` report redacts by default: it names the line and
the kind of credential, and the value itself is replaced — the
report is safe to paste anywhere. A deliberate `--show-secrets`
flag prints the value for local debugging, and it is
demonstrated once below, on the fixture's dummy key.

```
$ python_wizard check flawed.py
[OK] flawed.py
[exit 0]

$ python_wizard check syntax.py
[FAIL] syntax.py line 4, col 16: expected ':'
[exit 1]

$ python_wizard explain syntax.py
[FAIL] syntax.py line 4, col 16: expected ':'
      3|
->    4| def greet(name)
      5|     return "Hello, " + name
[exit 1]

$ python_wizard outline flawed.py
L  12 def   run_report
L  17 def   evaluate
L  22 def   divide
L  29 def   greet
[exit 0]

$ python_wizard imports flawed.py
{
  "stdlib": [
    "json",
    "os",
    "subprocess",
    "sys"
  ],
  "third_party": [],
  "local": [],
  "relative": []
}
[exit 0]

$ python_wizard loc flawed.py
{
  "lines": 34,
  "code": 20,
  "blank": 12,
  "comment": 2,
  "functions": 4,
  "classes": 0
}
[exit 0]

$ python_wizard complexity flawed.py
  2 branches  L  22 divide
  1 branches  L  12 run_report
  1 branches  L  17 evaluate
  1 branches  L  29 greet
[exit 0]

$ python_wizard score flawed.py
{
  "score": 69,
  "docstrings_missing": 3,
  "bare_excepts": 1,
  "todos": 2,
  "complexity_hotspots": 0
}
[exit 0]

$ python_wizard secrets flawed.py
L   7 [api_key] API_KEY = "<redacted>"
[exit 1]

$ python_wizard secrets flawed.py --show-secrets
L   7 API_KEY = "sk-demo-1234567890abcdef"
[exit 1]

$ python_wizard excepts flawed.py
L  25 bare except
[exit 1]

$ python_wizard todos flawed.py
L   9 [TODO] move the key into the environment before shipping
L  13 [TODO] replace the shell call with an argv list
[exit 1]

$ python_wizard docstrings flawed.py
L  12 run_report — no docstring
L  22 divide — no docstring
L  29 greet — no docstring
[exit 1]

$ python_wizard deadcode flawed.py
[hint] candidates only — attribute-called methods may false-positive
L  12 run_report
L  17 evaluate
L  22 divide
[exit 1]

$ python_wizard callmap flawed.py
{
  "run_report": [
    ".run"
  ],
  "evaluate": [
    "eval"
  ],
  "divide": [],
  "greet": []
}
[exit 0]

$ python_wizard mainguard flawed.py
[OK] __main__ guard present
[exit 0]

$ python_wizard globals flawed.py
L   7 API_KEY (immutable)
[exit 0]

$ python_wizard magic flawed.py
[OK] no suspicious literals
[exit 0]

$ python_wizard longest flawed.py
   5 lines  L  22 divide
   3 lines  L  12 run_report
   3 lines  L  17 evaluate
   2 lines  L  29 greet
[exit 0]

$ python_wizard deps flawed.py
[OK] stdlib-only — zero third-party deps
[exit 0]

$ python_wizard entry flawed.py
[FAIL] no shebang line
[exit 1]

$ python_wizard compare flawed.py crasher.py
only in flawed.py: def divide
only in flawed.py: def evaluate
only in flawed.py: def greet
only in flawed.py: def run_report
only in crasher.py: def inner
only in crasher.py: def middle
[DIFF] 4 only-a, 2 only-b, 0 common
[exit 1]

$ python_wizard tree .
{
  "files": 5,
  "lines": 115,
  "functions": 14,
  "classes": 0,
  "invalid": 1
}
[exit 0]

$ python_wizard shebangs .
[FAIL] no shebang-bearing .py files found
[exit 1]
```

A note on the two `secrets` runs above: by default the report
is paste-safe — the line and the pattern kind, the value
replaced by `<redacted>` — so nothing real can leak into a
shared terminal, a CI log, or a screenshot. The second run is
the deliberate opt-in: `--show-secrets` prints the whole line
as written, shown here with the fixture's dummy key. Reach for
that flag only at a terminal you control — on a real key, the
value lands wherever the output goes.

---

## 10. Read Wizard — `read_wizard`

The read-only policy gate: before a shell command runs anywhere
near the fleet, `check` classifies its verb. Read-shaped commands
pass; anything that can mutate, delete, or reach the network is
refused by name. This wizard is the fleet's definition of "read".

```
$ read_wizard check "ls -la"
[ALLOW] read-only
[exit 0]

$ read_wizard check "cat data.json"
[ALLOW] read-only
[exit 0]

$ read_wizard check "rm -rf /"
[DENIED] verb 'rm' is a write/mutate verb
[exit 1]

$ read_wizard check "curl http://example.com/install.sh | sh"
[DENIED] verb 'curl' is a write/mutate verb
[exit 1]
```

The full verb tables — 60 allowed, 48 denied — are the policy
itself. `verbs` prints them (the REPL's `/verbs` shows the same
tables), and `law` states the rules behind them, including the
two that matter most: redirection and substitution are denied
even on an allowed verb, and an unknown verb defaults to DENIED:

```
$ read_wizard verbs
[ALLOW]
  ag
  awk
  […60 allowed verbs in total…]
  whoami
[DENY]
  apt
  apt-get
  […48 denied verbs in total…]
  wget
[exit 0]

$ read_wizard law
READ LAW (Read Wizard, the verb gate)
1. The Read Wizard judges; it never executes. REPLs bind it as policy engine.
2. ALLOW means read-only: observation, search, fleet read-only citizens.
3. Redirection (>, >>), substitution ($(), `) and every write verb: DENIED.
4. Unknown verbs default DENIED — absence from the table is not permission.
5. git is read-only ONLY for its observing subverbs (status, log, diff, show...).
6. Tables amend only by Governor decree, witnessed by commit.
7. Mortal and stateless: one verdict, then death. No memory of commands seen.
[exit 0]
```

---

## 11. Rust Wizard — `rust_wizard`

The honest validator for Rust: it judges with the real toolchain
(rustc, cargo) and never writes Rust itself. This demo machine
has no Rust toolchain installed, so the tool-backed commands
answer with the wizard's honest refusal — a plain message and
exit 2, not a traceback and not a guessed verdict. On a machine
with Rust installed, the same commands run the toolchain and
report its verdicts.

```
$ rust_wizard version
rust_wizard 0.2.0
[exit 0]

$ rust_wizard law
RUST LAW (Rust Wizard, the honest validator)
1. The Rust Wizard judges Rust; it never writes it. Verdicts only.
2. Every verdict comes from the real toolchain (rustc, cargo).
   No toolchain, no verdict: a plain message, exit 2.
3. fmt speaks in --check: it reports drift, it never reformats.
4. clean is the one delete the Rust Wizard performs: a crate's
   own target/ directory, and nothing else, ever.
5. Mortal and stateless: one command, one verdict, then death.
[exit 0]

$ rust_wizard check hello.rs
[FAIL] rustc not found — install Rust to use rust_wizard check
[exit 2]

$ rust_wizard check crate
[FAIL] rustc not found — install Rust to use rust_wizard check
[exit 2]

$ rust_wizard build crate
[FAIL] cargo not found — install Rust to use rust_wizard build
[exit 2]
```

(The remaining verbs — `run`, `test`, `clippy`, `fmt`, `doc`,
`clean` — answer the same way here, each naming the tool it
needs. Their live-toolchain run is part of the completing proof
on a machine with Rust installed.)

---

## 12. Tmux Wizard — `tmux_wizard`

The session keeper: tmux sessions created, listed, inspected,
renamed, and killed — always by calling tmux with an argument
list, never through a shell, and always reporting what tmux
itself says. This demo runs against the machine's real tmux:

```
$ tmux_wizard version
tmux_wizard 0.2.0
[exit 0]

$ tmux_wizard law
TMUX LAW (Tmux Wizard, the session keeper)
1. The Tmux Wizard manages sessions; the truth about them comes
   from tmux itself, never from memory or invention.
2. tmux is always called with an argument list, never through
   a shell.
3. capture reads a pane; it changes nothing.
4. detach frees the client; the session and its work keep
   running.
5. kill is the only destroyer, and it names its session.
[exit 0]

$ tmux_wizard list
no sessions running
[exit 0]

$ tmux_wizard new demo /home/hatch/workspace/ds/work
[OK] session 'demo' created
[exit 0]

$ tmux_wizard list
demo
[exit 0]

$ tmux_wizard census
sessions total: 1
[OK] demo                 windows= 1 detached
census verdict: 1/1 healthy
[exit 0]

$ tmux_wizard capture demo 10
root@htch-runtime:/home/hatch/workspace/ds/work#
[exit 0]

$ tmux_wizard rename demo demo2
[OK] 'demo' -> 'demo2'
[exit 0]

$ tmux_wizard detach demo2
[FAIL] detach from 'demo2' failed: no current client
[exit 1]

$ tmux_wizard kill demo2
[OK] session 'demo2' killed
[exit 0]

$ tmux_wizard list
no sessions running
[exit 0]
```

The `detach` failure is the honest one: detach frees an
*attached* client, and this session was created detached — there
was no client to free, and the wizard says so instead of
claiming success.

---

## 13. Todo Wizard — `todo_wizard`

A plain, durable task list in a bank under your home directory —
the same bank the Godfather Wizard's `task` intake writes to,
which is why item #1 below is the task the Godfather Wizard took
in during section 3:

```
$ todo_wizard list
[ ] #1 (normal) water the demo plants
[exit 0]

$ todo_wizard add "Write the demo report"
[+] #2 Write the demo report
[exit 0]

$ todo_wizard add "Fix the bare except in flawed.py"
[+] #3 Fix the bare except in flawed.py
[exit 0]

$ todo_wizard add "Book the clinic appointment"
[+] #4 Book the clinic appointment
[exit 0]

$ todo_wizard note 1 "outline done, runs in progress"
[OK] noted
[exit 0]

$ todo_wizard done 2
[OK] completed
[exit 0]

$ todo_wizard list
[ ] #1 (normal) water the demo plants [1 notes]
[x] #2 (normal) Write the demo report
[ ] #3 (normal) Fix the bare except in flawed.py
[ ] #4 (normal) Book the clinic appointment
[exit 0]

$ todo_wizard undo 2
[OK] reopened
[exit 0]

$ todo_wizard oldest
#1 water the demo plants (created 2026-11-09T12:35:11)
[exit 0]

$ todo_wizard stats
{"total": 4, "done": 0, "pending": 4}
[exit 0]

$ todo_wizard overdue
no pending tasks older than 7 days
[exit 0]
```

`export` prints the whole bank as JSON — every field, including
the note and its timestamp — so the list is never locked inside
the tool:

```
$ todo_wizard export
[
  {
    "id": 1,
    "text": "water the demo plants",
    "priority": "normal",
    "done": false,
    "created": "2026-11-09T12:35:11",
    "completed": null,
    "notes": [
      {
        "text": "outline done, runs in progress",
        "at": "2026-11-09T12:35:20"
      }
    ]
  },
  […items 2–4 in the same shape…]
]
[exit 0]
```

---

## 14. Write Wizard — `write_wizard`

The consent wall. Nothing in the toolkit writes a file except
through this wizard, and this wizard writes only on a literal
`y` typed live by the person — no `--yes`, no `--force`, no
environment variable, no exception (its law, below, is eleven
clauses and every one of them is load-bearing). Content is first
**staged** in a quarantine under `~/.write-wizard/pending`; the
disk is untouched until consent. This is where every staged
proposal you have seen so far — the heal fix, the static Code
Guard fix — was waiting.

```
$ write_wizard law
WRITE LAW (Write Wizard, the consent wall)
1. propose stages content in ~/.write-wizard/pending — disk untouched.
2. preview runs the Python Wizard gate and the Diff Wizard against disk truth.
3. commit opens ONLY on a literal 'y' typed live by the Governor.
4. No --yes. No --force. No batch. No env var. No exception.
5. A failing syntax gate is a hard fail: commit MUST refuse.
6. Every write is re-read from disk; unequal bytes = reported FAIL.
7. Drafts survive refusal — quarantine keeps evidence, never destroys it.
8. Tables and laws amend only by Governor decree, witnessed by commit.
9. Every overwriting commit saves a backup first: rollback is a right.
10. Every wall event — commit, refusal, burn, rollback — is journaled.
11. Protected paths refuse writes absolutely, past any consent.
[exit 0]
```

Stage a note, and inspect the staging from every angle. Note
`pending`: the heal draft and the Code Guard fix from the
earlier sections are still quarantined alongside the new one —
drafts survive until the person decides:

```
$ printf "Fleet notes, first draft.\n" | write_wizard propose notes.txt
[OK] staged: e39538e7f27a7bf5.draft -> notes.txt (26 chars quarantined)
[exit 0]

$ write_wizard pending
  482886e03d950512.draft  ->  /home/hatch/workspace/ds/home/.debug-wizard/fix_syntax.txt
  a940135f5a4b3ea2.draft  ->  flawed.py
  e39538e7f27a7bf5.draft  ->  notes.txt
[exit 0]

$ write_wizard status notes.txt
target:   notes.txt
draft:    e39538e7f27a7bf5.draft
bytes:    26
staged:   0 minutes ago
shielded: no
[exit 0]

$ write_wizard preview notes.txt
[OK] non-python target: syntax gate waived
[NOTE] new file: notes.txt does not exist yet
--- proposed (first 800 chars) ---
Fleet notes, first draft.

[exit 0]

$ write_wizard verify notes.txt
[NOTE] target does not exist yet — new file
[exit 0]

$ write_wizard explain notes.txt
[WOULD WRITE] notes.txt (26 bytes staged)
  - new file — no backup needed
[exit 0]
```

(`diff` on a not-yet-existing file prints the same preview;
against an existing file it shows the true disk→draft diff, as
the second commit below demonstrates.)

Now the wall itself. Consent **refused** — the draft stays
quarantined and the file is simply never created:

```
$ printf "n\n" | write_wizard commit notes.txt
[OK] non-python target: syntax gate waived
[NOTE] new file: notes.txt does not exist yet
--- proposed (first 800 chars) ---
Fleet notes, first draft.

GOVERNOR CONSENT — write to notes.txt ? [y/N] consent withheld — draft stays quarantined
[exit 1]

$ ls notes.txt
ls: cannot access 'notes.txt': No such file or directory
```

Consent **given** — written, then re-read from disk and verified
byte-for-byte before the wizard calls it done:

```
$ printf "y\n" | write_wizard commit notes.txt
[OK] non-python target: syntax gate waived
[NOTE] new file: notes.txt does not exist yet
--- proposed (first 800 chars) ---
Fleet notes, first draft.

GOVERNOR CONSENT — write to notes.txt ? [y/N] [OK] written and verified on disk
[exit 0]

$ cat notes.txt
Fleet notes, first draft.
```

A second draft overwrites — but first the commit shows the real
diff, and a backup of the current file is saved before the
write. `rollback` (itself behind consent) restores it:

```
$ printf "Fleet notes, second draft — revised.\n" | write_wizard propose notes.txt
[OK] staged: e39538e7f27a7bf5.draft -> notes.txt (37 chars quarantined)
[exit 0]

$ printf "y\n" | write_wizard commit notes.txt
[OK] non-python target: syntax gate waived
--- diff (disk -> proposed) ---
--- notes.txt
+++ /home/hatch/workspace/ds/home/.write-wizard/pending/e39538e7f27a7bf5.draft
@@ -1 +1 @@
-Fleet notes, first draft.
+Fleet notes, second draft — revised.

[FAIL] files differ
GOVERNOR CONSENT — write to notes.txt ? [y/N] [OK] written and verified on disk
[exit 0]

$ cat notes.txt
Fleet notes, second draft — revised.

$ printf "y\n" | write_wizard rollback notes.txt
GOVERNOR CONSENT — roll back notes.txt to backup? [y/N] [OK] rolled back and verified on disk
[exit 0]

$ cat notes.txt
Fleet notes, first draft.
```

Protection is the wall's absolute form: a protected path
refuses **even with consent offered**. The draft stages fine —
staging harms nothing — but the commit cannot open:

```
$ write_wizard protect notes.txt
[OK] protected: /home/hatch/workspace/ds/work/notes.txt
[exit 0]

$ write_wizard protected
[SHIELD] /home/hatch/workspace/ds/work/notes.txt
[exit 0]

$ printf "overwrite attempt\n" | write_wizard propose notes.txt
[OK] staged: e39538e7f27a7bf5.draft -> notes.txt (18 chars quarantined)
[exit 0]

$ printf "y\n" | write_wizard commit notes.txt
[FAIL] path is PROTECTED — the wall refuses absolutely
[exit 1]

$ write_wizard unprotect notes.txt
[OK] unprotected: /home/hatch/workspace/ds/work/notes.txt
[exit 0]
```

And the wall keeps its own receipts. Every event above —
refusals included — is in the journal:

```
$ write_wizard stats
{
  "events": {
    "COMMIT_REFUSED": 2,
    "COMMITTED": 2,
    "BACKUP_SAVED": 1,
    "ROLLBACK_OK": 1,
    "PROTECT": 1,
    "UNPROTECT": 1
  },
  "pending_drafts": 3,
  "backups": 1,
  "protected": 0
}
[exit 0]

$ write_wizard audit
drafts=3 orphans=0 ghosts=0 oldest=2026-11-09T12:35:10
[exit 0]

$ write_wizard guard
[OK] 482886e03d950512.draft gate=waived -> /home/hatch/workspace/ds/home/.debug-wizard/fix_syntax.txt
[OK] a940135f5a4b3ea2.draft gate=PASS -> flawed.py
[OK] e39538e7f27a7bf5.draft gate=waived -> notes.txt
[exit 0]

$ write_wizard history notes.txt
2026-11-09T12:35:21  COMMIT_REFUSED   declined
2026-11-09T12:35:21  COMMITTED
2026-11-09T12:35:22  BACKUP_SAVED
2026-11-09T12:35:22  COMMITTED
2026-11-09T12:35:22  ROLLBACK_OK
2026-11-09T12:35:22  PROTECT
2026-11-09T12:35:22  COMMIT_REFUSED   path is PROTECTED
2026-11-09T12:35:22  UNPROTECT
[exit 0]

$ write_wizard law-digest
{
  "law_sha256": "e07d0d0a27352ecd5838522f78937e94fee3829794e86ef5bdadc2ae55c6b726",
  "law_chars": 800,
  "law_lines": 12
}
[exit 0]
```

---

## 15. The REPL — `godfather_wizard repl`, seatless

The cockpit: one prompt, the whole fleet. Every wizard is
reachable by slash command, plain language is routed
deterministically, and a model — when one is seated — can be
consulted under the same roof. The sessions in this chapter and
the next were driven by scripted input through a terminal, so
what you see is the real interactive surface, prompts and all.

This first session runs **seatless** — the demo machine's true
state — and it is worth seeing how much works with no model at
all, and how plainly the seat-dependent parts say what they
need. Launch:

```
$ godfather_wizard repl
   __________  ____  _________  ________  ____________
  / ____/ __ \/ __ \/ ____/   |/_  __/ / / / ____/ __ \
 / / __/ / / / / / / /_  / /| | / / / /_/ / __/ / /_/ /
/ /_/ / /_/ / /_/ / __/ / ___ |/ / / __  / /___/ _, _/
\____/\____/_____/_/   /_/  |_/_/ /_/ /_/_____/_/ |_|

G R A N D   M A S T E R   O F   T H E   S O V E R E I G N   F L E E T
100 cols | Sovereign Fleet: 13 citizens, zero lies

👁️  SESSION 2 — Sovereign Fleet Cockpit

Type /help for slash commands, /quit to exit.
```

`/help` is the map — every slash and what it dispatches to:

```
👑 godfather> /help
📜 AVAILABLE SLASH COMMANDS:
  /truth          → godfather_wizard brief
  /ls             → godfather_wizard listing
  /read           → godfather_wizard read
  /pycheck        → python_wizard check
  /fix            → godfather_wizard heal
  /heal           → godfather_wizard heal
  /todo           → todo_wizard add
  /todos          → todo_wizard list
  /diff           → diff_wizard files
  /models         → godfather_wizard models
  /brainstorm     → godfather_wizard brainstorm (model seat; hands off)
  /build          → godfather_wizard build (proposal -> diff -> double ask -> write_wizard)
  /debug          → godfather_wizard debug (proposal -> diff -> double ask -> write_wizard)
  /banner         → banner_wizard
  /codeguard      → codeguard_wizard
  /json           → json_wizard
  /rust           → rust_wizard
  /tmux           → tmux_wizard
  /write          → write_wizard
  /verbs          → read_wizard verbs
  /tasks          → todo_wizard list
  /audit          → debug_wizard audit
  /diag           → debug_wizard classify
  /bins           → godfather_wizard symlinks
  /history        → godfather_wizard history
  /stats          → godfather_wizard stats
  /routes         → godfather_wizard routes
  /fleet          → godfather_wizard fleet
  /law            → godfather_wizard law
  /help           → godfather_wizard help
  /status         → godfather_wizard status
  /census         → godfather_wizard census
  /diff <file> <instruction>  → godfather_wizard diff review (proposal form; the two-file form above compares two files)
  /voices         → pick voice (numbered dropdown)
  /model          → pick model (numbered dropdown)
  /more-commands  → full fleet arsenal (all citizens)
```

`/more-commands` expands every citizen's full usage (thirteen
sections; shown trimmed), and any wizard is reachable directly
through `/wiz`, or by its dedicated slash:

```
👑 godfather> /more-commands

📚 FLEET ARSENAL — 13 citizens
============================================================

BANNER_WIZARD (★):
    Banner Wizard — ASCII banner wizard
    alias: bannerwiz
    usage: banner_wizard <words...> [--subtitle TEXT] | --demo | --themes | --styles | --sizes | --fonts | --interactive
           banner_wizard --help | --version
[…twelve more citizen sections in the same shape…]
============================================================

👑 godfather> /banner
Banner Wizard — ASCII banner wizard
alias: bannerwiz
usage: banner_wizard <words...> [--subtitle TEXT] | --demo | --themes | --styles | --sizes | --fonts | --interactive
       banner_wizard --help | --version

👑 godfather> /fleet
[OK] 13 sibling wizards installed
  […the thirteen names, as in section 3…]

👑 godfather> /pycheck flawed.py
[OK] flawed.py

👑 godfather> /wiz python_wizard imports flawed.py
[ROUTE] universal delegation -> python_wizard imports flawed.py
{
  "stdlib": [
    "json",
    "os",
    "subprocess",
    "sys"
  ],
  "third_party": [],
  "local": [],
  "relative": []
}

👑 godfather> /json validate data.json
[OK] valid JSON (root type: dict)

👑 godfather> /diff before.txt after.txt
--- before.txt
+++ after.txt
@@ -1,4 +1,5 @@
 Wizard Central Toolkit demo notes.
-The fleet has twelve wizards.
+The fleet has twelve wizards and one router.
 Every write crosses the consent wall.
 Local first, always.
+Receipts for every crossing.

[FAIL] files differ

👑 godfather> /todos
[ ] #1 (normal) water the demo plants [1 notes]
[ ] #2 (normal) Write the demo report
[ ] #3 (normal) Fix the bare except in flawed.py
[ ] #4 (normal) Book the clinic appointment
```

Plain language routes by the deterministic table from section
3 — and a mutation request in plain language meets the consent
wall, not a tool:

```
👑 godfather> list the files in this workspace
[ROUTE] matched route: list/listing/whatshere
after.txt
before.txt
broken.json
crasher.py
crate/
data.json
data2.json
dirA/
dirB/
flawed.py
hello.rs
legacy.py
modelcheck.py
notes.txt
syntax.py
trace.txt

👑 godfather> check the syntax of flawed.py
[ROUTE] matched route: syntax/pycheck
[OK] flawed.py

👑 godfather> please delete every file in this folder right now
[CONSENT WALL] mutation intent detected — route through write_wizard
to mutate: echo 'content' | write_wizard propose <path>
then answer the wall yourself: write_wizard commit <path>
```

And the seat-dependent doors, seatless — each says exactly what
it needs, and nothing pretends:

```
👑 godfather> /models
no model seat is configured or serving — the fleet runs seatless
providers:
  Ollama (local — 127.0.0.1:11434): not serving
  Meta (Muse) (cloud — api.meta.ai): key not set
  Anthropic (cloud — api.anthropic.com): key not set
  OpenAI (cloud — api.openai.com): key not set
  Google (cloud — generativelanguage.googleapis.com): key not set
  DeepSeek (cloud — api.deepseek.com): key not set
model assignments (~/.godfather/models.json):
  default: (not set — no effective seat)
  brainstorm: (not set — no effective seat)
  build: (not set — no effective seat)
  debug: (not set — no effective seat)
  diff: (not set — no effective seat)
  audit: (not set — no effective seat)
guide: PROVIDERS.md — where to get each provider's key, and how to set up local models with Ollama

👑 godfather> /model

💾 MODEL SELECTOR (live Ollama roster)
[FAIL] no models found — is Ollama running?

👑 godfather> /voices

🎙️  VOICE SELECTOR (universal disk discovery)
[FAIL] no paired Piper voices found on this machine
roots scanned:
    […six voice roots under the sandbox home and system shares…]
hint: export VOICE_ROOT=<your voices dir> and retry

👑 godfather> /brainstorm a greeting module for this workspace
[OK] brainstorm mode — hands off: the seat can talk only; no tools run and no files change. Use /brainstorm end to leave.
no model seat is configured or serving — the brainstorm feature needs a live model

👑 godfather> /brainstorm end
[OK] brainstorm mode ended — hands remain off

👑 godfather> /build make me a file called greet.py with a greet function
no model seat is configured or serving — the build feature needs a live model

👑 godfather> /debug flawed.py
no model seat is configured or serving — the debug feature needs a live model

👑 godfather> /quit
[OK] Godfather bows out. Sovereignty preserved.
```

Proof that the seatless session wrote nothing — the file the
`/build` request named does not exist:

```
$ ls gen.py greet.py
ls: cannot access 'gen.py': No such file or directory
ls: cannot access 'greet.py': No such file or directory
```

---

## 16. Providers and seats

A **seat** is a provider plus a model. There are six providers:
Ollama (local, on your own machine) and five cloud APIs you can
opt into with your own key — Meta (Muse), Anthropic, OpenAI,
Google, and DeepSeek. The toolkit is local-first: nothing is
sent anywhere unless you seat a cloud provider, and keys live in
the environment only — never stored, never journaled, never
printed; status displays say only whether a key is set.

One seated model can run everything (the `default` seat);
per-task seats (`brainstorm`, `build`, `debug`, `diff`,
`audit`) are an option, never a requirement.
[PROVIDERS.md](PROVIDERS.md) is the setup guide for every seat —
where to get each key, and how to install Ollama and pull your
first local models. It ships with the toolkit; its opening:

```
# Providers — where every seat comes from

The Godfather Wizard does its model work through a **seat**: a
provider plus a model. There are six providers. One is local
(Ollama, on your own machine); five are cloud APIs you can opt
into. This sheet is the map: for every seat, where it comes
from, what it needs, and how to hand it to the toolkit.

The rules, once, for all six:

- **One model can run everything.** Assign a single `default`
  seat and every task uses it. Per-task seats (`brainstorm`,
  `build`, `debug`, `diff`, `audit`) are an option, never a
  requirement.
- **Keys live in the environment only.** Each cloud seat reads
  its key from an environment variable at call time. Keys are
  never written into the toolkit's files, never stored in the
  Godfather Wizard's bank, never journaled, and never printed —
  status displays say only whether a key is set.
- **A subscription is not an API key.** […]
```

Assigning a cloud seat **without its key set** is recorded
honestly — the assignment exists, and every display flags that
it cannot serve. This is the demo machine's real state (no keys
are set here), shown against the stub seat of the next chapter
so the serving Ollama lines are visible too:

```
$ godfather_wizard models
[OK] model seats — Ollama is serving:
  qwen2.5-coder:3b-instruct  <- seated
  llama3.2:3b
providers:
  Ollama (local — 127.0.0.1:11434): serving — 2 model(s)
  Meta (Muse) (cloud — api.meta.ai): key not set
  Anthropic (cloud — api.anthropic.com): key not set
  OpenAI (cloud — api.openai.com): key not set
  Google (cloud — generativelanguage.googleapis.com): key not set
  DeepSeek (cloud — api.deepseek.com): key not set
model assignments (~/.godfather/models.json):
  default: (not set — effective seat: ollama · qwen2.5-coder:3b-instruct)
  brainstorm: (not set — effective seat: ollama · qwen2.5-coder:3b-instruct)
  build: (not set — effective seat: ollama · qwen2.5-coder:3b-instruct)
  debug: (not set — effective seat: ollama · qwen2.5-coder:3b-instruct)
  diff: (not set — effective seat: ollama · qwen2.5-coder:3b-instruct)
  audit: (not set — effective seat: ollama · qwen2.5-coder:3b-instruct)
guide: PROVIDERS.md — where to get each provider's key, and how to set up local models with Ollama
[exit 0]

$ godfather_wizard models set default anthropic:claude-sonnet-4-5
[OK] default model set to anthropic:claude-sonnet-4-5
[exit 0]

$ godfather_wizard models
[…providers as above…]
model assignments (~/.godfather/models.json):
  default: anthropic:claude-sonnet-4-5 (key not set)
  […other tasks unset…]
[exit 0]

$ godfather_wizard models unset default
[OK] default model assignment removed (anthropic:claude-sonnet-4-5)
[exit 0]
```

With `ANTHROPIC_API_KEY` exported, that same assignment serves
for real. The mechanism is identical for every provider:
`provider:model`, key from the environment at call time.

---

## 17. Seats at work — the codegen suite, against a stub seat

> **Read this first — what "stub seat" means.** The demo machine
> has no Ollama daemon. For this chapter a small test server was
> run locally: it answers in Ollama's exact shape (the same
> endpoints the toolkit calls) with **pre-written replies** — a
> fixed greeting module for `/build`, a fixed repaired file for
> `/debug` and `/diff`, a fixed brainstorm answer, a fixed
> summary for the oracle. No model generated any of it. What the
> stub proves is everything the *toolkit* does around a seat:
> the calls it makes (the stub logged 7 chat calls and 1 roster
> call for the session below), the diffs it renders, the staging,
> the double ask, the wall, the journaling. On your machine a
> local model serves the seat instead — see PROVIDERS.md — and
> the same commands are the completing proof.

The codegen suite is four REPL modes, inherited from the same
design as the rest of the fleet: a model only ever **suggests**.
It authors complete content; the toolkit shows a diff; the
person decides — twice — and only then does the Write Wizard
land it.

`/brainstorm` is hands-off by construction: the seat can talk
only. Note the stub's canned reply deliberately ends with a
`TOOL:` line — the kind of line that, in oracle mode, would run
a tool. In brainstorm it is treated as text, and the REPL says
so:

```
👑 godfather> /brainstorm how should I structure a greeting module?
[OK] brainstorm mode — hands off: the seat can talk only; no tools run and no files change. Use /brainstorm end to leave.

👑 godfather: Three shapes for a greeting module: a single greet function, a Greeter class with greet and farewell methods, or a pair of small functions the caller composes. The pair is the simplest and the easiest to test.
TOOL: godfather_wizard listing.

[NOTE] brainstorm is hands-off: a TOOL: line was treated as text; nothing executed.

👑 godfather> /brainstorm end
[OK] brainstorm mode ended — hands remain off
```

`/build`, first refused at the first ask — the proposal is
staged, the person says no, nothing is written, and the draft
stays in quarantine as evidence:

```
👑 godfather> /build greet.py a small module with a greet function and a farewell function
--- build proposal by seat: ollama · qwen2.5-coder:3b-instruct for greet.py ---
--- greet.py (current)
+++ greet.py (model proposal)
@@ -0,0 +1,13 @@
+"""Greeting helpers for the demo workspace."""
+
+
+def greet(name):
+    return f"Hello, {name}!"
+
+
+def farewell(name):
+    return f"Goodbye, {name}."
+
+
+if __name__ == "__main__":
+    print(greet("demo"))
[STAGED] build proposal for greet.py — 37c946d4154a367a.draft -> greet.py (202 chars quarantined)
⚠️  write the model's proposal to greet.py? [y/N] n
[CONSENT WALL] consent withheld — nothing written; the staged proposal stays in write_wizard's quarantine
```

The same `/build` again, this time carried through the **double
ask** — a plain `y`, then the typed confirmation naming exactly
what is being agreed to:

```
👑 godfather> /build greet.py a small module with a greet function and a farewell function
--- build proposal by seat: ollama · qwen2.5-coder:3b-instruct for greet.py ---
[…same diff as above…]
[STAGED] build proposal for greet.py — 37c946d4154a367a.draft -> greet.py (202 chars quarantined)
⚠️  write the model's proposal to greet.py? [y/N] y
confirm by typing: yes, write greet.py
> yes, write greet.py
[OK] /home/hatch/workspace/ds/home/.write-wizard/pending/37c946d4154a367a.draft
[NOTE] new file: greet.py does not exist yet
--- proposed (first 800 chars) ---
"""Greeting helpers for the demo workspace."""


def greet(name):
    return f"Hello, {name}!"


def farewell(name):
    return f"Goodbye, {name}."


if __name__ == "__main__":
    print(greet("demo"))

[OK] build proposal written to greet.py through write_wizard
```

`/debug` works the same way against an existing file — the seat
gets the file plus the Python Wizard's check verdict and returns
complete repaired content. (The seat's reply here is the stub's
pre-written repair.)

```
👑 godfather> /debug flawed.py
[NOTE] flawed.py exists — this is a full-content revision
--- debug proposal by seat: ollama · qwen2.5-coder:3b-instruct for flawed.py ---
--- flawed.py (current)
+++ flawed.py (model proposal)
@@ -1,28 +1,23 @@
-"""Demo module with deliberate flaws for the audit wizards to find."""
+"""Demo module, repaired by the seat: flaws fixed, behavior kept."""
 import os
 import subprocess
-import sys
-import json  # unused on purpose
-
-API_KEY = "sk-demo-1234567890abcdef"
-
-# TODO: move the key into the environment before shipping
 
 
 def run_report():
-    # TODO: replace the shell call with an argv list
-    return subprocess.run("ls -la", shell=True, capture_output=True, text=True)
+    return subprocess.run(["ls", "-la"], capture_output=True, text=True)
 
 
 def evaluate(expression):
-    """Evaluate an arithmetic string (dangerous on purpose)."""
-    return eval(expression)
+    """Evaluate an arithmetic string safely (literals only)."""
+    import ast
+
+    return ast.literal_eval(expression)
 
 
 def divide(a, b):
     try:
         return a / b
-    except:
+    except ZeroDivisionError:
         return None
[…]
[STAGED] debug proposal for flawed.py — a940135f5a4b3ea2.draft -> flawed.py (539 chars quarantined)
⚠️  write the model's proposal to flawed.py? [y/N] y
confirm by typing: yes, write flawed.py
> yes, write flawed.py
[…write_wizard shows the disk→draft diff, then…]
[OK] debug proposal written to flawed.py through write_wizard
```

`/diff` in its proposal form is **review only** — a diff to
read, nothing staged, nothing asked. And the two-file form of
`/diff` still does what it always did (the argument shape
decides which `/diff` you mean):

```
👑 godfather> /diff flawed.py add a farewell function
[NOTE] flawed.py exists — this is a full-content revision
--- diff proposal by seat: ollama · qwen2.5-coder:3b-instruct for flawed.py ---
--- flawed.py (current)
+++ flawed.py (model proposal)
@@ -27,3 +27,7 @@

 if __name__ == "__main__":
     print(greet("demo"))
+
+
+def farewell(name):
+    return f"Goodbye, {name}."

👑 godfather> /diff before.txt after.txt
--- before.txt
+++ after.txt
@@ -1,4 +1,5 @@
 Wizard Central Toolkit demo notes.
-The fleet has twelve wizards.
+The fleet has twelve wizards and one router.
 Every write crosses the consent wall.
 Local first, always.
+Receipts for every crossing.

[FAIL] files differ
```

Finally, plain language with a seat: the question matches no
deterministic route, so the oracle consults the seat. The seat
answers with a tool request; the toolkit runs its own listing
sense and hands the result back; the seat summarizes. (Against
the stub, the summary text is pre-written; against your model,
the model writes it from the real listing.)

```
👑 godfather> what files are in this workspace
🤖 consulting oracle (seat: ollama · qwen2.5-coder:3b-instruct)...
🔧 godfatherwiz listing.

👑 godfather: The workspace holds the demo fixtures: flawed.py with seeded security findings, a crasher and its traceback, the JSON fixtures, the diff pair, and the Rust fixture.

👑 godfather> /quit
[OK] Godfather bows out. Sovereignty preserved.
```

What the accepted writes left behind — the build's file exists
with the seat's content, and the debugged file now passes the
Python Wizard's check:

```
$ ls greet.py && python_wizard check flawed.py
greet.py
[OK] flawed.py

$ head -8 greet.py
"""Greeting helpers for the demo workspace."""


def greet(name):
    return f"Hello, {name}!"


def farewell(name):
```

---

## 18. Code Guard Wizard — the model engine

> Stub-seat chapter, like section 17: the audit findings and
> the fixed code below are the stub's pre-written replies, in the
> exact shapes a real coder model returns. What is proven is the
> toolkit's side — the calls, the parsing, the gate, the wall.

The second engine. Where the static engine applies nine fixed
rules, the model engine seats a coder model as auditor: it reads
the file and reports issues in its own judgment — severity,
category, line range, and a suggested fix for each — plus a
score. `roster` now shows the seat serving, and which model the
audit/fix preference order picked:

```
$ codeguard_wizard roster
engine: model seat
engines:
[OK] static (built-in rules) — always available, no daemon needed
     rules:
     […the nine CG rules, as in section 5…]
[OK] model seat — daemon serves 2 model(s):
[OK] llama3.2:3b
[OK] qwen2.5-coder:3b-instruct <- audit/fix
[exit 0]

$ codeguard_wizard audit --engine model modelcheck.py
engine: model seat
[OK] modelcheck.py (python, model qwen2.5-coder:3b-instruct, score 38)
     issues: CRITICAL=1 HIGH=2 MEDIUM=1 LOW=1
     [CRITICAL] eval() executes a string as code (line [19, 19])
     [HIGH] Hardcoded API key (line [7, 7])
     [HIGH] subprocess call with shell=True (line [14, 14])
     [MEDIUM] Bare except (line [25, 25])
     [LOW] TODO marker left in the code (line [9, 9])
[exit 0]

$ codeguard_wizard scan --engine model modelcheck.py
engine: model seat
[OK] scanned 1 files
     CRITICAL=1 HIGH=2
     findings:
       modelcheck.py: C=1 H=2
[exit 1]

$ codeguard_wizard severity --engine model modelcheck.py
engine: model seat
[OK] HIGH+ severity: 3 findings
     [CRITICAL] eval() executes a string as code (line [19, 19])
     [HIGH] Hardcoded API key (line [7, 7])
     [HIGH] subprocess call with shell=True (line [14, 14])
[exit 1]
```

(`modelcheck.py` is a byte-identical copy of the flawed
fixture, kept pristine so the model runs never touch the
original. The two engines agree on this file's five real
problems — the static engine found the same five, plus the
second TODO.)

The model `fix` first runs as a preview — the seat's complete
corrected code, printed, disk untouched, with the consent lane
named:

```
$ codeguard_wizard fix --engine model modelcheck.py
engine: model seat
[OK] fix generated (5 issues, model qwen2.5-coder:3b-instruct) - preview only, disk untouched:
--- fixed code follows ---
"""Demo module, repaired by the seat: flaws fixed, behavior kept."""
[…the seat's complete repaired file — the same content the
/debug proposal carried in section 17…]
--- end ---
consent lane: re-run with --write to replace the file (or --out <path>)
[exit 0]
```

With `--write`, the fix does **not** write directly: it passes
the Python Wizard's syntax gate, stages through the Write
Wizard, and asks twice. Shown on `fixme.py`, another copy of
the fixture — refused first:

```
$ printf "n\n" | codeguard_wizard fix --engine model --write fixme.py
engine: model seat
[OK] pythonwiz gate passed
[STAGED] model fix for fixme.py — 9287db6521310194.draft -> fixme.py (538 chars quarantined)
⚠️  write the model's fix to fixme.py? [y/N] [CONSENT WALL] consent withheld — nothing written; the staged fix stays in writewiz's quarantine
[exit 1]

$ grep -c "eval" fixme.py
2
```

—the file still holds the flawed original (the word `eval`
appears twice: the call and its docstring warning). Then
accepted, with the typed second confirmation:

```
$ printf "y\nyes, write fixme.py\n" | codeguard_wizard fix --engine model --write fixme.py
engine: model seat
[OK] pythonwiz gate passed
[STAGED] model fix for fixme.py — 9287db6521310194.draft -> fixme.py (538 chars quarantined)
⚠️  write the model's fix to fixme.py? [y/N] confirm by typing: yes, write fixme.py
> [OK] /home/hatch/workspace/ds/home/.write-wizard/pending/9287db6521310194.draft
--- diff (disk -> proposed) ---
[…the repair diff, as in section 17…]
[OK] written: fixme.py (issues addressed: 5)
[exit 0]

$ python_wizard check fixme.py
[OK] fixme.py
[exit 0]

$ codeguard_wizard audit --engine static fixme.py
engine: static (built-in rules)
[OK] fixme.py (python, static rules)
     findings: HIGH=0 MEDIUM=0 LOW=0
     verdict: [OK] no high-severity findings
[exit 0]
```

The closing proof of the chapter: the other engine re-audits
the model's fix and finds nothing left.

### A defect this demo found — and its fix

The first run of this demo caught `explain` by file and line
failing under the model engine: the audit above reports the
`eval()` issue at line 19, and explain, asked about that very
line, answered that there was nothing there. The cause was
visible in the output itself: the model audit reports line
ranges as `[19, 19]` (a pair), while the explain lookup only
understood ranges in text form, so the two never matched.

The lookup now reads the pair form as well as the text forms.
The same two commands, re-run after the fix:

```
$ codeguard_wizard explain --engine static flawed.py 19
engine: static (built-in rules)
[OK] Rule at line 19:
     Severity: HIGH
     Title: CG003 eval-exec
     […the full explanation, as in section 5…]
[exit 0]

$ codeguard_wizard explain --engine model modelcheck.py 19
engine: model seat
[OK] Rule at line 19:
     Severity: CRITICAL
     Title: eval() executes a string as code
     Message: eval() runs any string as Python; if any part is influenced from outside, the caller can run anything.
[exit 0]
```

`explain` by file and line now works under both engines —
and by rule id, as in section 5.

---

## 19. Verification

Everything above ran against a fresh, non-editable install of
the package in a clean virtual environment, with the
environment's `bin` on `PATH` and a sandbox `HOME`, on
2026-11-09. The toolkit's own test suite, run in full against
the same tree:

```
$ python -m pytest
560 passed
```

What this demo did **not** prove, by design, and what completes
it on your machine:

- **A live local seat.** The seat-dependent chapters ran against
  a stub seat with pre-written replies. Run Ollama with a coder
  model seated (PROVIDERS.md walks it) and repeat sections 17–18:
  the same commands, your model's own words in the seats.
- **A live cloud seat.** No provider keys exist on the demo
  machine; the keyless-assignment behavior is shown as-run in
  section 16. With a key exported, `godfather_wizard models`
  shows the seat serving.
- **Rust verdicts.** The Rust Wizard's tool-backed commands are
  shown giving their honest no-toolchain refusal (section 11);
  with rustc and cargo installed they report real verdicts.

The fleet's promise is the one the seatless runs already keep:
what a wizard cannot do, it says — by name, with the reason,
and with the way to fix it in your hands.
