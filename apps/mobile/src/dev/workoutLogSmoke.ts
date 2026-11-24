import type { WorkoutExercise } from "@cal-ai/shared";
import { buildWorkoutPerformance, createSetDraft, parseSetDraft, restSecondsRemaining, workoutIntensityLabel } from "../flow/workoutLog";

function assert(value: unknown, message: string) {
  if (!value) throw new Error(message);
}

export function runWorkoutLogSmoke() {
  const exercise: WorkoutExercise = {
    id: "squat", name: "스쿼트", reps: "8-12회", sets: 3, targetRir: 2, restSeconds: 60,
    rationale: "하체", progressionAction: "hold", recommendationReason: "", recommendedLoadKg: 20, recommendedReps: 10
  };
  const untouched = createSetDraft(exercise);
  assert(buildWorkoutPerformance(exercise, [untouched]) === undefined, "suggested values do not imply completion");
  const record = buildWorkoutPerformance(exercise, [
    { ...untouched, completed: true },
    { amount: "8", load: "22,5", completed: true },
    untouched
  ]);
  assert(record?.setsCompleted === 2 && record?.completedSets?.[1]?.loadKg === 22.5 && record?.completedSets?.[1]?.repsCompleted === 8, "variable set values are preserved");
  assert(record?.effort === undefined, "missing exercise effort stays absent");
  const timed = parseSetDraft({ amount: "35", load: "", completed: true }, 1, true);
  assert(timed?.durationSeconds === 35 && timed?.repsCompleted === undefined && timed?.setNumber === 2, "timed exercises use seconds");
  assert(parseSetDraft({ amount: "101", load: "", completed: false }, 0, false) === null, "out of range repetitions are invalid");
  assert(parseSetDraft({ amount: "", load: "", completed: true }, 0, false)?.repsCompleted === undefined, "check-only sessions do not fabricate repetitions");
  assert(workoutIntensityLabel(undefined) === undefined && workoutIntensityLabel(9) === "힘들었어요", "history never invents intensity");
  assert(restSecondsRemaining(60_000, 540) === 60 && restSecondsRemaining(60_000, 61_000) === 0, "timer resumes from its deadline");
}
