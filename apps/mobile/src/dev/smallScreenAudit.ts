export const smallScreenAudit = {
  targetWidth: 320,
  profile: {
    locale: "ko-KR",
    fontScale: "default",
    deviceClass: "small iPhone/Android width",
    verificationMode: "static style and copy audit; no screenshot runner is configured in this Expo scaffold"
  },
  screens: [
    {
      screen: "Today Dashboard",
      inspectedKorean: ["음식 사진 찍기", "사진으로 분석하고 바로 확인", "남은 권장 섭취량", "단백질은 보충하고 지방은 가볍게 가는 쪽이 좋아요."],
      layoutEvidence: ["scan copy has flex:1 and minWidth:0", "header/action rows use flexWrap", "macro cards share available width"],
      observation: "CTA and hero text can wrap before clipping; numeric kcal row uses wrapping baseline row.",
      verdict: "pass"
    },
    {
      screen: "Scan/Analyze Evidence",
      inspectedKorean: ["음식 구성 확인 중", "밥 양과 소스가 범위를 크게 바꿀 수 있어요.", "밥 양만 확인하기"],
      layoutEvidence: ["CalorieRange row uses flexWrap", "food rows use flexWrap and gap", "primary button has centered text"],
      observation: "Long explanation sits in body text outside controls; food assumptions wrap under names.",
      verdict: "pass"
    },
    {
      screen: "One-Tap Clarification",
      inspectedKorean: ["밥 양이 어느 정도였나요?", "이것만 확인하면 범위가 꽤 줄어요.", "잘 모르겠어요", "잘 모르겠다면 그대로 저장해도 돼요"],
      layoutEvidence: ["chips use flexWrap", "chips use flexBasis 46% with minWidth fallback", "sheet content is in ScrollView"],
      observation: "Four Korean chip labels wrap into two rows on 320px instead of overflowing.",
      verdict: "pass"
    },
    {
      screen: "Review Result",
      inspectedKorean: ["저장해도 괜찮은 추정이에요", "밥 양은 확인했고, 소스는 사진상 추정했어요.", "식사로 기록", "수정"],
      layoutEvidence: ["action buttons use 2:1 flex with short Korean labels", "food rows wrap", "52px touch target"],
      observation: "Primary and secondary actions keep intact labels; detected-food assumptions can wrap.",
      verdict: "pass"
    },
    {
      screen: "Saved Impact",
      inspectedKorean: ["기록했어요", "오늘 남은 칼로리는 505kcal예요.", "저녁은 단백질을 조금 더 챙기면 좋아요.", "대시보드로 돌아가기"],
      layoutEvidence: ["confirmation badge and guidance are separate text blocks", "return button text is centered", "screen uses ScrollView"],
      observation: "Saved confirmation avoids toast-only clipping and leaves a clear dashboard return path.",
      verdict: "pass"
    }
  ],
  overallVerdict: "pass"
} as const;
