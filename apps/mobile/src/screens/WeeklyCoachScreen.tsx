import type { WeeklyCoachReport } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { CoachCard } from "../components/CoachCard";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, spacing, typography } from "../theme";

export function WeeklyCoachScreen({ report, status, error }: { readonly report?: WeeklyCoachReport; readonly status: RequestStatus; readonly error?: FlowError }) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>WEEKLY COACH</Text>
          <Text style={styles.title}>결과는 전문적으로, 다음 행동은 가볍게</Text>
          <Text style={styles.subtitle}>식사, 운동, 체중, 회복 기록을 함께 보고 다음 주에 바꿀 한두 가지만 골라요.</Text>
        </View>
        <TrustBuddy size={68} accessory="spoon" />
      </View>
      {error ? <FlowStatusCard error={error} /> : null}
      {status === "loading" && !report ? <CoachCard title="이번 주 기록을 정리하고 있어요" eyebrow="잠시만요"><Text style={styles.body}>반복된 패턴과 회복 신호를 함께 확인해요.</Text></CoachCard> : null}
      {report ? (
        <>
          <CoachCard title={report.headline} eyebrow={`이번 주 균형 점수 ${report.score}점`} tone="leaf">
            <View style={styles.scoreTrack}><View style={[styles.scoreFill, { width: `${report.score}%` }]} /></View>
            <View style={styles.evidenceRow}>
              <Evidence label="식사" value={report.evidence.mealsLogged} />
              <Evidence label="운동" value={report.evidence.workoutsCompleted} />
              <Evidence label="체중" value={report.evidence.weightLogs} />
              <Evidence label="회복" value={report.evidence.wellnessCheckIns} />
            </View>
          </CoachCard>
          <CoachCard title="잘한 점" eyebrow="유지할 것">
            {report.wins.map((item) => <Text key={item} style={styles.listItem}>• {item}</Text>)}
          </CoachCard>
          <CoachCard title="이번 주 초점" eyebrow="한 번에 많이 바꾸지 않기" tone="warm">
            {report.focusItems.map((item) => <Text key={item} style={styles.listItem}>• {item}</Text>)}
          </CoachCard>
          <CoachCard title="다음 주 세 가지" eyebrow="실행 계획">
            {report.nextWeekActions.map((item, index) => (
              <View key={item} style={styles.actionRow}><View style={styles.actionNumber}><Text style={styles.actionNumberText}>{index + 1}</Text></View><Text style={styles.actionText}>{item}</Text></View>
            ))}
            <Text style={styles.safety}>{report.safetyNote}</Text>
          </CoachCard>
        </>
      ) : null}
    </ScrollView>
  );
}

function Evidence({ label, value }: { readonly label: string; readonly value: number }) {
  return <View style={styles.evidence}><Text style={styles.evidenceValue}>{value}</Text><Text style={styles.evidenceLabel}>{label}</Text></View>;
}

const styles = StyleSheet.create({
  container: { gap: spacing.lg, padding: spacing.lg, paddingBottom: 112 },
  header: { alignItems: "center", flexDirection: "row", gap: spacing.md, paddingTop: spacing.sm },
  headerCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.screenTitle },
  subtitle: { color: colors.body, ...typography.body },
  body: { color: colors.body, ...typography.body },
  scoreTrack: { height: 12, overflow: "hidden", borderRadius: radii.pill, backgroundColor: colors.leafMuted },
  scoreFill: { height: "100%", borderRadius: radii.pill, backgroundColor: colors.leaf },
  evidenceRow: { flexDirection: "row", gap: spacing.sm },
  evidence: { flex: 1, minWidth: 0, alignItems: "center", gap: spacing.xs },
  evidenceValue: { color: colors.ink, fontSize: 20, lineHeight: 24, fontWeight: "800" },
  evidenceLabel: { color: colors.muted, ...typography.caption },
  listItem: { color: colors.body, ...typography.body },
  actionRow: { alignItems: "center", flexDirection: "row", gap: spacing.md, borderTopColor: colors.hairline, borderTopWidth: 1, paddingTop: spacing.md },
  actionNumber: { width: 30, height: 30, alignItems: "center", justifyContent: "center", borderRadius: radii.pill, backgroundColor: colors.leafTint },
  actionNumberText: { color: colors.leaf, ...typography.caption },
  actionText: { flex: 1, minWidth: 0, color: colors.ink, ...typography.bodyStrong },
  safety: { color: colors.muted, ...typography.caption }
});
