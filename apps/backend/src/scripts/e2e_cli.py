"""E2E CLI simulation for the ConceptCast pedagogical workflow.

This script runs the full multi-agent workflow for a specified topic across
all available AI providers and models by making actual API requests to the
running backend server. Results are logged to the e2e_reports directory.
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from infra.ai.factory import get_available_providers_and_models
from infra.settings import get_settings

# Configuration
BASE_URL = "http://localhost:8000"
REPORTS_DIR = Path(__file__).parent.parent.parent / "e2e_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ANSI Colors
CLR_RESET = "\033[0m"
CLR_BLUE = "\033[94m"
CLR_GREEN = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_RED = "\033[91m"
CLR_CYAN = "\033[96m"
CLR_MAGENTA = "\033[95m"
CLR_WHITE = "\033[97m"
CLR_BOLD = "\033[1m"
CLR_DIM = "\033[2m"

AGENT_COLORS = {
    "Analyst": CLR_BLUE,
    "Architect": CLR_CYAN,
    "Animator": CLR_MAGENTA,
}


def _truncate(value: str, limit: int = 180) -> str:
    cleaned = " ".join(value.strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."


def _summarize_structured_content(content: str) -> str:
    text = (content or "").strip()
    if not text:
        return "<empty structured output>"

    lower = text.lower()
    if "structured output commit" in lower:
        return "structured_output_commit"
    if "structured output result:" in lower:
        after = text.split("Structured output result:", maxsplit=1)[-1].strip()
        if not after:
            return "structured_output_result"
        first_line = after.splitlines()[0].strip()
        return _truncate(first_line or "structured_output_result")
    first_line = text.splitlines()[0].strip()
    return _truncate(first_line or "structured_output")


def _is_missing_text(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    normalized = value.strip().lower()
    return normalized in {"", "__missing__", "missing"}


def _summarize_plan_quality(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict):
        return {
            "concept_missing": True,
            "audience_missing": True,
            "teaching_steps_len": 0,
            "step_fields_missing": 0,
            "structural_ok": False,
        }

    steps_raw = plan.get("teaching_steps")
    steps = steps_raw if isinstance(steps_raw, list) else []
    missing_step_fields = 0
    for step in steps:
        if not isinstance(step, dict):
            missing_step_fields += 1
            continue
        if _is_missing_text(step.get("concept")):
            missing_step_fields += 1
        if _is_missing_text(step.get("visual_metaphor")):
            missing_step_fields += 1
        if _is_missing_text(step.get("narration")):
            missing_step_fields += 1

    concept_missing = _is_missing_text(plan.get("concept_title"))
    audience_missing = _is_missing_text(plan.get("target_audience"))
    teaching_steps_len = len(steps)
    structural_ok = (
        not concept_missing
        and not audience_missing
        and 5 <= teaching_steps_len <= 10
        and missing_step_fields == 0
    )
    return {
        "concept_missing": concept_missing,
        "audience_missing": audience_missing,
        "teaching_steps_len": teaching_steps_len,
        "step_fields_missing": missing_step_fields,
        "structural_ok": structural_ok,
    }


class E2EWorkflowLogger:
    """Handles logging of workflow events to terminal and file."""

    def __init__(
        self,
        provider: str,
        model_id: str,
        topic: str,
        *,
        verbose_structured: bool = False,
    ):
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_model = model_id.replace("/", "_").replace(":", "_")
        self.filename = REPORTS_DIR / f"{timestamp}_{provider}_{safe_model}.txt"
        self.topic = topic
        self.provider = provider
        self.model_id = model_id
        self.last_step = None
        self.printed_thoughts_count = 0
        self.last_progress = -1
        self.last_thought_content = ""
        self.verbose_structured = verbose_structured

        with self.filename.open("w", encoding="utf-8") as f:
            f.write("ConceptCast E2E API Report\n")
            f.write("=" * 30 + "\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Topic: {topic}\n")
            f.write(f"Provider: {provider}\n")
            f.write(f"Model: {model_id}\n")
            f.write("=" * 30 + "\n\n")

        print(f"\n{CLR_BOLD}{CLR_CYAN}🚀 Starting Workflow: {topic}{CLR_RESET}")  # noqa: T201
        print(f"{CLR_DIM}Model: {provider}/{model_id}{CLR_RESET}\n")  # noqa: T201

    def log_event(self, event_data: dict[str, Any]) -> None:  # noqa: C901, PLR0912, PLR0915
        """Logs an event from the SSE stream to the report file and terminal."""
        status = event_data.get("status")
        step = event_data.get("current_step")
        progress = event_data.get("render_progress", 0)
        error = event_data.get("error")
        plan = event_data.get("plan")
        has_plan = plan is not None
        has_storyboard = event_data.get("storyboard") is not None
        has_code = bool(event_data.get("manim_code"))
        plan_quality = _summarize_plan_quality(plan)

        # Log to file
        with self.filename.open("a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now(UTC).isoformat()}] STATUS: {status} | STEP: {step}\n"
            )
            f.write(
                "  ARTIFACTS: "
                f"plan={has_plan} "
                f"plan_structural_ok={plan_quality['structural_ok']} "
                f"teaching_steps_len={plan_quality['teaching_steps_len']} "
                f"plan_concept_missing={plan_quality['concept_missing']} "
                f"plan_target_audience_missing={plan_quality['audience_missing']} "
                f"storyboard={has_storyboard} "
                f"manim_code={has_code} "
                f"error_present={bool(error)}\n"
            )
            if error:
                f.write(f"  ERROR: {error}\n")
            thoughts = event_data.get("streamed_thoughts", [])
            if len(thoughts) > self.printed_thoughts_count:
                for i in range(self.printed_thoughts_count, len(thoughts)):
                    t = thoughts[i]
                    phase = t.get("phase")
                    content = t.get("content")
                    if phase == "structured_output" and not self.verbose_structured:
                        content = _summarize_structured_content(str(content or ""))
                    f.write(f"  THOUGHT - {t.get('agent')} ({phase}): {content}\n")
            elif thoughts and self.printed_thoughts_count > 0:
                # Log content delta for the last thought.
                # For structured outputs, providers may resend cumulative JSON
                # payloads (causing huge repeated log lines). Suppress that noise.
                last_t = thoughts[-1]
                if last_t.get("phase") == "structured_output":
                    f.write(
                        "  THOUGHT DELTA - "
                        f"{last_t.get('agent')} (structured_output suppressed)\n"
                    )
                else:
                    f.write(
                        f"  THOUGHT DELTA - {last_t.get('agent')}: {last_t.get('content')}\n"
                    )

        # Log to terminal
        if step != self.last_step and step:
            if self.last_step:
                # Step finished, show summary
                print(f"\n  {CLR_DIM}├─ Step Completed{CLR_RESET}")  # noqa: T201
                print(  # noqa: T201
                    "  "
                    f"{CLR_DIM}└─ Artifacts: "
                    f"plan={has_plan} "
                    f"plan_ok={plan_quality['structural_ok']} "
                    f"steps={plan_quality['teaching_steps_len']} "
                    f"concept_missing={plan_quality['concept_missing']} "
                    f"audience_missing={plan_quality['audience_missing']} "
                    f"storyboard={has_storyboard} "
                    f"code={has_code} "
                    f"error_present={bool(error)}{CLR_RESET}\n"
                )

            icon = (
                "📝"
                if "plan" in step
                else "🎨"
                if "arch" in step
                else "🎬"
                if "anim" in step
                else "⚙️"
            )
            print(f"{CLR_BOLD}{icon} Step: {step.replace('_', ' ').title()}{CLR_RESET}")  # noqa: T201
            self.last_step = step

        if status == "awaiting_review" and step == "rendering_failed_needs_fix":
            print(  # noqa: T201
                f"  {CLR_RED}{CLR_BOLD}Render failed -> paused for fix (awaiting_review).{CLR_RESET}"
            )
            if error:
                print(f"  {CLR_RED}{error}{CLR_RESET}")  # noqa: T201
        elif (
            status == "rendering"
            and step
            and (
                step.startswith("rendering_retry_")
                or step
                in {
                    "rendering_repair_regenerate_code",
                    "rendering_repair_retry_dispatched",
                }
            )
        ):
            print(  # noqa: T201
                f"  {CLR_YELLOW}{CLR_BOLD}Render repair loop active: {step}{CLR_RESET}"
            )
        elif (
            status == "animating"
            and step
            and step.startswith("rendering_repair_attempt_")
        ):
            print(  # noqa: T201
                f"  {CLR_YELLOW}Applying targeted code patch before re-render ({step}).{CLR_RESET}"
            )

        # Handle thoughts
        thoughts = event_data.get("streamed_thoughts", [])
        if not thoughts:
            return

        # 1. Handle NEW thoughts (appended to the list)
        if len(thoughts) > self.printed_thoughts_count:
            # If we were already printing a thought, end it
            if self.printed_thoughts_count > 0:
                print()  # noqa: T201

            for i in range(self.printed_thoughts_count, len(thoughts)):
                t = thoughts[i]
                agent = t.get("agent", "Unknown")
                phase = t.get("phase", "reasoning")
                content = t.get("content", "")
                if phase == "structured_output" and not self.verbose_structured:
                    content = _summarize_structured_content(content)

                # Visual style based on phase
                if agent == "system" and phase == "status":
                    header = f"{CLR_BOLD}{CLR_WHITE}󰋼 SYSTEM:{CLR_RESET}"
                    content_style = CLR_DIM
                elif phase == "structured_output":
                    color = AGENT_COLORS.get(agent, CLR_RESET)
                    header = (
                        f"{color}{CLR_BOLD}󰏬 {agent} (structured_output):{CLR_RESET}"
                    )
                    content_style = CLR_DIM
                elif phase == "tool_call":
                    color = AGENT_COLORS.get(agent, CLR_RESET)
                    header = f"{color}{CLR_BOLD}󱐋 {agent} (tool_call):{CLR_RESET}"
                    content_style = CLR_DIM
                else:
                    color = AGENT_COLORS.get(agent, CLR_RESET)
                    icon = "󰚩" if phase == "thinking" else "󰙨"
                    header = f"{color}{CLR_BOLD}{icon} {agent} ({phase}):{CLR_RESET}"
                    content_style = ""

                # Newline for subsequent thoughts in this batch
                if i > self.printed_thoughts_count:
                    print()  # noqa: T201

                print(f"  {header} {content_style}{content}", end="", flush=True)  # noqa: T201
                self.last_thought_content = content

            self.printed_thoughts_count = len(thoughts)

        # 2. Handle DELTAS for the last thought (aggregation)
        elif self.printed_thoughts_count > 0:
            last_t = thoughts[-1]
            current_content = last_t.get("content", "")
            if last_t.get("phase") == "structured_output":
                # Structured output deltas are often re-sent as cumulative JSON.
                # Keep state in sync but avoid printing huge chunks.
                self.last_thought_content = current_content
                return

            if not current_content or current_content == self.last_thought_content:
                return

            if current_content.startswith(self.last_thought_content):
                delta = current_content[len(self.last_thought_content) :]
                if delta:
                    print(delta, end="", flush=True)  # noqa: T201
                    self.last_thought_content = current_content
            else:
                # If content was re-chunked or reset, resync without spam.
                self.last_thought_content = current_content

        # Handle progress
        if status == "rendering" and progress > self.last_progress:
            bar_length = 20
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            sys.stdout.write(
                f"\r  {CLR_YELLOW}Rendering Progress: [{bar}] {progress}%{CLR_RESET}"
            )
            sys.stdout.flush()
            self.last_progress = progress

    def log_error(self, error: str) -> None:
        """Logs a critical error to the report file and terminal."""
        with self.filename.open("a", encoding="utf-8") as f:
            f.write(f"\nCRITICAL FAILURE: {error}\n")
        print(f"\n\n{CLR_RED}{CLR_BOLD}❌ FAILED: {error}{CLR_RESET}\n")  # noqa: T201

    def log_success(self, final_data: dict[str, Any]) -> None:
        """Logs final job completion details."""
        final_cost = final_data.get("cost", 0.0)
        duration = final_data.get("duration_seconds", 0.0)
        with self.filename.open("a", encoding="utf-8") as f:
            f.write("\nCOMPLETED SUCCESSFULLY\n")
            f.write(f"Final Cost: ${final_cost:.4f}\n")
            f.write(f"Duration: {duration:.2f}s\n")
            if final_data.get("video_url"):
                f.write(f"Video URL: {final_data.get('video_url')}\n")

        print(  # noqa: T201
            f"\n\n{CLR_GREEN}{CLR_BOLD}✨ Workflow Completed Successfully!{CLR_RESET}"
        )
        print(f"   {CLR_DIM}Final Cost: ${final_cost:.4f}{CLR_RESET}")  # noqa: T201
        print(f"   {CLR_DIM}Video Length: {duration:.2f}s{CLR_RESET}")  # noqa: T201
        if final_data.get("video_url"):
            print(  # noqa: T201
                f"   {CLR_BOLD}Video: {BASE_URL}{final_data.get('video_url')}{CLR_RESET}"
            )
        print("")  # noqa: T201

    def log_run_summary(self, event_data: dict[str, Any]) -> None:
        """Writes a compact end-of-run summary to terminal and report file."""
        status = event_data.get("status")
        step = event_data.get("current_step")
        error = event_data.get("error")
        failure_stage = event_data.get("failure_stage")
        failure_type = event_data.get("failure_type")
        failure_summary = event_data.get("failure_summary")
        plan = event_data.get("plan")
        storyboard = event_data.get("storyboard") is not None
        manim_code = bool(event_data.get("manim_code"))

        plan_quality = _summarize_plan_quality(plan)

        summary = (
            f"RUN SUMMARY | status={status} step={step} "
            f"plan_ok={plan_quality['structural_ok']} "
            f"plan_steps={plan_quality['teaching_steps_len']} "
            f"failure_stage={failure_stage} "
            f"failure_type={failure_type} "
            f"failure_summary={_truncate(str(failure_summary or ''))} "
            f"storyboard_present={storyboard} manim_code_present={manim_code} "
            f"error_present={bool(error)}"
        )

        with self.filename.open("a", encoding="utf-8") as f:
            f.write(f"\n{summary}\n")
            if error:
                f.write(f"  error={error}\n")

        print(f"\n{CLR_DIM}{summary}{CLR_RESET}")  # noqa: T201


async def monitor_job(job_id: str, e2e_logger: E2EWorkflowLogger) -> dict[str, Any]:
    """Monitors a job's progress via the SSE endpoint."""
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream(
                "GET", f"{BASE_URL}/jobs/{job_id}/events"
            ) as response:
                if response.status_code != 200:
                    error_detail = await response.aread()
                    raise Exception(
                        f"Failed to connect to SSE: {response.status_code} {error_detail.decode()}"
                    )

                last_event_data = {}
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        event_data = json.loads(data_str)

                        if "error" in event_data and event_data["error"]:
                            e2e_logger.log_error(event_data["error"])
                            return cast(dict[str, Any], event_data)

                        e2e_logger.log_event(event_data)
                        last_event_data = event_data

                        if event_data.get("status") in ["completed", "failed"]:
                            if event_data.get("status") == "completed":
                                e2e_logger.log_success(event_data)
                            e2e_logger.log_run_summary(event_data)
                            return cast(dict[str, Any], event_data)
                        if (
                            event_data.get("status") == "awaiting_review"
                            and event_data.get("current_step")
                            == "rendering_failed_needs_fix"
                        ):
                            e2e_logger.log_run_summary(event_data)
                            return cast(dict[str, Any], event_data)
                return cast(dict[str, Any], last_event_data)
        except Exception as e:
            e2e_logger.log_error(str(e))
            raise


