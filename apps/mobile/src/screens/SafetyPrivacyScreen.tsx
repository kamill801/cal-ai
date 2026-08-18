import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { TrustBuddy } from "../components/TrustBuddy";
import type { RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function SafetyPrivacyScreen({ onBack, onSignOut, onDeleteData, deletionStatus, deletionError }: { readonly onBack: () => void; readonly onSignOut?: () => void; readonly onDeleteData: () => void; readonly deletionStatus: RequestStatus; readonly deletionError?: string }) {
  const isDeleting = deletionStatus === "loading";

  function confirmDeletion(): void {
    Alert.alert(
      "앱 데이터를 모두 삭제할까요?",
      "식사, 운동, 체중, 회복 기록과 저장된 사진이 삭제됩니다. 이 작업은 되돌릴 수 없어요.",
      [
        { text: "취소", style: "cancel" },
        { text: "모두 삭제", style: "destructive", onPress: onDeleteData }
      ]
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>개인정보와 안전</Text>
          <Text style={styles.title}>출시 전 안전 체크</Text>
          <Text style={styles.subtitle}>사진은 비공개 저장소를 사용하고, 사용자는 앱 기록과 연결된 원본 사진을 직접 삭제할 수 있어요.</Text>
        </View>
        <TrustBuddy size={68} accessory="sprout" />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>현재 연결된 것</Text>
        <ChecklistItem title="음식 사진 업로드" body="앱이 API에서 presigned URL을 받고 Cloudflare R2 private bucket에 직접 업로드해요." />
        <ChecklistItem title="음식 분석 결과" body="운영 API가 OpenAI 모드일 때 음식 사진을 범위와 근거 중심으로 분석해요. 결과는 추정치이며 한 번의 확인으로 보정할 수 있어요." />
        <ChecklistItem title="신체 사진 분석" body="명시적으로 동의한 사진만 제한된 자세·운동 초점 관찰에 사용해요. 운영 provider를 켜기 전에는 안전한 mock 결과를 사용해요." />
        <ChecklistItem title="저장소" body="Vercel API, Neon Postgres, Cloudflare R2 private bucket을 사용해요." />
        <ChecklistItem title="내 앱 데이터 삭제" body="식사, 운동, 체중, 회복, 신체 사진 기록과 연결된 원본 이미지를 한 번에 삭제할 수 있어요." />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>출시 전 승인 필요</Text>
        <ChecklistItem title="카카오 로그인 활성화" body="Supabase Auth와 Kakao 앱을 연결하고 운영 API의 JWT 검증 설정을 켜야 해요." />
        <ChecklistItem title="신체 사진 AI 운영 승인" body="전송 범위와 보관 기간을 고지한 뒤 BODY_AI_PROVIDER를 별도로 켜야 해요." />
        <ChecklistItem title="보관 기간 자동 집행" body="사진 TTL과 매일 실행되는 cleanup 경로는 준비됐어요. 운영 CRON_SECRET 등록과 공개 개인정보 처리방침 연결을 확인해야 해요." />
        <ChecklistItem title="로그인 계정 자체 삭제" body="앱 데이터 삭제와 별개로 Supabase 로그인 계정 제거를 위한 운영 함수와 재인증 절차가 필요해요." />
      </View>

      <View style={styles.notice}>
        <Text style={styles.noticeText}>이 앱은 의료 진단이나 치료 목적이 아니며, 칼로리와 영양 추정은 참고용입니다.</Text>
      </View>

      <TouchableOpacity activeOpacity={0.86} style={styles.primaryButton} onPress={onBack} accessibilityRole="button">
        <Text style={styles.primaryButtonText}>대시보드로 돌아가기</Text>
      </TouchableOpacity>
      {onSignOut ? (
        <TouchableOpacity activeOpacity={0.86} style={styles.secondaryButton} onPress={onSignOut} accessibilityRole="button">
          <Text style={styles.secondaryButtonText}>로그아웃</Text>
        </TouchableOpacity>
      ) : null}
      <View style={styles.dangerZone}>
        <Text style={styles.dangerTitle}>내 앱 데이터 관리</Text>
        <Text style={styles.dangerBody}>삭제하면 현재 프로필에 연결된 기록과 원본 사진이 사라지며 복구할 수 없어요.</Text>
        {deletionError ? <Text style={styles.errorText}>{deletionError}</Text> : null}
        <TouchableOpacity
          activeOpacity={0.86}
          style={[styles.deleteButton, isDeleting && styles.buttonDisabled]}
          disabled={isDeleting}
          onPress={confirmDeletion}
          accessibilityRole="button"
          accessibilityState={{ disabled: isDeleting, busy: isDeleting }}
        >
          <Text style={styles.deleteButtonText}>{isDeleting ? "삭제 중" : "내 앱 데이터 모두 삭제"}</Text>
        </TouchableOpacity>
      </View>
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
  primaryButtonText: { color: colors.surface, fontSize: 16, lineHeight: 21, fontWeight: "800" },
  secondaryButton: { alignItems: "center", justifyContent: "center", minHeight: 52, borderColor: colors.hairline, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.md },
  secondaryButtonText: { color: colors.ink, ...typography.bodyStrong },
  dangerZone: { gap: spacing.sm, borderColor: colors.warningBorder, borderRadius: radii.card, borderWidth: 1, backgroundColor: colors.surface, padding: spacing.lg },
  dangerTitle: { color: colors.warningText, ...typography.sectionTitle },
  dangerBody: { color: colors.body, ...typography.body },
  errorText: { color: colors.warningText, ...typography.caption },
  deleteButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderColor: colors.warningBorder, borderRadius: radii.control, borderWidth: 1, backgroundColor: colors.warningBg, padding: spacing.md },
  deleteButtonText: { color: colors.warningText, ...typography.bodyStrong },
  buttonDisabled: { opacity: 0.5 }
});
