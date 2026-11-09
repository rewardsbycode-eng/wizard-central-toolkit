"""Provider layer — six seats for godfatherwiz (AVS, 2026-11-09).

Ollama stays local and unchanged. The five cloud providers are
seated only with the user's own key, read from the environment at
call time. These tests run local stub HTTP servers — no network —
and prove the request shapes, the response parsing, the seat
resolution, and that no key value ever reaches a display.
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from wiz_central_toolkit.godfatherwiz.lib import cli as gf_cli
from wiz_central_toolkit.godfatherwiz.lib import godfather_wizard as gw
from wiz_central_toolkit.writewiz import write_wizard as ww

_KEY_ENVS = ("MODEL_API_KEY", "META_API_KEY", "ANTHROPIC_API_KEY",
             "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
             "DEEPSEEK_API_KEY")


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    bank = home / ".godfather"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(gw, "HOME", home)
    monkeypatch.setattr(gw, "BANK", bank)
    monkeypatch.setattr(gw, "LEDGER", bank / "ledger.jsonl")
    monkeypatch.setattr(gw, "ROUTER_DB", bank / "routes.json")
    monkeypatch.setattr(gw, "STATE_FILE", bank / "session_state.json")
    monkeypatch.setattr(gw, "BIN", home / "bin")
    monkeypatch.delenv("GODFATHER_MODEL", raising=False)
    for env in _KEY_ENVS:
        monkeypatch.delenv(env, raising=False)
    monkeypatch.setattr(gf_cli, "speak_if_enabled", lambda text: None)

    write_bank = home / ".write-wizard"
    monkeypatch.setattr(ww, "HOME", home)
    monkeypatch.setattr(ww, "BANK", write_bank)
    monkeypatch.setattr(ww, "QUARANTINE", write_bank / "pending")
    monkeypatch.setattr(ww, "BACKUPS", write_bank / "backups")
    monkeypatch.setattr(ww, "LEDGER", write_bank / "ledger.jsonl")
    monkeypatch.setattr(ww, "PROTECTED", write_bank / "protected.json")
    return home


class StubServer:
    """A local HTTP stub: records requests, serves queued replies."""

    def __init__(self, responses):
        self.responses = list(responses)  # (status, json payload)
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                outer.requests.append({
                    "path": self.path,
                    "headers": {k.lower(): v for k, v in
                                self.headers.items()},
                    "body": json.loads(body) if body else {},
                })
                status, payload = outer.responses.pop(0) \
                    if outer.responses else (200, {})
                raw = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *args):
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True)

    def url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._server.shutdown()
        self._server.server_close()


def _point_at(monkeypatch, provider_id, url):
    monkeypatch.setitem(gw.PROVIDERS[provider_id], "url", url)


def _openai_reply(text):
    return (200, {"choices": [{"message": {"content": text}}]})


# ------------------------------------------------------------ parsing

def test_parse_seat_bare_names_stay_ollama():
    assert gw.parse_seat("m1") == ("ollama", "m1")
    assert gw.parse_seat("llama3.2:1b") == ("ollama", "llama3.2:1b")
    assert gw.parse_seat("qwen2.5-coder:7b-instruct") == \
        ("ollama", "qwen2.5-coder:7b-instruct")


def test_parse_seat_provider_qualified():
    assert gw.parse_seat("anthropic:claude-sonnet-4-5") == \
        ("anthropic", "claude-sonnet-4-5")
    assert gw.parse_seat("meta:muse-spark-1.3") == \
        ("meta", "muse-spark-1.3")
    assert gw.parse_seat("ollama:mistral:latest") == \
        ("ollama", "mistral:latest")
    assert gw.seat_label(("deepseek", "deepseek-chat")) == \
        "deepseek · deepseek-chat"


# ------------------------------------------------------- request shape

def test_deepseek_stub_request_and_reply(home, monkeypatch):
    with StubServer([_openai_reply("hello from deepseek")]) as stub:
        _point_at(monkeypatch, "deepseek",
                  stub.url("/v1/chat/completions"))
        monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy-deepseek-key")
        out = gw.call_seat_chat(
            ("deepseek", "deepseek-chat"),
            [{"role": "user", "content": "hi"}])
    assert out == "hello from deepseek"
    req = stub.requests[0]
    assert req["path"] == "/v1/chat/completions"
    assert req["headers"]["authorization"] == "Bearer dummy-deepseek-key"
    assert req["body"]["model"] == "deepseek-chat"
    assert req["body"]["messages"] == [{"role": "user", "content": "hi"}]


def test_openai_stub_request_and_reply(home, monkeypatch):
    with StubServer([_openai_reply("openai here")]) as stub:
        _point_at(monkeypatch, "openai", stub.url("/v1/chat/completions"))
        monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai-key")
        out = gw.call_seat_chat(("openai", "gpt-x"),
                                [{"role": "user", "content": "hi"}])
    assert out == "openai here"
    assert stub.requests[0]["headers"]["authorization"] == \
        "Bearer dummy-openai-key"


def test_meta_seat_points_at_meta_model_api():
    # The corrected door (2026-11-09): Meta retired the Llama API
    # preview; the Meta seat speaks to the Meta Model API, which
    # serves the Muse models, with Meta's prescribed key variable.
    spec = gw.PROVIDERS["meta"]
    assert spec["host"] == "api.meta.ai"
    assert spec["url"] == "https://api.meta.ai/v1/chat/completions"
    assert spec["key_envs"] == ("MODEL_API_KEY", "META_API_KEY")
    assert spec["display"] == "Meta (Muse)"


def test_meta_key_env_and_fallback(home, monkeypatch):
    with StubServer([_openai_reply("meta one"),
                     _openai_reply("meta two")]) as stub:
        _point_at(monkeypatch, "meta", stub.url("/v1/chat/completions"))
        monkeypatch.setenv("MODEL_API_KEY", "dummy-model-key")
        assert gw.call_seat_chat(("meta", "muse-spark-1.3"), []) == \
            "meta one"
        req = stub.requests[0]
        assert req["path"] == "/v1/chat/completions"
        assert req["headers"]["authorization"] == \
            "Bearer dummy-model-key"
        assert req["body"]["model"] == "muse-spark-1.3"
        monkeypatch.delenv("MODEL_API_KEY")
        monkeypatch.setenv("META_API_KEY", "dummy-meta-key")
        assert gw.call_seat_chat(("meta", "muse-spark-1.3"), []) == \
            "meta two"
        assert stub.requests[1]["headers"]["authorization"] == \
            "Bearer dummy-meta-key"


def test_meta_missing_key_names_model_api_key(home):
    with pytest.raises(RuntimeError) as excinfo:
        gw.call_seat_chat(("meta", "muse-spark-1.3"),
                          [{"role": "user", "content": "hi"}])
    assert "MODEL_API_KEY is not set" in str(excinfo.value)


def test_google_key_env_and_fallback(home, monkeypatch):
    with StubServer([_openai_reply("google one"),
                     _openai_reply("google two")]) as stub:
        _point_at(monkeypatch, "google",
                  stub.url("/v1beta/openai/chat/completions"))
        monkeypatch.setenv("GEMINI_API_KEY", "dummy-gemini-key")
        assert gw.call_seat_chat(("google", "gemini-x"), []) == \
            "google one"
        assert stub.requests[0]["path"] == \
            "/v1beta/openai/chat/completions"
        assert stub.requests[0]["headers"]["authorization"] == \
            "Bearer dummy-gemini-key"
        monkeypatch.delenv("GEMINI_API_KEY")
        monkeypatch.setenv("GOOGLE_API_KEY", "dummy-google-key")
        assert gw.call_seat_chat(("google", "gemini-x"), []) == \
            "google two"
        assert stub.requests[1]["headers"]["authorization"] == \
            "Bearer dummy-google-key"


def test_anthropic_blocks_system_and_headers(home, monkeypatch):
    payload = {"content": [
        {"type": "text", "text": "hello "},
        {"type": "tool_use", "id": "x", "name": "noop", "input": {}},
        {"type": "text", "text": "world"},
    ]}
    with StubServer([(200, payload)]) as stub:
        _point_at(monkeypatch, "anthropic", stub.url("/v1/messages"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic-key")
        out = gw.call_seat_chat(("anthropic", "claude-sonnet-4-5"), [
            {"role": "system", "content": "be terse"},
            {"role": "user", "content": "hi"},
        ])
    assert out == "hello world"
    req = stub.requests[0]
    assert req["path"] == "/v1/messages"
    assert req["headers"]["x-api-key"] == "dummy-anthropic-key"
    assert req["headers"]["anthropic-version"] == "2023-06-01"
    assert req["body"]["model"] == "claude-sonnet-4-5"
    assert req["body"]["max_tokens"] >= 1024
    assert req["body"]["system"] == "be terse"
    assert req["body"]["messages"] == [{"role": "user", "content": "hi"}]


def test_http_error_line_has_status_and_message_not_key(
        home, monkeypatch):
    with StubServer([(401, {"error": {"message": "bad key"}})]) as stub:
        _point_at(monkeypatch, "openai", stub.url("/v1/chat/completions"))
        monkeypatch.setenv("OPENAI_API_KEY", "dummy-secret-key")
        with pytest.raises(RuntimeError) as excinfo:
            gw.call_seat_chat(("openai", "gpt-x"),
                              [{"role": "user", "content": "hi"}])
    line = str(excinfo.value)
    assert "HTTP 401" in line and "bad key" in line
    assert "dummy-secret-key" not in line


def test_missing_key_call_is_an_honest_line(home):
    with pytest.raises(RuntimeError) as excinfo:
        gw.call_seat_chat(("deepseek", "deepseek-chat"),
                          [{"role": "user", "content": "hi"}])
    assert "DEEPSEEK_API_KEY is not set" in str(excinfo.value)


# --------------------------------------------------------- seat ruling

def test_cloud_seat_resolution_and_key_missing_honesty(
        home, monkeypatch):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: [])
    assert gw.set_model_assignment(
        "build", "anthropic:claude-sonnet-4-5")[0] == 0
    # no key: no seat, and the line names what is missing
    assert gw.seat_for("build") is None
    line = gw.seat_unavailable_line("build")
    assert "anthropic:claude-sonnet-4-5" in line
    assert "ANTHROPIC_API_KEY is not set" in line
    # key present (read from env): the seat is configured
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic-key")
    assert gw.seat_for("build") == ("anthropic", "claude-sonnet-4-5")


def test_cloud_default_fallback_and_task_override(home, monkeypatch):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: [])
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy-deepseek-key")
    assert gw.set_model_assignment("default", "openai:gpt-x")[0] == 0
    assert gw.seat_for("debug") == ("openai", "gpt-x")
    assert gw.set_model_assignment(
        "debug", "deepseek:deepseek-chat")[0] == 0
    assert gw.seat_for("debug") == ("deepseek", "deepseek-chat")
    assert gw.seat_for("diff") == ("openai", "gpt-x")


def test_tagged_bare_name_still_resolves_as_ollama(home, monkeypatch):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: ["llama3.2:1b"])
    assert gw.set_model_assignment("build", "llama3.2:1b")[0] == 0
    assert gw.seat_for("build") == ("ollama", "llama3.2:1b")


def test_models_set_validates_provider(home, monkeypatch):
    rc, out = gw.set_model_assignment("build", "bogus:some-model")
    assert rc == 2
    for pid in ("ollama", "meta", "anthropic", "openai", "google",
                "deepseek"):
        assert pid in out
    assert gw.load_model_assignments() == {}
    rc, _out = gw.set_model_assignment(
        "build", "anthropic:claude-sonnet-4-5")
    assert rc == 0
    assert json.loads((home / ".godfather" / "models.json").read_text()) \
        == {"build": "anthropic:claude-sonnet-4-5"}
    rc, _out = gw.set_model_assignment("build", "ollama:mistral:latest")
    assert rc == 0


# -------------------------------------------------------------- display

def test_models_display_never_prints_a_key(home, monkeypatch):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: [])
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-secret-key")
    assert gw.set_model_assignment(
        "build", "anthropic:claude-sonnet-4-5")[0] == 0
    rc, out = gw.seated_models()
    assert rc == 0
    assert "dummy-secret-key" not in out
    assert "build: anthropic:claude-sonnet-4-5 (key set)" in out
    for display in ("Ollama", "Meta (Muse)", "Anthropic", "OpenAI",
                    "Google", "DeepSeek"):
        assert display in out
    assert "key not set" in out  # the other providers, honestly


def test_models_display_points_at_providers_guide(home, monkeypatch):
    monkeypatch.setattr(gw, "_ollama_roster", lambda: [])
    rc, out = gw.seated_models()
    assert rc == 0
    assert "PROVIDERS.md" in out


# ------------------------------------------------------------ end to end

def _drive_repl(monkeypatch, lines):
    answers = iter(lines)
    monkeypatch.setattr(
        "builtins.input", lambda prompt="": next(answers))
    gf_cli.run_repl()


def test_build_lands_through_anthropic_seat(
        home, monkeypatch, capsys, tmp_path):
    target = tmp_path / "made.py"
    payload = {"content": [{"type": "text",
                            "text": "print('from anthropic')\n"}]}
    with StubServer([(200, payload)]) as stub:
        _point_at(monkeypatch, "anthropic", stub.url("/v1/messages"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic-key")
        monkeypatch.setattr(gw, "_ollama_roster", lambda: [])
        assert gw.set_model_assignment(
            "build", "anthropic:claude-sonnet-4-5")[0] == 0
        _drive_repl(monkeypatch, [
            f"/build {target} create a greeting",
            "y", f"yes, write {target}", "/exit"])
    out = capsys.readouterr().out
    assert target.read_text() == "print('from anthropic')\n"
    assert "seat: anthropic · claude-sonnet-4-5" in out
    rows = [r for r in gw.ledger_rows() if r["event"] == "CODEGEN"]
    assert len(rows) == 1 and "model=claude-sonnet-4-5" in rows[0]["detail"]
    req = stub.requests[0]
    assert req["headers"]["x-api-key"] == "dummy-anthropic-key"
    assert "build" in req["body"]["system"]


def test_oracle_one_round_on_deepseek_seat(home, monkeypatch, tmp_path):
    (tmp_path / "alpha.txt").write_text("a")
    replies = [
        _openai_reply(f"TOOL: godfatherwiz listing {tmp_path}"),
        _openai_reply("those are the files"),
    ]
    with StubServer(replies) as stub:
        _point_at(monkeypatch, "deepseek",
                  stub.url("/v1/chat/completions"))
        monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy-deepseek-key")
        monkeypatch.delenv("WIZ_AI_PROVIDER", raising=False)
        for attr in ("_last_calls", "_dup_count", "_last_result"):
            if hasattr(gw.oracle_tool_loop, attr):
                delattr(gw.oracle_tool_loop, attr)
        reply, memory = gw.oracle_tool_loop(
            "what files are here?", ("deepseek", "deepseek-chat"), [])
    assert reply == "those are the files"
    fed_back = "\n".join(m.get("content", "") for m in memory)
    assert "alpha.txt" in fed_back
    assert len(stub.requests) == 2
    assert stub.requests[0]["headers"]["authorization"] == \
        "Bearer dummy-deepseek-key"
