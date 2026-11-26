import { Camera, Dumbbell, Home, MessageCircle, TrendingUp, type LucideIcon } from "lucide-react-native";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { colors, freshGreen, radii, shadows, spacing, typography } from "../theme";

export type MainTab = "today" | "training" | "progress" | "coach";

const tabs: readonly { readonly id: MainTab; readonly label: string; readonly icon: LucideIcon }[] = [
  { id: "today", label: "오늘", icon: Home },
  { id: "training", label: "운동", icon: Dumbbell },
  { id: "progress", label: "변화", icon: TrendingUp },
  { id: "coach", label: "코치", icon: MessageCircle }
];

export function AppBottomNav({ activeTab, onSelect, onScan }: { readonly activeTab: MainTab; readonly onSelect: (tab: MainTab) => void; readonly onScan: () => void }) {
  const quiet = activeTab !== "coach";
  return (
    <View style={[styles.bar, quiet ? styles.quietBar : shadows.sheet]}>
      {tabs.slice(0, 2).map((tab) => <TabButton key={tab.id} tab={tab} active={activeTab === tab.id} onPress={() => onSelect(tab.id)} />)}
      <TouchableOpacity style={quiet ? styles.tab : styles.scanButton} activeOpacity={0.86} onPress={onScan} accessibilityRole="button" accessibilityLabel="식사 사진 기록" accessibilityHint="카메라를 열어 음식 분석을 시작합니다">
        <View style={quiet ? styles.quietScanIcon : undefined}><Camera color={freshGreen.onFill} size={quiet ? 18 : 22} strokeWidth={quiet ? 2 : 2.5} /></View>
        <Text style={quiet ? [styles.tabLabel, styles.tabTextActive] : styles.scanLabel}>기록</Text>
      </TouchableOpacity>
      {tabs.slice(2).map((tab) => <TabButton key={tab.id} tab={tab} active={activeTab === tab.id} onPress={() => onSelect(tab.id)} />)}
    </View>
  );
}

function TabButton({ tab, active, onPress }: { readonly tab: (typeof tabs)[number]; readonly active: boolean; readonly onPress: () => void }) {
  const Icon = tab.icon;
  return (
    <TouchableOpacity style={styles.tab} activeOpacity={0.78} onPress={onPress} accessibilityRole="tab" accessibilityLabel={`${tab.label} 탭`} accessibilityHint={`${tab.label} 화면으로 이동합니다`} accessibilityState={{ selected: active }}>
      <View style={styles.tabIcon}><Icon color={active ? freshGreen.indicator : colors.muted} size={20} strokeWidth={active ? 2.5 : 2} /></View>
      <Text style={[styles.tabLabel, active && styles.tabTextActive]}>{tab.label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  bar: { width: "100%", alignItems: "center", flexDirection: "row", borderTopColor: colors.hairline, borderTopWidth: 1, backgroundColor: colors.surface, paddingHorizontal: spacing.xs, paddingBottom: spacing.sm, paddingTop: spacing.xs, overflow: "hidden" },
  quietBar: { borderTopColor: "#e2e8e7" },
  quietScanIcon: { width: 30, height: 24, alignItems: "center", justifyContent: "center", borderRadius: 6, backgroundColor: freshGreen.fill },
  tab: { flex: 1, minWidth: 0, minHeight: 54, alignItems: "center", justifyContent: "center", gap: 2 },
  tabIcon: { width: 24, height: 24, alignItems: "center", justifyContent: "center" },
  tabLabel: { color: colors.muted, ...typography.caption },
  tabTextActive: { color: freshGreen.ink },
  scanButton: { width: 56, minHeight: 58, flexShrink: 0, marginTop: -16, alignItems: "center", justifyContent: "center", borderColor: colors.surface, borderWidth: 4, borderRadius: radii.pill, backgroundColor: freshGreen.fill, ...shadows.floating },
  scanLabel: { color: freshGreen.onFill, fontSize: 10, lineHeight: 13, fontWeight: "800" }
});
