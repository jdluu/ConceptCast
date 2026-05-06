# ConceptCast

ConceptCast uses AI to turn complex ideas into clear educational videos. It employs an **Agent Council**—a team of specialized agents sharing a **Global Context Object (GCO)**—to research, storyboard, and script animations using the Manim engine.

## Table of Contents

- [Overview](#overview)
- [How it Works](#how-it-works)
- [Methodology](#methodology)
- [Documentation & Wiki](#documentation--wiki)


## Overview

The goal is to support critical thinking rather than replace it. ConceptCast automates the difficult parts of coding visualizations, making it easier to produce high-fidelity tutorials for math, science, and business.

## How it Works

ConceptCast is built with an extensible, object-oriented architecture. It orchestrates multiple AI agents (Analyst, Architect, Animator, and Reviewer) to transform a text topic into a pedagogical curriculum and eventually a rendered video.

The system uses **Pydantic AI**, making it easy to add support for new AI providers by implementing a new provider class. In this implementation, **Nano GPT** is used to access various open-source models. Model identifiers can be easily updated in `apps/backend/src/infra/ai/nano_models.txt`.

## Methodology: Layered Memory

Unlike traditional linear pipelines, ConceptCast uses a **Global Context Object (GCO)** as a shared "production bible."

1.  **Global State (GCO)**: Centralized tracking of visual lexicon, spatial layout, and previous errors.
2.  **Shared Context**: Targeted injectors provide agents with specific slices of the GCO, ensuring Scene 10 respects the style and layout established in Scene 1.
3.  **Local Memory**: Agents maintain internal reasoning loops for self-correction and tool usage.

## Documentation & Wiki

For technical enthusiasts and contributors, please refer to our **[Project Wiki](docs/wiki/Home.md)** for:

- **[Architecture](docs/wiki/Architecture.md)**: Deep dive into the tech stack and system design.
- **[Setup Guide](docs/wiki/Setup-Guide.md)**: Installation, development, and testing instructions.


