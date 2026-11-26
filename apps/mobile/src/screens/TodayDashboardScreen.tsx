import type { CoachDashboard, DashboardMeal, DashboardTodayResponse, MealType } from "@cal-ai/shared";
import { Camera, ChevronDown, ChevronRight, CreditCard, ImageIcon, Info, RotateCcw, ShieldCheck, Soup, Trash2 } from "lucide-react-native";
import { useState, type ReactNode } from "react";
import { ScrollView, Text, TouchableOpacity, View } from "react-native";
import { confidenceLabelText } from "../components/ConfidencePill";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { todayDashboard as initialDashboard } from "../mockData";
import { freshGreen } from "../theme";
import { homeColors, styles } from "./TodayDashboardScreen.styles";

const mealTypeLabels: Record<MealType, string> = { breakfast: "아침", lunch: "점심", dinner: "저녁", snack: "간식" };
const macroFields = [
  { key: "proteinG", label: "단백질", color: freshGreen.indicator },
  { key: "carbsG", label: "탄수화물", color: homeColors.carb },
  { key: "fatG", label: "지방", color: homeColors.fat }
] as const;

const dayFormatter = new Intl.DateTimeFormat("ko-KR", { month: "long", day: "numeric", weekday: "long", timeZone: "UTC" });
const numberFormatter = new Intl.NumberFormat("ko-KR");

