# TECHSPEC: Trust-First Body Transformation Coach

## 0. Document Purpose

이 문서는 제품과 기술 사양을 정의한다. 개발자 또는 Codex CLI/OMX 에이전트가 이전 대화 없이도 무엇을 만들지 이해할 수 있어야 한다.

실제 구현 순서, 마일스톤, 태스크 체크리스트는 `docs/PLAN.md`에서 관리한다.

## 1. Product Overview

- Product name: TBD
- Working name: Trust-First Body Transformation Coach
- One-line definition: 음식 사진, 체중, 회복, 운동 수행, 선택적 신체 사진 기록을 함께 사용해 영양과 훈련의 다음 행동을 제안하는 몸 변화 코치 앱.
- Primary users: 감량 다이어터, 헬스/근육 증가 사용자, 몸 상태에 맞춰 식단을 조정하려는 사용자.
- MVP goal: 음식 사진 기록의 귀찮음과 AI 분석 불신을 줄이면서, 사용자가 오늘 먹고 운동하고 회복할 다음 행동을 한 앱에서 결정하게 한다.
- Core promise: 사용자는 짧은 기록만으로 오늘 남은 단백질, 다음 운동, 회복 신호, 주간 개선점을 이해한다.

### Implemented Coach Loop

1. 온보딩에서 목표, 운동 빈도, 경험, 장비, 세션 시간을 받는다.
2. 음식 사진 분석과 확인 질문 후 식사를 저장하고 칼로리·단백질 누적량을 계산한다.
3. 체중과 에너지·수면·근육통을 기록한다.
4. 선택적으로 신체 사진을 private storage에 올리고 제한된 시각 관찰과 운동 초점을 받는다.
5. 프로필과 신체 체크인 근거를 포함한 세트·반복·RIR 기반 운동 계획을 만든다.
6. 운동 완료를 기록하고 Today, Progress, Weekly Coach 화면을 갱신한다.
7. 식사 5회와 체중 2회 이후에는 목표를 자동 변경하지 않고 칼로리 조정안을 제안한다.

OpenAI 음식 이미지 분석은 provider seam 뒤에 구현되어 있다. 서버에서 `AI_PROVIDER=openai`와 API key를 설정한 경우 private R2 이미지를 짧은 수명의 presigned GET URL로 읽고, Responses API strict JSON schema 결과를 영속화한다. 결정론적 mock은 로컬 개발 fallback으로 유지한다. 신체 이미지 분석은 별도 `BODY_AI_PROVIDER`와 명시적 사용자 동의로만 활성화하며 체지방률, 질환, 외모, 신원 같은 민감 추론을 금지한다. 모바일은 업로드 전에 긴 변을 줄이고 JPEG로 반복 압축해 900KB 이하를 목표로 한다.

## 2. Recommended Technical Direction

### Recommended Stack

- Mobile app: React Native Expo
- API server: FastAPI
- Database: PostgreSQL
- Analysis execution: bounded synchronous Vercel Function for the internal MVP; Redis/RQ or equivalent worker is a later scale-up path
- Object storage: S3/R2/Supabase Storage compatible bucket
- AI provider: Vision-capable LLM with structured JSON output
- Nutrition data: public nutrition DBs plus normalized Korean food mapping
- Payments: RevenueCat later, not required for first internal MVP
- Analytics: PostHog
- Error monitoring: Sentry

### Why This Stack

- Expo gives a native camera/upload experience while keeping iteration fast.
- FastAPI is a clean fit for AI pipelines, async jobs, typed schemas, and Python nutrition-processing utilities.
- PostgreSQL keeps user profiles, logs, corrections, and personalization state queryable.
- Object storage separates uploaded images from relational data.
- RevenueCat can handle App Store/Play Store subscription complexity after product flow validation.

### Design Status

`DESIGN.md` is the current provisional design contract. Visual identity can still change after Figma review, but implementation should use the palette, typography, component names, and UX rules in `DESIGN.md` until it is refreshed.

## 3. Product Principles and Safety Position

### Principles

- Prefer trustworthy logging over maximum speed.
- Show uncertainty honestly.
- Ask only the questions that materially improve accuracy.
- Keep onboarding short.
- Learn from usage rather than forcing a long quiz.
- Avoid shame and medical overclaims.

### Claims the Product Must Not Make

- "정확한 칼로리" without uncertainty.
- Medical diagnosis or treatment advice.
- Guaranteed weight loss or muscle gain.
- Disease-specific diet prescriptions.
- Insulin, glucose, medication, pregnancy, or eating-disorder treatment guidance.

### Safe Wording Pattern

Use:

- "예상"
- "범위"
- "사진상 확인 어려운 부분"
- "다음 식사는 이런 성분을 보충하는 방향이 좋아요"

Avoid:

- "반드시"
- "치료"
- "진단"
- "무조건"
- "실패"
- "망쳤다"

## 4. MVP Scope

### Must-Have Features

