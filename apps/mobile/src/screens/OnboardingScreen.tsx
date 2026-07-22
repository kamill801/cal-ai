import type { ActivityLevel, GoalType, NutritionTarget, OnboardingRequest } from "@cal-ai/shared";
import { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { MacroSummary } from "../components/MacroSummary";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, shadows, spacing, typography } from "../theme";

type Sex = OnboardingRequest["sex"];
type TrainingFrequency = NonNullable<OnboardingRequest["trainingFrequency"]>;

interface OnboardingScreenProps {
  readonly status: RequestStatus;
  readonly error?: FlowError;
  readonly target?: NutritionTarget;
  readonly warnings: readonly string[];
  readonly onSubmit: (input: OnboardingRequest) => void;
  readonly onContinue: () => void;
}

export function OnboardingScreen({ status, error, target, warnings, onSubmit, onContinue }: OnboardingScreenProps) {
  const [age, setAge] = useState("29");
  const [heightCm, setHeightCm] = useState("172");
  const [currentWeightKg, setCurrentWeightKg] = useState("72");
  const [targetWeightKg, setTargetWeightKg] = useState("68");
  const [sex, setSex] = useState<Sex>("male");
  const [goalType, setGoalType] = useState<GoalType>("lose");
  const [activityLevel, setActivityLevel] = useState<ActivityLevel>("moderate");
  const [trainingFrequency, setTrainingFrequency] = useState<TrainingFrequency>("3-4");

  const isLoading = status === "loading";
  const parsed = parseOnboardingInput({ age, heightCm, currentWeightKg, targetWeightKg, sex, goalType, activityLevel, trainingFrequency });

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.heroCopy}>
          <Text style={styles.eyebrow}>초기 목표 설정</Text>
          <Text style={styles.title}>사진 한 장으로 식단 기록을 시작해요</Text>
          <Text style={styles.subtitle}>필요한 정보만 짧게 받고, 나중에 체중 변화와 기록이 쌓이면 목표를 다시 조정해요.</Text>
        </View>
        <TrustBuddy size={88} accessory="spoon" />
      </View>

      <View style={styles.formCard}>
        <View style={styles.inputRow}>
          <NumberField label="나이" value={age} onChangeText={setAge} suffix="세" />
          <NumberField label="키" value={heightCm} onChangeText={setHeightCm} suffix="cm" />
        </View>
        <View style={styles.inputRow}>
          <NumberField label="현재 체중" value={currentWeightKg} onChangeText={setCurrentWeightKg} suffix="kg" />
          <NumberField label="목표 체중" value={targetWeightKg} onChangeText={setTargetWeightKg} suffix="kg" />
        </View>
        <ChipGroup label="성별" value={sex} options={sexOptions} onChange={setSex} />
        <ChipGroup label="목표" value={goalType} options={goalOptions} onChange={setGoalType} />
        <ChipGroup label="활동량" value={activityLevel} options={activityOptions} onChange={setActivityLevel} />
        <ChipGroup label="운동 빈도" value={trainingFrequency} options={trainingOptions} onChange={setTrainingFrequency} />
      </View>

      {error ? <FlowStatusCard error={error} /> : null}
      {target ? (
        <View style={styles.resultCard}>
          <Text style={styles.sectionTitle}>초기 목표</Text>
          <View style={styles.targetRow}>
            <Text style={styles.targetNumber}>{target.caloriesKcal.toLocaleString()}</Text>
            <Text style={styles.targetUnit}>kcal</Text>
          </View>
          <MacroSummary macros={target} />
          {warnings.map((warning) => (
            <Text key={warning} style={styles.warningText}>{warning}</Text>
          ))}
        </View>
      ) : null}

      <TouchableOpacity
        activeOpacity={0.86}
        style={[styles.primaryButton, (isLoading || !parsed) && styles.buttonDisabled]}
        disabled={isLoading || !parsed}
        onPress={() => {
          if (parsed) {
            onSubmit(parsed);
          }
        }}
        accessibilityRole="button"
        accessibilityState={{ disabled: isLoading || !parsed, busy: isLoading }}
      >
        <Text style={styles.primaryButtonText}>{isLoading ? "계산 중" : target ? "다시 계산" : "목표 계산하기"}</Text>
      </TouchableOpacity>

      <TouchableOpacity activeOpacity={0.82} style={[styles.secondaryButton, !target && styles.buttonDisabled]} disabled={!target} onPress={onContinue} accessibilityRole="button" accessibilityState={{ disabled: !target }}>
        <Text style={styles.secondaryButtonText}>이 목표로 시작하기</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function NumberField({ label, value, suffix, onChangeText }: { readonly label: string; readonly value: string; readonly suffix: string; readonly onChangeText: (value: string) => void }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.inputWrap}>
        <TextInput value={value} onChangeText={onChangeText} keyboardType="decimal-pad" style={styles.input} accessibilityLabel={label} />
        <Text style={styles.inputSuffix}>{suffix}</Text>
      </View>
    </View>
  );
}

