import type { ConfidenceGroup, ConfidenceLabel } from "@cal-ai/shared";
import type { ImageSourcePropType } from "react-native";
import { Image, StyleSheet, Text, View } from "react-native";
import { colors, radii, spacing, typography } from "../theme";
import { ConfidencePill } from "./ConfidencePill";

export function MealPhotoFrame({
  source,
  stageText,
  confidenceLabel,
  confidenceGroup
}: {
  source: ImageSourcePropType;
  stageText: string;
  confidenceLabel?: ConfidenceLabel;
  confidenceGroup?: ConfidenceGroup;
}) {
  return (
    <View style={styles.frame}>
      <Image source={source} resizeMode="cover" style={styles.image} accessibilityLabel="분석 중인 음식 사진" />
      <View style={styles.overlay}>
        <Text style={styles.stage}>{stageText}</Text>
        {confidenceLabel ? <ConfidencePill label={confidenceLabel} group={confidenceGroup} /> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  frame: {
    overflow: "hidden",
    borderColor: colors.hairline,
    borderRadius: radii.photo,
    borderWidth: 1,
    backgroundColor: colors.surfaceSoft
  },
  image: {
    width: "100%",
    height: 218
  },
  overlay: {
    gap: spacing.sm,
    padding: spacing.md,
    backgroundColor: colors.surface
  },
  stage: {
    color: colors.ink,
    ...typography.sectionTitle
  }
});
