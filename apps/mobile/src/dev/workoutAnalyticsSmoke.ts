import { isAnalyticsEventName, workoutSaveEventName } from "../analytics/events";

export function runWorkoutAnalyticsSmoke(): void {
  const completed = workoutSaveEventName(true);
  const partial = workoutSaveEventName(false);
  if (completed !== "workout_completed" || partial !== "workout_partial_saved") {
    throw new Error("workout analytics must follow the server-confirmed completion state");
  }
  if (!isAnalyticsEventName(completed) || !isAnalyticsEventName(partial)) {
    throw new Error("workout save events must remain valid analytics events");
  }
  console.log("workout completion analytics smoke passed (4 cases)");
}
