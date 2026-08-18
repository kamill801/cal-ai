import { ShieldCheck } from "lucide-react-native";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { colors, radii, shadows, spacing, typography } from "../theme";

export function LoginScreen({ configured, loading, error, onKakaoLogin }: { readonly configured: boolean; readonly loading: boolean; readonly error?: string; readonly onKakaoLogin: () => void }) {
  return (
    <View style={styles.container}>
      <View style={styles.brand}>
        <View style={styles.icon}><ShieldCheck color={colors.leaf} size={28} /></View>
        <Text style={styles.eyebrow}>TRUST FIRST</Text>
        <Text style={styles.title}>내 기록을 이어서{`\n`}몸의 변화를 만들어요</Text>
        <Text style={styles.subtitle}>식사, 운동, 신체 체크인을 한 계정에 안전하게 모아 매일의 다음 행동을 연결해요.</Text>
      </View>
      <View style={styles.panel}>
        <TouchableOpacity style={[styles.kakaoButton, (!configured || loading) && styles.disabled]} disabled={!configured || loading} onPress={onKakaoLogin} accessibilityRole="button">
          {loading ? <ActivityIndicator color="#191919" /> : <Text style={styles.kakaoText}>카카오로 시작하기</Text>}
        </TouchableOpacity>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {!configured ? <Text style={styles.note}>Supabase와 Kakao 설정을 완료하면 로그인을 사용할 수 있어요.</Text> : null}
        <Text style={styles.legal}>로그인하면 서비스 이용약관과 개인정보 처리방침에 동의한 것으로 봅니다.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "space-between", padding: spacing.xl, paddingTop: 72, paddingBottom: 40, backgroundColor: colors.canvasWarm },
  brand: { gap: spacing.md },
  icon: { width: 52, height: 52, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.leafSoft },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.heroTitle },
  subtitle: { maxWidth: 340, color: colors.body, ...typography.body },
  panel: { gap: spacing.md },
  kakaoButton: { minHeight: 56, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: "#FEE500", ...shadows.card },
  kakaoText: { color: "#191919", fontSize: 16, lineHeight: 22, fontWeight: "800" },
  disabled: { opacity: 0.46 },
  error: { color: colors.danger, textAlign: "center", ...typography.caption },
  note: { color: colors.warningText, textAlign: "center", ...typography.caption },
  legal: { color: colors.muted, textAlign: "center", ...typography.caption }
});
