# Changelog

## 0.2.0 — 2026-11-08

- The sampler made whole for pip installs: godfatherwiz now
  resolves its sibling wizards from the installed package as
  well as the bin lane, and reports a wizard that is nowhere
  installed as honestly absent (never "reachable").
- FATHER LAW 1 amended to match: siblings are invoked where
  they live — the bin lane (~/bin) first, the installed package
  second; a sibling found nowhere is honestly absent.
- The October rename finished inside the package: the
  distribution is `wizard-central-toolkit` in pyproject, the
  README, the installer, and the two metadata lookups.
- README gains the door section: the Wizard Central Pro AI
  Modes Toolkit, still in the making, that this sampler is a
  window onto.
- COMMANDS.md added: every command, documented.
- Full-sweep fixes: godfatherwiz status probes the installed
  fleet (never absent citizens); diagnose calls commands that
  exist; debugwiz reads real tracebacks, stages its log and
  proposals through writewiz, and reports real timestamps;
  pythonwiz honors `#!/usr/bin/env` shebangs; bannerwiz
  --help/--version print text; a missing Rust toolchain is a
  plain sentence, never a traceback.
- rustwiz grows from 2 commands to 10 (run, test, clippy, fmt
  --check, doc, clean, law, version — every one a real verb of
  the toolchain it wraps); tmuxwiz gains capture and detach,
  plus law and version.
- codeguardwiz gains a second engine: built-in static rules
  (nine checks — syntax, hardcoded secrets, eval/exec, shell
  execution, pickle, weak hashes, bare and swallowed excepts,
  TODO markers) that audit Python with no model at all. The
  model seat remains the default whenever one is served;
  `--engine static|model` makes the choice the user's, and
  every output names the engine that produced it. Static fix
  stages its one deterministic rewrite through writewiz and
  never writes a file itself.
- README gains the full roster: all 41 wizards, each marked
  in this version or only in Pro.
- godfatherwiz's chains come home: audit is the truth anchor
  plus codeguardwiz audit; heal finds the sick file with
  debugwiz audit and stages the fix through debugwiz propose
  (writewiz's wall untouched); task is todowiz alone. And
  truthwiz's file senses — brief, listing, read, head, find,
  du, stat, symlinks — are absorbed into godfatherwiz, so
  `truth` and the REPL's /truth /ls /read /bins are served
  in-house; no command or slash was renamed or removed.
- Help parity: every wizard answers both `help` and `--help`
  with its own full command listing, exit 0 — bannerwiz no
  longer renders the word HELP as a banner, and godfatherwiz's
  bare `help` prints the full usage (a command name still
  gives that command's lines). A suite gate checks each
  wizard's help against the COMMANDS.md tables.
- REPL slash parity: every citizen in the box has a slash —
  /banner, /codeguard, /json, /rust, /tmux, /write, /verbs are
  new (35 in total). /fix and /heal no longer dispatch to the
  absent repairwiz: they run godfatherwiz's own heal chain,
  staging only. /models answers from the configured seats —
  the live Ollama roster when a daemon serves, one plain
  "no model seat" line when none does.
- REPL plain text routes first: the deterministic keyword
  router answers before the oracle is ever consulted, and the
  oracle speaks only when a model seat is actually serving —
  seatless unmapped text is "out of scope", never an oracle
  error. The oracle's instructions now teach godfatherwiz's
  own senses, and sense TOOL lines execute in-process end to
  end (a duplicate-shield NameError on that path is fixed).
- The consent wall is scoped to what it protects: route
  resolution in `godfatherwiz run` and the REPL walls only a
  route whose pipeline would change files — read-class routes
  run free whatever words the sentence carried, and staging
  routes (proposals) are suggestions, behind no wall. A
  write-class route asks twice — a plain ask, then a typed
  confirmation naming the action — before anything executes;
  there is no MCP gate in this project, so the double ask is
  the load-bearing wall.
- Small batch, the concluded remainders: codeguardwiz's model
  `fix --write` goes through the wall — the pythonwiz gate, then
  staging via writewiz, the double ask, and writewiz commit;
  a no at either ask writes nothing. The oracle's consent is at
  parity with `run`: staging TOOL lines never prompt, write-class
  lines ask twice, and a denial tells the model the Governor
  refused. debugwiz `stack` is real — a traceback digest (file
  or stdin) with the deepest project frame called out and
  repeated frames flagged as suspected recursion. FATHER LAW 2
  names godfatherwiz's own senses as the truth anchor, and the
  sampler's flavor stops borrowing Pro's numbers (no more
  "Citizen #33"). Two dead twin faces are removed —
  pythonwiz/cli.py (unimportable) and godfatherwiz/cli.py
  (stale, unreferenced) — and call_ollama no longer calls an
  ollamawiz that resolves nowhere.
- godfatherwiz gains the codegen suite in its REPL, inherited
  from devrepl's modes: /brainstorm (conversation with the tool
  channel off), /build and /debug (the seat authors complete
  content; the person reviews the full diff, answers the double
  ask, and only then writewiz commit lands it), and /diff
  (review-only — stages nothing, asks nothing, and remembers
  the proposal for a later /build or /debug). Nothing is auto:
  a model proposes, a person approves, in that order.
- Model seats become assignable per task: ~/.godfather/
  models.json holds `default`, `brainstorm`, `build`, `debug`,
  `diff`, and `audit` assignments (task, then default, then the
  live roster pick), managed with `godfatherwiz models`,
  `godfatherwiz models set`, and `godfatherwiz models unset`.
  One model can run everything; an assigned model that is not
  serving is reported honestly, never silently replaced.
- Seats gain providers: an assignment may now be
  `provider:model`, seating a model at one of five cloud
  providers — Meta (Muse), Anthropic, OpenAI, Google, and
  DeepSeek — beside the local Ollama seat. Cloud seats are the
  user's opt-in, seated only with the user's own API key read
  from the environment at call time; keys are never stored,
  journaled, or printed, and `godfatherwiz models` shows the
  six providers with key-set status only. Every model chat —
  the oracle and the four codegen modes — goes through one
  dispatch, and every model-authored proposal names its seat
  (`seat: <provider> · <model>`). Bare model names keep
  meaning Ollama, exactly as before.
