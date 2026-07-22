import type { AnalysisResult, RangeNarrowingResult } from "@cal-ai/shared";
import type { ImageSourcePropType } from "react-native";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CalorieRange } from "../components/CalorieRange";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { ConfidencePill } from "../components/ConfidencePill";
import { MacroSummary } from "../components/MacroSummary";
import { MealPhotoFrame } from "../components/MealPhotoFrame";
import { RangeNarrowing } from "../components/RangeNarrowing";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { scanPhotoSource } from "../mockData";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function ReviewResultScreen({
  analysis,
  photoSource,
  narrowing,
  status,
  error,
  onSave,
  onEdit,
  onRetry
}: {
  analysis: AnalysisResult;
  photoSource?: ImageSourcePropType;
  narrowing?: RangeNarrowingResult;
  status: RequestStatus;
  error?: FlowError;
  onSave: () => void;
  onEdit: () => void;
  onRetry: () => void;
}) {
  const isSaving = status === "loading";
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>분석 결과</Text>
        <Text style={styles.subtitle}>{isSaving ? "식사 기록으로 저장하고 있어요" : "사진 한 장으로 믿을 수 있는 범위를 만들었어요"}</Text>
      </View>

      <View style={styles.photoStage}>
        <MealPhotoFrame
          source={photoSource ?? scanPhotoSource}
          stageText={analysis.mealName}
          confidenceLabel={analysis.summary.confidenceLabel}
          confidenceGroup={analysis.summary.confidenceGroup}
        />
        <View style={styles.buddyOverlay}>
          <TrustBuddy size={72} accessory="magnifier" />
        </View>
      </View>

      <View style={styles.resultCard}>
        <View style={styles.confidenceRow}>
          <Text style={styles.cardLabel}>AI가 분석한 예상 칼로리</Text>
          <ConfidencePill label={analysis.summary.confidenceLabel} group={analysis.summary.confidenceGroup} />
        </View>
        <CalorieRange range={analysis.summary.calorieRange} label="예상" />
        <MacroSummary macros={analysis.summary} />
        {narrowing ? <RangeNarrowing narrowing={narrowing} /> : null}
        <Text style={styles.explanation}>{analysis.primaryExplanation}</Text>
      </View>

      <View style={styles.foodCard}>
        <View style={styles.foodHeader}>
          <Text style={styles.sectionTitle}>사진상 확인한 음식</Text>
          <Text style={styles.foodHeaderMeta}>분석 근거 보기</Text>
        </View>
        {analysis.detectedFoods.map((food) => (
          <View key={food.id} style={styles.foodRow}>
            <Text style={styles.foodName}>{food.name}</Text>
            <Text style={styles.foodAssumption}>{food.assumptionLabel}</Text>
          </View>
        ))}
      </View>

      {isSaving ? <FlowStatusCard title="저장 중" message="식사 기록과 오늘 대시보드를 업데이트하고 있어요." /> : null}
      {error ? <FlowStatusCard error={error} onRetry={onRetry} /> : null}

      <View style={styles.actionRow}>
        <TouchableOpacity activeOpacity={0.82} style={[styles.secondaryButton, isSaving && styles.buttonDisabled]} disabled={isSaving} onPress={onEdit} accessibilityRole="button" accessibilityState={{ disabled: isSaving }}>
          <Text style={styles.secondaryButtonText}>수정</Text>
        </TouchableOpacity>
        <TouchableOpacity activeOpacity={0.86} style={[styles.primaryButton, isSaving && styles.buttonDisabled]} disabled={isSaving} onPress={onSave} accessibilityRole="button" accessibilityState={{ disabled: isSaving, busy: isSaving }}>
          <Text style={styles.primaryButtonText}>{isSaving ? "저장 중" : "식사로 기록"}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.md,
    padding: spacing.lg,
    paddingBottom: spacing.xxl
  },
  header: {
    alignItems: "center",
    gap: spacing.xs,
    paddingTop: spacing.sm
  },
  title: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  subtitle: {
    color: colors.body,
    textAlign: "center",
    ...typography.body
  },
  photoStage: {
    position: "relative",
    marginTop: spacing.sm
  },
  buddyOverlay: {
    position: "absolute",
    right: spacing.md,
    bottom: 62,
    zIndex: 4
  },
  resultCard: {
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.photo,
    borderWidth: 1,
    backgroundColor: colors.surface,
    marginTop: -spacing.sm,
    padding: spacing.lg,
    ...shadows.card
  },
  confidenceRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: spacing.sm
  },
  cardLabel: {
    color: colors.muted,
    ...typography.caption
  },
  explanation: {
    color: colors.body,
    ...typography.body
  },
  foodCard: {
    gap: spacing.sm,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg,
    ...shadows.card
  },
  foodHeader: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: spacing.sm
  },
  sectionTitle: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  foodHeaderMeta: {
    color: colors.muted,
    ...typography.caption
  },
  foodRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: spacing.sm,
    borderTopColor: colors.hairline,
    borderTopWidth: 1,
    paddingTop: spacing.sm
  },
  foodName: {
    color: colors.ink,
    ...typography.bodyStrong
  },
  foodAssumption: {
    color: colors.muted,
    ...typography.caption
  },
  actionRow: {
    flexDirection: "row",
    gap: spacing.sm
  },
  primaryButton: {
    flex: 2,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 58,
    borderRadius: radii.control,
    backgroundColor: colors.leaf,
    padding: spacing.md
  },
  buttonDisabled: {
    opacity: 0.55
  },
  primaryButtonText: {
    color: colors.surface,
    textAlign: "center",
    fontSize: 16,
    lineHeight: 21,
    fontWeight: "800"
  },
  secondaryButton: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 58,
    borderColor: colors.hairline,
    borderRadius: radii.control,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.md
  },
  secondaryButtonText: {
    color: colors.ink,
    textAlign: "center",
    fontSize: 15,
    lineHeight: 20,
    fontWeight: "800"
  }
});
