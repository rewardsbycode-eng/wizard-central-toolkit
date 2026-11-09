# Security

The Wizard Central Toolkit is local-first: it runs on your
machine, phones nothing home, and asks before it writes —
file changes go through the Write Wizard's consent wall,
and shell commands can be checked against the Read
Wizard's verb gate before
they run.

## Model providers

The Godfather Wizard can seat a model at six providers. Ollama is
local and needs no key. The five cloud providers (Meta
(Muse), Anthropic, OpenAI, Google, DeepSeek) are opt-in: each
is used only when you assign a `provider:model` seat, and
only with your own API key, read from your environment
(`MODEL_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
`GEMINI_API_KEY`, `DEEPSEEK_API_KEY`) at call time. Keys are
never stored in the Godfather Wizard's bank, never journaled, and
never printed — status displays say only whether a key is
set. When a cloud seat is used, the prompts — and, for the
codegen `/build`, `/debug`, and `/diff` modes, the file
contents involved — are sent to that provider over HTTPS.
With an Ollama seat (or no seat), nothing leaves the machine.

[PROVIDERS.md](PROVIDERS.md) is the setup guide: where each
provider's key comes from, and how to run local models with
Ollama.

To report a vulnerability, open a private security advisory
or an issue on the GitHub repository:
https://github.com/rewardsbycode-eng/wizard-central-toolkit

Only the latest release is supported.
