# 운동 기구 사진 가이드: 제품·기술 명세

## 목적과 위치

사용자가 헬스장에서 낯선 기구를 만났을 때 운동 탭의 현재 루틴에서 바로 사진을 찍어 기구 종류를 확인하고, 해당 기구의 사용법 영상을 찾게 한다. 별도 메인 탭이나 사진 기반 운동 처방은 만들지 않는다. 계획이 없더라도 운동 탭에서 기구 찾기는 접근할 수 있다. 식단·체형 사진 흐름과 분리한다.

## 검증된 참고 서비스 (2026-09-30 확인)

- [Fitbod 운동 라이브러리](https://fitbod.me/about-fitbod-exercises/): 자사 발표 1,000만 명 이상 사용자, 1,600개 이상 운동, 80종 이상 기구의 전문가 촬영 시연. 시사점: 기구 이름을 끝점으로 두지 말고 운동 맥락과 동작 가이드로 연결한다.
- [Hevy 운동 라이브러리](https://help.hevyapp.com/hc/en-us/articles/35688251991575-Hevy-Exercise-Library-400-Exercises-and-Custom-Exercises): 400개 이상 운동, 기구·근육 필터, 동작 애니메이션과 단계별 설명. 루틴 편집·운동 기록 중에도 탐색 가능. 시사점: 기록 흐름 안에서 가이드를 열고 돌아오게 한다.
- [Hevy Google Play](https://play.google.com/store/apps/details?id=com.hevy): 500만 회 이상 다운로드와 인앱 구매가 확인되는 운영 서비스.
- [YouTube Data API search.list](https://developers.google.com/youtube/v3/docs/search/list): 서버 키로 영상 결과를 검색한다. 키가 없으면 영상 카드를 꾸며내지 않고 YouTube 검색 결과 URL만 제공한다. 검색 할당량과 결과 품질을 운영에서 모니터링한다.

참고 서비스의 콘텐츠나 UI를 복제하지 않는다. 이 기능의 차별점은 사진 식별 후 신뢰도·수동 수정·오늘 루틴 연결을 한 화면에 두는 것이다.

## 사용자 흐름

1. 운동 탭의 `기구 사용법 찾기`에서 카메라/앨범을 연다. 사람 얼굴이나 다른 이용자가 보이지 않도록 안내한다.
2. 사진 전송·OpenAI 분석 동의를 받고 기존 이미지 압축과 private R2 presign/PUT/complete 흐름을 재사용한다. 전용 presign은 서버에서 ID와 고정 파일명을 생성하고 PUT 유효시간을 120초로 제한한다. 클라이언트 원본 파일명은 서버에 보내지 않는다.
3. `POST /v1/profiles/{profile_id}/equipment-identifications`에 업로드 ID를 보낸다. 서버는 인증·프로필 소유권·업로드 소유권과 ready 상태를 확인한다.
4. AI는 18종 기구 카탈로그 ID 하나 또는 `unknown`, 신뢰도와 눈에 보이는 근거만 반환한다. 낮은 신뢰도/unknown이면 확정 표현을 하지 않는다. 분석 후 원격 이미지를 삭제하고 재업로드를 정리할 tombstone을 PUT 만료 + 1시간까지 유지한다. 삭제 실패는 결과를 버리지 않고 `cleanup_pending`으로 표시한다.
5. 사용자가 기구를 확인하거나 카탈로그에서 수정한다. 수동 선택도 동일한 다음 흐름을 쓴다.
6. `GET /v1/equipment-guides/{equipment_id}`는 검증된 카탈로그의 한국어 검색어로 YouTube API를 조회한다. 키가 없거나 할당량/응답 오류면 YouTube 검색 결과 링크를 제공한다. 외부 영상은 검증된 전문가 콘텐츠라고 표시하지 않는다.
7. 오늘 루틴과 관련되는 운동이 있으면 화면에 보여주되 루틴·세트·중량을 자동 변경하지 않는다. 사용법을 확인한 뒤 원래 운동 기록 위치로 돌아간다.

## API와 데이터 계약

- `GET /v1/equipment-guides/catalog`: ID, 한국어명, 관련 운동, 기본 주의 문구. 인증된 앱 세션에서 접근.
- `POST /v1/profiles/{profile_id}/equipment-image-uploads/presign`: `{ content_type: image/jpeg|image/png|image/webp, byte_size }` → 기존 presign 계약. 프로필·로그인 소유권과 provider 준비를 확인한 뒤 발급.
- R2 직접 PUT 후 `POST /image-uploads/complete`: 기존 완료 계약. SQLite/Postgres 모두 조건부 `pending → ready` 전환으로 완료/삭제/분석 간 경쟁을 막는다.
- `POST /v1/profiles/{profile_id}/equipment-identifications`: `{ image_upload_id }` → `{ equipment_id | null, confidence: high|medium|low|none, visible_evidence: string[], needs_confirmation: true, cleanup_pending: boolean }`. AI 비활성화 시 구조화된 503과 수동 선택 경로. 같은 요청을 다시 보내면 저장된 결과를 반환하고 AI를 재호출하지 않는다.
- `DELETE /v1/profiles/{profile_id}/equipment-image-uploads/{image_upload_id}`: 업로드 취소·실패 시 소유권 검증 후 정리. 이미 분석 중이면 서버 분석 종료 정리를 기다린다.
- `GET /v1/equipment-guides/{equipment_id}` → `{ equipment_id, name, search_url, source: youtube_api|search_link, videos: [{ video_id, title, channel_title, url }] }`. ID가 카탈로그 밖이면 404. URL은 YouTube 허용 호스트만.
- 기구 카탈로그는 서버가 소유한다. 모델 출력·사용자 입력을 검색어/URL로 직접 사용하지 않는다.
- `EQUIPMENT_AI_PROVIDER=disabled|openai` (기본 disabled), `EQUIPMENT_RETENTION_VERIFIED=false|true` (기본 false), `EQUIPMENT_DAILY_LIMIT=10`, `EQUIPMENT_GLOBAL_DAILY_LIMIT=100`. 기존 서버 전용 `AI_PROVIDER_API_KEY`와 `AI_MODEL_VISION` 재사용. `YOUTUBE_API_KEY`는 서버 전용 선택값. 공개 클라이언트 번들에 키를 넣지 않는다.

## 안전·운영

- 사진은 사용자 기록으로 장기 보관하지 않는다. 분석 직후 삭제를 시도하고, PUT 만료 + 1시간 이후 다시 삭제해 재전송 파일도 정리한다. 업로드 중단·삭제 실패는 `IMAGE_TTL_DAYS` 및 cleanup 경로가 처리한다. pending 업로드에도 presign 시점부터 정리 시간이 있다. [R2 presigned URL은 만료 전 재사용 가능](https://developers.cloudflare.com/r2/api/s3/presigned-urls/)하므로 객체 키를 즉시 잊어버리면 안 된다.
- [Vercel cron은 production을 대상으로 실행](https://vercel.com/docs/cron-jobs)한다. Preview에 cron이 있다고 정리가 보장된다고 판단하지 않는다. Preview 전용 DB/버킷과 정리 실행기 또는 R2 lifecycle을 실제 확인하기 전에는 `EQUIPMENT_RETENTION_VERIFIED=true`를 설정하지 않는다. 기본값은 AI 활성화를 차단한다.
- 기존 `coach_events`에 기구 결과 영수증을 저장한다. 별도 `equipment_usage`는 업로드 ID, 인증 사용자 ID의 SHA-256 값, 상태, 시각만 저장해 프로필 삭제·재생성으로 유료 한도를 우회하지 못하게 한다. SQLite `BEGIN IMMEDIATE`, Postgres transaction advisory lock으로 계정 일일 한도, 전체 일일 한도, 계정 동시 1회·전체 동시 3회를 직렬화한다. 실패한 시도도 한도에 포함하며 중복 영수증 조회는 제외한다. 결과 영수증은 프로필 삭제 시 제거한다. 최소 남용 방지 원장은 프로필 삭제 후에도 유지하며 cleanup에서 2일 이후 정리한다. 사용자 해시는 익명 정보로 간주하지 않는다.
- 프로필 삭제 시 만료 전 R2 PUT 재전송을 정리할 객체 키·기한만 남기고 소유자·로컬 자산 식별자는 제거한다. 취소와 분석 시작은 조건부 상태 변경으로 경쟁하며 이미 분석이 선점한 사진은 취소 요청이 삭제하지 않는다. 완료/실패 영수증은 반대 상태로 되돌리지 않으며 저장 성공 뒤 응답 확인만 실패하면 완료 영수증을 다시 읽어 재과금 없이 결과를 반환한다.
- 모델 요청은 `store=false`, 출력 350토큰, 22초 타임아웃, 자동 유료 재시도 없음이다. 사진에서 사람이나 건강·자세·브랜드를 추정하지 않도록 제한한다. OpenAI 측 보관 정책은 별도로 확인해야 하며 서버 삭제를 제3자 즉시 삭제로 설명하지 않는다.
- 화면 종료는 작업 단위 AbortSignal을 취소하고, 이미 발급된 업로드 ID는 인증된 discard로 정리한다. 전송되지 않은 분석은 시작하지 않는다. 이미 공급자에게 간 호출은 강제로 취소할 수 없으며 서버가 종료 후 정리한다. Web blob URL은 해제하며 네이티브의 이미지 준비 파일은 앱의 임시 캐시를 사용한다.
- 토큰 갱신으로 actions 객체가 바뀌어도 진행 중인 분석을 초기화하지 않는다. 계정 변경은 기존 OwnerApp 분리로 전체 작업을 취소한다.
- YouTube 성공은 1시간, 빈 결과/일반 오류는 5분 캐시하고, 403/429는 1시간 cooldown으로 검색 링크로 전환한다. 같은 인스턴스 내 기구별 single-flight를 사용한다. 서버리스 인스턴스 간 검색 캐시는 공유되지 않으므로 공급자 키의 할당량 제한·모니터링을 유지한다.
- 사진에 기구가 없거나 여러 기구가 겹치거나 불확실하면 `unknown` 또는 낮은 신뢰도로 반환하고 수동 선택을 권한다.
- 영상은 외부 제3자 콘텐츠이며 품질이 보증되지 않는다. 통증/부상/높은 중량은 전문가 확인을 안내한다.
- AI 유료 호출과 YouTube 쿼터 소비는 해당 서버 환경변수를 명시적으로 활성화할 때만 발생한다. 이 브랜치의 자동 테스트는 네트워크/유료 호출을 하지 않는다.
- `main` 병합/프로덕션 배포는 이 작업 범위에서 하지 않는다. 피처 브랜치와 Vercel Preview 배포만 허용한다.

## 활성화 및 검증 경계

브랜치: `codex/equipment-photo-guide`. 기본 Preview는 수동 기구 검색과 YouTube 링크를 사용할 수 있고 사진 AI는 비활성화 상태다. 실제 제공자 활성화는 별도 승인·검증 단계다.

1. Preview 전용 DB/스토리지, 버킷 CORS에 Preview origin, Supabase redirect allowlist와 로그인 세션을 확인한다.
2. 본인 소유 테스트 파일로 업로드 중단·삭제 실패·PUT 재사용 후 만료 정리를 확인한다. 운영 사용자 이미지를 테스트에 쓰지 않는다.
3. 정리가 실제 확인되면 Preview에만 `EQUIPMENT_RETENTION_VERIFIED=true`, `EQUIPMENT_AI_PROVIDER=openai`를 넣고 재배포한다. 이 시점부터 유료 호출이 가능하다. 키는 Vercel 서버 환경변수에만 둔다.
4. `YOUTUBE_API_KEY` 없이도 검색 링크는 동작한다. 실제 영상 목록이 필요하면 YouTube Data API v3 키를 서버 환경변수에 등록하고 API/쿼터 제한을 설정한다.
5. 실제 기구 사진 1회 분석 → 기구 확인/수정 → 영상 열기 → 원래 운동의 중량/체크 유지 → 서버 객체 정리를 검증한다. Android/iPhone 실기기 카메라·앨범·뒤로가기는 Web 테스트로 대체하지 않는다.

Web Preview는 같은 origin의 API를 호출한다. 로컬 Expo Web은 기존 `http://localhost:8015`를 기본으로 사용하고 다른 포트는 `EXPO_PUBLIC_API_BASE_URL`로 지정한다. 네이티브의 기존 API 설정은 유지한다.

## 수용 기준

- 로그인·소유권이 없는 스캔 요청은 거부되고 이미지가 다른 계정에 연결되지 않는다.
- 고정 카탈로그 외 AI 출력, malformed 결과, 공급자 실패는 실패 안전으로 처리된다.
- YouTube 키가 없어도 검색 링크가 작동하고, 키가 있으면 검증한 영상 URL만 노출한다.
- 사진 업로드·분석·수정·영상 열기·운동 기록 복귀가 모바일/웹에서 연결된다.
- API 테스트, shared/mobile typecheck, mobile smoke, web export, `git diff --check`가 통과한다.
