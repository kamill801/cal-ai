import type { AnalysisResult } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CalorieRange } from "../components/CalorieRange";
import { MealPhotoFrame } from "../components/MealPhotoFrame";
import { scanPhotoSource } from "../mockData";
import { colors, radii, spacing, typography } from "../theme";

export function AnalyzeEvidenceScreen({ analysis, onClarify }: { analysis: AnalysisResult; onClarify: () => void }) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>사진 분석</Text>
        <Text style={styles.title}>꼼꼼히 확인하고 있어요</Text>
      </View>

      <MealPhotoFrame
        source={scanPhotoSource}
        stageText={analysis.stageText}
        confidenceLabel={analysis.summary.confidenceLabel}
        confidenceGroup={analysis.summary.confidenceGroup}
      />

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

      <TouchableOpacity activeOpacity={0.86} style={styles.primaryButton} onPress={onClarify} accessibilityRole="button">
        <Text style={styles.primaryButtonText}>밥 양만 확인하기</Text>
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
  primaryButtonText: {
    color: colors.surface,
    textAlign: "center",
    fontSize: 16,
    lineHeight: 21,
    fontWeight: "800"
  }
});
