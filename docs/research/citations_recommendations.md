# Academic Citations & Reference Recommendations

This document outlines key academic papers and resources recommended for the ConceptCast thesis. Each entry includes a technical justification for its inclusion in the context of the Agent Council and GCO architecture.

## 1. Multi-Agent Systems & LLM Orchestration

### AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation
- **Authors**: Wu et al. (2023)
- **Why this matters**: This is the current state-of-the-art for multi-agent LLM systems. It provides a formal framework for agents that collaborate through conversation, which directly supports your "Agent Council" narrative in Chapter 4. Use this to justify the transition from a single model to a council.

### Generative Agents: Interactive Simulacra of Human Behavior
- **Authors**: Park et al. (2023)
- **Why this matters**: This paper introduced "Architecture of Generative Agents" (memory stream, reflection, and planning). It is foundational for explaining how agents maintain a persona and plan ahead, which justifies the `Analyst` and `Architect` agents in your framework.

## 2. Architecture & Memory Systems

### A Blackboard Architecture for Control
- **Authors**: Barbara Hayes-Roth (1985)
- **Why this matters**: This is the theoretical ancestor of your **Global Context Object (GCO)**. The blackboard model allows multiple independent "knowledge sources" (your agents) to contribute to a shared state. Citing this provides significant academic weight to your "Layered Memory" methodology.

### Voyager: An Open-Ended Embodied Agent with Large Language Models as Iterative Self-Paced Learners
- **Authors**: Wang et al. (2023)
- **Why this matters**: Voyager uses a "Skill Library" and an "Automatic Curriculum," which mirrors how your `Analyst` breaks down a topic. More importantly, it features an "Environment Feedback" loop that allows agents to fix their own code—directly supporting the logic behind your `Reviewer` agent and the repair loop.

## 3. Spatial Reasoning & Technical Engineering

### Sparks of Artificial General Intelligence: Early experiments with GPT-4
- **Authors**: Bubeck et al. (2023)
- **Why this matters**: Section 4 specifically explores GPT-4's ability to reason about 2D and 3D space. Use this to justify your pivot from fine-tuning smaller models (which fail at spatial logic) to utilizing larger frontier models for the `Architect` role.

### Thinking Fast and Slow in Large Language Models: System 1 & System 2
- **Authors**: Various (Recent AI literature often references Kahneman's framework)
- **Why this matters**: You can frame your GCO and "Thinking" phases as "System 2" reasoning (deliberate, planning) vs. standard chatbot interactions which are "System 1" (probabilistic, reactive).

## 4. Pedagogy & Educational Psychology

### Cognitive Load During Problem Solving: Effects on Learning
- **Author**: John Sweller (1988)
- **Why this matters**: This is critical for your "Problem Statement." It explains how high cognitive load (reading complex text answers) hinders learning. You can argue that ConceptCast's visual logic reduces cognitive load by externalizing the mental model into an animation.

### ChatGPT for Good? On Opportunities and Challenges of Large Language Models for Education
- **Authors**: Kasneci et al. (2023)
- **Why this matters**: Provides a balanced view on LLMs in education. Use it to support your claim about the "answer machine" effect and the importance of preserving the "how" and "why."

## 5. Core Engines

### Manim: A Community-Maintained Python Library for Creating Mathematical Animations
- **Author**: Grant Sanderson / Manim Community
- **Why this matters**: The primary engine. Citing the source demonstrates engineering rigor and acknowledges the foundation of your visualization layer.

### Pydantic AI: Agentic Framework for Python
- **Source**: Pydantic AI Team
- **Why this matters**: Justifies your use of a structured, type-safe framework for handling agent dependency injection and GCO persistence.
