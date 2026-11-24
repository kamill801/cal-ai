import type { CoachDashboard, WorkoutDay, WorkoutEffort, WorkoutExercise, WorkoutHistory, WorkoutPlan, WorkoutSessionInput } from "@cal-ai/shared";
import { Check, ChevronDown, ChevronUp, Minus, Plus, Timer, X } from "lucide-react-native";
import { useEffect, useRef, useState } from "react";
import { Keyboard, Modal, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { CoachCard } from "../components/CoachCard";
import { FlowStatusCard } from "../components/FlowStatusCard";
import { TrustBuddy } from "../components/TrustBuddy";
import type { FlowError, RequestStatus } from "../flow/scanToSaveFlow";
import { buildWorkoutPerformance, createSetDraft, effortOptions, isTimedExercise, maxWorkoutSets, parseSetDraft, restSecondsRemaining, workoutIntensityLabel, type SetDraft } from "../flow/workoutLog";
import { colors, radii, spacing, typography } from "../theme";

interface TrainingProps {
  readonly dashboard?: CoachDashboard;
  readonly plan?: WorkoutPlan;
  readonly history?: WorkoutHistory;
  readonly status: RequestStatus;
  readonly error?: FlowError;
  readonly visible: boolean;
  readonly refreshPending: boolean;
  readonly onRefresh: () => void;
  readonly onGenerate: () => void;
  readonly onStart: (workoutDayId: string) => void;
  readonly onComplete: (input: Omit<WorkoutSessionInput, "performedOn">) => Promise<boolean>;
}

interface ActiveSession {
  readonly planId: string;
  readonly day: WorkoutDay;
  readonly startedAt: number;
}

interface RestTimer {
  readonly exerciseId: string;
  readonly setIndex: number;
  readonly deadline: number;
}

export function TrainingScreen({ dashboard, plan, history, status, error, visible, refreshPending, onRefresh, onGenerate, onStart, onComplete }: TrainingProps) {
  const nextDay = plan?.days[(dashboard?.training.completedSessions ?? 0) % Math.max(plan.days.length, 1)];
  const [session, setSession] = useState<ActiveSession>();
  const [drafts, setDrafts] = useState<Record<string, SetDraft[]>>({});
  const [efforts, setEfforts] = useState<Partial<Record<string, WorkoutEffort>>>({});
  const [openExercise, setOpenExercise] = useState<string>();
  const [rest, setRest] = useState<RestTimer>();
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [finishing, setFinishing] = useState(false);
  const [discarding, setDiscarding] = useState(false);
  const [duration, setDuration] = useState("");
  const [durationEdited, setDurationEdited] = useState(false);
  const [intensity, setIntensity] = useState<number>();
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const scroll = useRef<ScrollView>(null);
  const day = session?.day ?? nextDay;

  const performance = session?.day.exercises.flatMap((exercise) => {
    const item = buildWorkoutPerformance(exercise, drafts[exercise.id] ?? [], efforts[exercise.id]);
    return item ? [item] : [];
  }) ?? [];
  const completedSets = performance.reduce((count, item) => count + item.setsCompleted, 0);
  const hasInvalidSet = session?.day.exercises.some((exercise) => (drafts[exercise.id] ?? []).some((item, index) => item.completed && !parseSetDraft(item, index, isTimedExercise(exercise)))) ?? false;
  const validDuration = /^\d+$/.test(duration.trim()) && +duration >= 1 && +duration <= 240;

  useEffect(() => {
    if (!rest || !visible || finishing) return;
    const remaining = restSecondsRemaining(rest.deadline, Date.now());
    setSecondsLeft(remaining);
    if (!remaining) return;
    const ticker = setInterval(() => {
      const seconds = restSecondsRemaining(rest.deadline, Date.now());
      setSecondsLeft(seconds);
      if (!seconds) clearInterval(ticker);
    }, 250);
    return () => clearInterval(ticker);
  }, [rest, visible, finishing]);

  function startWorkout() {
    if (!plan || !nextDay || session || refreshPending) return;
    setSession({ planId: plan.id, day: nextDay, startedAt: Date.now() });
    setDrafts(Object.fromEntries(nextDay.exercises.map((exercise) => [
      exercise.id,
      Array.from({ length: exercise.sets }, () => createSetDraft(exercise))
    ])));
    setEfforts({});
    setDuration("");
    setDurationEdited(false);
    setIntensity(undefined);
    setOpenExercise(nextDay.exercises[0]?.id);
    setSaved(false);
    onStart(nextDay.id);
  }

  function updateSet(id: string, index: number, patch: Partial<SetDraft>) {
    setDrafts((current) => ({ ...current, [id]: (current[id] ?? []).map((item, i) => i === index ? { ...item, ...patch } : item) }));
  }

  function toggleSet(exercise: WorkoutExercise, index: number) {
    const item = drafts[exercise.id]?.[index];
    if (!item || (!item.completed && !parseSetDraft(item, index, isTimedExercise(exercise)))) return;
    updateSet(exercise.id, index, { completed: !item.completed });
    if (!item.completed) {
      Keyboard.dismiss();
      setSecondsLeft(exercise.restSeconds);
      setRest({ exerciseId: exercise.id, setIndex: index, deadline: Date.now() + exercise.restSeconds * 1000 });
    } else if (rest?.exerciseId === exercise.id && rest.setIndex === index) {
      setRest(undefined);
    }
  }

  function changeSetCount(exercise: WorkoutExercise, add: boolean) {
    setDrafts((current) => {
      const sets = current[exercise.id] ?? [];
      if (add && sets.length < maxWorkoutSets) {
        const last = sets[sets.length - 1] ?? createSetDraft(exercise);
        return { ...current, [exercise.id]: [...sets, { ...last, completed: false }] };
      }
      if (!add && sets.length > 1 && !sets[sets.length - 1].completed) {
        return { ...current, [exercise.id]: sets.slice(0, -1) };
      }
      return current;
    });
  }

  function finishWorkout() {
    if (!session || completedSets === 0 || hasInvalidSet) return;
    Keyboard.dismiss();
    if (!durationEdited) setDuration(String(Math.max(1, Math.min(240, Math.round((Date.now() - session.startedAt) / 60_000)))));
    setFinishing(true);
  }

  async function saveWorkout() {
    if (!session || refreshPending || savingRef.current || completedSets === 0 || !validDuration || hasInvalidSet) return;
    savingRef.current = true;
    setSaving(true);
    try {
      const ok = await onComplete({
        planId: session.planId,
        workoutDayId: session.day.id,
        durationMinutes: +duration,
        completedExerciseIds: performance.map((item) => item.exerciseId),
        exercisePerformance: performance,
        sessionRpe: intensity
      });
      if (!ok) return;
      setFinishing(false);
      clearDraft();
      setSaved(true);
      scroll.current?.scrollTo({ y: 0, animated: true });
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  }

  function clearDraft() {
    setSession(undefined);
    setDrafts({});
    setEfforts({});
    setRest(undefined);
    setOpenExercise(undefined);
    setDiscarding(false);
  }

  const proteinGoal = dashboard?.nutrition.target.proteinG ?? 0;
  const protein = dashboard?.nutrition.consumed.proteinG ?? 0;
  const proteinPercent = proteinGoal ? Math.min(100, Math.round(protein / proteinGoal * 100)) : 0;

  return (
    <View style={styles.screen}>
      <ScrollView ref={scroll} keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerCopy}>
            <Text style={styles.eyebrow}>{session ? "운동 중" : "오늘의 운동"}</Text>
            <Text accessibilityRole="header" style={styles.title}>{day?.title ?? "내 운동 루틴 만들기"}</Text>
            {day ? <Text style={styles.body}>{session ? `${completedSets}세트 완료` : `${day.exercises.length}개 종목 · 약 ${plan?.sessionMinutes}분`}</Text> : null}
          </View>
          {session ? (
            <TouchableOpacity accessibilityRole="button" accessibilityLabel="운동 취소" onPress={() => { Keyboard.dismiss(); setDiscarding(true); }} style={styles.iconButton}>
              <X size={20} color={colors.muted} />
            </TouchableOpacity>
          ) : <TrustBuddy size={78} pose="workout" />}
        </View>
        {saved && !refreshPending ? <Text style={styles.saved} accessibilityLiveRegion="polite">운동 기록을 저장했어요.</Text> : null}
        {refreshPending && !finishing ? <>
          <FlowStatusCard title="운동 기록은 저장됐어요" message="화면을 갱신해 최신 운동 기록을 확인해 주세요." />
          <PrimaryButton label={status === "loading" ? "기록 불러오는 중" : "저장된 기록 다시 불러오기"} disabled={status === "loading"} onPress={onRefresh} />
        </> : error && !finishing ? <FlowStatusCard error={error} /> : null}
        {!plan && !session ? (
          <PrimaryButton label={status === "loading" ? "계획 만드는 중" : "운동 계획 만들기"} disabled={status === "loading"} onPress={onGenerate} />
        ) : null}
        {day && !session ? <PrimaryButton label="운동 시작" disabled={status === "loading" || refreshPending} onPress={startWorkout} /> : null}

        {day?.exercises.map((exercise) => (
          <ExerciseEntry key={`${session?.startedAt ?? "preview"}:${exercise.id}`} exercise={exercise} sets={drafts[exercise.id] ?? []}
            active={session !== undefined} expanded={openExercise === exercise.id} effort={efforts[exercise.id]}
            onExpand={() => setOpenExercise((value) => value === exercise.id ? undefined : exercise.id)}
            onUpdate={(index, patch) => updateSet(exercise.id, index, patch)}
            onCheck={(index) => toggleSet(exercise, index)}
            onSetCount={(add) => changeSetCount(exercise, add)}
            onEffort={(effort) => setEfforts((value) => ({ ...value, [exercise.id]: value[exercise.id] === effort ? undefined : effort }))}
          />
        ))}

        {!session && plan ? (
          <CoachCard title="이 계획에 반영한 것">
            {plan.personalizationBasis.map((basis) => <Text key={basis} style={styles.body}>{basis}</Text>)}
            <Text style={styles.caption}>{plan.progressionRule}</Text>
            <Text style={styles.caption}>{plan.safetyNote}</Text>
          </CoachCard>
        ) : null}
        {!session && proteinGoal > 0 ? (
          <CoachCard title={`오늘 단백질 ${protein} / ${proteinGoal}g`} tone="leaf">
            <View style={styles.progressTrack} accessible accessibilityRole="progressbar" accessibilityLabel="오늘 단백질 섭취 진행률" accessibilityValue={{ min: 0, max: 100, now: proteinPercent }}>
              <View style={[styles.progressFill, { width: `${proteinPercent}%` }]} />
            </View>
            <Text style={styles.body}>{dashboard?.nutrition.guidance}</Text>
          </CoachCard>
        ) : null}
        {!session && plan ? (
          <CoachCard title="최근 운동" eyebrow={`${history?.totalSessions ?? 0}회 기록`}>
            {!history?.sessions.length ? <Text style={styles.caption}>아직 저장한 운동이 없어요.</Text> : null}
            {history?.sessions.slice(0, 3).map((item) => (
              <View key={item.sessionId} style={styles.historyRow}>
                <View style={styles.headerCopy}>
                  <Text style={styles.strong}>{item.workoutTitle}</Text>
                  <Text style={styles.caption}>{[item.performedOn, `${item.durationMinutes}분`, workoutIntensityLabel(item.sessionRpe)].filter(Boolean).join(" · ")}</Text>
                </View>
                <View>
                  <Text style={styles.caption}>{item.setsCompleted ? `${item.setsCompleted}세트` : `${item.exerciseCount}종목`}</Text>
                  {item.totalVolumeKg > 0 ? <Text style={styles.caption}>{item.totalVolumeKg.toLocaleString()}kg</Text> : null}
                </View>
              </View>
            ))}
          </CoachCard>
        ) : null}
      </ScrollView>

      {session ? (
        <View style={styles.footer}>
          {rest ? (
            <View style={styles.restBanner}>
              <Timer size={18} color={colors.leaf} />
              <Text style={[styles.strong, styles.headerCopy]}>{secondsLeft ? `휴식 ${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, "0")}` : "휴식 완료"}</Text>
              <TouchableOpacity style={styles.iconButton} onPress={() => setRest(undefined)} accessibilityRole="button" accessibilityLabel={secondsLeft ? "휴식 건너뛰기" : "휴식 안내 닫기"}>
                <X size={19} color={colors.ink} />
              </TouchableOpacity>
            </View>
          ) : null}
          <PrimaryButton label="운동 끝내기" onPress={finishWorkout} disabled={completedSets === 0 || hasInvalidSet} />
        </View>
      ) : null}

      <Modal transparent visible={visible && finishing} animationType="fade" onRequestClose={() => !saving && setFinishing(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.finishSheet} accessibilityViewIsModal>
            <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.sheetContent}>
              <View style={styles.sheetHeader}>
                <View style={styles.headerCopy}>
                  <Text style={styles.eyebrow}>운동 마무리</Text>
                  <Text accessibilityRole="header" style={styles.sectionTitle}>오늘 운동은 어땠나요?</Text>
                </View>
                <TouchableOpacity accessibilityRole="button" accessibilityLabel="운동으로 돌아가기" disabled={saving} onPress={() => setFinishing(false)} style={styles.iconButton}>
                  <X size={20} color={colors.ink} />
                </TouchableOpacity>
              </View>
              <Text style={styles.caption}>{performance.length}개 종목 · {completedSets}세트 완료</Text>
              <View style={styles.finishDuration}>
                <Text style={styles.strong}>운동 시간</Text>
                <View style={styles.minutesInput}>
                  <View style={styles.minutesValue}>
                    <SetInput label="운동 시간(분)" value={duration} onChange={(value) => { setDurationEdited(true); setDuration(value); }} disabled={saving} />
                  </View>
                  <Text style={styles.caption}>분</Text>
                </View>
              </View>
              {!validDuration ? <Text style={styles.validation}>1~240분 사이의 시간을 입력해 주세요.</Text> : null}
              <Text style={styles.caption}>체감 강도 (선택)</Text>
              <EffortChoices selected={intensity} disabled={saving} onSelect={(score) => setIntensity((value) => value === score ? undefined : score)} />
              {error ? <FlowStatusCard error={error} /> : null}
              <PrimaryButton label={saving ? "저장 중…" : "운동 기록 저장"} disabled={saving || !validDuration} onPress={() => void saveWorkout()} />
            </ScrollView>
          </View>
        </View>
      </Modal>
      <Modal transparent visible={visible && discarding} animationType="fade" onRequestClose={() => setDiscarding(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.finishSheet} accessibilityViewIsModal>
            <View style={styles.sheetContent}>
              <Text accessibilityRole="header" style={styles.sectionTitle}>운동을 취소할까요?</Text>
              <Text style={styles.body}>오늘 아직 저장하지 않은 세트만 사라져요.</Text>
              <PrimaryButton label="계속 운동하기" onPress={() => setDiscarding(false)} />
              <TouchableOpacity style={styles.textButton} onPress={clearDraft} accessibilityRole="button">
                <Text style={styles.caption}>저장하지 않고 나가기</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

function ExerciseEntry({ exercise, sets, active, expanded, effort, onExpand, onUpdate, onCheck, onSetCount, onEffort }: {
  readonly exercise: WorkoutExercise;
  readonly sets: SetDraft[];
  readonly active: boolean;
  readonly expanded: boolean;
  readonly effort?: WorkoutEffort;
  readonly onExpand: () => void;
  readonly onUpdate: (index: number, patch: Partial<SetDraft>) => void;
  readonly onCheck: (index: number) => void;
  readonly onSetCount: (add: boolean) => void;
  readonly onEffort: (effort: WorkoutEffort) => void;
}) {
  const timed = isTimedExercise(exercise);
  const last = exercise.lastPerformance;
  const count = sets.filter((item) => item.completed).length;
  const [showEffort, setShowEffort] = useState(false);
  const unit = timed ? (exercise.reps.includes("/측") ? "한쪽 초" : "시간(초)") : (exercise.reps.includes("/측") ? "한쪽 횟수" : "횟수");
  const target = [!timed && exercise.recommendedLoadKg !== undefined ? `${exercise.recommendedLoadKg}kg` : undefined,
    !timed && exercise.recommendedReps !== undefined ? `${exercise.recommendedReps}회` : exercise.reps].filter(Boolean).join(" × ");
  const selectedEffort = effortOptions.find((option) => option.key === effort)?.score;
  return (
    <View style={[styles.exercise, expanded && styles.exerciseExpanded]}>
      <TouchableOpacity onPress={onExpand} accessibilityRole="button" aria-expanded={expanded} style={styles.exerciseHeader}>
        <View style={styles.headerCopy}>
          <Text style={styles.strong}>{exercise.name}</Text>
          <Text style={styles.caption}>{exercise.sets}세트 · {target}</Text>
        </View>
        {active ? <Text style={count >= exercise.sets ? styles.eyebrow : styles.caption}>{count}/{exercise.sets}</Text> : null}
        {expanded ? <ChevronUp size={19} color={colors.muted} /> : <ChevronDown size={19} color={colors.muted} />}
      </TouchableOpacity>
      {expanded ? (
        <View style={styles.exerciseBody}>
          {!timed ? <Text style={styles.caption}>{exercise.targetRir === 0 ? "추가 반복 여유 없음" : `${exercise.targetRir}회 정도 더 할 수 있을 때 멈춰요`}</Text> : null}
          <Text style={styles.caption}>{exercise.recommendationReason}</Text>
          {last && !last.completedSets ? (
            <Text style={styles.previous}>지난번 · {[last.loadKg !== undefined ? `${last.loadKg}kg` : "", last.repsCompleted !== undefined ? `${last.repsCompleted}회` : "", `${last.setsCompleted}세트`].filter(Boolean).join(" · ")}</Text>
          ) : null}
          {active ? (
            <>
              <View style={styles.setRow}>
                <Text style={[styles.columnLabel, styles.setNumber]}>세트</Text>
                <Text style={[styles.columnLabel, styles.previousColumn]}>지난번</Text>
                {!timed ? <Text style={[styles.columnLabel, styles.inputColumn]}>무게(kg)</Text> : null}
                <Text style={[styles.columnLabel, styles.inputColumn]}>{unit}</Text>
                <Text style={[styles.columnLabel, styles.checkColumn]}>완료</Text>
              </View>
              {sets.map((item, index) => {
                const previous = last?.completedSets?.find((prior) => prior.setNumber === index + 1);
                const previousText = previous && [!timed && previous.loadKg !== undefined ? `${previous.loadKg}kg` : "", timed ? previous.durationSeconds !== undefined ? `${previous.durationSeconds}초` : "" : previous.repsCompleted !== undefined ? `${previous.repsCompleted}회` : ""].filter(Boolean).join(" × ");
                const invalid = parseSetDraft(item, index, timed) === null;
                return (
                  <View key={index}>
                    <View style={[styles.setRow, styles.setValues, item.completed && styles.checkedRow]}>
                      <Text style={[styles.strong, styles.setNumber]}>{index + 1}</Text>
                      <Text style={[styles.previous, styles.previousColumn]}>{previousText || "—"}</Text>
                      {!timed ? (
                        <View style={styles.inputColumn}><SetInput label={`${exercise.name} ${index + 1}세트 무게(kg)`} decimal value={item.load} onChange={(load) => onUpdate(index, { load })} /></View>
                      ) : null}
                      <View style={styles.inputColumn}><SetInput label={`${exercise.name} ${index + 1}세트 ${unit}`} value={item.amount} onChange={(amount) => onUpdate(index, { amount })} /></View>
                      <TouchableOpacity accessibilityRole="checkbox" accessibilityLabel={`${exercise.name} ${index + 1}세트 완료`} aria-checked={item.completed} disabled={invalid && !item.completed} onPress={() => onCheck(index)} style={[styles.checkButton, item.completed && styles.checkedButton, invalid && !item.completed && styles.disabled]}>
                        <Check size={18} strokeWidth={2.5} color={item.completed ? colors.surface : colors.muted} />
                      </TouchableOpacity>
                    </View>
                    {invalid ? <Text style={styles.validation}>{timed ? "시간은 1~600초로 입력해 주세요." : "무게는 0~500kg, 횟수는 1~100회로 입력해 주세요."}</Text> : null}
                  </View>
                );
              })}
              <View style={styles.setActions}>
                <TouchableOpacity style={[styles.textButton, sets.length >= maxWorkoutSets && styles.disabled]} disabled={sets.length >= maxWorkoutSets} accessibilityRole="button" onPress={() => onSetCount(true)}>
                  <Plus size={16} color={colors.leaf} /><Text style={styles.eyebrow}>세트 추가</Text>
                </TouchableOpacity>
                {sets.length > 1 && !sets[sets.length - 1].completed ? (
                  <TouchableOpacity style={styles.iconButton} accessibilityRole="button" accessibilityLabel="마지막 세트 빼기" onPress={() => onSetCount(false)}>
                    <Minus size={18} color={colors.muted} />
                  </TouchableOpacity>
                ) : null}
                {count > 0 ? (
                  <TouchableOpacity style={styles.textButton} accessibilityRole="button" aria-expanded={showEffort} onPress={() => setShowEffort((value) => !value)}>
                    <Text style={styles.caption}>{showEffort ? "체감 접기" : "종목 체감"}</Text>
                  </TouchableOpacity>
                ) : null}
              </View>
              {showEffort && count > 0 ? (
                <EffortChoices selected={selectedEffort} onSelect={(score) => {
                  const option = effortOptions.find((value) => value.score === score);
                  if (option) onEffort(option.key);
                }} />
              ) : null}
            </>
          ) : (
            <Text style={styles.caption}>{exercise.rationale} · 세트 사이 {exercise.restSeconds}초 휴식</Text>
          )}
        </View>
      ) : null}
    </View>
  );
}

function EffortChoices({ selected, disabled, onSelect }: { readonly selected?: number; readonly disabled?: boolean; readonly onSelect: (value: number) => void }) {
  return (
    <View style={styles.effortRow} accessibilityRole="radiogroup" accessibilityLabel="체감 강도">
      {effortOptions.map((option) => (
        <TouchableOpacity key={option.key} disabled={disabled} accessibilityRole="radio" aria-checked={selected === option.score} onPress={() => onSelect(option.score)} style={[styles.effortButton, selected === option.score && styles.checkedButton]}>
          <Text style={[styles.strong, styles.effortLabel, selected === option.score && styles.primaryText]}>{option.label}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

function SetInput({ label, value, onChange, decimal, disabled }: { readonly label: string; readonly value: string; readonly onChange: (value: string) => void; readonly decimal?: boolean; readonly disabled?: boolean }) {
  return <TextInput accessibilityLabel={label} value={value} editable={!disabled} onChangeText={onChange} inputMode={decimal ? "decimal" : "numeric"} selectTextOnFocus placeholder="—" placeholderTextColor={colors.muted} maxLength={decimal ? 8 : 3} style={styles.setInput} />;
}

function PrimaryButton({ label, disabled, onPress }: { readonly label: string; readonly disabled?: boolean; readonly onPress: () => void }) {
  return (
    <TouchableOpacity accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress} style={[styles.primary, disabled && styles.disabled]}>
      <Text style={styles.primaryText}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { gap: spacing.md, padding: spacing.md, paddingBottom: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", gap: spacing.md, paddingHorizontal: spacing.xs, paddingVertical: spacing.sm },
  headerCopy: { flex: 1, minWidth: 0, gap: 2 },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.screenTitle },
  sectionTitle: { color: colors.ink, ...typography.sectionTitle },
  body: { color: colors.body, ...typography.body },
  strong: { color: colors.ink, ...typography.bodyStrong },
  caption: { color: colors.muted, ...typography.caption },
  saved: { color: colors.leaf, ...typography.bodyStrong },
  exercise: { backgroundColor: colors.surface, borderColor: colors.hairline, borderWidth: 1, borderRadius: 8 },
  exerciseExpanded: { borderColor: colors.leaf },
  exerciseHeader: { flexDirection: "row", alignItems: "center", gap: spacing.sm, minHeight: 64, padding: spacing.md },
  exerciseBody: { padding: spacing.sm, paddingTop: 0, gap: spacing.xs },
  setRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  setValues: { minHeight: 48, borderTopWidth: 1, borderTopColor: colors.hairline, paddingVertical: 2 },
  checkedRow: { backgroundColor: colors.leafTint },
  columnLabel: { color: colors.muted, ...typography.caption, textAlign: "center" },
  setNumber: { width: 28, textAlign: "center" },
  previousColumn: { flex: 1.2, minWidth: 0, textAlign: "center" },
  inputColumn: { flex: 1, minWidth: 0 },
  checkColumn: { width: 44, textAlign: "center" },
  previous: { color: colors.body, ...typography.caption },
  setInput: { minHeight: 44, paddingHorizontal: 3, paddingVertical: 0, borderColor: colors.hairline, borderWidth: 1, borderRadius: 8, backgroundColor: colors.surface, textAlign: "center", color: colors.ink, ...typography.bodyStrong },
  checkButton: { width: 44, height: 44, alignItems: "center", justifyContent: "center", borderRadius: 8, borderColor: colors.hairline, borderWidth: 1, backgroundColor: colors.surface },
  checkedButton: { borderColor: colors.leaf, backgroundColor: colors.leaf },
  setActions: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: spacing.xs },
  textButton: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: spacing.xs, paddingHorizontal: spacing.xs },
  iconButton: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  validation: { color: colors.body, ...typography.caption, paddingVertical: 2 },
  footer: { paddingHorizontal: spacing.md, paddingVertical: spacing.xs, gap: spacing.xs, backgroundColor: colors.canvas, borderTopWidth: 1, borderTopColor: colors.hairline },
  restBanner: { flexDirection: "row", alignItems: "center", gap: spacing.sm, backgroundColor: colors.leafTint, borderRadius: 8, paddingLeft: spacing.md },
  effortRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  effortButton: { flexGrow: 1, flexBasis: 80, minHeight: 44, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: colors.hairline, backgroundColor: colors.surface, borderRadius: 8, paddingHorizontal: 4, paddingVertical: spacing.xs },
  effortLabel: { textAlign: "center" },
  primary: { minHeight: 48, borderRadius: 8, alignItems: "center", justifyContent: "center", backgroundColor: colors.leaf, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  primaryText: { color: colors.surface, ...typography.bodyStrong, textAlign: "center" },
  disabled: { opacity: 0.48 },
  modalOverlay: { flex: 1, justifyContent: "flex-end", alignItems: "center", backgroundColor: "rgba(22, 33, 26, 0.45)" },
  finishSheet: { backgroundColor: colors.canvas, width: "100%", maxWidth: 520, maxHeight: "88%", borderTopLeftRadius: radii.control, borderTopRightRadius: radii.control },
  sheetContent: { padding: spacing.lg, paddingBottom: spacing.xl, gap: spacing.sm },
  sheetHeader: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  finishDuration: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: spacing.sm },
  minutesInput: { width: 92, flexDirection: "row", alignItems: "center", justifyContent: "flex-end", gap: spacing.xs },
  minutesValue: { width: 64 },
  historyRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, borderTopWidth: 1, borderTopColor: colors.hairline, paddingTop: spacing.sm },
  progressTrack: { height: 8, overflow: "hidden", borderRadius: radii.pill, backgroundColor: colors.leafMuted },
  progressFill: { height: "100%", borderRadius: radii.pill, backgroundColor: colors.leaf }
});