- User account/session
- Short onboarding
- Initial target calculation
- Food image upload/capture
- Image quality validation
- AI food analysis job
- Structured nutrition estimate
- Confidence/range and assumptions
- AI clarification questions
- Portion/eaten-ratio adjustment
- Meal save
- Today dashboard
- Weight log
- Basic progressive personalization
- Next-meal nutrient/menu-type recommendation
- Safety and privacy controls

### Should-Have Features

- Repeated food memory
- Weekly summary
- Korean/Asian meal presets
- Correction feedback tracking
- Analysis history

### Later Features

- Barcode scan
- Nutrition label OCR
- Voice input
- HealthKit/Google Fit
- Subscription billing
- Coach share/PDF export
- Figma-finalized design system

### Excluded Features

- Custom food-recognition model training
- Medical condition management
- Recipe generation
- Grocery shopping
- Full multi-day meal planning
- B2B console
- Exact competitor UI clone

## 5. User Experience Specification

### 5.1 Onboarding Inputs

| Field | Type | Required | Validation | Purpose |
| --- | --- | --- | --- | --- |
| age | number | yes | 14-100 | calorie target calculation |
| sex | enum | yes | male/female/other/skip policy TBD | BMR calculation |
| height_cm | number | yes | 100-230 | BMR calculation |
| current_weight_kg | number | yes | 30-250 | BMR and progress |
| target_weight_kg | number | optional | 30-250 | goal direction |
| goal_type | enum | yes | lose/maintain/gain/recomp | target strategy |
| activity_level | enum | yes | sedentary/light/moderate/high/athlete | TDEE estimate |
| training_frequency | enum | optional | none/1-2/3-4/5+ | protein and recommendation context |

Onboarding must be completable in under 3 minutes.

### 5.2 Food Scan Result Structure

The result screen must show:

- Food image preview
- Estimated calorie range
- Confidence score/label
- Total protein/carbs/fat
- Detected food items
- Portion assumptions
- Uncertainty reasons
- Clarification controls
- Save meal CTA

### 5.3 Clarification UX

The system may ask at most 2 high-impact questions before saving.

Question types:

- single choice
- segmented control
- slider
- stepper

Freeform text is allowed only as optional note, not the default correction path.

Example:

```json
{
  "question_key": "rice_amount",
  "question": "밥은 어느 정도 드셨나요?",
  "type": "single_choice",
  "options": [
    { "label": "반 공기", "value": "half_bowl", "grams_delta_hint": -80 },
    { "label": "한 공기보다 조금 적게", "value": "near_bowl", "grams_delta_hint": 0 },
    { "label": "한 공기 이상", "value": "full_plus", "grams_delta_hint": 60 }
  ]
}
```

### 5.4 Next-Meal Recommendation UX

V1 recommends nutrient direction and menu types, not exact recipes.

Example:

```text
오늘 단백질이 42g 부족하고 지방은 이미 충분해요.
다음 식사는 닭가슴살 샐러드, 두부/계란 위주 한식, 기름 적은 생선구이류가 좋아요.
```

## 6. Data Source Strategy

| Source | Role | MVP | Limits |
| --- | --- | --- | --- |
| User onboarding | initial target calculation | yes | self-reported data can be inaccurate |
| Food image | food recognition and portion estimate | yes | hidden sauce/oil/broth cannot be reliably inferred |
| User corrections | personalization and future defaults | yes | requires careful aggregation |
| Weight logs | target adjustment | yes | noisy day-to-day changes |
| Public nutrition DB | macro/nutrient lookup | yes | Korean/local foods may need mapping |
| Korean food DB | localized nutrition lookup | should | coverage and licensing must be verified |
| Barcode DB | packaged foods | later | not MVP core |
| Wearables/HealthKit | activity context | later | permission and platform complexity |

## 7. System Architecture

### 7.1 Logical Layers

1. Mobile app
   - onboarding
   - camera/upload
   - analysis result
   - correction controls
   - dashboard
   - insight/recommendation UI

2. API server
   - auth/session validation
   - profile and target APIs
   - food analysis job APIs
   - log APIs
   - recommendation APIs
   - privacy/data deletion APIs

3. AI pipeline
   - image preprocessing
   - food evidence extraction
   - nutrition DB resolution
   - portion estimate normalization
   - clarification decision
   - final estimate synthesis
   - safety/quality validation

4. Storage
   - PostgreSQL for structured records
   - object storage for images
   - Redis queue for analysis jobs

5. Analytics and monitoring
   - product events
   - AI quality events
   - application errors

### 7.2 Sync vs Async

Food image analysis should be asynchronous.

Flow:

1. Client uploads image.
2. API creates `analysis_job`.
3. Worker runs AI pipeline.
4. Client polls or subscribes to job status.
5. Result is returned with clarification state.

Small target calculations and dashboard reads are synchronous.

