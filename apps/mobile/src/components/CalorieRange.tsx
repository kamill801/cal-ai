import type { CalorieRange as CalorieRangeValue } from "@cal-ai/shared";
import { StyleSheet, Text, View } from "react-native";
import { colors, spacing, typography } from "../theme";

export function CalorieRange({ range, label = "예상 범위", compact = false }: { range: CalorieRangeValue; label?: string; compact?: boolean }) {
  return (
    <View style={styles.wrap} accessibilityLabel={`${label} 약 ${range.low}에서 ${range.high}킬로칼로리`}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.row}>
        <Text style={[styles.number, compact && styles.compactNumber]}>약 {range.low}-{range.high}</Text>
        <Text style={styles.unit}>kcal</Text>
      </View>
      <Text style={styles.midpoint}>중간값 {range.midpoint}kcal · 범위로 보는 게 더 안전해요</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.xs,
    minWidth: 0
  },
  label: {
    color: colors.muted,
    ...typography.caption
  },
  row: {
    alignItems: "baseline",
    flexDirection: "row",
    flexWrap: "wrap",
    columnGap: spacing.sm
  },
  number: {
    color: colors.ink,
    fontVariant: ["tabular-nums"],
    ...typography.displayNumber
  },
  compactNumber: {
    fontSize: 36,
    lineHeight: 40
  },
  unit: {
    color: colors.muted,
    ...typography.bodyStrong
  },
  midpoint: {
    color: colors.muted,
    ...typography.caption
  }
});
