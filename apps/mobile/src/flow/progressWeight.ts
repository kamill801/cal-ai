import type { ProgressWeightPoint } from "@cal-ai/shared";

const DAY_MS = 86_400_000;
const AXIS_STEPS = [0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100];

export type WeightRange = "twoWeeks" | "month";
type DatedWeightPoint = ProgressWeightPoint & { day: number };

export function getWeightTrend(history: readonly ProgressWeightPoint[] | undefined, range: WeightRange, now: Date) {
  const year = now.getFullYear();
  const month = now.getMonth();
  const date = now.getDate();
  const endDay = Date.UTC(year, month, date) / DAY_MS;
  const lastDayOfPreviousMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const startDay = range === "twoWeeks"
    ? endDay - 13
    : Date.UTC(year, month - 1, Math.min(date, lastDayOfPreviousMonth)) / DAY_MS + 1;

  const byDay = new Map<number, DatedWeightPoint>();
  for (const point of history ?? []) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(point.loggedOn) || !Number.isFinite(point.weightKg) || point.weightKg < 30 || point.weightKg > 250) {
      continue;
    }
    const utcDate = new Date(`${point.loggedOn}T00:00:00.000Z`);
    const day = utcDate.getTime() / DAY_MS;
    if (Number.isFinite(day) && day <= endDay && utcDate.toISOString().slice(0, 10) === point.loggedOn) {
      byDay.set(day, { ...point, day });
    }
  }
  const records = [...byDay.values()].sort((left, right) => left.day - right.day);
  const points = records.filter(({ day }) => day >= startDay);
  const latest = records.at(-1);
  const change = points.length > 1 && latest ? latest.weightKg - points[0].weightKg : undefined;
  return { records, points, startDay, endDay, latest, change };
}

export function weightAxis(weights: readonly number[]): number[] {
  const min = Math.min(...weights);
  const max = Math.max(...weights);
  const padding = Math.max((max - min) * 0.1, 0.15);
  const step = AXIS_STEPS.find((candidate) => Math.ceil((max + padding) / candidate) - Math.floor((min - padding) / candidate) <= 4) ?? 100;
  const bottomTick = Math.min(Math.floor((min - padding) / step), Math.max(Math.ceil((max + padding) / step) - 4, Math.floor((min + max) / 2 / step) - 2));
  return Array.from({ length: 5 }, (_, index) => (bottomTick + 4 - index) * step);
}

export function weightDateLabel(day: number, format: "axis" | "recent" | "full"): string {
  const date = new Date(day * DAY_MS);
  const month = date.getUTCMonth() + 1;
  const monthDay = date.getUTCDate();
  if (format === "axis") return `${month}.${monthDay}`;
  const label = `${month}월 ${monthDay}일`;
  return format === "full" ? `${date.getUTCFullYear()}년 ${label}` : label;
}

export function parseWeightInput(input: string): number | undefined {
  const normalized = input.trim().replace(",", ".");
  if (!/^\d+(?:\.\d*)?$/.test(normalized)) return undefined;
  const value = Number(normalized);
  return value >= 30 && value <= 250 ? value : undefined;
}
