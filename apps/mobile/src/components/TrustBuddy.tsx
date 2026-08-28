import type { ImageSourcePropType } from "react-native";
import { Image } from "react-native";

export type TrustBuddyPose = "meal" | "analysis" | "workout" | "progress" | "coach" | "celebrate";

const MASCOT_SOURCES: Record<TrustBuddyPose, ImageSourcePropType> = {
  meal: require("../../assets/mascot/mascot-meal.png"),
  analysis: require("../../assets/mascot/mascot-analysis.png"),
  workout: require("../../assets/mascot/mascot-workout.png"),
  progress: require("../../assets/mascot/mascot-progress.png"),
  coach: require("../../assets/mascot/mascot-coach.png"),
  celebrate: require("../../assets/mascot/mascot-celebrate.png")
};

const ACCESSIBILITY_LABELS: Record<TrustBuddyPose, string> = {
  meal: "밥을 먹으며 식사 기록을 응원하는 작은 코치",
  analysis: "돋보기로 식사를 살펴보는 작은 코치",
  workout: "두 팔에 힘을 주며 운동을 응원하는 작은 코치",
  progress: "변화 그래프를 보여주는 작은 코치",
  coach: "클립보드로 다음 행동을 알려주는 작은 코치",
  celebrate: "기록 완료를 축하하며 뛰는 작은 코치"
};

export function TrustBuddy({ size = 82, pose = "meal" }: { readonly size?: number; readonly pose?: TrustBuddyPose }) {
  return (
    <Image
      source={MASCOT_SOURCES[pose]}
      resizeMode="contain"
      style={{ width: size, height: size }}
      accessibilityLabel={ACCESSIBILITY_LABELS[pose]}
    />
  );
}
