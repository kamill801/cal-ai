# Competitive Product Research: Nutrition and Strength Coaching

Last reviewed: 2026-08-26

## Decision Summary

Cal AI should not try to out-YAZIO YAZIO with a larger recipe catalog or a broader fasting product. The product wedge is a trustworthy body-transformation loop for people who lift:

1. log food quickly,
2. correct uncertain estimates,
3. see the remaining calorie and protein target,
4. complete a prescribed strength session,
5. record actual performance and recovery,
6. receive a conservative, explained next target.

The competitive quality bar is therefore split in two:

- Nutrition logging must feel as quick and editable as a mature calorie tracker.
- Training must behave like a real logger first and an adaptive coach second.

## What We Adopt

### YAZIO: low-friction repeat logging

YAZIO combines photo, barcode, search, manual, recent, favorite, custom meal, and recipe logging with a daily diary. We should adopt the repeat-use principle without copying the full breadth in the first release.

Immediate product decisions:

- recent meals can be logged again without another AI call,
- individual meal records can be removed and daily totals recalculate,
- record IDs and dates are stable enough for history and correction,
- the photo flow remains the primary action, not the only action.

### Hevy: the session logger is the product

Hevy makes set completion, previous performance, rest timing, notes, personal records, and history central to the workout experience.

Immediate product decisions:

- show previous performance beside the current target,
- capture exercise-level effort instead of only session RPE,
- keep workout completion fast and usable in the gym,
- summarize recent sessions and volume without turning the screen into a dashboard wall.

### Fitbod: adapt from actual performance

Fitbod separates exercise selection from capability recommendations and adjusts sets, repetitions, and weight from training history, recovery, equipment, and feedback.

Immediate product decisions:

- keep deterministic exercise selection based on goal, experience, equipment, time, and recovery,
- update the next target after each recorded session,
- explain whether the app recommends increasing, holding, or reducing load.

### Alpha Progression and RP Hypertrophy: stable plan, precise progression

Alpha Progression keeps a stable program and recommends weight, repetitions, and RIR from actual performance. RP Hypertrophy adjusts volume from pump, soreness, workload, and recovery feedback and uses planned deloads.

Immediate product decisions:

- preserve a stable plan long enough to learn from repeated exercises,
- progress conservatively within a repetition range,
- use recovery to hold or reduce demands,
- defer mesocycles, per-muscle volume landmarks, and deload automation until enough workout history exists.

### JuggernautAI: readiness and transparent program phases

JuggernautAI uses user goals, strength, experience, recovery, weak points, and session feedback to adjust work from set to set through program blocks.

Immediate product decisions:

- readiness affects today's recommendation,
- program changes must name the evidence used,
- competition peaking and powerlifting-specific attempt selection are later specialist modes, not default MVP behavior.

### Ladder: coaching presence and pacing

Ladder combines an expert-authored weekly plan, in-ear coaching, video, pacing, progress tracking, and community. Its strength is not opaque automation but a feeling that a coach is present during the session.

Immediate product decisions:

- use short form cues and next-action language during training,
- keep the coach voice supportive and specific,
- defer audio coaching, community, and coach messaging until the tracking loop is proven.

## Quality Bar for Cal AI

Cal AI is not yet equal to mature category leaders in catalog size, wearable integrations, exercise video coverage, billing, or years of accumulated behavioral data. It can exceed them in a narrower Korean strength-training use case when these conditions are met:

- every estimate and recommendation exposes its evidence,
- Korean mixed meals are easy to correct,
- repeated meals take one tap rather than another scan,
- the workout screen remembers what the user actually lifted,
- the next load recommendation is deterministic and reversible,
- calorie, protein, training, weight, and recovery appear in one coherent weekly decision.

## Explicit Non-Goals for This Iteration

- copying competitor visual layouts or copy,
- adding fasting, a large recipe catalog, social feeds, or community,
- claiming injury diagnosis, posture diagnosis, or body-fat estimation,
- using an LLM to invent exercise prescriptions without structured constraints,
- automatic aggressive calorie or training-volume changes,
- powerlifting meet peaking, deload automation, or per-muscle volume landmarks before sufficient history exists.

## Sources

- YAZIO Help Center: https://help.yazio.com/hc/en-us/categories/360000052085-Diary
- Hevy features: https://www.hevyapp.com/features/
- Fitbod workout creation: https://help.fitbod.me/hc/en-us/articles/360004429814-How-Fitbod-Creates-Your-Workout
- Alpha Progression: https://alphaprogression.com/en
- RP Hypertrophy progression: https://help.rpstrength.com/hc/en-us/articles/32600173777815-How-does-the-app-determine-when-to-add-weight-reps-and-sets
- JuggernautAI: https://www.juggernautai.app/
- Ladder: https://www.joinladder.com/
