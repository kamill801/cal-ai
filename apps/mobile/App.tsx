import type { BodyCheckIn, CoachDashboard, NutritionTarget, OnboardingRequest, OnboardingResponse, ProgressSummary, WeeklyCoachReport, WorkoutEffort, WorkoutHistory, WorkoutPlan } from "@cal-ai/shared";
import { StatusBar } from "expo-status-bar";
import { useEffect, useMemo, useReducer, useState } from "react";
import { ActivityIndicator, Alert, Platform, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { ApiClientError, createCalAiApiClient } from "./src/api";
import { useAuthSession } from "./src/auth/useAuthSession";
import { onboardingFlowErrorFromUnknown } from "./src/api/errorMapping";
import { uploadImageToStorage } from "./src/api/imageUpload";
import { AppBottomNav, type MainTab } from "./src/components/AppBottomNav";
import { createInitialScanToSaveState, scanToSaveReducer, type FlowError, type RequestStatus, type ScanToSaveCommand } from "./src/flow/scanToSaveFlow";
import { delay } from "./src/flow/scanToSavePolling";
import { captureMealImageWithCamera, pickMealImageFromLibrary, type MealImagePickerResult } from "./src/media/mealImagePicker";
import { AnalyzeEvidenceScreen } from "./src/screens/AnalyzeEvidenceScreen";
import { ClarificationScreen } from "./src/screens/ClarificationScreen";
import { OnboardingScreen } from "./src/screens/OnboardingScreen";
import { LoginScreen } from "./src/screens/LoginScreen";
import { ReviewResultScreen } from "./src/screens/ReviewResultScreen";
import { SafetyPrivacyScreen } from "./src/screens/SafetyPrivacyScreen";
import { SavedImpactScreen } from "./src/screens/SavedImpactScreen";
import { TodayDashboardScreen } from "./src/screens/TodayDashboardScreen";
import { TrainingScreen } from "./src/screens/TrainingScreen";
import { ProgressScreen } from "./src/screens/ProgressScreen";
import { WeeklyCoachScreen } from "./src/screens/WeeklyCoachScreen";
import { clearProfileId, loadProfileId, saveProfileId } from "./src/session/profileSession";
import { profileRestoreAction, type ProfileRefreshResult } from "./src/session/profileRestore";
import { colors } from "./src/theme";

type AppScreen = "onboarding" | "safety" | MainTab;

export default function App() {
  const auth = useAuthSession();
  const [state, dispatch] = useReducer(scanToSaveReducer, undefined, createInitialScanToSaveState);
  const [appScreen, setAppScreen] = useState<AppScreen>("onboarding");
  const [onboardingStatus, setOnboardingStatus] = useState<RequestStatus>("idle");
  const [onboardingError, setOnboardingError] = useState<FlowError | undefined>(undefined);
  const [onboardingResult, setOnboardingResult] = useState<OnboardingResponse | undefined>(undefined);
  const [profileId, setProfileId] = useState<string | undefined>(undefined);
  const [sessionReady, setSessionReady] = useState(false);
  const [coachDashboard, setCoachDashboard] = useState<CoachDashboard | undefined>(undefined);
  const [workoutPlan, setWorkoutPlan] = useState<WorkoutPlan | undefined>(undefined);
  const [workoutHistory, setWorkoutHistory] = useState<WorkoutHistory | undefined>(undefined);
  const [progress, setProgress] = useState<ProgressSummary | undefined>(undefined);
  const [weeklyCoach, setWeeklyCoach] = useState<WeeklyCoachReport | undefined>(undefined);
  const [latestBodyCheckIn, setLatestBodyCheckIn] = useState<BodyCheckIn | undefined>(undefined);
  const [coachStatus, setCoachStatus] = useState<RequestStatus>("idle");
  const [coachError, setCoachError] = useState<FlowError | undefined>(undefined);
  const [deletionStatus, setDeletionStatus] = useState<RequestStatus>("idle");
  const [deletionError, setDeletionError] = useState<string | undefined>(undefined);
  const apiClient = useMemo(() => createCalAiApiClient(undefined, auth.session?.access_token), [auth.session?.access_token]);
  const photoSource = state.selectedImageUri ? { uri: state.selectedImageUri } : undefined;

  useEffect(() => {
    let isCurrent = true;

    async function restoreSession(): Promise<void> {
      if (!auth.ready) {
        return;
      }
      if (auth.enabled && !auth.session) {
        if (isCurrent) {
          setSessionReady(true);
        }
        return;
      }
      try {
        const storedProfileId = await loadProfileId();
        if (!storedProfileId || !isCurrent) {
          return;
        }
        setProfileId(storedProfileId);
        const restored = await refreshCoachData(storedProfileId);
        if (!isCurrent) {
          return;
        }
        const action = profileRestoreAction(restored);
        if (action === "open") {
          setAppScreen("today");
        } else if (action === "clear") {
          await clearProfileId();
          setProfileId(undefined);
        } else {
          setAppScreen("today");
        }
      } catch {
        setAppScreen("onboarding");
      } finally {
        if (isCurrent) {
          setSessionReady(true);
        }
      }
    }

    void restoreSession();
    return () => {
      isCurrent = false;
    };
  }, [auth.enabled, auth.ready, auth.session?.user.id, apiClient]);

  useEffect(() => {
    if (profileId) {
      void saveProfileId(profileId);
    }
  }, [profileId]);

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
          case "UPLOAD_IMAGE": {
            const uploaded = await uploadImageToStorage(activeCommand, apiClient);
            if (isCurrent) {
              dispatch({ type: "IMAGE_UPLOADED", imageUploadId: uploaded.imageUploadId });
            }
            return;
          }
          case "CREATE_ANALYSIS_JOB": {
            const created = await apiClient.createAnalysisJob({
              imageUploadId: activeCommand.imageUploadId,
              profileId,
              mealType: activeCommand.mealType
            });
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
              clarificationValue: activeCommand.clarificationValue,
              nutritionOverride: activeCommand.nutritionOverride,
              profileId,
              loggedOn: todayIso()
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
        dispatch({
          type: "COMMAND_FAILED",
          command: activeCommand,
          message: error instanceof ApiClientError ? error.userMessage : "요청 중 문제가 생겼어요. 다시 시도해 주세요.",
          code: error instanceof ApiClientError ? error.code : "unknown_error",
          kind: error instanceof ApiClientError ? error.kind : "unknown",
          retryable: error instanceof ApiClientError ? error.retryable : true,
          status: error instanceof ApiClientError ? error.status : undefined
        });
      }
    }

    void runCommand(command);

    return () => {
      isCurrent = false;
    };
  }, [apiClient, profileId, state.pendingCommand]);

  useEffect(() => {
    if (state.screen === "saved" && profileId) {
      void refreshCoachData(profileId);
    }
  }, [profileId, state.screen]);

  async function submitOnboarding(input: OnboardingRequest): Promise<void> {
    setOnboardingStatus("loading");
    setOnboardingError(undefined);
    try {
      const created = await apiClient.createOnboarding(input);
      setOnboardingResult(created);
      setOnboardingStatus("success");
    } catch (error) {
      setOnboardingStatus("error");
      setOnboardingError(onboardingFlowErrorFromUnknown(error));
    }
  }

  function continueFromOnboarding(target: NutritionTarget): void {
    dispatch({ type: "APPLY_NUTRITION_TARGET", target });
    if (onboardingResult) {
      setProfileId(onboardingResult.profileId);
      void refreshCoachData(onboardingResult.profileId);
    }
    setAppScreen("today");
  }

  async function refreshCoachData(activeProfileId: string): Promise<ProfileRefreshResult> {
    setCoachStatus("loading");
    setCoachError(undefined);
    try {
      const [dashboard, progressSummary, report, existingPlan, history] = await Promise.all([
        apiClient.getCoachDashboard(activeProfileId, todayIso()),
        apiClient.getProgress(activeProfileId),
        apiClient.getWeeklyCoach(activeProfileId),
        apiClient.getWorkoutPlan(activeProfileId).catch((error: unknown) => {
          if (error instanceof ApiClientError && error.status === 404) {
            return undefined;
          }
          throw error;
        }),
        apiClient.getWorkoutHistory(activeProfileId)
      ]);
      setCoachDashboard(dashboard);
      setProgress(progressSummary);
      setLatestBodyCheckIn(progressSummary.bodyCheckIns.at(-1));
      setWeeklyCoach(report);
      setWorkoutPlan(existingPlan);
      setWorkoutHistory(history);
      setCoachStatus("success");
      return "ok";
    } catch (error) {
      setCoachStatus("error");
      setCoachError(onboardingFlowErrorFromUnknown(error));
      if (error instanceof ApiClientError && error.status === 404 && error.code === "profile_not_found") {
        return "not_found";
      }
      return "failed";
    }
  }

  async function retrySessionRestore(): Promise<void> {
    if (!profileId) {
      return;
    }
    const restored = await refreshCoachData(profileId);
    if (restored === "not_found") {
      await clearProfileId();
      setProfileId(undefined);
      setAppScreen("onboarding");
    }
  }

  async function generatePlan(activeProfileId = profileId): Promise<void> {
    if (!activeProfileId) {
      return;
    }
    setCoachStatus("loading");
    setCoachError(undefined);
    try {
      const created = await apiClient.generateWorkoutPlan(activeProfileId);
      setWorkoutPlan(created);
      setCoachStatus("success");
      await refreshCoachData(activeProfileId);
    } catch (error) {
      setCoachStatus("error");
      setCoachError(onboardingFlowErrorFromUnknown(error));
    }
  }

  async function completeWorkout(input: {
    plan: WorkoutPlan;
    workoutDayId: string;
    durationMinutes: number;
    completedExerciseIds: string[];
    exercisePerformance: { exerciseId: string; setsCompleted: number; repsCompleted?: number; loadKg?: number; effort: WorkoutEffort }[];
    sessionRpe: number;
  }): Promise<void> {
    if (!profileId) {
      return;
    }
    setCoachStatus("loading");
    setCoachError(undefined);
    try {
      await apiClient.logWorkoutSession(profileId, {
        planId: input.plan.id,
        workoutDayId: input.workoutDayId,
        performedOn: todayIso(),
        durationMinutes: input.durationMinutes,
        completedExerciseIds: input.completedExerciseIds,
        exercisePerformance: input.exercisePerformance,
        sessionRpe: input.sessionRpe
      });
      await refreshCoachData(profileId);
    } catch (error) {
      setCoachStatus("error");
      setCoachError(onboardingFlowErrorFromUnknown(error));
    }
  }

  async function repeatMeal(mealLogId: string): Promise<void> {
    if (!profileId || coachStatus === "loading") {
      return;
    }
    setCoachStatus("loading");
    setCoachError(undefined);
    try {
      await apiClient.repeatMealLog(profileId, mealLogId, todayIso());
      await refreshCoachData(profileId);
    } catch (error) {
      setCoachStatus("error");
      setCoachError(onboardingFlowErrorFromUnknown(error));
    }
  }

  function confirmDeleteMeal(mealLogId: string, mealName: string): void {
    if (!profileId || coachStatus === "loading") {
      return;
    }
    if (Platform.OS === "web") {
      const confirmInBrowser = (globalThis as { confirm?: (message: string) => boolean }).confirm;
      if (confirmInBrowser?.(`${mealName} 기록을 오늘 섭취량에서 제외할까요?`)) {
        void deleteMeal(mealLogId);
      }
      return;
    }
    Alert.alert("식사 기록을 삭제할까요?", `${mealName} 기록을 오늘 섭취량에서 제외해요.`, [
      { text: "취소", style: "cancel" },
      {
        text: "삭제",
        style: "destructive",
        onPress: () => {
          void deleteMeal(mealLogId);
        }
      }
    ]);
  }

  async function deleteMeal(mealLogId: string): Promise<void> {
    if (!profileId) {
      return;
    }
    setCoachStatus("loading");
    setCoachError(undefined);
    try {
      await apiClient.deleteMealLog(profileId, mealLogId);
      await refreshCoachData(profileId);
    } catch (error) {
      setCoachStatus("error");
      setCoachError(onboardingFlowErrorFromUnknown(error));
    }
  }

  async function logWeight(weightKg: number): Promise<void> {
    if (!profileId) {
      return;
    }
    setCoachStatus("loading");
    try {
      await apiClient.logWeight(profileId, { loggedOn: todayIso(), weightKg });
      await refreshCoachData(profileId);
    } catch (error) {
      setCoachStatus("error");
      setCoachError(onboardingFlowErrorFromUnknown(error));
    }
  }

  async function logWellness(input: { energy: number; sleepQuality: number; soreness: number }): Promise<void> {
    if (!profileId) {
      return;
    }
    setCoachStatus("loading");
    try {
      await apiClient.logWellness(profileId, { loggedOn: todayIso(), ...input });
      await refreshCoachData(profileId);
    } catch (error) {
      setCoachStatus("error");
      setCoachError(onboardingFlowErrorFromUnknown(error));
    }
  }

  async function startScanFromCamera(): Promise<void> {
    try {
      handleMealImageResult(await captureMealImageWithCamera());
    } catch (error) {
      showImagePickerError(error);
    }
  }

  async function startScanFromLibrary(): Promise<void> {
    try {
      handleMealImageResult(await pickMealImageFromLibrary());
    } catch (error) {
      showImagePickerError(error);
    }
  }

  async function startBodyCheckInFromCamera(consentToAiAnalysis: true, view: BodyCheckIn["view"]): Promise<void> {
    try {
      await handleBodyImageResult(await captureMealImageWithCamera(), consentToAiAnalysis, view);
    } catch (error) {
      showImagePickerError(error);
    }
  }

  async function startBodyCheckInFromLibrary(consentToAiAnalysis: true, view: BodyCheckIn["view"]): Promise<void> {
    try {
      await handleBodyImageResult(await pickMealImageFromLibrary(), consentToAiAnalysis, view);
    } catch (error) {
      showImagePickerError(error);
    }
  }

  async function handleBodyImageResult(result: MealImagePickerResult, consentToAiAnalysis: true, view: BodyCheckIn["view"]): Promise<void> {
    if (result.status !== "selected") {
      if (result.status !== "cancelled") {
        handleMealImageResult(result);
      }
      return;
    }
    if (!profileId) {
      return;
    }
    setCoachStatus("loading");
    setCoachError(undefined);
    try {
      const uploaded = await uploadImageToStorage({ type: "UPLOAD_IMAGE", requestId: 1, ...result.image }, apiClient);
      const checkIn = await apiClient.createBodyCheckIn(profileId, {
        capturedOn: todayIso(),
        imageUploadId: uploaded.imageUploadId,
        view,
        consentToAiAnalysis
      });
      setLatestBodyCheckIn(checkIn);
      await refreshCoachData(profileId);
    } catch (error) {
      setCoachStatus("error");
      setCoachError(onboardingFlowErrorFromUnknown(error));
    }
  }

  async function signOut(): Promise<void> {
    await clearProfileId();
    setProfileId(undefined);
    setCoachDashboard(undefined);
    setWorkoutPlan(undefined);
    setWorkoutHistory(undefined);
    setProgress(undefined);
    setWeeklyCoach(undefined);
    setLatestBodyCheckIn(undefined);
    setAppScreen("onboarding");
    await auth.signOut();
  }

  async function deleteAppData(): Promise<void> {
    if (!profileId || deletionStatus === "loading") {
      return;
    }
    setDeletionStatus("loading");
    setDeletionError(undefined);
    try {
      await apiClient.deleteProfile(profileId);
      await clearProfileId();
      setProfileId(undefined);
      setCoachDashboard(undefined);
      setWorkoutPlan(undefined);
      setWorkoutHistory(undefined);
      setProgress(undefined);
      setWeeklyCoach(undefined);
      setLatestBodyCheckIn(undefined);
      setOnboardingResult(undefined);
      setAppScreen("onboarding");
      if (auth.enabled) {
        await auth.signOut();
      }
      setDeletionStatus("success");
    } catch (error) {
      setDeletionStatus("error");
      setDeletionError(error instanceof ApiClientError ? error.userMessage : "앱 데이터를 삭제하지 못했어요. 잠시 후 다시 시도해 주세요.");
    }
  }

  function handleMealImageResult(result: MealImagePickerResult): void {
    switch (result.status) {
      case "selected":
        dispatch({ type: "START_SCAN", image: result.image });
        return;
      case "permission_denied":
        Alert.alert("사진 권한이 필요해요", "식사 사진을 촬영하거나 선택하려면 권한을 허용해 주세요.");
        return;
      case "camera_unavailable":
        Alert.alert("카메라를 사용할 수 없어요", "시뮬레이터나 브라우저에서는 사진첩 선택으로 테스트해 주세요.");
        return;
      case "unsupported_type":
        Alert.alert("지원하지 않는 이미지예요", "JPG, PNG, WebP 형식의 음식 사진을 선택해 주세요.");
        return;
      case "too_large":
        Alert.alert("사진을 줄이지 못했어요", "다른 사진을 선택하거나 카메라에서 다시 촬영해 주세요.");
        return;
      case "read_failed":
        Alert.alert("사진을 불러오지 못했어요", "다른 사진으로 다시 시도해 주세요.");
        return;
      case "cancelled":
        return;
    }
  }

  if (!auth.ready || !sessionReady) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <StatusBar style="dark" />
        <View style={styles.sessionLoading} accessibilityLabel="프로필 불러오는 중">
          <ActivityIndicator color={colors.leaf} />
          <Text style={styles.sessionLoadingText}>오늘의 기록을 불러오고 있어요</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (auth.enabled && !auth.session) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <StatusBar style="dark" />
        <LoginScreen
          configured={auth.configured}
          loading={auth.loading}
          error={auth.error}
          onKakaoLogin={() => void auth.signInWithKakao()}
        />
      </SafeAreaView>
    );
  }

  if (profileId && !coachDashboard && coachStatus === "error") {
    return (
      <SafeAreaView style={styles.safeArea}>
        <StatusBar style="dark" />
        <View style={styles.sessionLoading} accessibilityLabel="프로필 연결 재시도">
          <Text style={styles.sessionErrorTitle}>기록을 잠시 불러오지 못했어요</Text>
          <Text style={styles.sessionLoadingText}>프로필은 기기에 안전하게 남아 있어요. 연결을 확인하고 다시 시도해 주세요.</Text>
          <TouchableOpacity style={styles.sessionRetryButton} onPress={() => void retrySessionRestore()} accessibilityRole="button">
            <Text style={styles.sessionRetryText}>다시 불러오기</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <View style={styles.content}>
      {state.screen === "today" && appScreen === "onboarding" ? (
        <OnboardingScreen
          status={onboardingStatus}
          error={onboardingError}
          target={onboardingResult?.target}
          warnings={onboardingResult?.warnings ?? []}
          onSubmit={(input) => {
            void submitOnboarding(input);
          }}
          onContinue={() => {
            if (onboardingResult) {
              continueFromOnboarding(onboardingResult.target);
            }
          }}
        />
      ) : null}
      {state.screen === "today" && appScreen === "safety" ? (
        <SafetyPrivacyScreen
          onBack={() => setAppScreen("today")}
          onSignOut={auth.enabled ? () => void signOut() : undefined}
          onDeleteData={() => void deleteAppData()}
          deletionStatus={deletionStatus}
          deletionError={deletionError}
        />
      ) : null}
      {state.screen === "today" && appScreen === "today" ? (
        <TodayDashboardScreen
          dashboard={state.dashboard}
          coachDashboard={coachDashboard}
          onCaptureMeal={() => {
            void startScanFromCamera();
          }}
          onPickMeal={() => {
            void startScanFromLibrary();
          }}
          onOpenSafety={() => setAppScreen("safety")}
          status={coachStatus}
          error={coachError}
          onRepeatMeal={(mealLogId) => void repeatMeal(mealLogId)}
          onDeleteMeal={confirmDeleteMeal}
        />
      ) : null}
      {state.screen === "today" && appScreen === "training" ? (
        <TrainingScreen dashboard={coachDashboard} plan={workoutPlan} history={workoutHistory} status={coachStatus} error={coachError} onGenerate={() => void generatePlan()} onComplete={(input) => void completeWorkout(input)} />
      ) : null}
      {state.screen === "today" && appScreen === "progress" ? (
        <ProgressScreen
          progress={progress}
          latestBodyCheckIn={latestBodyCheckIn}
          status={coachStatus}
          error={coachError}
          onLogWeight={(weightKg) => void logWeight(weightKg)}
          onLogWellness={(input) => void logWellness(input)}
          onCaptureBody={(consent, view) => void startBodyCheckInFromCamera(consent, view)}
          onPickBody={(consent, view) => void startBodyCheckInFromLibrary(consent, view)}
        />
      ) : null}
      {state.screen === "today" && appScreen === "coach" ? <WeeklyCoachScreen report={weeklyCoach} status={coachStatus} error={coachError} /> : null}
      {state.screen === "analyzing" ? (
        <AnalyzeEvidenceScreen
          analysis={state.analysis}
          photoSource={photoSource}
          status={state.status}
          error={state.error}
          onClarify={() => dispatch({ type: "OPEN_CLARIFICATION" })}
          onRetry={() => dispatch({ type: "RETRY_LAST" })}
          onCancel={() => dispatch({ type: "RETURN_DASHBOARD" })}
        />
      ) : null}
      {state.screen === "clarifying" && state.analysis ? (
        <ClarificationScreen
          analysis={state.analysis}
          photoSource={photoSource}
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
          photoSource={photoSource}
          narrowing={state.rangeNarrowing}
          status={state.status}
          error={state.error}
          onEdit={() => dispatch({ type: "EDIT_RESULT" })}
          onApplyManualAdjustment={(override) => dispatch({ type: "APPLY_MANUAL_ADJUSTMENT", override })}
          onSave={() => dispatch({ type: "SAVE_MEAL" })}
          onRetry={() => dispatch({ type: "RETRY_LAST" })}
        />
      ) : null}
      {state.screen === "saved" && state.analysis && state.impact ? (
        <SavedImpactScreen analysis={state.analysis} photoSource={photoSource} impact={state.impact} onDone={() => dispatch({ type: "RETURN_DASHBOARD" })} />
      ) : null}
      </View>
      {state.screen === "today" && (appScreen === "today" || appScreen === "training" || appScreen === "progress" || appScreen === "coach") ? (
        <AppBottomNav
          activeTab={appScreen}
          onSelect={(tab) => setAppScreen(tab)}
          onScan={() => {
            void startScanFromCamera();
          }}
        />
      ) : null}
    </SafeAreaView>
  );
}

function todayIso(): string {
  const now = new Date();
  const localTime = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return localTime.toISOString().slice(0, 10);
}

function showImagePickerError(error: unknown): void {
  if (error instanceof ApiClientError) {
    Alert.alert("사진을 불러오지 못했어요", error.userMessage);
    return;
  }
  Alert.alert("사진을 불러오지 못했어요", "다른 사진으로 다시 시도해 주세요.");
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvasWarm
  },
  content: { flex: 1 },
  sessionLoading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12
  },
  sessionLoadingText: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: "600",
    lineHeight: 21,
    maxWidth: 280,
    textAlign: "center"
  },
  sessionErrorTitle: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "800"
  },
  sessionRetryButton: {
    minHeight: 48,
    paddingHorizontal: 24,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 14,
    backgroundColor: colors.leaf
  },
  sessionRetryText: {
    color: colors.surface,
    fontSize: 15,
    fontWeight: "800"
  }
});
