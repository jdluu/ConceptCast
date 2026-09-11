"""Agent specialized in generating Manim Python code from visual storyboards.

Enforces strict Manim API usage rules and utilizes pedagogical best practices
for visual clarity and pacing.
"""

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import RunUsage, UsageLimits

from api.schemas import Scene, Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel
from infra.ai.factory import NanoConceptModel
from infra.ai.tools import (
    get_aesthetic_palette,
    lint_manim_code,
    lookup_manim_pattern,
    prepare_manim_docs,
    search_manim_docs,
)
from services.workflow.context_injectors import extract_animator_context

from .base import ConceptAgent

# Initialize the shared animator agent instance
animator_agent: ConceptAgent[str] = ConceptAgent("animator", str)

_CODE_BLOCK_PATTERN = re.compile(r"```(?:python|json)?\s*\n(.*?)```", re.DOTALL)
_CODE_JSON_KEYS = ("code", "python_code", "manim_code")


def _strip_stray_fences(code: str) -> str:
    """Removes stray markdown-fence lines and trailing prose after the last fence.

    Double-wrapped payloads (a fenced block inside a quoted/fenced payload) leave
    a standalone ``` line mid-code and prose after it; both break compilation.
    """
    lines = code.splitlines()
    # Drop leading fence lines
    while lines and lines[0].strip().startswith("```"):
        lines.pop(0)
    # Find last stray fence line; keep everything before it if code follows the first fence
    fence_idxs = [i for i, l in enumerate(lines) if l.strip().startswith("```")]
    if fence_idxs:
        last = fence_idxs[-1]
        # Keep content up to (not including) the last stray fence if there is code before it
        before = [l for l in lines[:last]]
        after = lines[last + 1 :]
        code_before = "\n".join(before).strip()
        try:
            compile(code_before, "<gen>", "exec")
            lines = before  # prose/fence tail dropped; code before the fence compiles
        except SyntaxError:
            pass  # fence was meaningful (e.g. inside a string); leave as-is
    return "\n".join(lines)


def _unwrap_quoted_payload(candidate: str) -> str:
    """Unwraps a JSON-string payload (quoted, escape-serialized source).

    Models sometimes emit the entire fenced block as a JSON string literal —
    a leading/trailing quote with ``\\n`` escape sequences. json.loads on the
    quoted text restores the real newlines.
    """
    stripped = candidate.strip()
    if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
        try:
            unwrapped = json.loads(stripped)
            if isinstance(unwrapped, str) and unwrapped.strip():
                return unwrapped
        except json.JSONDecodeError:
            pass
    return candidate


