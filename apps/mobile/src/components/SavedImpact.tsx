import type { SavedImpactViewModel } from "@cal-ai/shared";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, shadows, spacing, typography } from "../theme";
import { TrustBuddy } from "./TrustBuddy";

export function SavedImpact({ impact }: { impact: SavedImpactViewModel }) {
  return (
    <View style={styles.card} accessibilityLabel={`${impact.confirmation}. 남은 칼로리 ${impact.remainingCaloriesKcal}킬로칼로리`}>
      <View style={styles.header}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{impact.confirmation}</Text>
        </View>
        <TrustBuddy size={58} accessory="sprout" />
      </View>
      <Text style={styles.title}>오늘 남은 칼로리는 {impact.remainingCaloriesKcal.toLocaleString()}kcal예요.</Text>
      <Text style={styles.body}>{impact.nextMealSuggestion}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg,
    ...shadows.card
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.md
  },
  badge: {
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    backgroundColor: colors.leafSoft,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs
  },
  badgeText: {
    color: colors.leaf,
    ...typography.caption
  },
  title: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  body: {
    color: colors.body,
    ...typography.body
  }
});
