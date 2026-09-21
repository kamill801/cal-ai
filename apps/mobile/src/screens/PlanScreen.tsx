import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CoachCard } from "../components/CoachCard";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function PlanScreen({
  onBack,
  onCheckout,
  configured,
  loading,
  error,
  statusMessage
}: {
  readonly onBack: () => void;
  readonly onCheckout: () => void;
  readonly configured: boolean;
  readonly loading: boolean;
  readonly error?: string;
  readonly statusMessage?: string;
}) {
  const checkoutDisabled = loading || !configured;
  const actionLabel = configured ? "Pro 결제 시작" : "결제 준비 중";
  const checkoutMessage = statusMessage ?? "현재 앱은 무료 베타 상태예요. 실제 결제 연결이 끝나기 전까지는 체크아웃을 시작하지 않아요.";

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <TouchableOpacity style={styles.backButton} onPress={onBack} activeOpacity={0.84} accessibilityRole="button" accessibilityLabel="이전 화면으로 돌아가기">
        <Text style={styles.backText}>← 돌아가기</Text>
      </TouchableOpacity>

      <View style={styles.hero}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>무료 베타</Text>
        </View>
        <Text style={styles.title}>Cal AI는 지금 무료로 다듬는 중이에요</Text>
        <Text style={styles.subtitle}>식사 분석, 운동 계획, 주간 코칭을 먼저 안정적으로 만들고 있어요. 결제 화면은 준비된 뒤에만 열어둘게요.</Text>
      </View>

      <CoachCard title="현재 포함된 베타 기능" eyebrow="오늘 바로 사용">
        <View style={styles.featureList}>
          <PlanFeature title="사진 기반 식사 분석" description="칼로리와 매크로 범위를 근거와 함께 보여줘요." />
          <PlanFeature title="기록 기반 코칭" description="식사, 체중, 운동, 회복 기록을 함께 보고 다음 행동을 좁혀요." />
          <PlanFeature title="운동 계획과 완료 기록" description="현재 프로필에 맞춘 루틴을 만들고 세트 완료를 남길 수 있어요." />
        </View>
      </CoachCard>

      <CoachCard title="나중에 Pro로 옮겨갈 수 있는 것" eyebrow="준비 중" tone="leaf">
        <View style={styles.featureList}>
          <PlanFeature title="더 깊은 주간 리포트" description="반복 패턴, 정체 구간, 회복 신호를 더 길게 추적해요." />
          <PlanFeature title="고급 진행 분석" description="사진, 체중, 수행 기록을 묶어 변화의 근거를 더 촘촘히 보여줘요." />
          <PlanFeature title="우선 개선 제안" description="기록이 적은 날에도 가장 영향 큰 한 가지를 먼저 골라줘요." />
        </View>
      </CoachCard>

      <View style={styles.checkoutPanel}>
        <Text style={styles.checkoutTitle}>결제는 아직 닫혀 있어요</Text>
        <Text style={styles.checkoutMessage}>{checkoutMessage}</Text>
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
        <TouchableOpacity
          style={[styles.checkoutButton, checkoutDisabled && styles.checkoutButtonDisabled]}
          onPress={onCheckout}
          disabled={checkoutDisabled}
          activeOpacity={0.84}
          accessibilityRole="button"
          accessibilityState={{ disabled: checkoutDisabled, busy: loading }}
        >
          {loading ? <ActivityIndicator color={colors.surface} /> : <Text style={styles.checkoutButtonText}>{actionLabel}</Text>}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

function PlanFeature({ title, description }: { readonly title: string; readonly description: string }) {
  return (
    <View style={styles.featureRow}>
      <View style={styles.featureDot} />
      <View style={styles.featureCopy}>
        <Text style={styles.featureTitle}>{title}</Text>
        <Text style={styles.featureDescription}>{description}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.lg, padding: spacing.lg, paddingBottom: 112 },
  backButton: { alignSelf: "flex-start", borderRadius: radii.control, paddingVertical: spacing.sm },
  backText: { color: colors.leaf, ...typography.bodyStrong },
  hero: { gap: spacing.md, borderColor: colors.creamDeep, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.cream, padding: spacing.xl, ...shadows.card },
  badge: { alignSelf: "flex-start", borderRadius: radii.pill, backgroundColor: colors.leaf, paddingHorizontal: spacing.md, paddingVertical: spacing.xs },
  badgeText: { color: colors.surface, ...typography.caption },
  title: { color: colors.ink, ...typography.heroTitle },
  subtitle: { color: colors.body, ...typography.body },
  featureList: { gap: spacing.md },
  featureRow: { flexDirection: "row", gap: spacing.md },
  featureDot: { marginTop: 7, width: 8, height: 8, borderRadius: radii.pill, backgroundColor: colors.leaf },
  featureCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  featureTitle: { color: colors.ink, ...typography.bodyStrong },
  featureDescription: { color: colors.body, ...typography.body },
  checkoutPanel: { gap: spacing.md, borderColor: colors.hairline, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.lg },
  checkoutTitle: { color: colors.ink, ...typography.sectionTitle },
  checkoutMessage: { color: colors.body, ...typography.body },
  errorText: { color: colors.danger, ...typography.caption },
  checkoutButton: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.black, paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
  checkoutButtonDisabled: { backgroundColor: colors.mutedSoft },
  checkoutButtonText: { color: colors.surface, fontSize: 15, lineHeight: 20, fontWeight: "800" }
});
