import type { DashboardTodayResponse } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { ConfidencePill } from "../components/ConfidencePill";
import { MacroSummary } from "../components/MacroSummary";
import { colors, radii, spacing, typography } from "../theme";

export function TodayDashboardScreen({ dashboard, onStartScan }: { dashboard: DashboardTodayResponse; onStartScan: () => void }) {
  const remaining = dashboard.target.caloriesKcal - dashboard.consumed.caloriesKcal;
  const progress = Math.min(1, dashboard.consumed.caloriesKcal / dashboard.target.caloriesKcal);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>오늘의 식단</Text>
        <Text style={styles.title}>점심 전이에요</Text>
        <Text style={styles.subtitle}>사진으로 기록하고, 불확실한 부분만 짧게 확인해요.</Text>
      </View>

      <View style={styles.heroCard}>
        <View style={styles.spaceBetweenRow}>
          <Text style={styles.cardLabel}>남은 권장 섭취량</Text>
          <Text style={styles.goalLabel}>목표 -0.4kg/주</Text>
        </View>
        <View style={styles.kcalRow} accessibilityLabel={`남은 권장 섭취량 ${remaining}킬로칼로리`}>
          <Text style={styles.kcal}>{remaining.toLocaleString()}</Text>
          <Text style={styles.kcalUnit}>kcal</Text>
        </View>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${Math.round(progress * 100)}%` }]} />
        </View>
      </View>

      <MacroSummary macros={dashboard.consumed} />

      <TouchableOpacity style={styles.scanButton} activeOpacity={0.86} onPress={onStartScan} accessibilityRole="button">
        <View style={styles.scanCopy}>
          <Text style={styles.scanTitle}>음식 사진 찍기</Text>
          <Text style={styles.scanSubtitle}>사진으로 분석하고 바로 확인</Text>
        </View>
        <View style={styles.scanIcon}>
          <Text style={styles.scanIconText}>+</Text>
        </View>
      </TouchableOpacity>

      <View style={styles.guidanceCard}>
        <Text style={styles.warningLabel}>다음 식사 방향</Text>
        <Text style={styles.guidanceTitle}>{dashboard.nextMealGuidance.explanation}</Text>
        <Text style={styles.guidanceBody}>{dashboard.nextMealGuidance.menuTypeRecommendations.join(" · ")}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>최근 기록</Text>
        {dashboard.meals.map((meal) => (
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

const styles = StyleSheet.create({
  container: {
    gap: spacing.lg,
    padding: spacing.lg,
    paddingBottom: spacing.xxl
  },
  header: {
    gap: spacing.xs,
    paddingTop: spacing.sm
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
  heroCard: {
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg
  },
  spaceBetweenRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: spacing.sm
  },
  cardLabel: {
    color: colors.muted,
    ...typography.caption
  },
  goalLabel: {
    color: colors.leaf,
    ...typography.caption
  },
  kcalRow: {
    alignItems: "baseline",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  kcal: {
    color: colors.ink,
    fontVariant: ["tabular-nums"],
    ...typography.displayNumber
  },
  kcalUnit: {
    color: colors.muted,
    ...typography.bodyStrong
  },
  progressTrack: {
    height: 10,
    overflow: "hidden",
    borderRadius: radii.pill,
    backgroundColor: colors.leafMuted
  },
  progressFill: {
    height: "100%",
    borderRadius: radii.pill,
    backgroundColor: colors.leaf
  },
  scanButton: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.md,
    borderRadius: radii.control,
    backgroundColor: colors.leaf,
    padding: spacing.lg,
    minHeight: 72
  },
  scanCopy: {
    flex: 1,
    minWidth: 0
  },
  scanTitle: {
    color: colors.surface,
    fontSize: 17,
    lineHeight: 22,
    fontWeight: "800"
  },
  scanSubtitle: {
    color: "rgba(255, 255, 255, 0.78)",
    marginTop: spacing.xs,
    ...typography.caption
  },
  scanIcon: {
    alignItems: "center",
    justifyContent: "center",
    width: 42,
    height: 42,
    borderRadius: radii.control,
    backgroundColor: "rgba(255, 255, 255, 0.16)"
  },
  scanIconText: {
    color: colors.surface,
    fontSize: 24,
    fontWeight: "800"
  },
  guidanceCard: {
    gap: spacing.sm,
    borderColor: colors.warningBorder,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.warningBg,
    padding: spacing.lg
  },
  warningLabel: {
    color: colors.warningText,
    ...typography.caption
  },
  guidanceTitle: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  guidanceBody: {
    color: colors.body,
    ...typography.body
  },
  section: {
    gap: spacing.sm
  },
  sectionTitle: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  mealRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.md
  },
  thumb: {
    width: 48,
    height: 48,
    borderRadius: radii.photo,
    backgroundColor: colors.surfaceSoft
  },
  mealText: {
    flex: 1,
    minWidth: 0,
    gap: spacing.xs
  },
  mealName: {
    color: colors.ink,
    ...typography.bodyStrong
  },
  mealMetaRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  mealMeta: {
    color: colors.muted,
    ...typography.caption
  },
  mealKcal: {
    color: colors.ink,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: "800"
  }
});