async def run_single_simulation(  # noqa: PLR0913
    provider: str,
    model_id: str,
    topic: str,
    audience: str,
    *,
    hitl_enabled: bool,
    analyst_model: str | None = None,
    architect_model: str | None = None,
    animator_model: str | None = None,
    verbose_structured: bool = False,
) -> dict[str, Any]:
    """Runs a single simulation for one provider/model."""
    e2e_logger = E2EWorkflowLogger(
        provider, model_id, topic, verbose_structured=verbose_structured
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/jobs/create",
                json={
                    "topic": topic,
                    "target_audience": audience,
                    "provider": provider,
                    "model_id": model_id,
                    "analyst_model": analyst_model,
                    "architect_model": architect_model,
                    "animator_model": animator_model,
                    "hitl_enabled": hitl_enabled,
                },
            )
            if response.status_code != 200:
                e2e_logger.log_error(
                    f"Job creation failed: {response.status_code} {response.text}"
                )
                return {
                    "provider": provider,
                    "model_id": model_id,
                    "status": "failed",
                    "failure_summary": f"Job creation failed: {response.status_code}",
                    "report_file": str(e2e_logger.filename),
                }

            job_data = response.json()
            job_id = job_data["job_id"]

            final_event = await monitor_job(job_id, e2e_logger)
            return {
                "provider": provider,
                "model_id": model_id,
                "status": final_event.get("status"),
                "current_step": final_event.get("current_step"),
                "failure_stage": final_event.get("failure_stage"),
                "failure_type": final_event.get("failure_type"),
                "failure_summary": final_event.get("failure_summary"),
                "error": final_event.get("error"),
                "duration_seconds": final_event.get("duration_seconds"),
                "cost": final_event.get("cost"),
                "report_file": str(e2e_logger.filename),
            }

        except Exception as e:
            e2e_logger.log_error(f"Request failed: {str(e)}")
            return {
                "provider": provider,
                "model_id": model_id,
                "status": "failed",
                "failure_summary": f"Request failed: {str(e)}",
                "error": str(e),
                "report_file": str(e2e_logger.filename),
            }


