"""Integration-style check: a real agent run through run_agent_streamed with the
Mock provider emits a trace record (temporary verification)."""

import json
from pathlib import Path

import pytest

from infra.ai.factory import get_concept_model


@pytest.mark.asyncio
async def test_streaming_emits_trace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BENCH_TRACE_DIR", str(tmp_path))
    monkeypatch.setenv("BENCH_RUN_ID", "verify-run")
    monkeypatch.setenv("BENCH_ARM", "C")
    monkeypatch.setenv("BENCH_REP", "1")
    monkeypatch.setenv("BENCH_TOPIC", "verify topic")

    model = get_concept_model("mock", "mock-gpt-4")
    assert model is not None

    from domain.agents.base import ConceptAgent

    agent: ConceptAgent[str] = ConceptAgent("analyst", str)
    _, usage = await agent.run(model=model, prompt="Explain derivatives briefly.")

    files = list(tmp_path.glob("*.jsonl"))
    assert files, "no trace file written"
    recs = [json.loads(line) for line in files[0].read_text().splitlines()]
    assert any(r["stage"] == "analyst" for r in recs)
    assert all(r["arm"] == "C" for r in recs)
    assert all(r["model"] and "mock" in str(r["model"]) for r in recs)
