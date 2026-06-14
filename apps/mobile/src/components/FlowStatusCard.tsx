import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import type { FlowError } from "../flow/scanToSaveFlow";
import { colors, radii, spacing, typography } from "../theme";

export function FlowStatusCard({
  title,
  message,
  error,
  onRetry
}: {
  title?: string;
  message?: string;
  error?: FlowError;
  onRetry?: () => void;
}) {
  const isError = Boolean(error);

  return (
    <View style={[styles.card, isError && styles.errorCard]} accessibilityRole={isError ? "alert" : undefined}>
      <Text style={[styles.title, isError && styles.errorTitle]}>{error?.title ?? title}</Text>
      <Text style={styles.message}>{error?.message ?? message}</Text>
      {isError && onRetry ? (
        <TouchableOpacity activeOpacity={0.84} style={styles.retryButton} onPress={onRetry} accessibilityRole="button">
          <Text style={styles.retryText}>다시 시도</Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: spacing.sm,
    borderColor: colors.hairline,
    borderRadius: radii.card,
    borderWidth: 1,
    backgroundColor: colors.surface,
    padding: spacing.lg
  },
  errorCard: {
    borderColor: colors.danger,
    backgroundColor: "#fff7f7"
  },
  title: {
    color: colors.ink,
    ...typography.sectionTitle
  },
  errorTitle: {
    color: colors.danger
  },
  message: {
    color: colors.body,
    ...typography.body
  },
  retryButton: {
    alignSelf: "flex-start",
    marginTop: spacing.xs,
    borderRadius: radii.control,
    backgroundColor: colors.black,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md
  },
  retryText: {
    color: colors.surface,
    fontSize: 14,
    lineHeight: 18,
    fontWeight: "800"
  }
});
