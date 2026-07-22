import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function CoachCard({ title, eyebrow, children, tone = "default" }: { readonly title: string; readonly eyebrow?: string; readonly children: ReactNode; readonly tone?: "default" | "leaf" | "warm" }) {
  return (
    <View style={[styles.card, tone === "leaf" && styles.leaf, tone === "warm" && styles.warm]}>
      {eyebrow ? <Text style={styles.eyebrow}>{eyebrow}</Text> : null}
      <Text style={styles.title}>{title}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { gap: spacing.md, borderColor: colors.hairline, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.lg, ...shadows.card },
  leaf: { borderColor: colors.leafMuted, backgroundColor: colors.leafTint },
  warm: { borderColor: colors.warningBorder, backgroundColor: colors.warningBg },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.sectionTitle }
});