function ChipGroup<T extends string>({ label, value, options, onChange }: { readonly label: string; readonly value: T; readonly options: readonly { readonly label: string; readonly value: T }[]; readonly onChange: (value: T) => void }) {
  return (
    <View style={styles.chipSection}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.chipRow}>
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <TouchableOpacity key={option.value} activeOpacity={0.82} style={[styles.chip, selected && styles.chipSelected]} onPress={() => onChange(option.value)} accessibilityRole="button" accessibilityState={{ selected }}>
              <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{option.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

function parseOnboardingInput(input: {
  readonly age: string;
  readonly heightCm: string;
  readonly currentWeightKg: string;
  readonly targetWeightKg: string;
  readonly sex: Sex;
  readonly goalType: GoalType;
  readonly activityLevel: ActivityLevel;
  readonly trainingFrequency: TrainingFrequency;
}): OnboardingRequest | undefined {
  const age = Number(input.age);
  const heightCm = Number(input.heightCm);
  const currentWeightKg = Number(input.currentWeightKg);
  const targetWeightKg = input.targetWeightKg.trim() ? Number(input.targetWeightKg) : undefined;
  if (!Number.isFinite(age) || !Number.isFinite(heightCm) || !Number.isFinite(currentWeightKg)) {
    return undefined;
  }
  if (targetWeightKg !== undefined && !Number.isFinite(targetWeightKg)) {
    return undefined;
  }
  return { age, heightCm, currentWeightKg, targetWeightKg, sex: input.sex, goalType: input.goalType, activityLevel: input.activityLevel, trainingFrequency: input.trainingFrequency };
}

const sexOptions = [
  { label: "남성", value: "male" },
  { label: "여성", value: "female" },
  { label: "기타", value: "other" }
] as const;

const goalOptions = [
  { label: "감량", value: "lose" },
  { label: "유지", value: "maintain" },
  { label: "증량", value: "gain" },
  { label: "리컴프", value: "recomp" }
] as const;

const activityOptions = [
  { label: "낮음", value: "light" },
  { label: "보통", value: "moderate" },
  { label: "높음", value: "high" },
  { label: "선수급", value: "athlete" }
] as const;

const trainingOptions = [
  { label: "없음", value: "none" },
  { label: "주 1-2회", value: "1-2" },
  { label: "주 3-4회", value: "3-4" },
  { label: "주 5회+", value: "5+" }
] as const;

const styles = StyleSheet.create({
  container: { gap: spacing.lg, padding: spacing.lg, paddingBottom: spacing.xxl },
  header: { alignItems: "center", flexDirection: "row", gap: spacing.md, paddingTop: spacing.sm },
  heroCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.screenTitle },
  subtitle: { color: colors.body, ...typography.body },
  formCard: { gap: spacing.lg, borderColor: colors.hairline, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.lg, ...shadows.card },
  inputRow: { flexDirection: "row", gap: spacing.md },
  field: { flex: 1, gap: spacing.xs, minWidth: 0 },
  fieldLabel: { color: colors.muted, ...typography.caption },
  inputWrap: { alignItems: "center", flexDirection: "row", borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.surface, paddingHorizontal: spacing.md },
  input: { flex: 1, minHeight: 44, color: colors.ink, fontSize: 16, fontWeight: "700" },
  inputSuffix: { color: colors.muted, ...typography.caption },
  chipSection: { gap: spacing.sm },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  chip: { borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.surface, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  chipSelected: { borderColor: colors.leaf, backgroundColor: colors.leafTint },
  chipText: { color: colors.body, ...typography.caption },
  chipTextSelected: { color: colors.leaf },
  resultCard: { gap: spacing.md, borderColor: colors.leafMuted, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.leafTint, padding: spacing.lg, ...shadows.card },
  sectionTitle: { color: colors.ink, ...typography.sectionTitle },
  targetRow: { alignItems: "baseline", flexDirection: "row", gap: spacing.sm },
  targetNumber: { color: colors.ink, fontVariant: ["tabular-nums"], ...typography.displayNumber },
  targetUnit: { color: colors.muted, ...typography.bodyStrong },
  warningText: { color: colors.warningText, ...typography.body },
  primaryButton: { alignItems: "center", justifyContent: "center", minHeight: 58, borderRadius: radii.control, backgroundColor: colors.leaf, padding: spacing.md, ...shadows.card },
  secondaryButton: { alignItems: "center", justifyContent: "center", minHeight: 58, borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.md },
  buttonDisabled: { opacity: 0.48 },
  primaryButtonText: { color: colors.surface, fontSize: 16, lineHeight: 21, fontWeight: "800" },
  secondaryButtonText: { color: colors.ink, fontSize: 16, lineHeight: 21, fontWeight: "800" }
});
