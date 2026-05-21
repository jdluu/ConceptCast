import structlog
from pydantic_ai import RunContext

from domain.models.workflow import GlobalContext

logger = structlog.get_logger(__name__)

# Curated, aesthetically pleasing color palettes for Manim
PALETTES = {
    "nord": {
        "description": "Arctic, north-bluish clean and elegant theme.",
        "background": "#2E3440",
        "primary_text": "#ECEFF4",
        "secondary_text": "#D8DEE9",
        "accent_1": "#88C0D0",  # Frost Light Blue
        "accent_2": "#81A1C1",  # Frost Blue
        "accent_3": "#B48EAD",  # Aurora Purple
        "accent_4": "#A3BE8C",  # Aurora Green
        "accent_5": "#EBCB8B",  # Aurora Yellow
        "danger": "#BF616A",  # Aurora Red
    },
    "dracula": {
        "description": "Dark theme with vibrant, high-contrast neon accents.",
        "background": "#282A36",
        "primary_text": "#F8F8F2",
        "secondary_text": "#6272A4",
        "accent_1": "#FF79C6",  # Pink
        "accent_2": "#BD93F9",  # Purple
        "accent_3": "#8BE9FD",  # Cyan
        "accent_4": "#50FA7B",  # Green
        "accent_5": "#F1FA8C",  # Yellow
        "danger": "#FF5555",  # Red
    },
    "monokai_pro": {
        "description": "Professional, highly legible dark theme with warm accents.",
        "background": "#2D2A2E",
        "primary_text": "#FCFCFA",
        "secondary_text": "#727072",
        "accent_1": "#FF6188",  # Rose
        "accent_2": "#FC9867",  # Orange
        "accent_3": "#FFD866",  # Yellow
        "accent_4": "#A9DC76",  # Green
        "accent_5": "#78DCE8",  # Cyan
        "danger": "#FF6188",  # Rose
    },
    "tokyo_night": {
        "description": "Clean, dark theme celebrating the lights of Downtown Tokyo at night.",
        "background": "#1A1B26",
        "primary_text": "#C0CAF5",
        "secondary_text": "#565F89",
        "accent_1": "#7AA2F7",  # Blue
        "accent_2": "#BB9AF7",  # Purple
        "accent_3": "#9ECE6A",  # Green
        "accent_4": "#E0AF68",  # Orange
        "accent_5": "#2AC3DE",  # Cyan
        "danger": "#F7768E",  # Red
    },
    "catppuccin_mocha": {
        "description": "Soothing pastel dark theme.",
        "background": "#1E1E2E",
        "primary_text": "#CDD6F4",
        "secondary_text": "#A6ADC8",
        "accent_1": "#CBA6F7",  # Mauve
        "accent_2": "#F38BA8",  # Red
        "accent_3": "#FAB387",  # Peach
        "accent_4": "#A6E3A1",  # Green
        "accent_5": "#89B4FA",  # Blue
        "danger": "#F38BA8",  # Red
    },
}


def get_available_palettes() -> str:
    """Returns a formatted string of all available palettes."""
    output = ["Available Aesthetic Palettes:"]
    for name, data in PALETTES.items():
        output.append(f"- {name}: {data['description']}")
    return "\n".join(output)


async def get_aesthetic_palette(
    _ctx: RunContext[GlobalContext], palette_name: str
) -> str:
    """Retrieves a curated, professional color palette for styling Manim animations.

    Use this tool instead of relying on default Manim colors (like RED, BLUE) to
    ensure the generated video has a modern, beautiful, and consistent visual design.

    Args:
        palette_name: The name of the palette (e.g., 'nord', 'dracula', 'tokyo_night').
                      Pass 'list' or 'help' to see all available options.

    Returns:
        A formatted string containing the hex codes for the requested palette,
        or a list of available palettes if not found.
    """
    logger.info("get_aesthetic_palette_called", palette_name=palette_name)

    name = palette_name.lower().strip()

    if name in ("list", "help", ""):
        return get_available_palettes()

    if name not in PALETTES:
        return f"Palette '{name}' not found.\n\n" + get_available_palettes()

    palette = PALETTES[name]
    output = [f"--- PALETTE: {name.upper()} ---"]
    output.append(f"Description: {palette['description']}")
    output.append(
        "\nHex Codes (Use these directly in Manim via string, e.g. set_color('#2E3440')):"
    )

    for key, value in palette.items():
        if key != "description":
            output.append(f"- {key}: {value}")

    return "\n".join(output)