The MVP upload seam supports private-bucket object storage through a presigned upload flow. Clients request a presigned URL, upload image bytes directly to R2, then complete the upload metadata with the API before creating an analysis job. `image_reference` remains server-owned; clients pass only `image_upload_id` into analysis job creation. Local development still supports the mock/local metadata endpoint and sqlite fallback through `CAL_AI_API_DATA_PATH`. In OpenAI mode, the API creates a short-lived presigned GET URL only for the provider request; that URL is never persisted or returned to the mobile client.

## 8. Functional Requirements

### FR-1: User Profile and Onboarding

- Purpose: collect minimal initial data for target calculation.
- Output: `user_profile` and initial `nutrition_target`.
- Error states:
  - invalid height/weight/age
  - unsafe goal speed
  - missing required field
- Priority: MVP

### FR-2: Initial Target Calculation

- Purpose: estimate daily calories and macros.
- Business rules:
  - Use BMR/TDEE style calculation.
  - Apply safe deficit/surplus bounds.
  - Show estimates as adjustable, not medical facts.
- Priority: MVP

### FR-3: Food Image Analysis

- Purpose: estimate food items, portions, calories, and macros from a meal image.
- Inputs:
  - image
  - meal type
  - locale
  - user context
  - optional note
- Outputs:
  - analysis result
  - confidence/range
  - clarification questions
- Priority: MVP

### FR-4: Clarification and Portion Correction

- Purpose: improve trust by asking only high-impact questions.
- Business rules:
  - Maximum 2 clarification questions before save.
  - Questions are generated from uncertainty reasons.
  - Corrections must update estimated calories/macros.
- Priority: MVP

### FR-5: Meal Log Save

- Purpose: persist confirmed meal result.
- Business rules:
  - Save original AI result and corrected result separately.
  - Track correction deltas for personalization.
  - Allow user edits after save.
- Priority: MVP

### FR-6: Today Dashboard

- Purpose: show current day intake and remaining targets.
- Outputs:
  - calories consumed/remaining
  - macro progress
  - meal list
  - next-meal guidance summary
- Priority: MVP

### FR-7: Progressive Personalization

- Purpose: adapt target and recommendations based on usage.
- Inputs:
  - food logs
  - corrections
  - weight logs
  - goal
- Outputs:
  - target adjustment suggestion
  - meal guidance
- Priority: MVP/V1

### FR-8: Privacy Controls

- Purpose: user trust and legal safety.
- Requirements:
  - delete account
  - delete meal log
  - delete image
  - image retention policy
  - training opt-in flag
- Priority: MVP

### FR-9: Training Plan and Session Tracking

- Purpose: 목표, 운동 빈도, 가용 시간, 신체 체크인 초점을 실행 가능한 운동으로 바꾼다.
- Outputs: 운동일, 운동 종목, 세트, 반복 범위, RIR, 휴식 시간, 근거, 점진적 과부하 규칙.
- Business rules:
  - 통증이나 질환을 진단하지 않는다.
  - 사진 관찰을 확정적 약점 판정으로 표현하지 않는다.
  - 완료한 종목과 세션 RPE를 기록한다.
- Priority: MVP

### FR-10: Body and Recovery Check-in

- Purpose: 체중, 수면, 에너지, 근육통, 선택적 신체 사진을 주간 추세 맥락으로 사용한다.
- Business rules:
  - 신체 사진은 private bucket의 기존 direct-upload 흐름을 재사용한다.
  - 사진만으로 체지방률, 질환, 통증 원인을 추정하지 않는다.
  - 조명·거리·자세 차이를 고지하고 단일 사진보다 반복 기록을 우선한다.
- Priority: MVP

### FR-11: Weekly Coach and Target Adjustment

- Purpose: 식사, 운동, 체중, 회복, 신체 체크인을 합쳐 다음 주 행동을 정한다.
- Business rules:
  - 리포트의 근거 건수를 함께 표시한다.
  - 목표 조정은 식사 5회와 체중 2회 전에는 잠긴다.
  - 칼로리 목표는 자동 변경하지 않고 사용자의 명시적 확인을 요구한다.
- Priority: MVP

## 9. AI / Analysis Pipeline

### Step 1: Input Ingestion

Input:

```json
{
  "user_id": "uuid",
  "image_url": "storage://...",
  "meal_type": "lunch",
  "locale": "ko-KR",
  "optional_note": "국물은 거의 안 마셨어요",
  "user_context": {
    "goal_type": "lose",
    "daily_calorie_target": 1850,
    "protein_target_g": 130,
    "known_preferences": ["korean_food"]
  }
}
```

Checks:

- file type
- file size
- image readability
- safety filter for non-food or sensitive images

### Step 2: Preprocessing

Tasks:

- normalize image size
- strip unnecessary metadata
- generate storage key
- optionally create thumbnail

### Step 3: Evidence Extraction

Vision model extracts:

- visible food candidates
- likely cuisine
- visible portion cues
- container/plate cues
- uncertainty reasons
- hidden-ingredient risks

