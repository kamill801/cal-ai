import type { WorkoutExercise, WorkoutExercisePerformance, WorkoutSetLog } from "@cal-ai/shared";

export const maxWorkoutSets = 20;
export const effortOptions = [
  { key: "easy", label: "가벼웠어요", score: 5 },
  { key: "on_target", label: "적당했어요", score: 7 },
  { key: "hard", label: "힘들었어요", score: 9 }
] as const;

export interface SetDraft {
  readonly amount: string;
  readonly load: string;
  readonly completed: boolean;
}

export function isTimedExercise(exercise: WorkoutExercise): boolean {
  return exercise.reps.includes("초");
}

export function createSetDraft(exercise: WorkoutExercise): SetDraft {
  return {
    amount: !isTimedExercise(exercise) && exercise.recommendedReps !== undefined ? String(exercise.recommendedReps) : "",
    load: !isTimedExercise(exercise) && exercise.recommendedLoadKg !== undefined ? String(exercise.recommendedLoadKg) : "",
    completed: false
  };
}

export function parseSetDraft(draft: SetDraft, index: number, timed: boolean): WorkoutSetLog | null {
  const amount = draft.amount.trim();
  const load = draft.load.trim().replace(",", ".");
  if (amount && (!/^\d+$/.test(amount) || +amount < 1 || +amount > (timed ? 600 : 100))) return null;
  if (!timed && load && (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(load) || +load > 500)) return null;
  return {
    setNumber: index + 1,
    ...(amount ? (timed ? { durationSeconds: +amount } : { repsCompleted: +amount }) : {}),
    ...(!timed && load ? { loadKg: +load } : {})
  };
}

export function buildWorkoutPerformance(exercise: WorkoutExercise, drafts: readonly SetDraft[], effort?: WorkoutExercisePerformance["effort"]): WorkoutExercisePerformance | undefined {
  const timed = isTimedExercise(exercise);
  const completedSets = drafts.flatMap((draft, index) => {
    const log = draft.completed ? parseSetDraft(draft, index, timed) : null;
    return log ? [log] : [];
  });
  return completedSets.length > 0 ? { exerciseId: exercise.id, setsCompleted: completedSets.length, completedSets, effort } : undefined;
}

export function restSecondsRemaining(deadlineMs: number, nowMs: number): number {
  return Math.max(0, Math.ceil((deadlineMs - nowMs) / 1000));
}

export function workoutIntensityLabel(score?: number): string | undefined {
  return score === undefined ? undefined : effortOptions[score < 6 ? 0 : score < 9 ? 1 : 2].label;
}
