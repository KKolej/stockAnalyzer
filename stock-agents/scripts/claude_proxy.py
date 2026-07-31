#!/usr/bin/env python3
"""Proxy HTTP dla `claude -p` (subskrypcja Claude Code, bez płatnego API).

Uruchamiaj NA HOŚCIE (tam gdzie zalogowany Claude Code, nie w Dockerze):

    python3 scripts/claude_proxy.py

n8n (w kontenerze) woła go przez node HTTP Request:

    POST http://host.docker.internal:8787
    Body (JSON): {"prompt": "...", "system": "opcjonalnie", "model": "opcjonalnie"}

Odpowiedź: {"response": "..."} albo {"error": "..."}.

Uwaga: nasłuchuje na 0.0.0.0 (musi być osiągalny z sieci Dockera).
Na maszynie wystawionej do internetu ogranicz port 8787 firewallem.
Czysto stdlib — zero zależności.
"""
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("CLAUDE_PROXY_PORT", "8787"))
TIMEOUT = int(os.environ.get("CLAUDE_PROXY_TIMEOUT", "300"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 — konwencja http.server
        self._json(200, {"status": "ok", "usage": 'POST {"prompt": "..."}'})

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            prompt = body["prompt"]
        except (json.JSONDecodeError, KeyError, TypeError):
            self._json(400, {"error": 'Wymagany JSON: {"prompt": "..."}'})
            return

        # prompt idzie przez stdin (nie jako argv) — inaczej duże prompty (np. cały
        # WIG20) przekraczają MAX_ARG_STRLEN (~128 KB) i subprocess pada z E2BIG.
        cmd = ["claude", "-p"]
        if model := body.get("model"):
            cmd += ["--model", model]
        if system := body.get("system"):
            cmd += ["--append-system-prompt", system]

        try:
            out = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True, timeout=TIMEOUT
            )
        except subprocess.TimeoutExpired:
            self._json(504, {"error": f"claude -p przekroczył {TIMEOUT}s"})
            return
        except FileNotFoundError:
            self._json(500, {"error": "Brak `claude` w PATH — zainstaluj i zaloguj Claude Code"})
            return

        if out.returncode != 0:
            self._json(502, {"error": (out.stderr or out.stdout).strip()})
        else:
            self._json(200, {"response": out.stdout.strip()})

    def _json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"claude-proxy nasłuchuje na :{PORT} (POST {{'prompt': ...}})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
