import type { AnalysisResultSummary, NutritionTarget } from "@cal-ai/shared";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "../theme";

type MacroSource = Pick<NutritionTarget, "proteinG" | "carbsG" | "fatG"> | Pick<AnalysisResultSummary, "proteinG" | "carbsG" | "fatG">;

const macroRows = [
  { key: "carbsG", label: "탄수화물", color: colors.sky, backgroundColor: colors.skySoft },
  { key: "proteinG", label: "단백질", color: colors.leaf, backgroundColor: colors.leafTint },
  { key: "fatG", label: "지방", color: colors.fat, backgroundColor: colors.fatSoft }
] as const;

export function MacroSummary({ macros }: { macros: MacroSource }) {
  return (
    <View style={styles.row}>
      {macroRows.map((macro) => (
        <View key={macro.key} style={[styles.card, { backgroundColor: macro.backgroundColor }]} accessibilityLabel={`${macro.label} ${macros[macro.key]}그램`}>
          <Text style={[styles.label, { color: macro.color }]}>{macro.label}</Text>
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
    alignItems: "center",
    borderRadius: radii.control,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.md
  },
  label: {
    textAlign: "center",
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
