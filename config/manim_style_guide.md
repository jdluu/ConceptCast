# ConceptCast Manim Style & Knowledge Guide (v0.20.1)

## 1. Spatial Reasoning & Layout
- **Canvas Boundaries**: 14 units wide (-7 to 7), 8 units high (-4 to 4).
- **Regions**:
  - `MAIN_STAGE`: Center (0,0), radius 3. For primary metaphors.
  - `CAPTION_ZONE`: Bottom (-4 to -3.5 Y). For formulas or brief labels.
  - `SIDEBAR`: Right (5 to 7 X). For parameters or constants.
- **Relative Anchors**: Always use `.next_to(other, direction, buff=...)` or `.align_to(other, direction)`.
- **Z-Index**: Use `.set_z_index()` to prevent occlusion between overlapping shapes and labels.

## 2. Pythonic Manim (Proficiency)
- **Modern Animations**: Use `.animate` syntax: `obj.animate.shift(UP).set_color(RED)`.
- **Grouping**: Always wrap related objects in a `VGroup` for collective transformations.
- **Math Labels**: Use `MathTex` with double backslashes: `MathTex(r"\\frac{a}{b}")`.
- **Performance**: Prefer `Create`, `Write`, `FadeIn`, and `FadeOut` for clean entrances/exits.

## 3. Timing & Narration Sync
- **Rule of Thumb**: 1 second of animation per ~130-150 words of narration is wrong. Actually, it is ~2.5 words per second.
- **Syncing**: The `run_time` of your total animations in a scene MUST sum up to the `narration_duration`.
- **Pacing**: Use `self.wait()` to fill gaps if animations finish before narration ends. Use `Wait(duration)` inside `self.play()` if needed.

## 4. Visual Creativity & Consistency
- **Colors**: 
  - `BLUE`: Primary (Entities)
  - `GOLD`: Secondary (Highlights/Insights)
  - `TEAL`: Tertiary (Connections/Links)
  - `RED`: Negative/Error/Force
  - `GREEN`: Positive/Success/Growth
- **Stroke**: Standard `stroke_width=4`. For sub-elements, use `2`.
- **Fonts**: Default to `Sans-Serif`.

## 5. Library Knowledge (v0.20.1)
- **DashedLine**: Use `dash_length=0.05` instead of `dash_spacing`.
- **Arrow**: Use `tip_length=0.25` or `tip_shape`. Do NOT use `max_tip_length`.
- **Coordinate Systems**: Use `Axes(x_range=[-5, 5], y_range=[-3, 3])` for graphing.
- **Dynamic Values**: Use `ValueTracker` to animate numerical changes in labels.
- **Complex Paths**: Use `MoveAlongPath` for orbital or non-linear motion.
