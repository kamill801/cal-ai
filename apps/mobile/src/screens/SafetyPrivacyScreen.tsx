import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { TrustBuddy } from "../components/TrustBuddy";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function SafetyPrivacyScreen({ onBack }: { readonly onBack: () => void }) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>개인정보와 안전</Text>
          <Text style={styles.title}>출시 전 안전 체크</Text>
          <Text style={styles.subtitle}>지금 빌드는 내부 MVP 검증용입니다. 실제 출시 전에는 로그인, 삭제, 보관 기간, AI 제공자 정책을 확정해야 합니다.</Text>
        </View>
        <TrustBuddy size={68} accessory="sprout" />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>현재 연결된 것</Text>
        <ChecklistItem title="음식 사진 업로드" body="앱이 API에서 presigned URL을 받고 Cloudflare R2 private bucket에 직접 업로드해요." />
        <ChecklistItem title="음식 분석 결과" body="운영 API가 OpenAI 모드일 때 음식 사진을 범위와 근거 중심으로 분석해요. 결과는 추정치이며 한 번의 확인으로 보정할 수 있어요." />
        <ChecklistItem title="신체 사진 분석" body="현재는 내부 MVP용 제한된 mock 관찰만 제공해요. 별도 동의와 정책 검토 전에는 외부 AI로 보내지 않아요." />
        <ChecklistItem title="저장소" body="Vercel API, Neon Postgres, Cloudflare R2 private bucket을 사용해요." />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>출시 전 승인 필요</Text>
        <ChecklistItem title="로그인과 사용자별 분리" body="인증 provider와 user scoping 정책을 정해야 실제 개인 데이터로 볼 수 있어요." />
        <ChecklistItem title="신체 사진 AI 동의" body="외부 AI 분석을 도입하기 전에 전송 범위, 보관 기간, 동의 철회 방식을 확정해야 해요." />
        <ChecklistItem title="삭제/보관 정책" body="사진 TTL, 계정 삭제, 로그 삭제 정책과 API가 필요해요." />
      </View>

      <View style={styles.notice}>
        <Text style={styles.noticeText}>이 앱은 의료 진단이나 치료 목적이 아니며, 칼로리와 영양 추정은 참고용입니다.</Text>
      </View>

      <TouchableOpacity activeOpacity={0.86} style={styles.primaryButton} onPress={onBack} accessibilityRole="button">
        <Text style={styles.primaryButtonText}>대시보드로 돌아가기</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function ChecklistItem({ title, body }: { readonly title: string; readonly body: string }) {
  return (
    <View style={styles.item}>
      <View style={styles.dot} />
      <View style={styles.itemText}>
        <Text style={styles.itemTitle}>{title}</Text>
        <Text style={styles.itemBody}>{body}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.lg, padding: spacing.lg, paddingBottom: spacing.xxl },
  header: { alignItems: "center", flexDirection: "row", gap: spacing.md, paddingTop: spacing.sm },
  headerCopy: { flex: 1, minWidth: 0, gap: spacing.xs },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.screenTitle },
  subtitle: { color: colors.body, ...typography.body },
  card: { gap: spacing.md, borderColor: colors.hairline, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.lg, ...shadows.card },
  sectionTitle: { color: colors.ink, ...typography.sectionTitle },
  item: { flexDirection: "row", gap: spacing.md },
  dot: { width: 8, height: 8, borderRadius: radii.pill, backgroundColor: colors.leaf, marginTop: 7 },
  itemText: { flex: 1, gap: spacing.xs },
  itemTitle: { color: colors.ink, ...typography.bodyStrong },
  itemBody: { color: colors.body, ...typography.body },
  notice: { borderColor: colors.warningBorder, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.warningBg, padding: spacing.lg, ...shadows.card },
  noticeText: { color: colors.warningText, ...typography.body },
  primaryButton: { alignItems: "center", justifyContent: "center", minHeight: 58, borderRadius: radii.control, backgroundColor: colors.leaf, padding: spacing.md, ...shadows.card },
  primaryButtonText: { color: colors.surface, fontSize: 16, lineHeight: 21, fontWeight: "800" }
});
