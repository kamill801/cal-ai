import { useState } from "react";
import { KeyboardAvoidingView, Linking, Modal, Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { getApiBaseUrl } from "../api/config";
import { TrustBuddy } from "../components/TrustBuddy";
import type { RequestStatus } from "../flow/scanToSaveFlow";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function SafetyPrivacyScreen({ onBack, onSignOut, onDeleteData, onDeleteAccount, hasProfile = true, accountDeletionPending = false, deletionStatus, deletionError }: { readonly onBack?: () => void; readonly onSignOut?: () => void; readonly onDeleteData: () => void; readonly onDeleteAccount?: () => void; readonly hasProfile?: boolean; readonly accountDeletionPending?: boolean; readonly deletionStatus: RequestStatus; readonly deletionError?: string }) {
  const isDeleting = deletionStatus === "loading";
  const [confirmation, setConfirmation] = useState<"profile" | "account">();
  const [confirmationText, setConfirmationText] = useState("");
  const [linkError, setLinkError] = useState<string>();

  function confirmDeletion(kind: "profile" | "account"): void {
    setConfirmationText("");
    setConfirmation(kind);
  }

  function submitDeletion(): void {
    if (isDeleting || !confirmation || (confirmation === "account" && confirmationText !== "탈퇴")) return;
    const action = confirmation === "account" ? onDeleteAccount : onDeleteData;
    setConfirmation(undefined);
    setConfirmationText("");
    action?.();
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
        <ChecklistItem title="건강 기록" body="목표, 식사, 운동, 체중과 회복 기록은 목표 계산과 코칭에 사용해요. 일부 기능 이용 기록은 서비스 이용 현황과 오류 확인에도 사용되며 계정과 연결될 수 있어요." />
        <ChecklistItem title="신체 사진" body="신체 체크인 사진은 별도로 동의한 뒤 선택해서 전송해요. 신원, 질환, 외모 점수를 추정하지 않으며, 현재 제공되는 관찰이 실제 AI 분석인지 모의 결과인지 확인할 수 있어요." />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>보관과 삭제</Text>
        <ChecklistItem title="비공개 보관" body="원본 사진은 공개 주소로 노출하지 않고 앱의 기록과 연결해서 보관해요." />
        <ChecklistItem title="내가 직접 삭제" body="아래에서 현재 프로필의 기록과 연결된 사진 삭제를 요청할 수 있어요. 계정 전체 탈퇴는 별도이며, 외부 저장소 정리에는 재시도와 시간이 필요할 수 있어요." />
        <ChecklistItem title="민감한 추정 제한" body="사진으로 질환, 신원, 외모 점수 같은 민감한 정보를 추정하지 않아요." />
      </View>

      <View style={styles.notice}>
        <Text style={styles.noticeText}>이 앱은 의료 진단이나 치료 목적이 아니며, 칼로리와 영양 추정은 참고용입니다.</Text>
      </View>
      <View style={styles.links}>
        {[["/privacy", "개인정보처리방침"], ["/terms", "이용약관"], ["/support", "문의"]].map(([path, label]) => (
          <TouchableOpacity key={path} style={styles.linkButton} accessibilityRole="link" onPress={() => { void Linking.openURL(`${getApiBaseUrl()}${path}`).catch(() => setLinkError("안내 페이지를 열지 못했어요.")); }}><Text style={styles.linkText}>{label}</Text></TouchableOpacity>
        ))}
      </View>
      {linkError ? <Text style={styles.errorText} accessibilityRole="alert">{linkError}</Text> : null}

      {onBack ? <TouchableOpacity activeOpacity={0.86} style={styles.primaryButton} onPress={onBack} accessibilityRole="button">
        <Text style={styles.primaryButtonText}>앱으로 돌아가기</Text>
      </TouchableOpacity> : null}
      {onSignOut ? (
        <TouchableOpacity activeOpacity={0.86} style={styles.secondaryButton} onPress={onSignOut} accessibilityRole="button">
          <Text style={styles.secondaryButtonText}>로그아웃</Text>
        </TouchableOpacity>
      ) : null}
      {hasProfile && !accountDeletionPending ? <View style={styles.dangerZone}>
        <Text style={styles.dangerTitle}>내 앱 데이터 관리</Text>
        <Text style={styles.dangerBody}>삭제하면 현재 프로필에 연결된 기록과 원본 사진이 사라지며 복구할 수 없어요.</Text>
        {deletionError ? <Text style={styles.errorText}>{deletionError}</Text> : null}
        <TouchableOpacity
          activeOpacity={0.86}
          style={[styles.deleteButton, isDeleting && styles.buttonDisabled]}
          disabled={isDeleting}
          onPress={() => confirmDeletion("profile")}
          accessibilityRole="button"
          accessibilityState={{ disabled: isDeleting, busy: isDeleting }}
        >
          <Text style={styles.deleteButtonText}>{isDeleting ? "삭제 중" : "내 앱 데이터 모두 삭제"}</Text>
        </TouchableOpacity>
      </View> : null}
      {onDeleteAccount ? <View style={styles.dangerZone}>
        <Text style={styles.dangerTitle}>계정 탈퇴</Text>
        <Text style={styles.dangerBody}>{accountDeletionPending ? "계정 삭제가 접수되어 새 기록 작성은 차단됐어요. 서버에서 삭제를 계속 진행하며, 로그인 계정이 사라져도 사진 정리는 진행 중일 수 있어요." : "로그인 계정과 모든 프로필의 기록·사진 삭제를 요청해요. 접수와 완료는 다르며, 외부 사진 정리에는 시간이 필요할 수 있어요. 삭제한 데이터는 복구할 수 없고 카카오 계정 자체는 삭제되지 않아요."}</Text>
        {deletionError ? <Text style={styles.errorText} accessibilityRole="alert">{deletionError}</Text> : null}
        <TouchableOpacity style={[styles.deleteButton, isDeleting && styles.buttonDisabled]} onPress={() => confirmDeletion("account")} disabled={isDeleting} accessibilityRole="button" accessibilityState={{ disabled: isDeleting, busy: isDeleting }}>
          <Text style={styles.deleteButtonText}>{isDeleting ? "삭제 중" : accountDeletionPending ? "계정 삭제 다시 시도" : "계정 탈퇴"}</Text>
        </TouchableOpacity>
      </View> : null}
      <Modal visible={Boolean(confirmation)} transparent animationType="fade" onRequestClose={() => setConfirmation(undefined)}>
        <KeyboardAvoidingView style={styles.modalBackdrop} behavior={Platform.OS === "ios" ? "padding" : undefined}>
          <ScrollView style={styles.modalScroll} contentContainerStyle={styles.modal} keyboardShouldPersistTaps="handled" accessibilityViewIsModal>
            <Text style={styles.sectionTitle} accessibilityRole="header">{confirmation === "account" ? "계정과 모든 기록을 삭제할까요?" : "현재 프로필의 기록을 삭제할까요?"}</Text>
            <Text style={styles.dangerBody}>{confirmation === "account" ? "로그인 계정, 모든 앱 기록과 사진이 삭제됩니다. 되돌릴 수 없어요. 계속하려면 ‘탈퇴’를 입력해 주세요." : "현재 프로필의 식사, 운동, 체중, 회복 기록과 연결된 사진이 삭제됩니다. 이 작업은 되돌릴 수 없어요. 로그인 계정은 유지됩니다."}</Text>
            {confirmation === "account" ? <TextInput style={styles.confirmationInput} value={confirmationText} onChangeText={setConfirmationText} placeholder="탈퇴" accessibilityLabel="계정 탈퇴 확인 입력" autoCorrect={false} autoCapitalize="none" /> : null}
            <TouchableOpacity style={[styles.deleteButton, (isDeleting || (confirmation === "account" && confirmationText !== "탈퇴")) && styles.buttonDisabled]} onPress={submitDeletion} disabled={isDeleting || (confirmation === "account" && confirmationText !== "탈퇴")} accessibilityRole="button"><Text style={styles.deleteButtonText}>삭제 확인</Text></TouchableOpacity>
            <TouchableOpacity style={styles.secondaryButton} onPress={() => setConfirmation(undefined)} accessibilityRole="button"><Text style={styles.secondaryButtonText}>취소</Text></TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
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
  buttonDisabled: { opacity: 0.5 },
  links: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  linkButton: { minHeight: 44, justifyContent: "center", paddingHorizontal: spacing.sm },
  linkText: { color: colors.leaf, textDecorationLine: "underline", ...typography.caption },
  modalBackdrop: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.lg, backgroundColor: "rgba(0,0,0,0.45)" },
  modalScroll: { flexGrow: 0, width: "100%", maxWidth: 440, maxHeight: "100%", backgroundColor: colors.surface, borderRadius: radii.card },
  modal: { padding: spacing.lg, gap: spacing.md },
  confirmationInput: { minHeight: 52, borderColor: colors.hairline, borderWidth: 1, borderRadius: radii.control, paddingHorizontal: spacing.md, color: colors.ink, ...typography.body }
});
