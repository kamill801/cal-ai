---
name: cal-ai-design-quality
description: Use this for Cal AI visual design generation, UI/UX concept images, Figma direction prompts, or redesign loops when the goal is high-quality, non-generic, reference-informed app design without copying a fixed style.
metadata:
  short-description: Cal AI high-quality design loop
---

# Cal AI Design Quality

Use this skill when creating or evaluating Cal AI mobile UI concepts, visual direction prompts, Figma redesign briefs, or image-generation prompts. The goal is not to reuse one fixed tone. The goal is to repeatedly reach a high-quality, product-fit design outcome.

## Quality Bar

A good Cal AI visual direction must feel:

- Product-real: looks implementable as an actual mobile app, not only a marketing poster.
- Reference-informed: borrows design principles from references, never exact mascot, layout, text, brand, or trade dress.
- Trust-first: keeps calorie ranges, confidence, assumptions, and correction visible where nutrition accuracy matters.
- Emotionally easy: daily-use friendly, warm, low-shame, and non-clinical.
- Visually specific: has a clear art direction, palette, hierarchy, and component grammar.
- Korean-ready: Korean UI text must be short, legible, and natural. Generated image text is a draft, not implementation copy.

## Workflow

1. Define the design read in one sentence:
   - Audience
   - User job
   - Desired emotion
   - Trust requirement
   - Surface to generate

2. Separate style from quality:
   - Style can vary: cute, premium, minimal, editorial, warm, playful, calm, etc.
   - Quality must stay fixed: clear hierarchy, product realism, reference synthesis, credible nutrition UI, and non-copying constraints.

3. Inspect references before generating:
   - Identify 3-5 patterns worth adapting.
   - Identify what must not be copied.
   - Include at least one product-behavior pattern, not only visual mood.
   - If references are provided by the user, treat them as mood and quality benchmarks, not templates.

4. Build the prompt with these sections:
   - Use case
   - Asset type
   - Primary request
   - Audience
   - Reference sources and observed patterns
   - Patterns to adapt
   - Do not copy
   - Visual direction
   - Composition
   - Color and type
   - Text, if any
   - Must keep
   - Avoid
   - Output quality

5. Generate one focused image at a time.

6. Self-review the result before showing it:
   - Does it look like a usable app screen?
   - Is the food/photo evidence primary enough?
   - Is the trust structure visible?
   - Is the design too generic AI/SaaS?
   - Is the design too childish, too clinical, or too copied?
   - Would a Korean 20s-30s user plausibly use it daily?

7. Save the candidate non-destructively:
   - Save image concepts under `docs/design-concepts/`.
   - Save reusable prompts next to the image.
   - Save reference research under `docs/DESIGN_REFERENCE_RESEARCH.md` when new references inform the direction.

8. Stop at the approval gate:
   - Ask whether to approve, revise, or explore a variation.
   - Do not implement UI from an unapproved generated concept.

## Prompt Rules

- Never prompt for "AI app style" as a primary direction. That usually creates generic gradients, robots, and fake dashboards.
- Anchor the design in a concrete user moment: scan meal, review estimate, answer clarification, save meal, view daily guidance, or weekly insight.
- Use food photography as the main asset unless the requested surface is onboarding or coach.
- Use one original warmth device at most: mascot, sticker, friendly card, microcopy, or motion cue. Do not stack all of them.
- Keep nutrition trust visible through range, confidence, assumptions, and edit controls.
- For Korean UI text, use short copy that can be redrawn in Figma. Do not rely on generated text as final.

## Cal AI Product Constraints

- Prefer calorie ranges over exact one-number certainty.
- Ask only one or two high-impact clarification questions.
- Make correction feel like confirmation, not manual logging.
- Avoid shame, guilt, medical claims, and weight-loss pressure.
- Do not copy Cal AI, FoodLens, Lifesum, INOUT, YAZIO, MyFitnessPal, or user-provided references.
- Keep secrets, API details, backend settings, and production infrastructure out of visual prompts.

## Benchmark

The image at `assets/cal-ai-cute-trust-v1.png` is a quality benchmark, not a locked style. It demonstrates:

- Clear product surface instead of pure poster.
- Food-first hierarchy.
- Trust structure through calorie range, confidence, macros, and clarification.
- Original supportive character used as an accent.
- Korean consumer-app warmth without copying the input references.

When using the benchmark, preserve its level of craft and product specificity, not its exact mascot, palette, layout, or tone.
