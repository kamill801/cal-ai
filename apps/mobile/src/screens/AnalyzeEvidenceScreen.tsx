import type { AnalysisResult } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CalorieRange } from "../components/CalorieRange";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { MealPhotoFrame } from "../components/MealPhotoFrame";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { scanPhotoSource } from "../mockData";
import { colors, radii, spacing, typography } from "../theme";

export function AnalyzeEvidenceScreen({
  analysis,
  status,
  error,
  onClarify,
  onRetry
}: {
  analysis?: AnalysisResult;
  status: RequestStatus;
  error?: FlowError;
  onClarify: () => void;
  onRetry: () => void;
}) {
  const isLoading = status === "loading";
  const canClarify = Boolean(analysis?.clarificationQuestion) && !isLoading && !error;
  const canReview = Boolean(analysis) && !analysis?.clarificationQuestion && !isLoading && !error;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>사진 분석</Text>
        <Text style={styles.title}>{isLoading ? "사진을 분석하고 있어요" : "꼼꼼히 확인하고 있어요"}</Text>
      </View>

      {analysis ? (
        <MealPhotoFrame
          source={scanPhotoSource}
          stageText={analysis.stageText}
          confidenceLabel={analysis.summary.confidenceLabel}
          confidenceGroup={analysis.summary.confidenceGroup}
        />
      ) : (
        <View style={styles.photoPlaceholder}>
          <Text style={styles.placeholderTitle}>식사 사진 준비 완료</Text>
          <Text style={styles.placeholderBody}>FastAPI 분석 작업을 만들고 결과를 불러오는 중이에요.</Text>
        </View>
      )}

      {isLoading ? <FlowStatusCard title="분석 중" message="사진 확인, 음식 추정, 칼로리 범위 계산을 순서대로 진행하고 있어요." /> : null}
      {error ? <FlowStatusCard error={error} onRetry={onRetry} /> : null}

      {analysis ? (
        <View style={styles.panel}>
          <CalorieRange range={analysis.summary.calorieRange} />
          <Text style={styles.explanation}>{analysis.primaryExplanation}</Text>
          <View style={styles.foodList}>
            {analysis.detectedFoods.map((food) => (
              <View key={food.id} style={styles.foodRow}>
                <Text style={styles.foodName}>{food.name}</Text>
                <Text style={styles.foodAssumption}>{food.assumptionLabel}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      <TouchableOpacity
        activeOpacity={0.86}
        style={[styles.primaryButton, (!canClarify && !canReview) && styles.buttonDisabled]}
        onPress={onClarify}
        disabled={!canClarify && !canReview}
        accessibilityRole="button"
        accessibilityState={{ disabled: !canClarify && !canReview, busy: isLoading }}
      >
        <Text style={styles.primaryButtonText}>{canReview ? "결과 확인하기" : "밥 양만 확인하기"}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.lg,
    padding: spacing.lg,
    paddingBottom: spacing.xxl
  },
  header: {
    gap: spacing.xs
  },
  eyebrow: {
    color: colors.leaf,
    ...typography.caption
  },
  title: {
    color: colors.ink,
    ...typography.screenTitle
  },
  photoPlaceholder: {
    gap: spacing.sm,
    minHeight: 180,
    justifyContent: "center",
    borderColor: colors.hairline,
    borderRadius: radii.photo,
    borderWidth: 1,
    backgroundColor: colors.surfaceSoft,
    padding: spacing.lg
  },
  placeholderTitle: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  placeholderBody: {
    color: colors.body,
    ...typography.body
  },
  panel: {
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg
  },
  explanation: {
    color: colors.body,
    ...typography.body
  },
  foodList: {
    gap: spacing.sm
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
  primaryButton: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: 52,
    borderRadius: radii.control,
    backgroundColor: colors.leaf,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md
  },
  buttonDisabled: {
    opacity: 0.5
  },
  primaryButtonText: {
    color: colors.surface,
    textAlign: "center",
    fontSize: 16,
    lineHeight: 21,
    fontWeight: "800"
  }
});
