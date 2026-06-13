import type { SavedImpactViewModel } from "@cal-ai/shared";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "../theme";

export function SavedImpact({ impact }: { impact: SavedImpactViewModel }) {
  return (
    <View style={styles.card} accessibilityLabel={`${impact.confirmation}. 남은 칼로리 ${impact.remainingCaloriesKcal}킬로칼로리`}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{impact.confirmation}</Text>
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
    padding: spacing.lg
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
