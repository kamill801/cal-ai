import type { RangeNarrowingResult } from "@cal-ai/shared";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "../theme";

function RangeBox({ label, low, high, highlight }: { label: string; low: number; high: number; highlight?: boolean }) {
  return (
    <View style={[styles.box, highlight && styles.highlightBox]}>
      <Text style={styles.label}>{label}</Text>
      <Text style={[styles.value, highlight && styles.highlightText]}>{low}-{high}kcal</Text>
    </View>
  );
}

export function RangeNarrowing({ narrowing }: { narrowing: RangeNarrowingResult }) {
  return (
    <View style={styles.wrap} accessibilityLabel={`칼로리 범위가 ${narrowing.before.low}-${narrowing.before.high}에서 ${narrowing.after.low}-${narrowing.after.high}로 줄었어요`}>
      <View style={styles.row}>
        <RangeBox label="전" low={narrowing.before.low} high={narrowing.before.high} />
        <Text style={styles.arrow}>→</Text>
        <RangeBox label="후" low={narrowing.after.low} high={narrowing.after.high} highlight />
      </View>
      <Text style={styles.copy}>{narrowing.copy}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.sm,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.leafSoft,
    padding: spacing.md
  },
  row: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm
  },
  box: {
    flex: 1,
    minWidth: 0,
    borderRadius: radii.control,
    backgroundColor: colors.surface,
    padding: spacing.sm
  },
  highlightBox: {
    borderColor: colors.leaf,
    borderWidth: 1
  },
  label: {
    color: colors.muted,
    ...typography.caption
  },
  value: {
    color: colors.ink,
    marginTop: spacing.xs,
    fontSize: 15,
    lineHeight: 20,
    fontWeight: "800"
  },
  highlightText: {
    color: colors.leaf
  },
  arrow: {
    color: colors.muted,
    fontSize: 18,
    fontWeight: "800"
  },
  copy: {
    color: colors.body,
    ...typography.caption
  }
});
