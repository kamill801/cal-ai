import type { ProgressSummary } from "@cal-ai/shared";
import { List, Plus } from "lucide-react-native";
import { useState } from "react";
import { Keyboard, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { getWeightTrend, parseWeightInput, weightAxis, weightDateLabel, type WeightRange } from "../flow/progressWeight";
import { freshGreen } from "../theme";

export const progressColors = {
  paper: "#ffffff", ink: "#182222", muted: "#556462", weak: "#657372",
  line: "#e2e8e7", brand: freshGreen.ink, border: "#cadbc7", fill: freshGreen.tint, track: freshGreen.indicator, guide: "#8aae87"
} as const;

const RANGES = [{ value: "twoWeeks", label: "2주" }, { value: "month", label: "1개월" }] as const;
const CHART_HEIGHT = 213;
const Y_TOP = 21;
const Y_BOTTOM = 169;

export function ProgressWeightTrend({ progress, loading, onLogWeight }: {
  readonly progress?: ProgressSummary;
  readonly loading: boolean;
  readonly onLogWeight: (weightKg: number) => void;
}) {
  const [range, setRange] = useState<WeightRange>("twoWeeks");
  const [panel, setPanel] = useState<"record" | "history">();
  const [weight, setWeight] = useState("");
  const { records, points, latest, change, startDay, endDay } = getWeightTrend(progress?.weightHistory, range, new Date());
  const historyAvailable = progress?.weightHistory !== undefined;
  const latestWeight = latest?.weightKg ?? (!historyAvailable ? progress?.latestWeightKg : undefined);
  const parsedWeight = parseWeightInput(weight);
  const saveDisabled = loading || parsedWeight === undefined;

  function saveWeight() {
    if (loading || parsedWeight === undefined) return;
    Keyboard.dismiss();
    onLogWeight(parsedWeight);
  }

  function togglePanel(next: "record" | "history") {
    if (next === "record" && panel !== next && !weight && latestWeight !== undefined) setWeight(String(latestWeight));
    setPanel(panel === next ? undefined : next);
  }

  const emptyLabel = loading && !progress
    ? "체중 기록을 불러오는 중이에요."
    : !historyAvailable && progress
      ? "날짜별 기록을 불러올 수 없어요."
      : !progress
        ? "체중 기록을 확인할 수 없어요."
        : latest
          ? "이 기간에 기록한 체중이 없어요."
          : "아직 기록한 체중이 없어요.";

  return (
    <View style={styles.section}>
      <View style={styles.heading}>
        <Text accessibilityRole="header" style={styles.title}>체중 추세</Text>
        <View style={styles.segments} accessibilityRole="tablist" accessibilityLabel="체중 추세 기간">
          {RANGES.map(({ value, label }) => (
            <TouchableOpacity
              key={value}
              accessibilityRole="tab"
              accessibilityState={{ selected: range === value }}
              onPress={() => setRange(value)}
              style={[styles.segment, range === value && styles.segmentSelected]}
            >
              <Text style={[styles.segmentText, range === value && styles.selectedText]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {latestWeight !== undefined ? (
        <View style={styles.metric} accessible accessibilityLabel={`최근 체중 ${latestWeight.toFixed(1)}킬로그램`}>
          <Text style={styles.metricNumber}>{latestWeight.toFixed(1)}</Text>
          <Text style={styles.unit}>kg</Text>
        </View>
      ) : <Text style={styles.noMetric}>{loading && !progress ? "불러오는 중" : historyAvailable ? "기록 없음" : "기록 확인 전"}</Text>}
      {latestWeight !== undefined ? (
        <Text style={styles.caption}>
          최근 기록{latest ? ` · ${weightDateLabel(latest.day, endDay - latest.day >= 31 ? "full" : "recent")}` : ""}
          {change !== undefined ? <Text style={styles.change}> · 기간 첫 기록 대비 {formatChange(change)}kg</Text> : null}
          {!historyAvailable && progress?.weightChangeKg !== undefined
            ? <Text style={styles.change}> · 전체 첫 기록 대비 {formatChange(progress.weightChangeKg)}kg</Text>
            : null}
        </Text>
      ) : null}

      <WeightChart points={points} startDay={startDay} endDay={endDay} emptyLabel={emptyLabel} />
      <View style={styles.legend}>
        <View style={styles.legendLine} />
        <Text style={styles.caption}>기록한 체중 (kg)</Text>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity accessibilityRole="button" accessibilityState={{ expanded: panel === "record" }} onPress={() => togglePanel("record")} style={[styles.action, styles.recordAction]}>
          <Plus size={16} color={progressColors.brand} />
          <Text style={[styles.actionText, styles.selectedText]}>체중 기록</Text>
        </TouchableOpacity>
        <TouchableOpacity accessibilityRole="button" accessibilityState={{ expanded: panel === "history" }} onPress={() => togglePanel("history")} style={styles.action}>
          <List size={16} color={progressColors.muted} />
          <Text style={styles.actionText}>기록 보기</Text>
        </TouchableOpacity>
      </View>

      {panel === "record" ? (
        <View style={styles.panel}>
          <View style={styles.inputRow}>
            <TextInput
              value={weight}
              onChangeText={setWeight}
              onSubmitEditing={saveWeight}
              keyboardType="decimal-pad"
              placeholder="예: 72.0"
              placeholderTextColor={progressColors.weak}
              maxLength={10}
              style={styles.input}
              accessibilityLabel="현재 체중"
            />
            <Text style={styles.caption}>kg</Text>
            <TouchableOpacity style={[styles.saveButton, saveDisabled && styles.disabled]} disabled={saveDisabled} onPress={saveWeight} accessibilityRole="button" accessibilityState={{ disabled: saveDisabled }}>
              <Text style={styles.saveText}>{loading ? "저장 중" : "저장"}</Text>
            </TouchableOpacity>
          </View>
          {weight.trim() && parsedWeight === undefined ? <Text style={styles.caption}>30~250kg 사이로 입력해 주세요.</Text> : null}
        </View>
      ) : null}

      {panel === "history" ? (
        <View style={styles.panel}>
          <Text accessibilityRole="header" style={styles.historyTitle}>날짜별 마지막 기록</Text>
          {records.length ? [...records].reverse().map((record) => (
            <View key={record.day} style={styles.historyRow}>
              <Text style={styles.caption}>{weightDateLabel(record.day, "full")}</Text>
              <Text style={styles.historyValue}>{record.weightKg.toFixed(1)} kg</Text>
            </View>
          )) : <Text style={styles.caption}>{emptyLabel}</Text>}
        </View>
      ) : null}
    </View>
  );
}

function WeightChart({ points, startDay, endDay, emptyLabel }: {
  readonly points: ReturnType<typeof getWeightTrend>["points"];
  readonly startDay: number;
  readonly endDay: number;
  readonly emptyLabel: string;
}) {
  const [width, setWidth] = useState(0);
  const first = points[0];
  const last = points.at(-1);
  if (!first || !last) {
    return <View style={[styles.chart, styles.emptyChart]}><Text style={styles.caption}>{emptyLabel}</Text></View>;
  }

  const pointX = (day: number) => 42 + (day - startDay) / (endDay - startDay) * (width - 62);
  const ticks = weightAxis(points.map(({ weightKg }) => weightKg));
  const pointY = (weight: number) => Y_BOTTOM - (weight - ticks[4]) / (ticks[0] - ticks[4]) * (Y_BOTTOM - Y_TOP);
  const markers = points.map(({ day, weightKg }) => ({ day, x: pointX(day), y: pointY(weightKg) }));
  const xTicks = [0, 0.3, 0.6, 1].map((fraction) => startDay + Math.round(fraction * (endDay - startDay)));
  const chartLabel = `${weightDateLabel(startDay, "full")}부터 ${weightDateLabel(endDay, "full")}까지, 체중 기록 ${points.length}건. 최근 ${last.weightKg.toFixed(1)}킬로그램`;

  return (
    <View accessible accessibilityRole="image" accessibilityLabel={chartLabel} style={styles.chart} onLayout={({ nativeEvent: { layout } }) => setWidth(layout.width)}>
      {width >= 100 ? (
        <View style={StyleSheet.absoluteFill} importantForAccessibility="no-hide-descendants" accessibilityElementsHidden>
          {ticks.map((weight) => (
            <View key={weight} style={[styles.gridLine, { top: pointY(weight) }]} />
          ))}
          <View style={[styles.latestGuide, { left: pointX(last.day), top: pointY(last.weightKg), height: Y_BOTTOM - pointY(last.weightKg) }]} />
          {markers.slice(1).map(({ day, x, y }, index) => {
            const previous = markers[index];
            const dx = x - previous.x;
            const dy = y - previous.y;
            const length = Math.hypot(dx, dy);
            return <View key={day} style={[styles.plotLine, {
              left: (previous.x + x - length) / 2,
              top: (previous.y + y - 2.4) / 2,
              width: length,
              transform: [{ rotate: `${Math.atan2(dy, dx)}rad` }]
            }]} />;
          })}
          {markers.map(({ day, x, y }) => {
            const latest = day === last.day;
            const size = latest ? 12 : 7;
            return <View key={day} style={[styles.marker, latest && styles.latestMarker, {
              left: x - size / 2, top: y - size / 2, width: size, height: size, borderRadius: size / 2
            }]} />;
          })}
          {ticks.map((weight) => (
            <Text key={weight} allowFontScaling={false} style={[styles.axisLabel, styles.yLabel, { top: pointY(weight) - 7 }]}>{weight.toFixed(1)}</Text>
          ))}
          {xTicks.map((day) => (
            <Text key={day} allowFontScaling={false} style={[styles.axisLabel, styles.xLabel, { left: pointX(day) - 20 }]}>{weightDateLabel(day, "axis")}</Text>
          ))}
        </View>
      ) : null}
    </View>
  );
}

function formatChange(change: number): string {
  const value = Math.round(change * 10) / 10;
  if (value === 0) return "0.0";
  return `${value < 0 ? "−" : "+"}${Math.abs(value).toFixed(1)}`;
}

const styles = StyleSheet.create({
  section: { paddingTop: 12 },
  heading: { minHeight: 44, flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  title: { flexShrink: 1, color: progressColors.ink, fontSize: 17, fontWeight: "800" },
  segments: { flexDirection: "row", gap: 8, borderBottomWidth: 1, borderBottomColor: progressColors.line },
  segment: { minWidth: 44, minHeight: 44, justifyContent: "center", alignItems: "center", paddingHorizontal: 4, borderBottomWidth: 2, borderBottomColor: "transparent" },
  segmentSelected: { borderBottomColor: progressColors.brand },
  segmentText: { color: progressColors.weak, fontSize: 12, fontWeight: "600" },
  selectedText: { color: progressColors.brand, fontWeight: "800" },
  metric: { flexDirection: "row", flexWrap: "wrap", gap: 7, alignItems: "baseline", marginTop: 4 },
  metricNumber: { color: progressColors.ink, fontSize: 44, fontVariant: ["tabular-nums"], fontWeight: "800" },
  unit: { color: progressColors.muted, fontSize: 17, fontWeight: "700" },
  noMetric: { color: progressColors.ink, fontSize: 26, fontWeight: "800", marginTop: 8 },
  caption: { color: progressColors.muted, fontSize: 12, lineHeight: 17, fontVariant: ["tabular-nums"], flexShrink: 1 },
  change: { color: progressColors.brand, fontWeight: "700" },
  chart: { marginTop: 11, height: CHART_HEIGHT },
  gridLine: { position: "absolute", left: 36, right: 9, height: 1, backgroundColor: progressColors.line },
  latestGuide: { position: "absolute", width: 1, backgroundColor: progressColors.guide },
  plotLine: { position: "absolute", height: 2.4, borderRadius: 2, backgroundColor: progressColors.track },
  marker: { position: "absolute", borderWidth: 1.35, borderColor: progressColors.track, backgroundColor: progressColors.paper },
  latestMarker: { borderWidth: 2, borderColor: progressColors.paper, backgroundColor: progressColors.track },
  axisLabel: { position: "absolute", color: progressColors.weak, fontSize: 10, lineHeight: 14, fontWeight: "600", fontVariant: ["tabular-nums"] },
  yLabel: { left: 0, width: 29, textAlign: "right" },
  xLabel: { top: 180, width: 40, textAlign: "center" },
  emptyChart: { alignItems: "center", justifyContent: "center", borderBottomColor: progressColors.line, borderBottomWidth: 1, paddingHorizontal: 12 },
  legend: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4, marginBottom: 15 },
  legendLine: { backgroundColor: progressColors.track, height: 2, width: 10 },
  actions: { flexDirection: "row", gap: 8 },
  action: { flex: 1, minHeight: 46, flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 8, padding: 8, borderWidth: 1, borderColor: progressColors.line, borderRadius: 6 },
  recordAction: { borderColor: progressColors.border },
  actionText: { flexShrink: 1, color: progressColors.muted, fontSize: 14, fontWeight: "800", textAlign: "center" },
  panel: { gap: 8, paddingVertical: 12 },
  inputRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  input: { flex: 1, minWidth: 0, minHeight: 46, borderColor: progressColors.border, borderWidth: 1, borderRadius: 6, color: progressColors.ink, paddingHorizontal: 12, fontSize: 17, fontWeight: "700" },
  saveButton: { minHeight: 46, justifyContent: "center", alignItems: "center", borderRadius: 6, backgroundColor: freshGreen.fill, paddingHorizontal: 12 },
  saveText: { color: freshGreen.onFill, fontSize: 14, fontWeight: "800" },
  disabled: { opacity: 0.45 },
  historyTitle: { color: progressColors.ink, fontSize: 14, fontWeight: "800" },
  historyRow: { minHeight: 42, gap: 8, flexDirection: "row", justifyContent: "space-between", alignItems: "center", borderBottomWidth: 1, borderBottomColor: progressColors.line },
  historyValue: { color: progressColors.ink, fontSize: 14, fontVariant: ["tabular-nums"], fontWeight: "700" }
});
