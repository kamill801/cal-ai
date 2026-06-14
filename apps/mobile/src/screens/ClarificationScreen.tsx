import type { AnalysisResult, RangeNarrowingResult } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { CalorieRange } from "../components/CalorieRange";
import { ClarificationSheet } from "../components/ClarificationSheet";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { MealPhotoFrame } from "../components/MealPhotoFrame";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { scanPhotoSource } from "../mockData";
import { colors, spacing, typography } from "../theme";

export function ClarificationScreen({
  analysis,
  narrowing,
  selectedValue,
  status,
  error,
  onSelect,
  onSkip,
  onRetry
}: {
  analysis: AnalysisResult;
  narrowing?: RangeNarrowingResult;
  selectedValue?: string;
  status: RequestStatus;
  error?: FlowError;
  onSelect: (value: string) => void;
  onSkip: () => void;
  onRetry: () => void;
}) {
  if (!analysis.clarificationQuestion) {
    return null;
  }

  const isLoading = status === "loading";

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>원탭 보정</Text>
        <Text style={styles.title}>{isLoading ? "답변을 반영하고 있어요" : "이 질문 하나만 확인해요"}</Text>
      </View>
      <MealPhotoFrame source={scanPhotoSource} stageText={isLoading ? "범위 다시 계산 중" : "밥 양 확인 대기"} confidenceLabel={analysis.summary.confidenceLabel} confidenceGroup={analysis.summary.confidenceGroup} />
      <CalorieRange range={analysis.summary.calorieRange} compact />
      {isLoading ? <FlowStatusCard title="범위 조정 중" message="선택한 답변을 반영해 칼로리 범위를 다시 좁히고 있어요." /> : null}
      {error ? <FlowStatusCard error={error} onRetry={onRetry} /> : null}
      <ClarificationSheet question={analysis.clarificationQuestion} narrowing={narrowing} selectedValue={selectedValue} disabled={isLoading} onSelect={onSelect} onSkip={onSkip} />
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
