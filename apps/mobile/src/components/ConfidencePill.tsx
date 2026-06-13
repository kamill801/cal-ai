import type { ConfidenceGroup, ConfidenceLabel } from "@cal-ai/shared";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "../theme";

const labelToGroup: Record<ConfidenceLabel, ConfidenceGroup> = {
  high: "certain",
  medium_high: "certain",
  medium: "estimated",
  low: "needs_check",
  manual: "manual"
};

const groupCopy: Record<ConfidenceGroup, string> = {
  certain: "확실",
  estimated: "추정",
  needs_check: "확인 필요",
  manual: "직접 입력"
};

const groupColor: Record<ConfidenceGroup, string> = {
  certain: colors.leaf,
  estimated: colors.warningText,
  needs_check: colors.danger,
  manual: colors.muted
};

export function confidenceLabelText(label: ConfidenceLabel, group?: ConfidenceGroup): string {
  return groupCopy[group ?? labelToGroup[label]];
}

export function ConfidencePill({ label, group }: { label: ConfidenceLabel; group?: ConfidenceGroup }) {
  const resolvedGroup = group ?? labelToGroup[label];
  const color = groupColor[resolvedGroup];

  return (
    <View style={[styles.pill, { borderColor: color, backgroundColor: `${color}14` }]} accessibilityLabel={`신뢰도 ${groupCopy[resolvedGroup]}`}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <Text style={[styles.text, { color }]}>{groupCopy[resolvedGroup]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    alignItems: "center",
    alignSelf: "flex-start",
    flexDirection: "row",
    gap: spacing.xs,
    borderWidth: 1,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: radii.pill
  },
  text: {
    ...typography.caption
  }
});
