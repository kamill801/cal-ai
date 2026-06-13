import type { AnalysisResult, SavedImpactViewModel } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CalorieRange } from "../components/CalorieRange";
import { MealPhotoFrame } from "../components/MealPhotoFrame";
import { SavedImpact } from "../components/SavedImpact";
import { scanPhotoSource } from "../mockData";
import { colors, radii, spacing, typography } from "../theme";

export function SavedImpactScreen({ analysis, impact, onDone }: { analysis: AnalysisResult; impact: SavedImpactViewModel; onDone: () => void }) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>저장 완료</Text>
        <Text style={styles.title}>다음 식사 방향까지 정리했어요</Text>
      </View>
      <MealPhotoFrame source={scanPhotoSource} stageText={analysis.mealName} confidenceLabel={analysis.summary.confidenceLabel} confidenceGroup={analysis.summary.confidenceGroup} />
      <CalorieRange range={analysis.summary.calorieRange} compact />
      <SavedImpact impact={impact} />
      <TouchableOpacity activeOpacity={0.86} style={styles.primaryButton} onPress={onDone} accessibilityRole="button">
        <Text style={styles.primaryButtonText}>대시보드로 돌아가기</Text>
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
  primaryButton: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: 52,
    borderRadius: radii.control,
    backgroundColor: colors.leaf,
    padding: spacing.md
  },
  primaryButtonText: {
    color: colors.surface,
    textAlign: "center",
    fontSize: 16,
    lineHeight: 21,
    fontWeight: "800"
  }
});
