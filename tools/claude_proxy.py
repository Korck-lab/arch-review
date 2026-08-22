"""Local proxy: Anthropic Messages API -> `claude -p`.

A dev-only shim so an eval run can use Claude Code's local access instead of a
paid provider. The eval client relays native Anthropic Messages JSON to
`base_url`; this server translates each request into one `claude -p` call and
answers in Anthropic Message wire format. Auth is ignored.

Run:  python tools/claude_proxy.py [--port 8787]
Point the eval at it:
    [client]
    base_url = "http://127.0.0.1:8787"
    api_key_var = "CLAUDE_LOCAL_KEY"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# `claudei` is a shell launcher that sets ANTHROPIC_BASE_URL to the DeepSeek
# proxy and execs `claude`. We call the binary directly with that env, so the
# model path is identical and stdout is free of the launcher's banner lines.
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
# Model id passed to `claudei -p --model` for reviewer calls. Must be one the
# deepseek-in-claude proxy on :8016 registers; the display form
# `deepseek-v4-flash(1M)` is not recognized, its registered id is
# `claude-deepseek-v4-flash[1m]`.
PROXY_MODEL = os.environ.get("CLAUDE_PROXY_MODEL", "claude-deepseek-v4-flash[1m]")
# Stronger alias for judge calls. The eval asks for anthropic/claude-sonnet-5
# as judge; this local path has no sonnet, so the closest stronger model is
# deepseek-v4-pro, served under the same display-id convention on :8016.
PROXY_JUDGE_MODEL = os.environ.get(
    "CLAUDE_PROXY_JUDGE_MODEL", "claude-deepseek-v4-pro[1m]"
)
_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def strip_fences(text: str) -> str:
    """Remove markdown ```json fences the model may wrap JSON in. The eval's
    structured-output parser requires raw JSON; a fenced answer is a common
    LLM failure mode this shim tolerates."""
    return _FENCE.sub("", text).strip()


def request_model(body: dict) -> str | None:
    """The model for `claudei -p --model`, honoring the caller's request.

    The eval sends reviewer calls as deepseek/deepseek-v4-flash and judge
    calls as anthropic/claude-sonnet-5. A judge request maps to the stronger
    pro alias; anything else uses the pinned flash alias. A request that does
    not say flash or sonnet keeps the pinned default.
    """
    requested = (body.get("model") or "").lower()
    if "sonnet" in requested or "pro" in requested:
        return PROXY_JUDGE_MODEL
    return PROXY_MODEL


def schema_snippet(body: dict) -> dict | None:
    """The JSON schema a structured-output request carries, from `response_format`
    or the hidden schema tool. Real providers enforce it server-side; `claude -p`
    has no such mode, so the schema is injected into the prompt instead."""
    response_format = body.get("response_format")
    if isinstance(response_format, dict):
        schema = (response_format.get("json_schema") or {}).get("schema")
        if isinstance(schema, dict):
            return schema
    for tool in body.get("tools") or []:
        if not isinstance(tool, dict):
            continue
        function = tool.get("function") or {}
        if tool.get("type") == "function" and "input_schema" in function:
            input_schema = function.get("input_schema")
            if isinstance(input_schema, dict):
                return input_schema
    return None


def build_prompt(body: dict) -> str:
    """Flatten system + messages into one text prompt for `claude -p`.

    Handles both the Anthropic Messages shape (system + {role, content} where
    content is str or blocks) and the OpenAI Chat shape ({role, content} where
    content is str or a part list). A single joined prompt is the most robust
    translation: `claude -p` is one-shot, so exact turn fidelity is not needed.
    """
    parts: list[str] = []
    if schema := schema_snippet(body):
        parts.append("Output must be a single JSON object matching this JSON Schema:")
        parts.append(json.dumps(schema, indent=2))
    system = body.get("system")
    if isinstance(system, str) and system:
        parts.append(system)
    elif isinstance(system, list):
        parts.extend(b.get("text", "") for b in system if b.get("type") == "text")
    for message in body.get("messages", []):
        role = message.get("role", "user")
        content = message.get("content")
        if isinstance(content, str):
            parts.append(f"{role}: {content}")
        elif isinstance(content, list):
            text = "\n".join(
                b.get("text", "") for b in content if b.get("type") == "text"
            )
            if text:
                parts.append(f"{role}: {text}")
    return "\n\n".join(parts)


# The deepseek-in-claude proxy. The `claudei` launcher points `claude` at it
# with ANTHROPIC_BASE_URL and a gateway-discovery flag; we replicate exactly
# that wiring instead of invoking claudei.sh, whose stdout banners would land
# in the completion text.
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "http://localhost:8016")


def run_claude(prompt: str, model: str | None, timeout: int = 300) -> tuple[str, str]:
    """One `claude -p` call -> (stdout, stderr). Raises on nonzero exit."""
    argv = [CLAUDE_BIN, "-p", "--output-format", "text", "--dangerously-skip-permissions"]
    if model:
        argv += ["--model", model]
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = DEEPSEEK_BASE_URL
    env["CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY"] = "1"
    # The CLI auto-generates a session title with the configured default model.
    # A gateway model alias makes that call hard-fail and exits `claude -p`
    # with code 1 before any output. Title generation is nonessential traffic;
    # disable it so the model is only used for the actual completion.
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    proc = subprocess.run(
        argv,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed ({proc.returncode}): {proc.stderr.strip()[-800:]}")
    return proc.stdout.strip(), proc.stderr


def estimate_tokens(text: str) -> int:
    """Rough char/4 estimate; the exact count does not affect scoring."""
    return max(1, len(text) // 4)


def message_response(body: dict, text: str, output_tokens: int) -> dict:
    """A valid Anthropic Message object from one text completion."""
    model = body.get("model") or "claude"
    return {
        "id": "msg_local_claude_proxy",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": estimate_tokens(json.dumps(body)),
            "output_tokens": output_tokens,
        },
    }


def stream_events(response: dict) -> list[bytes]:
    """The minimal Anthropic SSE sequence for one text completion."""
    def event(kind: str, payload: dict) -> bytes:
        return f"event: {kind}\ndata: {json.dumps(payload)}\n\n".encode()

    head = {**response, "content": [], "stop_reason": None, "stop_sequence": None}
    text = response["content"][0]["text"]
    return [
        event("message_start", {"type": "message_start", "message": head}),
        event("content_block_start", {
            "type": "content_block_start", "index": 0,
            "content_block": {"type": "text", "text": ""},
        }),
        event("content_block_delta", {
            "type": "content_block_delta", "index": 0,
            "delta": {"type": "text_delta", "text": text},
        }),
        event("content_block_stop", {"type": "content_block_stop", "index": 0}),
        event("message_delta", {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn", "stop_sequence": None},
            "usage": response.get("usage") or {},
        }),
        event("message_stop", {"type": "message_stop"}),
    ]


def chat_response(body: dict, text: str, output_tokens: int) -> dict:
    """A valid OpenAI chat.completion object from one text completion."""
    model = body.get("model") or "claude"
    prompt_tokens = estimate_tokens(json.dumps(body))
    return {
        "id": "chatcmpl_local_claude_proxy",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": prompt_tokens + output_tokens,
        },
    }


def chat_stream_chunks(response: dict) -> list[bytes]:
    """The minimal OpenAI SSE sequence for one text completion."""
    base = {k: v for k, v in response.items() if k != "choices"}
    text = response["choices"][0]["message"]["content"]
    chunks = [
        {"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None},
        {"index": 0, "delta": {"content": text}, "finish_reason": None},
        {"index": 0, "delta": {}, "finish_reason": "stop"},
    ]
    out = []
    for choice in chunks:
        payload = {**base, "choices": [choice]}
        out.append(f"data: {json.dumps(payload)}\n\n".encode())
    out.append(b"data: [DONE]\n\n")
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass  # quiet; the eval logs enough

    def _reply_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _reply_sse(self, chunks: list[bytes]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        for chunk in chunks:
            self.wfile.write(chunk)
            self.wfile.flush()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        if path.endswith("/count_tokens"):
            self._reply_json(200, {"input_tokens": estimate_tokens(raw.decode())})
            return
        try:
            body = json.loads(raw or b"{}")
            prompt = build_prompt(body)
            if not prompt.strip():
                self._reply_json(400, {
                    "error": {"type": "invalid_request_error", "message": "empty prompt"}
                })
                return
            try:
                text, _ = run_claude(prompt, request_model(body))
            except RuntimeError as e:
                self._reply_json(502, {
                    "error": {"type": "api_error", "message": str(e)}
                })
                return
            if body.get("response_format"):
                # Structured-output requests: the eval's SDK parses the text as JSON.
                text = strip_fences(text)
            output_tokens = estimate_tokens(text)
            if path.endswith("/chat/completions"):
                response = chat_response(body, text, output_tokens)
                if body.get("stream"):
                    self._reply_sse(chat_stream_chunks(response))
                else:
                    self._reply_json(200, response)
            elif path.endswith("/messages"):
                response = message_response(body, text, output_tokens)
                if body.get("stream"):
                    self._reply_sse(stream_events(response))
                else:
                    self._reply_json(200, response)
            else:
                self._reply_json(404, {
                    "error": {"type": "invalid_request_error", "message": f"no route {path}"}
                })
        except Exception as e:  # noqa: BLE001 - surface any parse/build failure to the eval
            self._reply_json(500, {"error": {"type": "api_error", "message": str(e)}})

    do_GET = do_POST


def main() -> None:
    parser = argparse.ArgumentParser(description="Anthropic Messages API -> claude -p proxy")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"claude -p proxy on http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
