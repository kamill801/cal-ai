import type { AnalysisResultSummary, NutritionTarget } from "@cal-ai/shared";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "../theme";

type MacroSource = Pick<NutritionTarget, "proteinG" | "carbsG" | "fatG"> | Pick<AnalysisResultSummary, "proteinG" | "carbsG" | "fatG">;

const macroRows = [
  { key: "proteinG", label: "단백질", color: colors.protein },
  { key: "carbsG", label: "탄수화물", color: colors.carbs },
  { key: "fatG", label: "지방", color: colors.fat }
] as const;

export function MacroSummary({ macros }: { macros: MacroSource }) {
  return (
    <View style={styles.row}>
      {macroRows.map((macro) => (
        <View key={macro.key} style={styles.card} accessibilityLabel={`${macro.label} ${macros[macro.key]}그램`}>
          <View style={[styles.dot, { backgroundColor: macro.color }]} />
          <Text style={styles.label}>{macro.label}</Text>
          <Text style={styles.value}>{macros[macro.key]}g</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    gap: spacing.sm
  },
  card: {
    flex: 1,
    minWidth: 0,
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
  label: {
    color: colors.muted,
    ...typography.caption
  },
  value: {
    color: colors.ink,
    marginTop: spacing.xs,
    fontSize: 19,
    lineHeight: 23,
    fontWeight: "800"
  }
});
