import type { AnalysisResult, RangeNarrowingResult } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { CalorieRange } from "../components/CalorieRange";
import { ClarificationSheet } from "../components/ClarificationSheet";
import { MealPhotoFrame } from "../components/MealPhotoFrame";
import { scanPhotoSource } from "../mockData";
import { colors, spacing, typography } from "../theme";

export function ClarificationScreen({
  analysis,
  narrowing,
  selectedValue,
  onSelect,
  onSkip
}: {
  analysis: AnalysisResult;
  narrowing?: RangeNarrowingResult;
  selectedValue?: string;
  onSelect: (value: string) => void;
  onSkip: () => void;
}) {
  if (!analysis.clarificationQuestion) {
    return null;
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>원탭 보정</Text>
        <Text style={styles.title}>이 질문 하나만 확인해요</Text>
      </View>
      <MealPhotoFrame source={scanPhotoSource} stageText="밥 양 확인 대기" confidenceLabel={analysis.summary.confidenceLabel} confidenceGroup={analysis.summary.confidenceGroup} />
      <CalorieRange range={analysis.summary.calorieRange} compact />
      <ClarificationSheet question={analysis.clarificationQuestion} narrowing={narrowing} selectedValue={selectedValue} onSelect={onSelect} onSkip={onSkip} />
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
  }
});
