import { StatusBar } from "expo-status-bar";
import { useReducer } from "react";
import { SafeAreaView, StyleSheet } from "react-native";
import { createInitialScanToSaveState, scanToSaveReducer } from "./src/flow/scanToSaveFlow";
import { AnalyzeEvidenceScreen } from "./src/screens/AnalyzeEvidenceScreen";
import { ClarificationScreen } from "./src/screens/ClarificationScreen";
import { ReviewResultScreen } from "./src/screens/ReviewResultScreen";
import { SavedImpactScreen } from "./src/screens/SavedImpactScreen";
import { TodayDashboardScreen } from "./src/screens/TodayDashboardScreen";
import { colors } from "./src/theme";

export default function App() {
  const [state, dispatch] = useReducer(scanToSaveReducer, undefined, createInitialScanToSaveState);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      {state.screen === "today" ? (
        <TodayDashboardScreen dashboard={state.dashboard} onStartScan={() => dispatch({ type: "START_SCAN" })} />
      ) : null}
      {state.screen === "analyzing" ? (
        <AnalyzeEvidenceScreen analysis={state.analysis} onClarify={() => dispatch({ type: "OPEN_CLARIFICATION" })} />
      ) : null}
      {state.screen === "clarifying" ? (
        <ClarificationScreen
          analysis={state.analysis}
          narrowing={state.rangeNarrowing}
          selectedValue={state.selectedValue}
          onSelect={(value) => dispatch({ type: "CHOOSE_CLARIFICATION", value })}
          onSkip={() => dispatch({ type: "SKIP_CLARIFICATION" })}
        />
      ) : null}
      {state.screen === "review" ? (
        <ReviewResultScreen
          analysis={state.analysis}
          narrowing={state.rangeNarrowing}
          onEdit={() => dispatch({ type: "EDIT_RESULT" })}
          onSave={() => dispatch({ type: "SAVE_MEAL" })}
        />
      ) : null}
      {state.screen === "saved" ? (
        <SavedImpactScreen analysis={state.analysis} impact={state.impact} onDone={() => dispatch({ type: "RETURN_DASHBOARD" })} />
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.paper
  }
});
