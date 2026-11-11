import os
import re
from datetime import date
from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(include_in_schema=False)

OPERATOR = "아르케"
SUPPORT_EMAIL = "areche.ai.kr@gmail.com"
DEFAULT_POLICY_EFFECTIVE_DATE = "2026-11-10"
DEFAULT_POLICY_VERSION = "2026-11-10.1"

PAGES = {
    "privacy": ("개인정보처리방침", """
<p>Trust First Nutrition의 운영자는 아르케입니다. 이 문서는 계정, 식사·운동·신체 체크인과 이용 기록의 처리 경로를 설명합니다. 개인정보 문의와 권리 요청은 <a href="/support">문의 페이지</a>의 이메일로 보낼 수 있습니다.</p>
<nav aria-label="개인정보 문서 목차"><ul>
<li><a href="#data">정보와 이용 목적</a></li><li><a href="#photos">사진과 건강정보</a></li>
<li><a href="#processors">외부 처리</a></li><li><a href="#retention">보관과 삭제</a></li>
<li><a href="#rights">권리 요청</a></li><li><a href="#age">연령과 미확정 사항</a></li></ul></nav>
<h2 id="data">어떤 정보를 왜 사용하나요?</h2>
<dl><dt>계정과 로그인</dt><dd>인증 제공자의 사용자 식별자, 로그인 제공자 종류, 제공되는 경우 이메일과 표시 이름을 인증, 기록 소유권 확인, 운영자용 이용 현황에 사용합니다. 이메일 로그인 시 입력한 비밀번호는 Supabase 인증 경로로 전달됩니다. 앱 기록 API는 비밀번호 대신 인증 토큰을 사용합니다. 이메일 로그인 성공만으로 별도의 이메일 소유권 검증이 완료되었다고 단정하지 않습니다.</dd>
<dt>목표 설정과 건강·활동 기록</dt><dd>나이, 성별, 키, 현재·목표 체중, 목표 종류, 활동량, 운동 빈도·경험·장비·가능 시간을 목표 계산과 운동 계획에 사용합니다. 식사 종류·날짜·메모·영양 추정치·보정 답변, 체중 기록, 수면의 질·에너지·근육통·회복 메모, 운동 세트·반복·중량·강도·시간을 기록 관리와 코칭에 사용합니다. 분석 결과와 동의 이력도 저장할 수 있습니다.</dd>
<dt>선택한 사진과 업로드 정보</dt><dd>음식 사진은 식단 분석에, 신체 사진은 체크인 관찰에 사용합니다. 파일 이름·형식·크기, 이미지 식별자·저장 위치, 업로드 상태·시각·만료 예정 시각을 업로드 확인과 정리에 사용합니다.</dd>
<dt>서비스 이용 기록</dt><dd>계정·프로필·세션 식별자, 화면 이름, 기능 실행·완료·오류 이벤트와 시각, 마지막 활동 시각을 이용 현황·이탈 분석과 장애 대응에 사용합니다. 허용된 이벤트 속성에는 목표 종류, 보정 답변, 운동 시간·강도 등이 포함될 수 있어 이용 기록이 항상 익명인 것은 아닙니다. 운영자용 화면에서 계정별 활동을 조회할 수 있습니다.</dd>
<dt>기기 내 정보와 문의</dt><dd>로그인 세션, 프로필 식별자와 분석용 세션 식별자가 기기에 저장됩니다. 네이티브 앱의 인증 세션은 SecureStore, 웹 인증 세션과 일부 앱 식별자는 브라우저·앱 로컬 저장소를 사용합니다. 이메일 문의 시 직접 보낸 연락처와 문의 내용도 지원 과정에서 처리됩니다.</dd></dl>
<h2 id="photos">건강정보와 사진은 어떻게 선택하나요?</h2>
<p>체중·신체 사진·회복 기록은 건강 상태를 드러낼 수 있는 민감한 정보입니다. 목표 계산에 필요한 입력과 달리 사진·메모·추가 체크인은 해당 기능을 선택할 때 전송합니다. 사진을 제공하지 않아도 사진 분석 이외의 목표·체중·운동 기록을 이용할 수 있습니다. 다른 사람의 사진, 얼굴이나 불필요한 개인정보가 담긴 사진·메모는 보내지 마세요.</p>
<p>카메라 촬영은 기기 권한을 요청하고, 사진첩에서는 시스템 선택기로 고른 이미지를 이용합니다. 권한을 거부하거나 선택을 취소하면 해당 사진 기능을 진행하지 않습니다. 기기 설정에서 카메라 권한을 바꿀 수 있습니다. 권한 철회만으로 이미 업로드한 사진이 삭제되지는 않습니다.</p>
<p>신체 체크인은 로그인과 별도의 AI 분석 동의가 필요하며, 동의 시각·제공자·모델·동의 정책 버전을 기록합니다. 신체 사진 분석은 보수적인 운동 맥락의 관찰이며 신원·질환·체지방률·외모 점수 판정을 목적으로 하지 않습니다. 음식 영양 추정과 코칭도 의료 진단이나 치료가 아닙니다. 이 동의 기록만으로 모든 건강정보 처리에 필요한 법적 근거가 확정된 것은 아닙니다.</p>
<h2 id="processors">외부 서비스에는 무엇이 전달되나요?</h2>
<p>아래는 코드에 구현된 연결 경로입니다. 실제 이용되는 제공자는 운영 설정에 따라 달라지며, 이 목록은 배포 상태나 위탁·국외 이전 계약이 확인되었다는 뜻이 아닙니다.</p>
<dl><dt>Vercel</dt><dd>웹·API 호스팅을 위한 라우팅과 작업 일정 설정이 있습니다. 호스팅 과정의 요청 처리와 운영 로그 세부사항은 별도 확인이 필요합니다.</dd>
<dt>Supabase와 카카오</dt><dd>Supabase 인증을 사용하는 경우 계정 인증과 세션을 처리합니다. 카카오 로그인 경로도 있으며 실제 제공 정보는 로그인 제공자 설정에 따릅니다. Supabase의 앱 로그인 계정 삭제와 카카오 계정 자체의 삭제는 다릅니다.</dd>
<dt>Postgres 연결과 Neon, Cloudflare R2</dt><dd>앱 기록은 설정된 Postgres 데이터베이스 또는 로컬 SQLite에 저장하는 코드가 있습니다. Neon 연결 여부·지역은 별도 확인 대상입니다. R2가 선택되면 사진 파일과 업로드 정보가 전달되고, 제한 시간 서명 주소로 업로드·분석용 읽기를 허용합니다. 로컬·모의 저장 경로도 존재합니다.</dd>
<dt>OpenAI</dt><dd>실제 AI 제공자로 활성화된 경우 음식 사진의 분석용 주소, 식사 종류와 선택 메모를 전송합니다. 신체 분석에는 동의한 사진의 분석용 주소, 촬영 방향과 이전 체크인 존재 여부를 전송하며 이전 사진 자체는 이 요청에 포함하지 않습니다. 모의 분석 경로도 있습니다. 요청은 응답 저장을 끄는 옵션을 사용하지만, 이것만으로 제공자의 모든 로그·보관이 없거나 즉시 삭제된다고 보장하지 않습니다.</dd></dl>
<p>현재 확인한 이용 분석은 자체 API와 데이터베이스 경로입니다. 설정 예시에 PostHog·Sentry 항목이 있다는 사실만으로 외부 전송이 활성화되었다고 볼 수 없습니다. 각 제공자의 실제 수신 법인·처리 국가·이전 시점과 방식·보관 조건·재위탁·계약 및 적용 법적 근거는 운영자가 확정해야 할 미확인 사항입니다.</p>
<h2 id="retention">얼마나 보관하고 어떻게 삭제하나요?</h2>
<ul><li><strong>일반 기록·이용 기록:</strong> 저장·조회·삭제 경로는 있지만, 모든 기록에 적용되는 자동 보관 기한은 코드에서 확인되지 않았습니다. 기기에서 로그아웃하거나 앱을 삭제하는 것만으로 서버 기록이 삭제되지는 않습니다.</li>
<li><strong>사진:</strong> 업로드 완료 시 설정된 기간으로 만료 예정 시각을 계산하고 정리 API가 삭제를 시도합니다. 설정 예시의 사진 만료값은 30일이며 실제 운영 보관 기한이 확인된 값은 아닙니다. 정기 작업의 배포·실행·성공 여부는 확인되지 않았으므로 30일 이내 자동 삭제를 보장하지 않습니다. 사진 정리와 이미지 메타데이터·분석 결과·식사 기록 삭제는 별개입니다.</li>
<li><strong>프로필 기록 삭제:</strong> ‘내 앱 데이터 모두 삭제’는 현재 프로필 기록과 연결 사진을 대상으로 하며, 로그인 계정은 유지됩니다. 이 작업은 해당 계정의 이용 분석 이벤트·세션·분석용 사용자 정보도 함께 삭제합니다. 분석 정보의 삭제 범위는 현재 프로필에만 한정되지 않습니다. 식사 기록 하나의 삭제도 계정·사진·이용 기록 전체 삭제와 같지 않습니다.</li>
<li><strong>계정 탈퇴:</strong> 인증된 요청과 최종 확인 후 서버가 삭제 요청을 접수합니다. 접수 후에는 일반 API 이용과 새 기록 작성을 차단하고, 별도 서버 작업이 계정의 앱 기록·이용 기록·연결 사진과 Supabase 인증 계정 삭제를 진행하도록 구현되어 있습니다. 접수·로그아웃·인증 계정 삭제만으로 모든 삭제가 완료된 것은 아닙니다.</li>
<li><strong>삭제 후에도 남는 상태 정보:</strong> 접근 차단·재시도를 위한 계정 식별자, 삭제 단계·시각, 사진 객체 키와 정리 이력 등이 별도로 남을 수 있습니다. 삭제 완료 응답이 있는 경우에도 계정 식별자와 삭제 상태는 남습니다. 현재 코드에는 이 정보의 자동 만료가 없습니다. 일부 신규 R2 업로드에는 재생성 방지용 빈 객체를 남기는 선택 기능이 구현되어 있으나 기본적으로 비활성화되어 있고 실제 저장소 검증이 필요합니다. 활성화되더라도 사진 내용이 없는 0바이트 객체와 임의 객체 키가 남습니다. 기존 업로드나 저장 위치가 확인되지 않는 사진은 안전한 정리 조건을 검증하기 전까지 처리 중으로 유지합니다. 이 상태 정보의 최종 보관 기한과 외부 제공자 로그·백업의 삭제 범위는 확정되지 않았습니다.</li></ul>
<p>삭제 기능의 운영 활성화, 재시도 작업과 실제 삭제 결과는 별도로 검증해야 합니다. 즉시 삭제·특정 완료 기한·모든 사본의 완전 삭제를 약속하지 않습니다. 적용될 법정 보존 항목·기간과 문의 이메일 보관 기간도 운영자 확인 대상이며, 이 문서가 임의로 보존 의무나 기간을 정하지 않습니다. <a href="/account-deletion">계정 삭제 안내</a>에서 절차와 한계를 확인해 주세요.</p>
<h2 id="rights">열람·정정·삭제·동의 철회는 어떻게 요청하나요?</h2>
<p>앱에서 제공되는 조회·수정·삭제 기능을 이용할 수 있습니다. 제공되지 않는 항목의 열람·정정, 처리 정지, 동의 철회, 삭제 및 자료 제공 요청은 문의 이메일로 보내 주세요. 원하는 조치와 관련 계정·기록을 식별할 최소한의 설명만 적어 주세요. 이메일 발신 주소만으로 소유권을 확정하지 않으며, 타인 정보가 처리되지 않도록 안전한 확인 절차가 필요합니다.</p>
<p>사진 분석을 원하지 않으면 추가 사진 전송·동의를 중단할 수 있습니다. 이미 저장된 정보의 삭제는 별도로 요청해야 합니다. 처리 기한·제한 사유·확인 방식은 요청과 실제 운영 조건에 따라 안내해야 하며, 이 문서에서 자동 처리나 고정 응답 기한을 확약하지 않습니다. 원본 신체 사진, 비밀번호, 인증 코드, 인증 토큰 또는 API 키를 이메일이나 공개 게시물에 첨부하지 마세요.</p>
<h2 id="age">연령 기준과 정책 변경</h2>
<p>이 서비스의 이용 대상은 만 18세 이상입니다. 목표 설정은 입력 만 나이를 18~100세로 제한합니다. 이는 자기 입력값 검사이며 실제 나이 확인이나 보호자 동의 확인이 아닙니다. 입력값 제한만으로 이미 저장된 프로필의 접근까지 차단하는 것은 아닙니다. 만 18세 미만은 이용할 수 없으며, 해당 연령의 정보 처리가 우려되면 문의해 주세요.</p>
<p>이 페이지의 시행일과 정책 문서 버전은 아래 표시된 문서 기준입니다. 중요한 변경은 변경 내용과 적용일을 서비스에서 안내해야 합니다. 신체 분석 동의에 저장되는 정책 버전은 별도 설정이며, 이 페이지 버전을 바꾸어도 기존 동의가 갱신되거나 다시 수집되지는 않습니다.</p>
"""),
    "terms": ("서비스 이용약관", """
<h2>서비스 범위</h2><p>Trust First Nutrition은 식사·영양 기록, 목표 관리, 운동 계획과 수행 기록, 신체 체크인 및 코칭을 제공합니다. 운영자는 아르케입니다.</p>
<h2>추정치와 안전</h2><p>사진 분석 결과는 음식의 조리법과 실제 섭취량에 따라 달라지는 추정치입니다. 저장 전에 결과를 확인하고 수정해 주세요. 운동·영양 코칭은 일반적인 정보이며 의료 행위, 진단, 치료나 특정 신체 변화의 보장이 아닙니다. 통증이나 건강상 우려가 있으면 운동을 중단하고 적절한 전문가에게 상담하세요.</p>
<h2>계정과 이용</h2><p>본인이 이용할 권리가 있는 계정과 사진만 사용해야 합니다. 다른 사람의 사진이나 기록을 동의 없이 업로드하거나 타인의 계정·데이터에 접근해서는 안 됩니다. 사용자는 기록 삭제와 계정 탈퇴를 요청할 수 있습니다.</p>
<h2>연령과 개인정보</h2><p>이 서비스의 이용 대상은 만 18세 이상입니다. 목표 설정의 입력 만 나이 범위는 18~100세입니다. 이는 자기 입력값 검사이며 실제 나이 확인이나 보호자 동의 확인이 아닙니다. 입력값 제한만으로 이미 저장된 프로필의 접근까지 차단하는 것은 아닙니다. 만 18세 미만은 이용할 수 없습니다. 건강·사진 정보, 외부 처리와 보관상의 한계는 <a href="/privacy">개인정보처리방침</a>을 확인해 주세요.</p>
<h2>유료 기능과 변경</h2><p>유료 기능은 실제 제공 시 가격, 결제 조건과 취소·환불 조건을 별도로 표시하고 동의를 받습니다. 이 문서만으로 결제나 구독이 시작되지 않습니다. 기능·정책의 중요한 변경은 서비스에서 안내해야 합니다.</p>
<h2>문의 및 탈퇴</h2><p>서비스 문제는 <a href="/support">문의 페이지</a>, 탈퇴는 <a href="/account-deletion">계정 삭제 안내</a>를 이용해 주세요.</p>
"""),
    "support": ("문의", """
<h2>도움이 필요하신가요?</h2><p>로그인, 기록, 분석 오류 및 개인정보 요청은 아래 이메일로 보내 주세요. 사용 환경과 발생한 화면·시간을 알려주시면 확인에 도움이 됩니다.</p>
<p><strong>비밀번호, 인증 코드, 인증 토큰, API 키, 원본 신체 사진은 보내지 마세요.</strong> 스크린샷은 계정·건강정보를 가린 후 전달해 주세요. 건강 관련 세부 내용은 문제 확인에 필요한 범위로 줄여 주세요.</p>
<h2>로그인과 Google Play 심사 접근</h2><p>로그인이 구성된 앱에서는 카카오 로그인 또는 ‘이메일로 로그인’을 선택할 수 있습니다. 이메일 로그인은 이미 발급된 계정의 이메일과 비밀번호를 앱의 로그인 화면에 입력하는 방식이며, 이 공개 페이지는 계정 발급·비밀번호 재설정·이메일 소유권 검증 기능을 제공하지 않습니다.</p>
<p>Google Play 심사용 계정과 접근 절차는 운영자가 Play Console의 비공개 앱 액세스 항목에 별도로 등록·검증해야 합니다. 심사 계정의 이메일·비밀번호는 이 페이지에 게시하지 않습니다. 심사 접근 성공이나 추가 인증 면제를 이 문서만으로 보장하지 않습니다.</p>
<h2>개인정보와 삭제 요청</h2><p>열람·정정·삭제·동의 철회 등 원하는 조치와 로그인 가능 여부를 알려 주세요. 이메일을 보냈다는 사실만으로 계정 소유권이 검증되거나 삭제가 접수·완료되는 것은 아닙니다. 안전한 소유권 확인 후 처리 범위와 진행 상태를 안내해야 합니다. 문의 수신 가능 여부·담당자·응답 기한은 별도 운영 확인 대상입니다.</p>
<p><a href="/account-deletion">계정과 연결된 기록 삭제 방법</a> · <a href="/privacy">개인정보처리방침</a></p>
"""),
    "account-deletion": ("계정 삭제", """
<h2>계정과 연결된 데이터를 삭제하려면</h2><ol>
<li><a href="/?action=delete-account">앱에서 계정 삭제 열기</a>를 누릅니다.</li>
<li>삭제할 계정으로 로그인합니다. 이 링크를 열거나 로그인하는 것만으로 삭제되지 않습니다.</li>
<li>개인정보와 안전 화면에서 삭제 범위를 읽고 ‘계정 탈퇴’를 선택합니다.</li>
<li>최종 확인 화면에 ‘탈퇴’를 입력하고 삭제를 확인합니다.</li></ol>
<h2>삭제 범위와 되돌릴 수 없는 작업</h2><p>삭제 대상은 Supabase의 앱 로그인 계정과 해당 계정의 앱 프로필·식사·운동·체중·회복·신체 체크인·분석·이용 기록 및 연결된 사진입니다. 기존 카카오 계정 자체나 기기 사진첩의 원본은 삭제 대상이 아닙니다. 삭제된 기록은 앱에서 복구할 수 없습니다. ‘내 앱 데이터 모두 삭제’는 현재 프로필 기록과 연결 사진을 지우고 로그인 계정은 유지하므로 계정 탈퇴와 다릅니다. 이 작업은 해당 계정의 이용 분석 이벤트·세션·분석용 사용자 정보도 함께 삭제합니다. 분석 정보의 삭제 범위는 현재 프로필에만 한정되지 않습니다.</p>
<h2>접수와 완료는 다릅니다</h2><p>서버가 요청을 접수하면 일반 API 이용과 새 기록 작성을 차단하고 별도 서버 작업으로 삭제를 진행합니다. ‘처리 중’은 완료가 아니며, 로그아웃되거나 인증 계정이 먼저 삭제되어도 사진 정리는 계속 필요할 수 있습니다. 삭제 기능이 운영 설정에서 비활성화되었거나 접수에 실패했다면 요청이 접수되었다고 볼 수 없습니다.</p>
<p>사진 객체 키 등 외부 저장소의 정리 대상은 재시도를 위해 남을 수 있습니다. 일부 신규 R2 업로드에는 재생성 방지용 빈 객체를 남기는 선택 기능이 구현되어 있으나 기본적으로 비활성화되어 있고 실제 저장소 검증이 필요합니다. 활성화되더라도 사진 내용이 없는 0바이트 객체와 임의 객체 키가 남습니다. 기존 업로드나 저장 위치가 확인되지 않는 사진은 안전한 정리 조건을 검증하기 전까지 처리 중으로 유지합니다. 계정 식별자·삭제 단계·시각·정리 이력 등 접근 차단과 재시도 정보도 별도로 유지됩니다. 삭제 완료 응답이 있는 경우에도 계정 식별자와 삭제 상태는 남습니다. 현재 코드에는 이 정보의 자동 만료가 없습니다. 이 정보의 최종 보관 기한은 확정되지 않았습니다.</p>
<p>정리 작업 코드와 일정 설정이 있어도 실제 배포·실행·완료를 입증하지는 않습니다. 즉시 삭제·특정 완료 기한·제공자 로그와 백업을 포함한 모든 사본의 삭제를 보장하지 않습니다. 처리 중이거나 실패한 경우 앱에서 가능한 재시도를 이용하고, 로그인이 안 되거나 상태가 계속되면 문의해 주세요.</p>
<h2>로그인할 수 없나요?</h2><p>아래 문의 이메일로 계정 삭제를 요청해 주세요. 요청할 조치와 로그인 불가 상황을 최소한으로 설명해 주세요. 이메일 발신 주소만으로 계정 소유권을 확정하지 않으며, 안전한 확인 절차 후 처리해야 합니다. 비밀번호, 인증 코드, 인증 토큰, API 키 또는 사진을 이메일에 보내지 마세요. 이메일 요청만으로 자동 접수·삭제되는 것은 아닙니다.</p>
<p><a href="/privacy#retention">보관·삭제의 한계</a> · <a href="/support">로그인 및 개인정보 문의</a></p>
"""),
}


