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
          <Text style={styles.title}>내 기록은 이렇게 다뤄요</Text>
          <Text style={styles.subtitle}>사진과 건강 기록을 왜 사용하는지, 어디까지 분석하는지 숨기지 않고 알려드려요.</Text>
        </View>
        <TrustBuddy size={104} pose="coach" />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>사진과 기록</Text>
        <ChecklistItem title="음식 사진" body="선택한 사진은 비공개 저장소에 보관하고, 음식과 영양 범위를 분석하기 위해 OpenAI에 전송해요." />
        <ChecklistItem title="분석 결과" body="칼로리와 영양값은 사진을 바탕으로 한 추정치예요. 저장 전에 음식 이름과 영양값을 직접 확인하고 수정할 수 있어요." />
        <ChecklistItem title="건강 기록" body="목표, 식사, 운동, 체중과 회복 기록은 개인화된 오늘 목표와 주간 코칭을 만드는 데만 사용해요." />
        <ChecklistItem title="신체 사진" body="이번 베타에서는 로그인으로 사진을 보호하는 기능이 준비될 때까지 촬영과 업로드를 제공하지 않아요." />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>보관과 삭제</Text>
        <ChecklistItem title="비공개 보관" body="원본 사진은 공개 주소로 노출하지 않고 앱의 기록과 연결해서 보관해요." />
        <ChecklistItem title="내가 직접 삭제" body="아래의 ‘내 앱 데이터 모두 삭제’를 누르면 현재 프로필의 식사, 운동, 체중, 회복 기록과 연결된 원본 사진을 함께 삭제해요." />
        <ChecklistItem title="민감한 추정 제한" body="사진으로 질환, 신원, 외모 점수 같은 민감한 정보를 추정하지 않아요." />
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
