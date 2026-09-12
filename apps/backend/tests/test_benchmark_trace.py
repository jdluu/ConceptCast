"""Unit tests for the benchmark per-call trace emitter."""

import json
from pathlib import Path

import pytest

from infra.ai import trace as bench_trace


@pytest.fixture
def trace_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = tmp_path / "traces"
    monkeypatch.setenv("BENCH_TRACE_DIR", str(d))
    monkeypatch.setenv("BENCH_RUN_ID", "test-run")
    monkeypatch.setenv("BENCH_ARM", "C")
    monkeypatch.setenv("BENCH_REP", "1")
    monkeypatch.setenv("BENCH_TOPIC", "derivatives in calculus")
    monkeypatch.setenv("BENCH_TEMPERATURE", "0")
    return d


def test_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BENCH_TRACE_DIR", raising=False)
    assert not bench_trace.trace_enabled()
    # emit is a no-op, must not raise
    bench_trace.emit_call(agent_name="analyst", agent=object(), prompt="x")


def test_emit_success_record(trace_env: Path) -> None:
    class FakeUsage:
        input_tokens = 100
        cache_write_tokens = 0
        cache_read_tokens = 0
        output_tokens = 50
        input_audio_tokens = 0
        output_audio_tokens = 0
        requests = 1
        tool_calls = 0
        details = {"reasoning_tokens": 20}

    class FakeModel:
        model_name = "test-model"

    class FakeAgent:
        model = FakeModel()

    bench_trace.emit_call(
        agent_name="analyst",
        agent=FakeAgent(),
        prompt="hello prompt",
        attempt=2,
        usage=FakeUsage(),
        latency_ms=123.45,
        response="out",
    )
    files = list(trace_env.glob("*.jsonl"))
    assert len(files) == 1
    rec = json.loads(files[0].read_text().splitlines()[0])
    assert rec["run_id"] == "test-run"
    assert rec["arm"] == "C"
    assert rec["rep"] == 1
    assert rec["stage"] == "analyst"
    assert rec["attempt"] == 2
    assert rec["model"] == "test-model"
    assert rec["input_tokens"] == 100
    assert rec["output_tokens"] == 50
    assert rec["details"] == {"reasoning_tokens": 20}
    assert rec["latency_ms"] == 123.5
    assert rec["error"] is None
    assert rec["prompt_sha256"] and rec["response_sha256"]


def test_emit_error_record(trace_env: Path) -> None:
    bench_trace.emit_call(
        agent_name="animator", agent=object(), prompt="p", error="ValueError: boom", latency_ms=5.0
    )
    rec = json.loads(next(trace_env.glob("*.jsonl")).read_text().splitlines()[0])
    assert rec["error"] == "ValueError: boom"
    assert rec["input_tokens"] is None


def test_emit_never_raises(trace_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate I/O failure: point trace dir at a file, not a directory.
    trace_env.mkdir(parents=True, exist_ok=True)
    bad = trace_env / "not-a-dir"
    bad.write_text("x")
    monkeypatch.setenv("BENCH_TRACE_DIR", str(bad))
    bench_trace.emit_call(agent_name="x", agent=object(), prompt="p")  # must not raise
    assert list(trace_env.glob("*.jsonl")) == []  # nothing written, nothing crashed


def test_timer_measures() -> None:
    import time

    with bench_trace.Timer() as t:
        time.sleep(0.01)
    assert t.ms is not None and t.ms >= 10


def test_bench_context_overrides_env(trace_env: Path) -> None:
    """Benchmark v2: per-job context (set by orchestrator) overrides process env,
    and job_seq is recorded — required for parallel-job trace attribution."""
    from infra.ai import trace as bench_trace

    bench_trace.set_bench_context(job_seq=17, arm="C", rep=2, topic="derivatives in calculus")
    bench_trace.emit_call(agent_name="analyst", agent=object(), prompt="p")
    rec = json.loads(next(trace_env.glob("*.jsonl")).read_text().splitlines()[0])
    assert rec["job_seq"] == 17
    assert rec["arm"] == "C"
    assert rec["rep"] == 2
    assert rec["topic"] == "derivatives in calculus"

    bench_trace.clear_bench_context()
    bench_trace.emit_call(agent_name="analyst", agent=object(), prompt="p2")
    rec2 = json.loads(next(trace_env.glob("*.jsonl")).read_text().splitlines()[1])
    assert rec2["job_seq"] is None
    assert rec2["arm"] == "C"  # falls back to env
