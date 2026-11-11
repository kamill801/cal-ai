import { ChevronDown, ChevronUp, Eye, EyeOff, ShieldCheck } from "lucide-react-native";
import { useState } from "react";
import { ActivityIndicator, KeyboardAvoidingView, Linking, Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { getApiBaseUrl } from "../api/config";
import { colors, radii, shadows, spacing, typography } from "../theme";

interface LoginScreenProps {
  readonly configured: boolean;
  readonly loading: boolean;
  readonly error?: string;
  readonly onKakaoLogin: () => void;
  readonly onEmailLogin: (email: string, password: string) => Promise<void>;
}

export function LoginScreen({ configured, loading, error, onKakaoLogin, onEmailLogin }: LoginScreenProps) {
  const [emailOpen, setEmailOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [linkError, setLinkError] = useState<string>();
  const disabled = !configured || loading;

  async function openNotice(path: string): Promise<void> {
    try { await Linking.openURL(`${getApiBaseUrl()}${path}`); }
    catch { setLinkError("안내 페이지를 열지 못했어요. 잠시 후 다시 시도해 주세요."); }
  }

  async function submitEmail(): Promise<void> {
    if (disabled || !email.trim() || !password) return;
    try { await onEmailLogin(email, password); }
    finally { setPassword(""); }
  }

  return (
    <KeyboardAvoidingView style={styles.root} behavior={Platform.OS === "ios" ? "padding" : undefined}>
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
    <View style={styles.content}>
      <View style={styles.brand}>
        <View style={styles.icon}><ShieldCheck color={colors.leaf} size={28} /></View>
        <Text style={styles.eyebrow}>TRUST FIRST</Text>
        <Text style={styles.title}>내 기록을 이어서{`\n`}몸의 변화를 만들어요</Text>
        <Text style={styles.subtitle}>식사, 운동, 신체 체크인을 한 계정에 안전하게 모아 매일의 다음 행동을 연결해요.</Text>
      </View>
      <View style={styles.panel}>
        <TouchableOpacity style={[styles.kakaoButton, disabled && styles.disabled]} disabled={disabled} onPress={onKakaoLogin} accessibilityRole="button" accessibilityState={{ disabled, busy: loading }}>
          {loading ? <ActivityIndicator color="#191919" /> : <Text style={styles.kakaoText}>카카오로 시작하기</Text>}
        </TouchableOpacity>
        <TouchableOpacity style={styles.emailToggle} onPress={() => setEmailOpen(!emailOpen)} disabled={loading} accessibilityRole="button" accessibilityState={{ expanded: emailOpen, disabled: loading }}>
          <Text style={styles.emailToggleText}>이메일로 로그인</Text>
          {emailOpen ? <ChevronUp color={colors.body} size={18} /> : <ChevronDown color={colors.body} size={18} />}
        </TouchableOpacity>
        {emailOpen ? (
          <View style={styles.emailFields}>
            <Text style={styles.label}>이메일</Text>
            <TextInput style={styles.input} value={email} onChangeText={setEmail} autoCapitalize="none" autoCorrect={false} keyboardType="email-address" autoComplete="email" textContentType="emailAddress" placeholder="이메일 주소" accessibilityLabel="이메일" editable={!disabled} />
            <Text style={styles.label}>비밀번호</Text>
            <View style={styles.passwordRow}>
              <TextInput style={[styles.input, styles.passwordInput]} value={password} onChangeText={setPassword} secureTextEntry={!showPassword} autoCapitalize="none" autoCorrect={false} autoComplete="current-password" textContentType="password" placeholder="비밀번호" accessibilityLabel="비밀번호" editable={!disabled} onSubmitEditing={() => void submitEmail()} returnKeyType="go" />
              <TouchableOpacity style={styles.visibilityButton} onPress={() => setShowPassword(!showPassword)} accessibilityRole="button" accessibilityLabel={showPassword ? "비밀번호 숨기기" : "비밀번호 표시"}>
                {showPassword ? <EyeOff size={20} color={colors.body} /> : <Eye size={20} color={colors.body} />}
              </TouchableOpacity>
            </View>
            <TouchableOpacity style={[styles.emailButton, (disabled || !email.trim() || !password) && styles.disabled]} onPress={() => void submitEmail()} disabled={disabled || !email.trim() || !password} accessibilityRole="button">
              <Text style={styles.emailButtonText}>로그인</Text>
            </TouchableOpacity>
          </View>
        ) : null}
        {error || linkError ? <Text style={styles.error} accessibilityRole="alert">{error || linkError}</Text> : null}
        {!configured ? <Text style={styles.note}>로그인 연결을 준비하고 있어요. 잠시 후 다시 방문해 주세요.</Text> : null}
        <View style={styles.legalLinks}>
          {[["/terms", "이용약관"], ["/privacy", "개인정보처리방침"], ["/support", "문의"]].map(([path, label]) => (
            <TouchableOpacity key={path} style={styles.legalLink} accessibilityRole="link" onPress={() => void openNotice(path!)}><Text style={styles.legal}>{label}</Text></TouchableOpacity>
          ))}
        </View>
      </View>
    </View>
    </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.canvasWarm },
  container: { flexGrow: 1, alignItems: "center", padding: spacing.xl, paddingTop: 48, paddingBottom: 40 },
  content: { width: "100%", maxWidth: 440, flexGrow: 1, justifyContent: "space-between", gap: 48 },
  brand: { gap: spacing.md },
  icon: { width: 52, height: 52, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.leafSoft },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.heroTitle },
  subtitle: { color: colors.body, ...typography.body },
  panel: { gap: spacing.sm },
  kakaoButton: { minHeight: 56, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: "#FEE500", padding: spacing.sm, ...shadows.card },
  kakaoText: { color: "#191919", fontSize: 16, lineHeight: 22, fontWeight: "800" },
  emailToggle: { minHeight: 48, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.sm },
  emailToggleText: { color: colors.body, ...typography.bodyStrong },
  emailFields: { gap: spacing.sm },
  label: { color: colors.ink, ...typography.caption },
  input: { minHeight: 52, borderColor: colors.hairline, borderWidth: 1, borderRadius: radii.control, paddingHorizontal: spacing.md, color: colors.ink, backgroundColor: colors.surface, ...typography.body },
  passwordRow: { flexDirection: "row", alignItems: "center" },
  passwordInput: { flex: 1, minWidth: 0, paddingRight: 52 },
  visibilityButton: { position: "absolute", right: 4, width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  emailButton: { minHeight: 52, alignItems: "center", justifyContent: "center", backgroundColor: colors.leaf, borderRadius: radii.control, padding: spacing.sm },
  emailButtonText: { color: colors.surface, ...typography.bodyStrong },
  disabled: { opacity: 0.46 },
  error: { color: colors.danger, textAlign: "center", ...typography.caption },
  note: { color: colors.warningText, textAlign: "center", ...typography.caption },
  legalLinks: { flexDirection: "row", flexWrap: "wrap", justifyContent: "center" },
  legalLink: { minHeight: 44, justifyContent: "center", paddingHorizontal: spacing.sm },
  legal: { color: colors.muted, textAlign: "center", textDecorationLine: "underline", ...typography.caption }
});
