import type { CoachDashboard, DashboardTodayResponse } from "@cal-ai/shared";
import { ScrollView, Text, TouchableOpacity, View } from "react-native";
import { ConfidencePill } from "../components/ConfidencePill";
import { MacroSummary } from "../components/MacroSummary";
import { TrustBuddy } from "../components/TrustBuddy";
import { styles } from "./TodayDashboardScreen.styles";

export function TodayDashboardScreen({
  dashboard,
  coachDashboard,
  onCaptureMeal,
  onPickMeal,
  onOpenSafety
}: {
  readonly dashboard: DashboardTodayResponse;
  readonly coachDashboard?: CoachDashboard;
  readonly onCaptureMeal: () => void;
  readonly onPickMeal: () => void;
  readonly onOpenSafety: () => void;
}) {
  const target = coachDashboard?.nutrition.target ?? dashboard.target;
  const consumed = coachDashboard?.nutrition.consumed ?? dashboard.consumed;
  const remaining = coachDashboard?.nutrition.remaining.caloriesKcal ?? Math.max(0, target.caloriesKcal - consumed.caloriesKcal);
  const progress = target.caloriesKcal ? Math.min(1, consumed.caloriesKcal / target.caloriesKcal) : 0;
  const proteinRemaining = coachDashboard?.nutrition.remaining.proteinG ?? Math.max(0, target.proteinG - consumed.proteinG);
  const proteinProgress = coachDashboard?.nutrition.proteinProgress ?? Math.min(1, consumed.proteinG / target.proteinG);
  const meals = coachDashboard && consumed.caloriesKcal === 0 ? [] : dashboard.meals;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.topBar}>
        <View>
          <Text style={styles.greeting}>지연님, 오늘도</Text>
          <Text style={styles.title}>충분히 잘하고 있어요</Text>
        </View>
        <View style={styles.bell}>
          <View style={styles.bellDot} />
        </View>
      </View>

      <View style={styles.heroCard}>
        <View style={styles.buddyFloat}>
          <TrustBuddy size={76} accessory="sprout" />
        </View>
        <View style={styles.spaceBetweenRow}>
          <Text style={styles.cardLabel}>오늘 남은 권장 섭취량</Text>
          <Text style={styles.goalLabel}>개인 맞춤 목표</Text>
        </View>
        <View style={styles.kcalRow} accessibilityLabel={`남은 권장 섭취량 ${remaining}킬로칼로리`}>
          <Text style={styles.kcal}>{remaining.toLocaleString()}</Text>
          <Text style={styles.kcalUnit}>kcal</Text>
        </View>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${Math.round(progress * 100)}%` }]} />
        </View>
      </View>

      <MacroSummary macros={consumed} />

      <View style={styles.weeklyCard}>
        <View style={styles.spaceBetweenRow}>
          <Text style={styles.sectionTitle}>오늘 단백질</Text>
          <Text style={styles.cardLabel}>{proteinRemaining}g 남음</Text>
        </View>
        <View style={styles.progressTrack}><View style={[styles.progressFill, { width: `${Math.round(Math.min(1, proteinProgress) * 100)}%` }]} /></View>
        <Text style={styles.legendText}>{coachDashboard?.nutrition.guidance ?? "다음 식사에서 단백질을 먼저 챙기면 목표에 가까워져요."}</Text>
      </View>

      <TouchableOpacity style={styles.scanButton} activeOpacity={0.86} onPress={onCaptureMeal} accessibilityRole="button">
        <View style={styles.scanCopy}>
          <Text style={styles.scanTitle}>음식 사진 찍기</Text>
          <Text style={styles.scanSubtitle}>카메라로 촬영하고 바로 분석</Text>
        </View>
        <View style={styles.scanIcon}>
          <Text style={styles.scanIconText}>+</Text>
        </View>
      </TouchableOpacity>

      <View style={styles.secondaryActionRow}>
        <TouchableOpacity style={styles.secondaryAction} activeOpacity={0.82} onPress={onPickMeal} accessibilityRole="button">
          <Text style={styles.secondaryActionTitle}>사진첩에서 선택</Text>
          <Text style={styles.secondaryActionBody}>기존 음식 사진으로 테스트</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.secondaryAction} activeOpacity={0.82} onPress={onOpenSafety} accessibilityRole="button">
          <Text style={styles.secondaryActionTitle}>개인정보/안전</Text>
          <Text style={styles.secondaryActionBody}>MVP 검증 전 확인</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.guidanceCard}>
        <View style={styles.coachRow}>
          <TrustBuddy size={52} accessory="spoon" />
          <View style={styles.coachCopy}>
            <Text style={styles.warningLabel}>지금 가장 좋은 다음 행동</Text>
            <Text style={styles.guidanceTitle}>{coachDashboard?.nextAction.title ?? dashboard.nextMealGuidance.explanation}</Text>
          </View>
        </View>
        <Text style={styles.guidanceBody}>{coachDashboard?.nextAction.detail ?? dashboard.nextMealGuidance.menuTypeRecommendations.join(" · ")}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>최근 기록</Text>
        {meals.length === 0 ? <Text style={styles.legendText}>첫 식사를 기록하면 여기에 차곡차곡 보여드려요.</Text> : null}
        {meals.map((meal) => (
          <View key={meal.id} style={styles.mealRow}>
            <View style={styles.thumb} />
            <View style={styles.mealText}>
              <Text style={styles.mealName}>{meal.name}</Text>
              <View style={styles.mealMetaRow}>
                <Text style={styles.mealMeta}>{meal.mealType}</Text>
                <ConfidencePill label={meal.confidenceLabel} />
              </View>
            </View>
            <Text style={styles.mealKcal}>{meal.caloriesKcal}kcal</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}
