# Architecture

ConceptCast is a modular system designed for automated educational video production using a "Council" of specialized AI agents.

## Tech Stack

### Frontend
- **React + Vite**: High-performance, reactive user dashboard.
- **TanStack Query**: Asynchronous state management.
- **Zustand**: Client-side global state management.
- **Tailwind CSS v4**: Utility-first styling.
- **TypeScript**: Type-safety across the monorepo.

### Backend
- **FastAPI (Python)**: Async web framework for orchestrating agents.
- **uv**: High-speed Python package and project manager.
- **Manim Community**: Mathematical animation engine.
- **Pydantic-AI**: Agent orchestration framework.
- **Loguru**: Enhanced logging.

---

## AI Agents (The Council)

ConceptCast orchestrates multiple specialized agents to transform a text topic into a high-fidelity educational video.

### 1. Analyst Agent ("The Pedagogue")
- **Responsibility**: Deconstructs a complex topic into a sequential series of pedagogical steps.
- **Model**: `google-gla:gemini-1.5-pro`.
- **Output**: `CurriculumPlan`.

### 2. Validator Agent ("The Critic")
- **Responsibility**: Performs a pedagogical audit of the plan. Ensures logical progression and clarity.
- **Output**: `ValidationResult`.

### 3. Visual Architect Agent ("The Scenographer")
- **Responsibility**: Translates the curriculum into a detailed storyboard of Manim-compatible scenes and objects.
- **Output**: `Storyboard`.

### 4. Animator Agent ("The Animator")
- **Responsibility**: Translates the storyboard into executable Manim Python code.
- **Output**: Raw Python source code.

---

## System Flow

1. **User Request**: Topic and audience level submitted to FastAPI.
2. **Pedagogical Design**: Analyst generates the curriculum.
3. **Audit**: Validator checks the plan for accuracy and flow.
4. **Visual Mapping**: Architect creates scenes and visual objects.
5. **Code Generation**: Animator writes the Manim Python script.
6. **Rendering**: Subprocess runs Manim to produce the final MP4.
7. **Delivery**: Video is served via static file mount to the React dashboard.
