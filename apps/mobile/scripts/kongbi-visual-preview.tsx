import { registerRootComponent } from "expo";
import { useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { TrustBuddy, type TrustBuddyPose } from "../src/components/TrustBuddy";
import { LoginScreen } from "../src/screens/LoginScreen";
import { OnboardingScreen } from "../src/screens/OnboardingScreen";
import { TodayDashboardScreen } from "../src/screens/TodayDashboardScreen";
import { AnalyzeEvidenceScreen } from "../src/screens/AnalyzeEvidenceScreen";
import { ClarificationScreen } from "../src/screens/ClarificationScreen";
import { ReviewResultScreen } from "../src/screens/ReviewResultScreen";
import { TrainingScreen } from "../src/screens/TrainingScreen";
import { ProgressScreen } from "../src/screens/ProgressScreen";
import { WeeklyCoachScreen } from "../src/screens/WeeklyCoachScreen";
import { PlanScreen } from "../src/screens/PlanScreen";
import { PrivacyConsentScreen } from "../src/screens/PrivacyConsentScreen";
import { SavedImpactScreen } from "../src/screens/SavedImpactScreen";
import { todayDashboard, initialAnalysis, clarifiedAnalysis, rangeNarrowing, savedImpact } from "../src/mockData";
import { colors } from "../src/theme";

// Isolated visual fixture entry only: never imported by the production entry.
// All actions are inert; this surface cannot sign in, upload, save or delete.
const noop = () => {};
const scenes = ["로그인", "목표", "식사", "분석", "보정", "결과", "운동", "변화", "코치", "이용권", "동의", "저장", "캐릭터"] as const;
const poses: TrustBuddyPose[] = ["welcome", "meal", "analysis", "workout", "progress", "coach", "celebrate"];

function Preview() {
  const [scene, setScene] = useState<typeof scenes[number]>("로그인");
  return <View style={styles.root}>
    <View style={styles.nav} accessibilityLabel="로컬 시각 검증 전용">
      {scenes.map((name) => <TouchableOpacity key={name} onPress={() => setScene(name)} accessibilityRole="button"
        accessibilityState={{ selected: scene === name }} style={styles.tab}>
        <Text style={{ color: scene === name ? colors.leaf : colors.ink }}>{name}</Text>
      </TouchableOpacity>)}
    </View>
    <View style={styles.surface}>
      {scene === "로그인" ? <LoginScreen configured loading={false} onKakaoLogin={noop} onEmailLogin={async () => {}} /> : null}
      {scene === "목표" ? <OnboardingScreen status="idle" warnings={[]} onSubmit={noop} onContinue={noop} /> : null}
      {scene === "식사" ? <TodayDashboardScreen dashboard={todayDashboard} status="idle" onCaptureMeal={noop} onPickMeal={noop} onOpenSafety={noop} onOpenPlan={noop} onRepeatMeal={noop} onDeleteMeal={noop} /> : null}
      {scene === "분석" ? <AnalyzeEvidenceScreen analysis={initialAnalysis} status="success" onClarify={noop} onRetry={noop} onCancel={noop} /> : null}
      {scene === "보정" ? <ClarificationScreen analysis={initialAnalysis} status="idle" onSelect={noop} onSkip={noop} onRetry={noop} /> : null}
      {scene === "결과" ? <ReviewResultScreen analysis={clarifiedAnalysis} narrowing={rangeNarrowing} status="idle" onSave={noop} onEdit={noop} onApplyManualAdjustment={noop} onRetry={noop} /> : null}
      {scene === "운동" ? <TrainingScreen status="idle" onGenerate={noop} onStart={noop} onComplete={noop} /> : null}
      {scene === "변화" ? <ProgressScreen status="idle" bodyPhotoEnabled={false} onOpenSafety={noop} onLogWeight={noop} onLogWellness={noop} onCaptureBody={noop} onPickBody={noop} /> : null}
      {scene === "코치" ? <WeeklyCoachScreen status="idle" /> : null}
      {scene === "이용권" ? <PlanScreen onBack={noop} onCheckout={noop} configured={false} loading={false} /> : null}
      {scene === "동의" ? <PrivacyConsentScreen policyVersion="visual-fixture" status="idle" onSubmit={noop} onRetry={noop} onManage={noop} /> : null}
      {scene === "저장" ? <SavedImpactScreen analysis={clarifiedAnalysis} impact={savedImpact} onDone={noop} /> : null}
      {scene === "캐릭터" ? <View style={styles.gallery}>{poses.map((pose) =>
        <View key={pose} style={styles.tile}><TrustBuddy size={96} pose={pose} /><Text>{pose}</Text></View>)}</View> : null}
    </View>
  </View>;
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.cream },
  nav: { flexDirection: "row", flexWrap: "wrap", padding: 8, backgroundColor: colors.surface, gap: 4 },
  tab: { minHeight: 32, padding: 8, justifyContent: "center" },
  surface: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" },
  gallery: { flexDirection: "row", flexWrap: "wrap", justifyContent: "center", gap: 16, padding: 16 },
  tile: { alignItems: "center", gap: 8 }
});

registerRootComponent(Preview);
