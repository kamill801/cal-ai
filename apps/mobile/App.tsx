import { StatusBar } from "expo-status-bar";
import { useEffect, useMemo, useReducer } from "react";
import { SafeAreaView, StyleSheet } from "react-native";
import { ApiClientError, createCalAiApiClient } from "./src/api";
import { createInitialScanToSaveState, scanToSaveReducer, type ScanToSaveCommand } from "./src/flow/scanToSaveFlow";
import { AnalyzeEvidenceScreen } from "./src/screens/AnalyzeEvidenceScreen";
import { ClarificationScreen } from "./src/screens/ClarificationScreen";
import { ReviewResultScreen } from "./src/screens/ReviewResultScreen";
import { SavedImpactScreen } from "./src/screens/SavedImpactScreen";
import { TodayDashboardScreen } from "./src/screens/TodayDashboardScreen";
import { colors } from "./src/theme";

export default function App() {
  const [state, dispatch] = useReducer(scanToSaveReducer, undefined, createInitialScanToSaveState);
  const apiClient = useMemo(() => createCalAiApiClient(), []);

  useEffect(() => {
    const command = state.pendingCommand;
    if (!command) {
      return;
    }

    let isCurrent = true;

    async function runCommand(activeCommand: ScanToSaveCommand) {
      try {
        if (activeCommand.type === "FETCH_ANALYSIS_JOB" && activeCommand.delayMs && activeCommand.delayMs > 0) {
          await delay(activeCommand.delayMs);
          if (!isCurrent) {
            return;
          }
        }
        switch (activeCommand.type) {
          case "CREATE_ANALYSIS_JOB": {
            const created = await apiClient.createAnalysisJob({ imageUploadId: activeCommand.imageUploadId, mealType: activeCommand.mealType });
            if (isCurrent) {
              dispatch({ type: "ANALYSIS_JOB_CREATED", analysisJobId: created.analysisJobId });
            }
            return;
          }
          case "FETCH_ANALYSIS_JOB": {
            const job = await apiClient.getAnalysisJob(activeCommand.jobId);
            if (isCurrent) {
              dispatch({ type: "ANALYSIS_JOB_LOADED", job });
            }
            return;
          }
          case "SUBMIT_CLARIFICATION": {
            const clarified = await apiClient.submitClarification({
              jobId: activeCommand.jobId,
              questionKey: activeCommand.questionKey,
              value: activeCommand.value
            });
            if (isCurrent) {
              dispatch({ type: "CLARIFICATION_SUBMITTED", analysis: clarified.result, rangeNarrowing: clarified.rangeNarrowing });
            }
            return;
          }
          case "SAVE_MEAL": {
            const impact = await apiClient.saveMealLog({
              analysisJobId: activeCommand.analysisJobId,
              resultId: activeCommand.resultId,
              clarificationValue: activeCommand.clarificationValue
            });
            if (isCurrent) {
              dispatch({ type: "MEAL_SAVED", impact });
            }
            return;
          }
        }
      } catch (error) {
        if (!isCurrent) {
          return;
        }
        const message = error instanceof ApiClientError ? error.userMessage : "요청 중 문제가 생겼어요. 다시 시도해 주세요.";
        const code = error instanceof ApiClientError ? error.code : "unknown_error";
        dispatch({ type: "COMMAND_FAILED", command: activeCommand, message, code });
      }
    }

    void runCommand(command);

    return () => {
      isCurrent = false;
    };
  }, [apiClient, state.pendingCommand]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      {state.screen === "today" ? <TodayDashboardScreen dashboard={state.dashboard} onStartScan={() => dispatch({ type: "START_SCAN" })} /> : null}
      {state.screen === "analyzing" ? (
        <AnalyzeEvidenceScreen
          analysis={state.analysis}
          status={state.status}
          error={state.error}
          onClarify={() => dispatch({ type: "OPEN_CLARIFICATION" })}
          onRetry={() => dispatch({ type: "RETRY_LAST" })}
        />
      ) : null}
      {state.screen === "clarifying" && state.analysis ? (
        <ClarificationScreen
          analysis={state.analysis}
          narrowing={state.rangeNarrowing}
          selectedValue={state.selectedValue}
          status={state.status}
          error={state.error}
          onSelect={(value) => dispatch({ type: "CHOOSE_CLARIFICATION", value })}
          onSkip={() => dispatch({ type: "SKIP_CLARIFICATION" })}
          onRetry={() => dispatch({ type: "RETRY_LAST" })}
        />
      ) : null}
      {state.screen === "review" && state.analysis ? (
        <ReviewResultScreen
          analysis={state.analysis}
          narrowing={state.rangeNarrowing}
          status={state.status}
          error={state.error}
          onEdit={() => dispatch({ type: "EDIT_RESULT" })}
          onSave={() => dispatch({ type: "SAVE_MEAL" })}
          onRetry={() => dispatch({ type: "RETRY_LAST" })}
        />
      ) : null}
      {state.screen === "saved" && state.analysis && state.impact ? (
        <SavedImpactScreen analysis={state.analysis} impact={state.impact} onDone={() => dispatch({ type: "RETURN_DASHBOARD" })} />
      ) : null}
    </SafeAreaView>
  );
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.paper
  }
});
