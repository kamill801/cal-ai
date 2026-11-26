import type { BodyCheckIn, ProgressSummary } from "@cal-ai/shared";
import { Camera, Check, ChevronDown, ChevronRight, Flag, Moon, type LucideIcon } from "lucide-react-native";
import { useState, type ReactNode } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { ProgressWeightTrend, progressColors } from "../components/ProgressWeightTrend";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors, freshGreen, radii, shadows, spacing, typography } from "../theme";

type BodyPhotoView = BodyCheckIn["view"];

const BODY_PHOTO_VIEWS: ReadonlyArray<{ readonly value: BodyPhotoView; readonly label: string; readonly description: string }> = [
  { value: "front", label: "정면", description: "카메라를 정면으로 바라봐요" },
  { value: "side", label: "측면", description: "몸을 옆으로 돌려 촬영해요" },
  { value: "back", label: "후면", description: "카메라를 등지고 촬영해요" }
];

export function ProgressScreen({ progress, latestBodyCheckIn, status, error, bodyPhotoEnabled, onOpenSafety, onLogWeight, onLogWellness, onCaptureBody, onPickBody }: { readonly progress?: ProgressSummary; readonly latestBodyCheckIn?: BodyCheckIn; readonly status: RequestStatus; readonly error?: FlowError; readonly bodyPhotoEnabled: boolean; readonly onOpenSafety: () => void; readonly onLogWeight: (weightKg: number) => void; readonly onLogWellness: (input: { energy: number; sleepQuality: number; soreness: number }) => void; readonly onCaptureBody: (consentToAiAnalysis: true, view: BodyPhotoView) => void; readonly onPickBody: (consentToAiAnalysis: true, view: BodyPhotoView) => void }) {
  const [energy, setEnergy] = useState(3);
  const [sleepQuality, setSleepQuality] = useState(3);
  const [soreness, setSoreness] = useState(2);
  const [bodyAnalysisConsent, setBodyAnalysisConsent] = useState(false);
  const [selectedBodyView, setSelectedBodyView] = useState<BodyPhotoView>("front");
  const selectedBodyViewOption = BODY_PHOTO_VIEWS.find(({ value }) => value === selectedBodyView) ?? BODY_PHOTO_VIEWS[0];
  const targetAdjustment = progress?.targetAdjustment;
  const loading = status === "loading";
  const photoActionsDisabled = loading || !bodyAnalysisConsent;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>내 기록</Text>
          <Text style={styles.title} accessibilityRole="header">변화</Text>
        </View>
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <TrustBuddy size={60} pose="progress" />
        </View>
      </View>
      {error ? <FlowStatusCard error={error} /> : null}

      <ProgressWeightTrend progress={progress} loading={loading} onLogWeight={onLogWeight} />

      <View style={styles.disclosures}>
        <ProgressDisclosure icon={Moon} title="회복 상태" detail="체크인">
          <Text style={styles.scoreGuide}>1은 매우 낮음, 5는 매우 높음이에요. 근육통은 숫자가 높을수록 많이 뻐근하다는 뜻이에요.</Text>
          <ScoreRow label="에너지" value={energy} onChange={setEnergy} lowLabel="매우 낮음" highLabel="매우 높음" />
          <ScoreRow label="수면" value={sleepQuality} onChange={setSleepQuality} lowLabel="매우 나쁨" highLabel="매우 좋음" />
          <ScoreRow label="근육통" value={soreness} onChange={setSoreness} lowLabel="거의 없음" highLabel="매우 심함" />
          <TouchableOpacity
            style={[styles.primaryButton, loading && styles.buttonDisabled]}
            disabled={loading}
            onPress={() => onLogWellness({ energy, sleepQuality, soreness })}
            accessibilityRole="button"
            accessibilityState={{ disabled: loading }}
          >
            <Text style={styles.primaryButtonText}>오늘 상태 저장</Text>
          </TouchableOpacity>
        </ProgressDisclosure>

        <ProgressDisclosure icon={Camera} title="신체 사진" detail="선택 기록">
          {!bodyPhotoEnabled ? (
            <View style={styles.detail}>
              <Text style={styles.detailTitle}>신체 사진은 로그인 보호 후 제공해요</Text>
              <Text style={styles.body}>이번 베타에서는 체중과 회복 기록을 먼저 사용할 수 있어요. 신체 사진은 로그인으로 사용자를 구분하고 삭제 정책을 확인한 뒤 열 예정이에요.</Text>
              <TouchableOpacity style={styles.secondaryFullButton} onPress={onOpenSafety} accessibilityRole="button">
                <Text style={styles.secondaryButtonText}>사진과 기록 처리 방식 보기</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.detail}>
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
                  {bodyAnalysisConsent ? <Check color={freshGreen.onFill} size={16} strokeWidth={3} /> : null}
                </View>
                <Text style={styles.consentText}>이 사진을 비공개로 저장하고 AI가 자세와 운동 초점만 제한적으로 관찰하는 데 동의해요.</Text>
              </TouchableOpacity>
              <Text style={styles.safety}>동의하기 전에는 사진을 촬영하거나 불러올 수 없어요. 체지방률, 질환, 외모 점수, 신원 같은 민감 정보는 추정하지 않으며 앱에서 기록과 원본을 삭제할 수 있어요.</Text>
              <TouchableOpacity onPress={onOpenSafety} accessibilityRole="button"><Text style={styles.privacyLink}>사진과 기록 처리 방식 보기</Text></TouchableOpacity>
              <View style={styles.actionRow}>
                <TouchableOpacity
                  style={[styles.primaryButtonHalf, photoActionsDisabled && styles.buttonDisabled]}
                  disabled={photoActionsDisabled}
                  onPress={() => onCaptureBody(true, selectedBodyView)}
                  accessibilityRole="button"
                  accessibilityLabel={`${selectedBodyViewOption.label} 사진 촬영`}
                  accessibilityHint={bodyAnalysisConsent ? "카메라를 열어 신체 사진을 촬영합니다" : "먼저 사진 저장 및 AI 관찰에 동의해주세요"}
                  accessibilityState={{ disabled: photoActionsDisabled }}
                >
                  <Text style={styles.primaryButtonText}>{loading ? "처리 중" : "사진 촬영"}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.secondaryButton, photoActionsDisabled && styles.buttonDisabled]}
                  disabled={photoActionsDisabled}
                  onPress={() => onPickBody(true, selectedBodyView)}
                  accessibilityRole="button"
                  accessibilityLabel={`${selectedBodyViewOption.label} 사진 선택`}
                  accessibilityHint={bodyAnalysisConsent ? "사진 보관함에서 신체 사진을 선택합니다" : "먼저 사진 저장 및 AI 관찰에 동의해주세요"}
                  accessibilityState={{ disabled: photoActionsDisabled }}
                >
                  <Text style={styles.secondaryButtonText}>{loading ? "처리 중" : "사진 선택"}</Text>
                </TouchableOpacity>
              </View>
              {!latestBodyCheckIn ? <Text style={styles.emptyState}>아직 저장된 신체 사진이 없어요. 첫 기록을 남기면 다음 체크인부터 같은 방향의 변화를 비교할 수 있어요.</Text> : null}
            </View>
          )}

          {latestBodyCheckIn ? (
            <View style={styles.detail}>
              <Text style={styles.eyebrow}>제한된 사진 관찰</Text>
              <Text style={styles.detailTitle} accessibilityRole="header">이번 체크인에서 볼 것</Text>
              {latestBodyCheckIn.analysis.observations.map((observation) => (
                <View key={observation.title} style={styles.observation}><Text style={styles.observationTitle}>{observation.title}</Text><Text style={styles.body}>{observation.detail}</Text></View>
              ))}
              <Text style={styles.focusTitle}>운동 초점</Text>
              {latestBodyCheckIn.analysis.trainingFocus.map((focus) => <Text key={focus} style={styles.listItem}>• {focus}</Text>)}
              <Text style={styles.safety}>{latestBodyCheckIn.analysis.safetyNote}</Text>
            </View>
          ) : null}
        </ProgressDisclosure>

        <ProgressDisclosure icon={Flag} title="현재 목표 점검" detail="기록 기반">
          {targetAdjustment ? (
            <>
              {targetAdjustment.status === "suggested" ? (
                <Text style={styles.detailTitle}>하루 {targetAdjustment.calorieDelta > 0 ? "+" : ""}{targetAdjustment.calorieDelta}kcal 제안</Text>
              ) : null}
              <Text style={styles.body}>{targetAdjustment.reason}</Text>
              {targetAdjustment.requiresConfirmation ? <Text style={styles.safety}>자동으로 바꾸지 않아요. 목표 변경은 사용자가 확인한 뒤에만 적용됩니다.</Text> : null}
            </>
          ) : <Text style={styles.body}>{loading ? "목표를 불러오는 중이에요." : "목표 정보를 확인할 수 없어요."}</Text>}
        </ProgressDisclosure>
      </View>
    </ScrollView>
  );
}