Output:

```json
{
  "foods": [
    {
      "label": "제육볶음",
      "confidence": 0.86,
      "visible_portion": "medium serving",
      "uncertainty": ["oil_amount", "sauce_amount"]
    }
  ],
  "meal_context": {
    "cuisine": "korean",
    "multi_food": true,
    "image_quality": "good"
  }
}
```

### Step 4: Nutrition Resolution

Resolver maps detected foods to nutrition records.

Resolution strategy:

1. exact localized match
2. Korean food alias match
3. public DB generic equivalent
4. fallback estimated composite food

Each resolved item must keep provenance:

```json
{
  "food_name": "제육볶음",
  "source": "korean_food_db",
  "source_food_id": "ko-food-123",
  "calories_per_100g": 220,
  "protein_per_100g": 13,
  "carbs_per_100g": 9,
  "fat_per_100g": 14
}
```

### Step 5: Portion and Range Estimation

The system estimates grams and uncertainty.

Rules:

- Do not return a false-precision single number only.
- Calculate low/mid/high estimate.
- Mark hidden ingredient and portion-risk factors.

### Step 6: Clarification Decision

Select 0-2 questions based on expected impact on calorie variance.

Question priority examples:

1. rice amount
2. eaten ratio
3. broth consumption
4. sauce/oil amount
5. missing side dish

Do not ask low-impact questions that do not materially change nutrition.

### Step 7: Output Generation

Structured result:

```json
{
  "analysis_job_id": "uuid",
  "summary": {
    "calories_kcal": 615,
    "calorie_range": { "low": 540, "high": 710 },
    "protein_g": 31,
    "carbs_g": 72,
    "fat_g": 19,
    "confidence": 0.82,
    "confidence_label": "medium_high"
  },
  "items": [
    {
      "name": "제육볶음",
      "estimated_grams": 130,
      "calories_kcal": 286,
      "protein_g": 17,
      "carbs_g": 12,
      "fat_g": 18,
      "confidence": 0.84,
      "assumptions": ["normal_sauce_amount"]
    }
  ],
  "uncertainty_reasons": [
    "밥 양이 사진에서 일부 가려져 있어요",
    "양념 기름량은 사진만으로 정확히 알기 어려워요"
  ],
  "clarification_questions": [
    {
      "question_key": "rice_amount",
      "type": "single_choice",
      "question": "밥은 어느 정도 드셨나요?",
      "options": [
        { "label": "반 공기", "value": "half_bowl" },
        { "label": "한 공기보다 조금 적게", "value": "near_bowl" },
        { "label": "한 공기 이상", "value": "full_plus" }
      ]
    }
  ],
  "safety_notes": []
}
```

### Step 8: Safety and Quality Gate

Reject or soften outputs if:

- image is not food
- model confidence is too low
- estimated calories are extreme outliers
- recommendation implies unsafe restriction
- user goal is unsafe
- medical advice is requested

### Step 9: Logging and Evaluation

Log:

- model version/provider
- detected foods
- confidence
- clarification questions asked
- user answers
- correction deltas
- save/abandon outcome
- user feedback

Do not log raw images for model training unless opt-in exists.

## 10. Engine / Module Specifications

### Profile Engine

Purpose: create and update user nutrition profile.

Inputs:

- onboarding answers
- weight logs
- food logs
- activity level

Outputs:

- calorie target
- macro targets
- target confidence
- adjustment suggestions

### Food Analysis Engine

Purpose: run the image-to-nutrition pipeline.

Inputs:

- image
- meal type
- user context
- optional note

Outputs:

- structured analysis result
- clarification questions

### Clarification Engine

Purpose: choose the smallest set of questions that reduces calorie uncertainty.

Main rule:

- Ask at most 2 questions.
- Estimate expected impact before asking.
- Prefer Korean/Asian meal variables first when relevant.

### Nutrition Resolver

Purpose: map food labels and portions to nutrition values.

Dependencies:

- normalized food database
- alias table
- unit conversion rules

### Personalization Engine

Purpose: learn from user corrections and weight response.

Outputs:

- likely default portion preferences
- target adjustment suggestions
- next-meal guidance context

### Recommendation Engine

Purpose: generate next-meal nutrient and menu-type guidance.

Inputs:

- today's intake
- targets
- recent meal pattern
- goal type

Outputs:

```json
{
  "deficits": [
    { "nutrient": "protein_g", "amount": 42, "severity": "high" }
  ],
  "excesses": [
    { "nutrient": "fat_g", "amount": 12, "severity": "medium" }
  ],
  "menu_type_recommendations": [
    "닭가슴살 샐러드",
    "두부/계란 위주 한식",
    "기름 적은 생선구이류"
  ],
  "explanation": "단백질이 부족하고 지방은 이미 충분해서, 고단백 저지방 메뉴가 좋아요."
}
```

## 11. Business Logic

### Confidence

Confidence is not accuracy. It represents how much the system trusts its current estimate.

