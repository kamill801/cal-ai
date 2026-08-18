import { StyleSheet } from "react-native";
import { colors, radii, shadows, spacing, typography } from "../theme";

export const styles = StyleSheet.create({
  container: {
    gap: spacing.md,
    padding: spacing.lg,
    paddingBottom: spacing.xxl
  },
  topBar: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.md,
    paddingTop: spacing.sm
  },
  greeting: {
    color: colors.body,
    ...typography.bodyStrong
  },
  title: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  heroCard: {
    position: "relative",
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.photo,
    borderWidth: 1,
    backgroundColor: colors.surface,
    overflow: "hidden",
    padding: spacing.lg,
    ...shadows.card
  },
  spaceBetweenRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: spacing.sm
  },
  cardLabel: {
    color: colors.muted,
    ...typography.caption
  },
  goalLabel: {
    color: colors.leaf,
    ...typography.caption
  },
  kcalRow: {
    alignItems: "baseline",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  kcal: {
    color: colors.ink,
    fontVariant: ["tabular-nums"],
    ...typography.displayNumber
  },
  kcalUnit: {
    color: colors.muted,
    ...typography.bodyStrong
  },
  progressTrack: {
    height: 10,
    overflow: "hidden",
    borderRadius: radii.pill,
    backgroundColor: colors.leafMuted
  },
  progressFill: {
    height: "100%",
    borderRadius: radii.pill,
    backgroundColor: colors.leaf
  },
  weeklyCard: {
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg,
    ...shadows.card
  },
  barRow: {
    alignItems: "flex-end",
    flexDirection: "row",
    gap: spacing.sm,
    height: 78
  },
  barSlot: {
    flex: 1,
    height: "100%",
    justifyContent: "flex-end",
    borderRadius: radii.pill,
    backgroundColor: colors.leafTint,
    overflow: "hidden"
  },
  barFill: {
    minHeight: 16,
    borderTopLeftRadius: radii.pill,
    borderTopRightRadius: radii.pill,
    backgroundColor: colors.leaf
  },
  legendRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md
  },
  legendText: {
    color: colors.muted,
    ...typography.caption
  },
  scanButton: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.md,
    borderRadius: radii.card,
    backgroundColor: colors.leaf,
    padding: spacing.lg,
    minHeight: 74,
    ...shadows.card
  },
  scanCopy: {
    flex: 1,
    minWidth: 0
  },
  scanTitle: {
    color: colors.surface,
    fontSize: 17,
    lineHeight: 22,
    fontWeight: "800"
  },
  scanSubtitle: {
    color: "rgba(255, 255, 255, 0.78)",
    marginTop: spacing.xs,
    ...typography.caption
  },
  scanIcon: {
    alignItems: "center",
    justifyContent: "center",
    width: 42,
    height: 42,
    borderRadius: radii.pill,
    backgroundColor: "rgba(255, 255, 255, 0.16)"
  },
  scanIconText: {
    color: colors.surface,
    fontSize: 24,
    fontWeight: "800"
  },
  secondaryActionRow: {
    flexDirection: "row",
    gap: spacing.sm
  },
  secondaryAction: {
    flex: 1,
    gap: spacing.xs,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.md,
    ...shadows.card
  },
  secondaryActionTitle: {
    color: colors.ink,
    ...typography.bodyStrong
  },
  secondaryActionBody: {
    color: colors.muted,
    ...typography.caption
  },
  guidanceCard: {
    gap: spacing.sm,
    borderColor: colors.warningBorder,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.warningBg,
    padding: spacing.lg,
    ...shadows.card
  },
  coachRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md
  },
  coachCopy: {
    flex: 1,
    minWidth: 0
  },
  warningLabel: {
    color: colors.warningText,
    ...typography.caption
  },
  guidanceTitle: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  guidanceBody: {
    color: colors.body,
    ...typography.body
  },
  section: {
    gap: spacing.sm
  },
  sectionTitle: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  emptyState: {
    gap: spacing.xs,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surfaceSoft,
    padding: spacing.lg
  },
  emptyTitle: {
    color: colors.ink,
    ...typography.bodyStrong
  },
  mealRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.md,
    ...shadows.card
  },
  thumb: {
    width: 48,
    height: 48,
    borderRadius: radii.photo,
    backgroundColor: colors.surfaceSoft
  },
  mealText: {
    flex: 1,
    minWidth: 0,
    gap: spacing.xs
  },
  mealName: {
    color: colors.ink,
    ...typography.bodyStrong
  },
  mealMetaRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  mealMeta: {
    color: colors.muted,
    ...typography.caption
  },
  mealKcal: {
    color: colors.ink,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: "800"
  }
});
