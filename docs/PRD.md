# PRD: Trust-First AI Nutrition Logger

## 0. Document Status

- Status: Draft for PRD/techspec phase
- Last updated: 2026-06-09
- Source of truth inputs:
  - `.omx/specs/deep-interview-cal-ai-ideation.md`
  - `.omx/interviews/cal-ai-ideation-20260609T120932Z.md`
  - `DESIGN.md`
  - `concept.html`
- Design status: `DESIGN.md` is the provisional design contract. Final brand name, Figma file, pricing/paywall design, and coded design tokens remain undecided.

## 1. One-Line Concept

음식 사진을 더 믿을 수 있게 보정하고, 내 몸 변화에 맞춰 칼로리 목표와 다음 식사 방향을 조정해주는 AI 식단 기록 앱.

## 2. Product Category

- Consumer health and nutrition app
- AI food logging and macro tracking
- Body-adaptive diet support for weight loss, muscle gain, and body recomposition

## 3. Target Users

### Primary Users

1. 감량 다이어터
   - 음식 기록을 해야 한다는 건 알지만 매번 검색/입력이 귀찮다.
   - 사진 분석 앱을 써봤지만 칼로리가 믿기지 않아 지속하지 못했다.
   - 다음 끼니를 어떻게 조정해야 하는지 알고 싶다.

2. 헬스/근육 증가 사용자
   - 단백질과 탄단지 목표를 맞추고 싶다.
   - 반복 식단은 빠르게 기록하고 싶다.
   - 감량/증량/유지 단계에 따라 목표가 조정되길 원한다.

### Later Users

- 일반 건강관리 사용자
- 트레이너/영양사와 기록을 공유하려는 사용자
- 의료/혈당/보험/기관 연동 사용자

V1은 medical-adjacent 사용자를 직접 타깃하지 않는다.

## 4. Core User Pain

기존 칼로리 앱은 두 지점에서 이탈이 생긴다.

1. 기록이 귀찮다.
   - 음식 검색, 그램 입력, 항목 추가가 반복되면 지친다.
   - 특히 한식, 외식, 배달식은 구성 음식이 많아 입력이 번거롭다.

2. 사진 분석이 부정확하게 느껴진다.
   - AI가 단정적으로 숫자를 주면 틀렸을 때 신뢰가 무너진다.
   - 밥 양, 소스, 국물, 먹은 비율처럼 칼로리에 큰 영향을 주는 정보가 사진만으로는 불확실하다.

## 5. Core Promise

사용자는 30초 안팎의 짧은 보정만으로 더 믿을 수 있는 식단 기록을 얻고, 며칠 사용하면 앱이 자신의 몸 변화와 섭취 패턴을 반영해 목표와 다음 식사 방향을 제안한다.

## 6. Product Philosophy

- 빠른 척보다 믿을 수 있는 기록을 우선한다.
- AI가 다 맞힌다고 주장하지 않는다.
- 사용자는 데이터 입력자가 아니라 최종 확인자다.
- 처음에는 적게 묻고, 사용 기록이 쌓일수록 더 잘 맞춘다.
- 다이어트 압박감보다 실질적 조정과 선택 도움을 제공한다.

## 7. Differentiation

### 1. Trust-First Logging

Cal AI류 앱의 속도 중심 접근과 달리, V1은 약간 더 걸리더라도 신뢰 가능한 결과를 만든다. 칼로리 결과는 단정값만 보여주지 않고 범위, 신뢰도, 불확실성 이유를 함께 보여준다.

### 2. AI Clarification Instead of Manual Entry

사용자가 음식을 하나하나 검색하지 않는다. AI가 먼저 분석하고, 정확도에 큰 영향을 주는 것만 1-2개 질문한다.

예:

- 밥 양
- 국물 섭취 여부
- 소스/기름 정도
- 실제 먹은 비율

### 3. Progressive Personalization