Inputs:

- image quality
- food recognition confidence
- portion visibility
- hidden ingredient risk
- DB match quality
- user correction history

Labels:

- high
- medium_high
- medium
- low

### Calorie Range

Every scan result should include:

- low estimate
- midpoint estimate
- high estimate

If high-low range is too wide, clarification should be triggered.

### Target Adjustment

Target adjustment requires enough evidence.

Suggested minimum:

- at least 5 logged days in last 10 days
- at least 2 weight logs
- no obvious unsafe goal state

Adjustment should be suggested, not silently applied.

## 12. Data Model

### users

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | primary key |
| email | text | optional | auth provider dependent |
| locale | text | yes | default ko-KR |
| timezone | text | yes | dashboard date boundary |
| created_at | timestamptz | yes |  |
| deleted_at | timestamptz | optional | soft delete |

### user_profiles

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| user_id | uuid | yes | unique |
| age | int | yes | sensitive |
| sex | text | yes | sensitive |
| height_cm | numeric | yes | sensitive |
| current_weight_kg | numeric | yes | sensitive |
| target_weight_kg | numeric | optional | sensitive |
| goal_type | text | yes | lose/maintain/gain/recomp |
| activity_level | text | yes |  |
| training_frequency | text | optional |  |
| created_at | timestamptz | yes |  |
| updated_at | timestamptz | yes |  |

### nutrition_targets

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | primary key |
| user_id | uuid | yes | indexed |
| calories_kcal | int | yes |  |
| protein_g | int | yes |  |
| carbs_g | int | yes |  |
| fat_g | int | yes |  |
| source | text | yes | initial/manual/auto_suggestion |
| status | text | yes | active/proposed/archived |
| explanation | text | optional |  |
| calculated_at | timestamptz | yes |  |

### Local persistence foundation

The FastAPI service uses a repository boundary backed by Neon Postgres when `DATABASE_URL` is set and local sqlite otherwise (`CAL_AI_API_DATA_PATH`, default `.local/cal-ai-api.db`). It stores restart-stable metadata for:

- `image_uploads`: upload id, local asset metadata, storage provider, object key, server-owned `image_reference`, cleanup readiness metadata; no image bytes in API bodies.
- `analysis_jobs`: create request, returned job id/status, latest job response JSON.
- `clarifications`: submitted answers and resulting narrowed analysis response.
- `meal_logs`: save request and saved-impact response.

The mobile app includes an optional Supabase Auth Kakao OAuth gate with PKCE and secure session storage. When `AUTH_PROVIDER=supabase`, FastAPI requires `SUPABASE_JWT_ALGORITHM=RS256|ES256`, verifies the asymmetric Supabase JWT through JWKS, and scopes profiles, image uploads, and analysis jobs to the token subject. Anonymous local development remains available only while auth is explicitly disabled. Body-photo consent evidence stores the consent timestamp, provider, model, and policy version with each check-in. Food analysis can call OpenAI directly through the Responses HTTP API when server-side env configuration enables it; local development remains mock-first.

### analysis_jobs

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | primary key |
| user_id | uuid | yes | indexed |
| image_object_key | text | yes | private bucket |
| status | text | yes | queued/running/needs_clarification/completed/failed |
| meal_type | text | optional | breakfast/lunch/dinner/snack |
| model_provider | text | optional |  |
| model_name | text | optional |  |
| raw_result_json | jsonb | optional | restricted access |
| normalized_result_json | jsonb | optional |  |
| error_code | text | optional |  |
| created_at | timestamptz | yes |  |
| completed_at | timestamptz | optional |  |

### meal_logs

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | primary key |
| user_id | uuid | yes | indexed |
| analysis_job_id | uuid | optional |  |
| meal_type | text | yes |  |
| eaten_at | timestamptz | yes |  |
| calories_kcal | int | yes | corrected final |
| protein_g | numeric | yes |  |
| carbs_g | numeric | yes |  |
| fat_g | numeric | yes |  |
| confidence | numeric | optional | final confidence |
| created_at | timestamptz | yes |  |
| updated_at | timestamptz | yes |  |

### meal_log_items

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | primary key |
| meal_log_id | uuid | yes | indexed |
| name | text | yes | localized |
| source_food_id | text | optional | nutrition source |
| estimated_grams | numeric | optional |  |
| calories_kcal | int | yes |  |
| protein_g | numeric | yes |  |
| carbs_g | numeric | yes |  |
| fat_g | numeric | yes |  |
| confidence | numeric | optional |  |
| assumptions | jsonb | optional |  |

### correction_events

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | primary key |
| user_id | uuid | yes | indexed |
| analysis_job_id | uuid | yes | indexed |
| meal_log_id | uuid | optional |  |
| correction_type | text | yes | rice_amount/eaten_ratio/broth/sauce/item_edit |
| before_json | jsonb | yes |  |
| after_json | jsonb | yes |  |
| created_at | timestamptz | yes |  |