function ProgressDisclosure({ icon: Icon, title, detail, children }: {
  readonly icon: LucideIcon;
  readonly title: string;
  readonly detail: string;
  readonly children: ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);
  const Chevron = expanded ? ChevronDown : ChevronRight;
  return (
    <View style={styles.disclosure}>
      <TouchableOpacity style={styles.disclosureButton} onPress={() => setExpanded(!expanded)} accessibilityRole="button" accessibilityLabel={`${title}, ${detail}`} accessibilityState={{ expanded }}>
        <Icon color={progressColors.brand} size={16} />
        <Text style={styles.disclosureTitle}>{title}</Text>
        <Text style={styles.disclosureMeta}>{detail}</Text>
        <Chevron color={progressColors.weak} size={15} />
      </TouchableOpacity>
      {expanded ? <View style={styles.disclosureContent}>{children}</View> : null}
    </View>
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
  screen: { flex: 1, backgroundColor: progressColors.paper },
  container: { paddingHorizontal: 22, paddingBottom: 36 },
  header: { minHeight: 82, flexDirection: "row", alignItems: "center", gap: spacing.md, borderBottomWidth: 1, borderBottomColor: progressColors.line, paddingVertical: 8 },
  headerCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  eyebrow: { color: progressColors.weak, ...typography.caption },
  title: { color: progressColors.ink, fontSize: 30, lineHeight: 37, fontWeight: "800" },
  disclosures: { marginTop: 19, borderTopWidth: 1, borderTopColor: progressColors.line },
  disclosure: { borderBottomWidth: 1, borderBottomColor: progressColors.line },
  disclosureButton: { minHeight: 46, flexDirection: "row", alignItems: "center", gap: 9, paddingVertical: 4, paddingRight: 2 },
  disclosureTitle: { flex: 1, color: progressColors.ink, fontSize: 14, fontWeight: "800" },
  disclosureMeta: { flexShrink: 1, color: progressColors.muted, fontSize: 12, fontWeight: "600" },
  disclosureContent: { gap: spacing.md, paddingTop: spacing.xs, paddingBottom: spacing.lg },
  detail: { gap: spacing.md },
  detailTitle: { color: progressColors.ink, ...typography.sectionTitle },
  body: { color: progressColors.muted, ...typography.body },
  scoreGuide: { color: colors.muted, ...typography.caption },
  scoreRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", gap: spacing.md },
  scoreLabel: { width: 52, color: colors.ink, ...typography.bodyStrong },
  scoreButtons: { flex: 1, flexDirection: "row", gap: spacing.xs },
  scoreButton: { flex: 1, minHeight: 40, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderWidth: 1, borderRadius: radii.control, backgroundColor: colors.surface },
  scoreButtonSelected: { borderColor: freshGreen.indicator, backgroundColor: freshGreen.tint },
  scoreText: { color: colors.muted, ...typography.caption },
  scoreTextSelected: { color: freshGreen.ink },
  primaryButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: freshGreen.fill, padding: spacing.md, ...shadows.card },
  primaryButtonHalf: { flex: 1, minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: freshGreen.fill, padding: spacing.md },
  primaryButtonText: { color: freshGreen.onFill, fontSize: 15, lineHeight: 21, fontWeight: "800" },
  secondaryButton: { flex: 1, minHeight: 52, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderWidth: 1, borderRadius: radii.control, backgroundColor: colors.surface, padding: spacing.md },
  secondaryFullButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderWidth: 1, borderRadius: radii.control, backgroundColor: colors.surface, padding: spacing.md },
  secondaryButtonText: { color: colors.ink, fontSize: 15, lineHeight: 21, fontWeight: "800" },
  actionRow: { flexDirection: "row", gap: spacing.sm },
  viewSelector: { flexDirection: "row", gap: spacing.xs, padding: 4, borderRadius: radii.control, backgroundColor: freshGreen.tint },
  viewOption: { flex: 1, minHeight: 44, alignItems: "center", justifyContent: "center", borderColor: "transparent", borderWidth: 1, borderRadius: radii.control, paddingHorizontal: spacing.sm },
  viewOptionSelected: { borderColor: freshGreen.track, backgroundColor: colors.surface, ...shadows.card },
  viewOptionText: { color: colors.muted, ...typography.bodyStrong },
  viewOptionTextSelected: { color: freshGreen.ink },
  viewDescription: { color: colors.body, textAlign: "center", ...typography.caption },
  consentRow: { alignItems: "flex-start", flexDirection: "row", gap: spacing.sm, minHeight: 44 },
  checkbox: { width: 24, height: 24, alignItems: "center", justifyContent: "center", borderColor: colors.hairline, borderWidth: 1, borderRadius: 6, backgroundColor: colors.surface },
  checkboxChecked: { borderColor: freshGreen.indicator, backgroundColor: freshGreen.fill },
  consentText: { flex: 1, color: colors.body, ...typography.body },
  buttonDisabled: { opacity: 0.42 },
  emptyState: { borderTopColor: colors.hairline, borderTopWidth: 1, color: colors.muted, paddingTop: spacing.md, ...typography.caption },
  observation: { gap: spacing.xs, borderTopColor: freshGreen.track, borderTopWidth: 1, paddingTop: spacing.md },
  observationTitle: { color: colors.ink, ...typography.bodyStrong },
  focusTitle: { color: freshGreen.ink, ...typography.bodyStrong },
  listItem: { color: colors.body, ...typography.body },
  safety: { color: colors.muted, ...typography.caption },
  privacyLink: { color: freshGreen.ink, ...typography.bodyStrong }
});