export function TodayDashboardScreen({
  dashboard,
  coachDashboard,
  onCaptureMeal,
  onPickMeal,
  onOpenSafety,
  onOpenPlan,
  onRepeatMeal,
  onDeleteMeal,
  status,
  error
}: {
  readonly dashboard: DashboardTodayResponse;
  readonly coachDashboard?: CoachDashboard;
  readonly onCaptureMeal: () => void;
  readonly onPickMeal: () => void;
  readonly onOpenSafety: () => void;
  readonly onOpenPlan: () => void;
  readonly onRepeatMeal: (mealLogId: string) => void;
  readonly onDeleteMeal: (mealLogId: string, mealName: string) => void;
  readonly status: RequestStatus;
  readonly error?: FlowError;
}) {
  // The reducer can update the seed target before it has a real dashboard, but keeps the seed meals by reference.
  const savedDashboard = dashboard.meals === initialDashboard.meals ? undefined : dashboard;
  const snapshot = coachDashboard?.nutrition ?? savedDashboard;
  const date = formatDashboardDate(coachDashboard?.date ?? savedDashboard?.date);
  const consumed = snapshot?.consumed;
  const target = snapshot?.target;
  const remaining = coachDashboard?.nutrition.remaining.caloriesKcal ?? (target && consumed ? Math.max(0, target.caloriesKcal - consumed.caloriesKcal) : undefined);
  const proteinRemaining = coachDashboard?.nutrition.remaining.proteinG ?? (target && consumed ? Math.max(0, target.proteinG - consumed.proteinG) : undefined);
  const meals = coachDashboard?.meals ?? savedDashboard?.meals;
  const hasRecords = meals !== undefined && (meals.length > 0 || (consumed?.caloriesKcal ?? 0) > 0 || (consumed?.proteinG ?? 0) > 0);
  const nextActionTitle = coachDashboard?.nextAction.title ?? savedDashboard?.nextMealGuidance.explanation;
  const nextActionDetail = coachDashboard?.nextAction.detail ?? savedDashboard?.nextMealGuidance.menuTypeRecommendations.join(" · ");
  const nutritionGuidance = hasRecords
    ? coachDashboard?.nutrition.guidance ?? savedDashboard?.nextMealGuidance.explanation
    : "식사를 기록하면 섭취량과 남은 양을 계산해드려요.";

  return (
    <ScrollView style={styles.scroll} contentContainerStyle={styles.container}>
      <View style={styles.page}>
        <View style={styles.masthead}>
          <View style={styles.mastheadCopy}>
            {date ? <Text style={styles.date}>{date}</Text> : null}
            <Text style={styles.title} accessibilityRole="header">오늘</Text>
          </View>
          <TrustBuddy size={70} pose="meal" />
        </View>

        <View style={styles.summary}>
          <Text style={styles.metricTitle}>오늘 남은 칼로리</Text>
          <Text style={styles.kcal}>
            {formatNumber(remaining)} <Text style={styles.kcalUnit}>kcal</Text>
          </Text>
          <View style={styles.energyNote}>
            <Text style={styles.metricNote}>섭취 <Text style={styles.metricStrong}>{formatNumber(consumed?.caloriesKcal)}</Text> kcal</Text>
            <Text style={styles.metricNote}>목표 {formatNumber(target?.caloriesKcal)} kcal</Text>
          </View>
          <NutritionProgress label="오늘 칼로리 섭취 진행률" consumed={consumed?.caloriesKcal} target={target?.caloriesKcal} />
          <View style={styles.macros}>
            {macroFields.map(({ key, label, color }) => (
              <View key={key} style={styles.macro}>
                <Text style={[styles.macroLabel, key === "proteinG" && styles.proteinLabel]}>{label}</Text>
                <Text style={styles.macroValue}>
                  {formatNumber(consumed?.[key])}g <Text style={styles.macroGoal}>/ {formatNumber(target?.[key])}g</Text>
                </Text>
                <NutritionProgress label={`오늘 ${label} 섭취 진행률`} consumed={consumed?.[key]} target={target?.[key]} color={color} compact />
              </View>
            ))}
          </View>
        </View>

        <View style={styles.captureActions}>
          <TouchableOpacity style={styles.captureButton} activeOpacity={0.86} onPress={onCaptureMeal} accessibilityRole="button" accessibilityLabel="카메라로 음식 사진 찍기" accessibilityHint="촬영한 사진을 분석해 식사 기록을 시작합니다">
            <Camera color={freshGreen.onFill} size={18} />
            <Text style={styles.captureTitle}>음식 사진 찍기</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.albumButton} activeOpacity={0.75} onPress={onPickMeal} accessibilityRole="button" accessibilityLabel="사진첩에서 음식 사진 선택" accessibilityHint="이미 찍어둔 사진을 분석합니다">
            <ImageIcon color={homeColors.brand} size={18} />
          </TouchableOpacity>
        </View>

        {error ? <FlowStatusCard error={error} /> : null}

        <View style={styles.mealsSection}>
          <View style={styles.sectionHeading}>
            <Text style={styles.sectionTitle} accessibilityRole="header">오늘의 식사</Text>
            {meals ? <Text style={styles.mealMeta}>{formatNumber(meals.length)}건{meals.length > 1 ? " · 최신순" : ""}</Text> : null}
          </View>
          {meals?.map((meal) => (
            <MealRow key={meal.id} meal={meal} disabled={status === "loading"} onRepeat={onRepeatMeal} onDelete={onDeleteMeal} />
          ))}
          {!meals?.length ? (
            <View style={styles.emptyState}>
              <Text style={styles.mealName} accessibilityLiveRegion="polite">
                {meals ? "아직 기록한 식사가 없어요" : status === "loading" ? "식사 기록을 불러오고 있어요" : "식사 기록을 확인할 수 없어요"}
              </Text>
              {meals ? <Text style={styles.mutedText}>첫 사진을 남기면 분석 결과와 섭취량이 여기에 쌓여요.</Text> : null}
            </View>
          ) : null}
          <View style={styles.homeNote}>
            <Info color={homeColors.muted} size={14} />
            <Text style={styles.mutedText}>사진으로 기록한 영양값은 추정치예요.</Text>
          </View>
        </View>

        {nextActionTitle ? (
          <View style={styles.guidance}>
            <TrustBuddy size={54} pose="coach" />
            <View style={styles.guidanceCopy}>
              <Text style={styles.guidanceLabel} accessibilityRole="header">다음 행동</Text>
              <Text style={styles.mealName}>{nextActionTitle}</Text>
              {nextActionDetail ? <Text style={styles.mutedText}>{nextActionDetail}</Text> : null}
              {proteinRemaining !== undefined && proteinRemaining > 0 && !nutritionGuidance?.includes(`${proteinRemaining}g`) ? (
                <Text style={styles.mutedText}>단백질 {formatNumber(proteinRemaining)}g 남음</Text>
              ) : null}
              {nutritionGuidance && nutritionGuidance !== nextActionTitle && nutritionGuidance !== nextActionDetail ? (
                <Text style={styles.mutedText}>{nutritionGuidance}</Text>
              ) : null}
            </View>
          </View>
        ) : null}

        <View style={styles.settings}>
          <HomeLink icon={<ShieldCheck color={homeColors.brand} size={18} />} title="개인정보·안전" hint="저장과 분석 원칙 확인" onPress={onOpenSafety} />
          <HomeLink icon={<CreditCard color={homeColors.brand} size={18} />} title="플랜·결제" hint="무료 베타와 Pro 준비 상태 확인" onPress={onOpenPlan} />
        </View>
      </View>
    </ScrollView>
  );
}

