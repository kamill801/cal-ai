import type { ConfidenceGroup, ConfidenceLabel } from "@cal-ai/shared";
import type { ImageSourcePropType } from "react-native";
import { Image, StyleSheet, Text, View } from "react-native";
import { colors, radii, shadows, spacing, typography } from "../theme";
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
      <View pointerEvents="none" style={[styles.scanCorner, styles.scanCornerTopLeft]} />
      <View pointerEvents="none" style={[styles.scanCorner, styles.scanCornerTopRight]} />
      <View pointerEvents="none" style={[styles.scanCorner, styles.scanCornerBottomLeft]} />
      <View pointerEvents="none" style={[styles.scanCorner, styles.scanCornerBottomRight]} />
      <View style={styles.overlay}>
        <Text style={styles.stage}>{stageText}</Text>
        {confidenceLabel ? <ConfidencePill label={confidenceLabel} group={confidenceGroup} /> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  frame: {
    position: "relative",
    overflow: "hidden",
    borderColor: colors.hairline,
    borderRadius: radii.photo,
    borderWidth: 1,
    backgroundColor: colors.surfaceSoft,
    ...shadows.card
  },
  image: {
    width: "100%",
    height: 242
  },
  scanCorner: {
    position: "absolute",
    width: 34,
    height: 34,
    borderColor: colors.surface,
    zIndex: 2
  },
  scanCornerTopLeft: {
    top: spacing.lg,
    left: spacing.lg,
    borderTopWidth: 4,
    borderLeftWidth: 4,
    borderTopLeftRadius: radii.control
  },
  scanCornerTopRight: {
    top: spacing.lg,
    right: spacing.lg,
    borderTopWidth: 4,
    borderRightWidth: 4,
    borderTopRightRadius: radii.control
  },
  scanCornerBottomLeft: {
    bottom: 86,
    left: spacing.lg,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
    borderBottomLeftRadius: radii.control
  },
  scanCornerBottomRight: {
    right: spacing.lg,
    bottom: 86,
    borderRightWidth: 4,
    borderBottomWidth: 4,
    borderBottomRightRadius: radii.control
  },
  overlay: {
    gap: spacing.sm,
    padding: spacing.md,
    backgroundColor: "rgba(255, 255, 255, 0.94)"
  },
  stage: {
    color: colors.ink,
    ...typography.sectionTitle
  }
});
