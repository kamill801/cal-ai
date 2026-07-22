import type { AnalysisResult } from "@cal-ai/shared";
import { ArrowLeft } from "lucide-react-native";
import type { ImageSourcePropType } from "react-native";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CalorieRange } from "../components/CalorieRange";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { MealPhotoFrame } from "../components/MealPhotoFrame";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { scanPhotoSource } from "../mockData";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function AnalyzeEvidenceScreen({
  analysis,
  photoSource,
  status,
  error,
  onClarify,
  onRetry,
  onCancel
}: {
  analysis?: AnalysisResult;
  photoSource?: ImageSourcePropType;
  status: RequestStatus;
  error?: FlowError;
  onClarify: () => void;
  onRetry: () => void;
  onCancel: () => void;
}) {
  const isLoading = status === "loading";
  const canClarify = Boolean(analysis?.clarificationQuestion) && !isLoading && !error;
  const canReview = Boolean(analysis) && !analysis?.clarificationQuestion && !isLoading && !error;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <TouchableOpacity style={styles.backButton} onPress={onCancel} accessibilityRole="button" accessibilityLabel="분석 닫기">
            <ArrowLeft color={colors.ink} size={22} strokeWidth={2.4} />
          </TouchableOpacity>
          <Text style={styles.eyebrow}>식사 사진 촬영</Text>
        </View>
        <Text style={styles.title}>{isLoading ? "사진을 분석하고 있어요" : "사진 한 장으로 간편 기록"}</Text>
        <Text style={styles.subtitle}>밝은 곳에서 음식이 잘 보이게 찍으면 범위가 더 좋아져요.</Text>
      </View>

      {analysis ? (
        <MealPhotoFrame
          source={photoSource ?? scanPhotoSource}
          stageText={analysis.stageText}
          confidenceLabel={analysis.summary.confidenceLabel}
          confidenceGroup={analysis.summary.confidenceGroup}
        />
      ) : photoSource ? (
        <MealPhotoFrame source={photoSource} stageText={isLoading ? "사진 업로드 중" : "식사 사진 준비 완료"} />
      ) : (
        <View style={styles.photoPlaceholder}>
          <View style={[styles.scanCorner, styles.scanCornerTopLeft]} />
          <View style={[styles.scanCorner, styles.scanCornerTopRight]} />
          <View style={[styles.scanCorner, styles.scanCornerBottomLeft]} />
          <View style={[styles.scanCorner, styles.scanCornerBottomRight]} />
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
  headerTop: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
    borderColor: colors.hairline,
    borderRadius: radii.pill,
    borderWidth: 1,
    backgroundColor: colors.surface
  },
  eyebrow: {
    color: colors.leaf,
    ...typography.caption
  },
  title: {
    color: colors.ink,
    ...typography.screenTitle
  },
  subtitle: {
    color: colors.body,
    ...typography.body
  },
  photoPlaceholder: {
    position: "relative",
    gap: spacing.sm,
    minHeight: 300,
    justifyContent: "center",
    borderColor: "#4b4b4b",
    borderRadius: radii.photo,
    borderWidth: 1,
    backgroundColor: "#252525",
    padding: spacing.lg,
    ...shadows.floating
  },
  placeholderTitle: {
    color: colors.surface,
    ...typography.sectionTitle
  },
  placeholderBody: {
    color: "rgba(255, 255, 255, 0.72)",
    ...typography.body
  },
  scanCorner: {
    position: "absolute",
    width: 44,
    height: 44,
    borderColor: colors.surface
  },
  scanCornerTopLeft: {
    top: spacing.lg,
    left: spacing.lg,
    borderTopWidth: 5,
    borderLeftWidth: 5,
    borderTopLeftRadius: radii.control
  },
  scanCornerTopRight: {
    top: spacing.lg,
    right: spacing.lg,
    borderTopWidth: 5,
    borderRightWidth: 5,
    borderTopRightRadius: radii.control
  },
  scanCornerBottomLeft: {
    bottom: spacing.lg,
    left: spacing.lg,
    borderBottomWidth: 5,
    borderLeftWidth: 5,
    borderBottomLeftRadius: radii.control
  },
  scanCornerBottomRight: {
    right: spacing.lg,
    bottom: spacing.lg,
    borderRightWidth: 5,
    borderBottomWidth: 5,
    borderBottomRightRadius: radii.control
  },
  panel: {
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg,
    ...shadows.card
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
    minHeight: 58,
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
