import { Check } from "lucide-react-native";
import { useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { TrustBuddy } from "../components/TrustBuddy";
import type { RequestStatus } from "../flow/scanToSaveFlow";
import { colors, spacing, typography } from "../theme";

export function ConsentCheckbox({ label, checked, disabled = false, onChange }: {
  readonly label: string; readonly checked: boolean; readonly disabled?: boolean; readonly onChange: () => void;
}) {
  return <TouchableOpacity style={styles.checkboxRow} onPress={onChange} disabled={disabled}
    accessibilityRole="checkbox" accessibilityLabel={label} accessibilityState={{ checked, disabled }}>
    <View style={[styles.checkbox, checked && styles.checked]}>{checked ? <Check size={17} color={colors.surface} /> : null}</View>
    <Text style={styles.checkboxLabel}>{label}</Text>
  </TouchableOpacity>;
}

export function PrivacyConsentScreen({ policyVersion, status, error, onSubmit, onRetry, onManage, onSignOut }: {
  readonly policyVersion?: string; readonly status: RequestStatus; readonly error?: string;
  readonly onSubmit: (analyticsConsent: boolean) => void; readonly onRetry: () => void;
  readonly onManage: () => void; readonly onSignOut?: () => void;
}) {
  const [healthConsent, setHealthConsent] = useState(false);
  const [analyticsConsent, setAnalyticsConsent] = useState(false);
  const loading = status === "loading";
  const disabled = loading || !policyVersion || !healthConsent;
  return <ScrollView contentContainerStyle={styles.container}>
    <View style={styles.header}>
      <View style={styles.copy}><Text style={styles.eyebrow}>개인정보 사용 안내</Text>
        <Text style={styles.title}>기록 전에 확인해 주세요</Text></View>
      <TrustBuddy size={88} pose="coach" />
    </View>
    <Text style={styles.sectionTitle}>건강·운동 기록의 저장과 사용</Text>
    <Text style={styles.body}>입력한 나이, 성별, 키, 체중, 목표와 운동 정보는 앱 서버에 전송·저장하고, 영양 목표 계산과 맞춤 운동·코칭에 사용해요. 이후 저장한 식사·체중·회복·운동 기록도 계정에 연결해 사용해요.</Text>
    <Text style={styles.body}>음식 사진은 선택 사항이에요. 선택한 사진은 비공개 저장소에 보관하고 음식·영양 분석을 위해 OpenAI에 전송해요. 신체 사진은 별도로 동의한 뒤 선택하며, 현재 신체 관찰은 모의 결과예요.</Text>
    <Text style={styles.body}>건강 기록 사용에 동의하지 않으면 기록 기능을 시작하지 않아요. 개인정보 안내, 문의, 계정 삭제와 로그아웃은 동의 없이도 이용할 수 있어요.</Text>
    <ConsentCheckbox label="건강·운동 정보의 서버 전송·저장과 목표 계산·코칭 사용에 동의합니다 (기록 기능 이용 시 필요)"
      checked={healthConsent} disabled={loading || !policyVersion} onChange={() => setHealthConsent((value) => !value)} />
    <View style={styles.analytics}>
      <Text style={styles.sectionTitle}>서비스 이용 분석 (선택)</Text>
      <Text style={styles.body}>동의하면 화면·기능 이용, 오류 코드와 접속 시각을 서버로 보내 이용 현황을 확인해요. 계정·프로필·접속 세션과 연결될 수 있어요. 건강 입력값과 사진 내용은 분석 속성으로 보내지 않아요. 거절해도 기록 기능을 이용할 수 있고, 개인정보와 계정 관리에서 언제든 철회할 수 있어요.</Text>
      <ConsentCheckbox label="서비스 이용 분석에 동의합니다 (선택)" checked={analyticsConsent}
        disabled={loading || !policyVersion} onChange={() => setAnalyticsConsent((value) => !value)} />
    </View>
    {policyVersion ? <Text style={styles.version}>안내 버전 {policyVersion}</Text> : null}
    {loading ? <View style={styles.loading} accessibilityRole="progressbar" accessibilityLabel="동의 상태 처리 중"><ActivityIndicator color={colors.leaf} /><Text style={styles.body}>동의 상태를 확인하고 있어요</Text></View> : null}
    {error ? <Text style={styles.error} accessibilityRole="alert">{error}</Text> : null}
    <TouchableOpacity style={[styles.primary, disabled && styles.disabled]} disabled={disabled}
      accessibilityRole="button" accessibilityLabel="선택한 동의 저장 후 계속" accessibilityState={{ disabled, busy: loading }}
      onPress={() => { if (!disabled) onSubmit(analyticsConsent); }}><Text style={styles.primaryText}>동의하고 계속</Text></TouchableOpacity>
    {error || !policyVersion ? <TouchableOpacity style={styles.secondary} onPress={onRetry} disabled={loading}
      accessibilityRole="button" accessibilityState={{ disabled: loading }}><Text style={styles.link}>동의 상태 다시 시도</Text></TouchableOpacity> : null}
    <TouchableOpacity style={styles.secondary} onPress={onManage} accessibilityRole="button"><Text style={styles.link}>개인정보 안내 · 문의 · 계정 삭제</Text></TouchableOpacity>
    {onSignOut ? <TouchableOpacity style={styles.secondary} onPress={onSignOut} accessibilityRole="button"><Text style={styles.link}>로그아웃</Text></TouchableOpacity> : null}
  </ScrollView>;
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: spacing.xl, paddingBottom: 40, gap: spacing.lg, width: "100%", maxWidth: 560, alignSelf: "center" },
  header: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  copy: { flex: 1, minWidth: 0, gap: spacing.sm },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.screenTitle },
  sectionTitle: { color: colors.ink, ...typography.sectionTitle },
  body: { color: colors.body, ...typography.body },
  analytics: { borderTopWidth: 1, borderTopColor: colors.hairline, paddingTop: spacing.lg, gap: spacing.md },
  checkboxRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.md, minHeight: 48, paddingVertical: spacing.sm },
  checkbox: { height: 24, width: 24, borderWidth: 2, borderColor: colors.leaf, borderRadius: 4, alignItems: "center", justifyContent: "center", flexShrink: 0 },
  checked: { backgroundColor: colors.leaf },
  checkboxLabel: { flex: 1, minWidth: 0, color: colors.ink, ...typography.bodyStrong },
  primary: { minHeight: 52, justifyContent: "center", alignItems: "center", padding: spacing.md, backgroundColor: colors.leaf, borderRadius: 8 },
  primaryText: { color: colors.surface, ...typography.bodyStrong, textAlign: "center" },
  secondary: { minHeight: 44, justifyContent: "center", alignItems: "center", padding: spacing.sm },
  link: { color: colors.leaf, ...typography.bodyStrong, textAlign: "center" },
  version: { color: colors.muted, ...typography.caption },
  error: { color: colors.danger, ...typography.body },
  loading: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  disabled: { opacity: 0.46 }
});
