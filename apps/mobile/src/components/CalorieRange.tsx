import type { CalorieRange as CalorieRangeValue } from "@cal-ai/shared";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "../theme";

export function CalorieRange({ range, label = "예상 범위", compact = false }: { range: CalorieRangeValue; label?: string; compact?: boolean }) {
  return (
    <View style={styles.wrap} accessibilityLabel={`${label} 약 ${range.low}에서 ${range.high}킬로칼로리`}>
      <View style={styles.labelRow}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.info}>근거 기반 분석이에요</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.prefix}>예상</Text>
        <Text style={[styles.number, compact && styles.compactNumber]}>{range.low}-{range.high}</Text>
        <Text style={styles.unit}>kcal</Text>
      </View>
      <View style={styles.reasonPill}>
        <Text style={styles.reasonText}>중간값 {range.midpoint}kcal · 범위로 보는 게 더 안전해요</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.sm,
    minWidth: 0
  },
  labelRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  label: {
    color: colors.muted,
    ...typography.caption
  },
  info: {
    color: colors.leaf,
    ...typography.caption
  },
  row: {
    alignItems: "baseline",
    flexDirection: "row",
    flexWrap: "wrap",
    columnGap: spacing.sm
  },
  prefix: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  number: {
    color: colors.leaf,
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
  reasonPill: {
    alignSelf: "flex-start",
    borderRadius: radii.pill,
    backgroundColor: colors.leafTint,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm
  },
  reasonText: {
    color: colors.leaf,
    ...typography.caption
  }
});