def _normalize_escaped_newlines(candidate: str) -> str:
    """Converts literal ``\n`` escape sequences into real newlines.

    Some models emit JSON-string-escaped source (a quoted one-line payload with
    literal ``\n`` sequences). Compilation and the per-line scene isolation
    both require real newlines; only normalize when the candidate has none.
    """
    if "\n" not in candidate and ("\\n" in candidate or "\r" in candidate):
        candidate = candidate.replace("\\r\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    return candidate


def _recover_compilable_source(raw: str) -> str | None:
    """Recover a complete Python suffix when prose surrounds unfenced code."""
    lines = raw.strip().splitlines()
    starts: list[tuple[int, int]] = []
    for index, line in enumerate(lines):
        for marker in ("from manim import", "import manim"):
            column = line.find(marker)
            if column >= 0:
                starts.append((index, column))
                break
    for start, column in starts:
        source_lines = [lines[start][column:], *lines[start + 1 :]]
        for end in range(len(source_lines), 0, -1):
            candidate = "\n".join(source_lines[:end]).strip()
            try:
                compile(candidate, "<generated_manim>", "exec")
            except SyntaxError:
                continue
            return candidate
    return None


def extract_python_code(raw: str) -> str:  # noqa: C901, PLR0912
    """Extracts the last complete Python code block from model output.

    Falls back to the raw content (stripped of markdown fences) when no
    fenced block is detected. Preferring the *last* match handles cases
    where the model emits prose followed by a corrected version.

    Args:
        raw: Raw model output that may contain markdown fences and prose.

    Returns:
        The extracted Python source code.
    """
    blocks = _CODE_BLOCK_PATTERN.findall(raw)
    if blocks:
        candidates = [str(block).strip() for block in reversed(blocks)]
        for block_candidate in candidates:
            candidate = block_candidate
            if candidate.startswith("{"):
                try:
                    payload = json.loads(candidate)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    for key in _CODE_JSON_KEYS:
                        value = payload.get(key)
                        if isinstance(value, str) and value.strip():
                            candidate = value.strip()
                            break
            candidate = _unwrap_quoted_payload(candidate)
            candidate = _normalize_escaped_newlines(candidate)
            candidate = _strip_stray_fences(candidate)
            try:
                compile(candidate, "<generated_manim>", "exec")
            except SyntaxError:
                continue
            return candidate.rstrip("\n")
        raw = candidates[0]

    # Some compatible endpoints wrap the code in a JSON object. Accept only
    # known code fields; never select arbitrary prose or silently rewrite code.
    try:
        payload = json.loads(raw.strip())
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        for key in _CODE_JSON_KEYS:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().rstrip("\n")

    recovered = _recover_compilable_source(raw)
    if recovered is not None:
        return recovered

    # Fallback: strip leading/trailing fences that were not properly paired
    cleaned = _unwrap_quoted_payload(raw.strip())
    cleaned = _normalize_escaped_newlines(cleaned)
    cleaned = _strip_stray_fences(cleaned)
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


async def generate_manim_code(
    target_scene: Scene | Storyboard,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    retry_hint: str | None = None,
    ctx: GlobalContext | None = None,
    message_history: list[ModelMessage] | None = None,
    scene_id: int | None = None,
    usage_limits: UsageLimits | None = None,
) -> tuple[str, RunUsage]:
    """Generates Manim Python code derived from a visual storyboard.

    Args:
        target_scene: The specific scene or full storyboard to generate code for.
        model: The ConceptCast model to use for generation.
        on_thought: Optional callback for streaming agent thoughts.
        retry_hint: Optional feedback for iterative improvement.
        ctx: The Global Context Object (GCO) for the workflow.
        message_history: Optional history for stateful multi-turn retries.
        scene_id: Optional scene identifier for context injection.
        usage_limits: Optional pydantic-ai UsageLimits for capping requests/tokens.

    Returns:
        tuple[str, RunUsage]: The generated Python code and token usage metadata.
    """

    def _prepare_agent(agent: Agent[Any, Any]) -> None:
        agent.tool(prepare=prepare_manim_docs)(search_manim_docs)
        agent.tool()(lint_manim_code)
        agent.tool()(lookup_manim_pattern)
        agent.tool()(get_aesthetic_palette)

    if ctx:
        prompt = extract_animator_context(
            ctx,
            target_scene,
            scene_id=scene_id,
            include_errors=not (
                isinstance(model, NanoConceptModel)
                and model.model_id.startswith("qwen/")
            ),
        )
    else:
        prompt = f"Write Manim code for scene: {json.dumps(target_scene.model_dump())}"

    if retry_hint:
        prompt = f"{prompt}\n\nIMPORTANT REVISION FEEDBACK: {retry_hint}"

    if isinstance(model, NanoConceptModel) and model.model_id.startswith("qwen/"):
        prompt = (
            f"{prompt}\n\nOUTPUT CONTRACT: Return only the complete Python source code "
            "for SceneGen. Do not return JSON, Markdown fences, explanations, "
            "analysis, checkmarks, or text before or after the code. Preserve the "
            "storyboard's visual richness and animation intent."
        )

    result, usage = await animator_agent.run(
        model=model,
        prompt=prompt,
        on_thought=on_thought,
        ctx=ctx,
        pre_run_hook=_prepare_agent,
        message_history=message_history,
        usage_limits=usage_limits,
    )

    if isinstance(result, str):
        result = extract_python_code(result)

    return result, usage
