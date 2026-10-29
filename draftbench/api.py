"""Small Gemini REST client. Credentials never enter saved request records."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from .common import write_json

DEFAULT_MODEL = "gemini-3.8-flash"


class EvaluationError(ValueError):
    """A missing evaluation, never a zero-quality observation."""


def load_env(path):
    """Read a simple KEY=value file without shell expansion or overriding env."""
    if path is None:
        return
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError(f"Invalid environment entry on line {number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


class GeminiJudge:
    def __init__(self, model=None, timeout=120, retries=2):
        self.key = os.environ.get("DRAFTBENCH_EVAL_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not self.key or self.key == "replace-me":
            raise EvaluationError("Set DRAFTBENCH_EVAL_API_KEY (or GEMINI_API_KEY); do not commit it.")
        self.model = model or os.environ.get("DRAFTBENCH_EVAL_MODEL", DEFAULT_MODEL)
        if not re.fullmatch(r"[A-Za-z0-9._-]+", self.model):
            raise ValueError("Use a Gemini model ID, without a URL or models/ prefix")
        self.timeout, self.retries = timeout, retries

    def config(self):
        return {"provider": "gemini", "model": self.model, "temperature": 0,
                "timeout_seconds": self.timeout, "transport_retries": self.retries,
                "api": "v1beta/generateContent", "sampling_retries": 0}

    def call(self, role, instruction, payload, log_dir, media=()):
        parts = [{"text": json.dumps(payload, ensure_ascii=False, allow_nan=False)}]
        parts.extend(media)
        body = {"systemInstruction": {"parts": [{"text": instruction}]},
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 16384,
                                     "responseMimeType": "application/json"}}
        raw = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
        if len(raw) > 19_000_000:
            raise EvaluationError("Judge request exceeds 19 MB; reduce artifacts or provide smaller previews")
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=False)
        write_json(log_dir / "request.json", body)
        record = {"role": role, **self.config(), "request_sha256": hashlib.sha256(raw).hexdigest()}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        # Do not follow redirects with the API key.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        opener = urllib.request.build_opener(NoRedirect)
        for attempt in range(self.retries + 1):
            start = time.monotonic()
            request = urllib.request.Request(url, data=raw, headers={
                "Content-Type": "application/json", "x-goog-api-key": self.key})
            try:
                with opener.open(request, timeout=self.timeout) as response:
                    response_raw = response.read(4_000_001)
                if len(response_raw) > 4_000_000:
                    raise EvaluationError("Judge response exceeded 4 MB")
                result = json.loads(response_raw)
                # API error bodies may contain credentials; never log them.
                if "error" in result:
                    raise EvaluationError("Judge API returned an error object")
                write_json(log_dir / "response.json", result)
                candidates = result.get("candidates", [])
                if not candidates or candidates[0].get("finishReason") != "STOP":
                    raise EvaluationError("Judge response missing, blocked, or truncated; no score assigned")
                text = "".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])
                               if not p.get("thought"))
                def reject_constant(value):
                    raise ValueError("Non-finite JSON number")
                value = json.loads(text, parse_constant=reject_constant)
                if not isinstance(value, dict):
                    raise EvaluationError("Judge must return a JSON object")
                record.update({"attempts": attempt + 1, "elapsed_last_attempt_seconds": time.monotonic() - start,
                               "resolved_model": result.get("modelVersion"), "usage": result.get("usageMetadata"),
                               "status": "received"})
                write_json(log_dir / "call.json", record)
                return value
            except urllib.error.HTTPError as error:
                code = error.code
                retry = code in (429, 500, 502, 503, 504) and attempt < self.retries
                write_json(log_dir / f"transport-{attempt + 1}.json", {"http_status": code, "retry": retry})
                if retry:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                message = f"Judge HTTP {code}; check key, model access, quota and network (no score assigned)"
            except (urllib.error.URLError, TimeoutError, OSError):
                message = "Judge transport failed; inspect network/timeout (no score assigned)"
            except (ValueError, KeyError, TypeError, IndexError):
                message = "Judge returned missing, blocked, truncated or invalid JSON (no score assigned)"
            record.update({"attempts": attempt + 1, "status": "evaluation_error", "error": message})
            write_json(log_dir / "call.json", record)
            raise EvaluationError(message)
