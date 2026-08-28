import type { WeeklyCoachReport } from "@cal-ai/shared";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { CoachCard } from "../components/CoachCard";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, spacing, typography } from "../theme";

export function WeeklyCoachScreen({ report, status, error }: { readonly report?: WeeklyCoachReport; readonly status: RequestStatus; readonly error?: FlowError }) {
  const evidenceCount = report ? report.evidence.mealsLogged + report.evidence.workoutsCompleted + report.evidence.weightLogs + report.evidence.wellnessCheckIns + report.evidence.bodyCheckIns : 0;
  const hasEvidence = evidenceCount > 0;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>이번 주 코치</Text>
          <Text style={styles.title}>{hasEvidence ? "이번 주 결론부터 간단히 볼게요" : "기록이 쌓이면 함께 돌아봐요"}</Text>
          <Text style={styles.subtitle}>식사, 운동, 체중, 회복 기록을 함께 보고 다음 주에 바꿀 한두 가지만 골라요.</Text>
        </View>
        <TrustBuddy size={104} pose="coach" />
      </View>
      {error ? <FlowStatusCard error={error} /> : null}
      {status === "loading" && !report ? <CoachCard title="이번 주 기록을 정리하고 있어요" eyebrow="잠시만요"><Text style={styles.body}>반복된 패턴과 회복 신호를 함께 확인해요.</Text></CoachCard> : null}
      {report && hasEvidence ? (
        <>
          <CoachCard title={report.headline} eyebrow={`이번 주 균형 점수 ${report.score}점`} tone="leaf">
            <View style={styles.scoreTrack} accessible accessibilityRole="progressbar" accessibilityLabel="이번 주 균형 점수" accessibilityValue={{ min: 0, max: 100, now: report.score }}><View style={[styles.scoreFill, { width: `${report.score}%` }]} /></View>
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
      {report && !hasEvidence ? (
        <CoachCard title="아직 평가할 기록이 부족해요" eyebrow="점수 대신 다음 행동" tone="warm">
          <Text style={styles.body}>식사 한 번 또는 운동 한 번만 기록해도 이번 주 패턴을 설명할 근거가 생겨요.</Text>
          <View style={styles.emptySteps}>
            <Text style={styles.listItem}>1. 오늘 먹은 식사 한 장 기록하기</Text>
            <Text style={styles.listItem}>2. 운동한 날 완료 기록 남기기</Text>
          </View>
        </CoachCard>
      ) : null}
      {!report && status !== "loading" && !error ? (
        <CoachCard title="이번 주 기록을 불러오면 여기에 보여드려요" eyebrow="주간 요약">
          <Text style={styles.body}>식사, 운동, 체중, 회복 기록을 바탕으로 다음 주에 바꿀 행동을 한두 개만 골라드려요.</Text>
        </CoachCard>
      ) : null}
    </ScrollView>
  );
}

function Evidence({ label, value }: { readonly label: string; readonly value: number }) {
  return <View style={styles.evidence} accessible accessibilityLabel={`${label} 기록 ${value}개`}><Text style={styles.evidenceValue}>{value}</Text><Text style={styles.evidenceLabel}>{label}</Text></View>;
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
  emptySteps: { gap: spacing.sm },
  actionRow: { alignItems: "center", flexDirection: "row", gap: spacing.md, borderTopColor: colors.hairline, borderTopWidth: 1, paddingTop: spacing.md },
  actionNumber: { width: 30, height: 30, alignItems: "center", justifyContent: "center", borderRadius: radii.pill, backgroundColor: colors.leafTint },
  actionNumberText: { color: colors.leaf, ...typography.caption },
  actionText: { flex: 1, minWidth: 0, color: colors.ink, ...typography.bodyStrong },
  safety: { color: colors.muted, ...typography.caption }
});
