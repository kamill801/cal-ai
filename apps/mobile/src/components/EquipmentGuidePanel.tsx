import type { EquipmentCatalog, EquipmentGuide, EquipmentIdentification, EquipmentId, WorkoutExercise } from "@cal-ai/shared";
import { ArrowLeft, Camera, Check, ChevronRight, ExternalLink, ImagePlus, Search, ShieldCheck, X } from "lucide-react-native";
import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Image, Linking, Modal, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { ApiClientError } from "../api/client";
import { isYoutubeGuideUrl, type EquipmentGuideActions } from "../api/equipmentGuide";
import { captureMealImageWithCamera, pickMealImageFromLibrary } from "../media/mealImagePicker";
import { colors, radii, spacing, typography } from "../theme";
import { TrustBuddy } from "./TrustBuddy";

export function EquipmentGuidePanel({ actions, exercises = [], active = true }: { readonly actions: EquipmentGuideActions; readonly exercises?: WorkoutExercise[]; readonly active?: boolean }) {
  const [open, setOpen] = useState(false);
  const [catalog, setCatalog] = useState<EquipmentCatalog>();
  const [catalogAttempt, setCatalogAttempt] = useState(0);
  const [busy, setBusy] = useState<"catalog" | "photo" | "guide" | undefined>();
  const [error, setError] = useState<string>();
  const [photoUri, setPhotoUri] = useState<string>();
  const [identification, setIdentification] = useState<EquipmentIdentification>();
  const [selectedId, setSelectedId] = useState<EquipmentId>();
  const [query, setQuery] = useState("");
  const [showAll, setShowAll] = useState(true);
  const [consent, setConsent] = useState(false);
  const [guide, setGuide] = useState<EquipmentGuide>();
  const requestVersion = useRef(0);
  const actionsRef = useRef(actions);
  actionsRef.current = actions;
  const photoOperation = useRef<AbortController | undefined>(undefined);
  const photoReference = useRef<string | undefined>(undefined);

  function disposePhoto(): void {
    const uri = photoReference.current;
    if (uri?.startsWith("blob:")) URL.revokeObjectURL(uri);
    photoReference.current = undefined;
    setPhotoUri(undefined);
  }

  useEffect(() => () => {
    requestVersion.current += 1;
    photoOperation.current?.abort();
    const uri = photoReference.current;
    if (uri?.startsWith("blob:")) URL.revokeObjectURL(uri);
  }, []);

  useEffect(() => {
    if (!open) return;
    const version = ++requestVersion.current;
    setBusy("catalog");
    setError(undefined);
    setCatalog(undefined);
    void actionsRef.current.getCatalog().then((value) => {
      if (version === requestVersion.current) setCatalog(value);
    }).catch((value) => {
      if (version === requestVersion.current) setError(errorMessage(value));
    }).finally(() => {
      if (version === requestVersion.current) setBusy(undefined);
    });
    return () => { requestVersion.current += 1; };
  }, [open, catalogAttempt]);

  function close(): void {
    requestVersion.current += 1;
    photoOperation.current?.abort();
    setOpen(false);
    setBusy(undefined);
    disposePhoto();
    setIdentification(undefined);
    setGuide(undefined);
    setSelectedId(undefined);
    setQuery("");
    setShowAll(true);
    setConsent(false);
    setError(undefined);
  }

  useEffect(() => {
    if (!active) close();
  }, [active]);

  async function choosePhoto(source: "camera" | "library"): Promise<void> {
    if (busy || !consent) return;
    const version = ++requestVersion.current;
    const operation = new AbortController();
    photoOperation.current = operation;
    setBusy("photo");
    setError(undefined);
    setIdentification(undefined);
    setSelectedId(undefined);
    setGuide(undefined);
    try {
      const result = await (source === "camera" ? captureMealImageWithCamera() : pickMealImageFromLibrary());
      if (version !== requestVersion.current) {
        if (result.status === "selected" && result.image.uri.startsWith("blob:")) URL.revokeObjectURL(result.image.uri);
        return;
      }
      if (result.status === "cancelled") return;
      if (result.status !== "selected") {
        setError({ permission_denied: "카메라나 사진 접근 권한을 허용해 주세요.", camera_unavailable: "이 기기에서는 카메라를 열 수 없어요. 사진을 선택해 주세요.", unsupported_type: "JPG, PNG, WebP 사진을 선택해 주세요.", too_large: "사진 크기를 줄이지 못했어요. 더 작은 사진을 선택해 주세요.", read_failed: "사진을 읽지 못했어요. 다른 사진을 선택해 주세요." }[result.status]);
        return;
      }
      disposePhoto();
      photoReference.current = result.image.uri;
      setPhotoUri(result.image.uri);
      const value = await actionsRef.current.identify(result.image, operation.signal);
      if (version !== requestVersion.current) return;
      setIdentification(value);
      setSelectedId(value.equipmentId ?? undefined);
      setShowAll(!value.equipmentId);
      setQuery("");
    } catch (value) {
      if (version === requestVersion.current) setError(errorMessage(value));
    } finally {
      if (version === requestVersion.current) setBusy(undefined);
    }
  }

  async function confirmEquipment(): Promise<void> {
    if (!selectedId || busy) return;
    const version = ++requestVersion.current;
    setBusy("guide");
    setError(undefined);
    try {
      const value = await actionsRef.current.getGuide(selectedId);
      if (version === requestVersion.current) setGuide(value);
    } catch (value) {
      if (version === requestVersion.current) setError(errorMessage(value));
    } finally {
      if (version === requestVersion.current) setBusy(undefined);
    }
  }

  async function openVideo(url: string): Promise<void> {
    if (!isYoutubeGuideUrl(url)) {
      setError("영상 주소를 확인하지 못했어요. 다른 링크를 선택해 주세요.");
      return;
    }
    try { await Linking.openURL(url); }
    catch { setError("YouTube를 열지 못했어요. 잠시 뒤 다시 시도해 주세요."); }
  }

  function findAnotherEquipment(): void {
    setGuide(undefined);
    setSelectedId(undefined);
    setShowAll(true);
    setIdentification(undefined);
    disposePhoto();
    setQuery("");
    setError(undefined);
  }

  const options = (catalog?.items ?? []).filter((item) =>
    (showAll || item.id === selectedId) && (!query.trim() || `${item.name} ${item.exercises.join(" ")}`.replace(/\s/g, "").includes(query.trim().replace(/\s/g, "")))
  );
  const matchedExercises = guide ? exercises.filter((exercise) => guide.exercises.includes(exercise.name)) : [];

  return <>
    <TouchableOpacity style={styles.entry} onPress={() => { if (active) setOpen(true); }} accessibilityRole="button" accessibilityLabel="운동 기구 사용법 찾기">
      <View style={styles.entryIcon}><Camera color={colors.leaf} size={24} /></View>
      <View style={styles.flex}><Text style={styles.entryTitle}>처음 보는 기구인가요?</Text><Text style={styles.caption}>기구 이름과 사용법을 함께 확인해요</Text></View>
      <ChevronRight size={20} color={colors.muted} />
    </TouchableOpacity>
    <Modal visible={open && active} animationType="slide" onRequestClose={close}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.topBar}>
          <TouchableOpacity style={styles.iconButton} onPress={close} accessibilityRole="button" accessibilityLabel="운동 화면으로 돌아가기"><ArrowLeft size={24} color={colors.ink} /></TouchableOpacity>
          <Text style={styles.topTitle}>기구 사용법</Text>
          <TouchableOpacity style={styles.iconButton} onPress={close} accessibilityRole="button" accessibilityLabel="기구 가이드 닫기"><X size={22} color={colors.ink} /></TouchableOpacity>
        </View>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag">
          {guide ? <>
            <View style={styles.header}>
              <View style={styles.flex}><Text style={styles.eyebrow}>사용법을 확인하고 시작해요</Text><Text style={styles.title}>{guide.name}</Text></View>
              <TrustBuddy pose="workout" size={86} />
            </View>
            <View style={styles.notice}><ShieldCheck size={20} color={colors.leaf} /><Text style={[styles.body, styles.flex]}>{guide.safetyNote}</Text></View>
            {matchedExercises.length > 0 ? <View style={styles.section}><Text style={styles.sectionTitle}>오늘 루틴과 연결돼요</Text>{matchedExercises.map((item) => <Text key={item.id} style={styles.body}>{item.name} · {item.sets}세트 · {item.reps}</Text>)}</View> : null}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>YouTube 사용법 영상</Text>
              {guide.videos.map((video) => <TouchableOpacity key={video.videoId} style={styles.videoRow} onPress={() => void openVideo(video.url)} accessibilityRole="link" accessibilityLabel={`${video.title}, YouTube에서 열기`}>
                <View style={styles.videoIcon}><ExternalLink size={20} color={colors.fat} /></View>
                <View style={styles.flex}><Text style={styles.rowTitle}>{video.title}</Text><Text style={styles.caption}>{video.channelTitle}</Text></View><ChevronRight size={18} color={colors.muted} />
              </TouchableOpacity>)}
              <TouchableOpacity style={styles.secondary} onPress={() => void openVideo(guide.searchUrl)} accessibilityRole="link" accessibilityLabel={`${guide.name} 사용법 YouTube 검색`}><Search color={colors.leaf} size={18} /><Text style={styles.secondaryText}>{guide.videos.length ? "YouTube에서 더 찾아보기" : "YouTube에서 사용법 보기"}</Text><ExternalLink color={colors.leaf} size={16} /></TouchableOpacity>
              <Text style={styles.caption}>외부 영상은 제작자마다 설명이 달라요. 기구의 안내판을 함께 확인하고, 통증이 있으면 멈춰 주세요.</Text>
            </View>
            <TouchableOpacity style={styles.primary} onPress={close} accessibilityRole="button"><Text style={styles.primaryText}>운동 기록으로 돌아가기</Text></TouchableOpacity>
            <TouchableOpacity style={styles.textButton} onPress={findAnotherEquipment} accessibilityRole="button"><Text style={styles.secondaryText}>다른 기구 찾기</Text></TouchableOpacity>
          </> : <>
            <View style={styles.header}><View style={styles.flex}><Text style={styles.eyebrow}>낯선 기구도 차근차근</Text><Text style={styles.title}>어떤 기구인지{ "\n" }함께 찾아봐요</Text></View><TrustBuddy pose="workout" size={86} /></View>
            {busy === "catalog" ? <ActivityIndicator color={colors.leaf} accessibilityLabel="기구 목록 불러오는 중" /> : null}
            {catalog?.photoIdentificationAvailable ? <>
              <TouchableOpacity style={styles.consentRow} onPress={() => setConsent(!consent)} disabled={Boolean(busy)} accessibilityRole="checkbox" accessibilityLabel="기구 사진 AI 분석에 동의" accessibilityState={{ checked: consent, disabled: Boolean(busy) }}>
                <View style={[styles.checkbox, consent && styles.checkboxChecked]}>{consent ? <Check color={colors.surface} size={17} /> : null}</View><Text style={[styles.caption, styles.flex]}>기구 사진을 OpenAI로 보내 분석하는 데 동의해요. 서버 사진은 분석 뒤 삭제하며, 전송이나 삭제가 중단되면 보관 기간 안에 정리해요. 다른 사람이 나오지 않게 찍어 주세요.</Text>
              </TouchableOpacity>
              <View style={styles.photoButtons}>
                <TouchableOpacity style={[styles.photoButton, (!consent || busy) && styles.disabled]} disabled={!consent || Boolean(busy)} onPress={() => void choosePhoto("camera")} accessibilityRole="button" accessibilityLabel="운동 기구 사진 찍기" accessibilityState={{ disabled: !consent || Boolean(busy) }}><Camera size={22} color={colors.leaf} /><Text style={styles.secondaryText}>사진 찍기</Text></TouchableOpacity>
                <TouchableOpacity style={[styles.photoButton, (!consent || busy) && styles.disabled]} disabled={!consent || Boolean(busy)} onPress={() => void choosePhoto("library")} accessibilityRole="button" accessibilityLabel="운동 기구 사진 선택" accessibilityState={{ disabled: !consent || Boolean(busy) }}><ImagePlus size={22} color={colors.leaf} /><Text style={styles.secondaryText}>사진 선택</Text></TouchableOpacity>
              </View>
            </> : catalog ? <Text style={styles.body}>기구 이름을 선택하면 사용법을 바로 찾아볼 수 있어요.</Text> : null}
            {photoUri ? <Image source={{ uri: photoUri }} style={styles.photo} accessibilityLabel="선택한 운동 기구 사진" resizeMode="cover" /> : null}
            {busy === "photo" ? <View style={styles.loading} accessibilityLiveRegion="polite"><ActivityIndicator color={colors.leaf} /><Text style={styles.body}>기구의 모양을 확인하고 있어요</Text></View> : null}
            {identification ? <View style={styles.result} accessibilityLiveRegion="polite">
              <Text style={styles.sectionTitle}>{identification.equipmentId ? "이 기구가 맞나요?" : "사진만으로 구분하기 어려워요"}</Text>
              <Text style={styles.caption}>{identification.confidence === "low" || identification.confidence === "none" ? "이름을 직접 확인해 주세요. 다른 각도로 찍어도 좋아요." : "사진에서 보이는 모양으로 추정했어요. 기구 안내판과 비교해 주세요."}</Text>
              {identification.visibleEvidence.map((value, index) => <Text key={index} style={styles.caption}>{value}</Text>)}
              {identification.cleanupPending ? <Text style={styles.caption}>분석은 완료됐고 서버 사진 정리는 재시도 중이에요.</Text> : null}
            </View> : null}
            {catalog ? <View style={styles.section}>
              <View style={styles.sectionHeading}><Text style={styles.sectionTitle}>{selectedId && !showAll ? "확인할 기구" : "기구 이름으로 찾기"}</Text>{!showAll ? <TouchableOpacity onPress={() => { setSelectedId(undefined); setShowAll(true); }} style={styles.smallButton} accessibilityRole="button"><Text style={styles.secondaryText}>다른 기구</Text></TouchableOpacity> : null}</View>
              {showAll ? <View style={styles.search}><Search color={colors.muted} size={18} /><TextInput style={styles.searchInput} value={query} onChangeText={(value) => { setQuery(value); setSelectedId(undefined); }} placeholder="기구 또는 운동 이름" placeholderTextColor={colors.muted} accessibilityLabel="기구 또는 운동 이름 검색" /></View> : null}
              {options.map((item) => <TouchableOpacity key={item.id} style={styles.option} onPress={() => { setSelectedId(item.id); setShowAll(false); setQuery(""); setError(undefined); }} disabled={Boolean(busy)} accessibilityRole="radio" accessibilityLabel={item.name} accessibilityState={{ checked: selectedId === item.id, disabled: Boolean(busy) }}>
                <View style={[styles.radio, selectedId === item.id && styles.radioSelected]}>{selectedId === item.id ? <View style={styles.radioDot} /> : null}</View>
                <View style={styles.flex}><Text style={styles.rowTitle}>{item.name}</Text>{item.exercises.length ? <Text style={styles.caption} numberOfLines={1}>{item.exercises.slice(0, 2).join(" · ")}</Text> : null}</View>
              </TouchableOpacity>)}
              {!options.length ? <Text style={styles.body}>등록된 기구를 찾지 못했어요. 이름을 바꿔 검색하거나 헬스장 직원에게 확인해 주세요.</Text> : null}
              <TouchableOpacity style={[styles.primary, (!selectedId || busy) && styles.disabled]} onPress={() => void confirmEquipment()} disabled={!selectedId || Boolean(busy)} accessibilityRole="button" accessibilityState={{ disabled: !selectedId || Boolean(busy), busy: busy === "guide" }}><Text style={styles.primaryText}>{busy === "guide" ? "사용법 찾는 중" : "이 기구 사용법 보기"}</Text></TouchableOpacity>
            </View> : null}
          </>}
          {error ? <Text style={styles.error} accessibilityRole="alert" accessibilityLiveRegion="polite">{error}</Text> : null}
          {!catalog && !busy && error ? <TouchableOpacity style={styles.secondary} onPress={() => setCatalogAttempt((value) => value + 1)} accessibilityRole="button"><Text style={styles.secondaryText}>다시 불러오기</Text></TouchableOpacity> : null}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  </>;
}

