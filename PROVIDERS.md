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
- **A subscription is not an API key.** A consumer subscription
  to any AI product — a chat plan, a pro tier, anything like
  it — does not include developer API access. Every cloud seat
  below needs its own developer API key, made at the provider's
  own dashboard. That is the providers' rule, not ours.

Assignments are made with:

```
godfather_wizard models set <task> <seat>
```

where a seat is a bare Ollama model name (`llama3.2:3b`) or a
provider-qualified name (`anthropic:claude-sonnet-4-5`).
`godfather_wizard models` shows the providers, the live
roster, and the assignments at any time.

---

## Part 1 — Local and free, from zero: Ollama

Ollama runs open models on your own machine. No account, no
key, no per-token bill, and nothing leaves the machine. It is
the seat that ships in the box, and the toolkit is built to
work with the smallest models first — if it works with the
weakest model you have, it works with any model.

### Install Ollama

On macOS or Linux, Ollama's own one-liner:

```
curl -fsSL https://ollama.com/install.sh | sh
```

On Windows, and for the macOS app, download the installer
from <https://ollama.com/download> and run it like any other
program. Either way, check the install:

```
ollama --version
```

Ollama then serves on your machine at `127.0.0.1:11434`.

### Pull your first models

`ollama pull` downloads a model; `ollama run` pulls it if
needed and opens a chat with it. Start small:

```
ollama pull llama3.2:1b
ollama pull llama3.2:3b
ollama pull qwen2.5-coder:3b
ollama list
```

- `llama3.2:1b` — the floor: the smallest sensible seat, for
  the weakest machines.
- `llama3.2:3b` — a good general default seat.
- `qwen2.5-coder:3b` — a small coder, suited to the `build`,
  `debug`, and `diff` seats.

`ollama list` shows your roster. The full library is at
ollama.com; bigger models are there when your hardware wants
them, but nothing in the toolkit requires one.

### How the Godfather Wizard finds the seat

It reads Ollama's live roster itself — there is nothing to
configure. Run:

```
godfather_wizard models
```

and the roster is listed, with the model that would serve
marked. To name the seat explicitly, assign a bare model
name:

```
godfather_wizard models set default llama3.2:3b
```

An assigned model that is not in the live roster is reported
honestly and never silently replaced.

### ollmcp — an MCP client for your own Ollama

If you want your local models to use tools through the Model
Context Protocol (MCP), there is a free client built for
exactly that: the **MCP Client for Ollama**, run as
**`ollmcp`** (project: `mcp-client-for-ollama`, by jonigl).
It connects one or more MCP servers to your local Ollama
models and lets the models call the servers' tools. It needs
Python 3.10+, Ollama running, and — for the `uvx` route —
the uv package manager. Install and run it either way:

```
pip install ollmcp
ollmcp
```

```
uvx ollmcp
```

Its homes are its PyPI page (project `mcp-client-for-ollama`)
and its GitHub repository (github.com/jonigl/mcp-client-for-ollama).

**The honest note, in plain words:** ollmcp works standalone
— install it, pair it with your Ollama, and your models can
use MCP tools. But it is *your own* MCP layer, not Wizard
Central's. It does not carry this toolkit's or Pro's
protection: the free toolkit has no MCP gate of its own, and
ollmcp adds none — no MCP gate deciding what a model may
reach, no double-ask consent wall before a model's action
lands, no grants, and no hash-chained receipts of what
crossed. The gated, twice-asked, receipted bridge is part of
the Wizard Central Pro AI Modes Toolkit. If what you want is
a local model talking to MCP tools today, ollmcp is a good
free way to do it — just know which layer you are standing
on.

---

## Part 2 — The five cloud seats

Each cloud seat follows the same pattern: make a developer
API key at the provider's own dashboard, export it under the
variable the toolkit reads, then assign the seat. Copy every
key the moment it is shown — dashboards show a key in full
only once. Export in the same shell you run the wizard from,
for example:

```
export ANTHROPIC_API_KEY=<your key>
```

### Meta — `meta`

Meta's developer API is the **Meta
...[truncated 3391 chars]