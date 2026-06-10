import { StatusBar } from "expo-status-bar";
import { SafeAreaView, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { todayDashboard } from "./src/mockData";
import { colors, radii, spacing } from "./src/theme";

function MacroCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={styles.macroCard}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <Text style={styles.macroLabel}>{label}</Text>
      <Text style={styles.macroValue}>{value}</Text>
    </View>
  );
}

export default function App() {
  const remaining = todayDashboard.target.caloriesKcal - todayDashboard.consumed.caloriesKcal;
  const progress = todayDashboard.consumed.caloriesKcal / todayDashboard.target.caloriesKcal;

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <Text style={styles.eyebrow}>오늘의 식단</Text>
          <Text style={styles.title}>점심 전이에요</Text>
        </View>

        <View style={styles.heroCard}>
          <View style={styles.row}>
            <Text style={styles.cardLabel}>남은 권장 섭취량</Text>
            <Text style={styles.greenLabel}>목표 -0.4kg/주</Text>
          </View>
          <View style={styles.kcalRow}>
            <Text style={styles.kcal}>{remaining.toLocaleString()}</Text>
            <Text style={styles.kcalUnit}>kcal</Text>
          </View>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${Math.round(progress * 100)}%` }]} />
          </View>
        </View>

        <View style={styles.macroGrid}>
          <MacroCard label="단백질" value={`${todayDashboard.consumed.proteinG}g`} color={colors.protein} />
          <MacroCard label="탄수화물" value={`${todayDashboard.consumed.carbsG}g`} color={colors.carbs} />
          <MacroCard label="지방" value={`${todayDashboard.consumed.fatG}g`} color={colors.fat} />
        </View>

        <TouchableOpacity style={styles.scanButton} activeOpacity={0.86}>
          <View>
            <Text style={styles.scanTitle}>음식 사진 찍기</Text>
            <Text style={styles.scanSubtitle}>사진으로 분석하고 바로 확인</Text>
          </View>
          <View style={styles.scanIcon}>
            <Text style={styles.scanIconText}>+</Text>
          </View>
        </TouchableOpacity>

        <View style={styles.guidanceCard}>
          <Text style={styles.warningLabel}>다음 식사 방향</Text>
          <Text style={styles.guidanceTitle}>{todayDashboard.nextMealGuidance.explanation}</Text>
          <Text style={styles.guidanceBody}>{todayDashboard.nextMealGuidance.menuTypeRecommendations.join(", ")}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>최근 기록</Text>
          {todayDashboard.meals.map((meal) => (
            <View key={meal.id} style={styles.mealRow}>
              <View style={styles.thumb} />
              <View style={styles.mealText}>
                <Text style={styles.mealName}>{meal.name}</Text>
                <Text style={styles.mealMeta}>{meal.mealType} · {meal.confidenceLabel}</Text>
              </View>
              <Text style={styles.mealKcal}>{meal.caloriesKcal}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.paper
  },
  container: {
    gap: spacing.lg,
    padding: spacing.lg,
    paddingBottom: spacing.xxl
  },
  header: {
    gap: 4,
    paddingTop: spacing.sm
  },
  eyebrow: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700"
  },
  title: {
    color: colors.ink,
    fontSize: 28,
    fontWeight: "800",
    lineHeight: 32
  },
  heroCard: {
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between"
  },
  cardLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700"
  },
  greenLabel: {
    color: colors.green,
    fontSize: 12,
    fontWeight: "800"
  },
  kcalRow: {
    alignItems: "baseline",
    flexDirection: "row",
    gap: spacing.sm
  },
  kcal: {
    color: colors.ink,
    fontSize: 56,
    fontWeight: "800",
    lineHeight: 58
  },
  kcalUnit: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: "800"
  },
  progressTrack: {
    height: 10,
    overflow: "hidden",
    borderRadius: radii.pill,
    backgroundColor: "#e7eadf"
  },
  progressFill: {
    height: "100%",
    borderRadius: radii.pill,
    backgroundColor: colors.greenSoft
  },
  macroGrid: {
    flexDirection: "row",
    gap: spacing.sm
  },
  macroCard: {
    flex: 1,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.md
  },
  dot: {
    width: 8,
    height: 8,
    marginBottom: spacing.sm,
    borderRadius: radii.pill
  },
  macroLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "700"
  },
  macroValue: {
    color: colors.ink,
    marginTop: 4,
    fontSize: 19,
    fontWeight: "800"
  },
  scanButton: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    borderRadius: radii.control,
    backgroundColor: colors.green,
    padding: spacing.lg
  },
  scanTitle: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "800"
  },
  scanSubtitle: {
    color: "rgba(255, 255, 255, 0.76)",
    marginTop: 4,
    fontSize: 12,
    fontWeight: "700"
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
    color: "#ffffff",
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
    fontSize: 12,
    fontWeight: "800"
  },
  guidanceTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: "800",
    lineHeight: 22
  },
  guidanceBody: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "500",
    lineHeight: 19
  },
  section: {
    gap: spacing.sm
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "800"
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
    width: 36,
    height: 36,
    borderRadius: radii.card,
    backgroundColor: colors.soft
  },
  mealText: {
    flex: 1
  },
  mealName: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "800"
  },
  mealMeta: {
    color: colors.muted,
    marginTop: 2,
    fontSize: 11,
    fontWeight: "600"
  },
  mealKcal: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "800"
  }
});
