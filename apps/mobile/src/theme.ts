export const colors = {
  ink: "#20221f",
  black: "#0a0a0a",
  body: "#3a3a3a",
  muted: "#6a6a6a",
  mutedSoft: "#9a9a9a",
  hairline: "#d8ded2",
  canvas: "#fffaf0",
  paper: "#fbfaf6",
  surface: "#ffffff",
  surfaceSoft: "#f5f0e0",
  leaf: "#2f6540",
  leafSoft: "#eef4ec",
  leafMuted: "#dfeade",
  protein: "#4b8397",
  carbs: "#cc8a25",
  fat: "#d35b45",
  peach: "#ffb084",
  lavender: "#b8a4ed",
  warningBg: "#fff8ee",
  warningBorder: "#f0d4b5",
  warningText: "#7a4e11",
  danger: "#ef4444",
  success: "#22c55e"
} as const;

export const radii = {
  card: 8,
  control: 8,
  photo: 12,
  sheet: 18,
  pill: 999
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32
} as const;

export const typography = {
  caption: { fontSize: 12, lineHeight: 16, fontWeight: "700" as const },
  body: { fontSize: 14, lineHeight: 21, fontWeight: "500" as const },
  bodyStrong: { fontSize: 15, lineHeight: 22, fontWeight: "700" as const },
  sectionTitle: { fontSize: 17, lineHeight: 23, fontWeight: "800" as const },
  screenTitle: { fontSize: 26, lineHeight: 31, fontWeight: "800" as const },
  displayNumber: { fontSize: 50, lineHeight: 54, fontWeight: "800" as const }
} as const;

export const shadows = {
  sheet: {
    shadowColor: "#000000",
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: -6 },
    elevation: 5
  }
} as const;