### weight_logs

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | primary key |
| user_id | uuid | yes | indexed |
| weight_kg | numeric | yes | sensitive |
| logged_at | timestamptz | yes |  |

### recommendation_events

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | primary key |
| user_id | uuid | yes | indexed |
| type | text | yes | next_meal/target_adjustment |
| payload_json | jsonb | yes |  |
| user_feedback | text | optional | helpful/not_helpful |
| created_at | timestamptz | yes |  |

## 13. API Design

### POST /v1/onboarding

Purpose: create/update profile and initial nutrition target.

Request:

```json
{
  "age": 29,
  "sex": "male",
  "height_cm": 176,
  "current_weight_kg": 82,
  "target_weight_kg": 75,
  "goal_type": "lose",
  "activity_level": "moderate",
  "training_frequency": "3-4"
}
```

Response:

```json
{
  "profile_id": "uuid",
  "target": {
    "calories_kcal": 1850,
    "protein_g": 130,
    "carbs_g": 190,
    "fat_g": 55
  },
  "warnings": []
}
```

### POST /v1/analysis-jobs

Purpose: create food image analysis job.

Request:

```json
{
  "image_upload_id": "uuid",
  "profile_id": "profile-id",
  "meal_type": "lunch",
  "optional_note": "밥은 거의 다 먹었어요"
}
```

Response:

```json
{
  "analysis_job_id": "uuid",
  "status": "queued"
}
```

### POST /v1/image-uploads

Purpose: create a mock/local upload record before analysis job creation.

Request:

```json
{
  "local_asset_id": "local-demo-meal-preview",
  "file_name": "meal-preview.png",
  "content_type": "image/png",
  "byte_size": 420000
}
```

Response:

```json
{
  "image_upload_id": "local-upload-local-demo-meal-preview",
  "image_reference": "local-image://local-upload-local-demo-meal-preview",
  "status": "ready"
}
```

### POST /image-uploads/presign

Purpose: request a direct-to-R2 upload URL for a private bucket object.

Request:

```json
{
  "local_asset_id": "camera-roll-asset",
  "file_name": "meal-preview.png",
  "content_type": "image/png",
  "byte_size": 420000
}
```

Response:

```json
{
  "image_upload_id": "image-upload-uuid",
  "object_key": "uploads/image-upload-uuid/meal-preview.png",
  "upload_url": "https://...",
  "headers": { "Content-Type": "image/png" },
  "expires_at": "2026-06-20T00:15:00+00:00",
  "max_bytes": 8000000,
  "soft_limit_bytes": 8000000000,
  "soft_limit_exceeded": false,
  "ttl_days": 30
}
```

### POST /image-uploads/complete

Purpose: confirm a completed direct R2 upload and persist metadata for analysis job creation.

Request:

```json
{
  "image_upload_id": "image-upload-uuid",
  "object_key": "uploads/image-upload-uuid/meal-preview.png",
  "local_asset_id": "camera-roll-asset",
  "file_name": "meal-preview.png",
  "content_type": "image/png",
  "byte_size": 420000,
  "etag": "optional-storage-etag"
}
```

Response:

```json
{
  "image_upload_id": "image-upload-uuid",
  "image_reference": "r2://cal-ai-meal-images/uploads/image-upload-uuid/meal-preview.png",
  "status": "ready"
}
```

MVP constraints:

- Image bytes must not be uploaded through the Vercel API body.
- R2 remains private; clients upload directly with presigned PUT URLs.
- `IMAGE_UPLOAD_MAX_BYTES` is the per-image hard limit.
- `UPLOAD_SOFT_LIMIT_BYTES` is the aggregate image storage soft limit; presign is rejected when current pending/ready upload bytes plus the requested upload would exceed it.
- `complete` must match a previously persisted pending presign record by `image_upload_id`, `object_key`, `file_name`, `content_type`, and `byte_size`.
- For R2, `complete` performs a server-side presigned HEAD request and verifies that the object exists and its actual content length and content type match the pending record before setting `upload_status=ready`.
- Local development persistence uses sqlite via `CAL_AI_API_DATA_PATH`; production uses `DATABASE_URL`.
- Unknown `image_upload_id` values must fail before provider/model payload construction.
- Supported content types are JPG, PNG, and WebP.
- Images above 8MB are rejected.

### GET /v1/analysis-jobs/{id}

Purpose: read job state and result.

Response:

```json
{
  "id": "uuid",
  "status": "needs_clarification",
  "result": {
    "summary": {
      "calories_kcal": 615,
      "calorie_range": { "low": 540, "high": 710 },
      "protein_g": 31,
      "carbs_g": 72,
      "fat_g": 19,
      "confidence": 0.82
    },
    "clarification_questions": []
  }
}
```

### POST /v1/analysis-jobs/{id}/clarifications

Purpose: apply user clarification answers.

Request:

```json
{
  "answers": [
    { "question_key": "rice_amount", "value": "near_bowl" }
  ]
}
```

