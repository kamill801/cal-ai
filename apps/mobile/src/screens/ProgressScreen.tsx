import type { BodyCheckIn, ProgressSummary } from "@cal-ai/shared";
import { Check } from "lucide-react-native";
import { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { CoachCard } from "../components/CoachCard";
import { FlowStatusCard } from "../components/FlowStatusCard";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, shadows, spacing, typography } from "../theme";

type BodyPhotoView = BodyCheckIn["view"];

const BODY_PHOTO_VIEWS: ReadonlyArray<{ readonly value: BodyPhotoView; readonly label: string; readonly description: string }> = [
  { value: "front", label: "정면", description: "카메라를 정면으로 바라봐요" },
  { value: "side", label: "측면", description: "몸을 옆으로 돌려 촬영해요" },
  { value: "back", label: "후면", description: "카메라를 등지고 촬영해요" }
];

export function ProgressScreen({ progress, latestBodyCheckIn, status, error, onLogWeight, onLogWellness, onCaptureBody, onPickBody }: { readonly progress?: ProgressSummary; readonly latestBodyCheckIn?: BodyCheckIn; readonly status: RequestStatus; readonly error?: FlowError; readonly onLogWeight: (weightKg: number) => void; readonly onLogWellness: (input: { energy: number; sleepQuality: number; soreness: number }) => void; readonly onCaptureBody: (consentToAiAnalysis: true, view: BodyPhotoView) => void; readonly onPickBody: (consentToAiAnalysis: true, view: BodyPhotoView) => void }) {
  const [weight, setWeight] = useState(progress?.latestWeightKg?.toString() ?? "");
  const [energy, setEnergy] = useState(3);
  const [sleepQuality, setSleepQuality] = useState(3);
  const [soreness, setSoreness] = useState(2);
  const [bodyAnalysisConsent, setBodyAnalysisConsent] = useState(false);
  const [selectedBodyView, setSelectedBodyView] = useState<BodyPhotoView>("front");
  const parsedWeight = Number(weight);
  const selectedBodyViewOption = BODY_PHOTO_VIEWS.find(({ value }) => value === selectedBodyView) ?? BODY_PHOTO_VIEWS[0];

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>변화 기록</Text>
        <Text style={styles.title}>작은 기록이 몸의 변화를 보여줘요</Text>
        <Text style={styles.subtitle}>체중과 회복 상태, 같은 조건의 사진을 함께 보면 다음 운동을 더 현실적으로 조절할 수 있어요.</Text>
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
        <Text style={styles.scoreGuide}>1은 매우 낮음, 5는 매우 높음이에요. 근육통은 숫자가 높을수록 많이 뻐근하다는 뜻이에요.</Text>
        <ScoreRow label="에너지" value={energy} onChange={setEnergy} lowLabel="매우 낮음" highLabel="매우 높음" />
        <ScoreRow label="수면" value={sleepQuality} onChange={setSleepQuality} lowLabel="매우 나쁨" highLabel="매우 좋음" />
        <ScoreRow label="근육통" value={soreness} onChange={setSoreness} lowLabel="거의 없음" highLabel="매우 심함" />
        <TouchableOpacity style={styles.primaryButton} disabled={status === "loading"} onPress={() => onLogWellness({ energy, sleepQuality, soreness })} accessibilityRole="button"><Text style={styles.primaryButtonText}>오늘 상태 저장</Text></TouchableOpacity>
      </CoachCard>

      <CoachCard title="신체 사진 체크인" eyebrow="선택 기록">
        <Text style={styles.body}>같은 조명과 거리, 자세로 찍으면 지난 기록과 비교하기 좋아요. 원하는 촬영 방향을 먼저 골라주세요.</Text>
        <View style={styles.viewSelector} accessibilityRole="radiogroup" accessibilityLabel="신체 사진 촬영 방향">
          {BODY_PHOTO_VIEWS.map(({ value, label }) => {
            const isSelected = selectedBodyView === value;

            return (
              <TouchableOpacity
                key={value}
                style={[styles.viewOption, isSelected && styles.viewOptionSelected]}
                onPress={() => setSelectedBodyView(value)}
                accessibilityRole="radio"
                accessibilityLabel={`${label} 사진`}
                accessibilityState={{ selected: isSelected }}
              >
                <Text style={[styles.viewOptionText, isSelected && styles.viewOptionTextSelected]}>{label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
        <Text style={styles.viewDescription}>{selectedBodyViewOption.description}</Text>
        <TouchableOpacity
          style={styles.consentRow}
          onPress={() => setBodyAnalysisConsent((value) => !value)}
          accessibilityRole="checkbox"
          accessibilityLabel="신체 사진 저장 및 제한적 AI 관찰에 동의"
          accessibilityState={{ checked: bodyAnalysisConsent }}
        >
          <View style={[styles.checkbox, bodyAnalysisConsent && styles.checkboxChecked]}>
            {bodyAnalysisConsent ? <Check color={colors.surface} size={16} strokeWidth={3} /> : null}
          </View>
          <Text style={styles.consentText}>이 사진을 비공개로 저장하고 AI가 자세와 운동 초점만 제한적으로 관찰하는 데 동의해요.</Text>
        </TouchableOpacity>
        <Text style={styles.safety}>동의하기 전에는 사진을 촬영하거나 불러올 수 없어요. 체지방률, 질환, 외모 점수, 신원 같은 민감 정보는 추정하지 않아요.</Text>
        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.primaryButtonHalf, !bodyAnalysisConsent && styles.buttonDisabled]}
            disabled={status === "loading" || !bodyAnalysisConsent}
            onPress={() => onCaptureBody(true, selectedBodyView)}
            accessibilityRole="button"
            accessibilityLabel={`${selectedBodyViewOption.label} 사진 촬영`}
            accessibilityHint={bodyAnalysisConsent ? "카메라를 열어 신체 사진을 촬영합니다" : "먼저 사진 저장 및 AI 관찰에 동의해주세요"}
            accessibilityState={{ disabled: status === "loading" || !bodyAnalysisConsent }}
          >
            <Text style={styles.primaryButtonText}>{status === "loading" ? "처리 중" : "사진 촬영"}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.secondaryButton, !bodyAnalysisConsent && styles.buttonDisabled]}
            disabled={status === "loading" || !bodyAnalysisConsent}
            onPress={() => onPickBody(true, selectedBodyView)}
            accessibilityRole="button"
            accessibilityLabel={`${selectedBodyViewOption.label} 사진 선택`}
            accessibilityHint={bodyAnalysisConsent ? "사진 보관함에서 신체 사진을 선택합니다" : "먼저 사진 저장 및 AI 관찰에 동의해주세요"}
            accessibilityState={{ disabled: status === "loading" || !bodyAnalysisConsent }}
          >
            <Text style={styles.secondaryButtonText}>{status === "loading" ? "처리 중" : "사진 선택"}</Text>
          </TouchableOpacity>
        </View>
        {!latestBodyCheckIn ? <Text style={styles.emptyState}>아직 저장된 신체 사진이 없어요. 첫 기록을 남기면 다음 체크인부터 같은 방향의 변화를 비교할 수 있어요.</Text> : null}
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

function ScoreRow({ label, value, onChange, lowLabel, highLabel }: { readonly label: string; readonly value: number; readonly onChange: (value: number) => void; readonly lowLabel: string; readonly highLabel: string }) {
  return (
    <View style={styles.scoreRow}>
      <Text style={styles.scoreLabel}>{label}</Text>
      <View style={styles.scoreButtons}>
        {[1, 2, 3, 4, 5].map((score) => (
          <TouchableOpacity
            key={score}
            style={[styles.scoreButton, value === score && styles.scoreButtonSelected]}
            onPress={() => onChange(score)}
            accessibilityRole="radio"
            accessibilityLabel={`${label} ${score}점, ${score === 1 ? lowLabel : score === 5 ? highLabel : "보통 범위"}`}
            accessibilityState={{ selected: value === score }}
          >
            <Text style={[styles.scoreText, value === score && styles.scoreTextSelected]}>{score}</Text>
          </TouchableOpacity>
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
  scoreGuide: { color: colors.muted, ...typography.caption },
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
  viewSelector: { flexDirection: "row", gap: spacing.xs, padding: 4, borderRadius: radii.control, backgroundColor: colors.canvas },
  viewOption: { flex: 1, minHeight: 44, alignItems: "center", justifyContent: "center", borderColor: "transparent", borderWidth: 1, borderRadius: radii.control, paddingHorizontal: spacing.sm },
  viewOptionSelected: { borderColor: colors.leafMuted, backgroundColor: colors.surface, ...shadows.card },
  viewOptionText: { color: colors.muted, ...typography.bodyStrong },
  viewOptionTextSelected: { color: colors.leaf },
  viewDescription: { color: colors.body, textAlign: "center", ...typography.caption },
  consentRow: { alignItems: "flex-start", flexDirection: "row", gap: spacing.sm, minHeight: 44 },
  checkbox: { width: 24, height: 24, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderWidth: 1, borderRadius: 6, backgroundColor: colors.surface },
  checkboxChecked: { borderColor: colors.leaf, backgroundColor: colors.leaf },
  consentText: { flex: 1, color: colors.body, ...typography.body },
  buttonDisabled: { opacity: 0.42 },
  emptyState: { borderTopColor: colors.hairline, borderTopWidth: 1, color: colors.muted, paddingTop: spacing.md, ...typography.caption },
  observation: { gap: spacing.xs, borderTopColor: colors.leafMuted, borderTopWidth: 1, paddingTop: spacing.md },
  observationTitle: { color: colors.ink, ...typography.bodyStrong },
  focusTitle: { color: colors.leaf, ...typography.bodyStrong },
  listItem: { color: colors.body, ...typography.body },
  safety: { color: colors.muted, ...typography.caption }
});
