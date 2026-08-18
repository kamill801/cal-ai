import type { CoachDashboard, WorkoutPlan } from "@cal-ai/shared";
import { Check } from "lucide-react-native";
import { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { CoachCard } from "../components/CoachCard";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, shadows, spacing, typography } from "../theme";

interface WorkoutCompletionInput {
  readonly plan: WorkoutPlan;
  readonly workoutDayId: string;
  readonly durationMinutes: number;
  readonly completedExerciseIds: string[];
  readonly exercisePerformance: { exerciseId: string; setsCompleted: number; repsCompleted?: number; loadKg?: number }[];
  readonly sessionRpe: number;
}

export function TrainingScreen({ dashboard, plan, status, error, onGenerate, onComplete }: { readonly dashboard?: CoachDashboard; readonly plan?: WorkoutPlan; readonly status: RequestStatus; readonly error?: FlowError; readonly onGenerate: () => void; readonly onComplete: (input: WorkoutCompletionInput) => void }) {
  const proteinTarget = dashboard?.nutrition.target.proteinG ?? 0;
  const proteinConsumed = dashboard?.nutrition.consumed.proteinG ?? 0;
  const proteinProgress = proteinTarget ? Math.min(1, proteinConsumed / proteinTarget) : 0;
  const proteinProgressPercent = Math.round(proteinProgress * 100);
  const planDayCount = Math.max(plan?.days.length ?? 1, 1);
  const nextDay = plan?.days[(dashboard?.training.completedSessions ?? 0) % planDayCount];
  const [completedExerciseIds, setCompletedExerciseIds] = useState<string[]>([]);
  const [performance, setPerformance] = useState<Record<string, { sets: string; reps: string; load: string }>>({});
  const [durationMinutes, setDurationMinutes] = useState(String(plan?.sessionMinutes ?? 60));
  const [sessionRpe, setSessionRpe] = useState(7);

  useEffect(() => {
    setCompletedExerciseIds([]);
    setPerformance(Object.fromEntries((nextDay?.exercises ?? []).map((exercise) => [exercise.id, { sets: String(exercise.sets), reps: "", load: "" }])));
    setDurationMinutes(String(plan?.sessionMinutes ?? 60));
    setSessionRpe(7);
  }, [nextDay?.id, plan?.sessionMinutes]);

  const parsedDuration = Number(durationMinutes);
  const canSaveSession = completedExerciseIds.length > 0 && Number.isInteger(parsedDuration) && parsedDuration >= 5 && parsedDuration <= 240;

  function toggleExercise(exerciseId: string): void {
    setCompletedExerciseIds((current) => current.includes(exerciseId) ? current.filter((id) => id !== exerciseId) : [...current, exerciseId]);
  }

  function updatePerformance(exerciseId: string, field: "sets" | "reps" | "load", value: string): void {
    setPerformance((current) => ({
      ...current,
      [exerciseId]: { ...(current[exerciseId] ?? { sets: "", reps: "", load: "" }), [field]: value }
    }));
  }

  function saveSession(): void {
    if (!plan || !nextDay || !canSaveSession) {
      return;
    }
    onComplete({
      plan,
      workoutDayId: nextDay.id,
      durationMinutes: parsedDuration,
      completedExerciseIds,
      exercisePerformance: completedExerciseIds.map((exerciseId) => {
        const item = performance[exerciseId] ?? { sets: "0", reps: "", load: "" };
        const reps = item.reps.trim() ? Number(item.reps) : undefined;
        const load = item.load.trim() ? Number(item.load) : undefined;
        return {
          exerciseId,
          setsCompleted: Math.max(0, Math.min(20, Number(item.sets) || 0)),
          repsCompleted: Number.isFinite(reps) ? reps : undefined,
          loadKg: Number.isFinite(load) ? load : undefined
        };
      }),
      sessionRpe
    });
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>오늘의 운동</Text>
          <Text style={styles.title}>{nextDay ? "오늘 할 운동을 준비했어요" : "내 상황에 맞는 루틴을 만들어요"}</Text>
          <Text style={styles.subtitle}>목표, 운동 빈도, 회복 기록을 함께 보고 다음 세션을 정리해요.</Text>
        </View>
        <TrustBuddy size={64} accessory="sprout" />
      </View>

      {error ? <FlowStatusCard error={error} /> : null}
      <CoachCard title={proteinTarget > 0 ? `단백질 ${proteinConsumed} / ${proteinTarget}g` : "단백질 목표를 준비하고 있어요"} eyebrow="운동을 위한 오늘의 연료" tone="leaf">
        <View style={styles.progressTrack} accessible accessibilityRole="progressbar" accessibilityLabel="오늘 단백질 섭취 진행률" accessibilityValue={{ min: 0, max: 100, now: proteinProgressPercent }}><View style={[styles.progressFill, { width: `${proteinProgressPercent}%` }]} /></View>
        <Text style={styles.body}>{dashboard?.nutrition.guidance ?? "식사를 기록하면 운동일 단백질 섭취량과 남은 양을 보여드려요."}</Text>
      </CoachCard>

      {!plan ? (
        <CoachCard title="내 첫 운동 계획" eyebrow="주간 루틴">
          <Text style={styles.body}>복잡한 분할보다 반복하기 쉬운 전신 루틴으로 시작해요. 각 세트는 2회 정도 여유를 남겨요.</Text>
          <TouchableOpacity style={[styles.primaryButton, status === "loading" && styles.buttonDisabled]} disabled={status === "loading"} onPress={onGenerate} accessibilityRole="button" accessibilityLabel="개인 맞춤 운동 계획 만들기" accessibilityState={{ disabled: status === "loading", busy: status === "loading" }}>
            <Text style={styles.primaryButtonText}>{status === "loading" ? "계획 만드는 중" : "운동 계획 만들기"}</Text>
          </TouchableOpacity>
        </CoachCard>
      ) : null}

      {plan && nextDay ? (
        <>
          <CoachCard title={nextDay.title} eyebrow={`다음 운동 · ${nextDay.focus}`} tone="warm">
            {nextDay.exercises.map((exercise) => {
              const isCompleted = completedExerciseIds.includes(exercise.id);
              const values = performance[exercise.id] ?? { sets: String(exercise.sets), reps: "", load: "" };
              return (
              <View key={exercise.id} style={[styles.exerciseRow, isCompleted && styles.exerciseRowCompleted]}>
                <TouchableOpacity
                  style={[styles.exerciseCheck, isCompleted && styles.exerciseCheckSelected]}
                  onPress={() => toggleExercise(exercise.id)}
                  accessibilityRole="checkbox"
                  accessibilityLabel={`${exercise.name} 수행 완료`}
                  accessibilityState={{ checked: isCompleted }}
                >
                  {isCompleted ? <Check color={colors.surface} size={18} strokeWidth={3} /> : null}
                </TouchableOpacity>
                <View style={styles.exerciseCopy}>
                  <Text style={styles.exerciseName}>{exercise.name}</Text>
                  <Text style={styles.exerciseMeta}>{exercise.sets}세트 · {exercise.reps} · RIR {exercise.targetRir}</Text>
                  <Text style={styles.rationale}>{exercise.rationale}</Text>
                  {isCompleted ? (
                    <View style={styles.performanceRow}>
                      <PerformanceInput label="세트" value={values.sets} onChangeText={(value) => updatePerformance(exercise.id, "sets", value)} />
                      <PerformanceInput label="반복" value={values.reps} onChangeText={(value) => updatePerformance(exercise.id, "reps", value)} />
                      <PerformanceInput label="kg" value={values.load} onChangeText={(value) => updatePerformance(exercise.id, "load", value)} decimal />
                    </View>
                  ) : null}
                </View>
                <Text style={styles.rest}>{exercise.restSeconds}초</Text>
              </View>
            );})}
            <View style={styles.sessionFields}>
              <View style={styles.durationField}>
                <Text style={styles.fieldLabel}>운동 시간</Text>
                <View style={styles.durationInputShell}>
                  <TextInput style={styles.durationInput} value={durationMinutes} onChangeText={setDurationMinutes} keyboardType="number-pad" accessibilityLabel="운동 시간, 분" />
                  <Text style={styles.inputUnit}>분</Text>
                </View>
              </View>
              <View style={styles.rpeField}>
                <Text style={styles.fieldLabel}>오늘 체감 강도 RPE</Text>
                <View style={styles.rpeRow} accessibilityRole="radiogroup">
                  {[5, 6, 7, 8, 9, 10].map((value) => (
                    <TouchableOpacity key={value} style={[styles.rpeButton, sessionRpe === value && styles.rpeButtonSelected]} onPress={() => setSessionRpe(value)} accessibilityRole="radio" accessibilityLabel={`체감 강도 ${value}`} accessibilityState={{ selected: sessionRpe === value }}>
                      <Text style={[styles.rpeText, sessionRpe === value && styles.rpeTextSelected]}>{value}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            </View>
            <Text style={styles.sessionHelp}>완료한 종목만 체크해도 저장돼요. 중량과 반복은 다음 증량 판단에 사용합니다.</Text>
            <TouchableOpacity style={[styles.primaryButton, (status === "loading" || !canSaveSession) && styles.buttonDisabled]} disabled={status === "loading" || !canSaveSession} onPress={saveSession} accessibilityRole="button" accessibilityLabel="오늘 운동 수행 기록 저장" accessibilityState={{ disabled: status === "loading" || !canSaveSession, busy: status === "loading" }}>
              <Text style={styles.primaryButtonText}>{status === "loading" ? "기록 중" : `${completedExerciseIds.length}개 종목 기록 저장`}</Text>
            </TouchableOpacity>
          </CoachCard>

          <CoachCard title="이 계획에 반영한 것" eyebrow="개인화 근거">
            {plan.personalizationBasis.map((basis) => <Text key={basis} style={styles.listItem}>• {basis}</Text>)}
          </CoachCard>

          <CoachCard title="다음 중량은 이렇게" eyebrow="점진적 과부하">
            <Text style={styles.body}>{plan.progressionRule}</Text>
            <Text style={styles.safety}>{plan.safetyNote}</Text>
          </CoachCard>
        </>
      ) : null}
    </ScrollView>
  );
}

function PerformanceInput({ label, value, onChangeText, decimal = false }: { readonly label: string; readonly value: string; readonly onChangeText: (value: string) => void; readonly decimal?: boolean }) {
  return (
    <View style={styles.performanceInputShell}>
      <TextInput style={styles.performanceInput} value={value} onChangeText={onChangeText} keyboardType={decimal ? "decimal-pad" : "number-pad"} accessibilityLabel={`${label} 수행값`} />
      <Text style={styles.performanceUnit}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.lg, padding: spacing.lg, paddingBottom: 112 },
  header: { alignItems: "center", flexDirection: "row", gap: spacing.md, paddingTop: spacing.sm },
  headerCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.screenTitle },
  subtitle: { color: colors.body, ...typography.body },
  progressTrack: { height: 10, overflow: "hidden", borderRadius: radii.pill, backgroundColor: colors.leafMuted },
  progressFill: { height: "100%", borderRadius: radii.pill, backgroundColor: colors.leaf },
  body: { color: colors.body, ...typography.body },
  exerciseRow: { alignItems: "flex-start", flexDirection: "row", gap: spacing.sm, borderTopColor: colors.hairline, borderTopWidth: 1, paddingTop: spacing.md },
  exerciseRowCompleted: { borderTopColor: colors.leafMuted },
  exerciseCheck: { width: 28, height: 28, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderRadius: 8, borderWidth: 1, backgroundColor: colors.surface },
  exerciseCheckSelected: { borderColor: colors.leaf, backgroundColor: colors.leaf },
  exerciseCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  exerciseName: { color: colors.ink, ...typography.bodyStrong },
  exerciseMeta: { color: colors.leaf, ...typography.caption },
  rationale: { color: colors.muted, ...typography.body },
  rest: { color: colors.muted, ...typography.caption },
  performanceRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs, marginTop: spacing.xs },
  performanceInputShell: { width: 76, minHeight: 42, alignItems: "center", flexDirection: "row", borderColor: colors.hairline, borderRadius: 10, borderWidth: 1, backgroundColor: colors.canvas, paddingHorizontal: spacing.xs },
  performanceInput: { flex: 1, minWidth: 24, color: colors.ink, paddingVertical: spacing.xs, textAlign: "center", ...typography.bodyStrong },
  performanceUnit: { color: colors.muted, ...typography.caption },
  sessionFields: { gap: spacing.md, borderTopColor: colors.hairline, borderTopWidth: 1, paddingTop: spacing.md },
  durationField: { gap: spacing.xs },
  fieldLabel: { color: colors.ink, ...typography.bodyStrong },
  durationInputShell: { width: 130, minHeight: 46, alignItems: "center", flexDirection: "row", borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.canvas, paddingHorizontal: spacing.sm },
  durationInput: { flex: 1, color: colors.ink, paddingVertical: spacing.sm, ...typography.bodyStrong },
  inputUnit: { color: colors.muted, ...typography.caption },
  rpeField: { gap: spacing.xs },
  rpeRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  rpeButton: { width: 42, height: 42, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderRadius: 12, borderWidth: 1, backgroundColor: colors.surface },
  rpeButtonSelected: { borderColor: colors.leaf, backgroundColor: colors.leaf },
  rpeText: { color: colors.ink, ...typography.bodyStrong },
  rpeTextSelected: { color: colors.surface },
  sessionHelp: { color: colors.muted, ...typography.caption },
  primaryButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.leaf, padding: spacing.md, ...shadows.card },
  buttonDisabled: { opacity: 0.48 },
  primaryButtonText: { color: colors.surface, fontSize: 15, lineHeight: 21, fontWeight: "800" },
  safety: { color: colors.muted, ...typography.caption },
  listItem: { color: colors.body, ...typography.body }
});