긴 온보딩으로 모든 것을 묻지 않는다. 신체/목표/운동량만으로 시작하고, 며칠간의 음식 기록, 체중 변화, 수정 내역을 바탕으로 점점 개인화한다.

### 4. Next-Meal Nutrient Guidance

V1은 레시피/장보기까지 가지 않는다. 오늘 부족하거나 과한 성분을 분석하고, 다음 식사에서 어떤 메뉴 유형을 선택하면 좋은지 제안한다.

## 8. MVP Scope

### Must Have

- 계정 생성 또는 최소 로그인
- 신체/목표/운동량 기반 짧은 온보딩
- 초기 칼로리/탄단지 목표 계산
- 음식 사진 업로드 또는 촬영
- AI 음식 분석
- 신뢰도/범위 기반 결과 표시
- AI clarification 질문 1-2개
- 간단한 portion slider 또는 선택형 보정
- 식사 로그 저장
- 오늘의 칼로리/탄단지 대시보드
- 며칠간의 기록 기반 목표 보정 제안
- 부족 성분 및 다음 식사 메뉴 유형 추천
- 개인정보/건강정보 안전 고지

### Should Have

- 반복 음식 기억
- 체중 로그
- 주간 요약 리포트
- 한국/아시아식 보정 프리셋
- 사용자가 AI 추정치를 수정한 내역 저장

### Could Have

- 바코드 스캔
- 영양성분표 OCR
- 음성 입력
- Apple Health / Google Fit 연동
- PDF 리포트

### Explicitly Excluded From V1

- 경쟁사 UI/브랜딩/문구 복제
- 긴 quiz-style 온보딩
- 수동 DB 검색 중심 경험
- 레시피 생성
- 장보기/쇼핑 연동
- 여러 날 식단표 자동 생성
- 병원/트레이너/B2B 콘솔
- 의료 진단/치료/혈당 dosing 조언
- 자체 음식 인식 모델 학습
- 최종 가격/결제 정책 확정
- 최종 색감/브랜드/디자인 시스템 확정

## 9. Core User Flow

### First-Run Flow

1. 사용자가 앱을 연다.
2. 짧은 온보딩을 완료한다.
   - 키
   - 몸무게
   - 나이
   - 성별 또는 대사 계산에 필요한 설정
   - 목표: 감량/유지/증량/리컴프
   - 운동량/활동량
3. 앱이 초기 칼로리/탄단지 목표를 계산한다.
4. 사용자가 첫 식사를 촬영한다.
5. AI가 음식 후보, 양, 칼로리 범위, 탄단지를 분석한다.
6. 앱이 필요한 경우 1-2개 clarification 질문을 묻는다.
7. 사용자가 탭/슬라이더로 보정한다.
8. 앱이 결과를 다시 계산하고 식사 로그로 저장한다.
9. 대시보드가 오늘의 남은 칼로리/성분을 갱신한다.

### Returning User Flow

1. 사용자가 식사를 촬영한다.
2. 앱은 이전 보정 패턴과 자주 먹는 음식 맥락을 반영한다.
3. 필요한 질문만 짧게 묻는다.
4. 기록 저장 후 오늘 부족/초과 성분을 표시한다.
5. 다음 식사 메뉴 유형을 제안한다.
6. 충분한 로그와 체중 변화가 쌓이면 목표 조정을 제안한다.

## 10. Key Screens

### Onboarding

- 목적: 초기 목표 계산에 필요한 최소 정보 수집
- 원칙: 3분 이내 완료
- 제외: 긴 식습관/심리/질병 질문

### Today Dashboard

- 오늘 섭취량
- 남은 칼로리
- 단백질/탄수화물/지방 진행률
- 식사별 로그
- 사진 촬영 CTA
- 다음 식사 추천 요약

### Food Scan

- 사진 촬영/업로드
- 이미지 품질 검사
- 분석 중 상태
- 실패 시 재촬영/수동 메모 옵션

### Analysis Result

