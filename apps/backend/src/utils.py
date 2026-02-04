from schemas import CurriculumPlan, TeachingStep


def generate_mock_plan(topic: str, target_audience: str) -> CurriculumPlan:
    """
    Generates a deterministic mock curriculum plan for development/testing.

    Args:
        topic: The requested topic.
        target_audience: The target audience.

    Returns:
        CurriculumPlan: A structured mock plan.
    """
    return CurriculumPlan(
        concept_title=f"Mock: {topic}",
        target_audience=target_audience,
        teaching_steps=[
            TeachingStep(
                step_id=1,
                concept="Introduction",
                visual_metaphor="Opening curtain",
                narration="Welcome to the concept.",
            ),
            TeachingStep(
                step_id=2,
                concept="Core Logic",
                visual_metaphor="Gears turning",
                narration="This is how it works.",
            ),
        ],
    )