def _print_aggregate_summary(results: list[dict[str, Any]]) -> None:
    if not results:
        return

    print(f"\n{CLR_BOLD}Overall E2E Summary{CLR_RESET}")  # noqa: T201
    header = f"{'Provider/Model':56} {'Status':14} {'Failure Summary'}"
    print(header)  # noqa: T201
    print("-" * len(header))  # noqa: T201

    passed = 0
    failed = 0
    paused = 0
    for item in results:
        status = str(item.get("status") or "unknown")
        if status == "completed":
            passed += 1
        elif status == "awaiting_review":
            paused += 1
        else:
            failed += 1
        model_key = f"{item.get('provider')}/{item.get('model_id')}"
        failure_summary = str(item.get("failure_summary") or item.get("error") or "-")
        print(  # noqa: T201
            f"{_truncate(model_key, 56):56} "
            f"{status:14} {_truncate(failure_summary, 120)}"
        )

    print(  # noqa: T201
        f"\n{CLR_DIM}Counts: completed={passed} awaiting_review={paused} failed={failed}{CLR_RESET}\n"
    )


async def run_full_simulation(  # noqa: PLR0913
    topic: str,
    audience: str,
    include_mock: bool = True,
    *,
    hitl_enabled: bool,
    analyst_model: str | None = None,
    architect_model: str | None = None,
    animator_model: str | None = None,
    verbose_structured: bool = False,
    aggregate_report: bool = True,
) -> None:
    """Runs simulations across all active models sequentially."""
    settings = get_settings()
    active_providers = get_available_providers_and_models(settings)

    # Ensure backend is up
    async with httpx.AsyncClient() as client:
        try:
            await client.get(f"{BASE_URL}/health")
        except Exception:
            print(  # noqa: T201
                f"{CLR_RED}Backend server not found at {BASE_URL}. Please start it with 'make dev' first.{CLR_RESET}"
            )
            return

    aggregate_results: list[dict[str, Any]] = []
    for provider_info in active_providers:
        provider = provider_info.provider
        if provider == "mock" and not include_mock:
            continue

        for model_id in provider_info.models:
            result = await run_single_simulation(
                provider,
                model_id,
                topic,
                audience,
                hitl_enabled=hitl_enabled,
                analyst_model=analyst_model,
                architect_model=architect_model,
                animator_model=animator_model,
                verbose_structured=verbose_structured,
            )
            aggregate_results.append(result)

    _print_aggregate_summary(aggregate_results)

    if aggregate_report:
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        aggregate_path = REPORTS_DIR / f"{ts}_aggregate_report.json"
        payload = {
            "topic": topic,
            "audience": audience,
            "generated_at": datetime.now(UTC).isoformat(),
            "results": aggregate_results,
        }
        with aggregate_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"{CLR_DIM}Aggregate report: {aggregate_path}{CLR_RESET}")  # noqa: T201


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ConceptCast E2E Workflow API Simulation"
    )
    parser.add_argument("--topic", type=str, required=True, help="Pedagogical topic")
    parser.add_argument(
        "--audience", type=str, default="General Audience", help="Target audience"
    )
    parser.add_argument("--no-mock", action="store_true", help="Skip the mock provider")
    parser.add_argument("--hitl-enabled", action="store_true", help="Force-enable HITL")
    parser.add_argument(
        "--hitl-disabled", action="store_true", help="Force-disable HITL"
    )
    parser.add_argument(
        "--analyst-model", type=str, default=None, help="Override analyst model"
    )
    parser.add_argument(
        "--architect-model", type=str, default=None, help="Override architect model"
    )
    parser.add_argument(
        "--animator-model", type=str, default=None, help="Override animator model"
    )
    parser.add_argument(
        "--verbose-structured",
        action="store_true",
        help="Print full structured-output payloads in terminal and report logs.",
    )
    parser.add_argument(
        "--no-aggregate-report",
        action="store_true",
        help="Disable writing aggregate JSON report for the full run.",
    )

    args = parser.parse_args()
    settings = get_settings()

    try:
        asyncio.run(
            run_full_simulation(
                args.topic,
                args.audience,
                not args.no_mock,
                hitl_enabled=(
                    False
                    if args.hitl_disabled
                    else (True if args.hitl_enabled else bool(settings.hitl_enabled))
                ),
                analyst_model=args.analyst_model,
                architect_model=args.architect_model,
                animator_model=args.animator_model,
                verbose_structured=args.verbose_structured,
                aggregate_report=not args.no_aggregate_report,
            )
        )
    except KeyboardInterrupt:
        print(f"\n{CLR_YELLOW}Simulation interrupted by user.{CLR_RESET}")  # noqa: T201
        sys.exit(1)
