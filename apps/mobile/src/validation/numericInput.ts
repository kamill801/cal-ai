const limits = {
  weight: { min: 30, max: 250, integer: false },
  sets: { min: 0, max: 20, integer: true },
  reps: { min: 0, max: 100, integer: true },
  load: { min: 0, max: 500, integer: false },
  duration: { min: 5, max: 240, integer: true }
} as const;

type NumericInput = { status: "blank" } | { status: "invalid" } | { status: "valid"; value: number };

export function parseNumericInput(raw: string, field: keyof typeof limits): NumericInput {
  const text = raw.trim();
  if (!text) return { status: "blank" };
  if (!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(text)) return { status: "invalid" };
  const value = Number(text);
  const rule = limits[field];
  if (!Number.isFinite(value) || value < rule.min || value > rule.max || (rule.integer && !Number.isInteger(value))) {
    return { status: "invalid" };
  }
  return { status: "valid", value };
}
