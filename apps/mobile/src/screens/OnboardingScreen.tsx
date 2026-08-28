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
type ExperienceLevel = NonNullable<OnboardingRequest["experienceLevel"]>;
type Equipment = NonNullable<OnboardingRequest["availableEquipment"]>[number];

interface OnboardingScreenProps {
  readonly status: RequestStatus;
  readonly error?: FlowError;
  readonly target?: NutritionTarget;
  readonly warnings: readonly string[];
  readonly onSubmit: (input: OnboardingRequest) => void;
  readonly onContinue: () => void;
}

export function OnboardingScreen({ status, error, target, warnings, onSubmit, onContinue }: OnboardingScreenProps) {
  const [age, setAge] = useState("");
  const [heightCm, setHeightCm] = useState("");
  const [currentWeightKg, setCurrentWeightKg] = useState("");
  const [targetWeightKg, setTargetWeightKg] = useState("");
  const [sex, setSex] = useState<Sex>();
  const [goalType, setGoalType] = useState<GoalType>();
  const [activityLevel, setActivityLevel] = useState<ActivityLevel>();
  const [trainingFrequency, setTrainingFrequency] = useState<TrainingFrequency>();
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>();
  const [availableEquipment, setAvailableEquipment] = useState<Equipment[]>([]);
  const [sessionMinutes, setSessionMinutes] = useState("");

  const isLoading = status === "loading";
  const parsed = parseOnboardingInput({
    age,
    heightCm,
    currentWeightKg,
    targetWeightKg,
    sex,
    goalType,
    activityLevel,
    trainingFrequency,
    experienceLevel,
    availableEquipment,
    sessionMinutes
  });
  const rangeWarning = numericRangeWarning({ age, heightCm, currentWeightKg, targetWeightKg, sessionMinutes });

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.heroCopy}>
          <Text style={styles.eyebrow}>초기 목표 설정</Text>
          <Text style={styles.title}>사진 한 장으로 식단 기록을 시작해요</Text>
          <Text style={styles.subtitle}>필요한 정보만 짧게 받고, 나중에 체중 변화와 기록이 쌓이면 목표를 다시 조정해요.</Text>
        </View>
        <TrustBuddy size={112} pose="meal" />
      </View>

      {rangeWarning ? <Text style={styles.validationText} accessibilityRole="alert">{rangeWarning}</Text> : null}

      <View style={styles.formCard}>
        <View style={styles.inputRow}>
          <NumberField label="나이" value={age} onChangeText={setAge} suffix="세" placeholder="예: 29" />
          <NumberField label="키" value={heightCm} onChangeText={setHeightCm} suffix="cm" placeholder="예: 172" />
        </View>
        <View style={styles.inputRow}>
          <NumberField label="현재 체중" value={currentWeightKg} onChangeText={setCurrentWeightKg} suffix="kg" placeholder="예: 72" />
          <NumberField label="목표 체중 (선택)" value={targetWeightKg} onChangeText={setTargetWeightKg} suffix="kg" placeholder="예: 68" />
        </View>
        <ChipGroup label="성별" value={sex} options={sexOptions} onChange={setSex} />
        <ChipGroup label="목표" value={goalType} options={goalOptions} onChange={setGoalType} />
        <ChipGroup label="활동량" value={activityLevel} options={activityOptions} onChange={setActivityLevel} />
        <ChipGroup label="운동 빈도" value={trainingFrequency} options={trainingOptions} onChange={setTrainingFrequency} />
        <View style={styles.divider} />
        <View style={styles.sectionIntro}>
          <Text style={styles.sectionTitle}>운동 계획 개인화</Text>
          <Text style={styles.helperText}>경력과 환경에 맞는 종목 수, 난이도, 운동 시간을 정하는 데 사용해요.</Text>
        </View>
        <ChipGroup label="운동 경력" value={experienceLevel} options={experienceOptions} onChange={setExperienceLevel} />
        <MultiChipGroup
          label="사용 가능한 장비"
          values={availableEquipment}
          options={equipmentOptions}
          onToggle={(equipment) => {
            setAvailableEquipment((current) => current.includes(equipment) ? current.filter((item) => item !== equipment) : [...current, equipment]);
          }}
        />
        <NumberField label="한 번에 운동할 시간" value={sessionMinutes} onChangeText={setSessionMinutes} suffix="분" placeholder="예: 60" />
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
        accessibilityLabel={target ? "입력한 정보로 목표 다시 계산하기" : "입력한 정보로 목표 계산하기"}
        accessibilityHint={!parsed ? "필수 정보를 모두 입력하면 활성화됩니다" : undefined}
        accessibilityState={{ disabled: isLoading || !parsed, busy: isLoading }}
      >
        <Text style={styles.primaryButtonText}>{isLoading ? "계산 중" : target ? "다시 계산" : "목표 계산하기"}</Text>
      </TouchableOpacity>

      <TouchableOpacity activeOpacity={0.82} style={[styles.secondaryButton, !target && styles.buttonDisabled]} disabled={!target} onPress={onContinue} accessibilityRole="button" accessibilityLabel="계산된 목표로 시작하기" accessibilityState={{ disabled: !target }}>
        <Text style={styles.secondaryButtonText}>이 목표로 시작하기</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function NumberField({ label, value, suffix, placeholder, onChangeText }: { readonly label: string; readonly value: string; readonly suffix: string; readonly placeholder: string; readonly onChangeText: (value: string) => void }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.inputWrap}>
        <TextInput value={value} onChangeText={onChangeText} placeholder={placeholder} placeholderTextColor={colors.muted} keyboardType="decimal-pad" style={styles.input} accessibilityLabel={`${label}, ${suffix} 단위`} />
        <Text style={styles.inputSuffix}>{suffix}</Text>
      </View>
    </View>
  );
}

