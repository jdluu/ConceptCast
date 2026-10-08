import structlog
from pydantic_ai import RunContext

from domain.models.workflow import GlobalContext
from infra.settings import PROJECT_ROOT

logger = structlog.get_logger(__name__)

# Vendored from https://github.com/adithya-s-k/manim_skill (MIT); see
# prompts/skills/manimce/README.md for provenance. Path resolved from the project root — a
# relative path silently resolved against the backend's CWD (apps/backend), where the
# directory does not exist, so every lookup_manim_pattern call returned "No patterns
# directory found" and the models animated without their pattern library.
SKILLS_DIR = PROJECT_ROOT / "prompts" / "skills" / "manimce"


def get_available_patterns() -> str:
    """Returns a list of all available Manim pattern topics."""
    if not SKILLS_DIR.exists():
        return "No patterns directory found."

    files = []
    for f in SKILLS_DIR.glob("*.md"):
        files.append(f.stem)

    if not files:
        return "No pattern files found."

    return "Available Manim Pattern Topics:\n- " + "\n- ".join(sorted(files))


async def lookup_manim_pattern(_ctx: RunContext[GlobalContext], topic: str) -> str:
    """Looks up best practices and code examples for a specific Manim concept.

    Use this tool BEFORE writing complex animations to get verified patterns
    and avoid common syntax errors.

    Args:
        topic: The topic to look up. To see a list of available topics,
               pass "help" or "list". Examples: "animations", "axes", "colors".

    Returns:
        A markdown-formatted string containing the best practices and code
        examples for the requested topic.
    """
    logger.info("lookup_manim_pattern_called", topic=topic)

    topic = topic.lower().strip()

    if topic in ("help", "list", "index", ""):
        return get_available_patterns()

    # Prevent path traversal
    safe_topic = "".join(c for c in topic if c.isalnum() or c in ("-", "_"))

    file_path = SKILLS_DIR / f"{safe_topic}.md"

    if not file_path.exists():
        # Try to find a partial match
        available = [f.stem for f in SKILLS_DIR.glob("*.md")]
        matches = [f for f in available if safe_topic in f or f in safe_topic]

        if matches:
            suggestions = ", ".join(matches)
            return f"Topic '{topic}' not found. Did you mean: {suggestions}?"

        return f"Topic '{topic}' not found. " + get_available_patterns()

    try:
        content = file_path.read_text(encoding="utf-8")
        return f"--- MANIM PATTERN: {safe_topic.upper()} ---\n\n{content}"
    except Exception as e:
        logger.error("manim_pattern_read_error", error=str(e), topic=topic)
        return f"Error reading pattern: {str(e)}"
