"""Benchmark per-call trace emitter (benchmark v2).

Appends one JSON record per LLM call to an append-only JSONL file. Enabled
only when ``BENCH_TRACE_DIR`` is set; zero overhead and zero behavior change
for interactive usage.

Environment contract (set by the benchmark runner):
    BENCH_TRACE_DIR   output directory for <run_id>.jsonl (required to enable)
    BENCH_RUN_ID      logical run identifier (default: date-stamped)
    BENCH_ARM         arm label: A | B | C
    BENCH_REP         replication index (int)
    BENCH_TOPIC       topic string exactly as shown to the model

The emitter never raises: tracing must never break generation. Parse failures
and I/O errors are logged and swallowed.

Schema (one JSON object per line):
    ts, run_id, arm, rep, topic, stage, attempt, model,
    prompt_sha256, prompt_chars, response_sha256,
    input_tokens, cache_write_tokens, cache_read_tokens, output_tokens,
    output_audio_tokens, input_audio_tokens, details (raw usage extras),
    requests, tool_calls, latency_ms, temperature, error
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

#: Per-task benchmark context. The orchestrator sets job_seq (and may override
#: arm/rep/topic) before running a job so concurrent jobs attribute traces
#: correctly despite sharing one process environment.
_bench_ctx: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "bench_ctx", default=None
)


def set_bench_context(job_seq: int | None = None, **overrides: Any) -> None:
    """Sets the benchmark context for the current async task."""
    ctx = dict(_bench_ctx.get() or {})
    if job_seq is not None:
        ctx["job_seq"] = job_seq
    ctx.update({k: v for k, v in overrides.items() if v is not None})
    _bench_ctx.set(ctx)


def clear_bench_context() -> None:
    _bench_ctx.set(None)

_TRACE_FIELDS = (
    "input_tokens",
    "cache_write_tokens",
    "cache_read_tokens",
    "output_tokens",
    "input_audio_tokens",
    "output_audio_tokens",
    "requests",
    "tool_calls",
)


def trace_enabled() -> bool:
    """True when benchmark tracing is active for this process."""
    return bool(os.environ.get("BENCH_TRACE_DIR"))


def _run_id() -> str:
    return os.environ.get("BENCH_RUN_ID") or datetime.now(UTC).strftime("bench-%Y%m%d-%H%M%S")


def _trace_file() -> Path:
    d = Path(os.environ["BENCH_TRACE_DIR"])
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_run_id()}.jsonl"


def _sha(text: Any) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(str(text).encode()).hexdigest()


def _usage_dict(usage: Any) -> dict[str, Any]:
    """Extract known usage fields; keys always present (None when unavailable)."""
    out: dict[str, Any] = {f: None for f in _TRACE_FIELDS}
    if usage is None:
        return out
    for f in _TRACE_FIELDS:
        out[f] = getattr(usage, f, None)
    details = getattr(usage, "details", None)
    # Reasoning tokens frequently ride in details (provider-specific key).
    out["details"] = details or None
    return out


def _model_id(agent: Any) -> str | None:
    """Best-effort model id extraction from a pydantic-ai Agent."""
    try:
        model = agent.model
        return getattr(model, "model_name", None) or getattr(model, "_model_name", None)
    except Exception:  # noqa: BLE001 — tracing must never break generation
        return None


def _temperature(agent: Any) -> float | None:
    """Best-effort temperature extraction from the agent's model settings."""
    try:
        ms = getattr(agent, "model_settings", None) or {}
        # pydantic-ai stores settings on the request; agents expose via model.settings rarely.
        # Accept an explicit env override too (pinned by the runner).
        env_t = os.environ.get("BENCH_TEMPERATURE")
        if env_t is not None:
            return float(env_t)
        if isinstance(ms, dict):
            return ms.get("temperature")
        return getattr(ms, "temperature", None)
    except Exception:  # noqa: BLE001
        return None


def emit_call(
    *,
    agent_name: str,
    agent: Any,
    prompt: Any,
    attempt: int | None = None,
    usage: Any = None,
    latency_ms: float | None = None,
    error: str | None = None,
    response: Any = None,
) -> None:
    """Append one per-call record. Never raises."""
    if not trace_enabled():
        return
    try:
        ctx = _bench_ctx.get() or {}
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "run_id": _run_id(),
            "arm": ctx.get("arm") or os.environ.get("BENCH_ARM"),
            "rep": ctx.get("rep") if ctx.get("rep") is not None else (int(os.environ["BENCH_REP"]) if os.environ.get("BENCH_REP") else None),
            "topic": ctx.get("topic") or os.environ.get("BENCH_TOPIC"),
            "job_seq": ctx.get("job_seq"),
            "stage": agent_name,
            "attempt": attempt,
            "model": _model_id(agent),
            "prompt_sha256": _sha(prompt),
            "prompt_chars": len(str(prompt)) if prompt is not None else None,
            "response_sha256": _sha(response),
            "temperature": _temperature(agent),
            "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
            "error": error,
            **_usage_dict(usage),
        }
        path = _trace_file()
        with path.open("a") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as e:  # noqa: BLE001 — tracing must never break generation
        logger.warning("benchmark_trace_write_failed", error=str(e))


class Timer:
    """Context manager measuring wall-clock milliseconds (monotonic)."""

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        self.ms: float | None = None
        return self

    def __exit__(self, *exc: object) -> None:
        self.ms = (time.perf_counter() - self._start) * 1000.0