function ChipGroup<T extends string>({ label, value, options, onChange }: { readonly label: string; readonly value?: T; readonly options: readonly { readonly label: string; readonly value: T }[]; readonly onChange: (value: T) => void }) {
  return (
    <View style={styles.chipSection}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.chipRow}>
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <TouchableOpacity key={option.value} activeOpacity={0.82} style={[styles.chip, selected && styles.chipSelected]} onPress={() => onChange(option.value)} accessibilityRole="radio" accessibilityLabel={`${label}, ${option.label}`} accessibilityState={{ selected }}>
              <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{option.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

function MultiChipGroup<T extends string>({ label, values, options, onToggle }: { readonly label: string; readonly values: readonly T[]; readonly options: readonly { readonly label: string; readonly value: T }[]; readonly onToggle: (value: T) => void }) {
  return (
    <View style={styles.chipSection}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.chipRow}>
        {options.map((option) => {
          const selected = values.includes(option.value);
          return (
            <TouchableOpacity key={option.value} activeOpacity={0.82} style={[styles.chip, selected && styles.chipSelected]} onPress={() => onToggle(option.value)} accessibilityRole="checkbox" accessibilityLabel={`${label}, ${option.label}`} accessibilityState={{ checked: selected }}>
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
  readonly sex?: Sex;
  readonly goalType?: GoalType;
  readonly activityLevel?: ActivityLevel;
  readonly trainingFrequency?: TrainingFrequency;
  readonly experienceLevel?: ExperienceLevel;
  readonly availableEquipment: readonly Equipment[];
  readonly sessionMinutes: string;
}): OnboardingRequest | undefined {
  const age = Number(input.age);
  const heightCm = Number(input.heightCm);
  const currentWeightKg = Number(input.currentWeightKg);
  const targetWeightKg = input.targetWeightKg.trim() ? Number(input.targetWeightKg) : undefined;
  const sessionMinutes = Number(input.sessionMinutes);
  if (!input.age.trim() || !input.heightCm.trim() || !input.currentWeightKg.trim() || !input.sessionMinutes.trim()) {
    return undefined;
  }
  if (!input.sex || !input.goalType || !input.activityLevel || !input.trainingFrequency || !input.experienceLevel || input.availableEquipment.length === 0) {
    return undefined;
  }
  if (!Number.isInteger(age) || age < 14 || age > 100 || !Number.isFinite(heightCm) || heightCm < 100 || heightCm > 230 || !Number.isFinite(currentWeightKg) || currentWeightKg < 30 || currentWeightKg > 250 || !Number.isInteger(sessionMinutes) || sessionMinutes < 20 || sessionMinutes > 120) {
    return undefined;
  }
  if (targetWeightKg !== undefined && (!Number.isFinite(targetWeightKg) || targetWeightKg < 30 || targetWeightKg > 250)) {
    return undefined;
  }
  return {
    age,
    heightCm,
    currentWeightKg,
    targetWeightKg,
    sex: input.sex,
    goalType: input.goalType,
    activityLevel: input.activityLevel,
    trainingFrequency: input.trainingFrequency,
    experienceLevel: input.experienceLevel,
    availableEquipment: [...input.availableEquipment],
    sessionMinutes
  };
}

function numericRangeWarning(input: { readonly age: string; readonly heightCm: string; readonly currentWeightKg: string; readonly targetWeightKg: string; readonly sessionMinutes: string }): string | undefined {
  const checks = [
    { value: input.age, valid: (number: number) => Number.isInteger(number) && number >= 14 && number <= 100, message: "나이는 14~100세 사이의 정수로 입력해 주세요." },
    { value: input.heightCm, valid: (number: number) => number >= 100 && number <= 230, message: "키는 100~230cm 사이로 입력해 주세요." },
    { value: input.currentWeightKg, valid: (number: number) => number >= 30 && number <= 250, message: "현재 체중은 30~250kg 사이로 입력해 주세요." },
    { value: input.targetWeightKg, valid: (number: number) => number >= 30 && number <= 250, message: "목표 체중은 30~250kg 사이로 입력해 주세요." },
    { value: input.sessionMinutes, valid: (number: number) => Number.isInteger(number) && number >= 20 && number <= 120, message: "운동 시간은 20~120분 사이의 정수로 입력해 주세요." }
  ];
  return checks.find(({ value, valid }) => value.trim() && (!Number.isFinite(Number(value)) || !valid(Number(value))))?.message;
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
  { label: "거의 없음", value: "sedentary" },
  { label: "낮음", value: "light" },
  { label: "보통", value: "moderate" },
  { label: "높음", value: "high" },
  { label: "선수급", value: "athlete" }
] as const;

const experienceOptions = [
  { label: "입문", value: "beginner" },
  { label: "중급", value: "intermediate" },
  { label: "숙련", value: "advanced" }
] as const;

const equipmentOptions = [
  { label: "맨몸", value: "bodyweight" },
  { label: "덤벨", value: "dumbbells" },
  { label: "헬스장", value: "gym" }
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
  divider: { height: 1, backgroundColor: colors.hairline },
  sectionIntro: { gap: spacing.xs },
  inputRow: { flexDirection: "row", gap: spacing.md },
  field: { flex: 1, gap: spacing.xs, minWidth: 0 },
  fieldLabel: { color: colors.muted, ...typography.caption },
  helperText: { color: colors.body, ...typography.body },
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
  validationText: { color: colors.warningText, ...typography.caption },
  primaryButton: { alignItems: "center", justifyContent: "center", minHeight: 58, borderRadius: radii.control, backgroundColor: colors.leaf, padding: spacing.md, ...shadows.card },
  secondaryButton: { alignItems: "center", justifyContent: "center", minHeight: 58, borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.md },
  buttonDisabled: { opacity: 0.48 },
  primaryButtonText: { color: colors.surface, fontSize: 16, lineHeight: 21, fontWeight: "800" },
  secondaryButtonText: { color: colors.ink, fontSize: 16, lineHeight: 21, fontWeight: "800" }
});