function errorMessage(value: unknown): string {
  return value instanceof ApiClientError ? value.userMessage : "잠시 연결하지 못했어요. 다시 시도해 주세요.";
}

const styles = StyleSheet.create({
  entry: { flexDirection: "row", alignItems: "center", gap: spacing.md, paddingVertical: spacing.md, borderTopWidth: 1, borderBottomWidth: 1, borderColor: colors.hairline },
  entryIcon: { width: 46, height: 46, borderRadius: radii.control, backgroundColor: colors.skySoft, alignItems: "center", justifyContent: "center" },
  entryTitle: { color: colors.ink, ...typography.bodyStrong },
  flex: { flex: 1, minWidth: 0, gap: spacing.xs },
  safeArea: { flex: 1, backgroundColor: colors.canvasWarm },
  topBar: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", padding: spacing.sm, borderBottomWidth: 1, borderColor: colors.hairline },
  iconButton: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  topTitle: { color: colors.ink, ...typography.sectionTitle },
  content: { gap: spacing.lg, padding: spacing.lg, paddingBottom: 36, width: "100%", maxWidth: 640, alignSelf: "center" },
  header: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  eyebrow: { color: colors.leaf, ...typography.caption },
  title: { color: colors.ink, ...typography.screenTitle },
  body: { color: colors.body, ...typography.body },
  caption: { color: colors.muted, ...typography.caption },
  consentRow: { flexDirection: "row", gap: spacing.md, alignItems: "center", minHeight: 48 },
  checkbox: { width: 24, height: 24, alignItems: "center", justifyContent: "center", borderRadius: 6, borderWidth: 1, borderColor: colors.muted },
  checkboxChecked: { borderColor: colors.leaf, backgroundColor: colors.leaf },
  photoButtons: { flexDirection: "row", gap: spacing.md },
  photoButton: { flex: 1, minHeight: 64, alignItems: "center", justifyContent: "center", gap: spacing.xs, borderWidth: 1, borderColor: colors.hairline, backgroundColor: colors.surface, borderRadius: radii.control },
  photo: { width: "100%", aspectRatio: 4 / 3, borderRadius: radii.photo, backgroundColor: colors.surfaceSoft },
  loading: { flexDirection: "row", gap: spacing.sm, alignItems: "center" },
  result: { paddingVertical: spacing.md, gap: spacing.sm, borderBottomWidth: 1, borderColor: colors.hairline },
  section: { gap: spacing.md, paddingTop: spacing.md },
  sectionHeading: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: spacing.sm },
  sectionTitle: { color: colors.ink, ...typography.sectionTitle },
  smallButton: { minHeight: 44, justifyContent: "center", paddingHorizontal: spacing.sm },
  search: { flexDirection: "row", alignItems: "center", gap: spacing.sm, borderWidth: 1, borderColor: colors.hairline, borderRadius: radii.control, paddingHorizontal: spacing.md, backgroundColor: colors.surface },
  searchInput: { flex: 1, minWidth: 0, minHeight: 48, color: colors.ink, ...typography.body },
  option: { flexDirection: "row", gap: spacing.md, alignItems: "center", minHeight: 62, paddingVertical: spacing.sm, borderBottomWidth: 1, borderColor: colors.hairline },
  radio: { width: 22, height: 22, borderWidth: 1.5, borderRadius: 11, borderColor: colors.muted, alignItems: "center", justifyContent: "center" },
  radioSelected: { borderColor: colors.leaf },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: colors.leaf },
  rowTitle: { color: colors.ink, ...typography.bodyStrong },
  primary: { minHeight: 52, alignItems: "center", justifyContent: "center", padding: spacing.md, backgroundColor: colors.leaf, borderRadius: radii.control },
  primaryText: { color: colors.surface, ...typography.bodyStrong },
  secondary: { flexDirection: "row", flexWrap: "wrap", minHeight: 50, gap: spacing.sm, alignItems: "center", justifyContent: "center", padding: spacing.md, borderWidth: 1, borderColor: colors.hairline, borderRadius: radii.control, backgroundColor: colors.surface },
  secondaryText: { color: colors.leaf, ...typography.bodyStrong },
  textButton: { minHeight: 44, alignItems: "center", justifyContent: "center" },
  disabled: { opacity: 0.45 },
  notice: { flexDirection: "row", gap: spacing.sm, alignItems: "center", backgroundColor: colors.leafTint, padding: spacing.md, borderRadius: radii.control },
  videoRow: { flexDirection: "row", gap: spacing.md, alignItems: "center", minHeight: 76, borderBottomWidth: 1, borderColor: colors.hairline, paddingVertical: spacing.md },
  videoIcon: { width: 40, height: 40, alignItems: "center", justifyContent: "center", borderRadius: radii.control, backgroundColor: colors.fatSoft },
  error: { color: colors.danger, ...typography.body }
});
