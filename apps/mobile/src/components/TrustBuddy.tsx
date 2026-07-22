import { StyleSheet, View } from "react-native";
import { colors, radii, shadows } from "../theme";

export function TrustBuddy({ size = 82, accessory = "spoon" }: { readonly size?: number; readonly accessory?: "spoon" | "magnifier" | "sprout" }) {
  const bodySize = size;
  const eyeSize = Math.max(4, Math.round(size * 0.085));
  const cheekSize = Math.max(8, Math.round(size * 0.13));

  return (
    <View style={[styles.wrap, { width: bodySize, height: Math.round(bodySize * 1.12) }]} accessibilityLabel="식단 기록을 도와주는 작은 코치">
      {accessory === "spoon" ? <View style={[styles.spoon, { height: Math.round(size * 0.82), left: Math.round(size * -0.08) }]} /> : null}
      {accessory === "magnifier" ? (
        <View style={[styles.magnifier, { width: Math.round(size * 0.46), height: Math.round(size * 0.46), left: Math.round(size * -0.15), top: Math.round(size * 0.34) }]}>
          <View style={styles.magnifierHandle} />
        </View>
      ) : null}
      {accessory === "sprout" ? (
        <View style={[styles.sprout, { top: Math.round(size * 0.04), right: Math.round(size * 0.08) }]}>
          <View style={styles.sproutLeaf} />
          <View style={[styles.sproutLeaf, styles.sproutLeafSecond]} />
        </View>
      ) : null}
      <View style={[styles.body, { width: bodySize, height: Math.round(bodySize * 1.04), borderRadius: Math.round(bodySize * 0.48) }]}>
        <View style={[styles.eye, { width: eyeSize, height: eyeSize, left: Math.round(size * 0.31), top: Math.round(size * 0.43) }]} />
        <View style={[styles.eye, { width: eyeSize, height: eyeSize, right: Math.round(size * 0.31), top: Math.round(size * 0.43) }]} />
        <View style={[styles.mouth, { top: Math.round(size * 0.55) }]} />
        <View style={[styles.cheek, { width: cheekSize, height: cheekSize, left: Math.round(size * 0.18), top: Math.round(size * 0.51) }]} />
        <View style={[styles.cheek, { width: cheekSize, height: cheekSize, right: Math.round(size * 0.18), top: Math.round(size * 0.51) }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    position: "relative"
  },
  body: {
    position: "absolute",
    right: 0,
    bottom: 0,
    backgroundColor: colors.cream,
    borderColor: "#f8dfb7",
    borderWidth: 1,
    ...shadows.card
  },
  eye: {
    position: "absolute",
    borderRadius: radii.pill,
    backgroundColor: colors.ink
  },
  mouth: {
    position: "absolute",
    alignSelf: "center",
    width: 10,
    height: 5,
    borderRadius: 5,
    backgroundColor: colors.ink
  },
  cheek: {
    position: "absolute",
    borderRadius: radii.pill,
    backgroundColor: colors.peach
  },
  spoon: {
    position: "absolute",
    top: 4,
    width: 14,
    borderRadius: radii.pill,
    backgroundColor: colors.creamDeep,
    transform: [{ rotate: "-18deg" }],
    ...shadows.card
  },
  magnifier: {
    position: "absolute",
    zIndex: 2,
    borderColor: colors.ink,
    borderWidth: 5,
    borderRadius: radii.pill,
    backgroundColor: "rgba(255, 255, 255, 0.46)"
  },
  magnifierHandle: {
    position: "absolute",
    right: -10,
    bottom: -14,
    width: 8,
    height: 22,
    borderRadius: radii.pill,
    backgroundColor: colors.ink,
    transform: [{ rotate: "-38deg" }]
  },
  sprout: {
    position: "absolute",
    zIndex: 3,
    width: 28,
    height: 28
  },
  sproutLeaf: {
    position: "absolute",
    width: 18,
    height: 11,
    borderTopLeftRadius: 12,
    borderBottomRightRadius: 12,
    backgroundColor: colors.leaf,
    transform: [{ rotate: "-22deg" }]
  },
  sproutLeafSecond: {
    right: 0,
    top: 7,
    backgroundColor: colors.fiber,
    transform: [{ rotate: "28deg" }]
  }
});