Response:

```json
{
  "status": "completed",
  "result": {
    "summary": {
      "calories_kcal": 615,
      "calorie_range": { "low": 580, "high": 660 },
      "protein_g": 31,
      "carbs_g": 72,
      "fat_g": 19,
      "confidence": 0.9
    }
  }
}
```

### POST /v1/meal-logs

Purpose: save confirmed analysis as meal log.

Request:

```json
{
  "analysis_job_id": "uuid",
  "result_id": "analysis-result-id",
  "clarification_value": "one_bowl",
  "profile_id": "profile-id",
  "logged_on": "2026-06-09",
  "nutrition_override": {
    "meal_name": "직접 수정한 닭가슴살 덮밥",
    "calories_kcal": 510,
    "protein_g": 42,
    "carbs_g": 55,
    "fat_g": 12
  }
}
```

`nutrition_override` is optional. When present, the saved meal is marked as user-confirmed/manual and the corrected values drive dashboard accumulation.

### GET /v1/dashboard/today

Purpose: get today intake, targets, and next-meal guidance.

### POST /v1/weight-logs

Purpose: save weight log.

### GET /v1/recommendations/next-meal

Purpose: get nutrient-gap and menu-type recommendation.

### DELETE /v1/profiles/{profile_id}

Purpose: permanently delete profile-scoped app data, unsaved profile-linked scans, authenticated owner uploads, and linked private image objects. Supabase Auth identity deletion remains a separate re-authenticated operation. Image metadata enters a retryable `deleting` state before object deletion so a partial failure does not lose the object key required for recovery.

### GET /internal/cleanup-images

Purpose: daily retention cleanup for expired private image objects. The endpoint requires `Authorization: Bearer <CRON_SECRET>` and is invoked by Vercel Cron once per day.

## 14. AI Call Design

### Model Roles

1. Vision extraction model
   - reads image
   - detects food evidence
   - returns structured candidates

2. Nutrition resolver
   - deterministic/service layer
   - maps candidates to nutrition DB

3. Clarification planner
   - model or rule-assisted
   - chooses at most 2 high-impact questions

4. Recommendation generator
   - uses deterministic nutrient gap plus controlled LLM phrasing

### Structured Output Requirements

All AI calls that affect saved nutrition values must return schema-validated JSON. The app must reject or retry malformed outputs.

### Prompt Constraints

- Do not provide medical diagnosis.
- Do not claim exact calorie precision.
- Return uncertainty reasons.
- Prefer Korean-localized food labels.
- Separate visible evidence from assumptions.
- Do not invent brand/package facts from image unless visible.

## 15. Privacy, Security, and Retention

### Data Sensitivity

Sensitive:

- height
- weight
- goal weight
- food logs
- images
- health-related goals

### Retention Defaults

- Raw food/body images: retain for `IMAGE_TTL_DAYS` (default 30 days), then delete through the daily cleanup job.
- Analysis JSON: retain for history and personalization.
- Raw AI responses: restricted access, consider shorter retention.
- Deleted profile data: mark image metadata as `deleting`, remove linked private storage objects, then remove meal, coach, analysis, and image metadata before returning success. Failed deletion remains retryable because the object key is retained until finalization.

### Access Control

- Users can only access their own records.
- Admin access to raw images should be restricted and audited.
- Use signed URLs for private images.

### Training Use

- Do not use user images or logs for model training without explicit opt-in.

## 16. Analytics and Evaluation

### Product Events

- onboarding_started
- onboarding_completed
- analysis_job_created
- analysis_job_completed
- clarification_shown
- clarification_answered
- meal_saved
- meal_edited
- recommendation_viewed
- target_adjustment_suggested
- target_adjustment_accepted

### AI Quality Metrics

- average confidence
- correction rate
- calorie delta after correction
- clarification answer rate
- failed analysis rate
- outlier estimate rate
- saved rate by confidence label

### Evaluation Dataset

Create a small internal test set:

- Korean rice bowl
- soup/stew meal
- multi-side-dish meal
- convenience store packaged meal
- salad/protein meal
- delivery food
- low-quality image

Each case should define expected detected items, uncertainty reasons, and likely clarification questions.

## 17. Nonfunctional Requirements

- Mobile-first.
- Analysis job p95 target: TBD after provider selection.
- API responses must have typed error codes.
- Food scan failures must offer retry and manual note fallback.
- Dashboard should load even if recommendation generation fails.
- App must work gracefully on slow network.
- Accessibility: tap targets at least mobile-friendly size; color should not be the only status indicator.

## 18. Environment Variables

Expected:

