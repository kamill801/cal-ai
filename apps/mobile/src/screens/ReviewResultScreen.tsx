import type { AnalysisResult, RangeNarrowingResult } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CalorieRange } from "../components/CalorieRange";
import { ConfidencePill } from "../components/ConfidencePill";
import { MacroSummary } from "../components/MacroSummary";
import { MealPhotoFrame } from "../components/MealPhotoFrame";
import { RangeNarrowing } from "../components/RangeNarrowing";
import { scanPhotoSource } from "../mockData";
import { colors, radii, spacing, typography } from "../theme";

export function ReviewResultScreen({
  analysis,
  narrowing,
  onSave,
  onEdit
}: {
  analysis: AnalysisResult;
  narrowing?: RangeNarrowingResult;
  onSave: () => void;
  onEdit: () => void;
}) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>결과 확인</Text>
        <Text style={styles.title}>저장해도 괜찮은 추정이에요</Text>
      </View>

      <MealPhotoFrame
        source={scanPhotoSource}
        stageText={analysis.mealName}
        confidenceLabel={analysis.summary.confidenceLabel}
        confidenceGroup={analysis.summary.confidenceGroup}
      />

      <View style={styles.resultCard}>
        <View style={styles.confidenceRow}>
          <Text style={styles.cardLabel}>신뢰도</Text>
          <ConfidencePill label={analysis.summary.confidenceLabel} group={analysis.summary.confidenceGroup} />
        </View>
        <CalorieRange range={analysis.summary.calorieRange} />
        <MacroSummary macros={analysis.summary} />
        {narrowing ? <RangeNarrowing narrowing={narrowing} /> : null}
        <Text style={styles.explanation}>{analysis.primaryExplanation}</Text>
      </View>

      <View style={styles.foodCard}>
        <Text style={styles.sectionTitle}>사진상 확인한 음식</Text>
        {analysis.detectedFoods.map((food) => (
          <View key={food.id} style={styles.foodRow}>
            <Text style={styles.foodName}>{food.name}</Text>
            <Text style={styles.foodAssumption}>{food.assumptionLabel}</Text>
          </View>
        ))}
      </View>

      <View style={styles.actionRow}>
        <TouchableOpacity activeOpacity={0.82} style={styles.secondaryButton} onPress={onEdit} accessibilityRole="button">
          <Text style={styles.secondaryButtonText}>수정</Text>
        </TouchableOpacity>
        <TouchableOpacity activeOpacity={0.86} style={styles.primaryButton} onPress={onSave} accessibilityRole="button">
          <Text style={styles.primaryButtonText}>식사로 기록</Text>
        </TouchableOpacity>
      </View>
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
  resultCard: {
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg
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
    padding: spacing.lg
  },
  sectionTitle: {
    color: colors.ink,
    ...typography.sectionTitle
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
    minHeight: 52,
    borderRadius: radii.control,
    backgroundColor: colors.black,
    padding: spacing.md
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
    minHeight: 52,
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