- 예상 칼로리 범위
- confidence
- 감지된 음식
- portion assumptions
- AI clarification 질문
- slider/tap 보정
- 저장 CTA

### Personalization Insight

- 최근 기록/체중 변화 기반 목표 조정 제안
- 부족/초과 성분
- 다음 식사 메뉴 유형 추천
- 추천 이유

## 11. Content and Tone

- 직접적이지만 압박하지 않는다.
- 사용자의 실패를 비난하지 않는다.
- "정확히 723kcal"보다 "약 620-760kcal, 밥 양이 가장 큰 변수예요"처럼 말한다.
- "먹지 마세요"보다 "다음 식사는 단백질을 보충하고 지방은 낮추는 쪽이 좋아요"처럼 말한다.
- 의료적 표현은 피하고 필요한 경우 전문가 상담을 안내한다.

## 12. Monetization Assumptions

가격과 paywall은 아직 확정하지 않는다.

기본 가정:

- 무료 사용자는 제한된 횟수의 사진 분석을 사용할 수 있어야 한다.
- 유료 가치는 무제한 분석, 개인화 보정, 고급 리포트, 반복 음식 기억, 더 깊은 AI 코칭에서 나온다.
- exact pricing, free scan count, trial length, paywall copy는 디자인/제품 검토 후 확정한다.

## 13. Retention Hooks

- 기록할수록 더 잘 맞는 개인 보정
- 자주 먹는 음식/양 기억
- 체중 변화 기반 목표 조정
- 다음 식사 추천
- 주간 리포트

V1은 streak이나 badge를 핵심 리텐션으로 삼지 않는다. 신뢰와 개인화가 주 리텐션이다.

## 14. Success Metrics

### Activation

- 온보딩 완료율
- 첫 식사 스캔 완료율
- 첫 분석 후 저장률
- clarification 응답률

### Trust

- 분석 결과 수정률
- 같은 사용자의 반복 수정 감소
- confidence 낮은 결과의 저장률
- 재촬영률

### Retention

- D1/D7 retention
- 사용자당 주간 식사 기록 수
- 체중 로그 입력 지속률
- 목표 조정 제안 수락률

### Recommendation Quality

- 다음 식사 추천 클릭/확인률
- 추천 후 다음 식사 macro 개선 여부
- "도움됨/별로" 피드백

## 15. Privacy and Safety Requirements

- 음식 사진은 분석 목적 외 사용하지 않는다.
- 사용자 동의 없이 모델 학습에 사용하지 않는다.
- 이미지 보관 기간과 삭제 옵션을 명확히 제공한다.
- 건강정보와 민감정보는 최소 수집한다.
- 극단적 감량 목표는 경고하거나 완화한다.
- 섭식장애, 임신/수유, 당뇨 등 의료적 맥락은 전문 상담 안내와 안전 문구를 포함한다.

## 16. Design Follow-Up

현재 repo 루트의 `DESIGN.md`를 MVP 구현 전 디자인 기준으로 사용한다. 다음 단계에서 Figma 플러그인 또는 별도 디자인 툴을 사용해 아래를 확정한 뒤 `DESIGN.md`와 관련 문서를 갱신한다.

- 브랜드 이름
- 색감
- 타입 시스템
- 앱 아이콘/로고 방향
- 모바일 화면 레이아웃
- 컴포넌트 상태
- paywall UX

디자인 확정 후 업데이트 대상:

- `DESIGN.md`: canonical design contract
- `docs/PRD.md`: UX와 화면 설명
- `docs/TECHSPEC.md`: design token, component contract, asset policy
- `docs/PLAN.md`: 디자인 반영 구현 태스크

## 17. Open Questions

- 최종 브랜드명
- iOS/Android 동시 출시 여부
- 결제 방식과 가격
- 무료 스캔 제한
- 음식 사진 저장 기본 정책
- 한국 식품 DB의 초기 확보 방식
