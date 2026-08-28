import type { CoachDashboard, DashboardTodayResponse } from "@cal-ai/shared";
import { RotateCcw, Trash2 } from "lucide-react-native";
import { ScrollView, Text, TouchableOpacity, View } from "react-native";
import { ConfidencePill } from "../components/ConfidencePill";
import { MacroSummary } from "../components/MacroSummary";
import { TrustBuddy } from "../components/TrustBuddy";
import { FlowStatusCard } from "../components/FlowStatusCard";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors } from "../theme";
import { styles } from "./TodayDashboardScreen.styles";

export function TodayDashboardScreen({
  dashboard,
  coachDashboard,
  onCaptureMeal,
  onPickMeal,
  onOpenSafety,
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
  readonly onRepeatMeal: (mealLogId: string) => void;
  readonly onDeleteMeal: (mealLogId: string, mealName: string) => void;
  readonly status: RequestStatus;
  readonly error?: FlowError;
}) {
  const target = coachDashboard?.nutrition.target ?? dashboard.target;
  const consumed = coachDashboard?.nutrition.consumed ?? dashboard.consumed;
  const remaining = coachDashboard?.nutrition.remaining.caloriesKcal ?? Math.max(0, target.caloriesKcal - consumed.caloriesKcal);
  const progress = target.caloriesKcal ? Math.min(1, consumed.caloriesKcal / target.caloriesKcal) : 0;
  const proteinRemaining = coachDashboard?.nutrition.remaining.proteinG ?? Math.max(0, target.proteinG - consumed.proteinG);
  const proteinProgress = coachDashboard?.nutrition.proteinProgress ?? Math.min(1, consumed.proteinG / target.proteinG);
  const meals = coachDashboard?.meals ?? dashboard.meals;
  const calorieProgressPercent = Math.round(progress * 100);
  const proteinProgressPercent = Math.round(Math.min(1, proteinProgress) * 100);
  const hasRecords = meals.length > 0 || consumed.caloriesKcal > 0 || consumed.proteinG > 0;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.topBar}>
        <View style={styles.topBarCopy}>
          <Text style={styles.greeting}>오늘의 식단</Text>
          <Text style={styles.title}>{hasRecords ? "기록한 만큼 더 정확해져요" : "첫 식사를 기록해볼까요?"}</Text>
        </View>
        <TrustBuddy size={80} pose="meal" />
      </View>

      <TouchableOpacity style={styles.scanButton} activeOpacity={0.86} onPress={onCaptureMeal} accessibilityRole="button" accessibilityLabel="카메라로 음식 사진 찍기" accessibilityHint="촬영한 사진을 분석해 식사 기록을 시작합니다">
        <View style={styles.scanCopy}>
          <Text style={styles.scanTitle}>음식 사진 찍기</Text>
          <Text style={styles.scanSubtitle}>촬영하고 한 번 확인하면 기록돼요</Text>
        </View>
        <View style={styles.scanIcon} accessible={false}>
          <Text style={styles.scanIconText}>+</Text>
        </View>
      </TouchableOpacity>

      {error ? <FlowStatusCard error={error} /> : null}

      <View style={styles.heroCard}>
        <View style={styles.spaceBetweenRow}>
          <Text style={styles.cardLabel}>오늘 남은 권장 섭취량</Text>
          <Text style={styles.goalLabel}>개인 맞춤 목표</Text>
        </View>
        <View style={styles.kcalRow} accessibilityLabel={`남은 권장 섭취량 ${remaining}킬로칼로리`}>
          <Text style={styles.kcal}>{remaining.toLocaleString()}</Text>
          <Text style={styles.kcalUnit}>kcal</Text>
        </View>
        <View style={styles.progressTrack} accessible accessibilityRole="progressbar" accessibilityLabel="오늘 칼로리 섭취 진행률" accessibilityValue={{ min: 0, max: 100, now: calorieProgressPercent }}>
          <View style={[styles.progressFill, { width: `${calorieProgressPercent}%` }]} />
        </View>
      </View>

      <View style={styles.weeklyCard}>
        <View style={styles.spaceBetweenRow}>
          <Text style={styles.sectionTitle}>오늘 단백질</Text>
          <Text style={styles.cardLabel}>{proteinRemaining}g 남음</Text>
        </View>
        <View style={styles.progressTrack} accessible accessibilityRole="progressbar" accessibilityLabel="오늘 단백질 섭취 진행률" accessibilityValue={{ min: 0, max: 100, now: proteinProgressPercent }}><View style={[styles.progressFill, { width: `${proteinProgressPercent}%` }]} /></View>
        <Text style={styles.legendText}>{hasRecords ? coachDashboard?.nutrition.guidance ?? "다음 식사에서 단백질을 먼저 챙기면 목표에 가까워져요." : "식사를 기록하면 섭취량과 남은 양을 계산해드려요."}</Text>
      </View>

      <MacroSummary macros={consumed} />

      <View style={styles.secondaryActionRow}>
        <TouchableOpacity style={styles.secondaryAction} activeOpacity={0.82} onPress={onPickMeal} accessibilityRole="button" accessibilityLabel="사진첩에서 음식 사진 선택" accessibilityHint="이미 찍어둔 사진을 분석합니다">
          <Text style={styles.secondaryActionTitle}>사진첩에서 선택</Text>
          <Text style={styles.secondaryActionBody}>이미 찍어둔 사진 기록</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.secondaryAction} activeOpacity={0.82} onPress={onOpenSafety} accessibilityRole="button" accessibilityLabel="개인정보와 분석 안전 원칙 보기">
          <Text style={styles.secondaryActionTitle}>개인정보·안전</Text>
          <Text style={styles.secondaryActionBody}>저장과 분석 원칙 확인</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.guidanceCard}>
        <View style={styles.coachRow}>
          <TrustBuddy size={84} pose="coach" />
          <View style={styles.coachCopy}>
            <Text style={styles.warningLabel}>지금 가장 좋은 다음 행동</Text>
            <Text style={styles.guidanceTitle}>{coachDashboard?.nextAction.title ?? dashboard.nextMealGuidance.explanation}</Text>
          </View>
        </View>
        <Text style={styles.guidanceBody}>{coachDashboard?.nextAction.detail ?? dashboard.nextMealGuidance.menuTypeRecommendations.join(" · ")}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>최근 기록</Text>
        {meals.length === 0 ? (
          <View style={styles.emptyState} accessibilityLabel="아직 기록한 식사가 없습니다">
            <Text style={styles.emptyTitle}>아직 기록한 식사가 없어요</Text>
            <Text style={styles.legendText}>첫 사진을 남기면 분석 결과와 섭취량이 여기에 쌓여요.</Text>
          </View>
        ) : null}
        {meals.map((meal) => (
          <View key={meal.id} style={styles.mealRow}>
            <View style={styles.thumb} />
            <View style={styles.mealText}>
              <Text style={styles.mealName}>{meal.name}</Text>
              <View style={styles.mealMetaRow}>
                <Text style={styles.mealMeta}>{mealTypeLabel(meal.mealType)}</Text>
                <ConfidencePill label={meal.confidenceLabel} />
              </View>
            </View>
            <View style={styles.mealTrailing}>
              <Text style={styles.mealKcal}>{meal.caloriesKcal}kcal</Text>
              <View style={styles.mealActions}>
                <TouchableOpacity
                  style={styles.mealActionButton}
                  disabled={status === "loading"}
                  onPress={() => onRepeatMeal(meal.id)}
                  hitSlop={4}
                  accessibilityRole="button"
                  accessibilityLabel={`${meal.name} 다시 기록`}
                  accessibilityState={{ disabled: status === "loading" }}
                >
                  <RotateCcw color={colors.leaf} size={16} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.deleteActionButton}
                  disabled={status === "loading"}
                  onPress={() => onDeleteMeal(meal.id, meal.name)}
                  hitSlop={4}
                  accessibilityRole="button"
                  accessibilityLabel={`${meal.name} 기록 삭제`}
                  accessibilityState={{ disabled: status === "loading" }}
                >
                  <Trash2 color={colors.muted} size={16} />
                </TouchableOpacity>
              </View>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

function mealTypeLabel(value: string): string {
  return { breakfast: "아침", lunch: "점심", dinner: "저녁", snack: "간식" }[value] ?? value;
}
