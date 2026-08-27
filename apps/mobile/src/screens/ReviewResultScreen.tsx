import type { AnalysisResult, MealNutritionOverride, RangeNarrowingResult } from "@cal-ai/shared";
import { useEffect, useState } from "react";
import type { ImageSourcePropType } from "react-native";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
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
  onApplyManualAdjustment,
  onRetry
}: {
  analysis: AnalysisResult;
  photoSource?: ImageSourcePropType;
  narrowing?: RangeNarrowingResult;
  status: RequestStatus;
  error?: FlowError;
  onSave: () => void;
  onEdit: () => void;
  onApplyManualAdjustment: (override: MealNutritionOverride) => void;
  onRetry: () => void;
}) {
  const isSaving = status === "loading";
  const [showEvidence, setShowEvidence] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [mealName, setMealName] = useState(analysis.mealName);
  const [calories, setCalories] = useState(String(analysis.summary.caloriesKcal));
  const [protein, setProtein] = useState(String(analysis.summary.proteinG));
  const [carbs, setCarbs] = useState(String(analysis.summary.carbsG));
  const [fat, setFat] = useState(String(analysis.summary.fatG));

  useEffect(() => {
    setMealName(analysis.mealName);
    setCalories(String(analysis.summary.caloriesKcal));
    setProtein(String(analysis.summary.proteinG));
    setCarbs(String(analysis.summary.carbsG));
    setFat(String(analysis.summary.fatG));
  }, [analysis]);

  const parsed = {
    caloriesKcal: Number(calories),
    proteinG: Number(protein),
    carbsG: Number(carbs),
    fatG: Number(fat)
  };
  const canApply = mealName.trim().length > 0
    && Number.isInteger(parsed.caloriesKcal) && parsed.caloriesKcal > 0 && parsed.caloriesKcal <= 5000
    && [parsed.proteinG, parsed.carbsG, parsed.fatG].every((value) => Number.isInteger(value) && value >= 0 && value <= 500);

  function applyManualAdjustment(): void {
    if (!canApply) {
      return;
    }
    onApplyManualAdjustment({ mealName: mealName.trim(), ...parsed });
    setShowEditor(false);
  }

  return (
    <View style={styles.screen}>
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

      {isSaving ? <FlowStatusCard title="저장 중" message="식사 기록과 오늘 대시보드를 업데이트하고 있어요." /> : null}
      {error ? <FlowStatusCard error={error} onRetry={onRetry} /> : null}

      <View style={styles.foodCard}>
        <View style={styles.foodHeader}>
          <Text style={styles.sectionTitle}>사진상 확인한 음식</Text>
          <TouchableOpacity
            onPress={() => setShowEvidence((visible) => !visible)}
            accessibilityRole="button"
            accessibilityState={{ expanded: showEvidence }}
          >
            <Text style={styles.foodHeaderMeta}>{showEvidence ? "근거 접기" : "분석 근거 보기"}</Text>
          </TouchableOpacity>
        </View>
        {analysis.detectedFoods.map((food) => (
          <View key={food.id} style={styles.foodRow}>
            <Text style={styles.foodName}>{food.name}</Text>
            <Text style={styles.foodAssumption}>{food.assumptionLabel}</Text>
          </View>
        ))}
        {showEvidence ? (
          <View style={styles.evidencePanel}>
            <Text style={styles.evidenceTitle}>추정에 영향을 준 점</Text>
            {analysis.uncertaintyReasons.length ? analysis.uncertaintyReasons.map((reason) => (
              <Text key={reason} style={styles.evidenceText}>· {reason}</Text>
            )) : <Text style={styles.evidenceText}>사진에서 주요 음식과 양이 비교적 선명하게 보였어요.</Text>}
            <Text style={styles.evidenceNote}>사진 분석은 추정치예요. 소스, 기름, 실제 먹은 양이 다르면 아래에서 직접 고쳐주세요.</Text>
          </View>
        ) : null}
      </View>

      {showEditor ? (
        <View style={styles.editorCard}>
          <View style={styles.editorHeader}>
            <View style={styles.editorHeaderCopy}>
              <Text style={styles.sectionTitle}>직접 확인한 값으로 수정</Text>
              <Text style={styles.editorHelp}>음식 이름이나 영양값이 다르면 저장 전에 고칠 수 있어요.</Text>
            </View>
            <TrustBuddy size={48} accessory="sprout" />
          </View>
          <TextInput
            style={styles.nameInput}
            value={mealName}
            onChangeText={setMealName}
            placeholder="식사 이름"
            placeholderTextColor={colors.muted}
            accessibilityLabel="식사 이름"
          />
          <View style={styles.nutritionInputs}>
            <NutritionInput label="칼로리" unit="kcal" value={calories} onChangeText={setCalories} />
            <NutritionInput label="단백질" unit="g" value={protein} onChangeText={setProtein} />
            <NutritionInput label="탄수화물" unit="g" value={carbs} onChangeText={setCarbs} />
            <NutritionInput label="지방" unit="g" value={fat} onChangeText={setFat} />
          </View>
          {!canApply ? <Text style={styles.validationText}>칼로리는 1~5000, 영양소는 0~500 사이의 정수로 입력해 주세요.</Text> : null}
          <View style={styles.editorActions}>
            {analysis.clarificationQuestion ? (
              <TouchableOpacity style={styles.textButton} onPress={onEdit} accessibilityRole="button">
                <Text style={styles.textButtonText}>양 다시 확인</Text>
              </TouchableOpacity>
            ) : null}
            <TouchableOpacity
              style={[styles.applyButton, !canApply && styles.buttonDisabled]}
              disabled={!canApply}
              onPress={applyManualAdjustment}
              accessibilityRole="button"
              accessibilityState={{ disabled: !canApply }}
            >
              <Text style={styles.applyButtonText}>수정값 반영</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : null}

    </ScrollView>
      <View style={styles.stickyActions}>
        <TouchableOpacity activeOpacity={0.82} style={[styles.secondaryButton, isSaving && styles.buttonDisabled]} disabled={isSaving} onPress={() => setShowEditor((visible) => !visible)} accessibilityRole="button" accessibilityState={{ disabled: isSaving, expanded: showEditor }}>
          <Text style={styles.secondaryButtonText}>{showEditor ? "수정 닫기" : "수정"}</Text>
        </TouchableOpacity>
        <TouchableOpacity activeOpacity={0.86} style={[styles.primaryButton, isSaving && styles.buttonDisabled]} disabled={isSaving} onPress={onSave} accessibilityRole="button" accessibilityState={{ disabled: isSaving, busy: isSaving }}>
          <Text style={styles.primaryButtonText}>{isSaving ? "저장 중" : "식사로 기록"}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function NutritionInput({ label, unit, value, onChangeText }: { readonly label: string; readonly unit: string; readonly value: string; readonly onChangeText: (value: string) => void }) {
  return (
    <View style={styles.nutritionInputGroup}>
      <Text style={styles.inputLabel}>{label}</Text>
      <View style={styles.numberInputShell}>
        <TextInput
          style={styles.numberInput}
          value={value}
          onChangeText={onChangeText}
          keyboardType="number-pad"
          accessibilityLabel={`${label} ${unit}`}
        />
        <Text style={styles.inputUnit}>{unit}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.canvasWarm
  },
  container: {
    gap: spacing.md,
    padding: spacing.lg,
    paddingBottom: 112
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
    color: colors.leaf,
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
  evidencePanel: { gap: spacing.xs, borderTopColor: colors.hairline, borderTopWidth: 1, paddingTop: spacing.md },
  evidenceTitle: { color: colors.ink, ...typography.bodyStrong },
  evidenceText: { color: colors.body, ...typography.body },
  evidenceNote: { color: colors.muted, marginTop: spacing.xs, ...typography.caption },
  editorCard: { gap: spacing.md, borderColor: colors.leafMuted, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.lg, ...shadows.card },
  editorHeader: { alignItems: "center", flexDirection: "row", gap: spacing.sm },
  editorHeaderCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  editorHelp: { color: colors.body, ...typography.body },
  nameInput: { minHeight: 52, borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, color: colors.ink, backgroundColor: colors.canvas, paddingHorizontal: spacing.md, ...typography.bodyStrong },
  nutritionInputs: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  nutritionInputGroup: { width: "48%", gap: spacing.xs },
  inputLabel: { color: colors.muted, ...typography.caption },
  numberInputShell: { minHeight: 48, alignItems: "center", flexDirection: "row", borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.canvas, paddingHorizontal: spacing.sm },
  numberInput: { flex: 1, color: colors.ink, paddingVertical: spacing.sm, ...typography.bodyStrong },
  inputUnit: { color: colors.muted, ...typography.caption },
  validationText: { color: colors.warningText, ...typography.caption },
  editorActions: { alignItems: "center", flexDirection: "row", justifyContent: "flex-end", gap: spacing.sm },
  textButton: { minHeight: 44, justifyContent: "center", paddingHorizontal: spacing.sm },
  textButtonText: { color: colors.leaf, ...typography.bodyStrong },
  applyButton: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.leaf, paddingHorizontal: spacing.lg },
  applyButtonText: { color: colors.surface, ...typography.bodyStrong },
  stickyActions: {
    flexDirection: "row",
    gap: spacing.sm,
    borderTopColor: colors.hairline,
    borderTopWidth: 1,
    backgroundColor: colors.canvasWarm,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md
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
