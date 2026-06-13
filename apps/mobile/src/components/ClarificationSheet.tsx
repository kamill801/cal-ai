import type { ClarificationQuestion, RangeNarrowingResult } from "@cal-ai/shared";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { colors, radii, shadows, spacing, typography } from "../theme";
import { RangeNarrowing } from "./RangeNarrowing";

export function ClarificationSheet({
  question,
  narrowing,
  selectedValue,
  onSelect,
  onSkip
}: {
  question: ClarificationQuestion;
  narrowing?: RangeNarrowingResult;
  selectedValue?: string;
  onSelect: (value: string) => void;
  onSkip: () => void;
}) {
  return (
    <View style={styles.sheet} accessibilityLabel="한 번만 확인하는 보정 질문">
      <View style={styles.handle} />
      <Text style={styles.eyebrow}>한 번만 확인할게요</Text>
      <Text style={styles.question}>{question.question}</Text>
      <Text style={styles.helper}>{question.helperText}</Text>
      <View style={styles.chipWrap}>
        {question.options.map((option) => {
          const selected = selectedValue === option.value;
          return (
            <TouchableOpacity
              key={option.value}
              activeOpacity={0.86}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              style={[styles.chip, selected && styles.chipSelected]}
              onPress={() => onSelect(option.value)}
            >
              <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{option.label}</Text>
              {option.helperText ? <Text style={[styles.chipHelper, selected && styles.chipHelperSelected]}>{option.helperText}</Text> : null}
            </TouchableOpacity>
          );
        })}
      </View>
      {narrowing ? <RangeNarrowing narrowing={narrowing} /> : null}
      <TouchableOpacity activeOpacity={0.82} style={styles.skipButton} onPress={onSkip}>
        <Text style={styles.skipText}>잘 모르겠다면 그대로 저장해도 돼요</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  sheet: {
    gap: spacing.md,
    borderTopLeftRadius: radii.sheet,
    borderTopRightRadius: radii.sheet,
    borderColor: colors.hairline,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg,
    ...shadows.sheet
  },
  handle: {
    alignSelf: "center",
    width: 42,
    height: 4,
    borderRadius: radii.pill,
    backgroundColor: colors.hairline
  },
  eyebrow: {
    color: colors.leaf,
    ...typography.caption
  },
  question: {
    color: colors.ink,
    ...typography.screenTitle
  },
  helper: {
    color: colors.body,
    ...typography.body
  },
  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm
  },
  chip: {
    minWidth: 112,
    flexGrow: 1,
    flexBasis: "46%",
    borderColor: colors.hairline,
    borderRadius: radii.control,
    borderWidth: 1,
    backgroundColor: colors.paper,
    padding: spacing.md
  },
  chipSelected: {
    borderColor: colors.leaf,
    backgroundColor: colors.leafSoft
  },
  chipText: {
    color: colors.ink,
    ...typography.bodyStrong
  },
  chipTextSelected: {
    color: colors.leaf
  },
  chipHelper: {
    color: colors.muted,
    marginTop: spacing.xs,
    ...typography.caption
  },
  chipHelperSelected: {
    color: colors.leaf
  },
  skipButton: {
    minHeight: 44,
    justifyContent: "center"
  },
  skipText: {
    color: colors.muted,
    textAlign: "center",
    ...typography.caption
  }
});
