import type { BodyCheckIn, ProgressSummary } from "@cal-ai/shared";
import { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { CoachCard } from "../components/CoachCard";
import { FlowStatusCard } from "../components/FlowStatusCard";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function ProgressScreen({ progress, latestBodyCheckIn, status, error, onLogWeight, onLogWellness, onCaptureBody, onPickBody }: { readonly progress?: ProgressSummary; readonly latestBodyCheckIn?: BodyCheckIn; readonly status: RequestStatus; readonly error?: FlowError; readonly onLogWeight: (weightKg: number) => void; readonly onLogWellness: (input: { energy: number; sleepQuality: number; soreness: number }) => void; readonly onCaptureBody: () => void; readonly onPickBody: () => void }) {
  const [weight, setWeight] = useState(progress?.latestWeightKg?.toString() ?? "");
  const [energy, setEnergy] = useState(3);
  const [sleepQuality, setSleepQuality] = useState(3);
  const [soreness, setSoreness] = useState(2);
  const parsedWeight = Number(weight);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>PROGRESS</Text>
        <Text style={styles.title}>몸 변화는 한 장보다 흐름으로 봐요</Text>
        <Text style={styles.subtitle}>체중, 회복, 운동 기록과 같은 조건의 사진을 함께 보면 다음 조언이 더 현실적이에요.</Text>
      </View>
      {error ? <FlowStatusCard error={error} /> : null}

      <CoachCard title={progress?.latestWeightKg ? `최근 ${progress.latestWeightKg}kg` : "첫 체중 기록"} eyebrow="체중 추세">
        <View style={styles.inputRow}>
          <TextInput value={weight} onChangeText={setWeight} keyboardType="decimal-pad" placeholder="예: 72.0" placeholderTextColor={colors.muted} style={styles.input} accessibilityLabel="현재 체중" />
          <Text style={styles.unit}>kg</Text>
          <TouchableOpacity style={styles.smallButton} disabled={!Number.isFinite(parsedWeight) || status === "loading"} onPress={() => onLogWeight(parsedWeight)} accessibilityRole="button"><Text style={styles.smallButtonText}>기록</Text></TouchableOpacity>
        </View>
        <Text style={styles.body}>{progress?.weightChangeKg === undefined ? "주 2-3회 비슷한 시간에 기록하면 일시적인 수분 변화를 덜 크게 보게 돼요." : `첫 기록보다 ${progress.weightChangeKg > 0 ? "+" : ""}${progress.weightChangeKg}kg 변했어요.`}</Text>
      </CoachCard>

      {progress ? (
        <CoachCard
          title={progress.targetAdjustment.status === "suggested" ? `하루 ${progress.targetAdjustment.calorieDelta > 0 ? "+" : ""}${progress.targetAdjustment.calorieDelta}kcal 제안` : "현재 목표 점검"}
          eyebrow="기록 기반 조정"
          tone={progress.targetAdjustment.status === "suggested" ? "warm" : "leaf"}
        >
          <Text style={styles.body}>{progress.targetAdjustment.reason}</Text>
          {progress.targetAdjustment.requiresConfirmation ? <Text style={styles.safety}>자동으로 바꾸지 않아요. 목표 변경은 사용자가 확인한 뒤에만 적용됩니다.</Text> : null}
        </CoachCard>
      ) : null}

      <CoachCard title="오늘 회복 상태" eyebrow="1분 체크인" tone="warm">
        <ScoreRow label="에너지" value={energy} onChange={setEnergy} />
        <ScoreRow label="수면" value={sleepQuality} onChange={setSleepQuality} />
        <ScoreRow label="근육통" value={soreness} onChange={setSoreness} />
        <TouchableOpacity style={styles.primaryButton} disabled={status === "loading"} onPress={() => onLogWellness({ energy, sleepQuality, soreness })} accessibilityRole="button"><Text style={styles.primaryButtonText}>오늘 상태 저장</Text></TouchableOpacity>
      </CoachCard>

      <CoachCard title="신체 사진 체크인" eyebrow="선택 기록">
        <Text style={styles.body}>같은 조명, 거리, 자세로 찍으면 주간 변화를 비교하기 좋아요. 사진만으로 체지방률이나 건강 상태를 판단하지 않아요.</Text>
        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.primaryButtonHalf} disabled={status === "loading"} onPress={onCaptureBody} accessibilityRole="button"><Text style={styles.primaryButtonText}>사진 촬영</Text></TouchableOpacity>
          <TouchableOpacity style={styles.secondaryButton} disabled={status === "loading"} onPress={onPickBody} accessibilityRole="button"><Text style={styles.secondaryButtonText}>사진 선택</Text></TouchableOpacity>
        </View>
      </CoachCard>

      {latestBodyCheckIn ? (
        <CoachCard title="이번 체크인에서 볼 것" eyebrow="제한된 사진 관찰" tone="leaf">
          {latestBodyCheckIn.analysis.observations.map((observation) => (
            <View key={observation.title} style={styles.observation}><Text style={styles.observationTitle}>{observation.title}</Text><Text style={styles.body}>{observation.detail}</Text></View>
          ))}
          <Text style={styles.focusTitle}>운동 초점</Text>
          {latestBodyCheckIn.analysis.trainingFocus.map((focus) => <Text key={focus} style={styles.listItem}>• {focus}</Text>)}
          <Text style={styles.safety}>{latestBodyCheckIn.analysis.safetyNote}</Text>
        </CoachCard>
      ) : null}
    </ScrollView>
  );
}

