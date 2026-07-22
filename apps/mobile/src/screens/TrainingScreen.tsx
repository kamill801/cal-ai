import type { CoachDashboard, WorkoutPlan } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CoachCard } from "../components/CoachCard";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function TrainingScreen({ dashboard, plan, status, error, onGenerate, onComplete }: { readonly dashboard?: CoachDashboard; readonly plan?: WorkoutPlan; readonly status: RequestStatus; readonly error?: FlowError; readonly onGenerate: () => void; readonly onComplete: (plan: WorkoutPlan) => void }) {
  const proteinTarget = dashboard?.nutrition.target.proteinG ?? 0;
  const proteinConsumed = dashboard?.nutrition.consumed.proteinG ?? 0;
  const proteinProgress = proteinTarget ? Math.min(1, proteinConsumed / proteinTarget) : 0;
  const nextDay = plan?.days[(dashboard?.training.completedSessions ?? 0) % (plan?.days.length ?? 1)];

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>TRAINING</Text>
          <Text style={styles.title}>오늘 운동, 이것만 하면 충분해요</Text>
          <Text style={styles.subtitle}>목표, 운동 빈도, 회복 기록을 함께 보고 다음 세션을 정리해요.</Text>
        </View>
        <TrustBuddy size={64} accessory="sprout" />
      </View>

      {error ? <FlowStatusCard error={error} /> : null}
      <CoachCard title={`단백질 ${proteinConsumed} / ${proteinTarget}g`} eyebrow="운동을 위한 오늘의 연료" tone="leaf">
        <View style={styles.progressTrack}><View style={[styles.progressFill, { width: `${Math.round(proteinProgress * 100)}%` }]} /></View>
        <Text style={styles.body}>{dashboard?.nutrition.guidance ?? "식사를 기록하면 운동일 단백질 잔여량을 보여드려요."}</Text>
      </CoachCard>

      {!plan ? (
        <CoachCard title="내 첫 운동 계획" eyebrow="주간 루틴">
          <Text style={styles.body}>복잡한 분할보다 반복하기 쉬운 전신 루틴으로 시작해요. 각 세트는 2회 정도 여유를 남겨요.</Text>
          <TouchableOpacity style={styles.primaryButton} disabled={status === "loading"} onPress={onGenerate} accessibilityRole="button">
            <Text style={styles.primaryButtonText}>{status === "loading" ? "계획 만드는 중" : "운동 계획 만들기"}</Text>
          </TouchableOpacity>
        </CoachCard>
      ) : null}

      {plan && nextDay ? (
        <>
          <CoachCard title={nextDay.title} eyebrow={`다음 운동 · ${nextDay.focus}`} tone="warm">
            {nextDay.exercises.map((exercise) => (
              <View key={exercise.id} style={styles.exerciseRow}>
                <View style={styles.exerciseCopy}>
                  <Text style={styles.exerciseName}>{exercise.name}</Text>
                  <Text style={styles.exerciseMeta}>{exercise.sets}세트 · {exercise.reps} · RIR {exercise.targetRir}</Text>
                  <Text style={styles.rationale}>{exercise.rationale}</Text>
                </View>
                <Text style={styles.rest}>{exercise.restSeconds}초</Text>
              </View>
            ))}
            <TouchableOpacity style={styles.primaryButton} disabled={status === "loading"} onPress={() => onComplete(plan)} accessibilityRole="button">
              <Text style={styles.primaryButtonText}>{status === "loading" ? "기록 중" : "오늘 운동 완료"}</Text>
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
  exerciseRow: { flexDirection: "row", gap: spacing.md, borderTopColor: colors.hairline, borderTopWidth: 1, paddingTop: spacing.md },
  exerciseCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  exerciseName: { color: colors.ink, ...typography.bodyStrong },
  exerciseMeta: { color: colors.leaf, ...typography.caption },
  rationale: { color: colors.muted, ...typography.body },
  rest: { color: colors.muted, ...typography.caption },
  primaryButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.leaf, padding: spacing.md, ...shadows.card },
  primaryButtonText: { color: colors.surface, fontSize: 15, lineHeight: 21, fontWeight: "800" },
  safety: { color: colors.muted, ...typography.caption },
  listItem: { color: colors.body, ...typography.body }
});
