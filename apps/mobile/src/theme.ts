export const colors = {
  ink: "#20221f",
  black: "#0a0a0a",
  body: "#3a3a3a",
  muted: "#6a6a6a",
  mutedSoft: "#9a9a9a",
  hairline: "#d8ded2",
  canvas: "#fffaf0",
  canvasWarm: "#fff8ef",
  paper: "#fbfaf6",
  surface: "#ffffff",
  surfaceSoft: "#f5f0e0",
  cream: "#fff3de",
  creamDeep: "#f2d6a8",
  leaf: "#2f6540",
  leafSoft: "#eef4ec",
  leafMuted: "#dfeade",
  leafTint: "#f4fbf0",
  skySoft: "#edf7ff",
  sky: "#4b9be8",
  protein: "#4b8397",
  proteinSoft: "#eef8fb",
  carbs: "#cc8a25",
  carbsSoft: "#fff8df",
  fat: "#d35b45",
  fatSoft: "#fff1ed",
  fiber: "#5c8f5f",
  fiberSoft: "#edf6ea",
  peach: "#ffb084",
  peachSoft: "#fff2e8",
  lavender: "#b8a4ed",
  lavenderSoft: "#f2edff",
  warningBg: "#fff8ee",
  warningBorder: "#f0d4b5",
  warningText: "#7a4e11",
  danger: "#ef4444",
  success: "#22c55e"
} as const;

export const radii = {
  card: 16,
  control: 14,
  photo: 18,
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
  heroTitle: { fontSize: 30, lineHeight: 36, fontWeight: "900" as const },
  displayNumber: { fontSize: 50, lineHeight: 54, fontWeight: "800" as const }
} as const;

export const shadows = {
  card: {
    shadowColor: "#2f2417",
    shadowOpacity: 0.07,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 3
  },
  floating: {
    shadowColor: "#2f2417",
    shadowOpacity: 0.12,
    shadowRadius: 22,
    shadowOffset: { width: 0, height: 10 },
    elevation: 6
  },
  sheet: {
    shadowColor: "#000000",
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: -6 },
    elevation: 5
  }
} as const;
