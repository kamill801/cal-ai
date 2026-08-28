import type { CoachDashboard, WorkoutEffort, WorkoutHistory, WorkoutPlan } from "@cal-ai/shared";
import { Check } from "lucide-react-native";
import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
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
  readonly exercisePerformance: { exerciseId: string; setsCompleted: number; repsCompleted?: number; loadKg?: number; effort: WorkoutEffort }[];
  readonly sessionRpe: number;
}

interface PerformanceDraft {
  sets: string;
  reps: string;
  load: string;
  effort: WorkoutEffort;
}

export function TrainingScreen({ dashboard, plan, history, status, error, onGenerate, onComplete }: { readonly dashboard?: CoachDashboard; readonly plan?: WorkoutPlan; readonly history?: WorkoutHistory; readonly status: RequestStatus; readonly error?: FlowError; readonly onGenerate: () => void; readonly onComplete: (input: WorkoutCompletionInput) => void }) {
  const proteinTarget = dashboard?.nutrition.target.proteinG ?? 0;
  const proteinConsumed = dashboard?.nutrition.consumed.proteinG ?? 0;
  const proteinProgress = proteinTarget ? Math.min(1, proteinConsumed / proteinTarget) : 0;
  const proteinProgressPercent = Math.round(proteinProgress * 100);
  const planDayCount = Math.max(plan?.days.length ?? 1, 1);
  const nextDay = plan?.days[(dashboard?.training.completedSessions ?? 0) % planDayCount];
  const [completedExerciseIds, setCompletedExerciseIds] = useState<string[]>([]);
  const [performance, setPerformance] = useState<Record<string, PerformanceDraft>>({});
  const [durationMinutes, setDurationMinutes] = useState(String(plan?.sessionMinutes ?? 60));
  const [sessionRpe, setSessionRpe] = useState(7);

  useEffect(() => {
    setCompletedExerciseIds([]);
    setPerformance(Object.fromEntries((nextDay?.exercises ?? []).map((exercise) => [exercise.id, { sets: String(exercise.sets), reps: exercise.recommendedReps ? String(exercise.recommendedReps) : "", load: exercise.recommendedLoadKg ? String(exercise.recommendedLoadKg) : "", effort: "on_target" }])));
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
      [exerciseId]: { ...(current[exerciseId] ?? { sets: "", reps: "", load: "", effort: "on_target" }), [field]: value }
    }));
  }

  function updateEffort(exerciseId: string, effort: WorkoutEffort): void {
    setPerformance((current) => ({
      ...current,
      [exerciseId]: { ...(current[exerciseId] ?? { sets: "", reps: "", load: "", effort: "on_target" }), effort }
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
        const item = performance[exerciseId] ?? { sets: "0", reps: "", load: "", effort: "on_target" };
        const reps = item.reps.trim() ? Number(item.reps) : undefined;
        const load = item.load.trim() ? Number(item.load) : undefined;
        return {
          exerciseId,
          setsCompleted: Math.max(0, Math.min(20, Number(item.sets) || 0)),
          repsCompleted: Number.isFinite(reps) ? reps : undefined,
          loadKg: Number.isFinite(load) ? load : undefined,
          effort: item.effort
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
          <Text style={styles.title}>{nextDay ? "오늘 할 운동을\n준비했어요" : "내 상황에 맞는\n루틴을 만들어요"}</Text>
          <Text style={styles.subtitle}>목표, 운동 빈도, 회복 기록을 함께 보고 다음 세션을 정리해요.</Text>
        </View>
        <TrustBuddy size={104} pose="workout" />
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
            <Text style={styles.sessionHelp}>완료한 종목의 이름이나 체크박스를 눌러주세요. 현재 {completedExerciseIds.length}개 선택했어요.</Text>
            {nextDay.exercises.map((exercise) => {
              const isCompleted = completedExerciseIds.includes(exercise.id);
              const values = performance[exercise.id] ?? { sets: String(exercise.sets), reps: "", load: "", effort: "on_target" };
              return (
              <View key={exercise.id} style={[styles.exerciseRow, isCompleted && styles.exerciseRowCompleted]}>
                <View style={styles.exerciseHeader}>
                  <ExerciseCheckbox checked={isCompleted} label={`${exercise.name} 수행 완료`} onChange={() => toggleExercise(exercise.id)} />
                  <TouchableOpacity style={styles.exerciseHeading} onPress={() => toggleExercise(exercise.id)} accessibilityRole="button" accessibilityLabel={`${exercise.name} ${isCompleted ? "완료 취소" : "완료 체크"}`}>
                    <Text style={styles.exerciseName}>{exercise.name}</Text>
                    <Text style={styles.exerciseMeta}>{exercise.sets}세트 · {exercise.reps} · RIR {exercise.targetRir}</Text>
                  </TouchableOpacity>
                  <Text style={styles.rest}>{exercise.restSeconds}초</Text>
                </View>
                <View style={styles.exerciseBody}>
                  {exercise.lastPerformance ? <Text style={styles.previousPerformance}>이전 {formatPerformance(exercise.lastPerformance)}</Text> : null}
                  {exercise.progressionAction === "collect_baseline" ? (
                    <Text style={styles.baselinePrompt}>첫 수행의 중량과 반복을 기록하면 다음 목표를 계산해요.</Text>
                  ) : (
                    <View style={[styles.recommendation, recommendationTone(exercise.progressionAction)]}>
                      <View style={styles.recommendationHeader}>
                        <Text style={styles.recommendationTitle}>{recommendationLabel(exercise.progressionAction)}</Text>
                        <Text style={styles.recommendationTarget}>{formatRecommendation(exercise)}</Text>
                      </View>
                      <Text style={styles.recommendationReason}>{exercise.recommendationReason}</Text>
                    </View>
                  )}
                  <Text style={styles.rationale}>{exercise.rationale}</Text>
                  {isCompleted ? (
                    <View style={styles.performanceEditor}>
                      <View style={styles.performanceRow}>
                        <PerformanceInput label="세트" value={values.sets} onChangeText={(value) => updatePerformance(exercise.id, "sets", value)} />
                        <PerformanceInput label="반복" value={values.reps} onChangeText={(value) => updatePerformance(exercise.id, "reps", value)} />
                        <PerformanceInput label="kg" value={values.load} onChangeText={(value) => updatePerformance(exercise.id, "load", value)} decimal />
                      </View>
                      <View style={styles.effortRow} accessibilityRole="radiogroup">
                        {(["easy", "on_target", "hard"] as const).map((effort) => (
                          <TouchableOpacity key={effort} style={[styles.effortButton, values.effort === effort && styles.effortButtonSelected]} onPress={() => updateEffort(exercise.id, effort)} hitSlop={4} accessibilityRole="radio" accessibilityLabel={`${exercise.name} 체감 ${effortLabel(effort)}`} accessibilityState={{ selected: values.effort === effort }}>
                            <Text style={[styles.effortText, values.effort === effort && styles.effortTextSelected]}>{effortLabel(effort)}</Text>
                          </TouchableOpacity>
                        ))}
                      </View>
                    </View>
                  ) : null}
                </View>
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

          <CoachCard title="최근 운동" eyebrow={`${history?.totalSessions ?? 0}회 기록`}>
            <Text style={styles.body}>{history?.summary ?? "첫 운동을 기록하면 수행 흐름을 보여드려요."}</Text>
            {(history?.sessions ?? []).slice(0, 3).map((session) => (
              <View key={session.sessionId} style={styles.historyRow}>
                <View style={styles.historyCopy}>
                  <Text style={styles.historyTitle}>{session.workoutTitle}</Text>
                  <Text style={styles.historyMeta}>{session.performedOn} · {session.durationMinutes}분 · RPE {session.sessionRpe}</Text>
                </View>
                <Text style={styles.historyVolume}>{session.totalVolumeKg > 0 ? `${session.totalVolumeKg.toLocaleString()}kg` : `${session.exerciseCount}종목`}</Text>
              </View>
            ))}
          </CoachCard>
        </>
      ) : null}
    </ScrollView>
  );
}

const webCheckboxStyle: CSSProperties = {
  width: 28,
  height: 28,
  flexShrink: 0,
  margin: 0,
  accentColor: colors.leaf,
  cursor: "pointer"
};

function ExerciseCheckbox({ checked, label, onChange }: { readonly checked: boolean; readonly label: string; readonly onChange: () => void }) {
  if (Platform.OS === "web") {
    return <input type="checkbox" checked={checked} aria-label={label} onChange={onChange} style={webCheckboxStyle} />;
  }
  return (
    <TouchableOpacity
      style={[styles.exerciseCheck, checked && styles.exerciseCheckSelected]}
      onPress={onChange}
      hitSlop={8}
      accessibilityRole="checkbox"
      accessibilityLabel={label}
      accessibilityState={{ checked }}
    >
      {checked ? <Check color={colors.surface} size={18} strokeWidth={3} /> : null}
    </TouchableOpacity>
  );
}

function effortLabel(value: WorkoutEffort): string {
  return { easy: "여유", on_target: "적정", hard: "버거움" }[value];
}

function recommendationLabel(value: "collect_baseline" | "increase" | "hold" | "reduce"): string {
  return { collect_baseline: "기준 수집", increase: "증량", hold: "유지", reduce: "조절" }[value];
}

function formatPerformance(value: { setsCompleted: number; repsCompleted?: number; loadKg?: number; effort: WorkoutEffort }): string {
  const load = value.loadKg !== undefined ? `${value.loadKg}kg · ` : "";
  const reps = value.repsCompleted !== undefined ? `${value.repsCompleted}회 · ` : "";
  return `${load}${value.setsCompleted}세트 · ${reps}${effortLabel(value.effort)}`;
}

function formatRecommendation(exercise: WorkoutPlan["days"][number]["exercises"][number]): string {
  if (exercise.recommendedLoadKg !== undefined && exercise.recommendedReps !== undefined) {
    return `${exercise.recommendedLoadKg}kg × ${exercise.recommendedReps}회`;
  }
  if (exercise.recommendedReps !== undefined) {
    return `${exercise.recommendedReps}회`;
  }
  return "이번 수행을 기록해 주세요";
}

function recommendationTone(action: "collect_baseline" | "increase" | "hold" | "reduce") {
  if (action === "increase") return styles.recommendationIncrease;
  if (action === "reduce") return styles.recommendationReduce;
  return styles.recommendationNeutral;
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
  exerciseRow: { gap: spacing.sm, borderTopColor: colors.hairline, borderTopWidth: 1, paddingTop: spacing.md },
  exerciseRowCompleted: { borderTopColor: colors.leafMuted },
  exerciseHeader: { alignItems: "flex-start", flexDirection: "row", gap: spacing.sm },
  exerciseCheck: { width: 28, height: 28, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderRadius: 8, borderWidth: 1, backgroundColor: colors.surface },
  exerciseCheckSelected: { borderColor: colors.leaf, backgroundColor: colors.leaf },
  exerciseHeading: { flex: 1, minWidth: 0, gap: 2 },
  exerciseBody: { gap: spacing.xs, paddingLeft: 36 },
  exerciseName: { color: colors.ink, ...typography.bodyStrong },
  exerciseMeta: { color: colors.leaf, ...typography.caption },
  rationale: { color: colors.muted, ...typography.body },
  previousPerformance: { color: colors.body, ...typography.caption },
  baselinePrompt: { color: colors.muted, ...typography.caption },
  recommendation: { gap: 2, borderRadius: radii.control, padding: spacing.sm },
  recommendationHeader: { alignItems: "baseline", flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  recommendationNeutral: { backgroundColor: colors.surfaceSoft },
  recommendationIncrease: { backgroundColor: colors.leafTint },
  recommendationReduce: { backgroundColor: colors.warningBg },
  recommendationTitle: { color: colors.ink, ...typography.bodyStrong },
  recommendationTarget: { color: colors.leaf, ...typography.bodyStrong },
  recommendationReason: { color: colors.muted, ...typography.caption },
  rest: { color: colors.muted, ...typography.caption },
  performanceRow: { flexDirection: "row", gap: spacing.xs, marginTop: spacing.xs },
  performanceEditor: { gap: spacing.sm },
  performanceInputShell: { flex: 1, minWidth: 0, minHeight: 42, alignItems: "center", flexDirection: "row", borderColor: colors.hairline, borderRadius: 10, borderWidth: 1, backgroundColor: colors.canvas, paddingHorizontal: spacing.xs },
  performanceInput: { flex: 1, minWidth: 24, color: colors.ink, paddingVertical: spacing.xs, textAlign: "center", ...typography.bodyStrong },
  performanceUnit: { color: colors.muted, ...typography.caption },
  effortRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  effortButton: { minHeight: 36, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.surface, paddingHorizontal: spacing.sm },
  effortButtonSelected: { borderColor: colors.leaf, backgroundColor: colors.leaf },
  effortText: { color: colors.body, ...typography.caption },
  effortTextSelected: { color: colors.surface },
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
  listItem: { color: colors.body, ...typography.body },
  historyRow: { alignItems: "center", flexDirection: "row", gap: spacing.sm, borderTopColor: colors.hairline, borderTopWidth: 1, paddingTop: spacing.sm },
  historyCopy: { flex: 1, minWidth: 0 },
  historyTitle: { color: colors.ink, ...typography.bodyStrong },
  historyMeta: { color: colors.muted, ...typography.caption },
  historyVolume: { color: colors.leaf, ...typography.bodyStrong }
});