def policy_metadata() -> tuple[str, str]:
    # Read only public document settings; never interpolate arbitrary environment values.
    effective_date = os.environ.get("PUBLIC_POLICY_EFFECTIVE_DATE", DEFAULT_POLICY_EFFECTIVE_DATE)
    try:
        if date.fromisoformat(effective_date).isoformat() != effective_date:
            effective_date = DEFAULT_POLICY_EFFECTIVE_DATE
    except ValueError:
        effective_date = DEFAULT_POLICY_EFFECTIVE_DATE
    version = os.environ.get("PUBLIC_POLICY_VERSION", DEFAULT_POLICY_VERSION)
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\.[0-9]{1,4}", version) is None:
        version = DEFAULT_POLICY_VERSION
    return effective_date, version


def render_page(slug: str) -> HTMLResponse:
    title, body = PAGES[slug]
    effective_date, version = policy_metadata()
    title = escape(title)
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | Trust First Nutrition</title>
<style>body{{margin:0;background:#fdf9f2;color:#232722;font-family:system-ui,sans-serif;line-height:1.75}}main{{max-width:720px;margin:auto;padding:40px 22px 64px}}a{{color:#2f6842}}h1{{font-size:28px;line-height:1.35}}h2{{font-size:19px;margin-top:30px}}nav,footer,.metadata{{font-size:14px}}footer{{border-top:1px solid #d9e1d6;margin-top:36px;padding-top:20px}}li{{margin:10px 0}}dt{{font-weight:700;margin-top:18px}}dd{{margin:6px 0 18px}}p,a,li,dd,dt{{overflow-wrap:anywhere}}.notice{{border-left:3px solid #2f6842;padding-left:16px}}a:focus-visible{{outline:3px solid #2f6842;outline-offset:3px}}.skip{{position:absolute;left:12px;top:12px;transform:translateY(-200%);background:#fdf9f2;padding:8px}}.skip:focus{{transform:none}}@media(max-width:480px){{main{{padding-top:32px}}h1{{font-size:26px}}}}</style>
</head><body><a class="skip" href="#content">본문으로 이동</a><main id="content"><nav aria-label="홈"><a href="/">Trust First Nutrition</a></nav><h1>{title}</h1>
<p class="metadata">시행일(문서 기준): <time datetime="{effective_date}">{effective_date}</time><br>정책 문서 버전: {escape(version)}</p>
<aside class="notice" aria-label="문서의 확인 범위"><p>이 안내는 코드와 설정 예시를 기준으로 작성한 기술 문서입니다. 실제 운영 설정·제공자 계약·삭제 작업의 실행은 별도 확인이 필요합니다. 최종 법률 검토나 준법 확인을 마쳤다는 뜻이 아닙니다.</p></aside>{body}
<footer><p>운영자: {escape(OPERATOR)}<br>문의: <a href="mailto:{escape(SUPPORT_EMAIL, quote=True)}">{escape(SUPPORT_EMAIL)}</a></p>
<nav aria-label="관련 문서"><a href="/privacy">개인정보</a> · <a href="/terms">이용약관</a> · <a href="/support">문의</a> · <a href="/account-deletion">계정 삭제</a></nav></footer></main></body></html>"""
    return HTMLResponse(html, headers={
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    })


@router.get("/privacy", response_class=HTMLResponse)
def privacy():
    return render_page("privacy")


@router.get("/terms", response_class=HTMLResponse)
def terms():
    return render_page("terms")


@router.get("/support", response_class=HTMLResponse)
def support():
    return render_page("support")


@router.get("/account-deletion", response_class=HTMLResponse)
def account_deletion():
    return render_page("account-deletion")