```text
DATABASE_URL=
REDIS_URL=
CORS_ALLOWED_ORIGINS=http://localhost:8081,http://127.0.0.1:8081
STORAGE_PROVIDER=local
R2_BUCKET_NAME=
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_ENDPOINT=
R2_REGION=auto
IMAGE_UPLOAD_MAX_BYTES=8000000
IMAGE_TTL_DAYS=30
UPLOAD_SOFT_LIMIT_BYTES=8000000000
CRON_SECRET=
AI_PROVIDER_API_KEY=
AI_PROVIDER=mock
BODY_AI_PROVIDER=mock
AI_MODEL_VISION=
AI_MODEL_TEXT=
AUTH_PROVIDER=disabled
SUPABASE_URL=
SUPABASE_JWT_ALGORITHM=ES256
ADMIN_DASHBOARD_ENABLED=false
ADMIN_SUPABASE_URL=
ADMIN_SUPABASE_JWT_ALGORITHM=ES256
ADMIN_USER_IDS=
ANALYTICS_TIMEZONE=Asia/Seoul
PAYMENT_PROVIDER=disabled
GROBLE_PRODUCT_ID=
GROBLE_WEBHOOK_SECRET=
POSTHOG_KEY=
SENTRY_DSN=
```

Groble variables remain unset until signed order creation and webhook verification are implemented.

## 19. Design Integration Contract

Current design source:

- `DESIGN.md`

Implementation must:

- use semantic, replaceable design tokens derived from `DESIGN.md`
- keep component names close to the `DESIGN.md` component inventory
- preserve trust-first UX requirements: calorie range, confidence, uncertainty reasons, and at most 2 clarification questions
- avoid hard-coded competitor-clone styling or exact copied UI structures

After Figma/design work, update this document with:

- final design token names
- color roles
- typography scale
- component inventory
- screen route mapping
- asset handling policy
- paywall visual states, if pricing is decided

Until then, implementation should use replaceable tokens aligned to `DESIGN.md`.

## 20. Open Technical Decisions

- Exact auth provider
- FastAPI vs Next.js API if web-first strategy changes
- Initial Korean nutrition DB source and licensing
- Image retention duration
- Exact AI provider/model names
- Whether MVP is Expo mobile app only or also web/PWA
- Billing launch timing

## 21. Separate Admin, Analytics, and Billing Foundation

`apps/admin` is a standalone Vite application deployed from its own Vercel project and domain. The consumer Expo app contains no admin route or link. Admin authentication uses a manually created Supabase email/password account; the browser receives only the publishable key. FastAPI verifies the asymmetric Supabase JWT and then requires the token subject to match `ADMIN_USER_IDS`. Disabled admin routes return `404`, valid non-admin users receive `403`, and responses use `Cache-Control: no-store`.

Neon Postgres remains canonical in production, with sqlite fallback locally. The operational tables are `app_users`, `app_sessions`, `product_events`, `billing_subscriptions`, `billing_payments`, and `admin_audit_logs`. Mobile analytics are non-blocking and use an event-name whitelist, a property-key allowlist, 30-minute sessions, and one-minute foreground heartbeats. “Realtime” means activity within five minutes, not a socket connection.

The admin API exposes `GET /internal/admin/overview` and `GET /internal/admin/users/{user_id}`. Funnel stages are sequential within a 30-day window. User first-seen time is the first authenticated event observed by Cal AI; exact Supabase signup time requires a trusted Auth event integration.

`GET /v1/billing/status` powers an honest free-beta plan screen. Billing tables and UI are present, but `checkout_available` stays false until Groble order creation, signature verification, idempotent webhook handling, and entitlement updates are implemented and approved.

## 22. Repeat Logging and Adaptive Workout Targets

### Meal record operations

Profile-scoped meal APIs expose stable `meal_log_id` values. Repeat creates a new record using the confirmed nutrition payload from the source meal and does not create a new analysis job or AI request. Delete removes only the selected meal record. Both operations rebuild the daily dashboard from persisted meal records so totals cannot depend on stale nested dashboard snapshots.

Required operations:

- `GET /v1/profiles/{profile_id}/meal-logs`
- `POST /v1/profiles/{profile_id}/meal-logs/{meal_log_id}/repeat`
- `DELETE /v1/profiles/{profile_id}/meal-logs/{meal_log_id}`

### Adaptive workout recommendation

Exercise performance captures aggregate completed sets, repetitions, load, and exercise-level effort (`easy`, `on_target`, `hard`) for the MVP. After a session is persisted, the active workout plan is updated with the prior performance and next recommendation.

The deterministic recommendation order is:

1. Missing load or repetition evidence: collect a baseline and do not prescribe an increase.
2. Hard effort, session RPE 9+, or performance below the repetition range: hold or reduce load conservatively.
3. Easy effort at the top of the repetition range with all planned sets complete: increase by the smallest usable equipment step; if that jump is too large, hold instead.
4. On-target work: hold load and progress repetitions before load.
5. Low recovery in the latest wellness check-in: suppress increases even when performance was strong.

Every recommendation includes an action, target, and plain-language reason. The client may display this structured recommendation but must not convert it into a medical or injury claim.

Required operation:

- `GET /v1/profiles/{profile_id}/workout-history`
