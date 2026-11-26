import { StyleSheet } from "react-native";
import { freshGreen } from "../theme";

export const homeColors = {
  paper: "#FFFFFF",
  ink: "#182222",
  muted: "#556462",
  weak: "#657372",
  line: "#E2E8E7",
  track: "#EAF0EE",
  outline: "#CBD8D3",
  brand: freshGreen.ink,
  cool: "#EFF4F6",
  blue: "#466B82",
  carb: "#6F96A8",
  fat: "#B38761"
};

export const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: homeColors.paper
  },
  container: {
    flexGrow: 1,
    paddingHorizontal: 22,
    paddingBottom: 24,
    alignItems: "center"
  },
  page: {
    width: "100%",
    maxWidth: 540
  },
  masthead: {
    minHeight: 84,
    paddingBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: homeColors.line
  },
  mastheadCopy: {
    flex: 1,
    gap: 3
  },
  date: {
    color: homeColors.weak,
    fontSize: 12,
    fontWeight: "700"
  },
  title: {
    color: homeColors.ink,
    fontSize: 30,
    fontWeight: "800"
  },
  summary: {
    paddingTop: 19,
    paddingBottom: 16
  },
  metricTitle: {
    color: homeColors.muted,
    fontSize: 13,
    fontWeight: "700"
  },
  kcal: {
    marginTop: 2,
    color: homeColors.ink,
    fontSize: 49,
    fontWeight: "800",
    fontVariant: ["tabular-nums"]
  },
  kcalUnit: {
    color: homeColors.muted,
    fontSize: 18,
    fontWeight: "700"
  },
  energyNote: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: 4,
    marginTop: 10,
    marginBottom: 7
  },
  metricNote: {
    color: homeColors.muted,
    fontSize: 12,
    fontVariant: ["tabular-nums"]
  },
  metricStrong: {
    color: homeColors.ink,
    fontWeight: "800"
  },
  progressTrack: {
    height: 4,
    borderRadius: 2,
    backgroundColor: homeColors.track,
    overflow: "hidden"
  },
  progressFill: {
    height: "100%"
  },
  macros: {
    flexDirection: "row",
    gap: 11,
    marginTop: 16
  },
  macro: {
    flex: 1,
    minWidth: 0
  },
  macroLabel: {
    marginBottom: 2,
    color: homeColors.muted,
    fontSize: 11,
    fontWeight: "700"
  },
  proteinLabel: {
    color: homeColors.brand
  },
  macroValue: {
    marginBottom: 6,
    color: homeColors.ink,
    fontSize: 17,
    fontWeight: "800",
    fontVariant: ["tabular-nums"]
  },
  macroGoal: {
    color: homeColors.muted,
    fontSize: 11,
    fontWeight: "500"
  },
  macroTrack: {
    marginTop: "auto",
    height: 3
  },
  captureActions: {
    flexDirection: "row",
    gap: 8
  },
  captureButton: {
    flex: 1,
    minHeight: 48,
    paddingHorizontal: 10,
    paddingVertical: 8,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 7,
    borderRadius: 6,
    backgroundColor: freshGreen.fill
  },
  captureTitle: {
    flexShrink: 1,
    color: freshGreen.onFill,
    fontWeight: "800",
    fontSize: 13
  },
  albumButton: {
    width: 48,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: homeColors.outline
  },
  mealsSection: {
    marginTop: 21
  },
  sectionHeading: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: 8,
    paddingBottom: 9
  },
  sectionTitle: {
    color: homeColors.ink,
    fontSize: 17,
    fontWeight: "800"
  },
  meal: {
    borderTopColor: homeColors.line,
    borderTopWidth: 1
  },
  mealRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    minHeight: 69,
    paddingVertical: 12
  },
  thumb: {
    width: 43,
    height: 43,
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: homeColors.cool
  },
  mealCopy: {
    flex: 1,
    minWidth: 0,
    gap: 2
  },
  mealName: {
    color: homeColors.ink,
    fontSize: 14,
    fontWeight: "800"
  },
  mealMeta: {
    color: homeColors.muted,
    fontSize: 11,
    fontVariant: ["tabular-nums"]
  },
  mealTrailing: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    maxWidth: "42%"
  },
  mealKcal: {
    flexShrink: 1,
    textAlign: "right",
    color: homeColors.ink,
    fontSize: 14,
    fontWeight: "800",
    fontVariant: ["tabular-nums"]
  },
  mealKcalUnit: {
    color: homeColors.muted,
    fontSize: 10,
    fontWeight: "600"
  },
  mealDetails: {
    paddingBottom: 10,
    gap: 6
  },
  detailMacros: {
    flexDirection: "row",
    flexWrap: "wrap",
    columnGap: 14,
    rowGap: 4
  },
  mealActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  mealAction: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    minHeight: 44,
    paddingHorizontal: 12,
    borderColor: homeColors.outline,
    borderWidth: 1,
    borderRadius: 6
  },
  mealActionText: {
    color: homeColors.brand,
    fontSize: 12,
    fontWeight: "700"
  },
  deleteText: {
    color: homeColors.muted
  },
  disabled: {
    opacity: 0.5
  },
  emptyState: {
    gap: 4,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: homeColors.line
  },
  homeNote: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: homeColors.line
  },
  mutedText: {
    flexShrink: 1,
    color: homeColors.muted,
    fontSize: 12
  },
  guidance: {
    marginTop: 24,
    paddingVertical: 14,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    borderTopWidth: 1,
    borderTopColor: homeColors.line
  },
  guidanceCopy: {
    flex: 1,
    gap: 4
  },
  guidanceLabel: {
    color: homeColors.brand,
    fontSize: 11,
    fontWeight: "700"
  },
  settings: {
    marginTop: 8,
    borderBottomWidth: 1,
    borderBottomColor: homeColors.line
  },
  settingsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    minHeight: 54,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: homeColors.line
  },
  settingsCopy: {
    flex: 1,
    gap: 3
  }
});
