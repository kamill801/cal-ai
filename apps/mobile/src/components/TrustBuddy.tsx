import type { ImageSourcePropType } from "react-native";
import { Image } from "react-native";

export type TrustBuddyPose = "welcome" | "meal" | "analysis" | "workout" | "progress" | "coach" | "celebrate";

const MASCOT_SOURCES: Record<TrustBuddyPose, ImageSourcePropType> = {
  welcome: require("../../assets/mascot/mascot-welcome.png"),
  meal: require("../../assets/mascot/mascot-meal.png"),
  analysis: require("../../assets/mascot/mascot-analysis.png"),
  workout: require("../../assets/mascot/mascot-workout.png"),
  progress: require("../../assets/mascot/mascot-progress.png"),
  coach: require("../../assets/mascot/mascot-coach.png"),
  celebrate: require("../../assets/mascot/mascot-celebrate.png")
};

const ACCESSIBILITY_LABELS: Record<TrustBuddyPose, string> = {
  welcome: "첫 기록을 반갑게 맞이하는 콩비",
  meal: "식사 기록을 응원하는 콩비",
  analysis: "돋보기로 식사를 살펴보는 콩비",
  workout: "운동을 응원하는 콩비",
  progress: "기록의 변화를 살펴보는 콩비",
  coach: "다음 행동을 함께 정리하는 콩비",
  celebrate: "기록 저장을 축하하는 콩비"
};

export function TrustBuddy({ size = 82, pose = "meal" }: { readonly size?: number; readonly pose?: TrustBuddyPose }) {
  return (
    <Image
      source={MASCOT_SOURCES[pose]}
      resizeMode="contain"
      style={{ width: size, height: size, flexShrink: 0 }}
      accessible
      accessibilityRole="image"
      accessibilityLabel={ACCESSIBILITY_LABELS[pose]}
    />
  );
}