function MealRow({ meal, disabled, onRepeat, onDelete }: {
  meal: DashboardMeal;
  disabled: boolean;
  onRepeat: (id: string) => void;
  onDelete: (id: string, name: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const nutrition = meal.nutrition;
  const meta = [mealTypeLabels[meal.mealType], nutrition ? `단백질 ${formatNumber(nutrition.proteinG)}g` : undefined, confidenceLabelText(meal.confidenceLabel)].filter(Boolean).join(" · ");
  const Chevron = expanded ? ChevronDown : ChevronRight;

  return (
    <View style={styles.meal}>
      <TouchableOpacity style={styles.mealRow} activeOpacity={0.75} onPress={() => setExpanded(!expanded)} accessibilityRole="button" accessibilityState={{ expanded }} accessibilityHint={expanded ? "식사 상세를 접습니다" : "식사 상세와 기록 옵션을 엽니다"}>
        <View style={styles.thumb}><Soup color={homeColors.blue} size={20} /></View>
        <View style={styles.mealCopy}>
          <Text style={styles.mealName}>{meal.name}</Text>
          <Text style={styles.mealMeta}>{meta}</Text>
        </View>
        <View style={styles.mealTrailing}>
          <Text style={styles.mealKcal}>{formatNumber(meal.caloriesKcal)} <Text style={styles.mealKcalUnit}>kcal</Text></Text>
          <Chevron color={homeColors.weak} size={14} />
        </View>
      </TouchableOpacity>
      {expanded ? (
        <View style={styles.mealDetails}>
          {nutrition ? (
            <View style={styles.detailMacros}>
              {macroFields.map(({ key, label }) => (
                <Text key={key} style={styles.mutedText}>{label} <Text style={styles.metricStrong}>{formatNumber(nutrition[key])}g</Text></Text>
              ))}
            </View>
          ) : null}
          <View style={styles.mealActions}>
            <TouchableOpacity style={[styles.mealAction, disabled && styles.disabled]} disabled={disabled} activeOpacity={0.75} onPress={() => onRepeat(meal.id)} accessibilityRole="button" accessibilityLabel={`${meal.name} 다시 기록`} accessibilityState={{ disabled }}>
              <RotateCcw color={homeColors.brand} size={16} />
              <Text style={styles.mealActionText}>다시 기록</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.mealAction, disabled && styles.disabled]} disabled={disabled} activeOpacity={0.75} onPress={() => onDelete(meal.id, meal.name)} accessibilityRole="button" accessibilityLabel={`${meal.name} 기록 삭제`} accessibilityState={{ disabled }}>
              <Trash2 color={homeColors.muted} size={16} />
              <Text style={[styles.mealActionText, styles.deleteText]}>삭제</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : null}
    </View>
  );
}

function NutritionProgress({ label, consumed, target, color = freshGreen.indicator, compact = false }: {
  label: string;
  consumed?: number;
  target?: number;
  color?: string;
  compact?: boolean;
}) {
  const percent = consumed !== undefined && target !== undefined && target > 0
    ? Math.round(Math.min(1, Math.max(0, consumed / target)) * 100)
    : undefined;
  return (
    <View style={[styles.progressTrack, compact && styles.macroTrack]} accessible={percent !== undefined} accessibilityRole="progressbar" accessibilityLabel={label} accessibilityValue={percent === undefined ? undefined : { min: 0, max: 100, now: percent }}>
      {percent !== undefined ? <View style={[styles.progressFill, { width: `${percent}%`, backgroundColor: color }]} /> : null}
    </View>
  );
}

function HomeLink({ icon, title, hint, onPress }: { icon: ReactNode; title: string; hint: string; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.settingsRow} activeOpacity={0.75} onPress={onPress} accessibilityRole="button" accessibilityLabel={title} accessibilityHint={hint}>
      {icon}
      <View style={styles.settingsCopy}>
        <Text style={styles.mealName}>{title}</Text>
        <Text style={styles.mutedText}>{hint}</Text>
      </View>
      <ChevronRight color={homeColors.weak} size={14} />
    </TouchableOpacity>
  );
}

function formatDashboardDate(value?: string): string | undefined {
  if (!value) return undefined;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? undefined : dayFormatter.format(date);
}

function formatNumber(value?: number): string {
  return value === undefined ? "-" : numberFormatter.format(value);
}