function ScoreRow({ label, value, onChange }: { readonly label: string; readonly value: number; readonly onChange: (value: number) => void }) {
  return (
    <View style={styles.scoreRow}>
      <Text style={styles.scoreLabel}>{label}</Text>
      <View style={styles.scoreButtons}>
        {[1, 2, 3, 4, 5].map((score) => (
          <TouchableOpacity key={score} style={[styles.scoreButton, value === score && styles.scoreButtonSelected]} onPress={() => onChange(score)} accessibilityRole="button" accessibilityState={{ selected: value === score }}><Text style={[styles.scoreText, value === score && styles.scoreTextSelected]}>{score}</Text></TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.lg, padding: spacing.lg, paddingBottom: 112 },
  header: { gap: spacing.xs, paddingTop: spacing.sm },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.screenTitle },
  subtitle: { color: colors.body, ...typography.body },
  inputRow: { alignItems: "center", flexDirection: "row", gap: spacing.sm },
  input: { flex: 1, minWidth: 0, minHeight: 48, borderColor: colors.hairline, borderWidth: 1, borderRadius: radii.control, color: colors.ink, backgroundColor: colors.surface, paddingHorizontal: spacing.md, fontSize: 19, fontWeight: "800" },
  unit: { color: colors.muted, ...typography.bodyStrong },
  smallButton: { width: 64, minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.leaf, paddingHorizontal: spacing.sm },
  smallButtonText: { color: colors.surface, ...typography.bodyStrong },
  body: { color: colors.body, ...typography.body },
  scoreRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", gap: spacing.md },
  scoreLabel: { width: 52, color: colors.ink, ...typography.bodyStrong },
  scoreButtons: { flex: 1, flexDirection: "row", gap: spacing.xs },
  scoreButton: { flex: 1, minHeight: 40, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderWidth: 1, borderRadius: radii.control, backgroundColor: colors.surface },
  scoreButtonSelected: { borderColor: colors.leaf, backgroundColor: colors.leafTint },
  scoreText: { color: colors.muted, ...typography.caption },
  scoreTextSelected: { color: colors.leaf },
  primaryButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.leaf, padding: spacing.md, ...shadows.card },
  primaryButtonHalf: { flex: 1, minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.leaf, padding: spacing.md },
  primaryButtonText: { color: colors.surface, fontSize: 15, lineHeight: 21, fontWeight: "800" },
  secondaryButton: { flex: 1, minHeight: 52, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderWidth: 1, borderRadius: radii.control, backgroundColor: colors.surface, padding: spacing.md },
  secondaryButtonText: { color: colors.ink, fontSize: 15, lineHeight: 21, fontWeight: "800" },
  actionRow: { flexDirection: "row", gap: spacing.sm },
  observation: { gap: spacing.xs, borderTopColor: colors.leafMuted, borderTopWidth: 1, paddingTop: spacing.md },
  observationTitle: { color: colors.ink, ...typography.bodyStrong },
  focusTitle: { color: colors.leaf, ...typography.bodyStrong },
  listItem: { color: colors.body, ...typography.body },
  safety: { color: colors.muted, ...typography.caption }
});
