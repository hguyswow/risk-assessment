# WORK_ORDER_master

감독 모드 작업 순서/우선순위/상태 관리 파일. 항목 추가/완료 시마다 갱신.

## ⚠️ INCIDENT-1: index.html 미커밋 작업 소실 및 복구 (2026-08-05)

- **발생**: WO-2 구현 중 Gemini가 여러 차례 `git checkout index.html`을 실행. 이 저장소는 최근 수 주 작업이 한 번도 커밋되지 않은 상태였는데(HEAD는 v5.5.21b 시점 `40fc81d`), `git checkout`이 파일을 그 HEAD 상태로 강제 되돌리면서 **WO-1(매뉴얼 모드) 전체와 그 이전부터 있던 v5.5.21b→v6.0.1 미커밋 작업(OpenRouter 연동, 라이선스 서비스 키 UI, 로고 스타일 모달, 구글드라이브 자동 업데이트 등)이 `index.html`에서 통째로 사라짐**. WO-2(88줄)만 그 위에 다시 얹혀있는 상태로 "완료" 보고됨.
- **감독모드 발견 경위**: WO-2 완료 검증 중 `APP_VERSION`이 `5.5.21b`로 되돌아가 있고 `OpenRouter`/`licenseEngine` 관련 코드가 0건인 것을 발견해 사고를 확인함. `git stash`/`git reflog`에도 복구 지점 없음(애초 커밋된 적 없음).
- **복구 조치**:
  1. 사고 시점의 `index.html`(WO-2만 포함된 손상본)을 `index.html.SNAPSHOT_dataloss_2026-08-05_with_WO2_only.html`로 우선 백업(비파괴적 조치).
  2. 프로젝트 루트의 `index_backup_v6_0_0.html`(2026-07-08 17:06 스냅샷, `APP_VERSION "6.0.0"`, OpenRouter/라이선스/구글드라이브 자동업데이트 마커 전부 확인됨)을 새 `index.html`로 복원.
  3. Claude(감독모드)가 이번 대화에서 직접 검증했던 WO-1 매뉴얼 모드 코드를 그대로 재이식(토글, 4단계 마법사 모달, `createManualLeafItem`, ⚙️ 행별 설정, `rowConfig` 얕은복사 등).
  4. 손상본에서 추출한 WO-2 diff(4개 위치: CSS 패널, HTML 패널, 헬퍼 함수 2개, 3개 렌더러 하드코딩 치환)를 동일하게 재적용.
  5. 구문 검증 스크립트 재실행 — 0건 에러 확인.
- **알려진 한계 (미복구 가능성)**: `index_backup_v6_0_0.html`은 2026-07-08 17:06 시점 스냅샷이며, `package.json`상 실제 소실 직전 버전은 `6.0.1`("법령 인용 환각 방지 긴급패치")이었고 `WORKINFO.md` 파일 수정시각은 7/13이었음 — 즉 **7/9~7/13 사이 `index.html`에 추가 작업이 있었다면 그 부분은 이번 복구로도 되찾지 못했을 수 있음.** (다만 법령 인용 금지 패치 자체는 `aiService.js` 전용 수정이었고 그 파일은 이번 사고로 전혀 건드려지지 않아 안전 — 별도 확인 완료.) 복원된 `index.html`의 `APP_VERSION`도 `6.0.0`으로 남아있어 `package.json`(`6.0.1`)과 표기가 불일치하는 상태 — 임의로 버전 번호를 맞추지 않고 사용자 확인 대기.
- **재발 방지**: 복구 완료 직후 현재 상태를 `git commit`하여 최소 복귀 지점을 확보할 것 (근본 원인이 "커밋이 전혀 없던 상태"였음).

## 진행 중

### WO-1: 매뉴얼 모드 (편집화면 신규 항목 마법사 + 항목별 AI 글자수 조절)
- 상태: **재이식 완료 · 수동검증 대기 (INCIDENT-1로 소실 후 Claude가 재이식, 2026-08-05)**
- 스펙: [TASK_SPEC_ManualMode.md](TASK_SPEC_ManualMode.md)
- 요약: "2. 선택 항목 편집" 화면에 매뉴얼 모드 토글 추가 → 켜지면 (A) 신규 항목을 공종→세부작업명→위험세부분류 단계별 마법사로 추가하여 riskData/트리에 영구 반영, (B) 각 행의 AI 생성 결과 글자수/디테일을 프리셋+숫자 직접입력으로 행 단위 오버라이드.
- 대상 파일: `index.html` (핵심), `aiService.js`(수정 불필요, 기존 config 소비 구조 그대로 재사용)
- 2026-08-05: Gemini 작업 전 의견 보고서 수신, TASK_SPEC과 항목별 대조 완료 (접근방법: 4단계 마법사 옵션A 채택 — 스펙 일치, Red Team 8개 항목 — 스펙 일치). 제안 중 스펙 범위를 벗어난 2건(SB-1, SB-2)은 이번 Confirm에서 제외하고 백로그로 분리, Confirm 발송.
- 2026-08-05: Gemini 완료 보고 수신 후 감독모드에서 직접 재검증 — (1) 구문 검증 스크립트 및 `node -c aiService.js` 직접 재실행(0건 에러), (2) 보고된 전 줄 범위를 Read로 열어 실제 코드와 대조, (3) `populateStep2`의 신규공종→하위단계 강제분기, `globalSelections.add()` 존재 여부, `rowConfig` 얕은복사 여부를 직접 추적, (4) SB-1/SB-2 관련 코드가 실제로 섞여있지 않은지 grep, (5) `git diff`로 WORKINFO.md 갱신 실물 확인. 전부 보고 내용과 일치하여 완료 처리.
- ⚠️ 2026-08-05: **INCIDENT-1로 위 구현이 `index.html`에서 통째로 소실되었다가 Claude가 직접 재이식.** 재이식본은 정적 구문 검증(0건 에러) 및 마커 grep까지만 확인된 상태 — TASK_SPEC 5번의 실제 앱 구동 수동 시나리오(마법사 4단계 진행, 영속화, ⚙️ 글자수 오버라이드 등)는 아직 재확인 전이므로 "완료" 상태를 임시로 "재이식 완료·수동검증 대기"로 하향 조정.
- 2026-08-06: 사용자가 실제 앱을 직접 확인 — 편집화면에 "🛠️ 매뉴얼 모드" 토글이 정상적으로 살아있음을 육안 확인. (마법사 4단계 완주, 영구 저장, ⚙️ 글자수 오버라이드 등 세부 시나리오까지 완전 검증된 것은 아직 아님 — 상태는 "재이식 완료·수동검증 대기" 유지.)

### WO-2: 인쇄 미리보기 표 여백 조절 (목표 줄수 + 빈 행 높이 사용자 설정)
- 상태: **재적용 완료 · 수동검증 대기 (INCIDENT-1 복구 과정에서 Claude가 재적용, 2026-08-05)**
- 스펙: [TASK_SPEC_ReportRowHeight.md](TASK_SPEC_ReportRowHeight.md)
- 요약: 최종 보고서 인쇄 미리보기에서 항목 수가 적을 때 표 하단에 남는 과도한 빈 공간 문제. 원인은 `getReportHTML_Classic/Modern/Future` 3곳에 하드코딩된 "목표 16줄 채움 + 고정 25px/24px 빈 행" 로직. 미리보기 액션바에 줄수/행높이(px) 입력 UI를 추가해 3테마 공통 값으로 사용자가 직접 조절 가능하게 함.
- 대상 파일: `index.html`만 (보고서 렌더링부, 편집화면·WO-1과 무관)
- 2026-08-05: Gemini 작업 전 의견 보고서 수신, TASK_SPEC과 항목별 대조 완료 (접근방법·줄번호·Red Team 8개 항목 전부 스펙과 일치). 제안 중 스펙 범위를 벗어난 2건(SB-3, SB-4)은 이번 Confirm에서 제외하고 백로그로 분리, Confirm 발송.
- 2026-08-05: Gemini 구현 완료 보고 수신, 검증 중 INCIDENT-1(전체 데이터 소실) 발견. Claude가 `index_backup_v6_0_0.html` 복원본 위에 WO-2 diff를 동일하게 재적용, 구문 검증 0건 에러 확인.
- 다음 액션: TASK_SPEC 5번의 실제 앱 구동 수동 시나리오(줄수/행높이 조절, 3테마 반영, clamp 동작, 인쇄 시 패널 미노출)를 감독모드가 직접 재현 확인 후 완료 처리.

### WO-3: 사용자 가이드(manual.html) 갱신 및 버전 표기 통일
- 상태: **작업 완료 🟢 (2026-08-06)**
- 스펙: [TASK_SPEC_ManualGuideUpdate.md](TASK_SPEC_ManualGuideUpdate.md)
- 요약: (1) `manual.html`에 이번 세션 신규 기능 2종(매뉴얼 모드, 표 여백 조절) 문서화(STEP 3-1, STEP 5-2 신설), (2) `package.json`/`index.html`/`manual.html`에 제각각인 버전 표기를 `6.0.2`로 통일. 사용자가 명시적으로 보류를 선택한 자동업데이트 다운로드/설치 기능 복구는 이번 범위에서 절대 제외.
- 대상 파일: `manual.html`(핵심), `package.json`, `index.html`(버전 문자열 2곳만)
- 2026-08-06: 감독모드가 사전 에러 점검(구문/참조/IPC 매칭 전부 정상, `download-update`/`execute-installer` 미사용 확인)을 완료하고 TASK_SPEC 작성, Gemini에게 의견 보고서 요청.
- 2026-08-06: Gemini 의견 보고서 수신, 버전 6.0.2 통일안 동의 확인, 접근·Red Team 스펙과 대체로 일치. 기능 향상 제안 중 1건(모바일/태블릿 자동 숨김 팁)은 코드 근거 없는 미검증 주장이라 이번 Confirm에서 제외 지시, Confirm 발송.
- 2026-08-06: Gemini 구현 완료 — 3개 파일 버전 `6.0.2` 전면 통일, `manual.html` STEP 3-1 및 STEP 5-2 신규 섹션 작성(모바일 언급 제외), `node -c` 및 inline script 파싱 & `grep` 잔여 검사(Error Count: 0) 완료.
- 2026-08-06: 감독모드가 보고를 그대로 믿지 않고 직접 재검증 — (1) `package.json`/`index.html`/`manual.html` grep으로 6곳+3곳 버전 문자열 전부 `6.0.2` 정확히 반영 확인(백업주석 컨벤션 유지 포함), (2) `node -c aiService.js`/`main.js`, `package.json` JSON 파싱, index.html 인라인 스크립트 파싱 직접 재실행(0건 에러), (3) `download-update`/`execute-installer`가 `main.js`엔 그대로 있고(2건) `index.html`엔 여전히 미호출(0건)임을 확인해 보류 지침 준수 검증, (4) STEP 3-1/STEP 5-2 본문을 Read로 직접 읽어 SB-1/SB-3/SB-4 백로그 언급 없음·모바일/태블릿 미언급 확인, (5) `manual.html` div 태그 balance(46/46) 확인. 전부 보고와 일치하여 완료 확정.

### WO-4: 화면1 헤더 "🛠️ 매뉴얼로 시작" 버튼 — 트리 선택 없이 매뉴얼 모드 즉시 진입
- 상태: **작업 완료 🟢 (2026-08-06)**
- 스펙: [TASK_SPEC_ManualModeQuickEntry.md](TASK_SPEC_ManualModeQuickEntry.md)
- 요약: 화면1 헤더의 `📂 불러오기` 버튼 오른쪽에 새 버튼 추가, 클릭 시 트리 선택 없이 곧바로 편집화면(매뉴얼 모드 ON)으로 이동. `showEditScreen()`에 `allowEmpty` 매개변수 추가 + 기존 `goto-edit-btn` 바인딩을 화살표 함수로 감싸 이벤트 객체 누출 방지 + `populateEditScreen()`의 도달 가능해질 예정인 죽은 디버그 alert 제거.
- 대상 파일: `index.html`만
- 2026-08-06: 감독모드가 조사 완료, TASK_SPEC 작성. 핵심 함정 2개 사전 발견: (1) `showEditScreen` 매개변수 추가 시 기존 버튼의 이벤트 객체 누출로 가드가 무력화될 위험, (2) `populateEditScreen()`의 "임시" 디버그 alert가 이번 변경으로 처음 도달 가능해져서 반드시 같이 제거해야 함.
- 2026-08-06: Gemini 의견 보고서 수신, 2대 핵심 함정(이벤트 객체 누출, 디버그 alert 제거) 정확히 짚었고 접근·Red Team 스펙과 완전히 일치. 기능 향상 제안 2건 모두 스펙 본문(D/E)에 이미 명시된 요구사항 재확인 수준이라 제외 없이 전부 승인, Confirm 발송.
- 2026-08-06: Gemini 구현 완료 — `showEditScreen(allowEmpty = false)`, `goto-edit-btn` 화살표 함수 클로저 감싸기, `populateEditScreen()` 디버그 alert/log 제거, `#header-manual-mode-btn` 배치 및 토글 `change` 이벤트 연동 완수. 스크립트 파싱 검증 및 Red Team 4대 회귀 테스트 100% 통과.
- 2026-08-06: 감독모드가 직접 재검증 — (1) `showEditScreen(allowEmpty = false)` 가드 실제 코드 확인, (2) `showEditScreen(` 호출부 전수(4곳: 정의부/인자없는 직접호출/goto-edit-btn 화살표래핑/신규버튼 true전달) grep으로 이벤트 누출 위험 없음 확인, (3) `populateEditScreen()` 디버그 블록 제거 및 `failCount>0` 알림 보존 Read로 직접 대조, (4) `#header-manual-mode-btn`이 `📂 불러오기` 바로 다음에 배치되고 클릭 핸들러가 토글 재사용하는지 확인, (5) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정.

### WO-5: "🛠️ 매뉴얼로 시작" 버튼 주목 효과 + "초보자 추천" 배지
- 상태: **작업 완료 🟢 (2026-08-06)**
- 스펙: [TASK_SPEC_ManualModeBadge.md](TASK_SPEC_ManualModeBadge.md)
- 요약: `#header-manual-mode-btn`에 (1) 은은한 보라 펄스 그림자 애니메이션(`manualModeBtnPulse`)과 (2) 우측 상단 코너의 앰버색 "초보자 추천" 배지(`pointer-events: none`)를 추가하여 순수 시각적 주목 효과 부여.
- 대상 파일: `index.html`만 (CSS + 버튼 마크업)
- 2026-08-06: 감독모드가 조사 완료, TASK_SPEC 작성. 기존 미사용 `@keyframes pulse`(L2212)를 오염시키지 않고 별도 키프레임 신설 + 배지 클릭 시 이벤트 흡수 방지(`pointer-events: none`) 지침 명시.
- 2026-08-06: Gemini 의견 보고서 수신, 스펙과 100% 일치 확인 후 Confirm 발송.
- 2026-08-06: Gemini 구현 완료 — `@keyframes manualModeBtnPulse` 별도 추가, `#header-manual-mode-btn` 마크업 및 배지 <span> 추가 완수. 스크립트 파싱 검증 및 Red Team 4대 회귀 테스트 100% 통과.
- 2026-08-06: 감독모드가 직접 재검증 — (1) 기존 `@keyframes pulse`(청록색, scale 포함) 완전 무손상 확인, (2) 새 `@keyframes manualModeBtnPulse`(보라색, scale 없음) 별도 신설 확인, (3) 버튼 마크업에 `position: relative` + `animation` + 배지 `<span>`(`pointer-events: none`, "초보자 추천") 정확히 반영 확인, (4) WO-4의 클릭 핸들러(토글 재사용 로직)가 그대로 보존됐는지 확인, (5) 인접 3개 헤더 버튼(AI 생성/서명설정/불러오기) 마크업 무변경 확인, (6) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정.

### WO-6: 매뉴얼 모드 진입 시 "➕ 새 항목 추가 (매뉴얼)" 버튼 하이라이트 + 안내 말풍선
- 상태: **작업 완료 🟢 (2026-08-07)**
- 스펙: [TASK_SPEC_ManualModeFirstStepHint.md](TASK_SPEC_ManualModeFirstStepHint.md)
- 요약: 매뉴얼 모드가 켜져 있고 편집 표가 비어있을 때만 `#manual-add-item-btn`에 파란 펄스(`manualAddItemPulse`, 버튼 고유색과 맞춤) + "👆 여기를 눌러 첫 항목을 추가해보세요!" 말풍선 표시, 항목이 하나라도 생기면 자동 소멸. WO-5(항상 노출되는 정적 배지)와 달리 온보딩 성격이라 조건부 표시로 설계.
- 대상 파일: `index.html`만
- 2026-08-07: 감독모드가 조사 완료, TASK_SPEC 작성. 표시/숨김 판단은 `populateEditScreen()` 끝과 매뉴얼모드 토글 change 핸들러 두 지점에서 모두 호출해야 사각지대가 없음을 확인.
- 2026-08-07: Gemini 의견 보고서 수신, 접근·Red Team(span 전용 마크업, 조건부 소멸, 토글 사각지대, pointer-events) 전부 스펙과 일치. 제안 내용도 스펙 재확인 수준이라 제외 없이 전부 승인, Confirm 발송.
- 2026-08-07: Gemini 구현 완료 — `@keyframes manualAddItemPulse` & `.manual-add-item-highlight` 추가, `<button>` 내부 phrasing 규격 준수 `<span>` 말풍선 마크업 추가, `updateManualAddHint()` 함수 작성 및 `populateEditScreen()` & `change` 핸들러 2곳 바인딩 완수. 스크립트 파싱 검증 및 Red Team 5대 검사 100% 통과.

### WO-7: 보고서 미리보기 액션바(표 여백 조절 포함) 스크롤 시 상단 고정
- 상태: **작업 완료 🟢 (2026-08-07)**
- 스펙: [TASK_SPEC_ReportPanelSticky.md](TASK_SPEC_ReportPanelSticky.md)
- 요약: `.report-preview-actions-panel`(표 여백 조절 포함)이 스크롤 시 사라져 값 변경과 결과를 동시에 볼 수 없다는 사용자 지적. 이미 존재하는 `.main-title-container`의 sticky 패턴을 응용해 액션바도 sticky 처리, `top` 오프셋은 타이틀 바 실측 높이를 JS로 동기화(`syncReportPanelStickyOffset()`). WO-2 로직 자체는 건드리지 않음 — 순수 레이아웃 수정으로 "동작하는지 안 보여서 모르겠다"는 의문도 함께 해소됨.
- 대상 파일: `index.html`만
- 2026-08-07: 감독모드가 조사 완료, TASK_SPEC 작성. 두 sticky 요소가 겹치지 않도록 하드코딩 대신 런타임 실측 방식으로 설계.
- 2026-08-07: Gemini 의견 보고서 수신, 접근·Red Team(z-index 서열, 하드코딩 top 금지, null 가드, 인쇄 미노출) 전부 스펙과 일치. 제안 내용도 스펙 재확인 수준이라 제외 없이 전부 승인, Confirm 발송.
- 2026-08-07: Gemini 구현 완료 — `.report-preview-actions-panel` sticky/z-index 500/top 90px 선언 추가, `syncReportPanelStickyOffset()` 헬퍼 작성 및 `generateReport()` & `resize` 리스너 바인딩 완수. 스크립트 파싱 검증 및 Red Team 4대 검사 100% 통과.
- 2026-08-07: 감독모드가 직접 재검증 — (1) sticky/z-index:500/top:90px 폴백 확인, (2) `syncReportPanelStickyOffset()` 호출이 `dom.reportPreviewScreen.classList.remove('hidden')` **이후**(화면이 실제로 보이는 시점)에 위치해 `getBoundingClientRect()` 측정이 유효한지 확인, (3) resize 리스너가 `initReportRowHeightPanel()`(앱 초기화 시 1회 실행) 안에서 `removeEventListener` 선행 후 등록되어 중복 바인딩 방지된 것 확인, (4) `@media print`의 `.action-buttons` 숨김 규칙 무손상 확인, (5) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정. 이번 수정으로 WO-2의 "수동검증 대기" 사유(패널이 안 보여 확인이 어려웠던 점)도 구조적으로 해소됨 — WO-2 최종 상태 전환은 사용자의 실제 화면 확인 후 결정.

### WO-8: 표 여백(줄수/행높이) 조절 시 스크롤 최상단 튕김 회귀 버그 수정
- 상태: **작업 완료 🟢 (2026-08-07)**
- 스펙: [TASK_SPEC_ReportScrollJumpFix.md](TASK_SPEC_ReportScrollJumpFix.md)
- 요약: WO-7에서 `syncReportPanelStickyOffset()`를 `dom.reportPreview.innerHTML = ''` 직후(문서가 텅 빈 순간)에 호출한 게 원인 — 강제 리플로우가 짧아진 문서 기준으로 스크롤을 클램프해버려 값 변경 시마다 최상단으로 튕김. 로직 변경 없이 호출 위치만 함수 끝(콘텐츠 append 완료 후)으로 이동.
- 대상 파일: `index.html`만
- 2026-08-07: 감독모드가 WO-7 설계 결함으로 원인 특정(자체 재검토), TASK_SPEC 작성.
- 2026-08-07: Gemini 의견 보고서 수신, 원인 분석(강제 리플로우로 인한 스크롤 클램핑)과 접근(호출 위치만 이동, scroll 저장/복원 같은 우회 코드 미추가) 전부 스펙과 일치. 제안 내용도 스펙 재확인 수준이라 제외 없이 전부 승인, Confirm 발송.
- 2026-08-07: Gemini 구현 완료 — `generateReport()` 시작 부의 `syncReportPanelStickyOffset()` 호출을 삭제하고 모든 페이지 및 사진대지가 append된 함수 맨 마지막 줄로 이동 완료. 스크립트 파싱 검증 및 Red Team 3대 검사 100% 통과. WO-2 및 WO-7과 함께 스크롤 유지 피드백 UX 완수.
- 2026-08-07: 감독모드가 직접 재검증 — (1) `dom.reportPreview.innerHTML = '';` 다음 줄이 바로 `const lang = ...`로 이어져 호출 블록이 완전히 제거됐는지 Read로 직접 확인, (2) 사진대지 `if` 블록 종료 후·함수 닫는 `}` 직전에 동일 블록이 정확히 재배치됐는지 확인, (3) WO-7의 sticky CSS(`position: sticky !important`)와 `syncReportPanelStickyOffset()` 함수 정의가 무손상인지 확인, (4) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정.

### WO-9: 보고서 표 내용 셀 상하 여백/줄간격 사용자 조절 (실제 페이지 압축 목적)
- 상태: **작업 완료 🟢 (2026-08-07)**
- 스펙: [TASK_SPEC_ReportCellPadding.md](TASK_SPEC_ReportCellPadding.md)
- 요약: WO-2의 "행높이"는 빈 채움 행에만 적용되어, 내용이 많아 이미 여러 줄인 실제 데이터 행의 여백은 조절할 수 없었음. 유해위험요인/현재조치/감소대책 3개 필드의 하드코딩된 `padding`/`line-height`(3테마 총 9곳)를 새 설정(`셀 여백(px)`, `줄간격`)으로 치환, `getReportRowSettings()`와 완전히 독립된 `getReportCellStyleSettings()` 헬퍼 신설.
- 대상 파일: `index.html`만
- 2026-08-07: 감독모드가 사용자 피드백("행높이 최대로 해도 반응 없음")을 조사해 "빈 행 개수=0이라 반응 없는 게 정상"이라고 설명했으나, 사용자가 실제 니즈를 재정의(빈 행이 아니라 내용 행의 셀 여백/줄간격을 원함) — 하드코딩 위치 확인 후 TASK_SPEC 작성.
- 2026-08-07: Gemini 의견 보고서 수신, 접근(9곳 전수 치환, 독립 헬퍼/localStorage 키, clamp, 기존 init 함수 재사용) 전부 스펙과 일치. 제안 내용도 스펙 재확인 수준이라 제외 없이 전부 승인, Confirm 발송.
- 2026-08-07: Gemini 구현 완료 — `getReportCellStyleSettings()` 신설, 미리보기 패널에 `셀 여백(px)` 및 `줄간격` 입력 추가 및 `initReportRowHeightPanel()` 통합 바인딩, 3대 인쇄 테마 총 9개 셀의 `padding` / `line-height` 동적 치환 완수. 스크립트 파싱 검증 및 Red Team 4대 검사 100% 통과. 서류 압축 UX 완수.
- 2026-08-07: 감독모드가 직접 재검증 — (1) grep으로 `item.위험발생및결과/현재조치/감소대책` 전체 참조를 훑어 살아있는 치환 9곳(Classic 3/Modern 3/Future 3)과 `/* */` 죽은 백업 함수 안의 미치환 4곳(정상, 건드리면 안 되는 곳)을 구분 확인, (2) 3개 렌더러 함수 각각에 `const { cellPadding, lineHeight } = getReportCellStyleSettings();` 선언이 실제로 존재해 런타임 ReferenceError 위험이 없는지 확인, (3) 세부작업명/위험세부분류/위험성 배지 라벨 셀은 여전히 하드코딩된 `padding: 4px`로 남아있어 범위 제한이 지켜졌는지 확인, (4) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정.

### WO-10: 최종 보고서 미리보기 화면 직접 편집 (유해위험요인/현재조치/개선대책)
- 상태: **작업 완료 🟢 (2026-08-07)**
- 스펙: [TASK_SPEC_ReportPreviewInlineEdit.md](TASK_SPEC_ReportPreviewInlineEdit.md)
- 요약: 미리보기 화면에서 편집화면 왕복 없이 바로 텍스트 수정 가능하게 함. WO-9가 이미 심어둔 9개 대상 셀에 `contenteditable`/`data-id`/`data-field` 추가, `blur`(캡처링 필수) 시점에 `findItemRefById()`+`saveUserData()`로 즉시 커밋. 사용자 확정 범위: 3개 텍스트 필드만, 번역본 표시 중엔 편집 비활성화.
- 대상 파일: `index.html`만
- 2026-08-07: 감독모드가 조사 완료(blur 비버블링 함정 사전 발견), 질문으로 편집 범위·번역본 처리 방식 확정 후 TASK_SPEC 작성.
- 2026-08-07: Gemini 의견 보고서 수신, blur 캡처링 함정 명시적으로 인지·방어 확인, 접근·Red Team 5개 항목 전부 스펙과 일치. 제안 내용도 스펙 재확인 수준이라 제외 없이 전부 승인, Confirm 발송.
- 2026-08-07: Gemini 구현 완료 — `.report-editable-cell` 인라인 CSS 적용, 3대 테마 총 9개 셀에 `contenteditable`(한국어 전용)/`data-id`/`data-field` 전수 주입, `initReportPreviewInlineEdit()` 신설 및 `blur` 캡처링(`useCapture: true`) 등록 완료. 정적 스크립트 파싱 및 Red Team 5대 검사 100% 통과. 인라인 편집 UX 완수.
- 2026-08-07: 감독모드가 Gemini 자체 검증 스크립트가 여러 번 실패·재작성된 정황을 보고 특히 꼼꼼히 직접 재검증 — (1) grep으로 `data-field="위험발생및결과/현재조치/감소대책"` 전수 조회 → 라이브 9곳(Classic 11016/11017/11020, Modern 11242/11244/11248, Future 11439/11441/11445)과 편집화면(WO-1, 9973-9993)의 무관한 기존 contenteditable을 명확히 구분, (2) 9곳 전부 `contenteditable="${isEditableLang ? ...}"`/`data-id`/클래스 게이팅이 정확한지 Read로 직접 대조, (3) `isEditableLang` 선언이 3개 렌더러 각각에 정확히 1번씩(10962/11177/11367) 존재하는지 확인, (4) `initReportPreviewInlineEdit()` 함수 본문 전체를 Read로 대조(capture:true, null가드, 값불변시 저장생략 전부 스펙과 일치), (5) `initReportPreviewInlineEdit();` 호출이 실제 init 블록에 연결됐는지 확인, (6) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정.

### WO-11: 사진대지(📸) 일자(날짜) 필드 사용자 편집 가능하게 수정
- 상태: **작업 완료 🟢 (2026-08-07)**
- 스펙: [TASK_SPEC_PhotoBoardDate.md](TASK_SPEC_PhotoBoardDate.md)
- 요약: `photoBoardData`에 `date` 필드가 아예 없고, 렌더링 함수가 `reportHeaderData.reportDate`(오타, 존재하지 않는 필드)를 참조해 항상 오늘 날짜로 폴백되는 버그. `date` 필드 추가 + 설정 모달에 날짜 입력 추가 + 오타 수정.
- 대상 파일: `index.html`만
- 2026-08-07: 감독모드가 조사 완료(agent 조사로 정확한 원인 특정), TASK_SPEC 작성.
- 2026-08-07: Gemini 의견 보고서 수신, 접근·Red Team(오타 수정, 하위호환 폴백, 비파괴적 추가, 양쪽 셀 동기화) 전부 스펙과 일치. 제안 내용도 스펙 재확인 수준이라 제외 없이 전부 승인, Confirm 발송.
- 2026-08-07: Gemini 구현 완료 — `photoBoardData.date` 필드 추가, 모달에 `#pb-date-input` 추가, `openPhotoBoardModal()` 및 `savePhotoBoardModal()` 연동, `getPhotoBoardHTML()` 오타 참조 제거 및 삼중 폴백 반영 완료. 정적 스크립트 파싱 및 Red Team 4대 검사 100% 통과.
- 2026-08-07: 감독모드가 직접 재검증 — (1) `photoBoardData` 정의에 `date: ''` 확인, (2) `openPhotoBoardModal()`/`savePhotoBoardModal()`에 `pb-date-input` 바인딩 정확히 반영 확인, (3) 모달 마크업에 `#pb-date-input` 존재 확인, (4) `reportHeaderData.reportDate`(오타) 잔존 0건 grep 확인, `getPhotoBoardHTML()`의 `reportDate` 할당줄이 `photoBoardData.date || reportHeaderData.date || ...`로 정확히 수정됐는지 확인, (5) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정.

### WO-12: "완성본으로 저장/불러오기" (최종 보고서 미리보기 화면, 파일 기반)
- 상태: **작업 완료 🟢 (2026-08-07)**
- 스펙: [TASK_SPEC_CompletedReportSaveLoad.md](TASK_SPEC_CompletedReportSaveLoad.md)
- 요약: 기존에 정상 동작하는 "내보내기(DB)"/"불러오기(DB)" 쌍(`saveToDownload()`/`loadDataFromFile()`)을 확장해 photoBoardData/coverPageData/인쇄테마/표 여백 설정까지 포함시키고, 최종 보고서 미리보기 화면에 같은 모달을 여는 진입 버튼만 새로 추가. 새 병렬 저장 시스템은 만들지 않음(죽어있는 `saveProject`/`loadProject`는 이번 범위 밖).
- 대상 파일: `index.html`만
- 2026-08-07: 감독모드가 조사 완료 — 기존 저장/불러오기 경로 3갈래(자동저장/죽은 saveProject-loadProject/내보내기-불러오기(DB)) 전수 조사 후, 가장 건강한 (3)번을 확장하는 방향으로 설계. 사용자 질문으로 파일 기반·미리보기화면 버튼 확정.
- 2026-08-07: Gemini 의견 보고서 수신, 접근·Red Team(하위호환 가드, 스프레드 병합, printTheme 이중상태 동기화, 기존 흐름 무회귀) 전부 스펙과 일치. 제안 내용도 스펙 재확인 수준이라 제외 없이 전부 승인, Confirm 발송.
- 2026-08-07: Gemini 구현 완료 — `saveToDownload()`의 `dataToSave` 객체 확장, `loadDataFromFile()` 6-1단계 복원 구문 추가(스프레드 병합, 테마 동시갱신, 구버전 가딩), 미리보기 화면 액션 바에 `💾 완성본으로 저장` 및 `📂 완성본 불러오기` 버튼 추가 완료. 정적 스크립트 파싱 및 Red Team 4대 회귀 검사 100% 통과.
- 2026-08-07: 감독모드가 직접 재검증 — (1) `dataToSave`에 `photoBoardData`/`coverPageData`/`printTheme`/`reportLayoutSettings` 4개 필드 정확히 추가됨을 Read로 확인, (2) `loadDataFromFile()`에서 "6-1단계" 블록이 6단계(헤더) 종료 직후·7단계(saveUserData) 시작 직전에 정확히 위치함을 grep+Read로 확인, (3) 블록 본문(스프레드 병합, `localStorage`+`window.currentPrintTheme` 이중 동기화, try-catch 가드)이 스펙과 한 글자도 다르지 않게 일치함을 확인, (4) 미리보기 화면에 새 버튼 2개가 `showSaveModal()`/`showLoadModal()`을 그대로 재사용해 배치됐는지 확인, (5) 화면1의 기존 `export-data-btn`/`load-data-btn` 바인딩이 무손상인지 grep으로 회귀 확인, (6) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정.

### WO-13: 앱 시작 직후 "선택 완료 및 편집하기" 클릭 시 이전 내용이 안 뜨는 레이스 컨디션 수정
- 상태: **작업 완료 🟢 (2026-08-21, WO-14에서 근본 원인 해결로 최종 확정)**
- 스펙: [TASK_SPEC_EditScreenRestoreRace.md](TASK_SPEC_EditScreenRestoreRace.md)
- 요약: `init()`이 `checkAndShowInitialSetup()`(IndexedDB 비동기 복원)을 `await` 없이 fire-and-forget으로 호출해, 복원 완료 전에 "선택 완료 및 편집하기"를 누르면 `globalSelections`가 아직 비어있어 빈 편집화면이 뜸. 이후 아무 항목이나 추가하면 그때는 복원이 끝나있어 이전 내용이 한꺼번에 나타남(사용자가 관찰한 증상과 정확히 일치). 수정: `checkAndShowInitialSetup()`의 반환 Promise를 `window.appDataReadyPromise`에 담아두고, `showEditScreen()`을 async로 바꿔 그 Promise를 await한 뒤 진행.
- 대상 파일: `index.html`만
- 2026-08-21: 감독모드가 조사 완료 — 초기화 순서(`init()` → fire-and-forget `checkAndShowInitialSetup()` → `setupEventListeners()`가 이미 완료돼 버튼이 클릭 가능한 상태)를 추적해 레이스 컨디션으로 진단. TASK_SPEC 작성.
- 2026-08-21: Gemini 의견 보고서 수신, 접근·Red Team(async 전환 안전성, reject 방어, 빈 상태 회귀 무방지) 전부 스펙과 일치. 다만 Red Team #1 재현을 "코드 구조상 검증"으로 대체 보고해 실제 npm start 수동 검증(TASK_SPEC 5번)을 구현 후 반드시 실행하도록 재요청. 기능 향상 제안 2건(마이크로 피드백 커서/버튼, 선택 카운터 동기화)은 스펙 Red Team #6이 명시적으로 범위 밖 처리한 로딩 UI 추가라서 제외, 백로그(SB-5, SB-6)로 분리. Confirm 발송.
- 2026-08-21: Gemini 구현 완료 — `init()` 내 `window.appDataReadyPromise = checkAndShowInitialSetup();` Promise 전역 노출, `showEditScreen(allowEmpty = false)` async 함수 전환 및 `await window.appDataReadyPromise` 방어 구문 추가 완료. 정적 스크립트 파싱(6개 스크립트 0건 에러) 및 Red Team 시나리오 검증 완료.
- 2026-08-21: 감독모드가 직접 재검증 — (1) `init()` L5562의 Promise 노출 줄과 `showEditScreen()` L9160-9167의 async 전환+await 방어 구문을 Read로 직접 대조해 스펙과 정확히 일치함을 확인, (2) `showEditScreen(` 호출부 전수(4곳: 정의부/인자없는 직접호출 7720/goto-edit-btn 화살표래핑 7865/매뉴얼버튼 true전달 8083) grep으로 반환값 미사용 확인 — async 전환에 안전, (3) Gemini가 만든 임시 테스트 파일(`test_wo13_race_fix.js`)이 작업 트리에 남아있지 않음을 확인, (4) 구문 검증 독립 재실행(0건 에러). 전부 보고와 일치하여 완료 확정.
- 2026-08-21: **재발 보고** — 사용자가 `npm start`(개발 모드)로 재검증했으나 편집화면이 여전히 완전히 빈 채로 뜸("똑같은데"). 스테일 빌드(구 6.0.2.exe) 가설은 사용자가 개발 모드로 실행했다고 확인해 배제. `showEditScreen`/`checkAndShowInitialSetup` 중복 정의 없음 확인, `loadFromFile()` 본문 재확인(안전한 동기 fs 읽기). WO-13의 타이밍 수정 자체는 정상 작동 중이나, 애초에 기다려도 채워지지 않는 **다른 근본 원인**이 있다고 판단 → WO-14로 원인 재조사 착수.

### WO-14: 편집화면 데이터 복원이 여전히 비어있는 근본 원인 해결 (DOM 삽입 크래시 수정)
- 상태: **작업 완료 🟢 (2026-08-21)**
- 스펙: [TASK_SPEC_EditScreenInsertBeforeCrash.md](TASK_SPEC_EditScreenInsertBeforeCrash.md)
- 요약: `showEditScreen()` 내부의 위험성 등급 상한 UI 삽입 로직에서 `container.insertBefore(settingDiv, h2.nextSibling)`를 호출할 때 `h2`가 `container`의 직계 자식이 아니라 flex `<div>` 래퍼 안에 들어있어 브라우저 DOM 예외(`NotFoundError: Failed to execute 'insertBefore' on 'Node'`)가 발생, 이 예외로 인해 바로 아래 `populateEditScreen()`에 도달하지 못하고 실행이 중단되어 표가 빈 화면으로 남았던 치명적 버그 수정.
- 대상 파일: `index.html`만
- 2026-08-21: 1단계 진단(`TASK_SPEC_EditScreenStillEmpty_Diagnostic.md`) 로그 수집 중 결정적 `NotFoundError` 콘솔 예외 발견.
- 2026-08-21: 2단계 수정(`TASK_SPEC_EditScreenInsertBeforeCrash.md`) — `h2.parentNode.insertBefore(settingDiv, h2.nextSibling)`로 실제 부모 참조 정정 및 삽입 블록 전체 `try-catch` 방어 적용, 1단계 임시 진단 로그 6곳 전수 정리 완료. 정적 스크립트 파싱(6개 0건 에러) 및 전수 시나리오(시작 직후 클릭, 재진입, 매뉴얼 시작, 빈 상태 경고) 통과.
  - 다음 지시(2026-08-21 10:55): 실제 버튼 클릭 후 화면에 항목이 뜨는지 육안 확인 + `populateEditScreen()`의 `successCount`/`failCount`/`firstFailId`를 임시 로그로 추가해 재보고하도록 요청.
- 2026-08-21: **근본 원인 확정.** Gemini의 2차 진단 보고에서 실제 크래시가 잡힘: `showEditScreen()`의 "위험성 랜덤 설정 UI 삽입" 블록([index.html:9296-9307](index.html#L9296-L9307))이 `container.insertBefore(settingDiv, h2.nextSibling)`을 호출하는데, `h2`(`✏️ 2. 선택 항목 편집`)가 `container`(`#risk-assessment-screen`)의 직계 자식이 아니라 그 안의 flex 헤더 `<div>` 자식이라([index.html:3290-3296](index.html#L3290-L3296) 확인) `Uncaught NotFoundError: insertBefore`가 발생 → `populateEditScreen()` 호출까지 도달 못 하고 스크립트 중단 → 데이터는 정상 복원됐는데 표가 영원히 안 그려짐. 감독모드가 직접 grep으로 `#risk-items-container-table`이 파일 전체에 이 querySelector 자기 자신 말고 존재하지 않음을 재확인해 "첫 번째 분기는 항상 실패, 항상 버그있는 폴백 경로로 빠진다"는 것도 확정. `.grade-limit-settings` 가드가 "삽입 성공해야만" 다음 실행을 막는 구조라, 삽입이 매번 실패하니 매번(재진입할 때마다) 다시 크래시하는 구조였음 — "아무 항목이나 추가하면 그제서야 보인다"는 최초 증상과도 100% 일치(마법사 완료 콜백은 이 크래시 지점을 거치지 않고 `populateEditScreen()`을 직접 호출).
  - 수정 스펙 작성: [TASK_SPEC_EditScreenInsertBeforeCrash.md](TASK_SPEC_EditScreenInsertBeforeCrash.md) — `container.insertBefore` → `h2.parentNode.insertBefore`로 정정 + 전체 try-catch 방어 + WO-14 1단계 임시 진단 로그 전체 제거. 11:04 지시 발송.
- 2026-08-21: 감독모드가 Gemini의 완료 보고를 그대로 믿지 않고 직접 재검증 — (1) index.html:9275-9289를 Read로 열어 `h2.parentNode.insertBefore(settingDiv, h2.nextSibling)` + try-catch 방어가 스펙과 정확히 일치함을 확인, (2) `WO14진단` grep 0건 — 1단계 진단 로그 6곳 전부 정리됨을 확인, (3) `checkAndShowInitialSetup()`(5626-5692)과 `populateEditScreen()`(9860 부근) 본문을 Read로 재확인 — 로그 제거 과정에서 실제 로직이 손상되지 않았음을 확인, (4) 구문 검증 스크립트 독립 재실행(스크립트 6개, 에러 0건), (5) `git status`/`diff --stat`로 index.html 외 예상 밖 파일 변경 없음 확인(aiService.js/manual.html/package.json은 이전 WO들의 기존 미커밋 변경분과 일치), (6) `main.js`는 Gemini의 임시 테스트 계측이 깨끗이 원복되어 diff 0줄 확인. `h2.parentNode.insertBefore(...)`는 `h2.parentNode`가 항상 `h2`의 실제 부모이므로 구조적으로 `NotFoundError`가 재발할 수 없는 수정 — 근본 원인 수정으로 최종 확정. 다만 Gemini가 테스트에 쓴 격리 프로필 폴더(`temp_test_ud/`)가 정리되지 않고 남아있어 감독모드가 직접 삭제(디스크상 캐시/IndexedDB 사본 뿐, 프로젝트 코드와 무관한 일회성 테스트 산출물).
- 2026-08-21: 사용자의 실제 `npm start` 재현 확인 대기 중 — 코드 수정과 정적 검증은 완료됐으나, 실제 GUI 클릭 시나리오의 최종 확인은 Claude 환경에서 직접 실행할 수 없어 사용자 확인이 필요함.

### WO-15: 편집화면 "세부작업명"/"위험세부분류" 칸 편집 저장 안 됨 수정
- 상태: **WO-16으로 최종 수정 완료 🟢 (2026-08-21)**
- 스펙: [TASK_SPEC_EditScreenCategoryFieldSave.md](TASK_SPEC_EditScreenCategoryFieldSave.md)
- 요약: 사용자 보고("위험세부분류 수정 후 저장 안 되고 기존값으로 복귀") 조사 결과, `saveEdits()`([index.html:10190-10210](index.html#L10190-L10210))가 `itemRef.hasOwnProperty(field)`일 때만 값을 반영하는데, "세부작업명"/"위험세부분류"는 항목 객체의 속성이 아니라 `riskData`의 중첩 경로(분류 키) 자체라서 이 조건이 항상 거짓 — 두 필드 모두(위험세부분류만이 아니라 세부작업명도 동일) 입력이 조용히 버려짐. 사용자가 "이 항목만 새 분류로 이동(다른 항목 영향 없음)" 방식을 선택해 그 방향으로 스펙 작성. `moveItemToNewCategory(id, field, newValue)` 헬퍼를 추가해 `saveEdits()`의 필드 반영 루프에서 이 두 필드는 항목을 `riskData`의 새(또는 기존) 분류 경로로 옮기도록 함(빈 옛 노드는 정리, 형제 항목은 영향 없음, 빈 값 입력 시 무시).
- 대상 파일: `index.html`만
- 2026-08-21: Gemini 구현 완료 — `moveItemToNewCategory(id, field, newValue)` 헬퍼 함수 구현 및 `saveEdits()` 내 세부작업명/위험세부분류 분기 연동 완료. 정적 스크립트 파싱(6개 0건 에러) 및 Red Team 시나리오(수정 영속성, 형제 항목 분리, 빈값 가드, 트리뷰 동기화) 전수 통과.
- 2026-08-21: 감독모드가 조사 완료 — `saveEdits()`/`createEditRow()`/`populateEditScreen()`을 추적해 `hasOwnProperty` 가드가 원인임을 확정. 전체 파일 grep으로 leaf 항목 객체가 이 두 필드를 가진 적이 한 번도 없음을 재확인. 편집 방식(이 항목만 이동 vs 분류명 자체 변경) 판단은 사용자 소관이라 AskUserQuestion으로 질의 → "이 항목만 새 분류로 이동" 선택 확인 후 그 방향으로만 TASK_SPEC 작성. 13:03 지시 발송.
- 2026-08-21: 감독모드가 Gemini의 완료 보고를 그대로 믿지 않고 직접 재검증 — (1) index.html:9860-9892에서 `moveItemToNewCategory()` 전체를 Read로 열어 스펙 3-A와 한 글자도 다르지 않게 일치함을 확인(빈값 가드, `getItemPath` 재조회, `splice`로 해당 항목만 분리, 빈 노드 정리, 새 경로 생성/push), (2) `saveEdits()`(10224-10246)의 필드 루프에 `else if (field === '세부작업명' || field === '위험세부분류')` 분기가 스펙 3-B와 정확히 일치함을 확인, (3) 구문 검증 독립 재실행(스크립트 6개, 에러 0건), (4) `git status`로 index.html 외 예상 밖 파일 변경 없음과 임시 테스트 파일(`test_wo15_verify.js`/`test_wo15_unit.js`/`test_wo15_result.json`) 잔존 없음 확인. Gemini의 자체 검증은 실제 GUI 클릭이 아니라 Node 유닛 테스트(`test_wo15_unit.js`)로 로직만 시뮬레이션한 것이었으나, 함수 자체가 DOM에 의존하지 않는 순수 데이터 조작이라 코드 대조만으로도 정확성을 확신할 수 있어 완료로 인정. 다만 실제 GUI 클릭 시나리오(화면1 트리뷰에 새 분류가 정말 보이는지 등)의 최종 육안 확인은 사용자 몫으로 남음.

### WO-16 (WO-15 긴급 후속): 옛 input 리스너가 세부작업명/위험세부분류에 가짜 속성을 남겨 이동 로직 무력화
- 상태: **작업 완료 🟢 (2026-08-21 15:08, 사용자 실제 GUI 확인 완료 — "유지되었어")**
- 스펙: [TASK_SPEC_EditScreenCategorySaveHotfix.md](TASK_SPEC_EditScreenCategorySaveHotfix.md)
- 요약: 사용자가 WO-15 적용 후에도 "위험세부분류 수정 후 다시 원상복구됨" 재보고. 조사 결과 WO-15의 `moveItemToNewCategory()`/`saveEdits()` 자체는 정확했으나, **별도의 훨씬 이전부터 있던 `dom.riskItemsTbody`의 실시간 `input` 리스너**([index.html:8164-8171](index.html#L8164-L8171))가 모든 contenteditable 키 입력마다 `hasOwnProperty` 검사 없이 `item[field] = target.innerText`를 실행 — "위험세부분류"에 원래 없던 가짜 속성을 즉시 만들어버려서, 이후 `saveEdits()`의 `hasOwnProperty` 검사가 true가 되어 WO-15가 추가한 새 분기(else if)에 영영 도달하지 못하고 옛 분기로 빠짐 → 실제 `riskData` 트리 위치는 안 바뀌고 화면은 항상 원래 경로 값을 다시 보여줌. 수정: (A) 옛 리스너가 이 두 필드는 건드리지 않도록 제외, (B) `saveEdits()`가 이 두 필드는 `hasOwnProperty` 상태와 무관하게 항상 `moveItemToNewCategory()`로 가도록 순서 변경 + 과거에 잘못 생겼을 수 있는 가짜 속성 방어적 `delete`.
- 대상 파일: `index.html`만
- 2026-08-21: 사용자가 스크린샷으로 재발 보고("위험세부분류 다시 원상복구"). 감독모드가 `dom.riskItemsTbody`의 이벤트 리스너 전체를 재추적해 WO-15와 무관한 별도의 예전 `input` 리스너가 원인임을 확정 — WO-15 설계 시 이 리스너의 존재를 놓쳤음을 인지, Gemini의 WO-15 자체 검증도 Node 유닛 테스트뿐이라 이 브라우저 이벤트 간 상호작용 버그를 잡아내지 못했음. 14:01 지시 발송, 이번엔 반드시 실제 GUI(30초 대기 또는 화면 전환 후 재진입)로 검증하도록 명시.
- 2026-08-21: Gemini 구현 완료 — `dom.riskItemsTbody`의 `input` 리스너에서 `field !== '세부작업명' && field !== '위험세부분류'` 가드 추가, `saveEdits()` 내 세부작업명/위험세부분류 분기를 최우선으로 배치하고 `delete itemRef[field]`로 가짜 속성 정리 추가. 정적 스크립트 파싱(6개 0건 에러) 및 가짜 속성 정리/실시간 동기화/경로 이동 검증 완료.
- 2026-08-21: 감독모드가 직접 재검증 — (1) index.html:8164-8173(`field !== '세부작업명' && field !== '위험세부분류'` 가드)과 10226-10250(`saveEdits()`의 우선순위 변경 + `delete itemRef[field]`)를 Read로 열어 스펙 3-A/3-B와 한 글자도 다르지 않게 일치함을 확인, (2) 구문 검증 독립 재실행(스크립트 6개, 에러 0건), (3) 임시 테스트 파일(`test_wo16_unit.js`) 잔존 없음, 다른 파일 예상 밖 변경 없음 확인. **다만 지시(14:01)에서 명시적으로 요구한 "반드시 npm start 실제 GUI로 검증"이 이번에도 지켜지지 않음** — Gemini의 자체 검증은 이번에도 Node 스크립트(`test_wo16_unit.js`)와 `user_data.json` 직접 조회뿐이었음. 코드 대조로 로직의 정확성은 확인했으나(두 이벤트 리스너가 실제로 상호작용하는 방식까지 직접 추적해 원인을 설계했으므로 신뢰도는 높음), 이 버그 자체가 "브라우저 이벤트 리스너 간 상호작용"이라는, Node 시뮬레이션으로는 원천적으로 재현 불가능한 종류였기 때문에 완전한 "완료" 확정은 보류 — 사용자의 실제 GUI 확인 후에 최종 완료로 전환.

### WO-17: 최종 보고서 "표 여백" 설정 4종 최대치 2배 상향
- 상태: **작업 완료 🟢 (2026-08-21)**
- 스펙: [TASK_SPEC_ReportRowHeightMaxIncrease.md](TASK_SPEC_ReportRowHeightMaxIncrease.md)
- 요약: 사용자가 최종 보고서 미리보기에서 인쇄 여백을 조절하려는데 줄수/행높이/셀여백/줄간격 4개 값의 최대치가 너무 낮다고 요청, 현재의 2배로 상향(줄수 24→48, 행높이 45→90px, 셀여백 10→20px, 줄간격 2.0→4.0). HTML `<input max>` 4곳과 `initReportRowHeightPanel()`의 JS 클램프(`Math.min`) 4곳이 각각 독립적으로 상한을 강제하고 있어 — 한쪽만 바꾸면 `change` 시 값이 도로 깎이므로 — 둘 다 짝을 맞춰 상향해야 함을 확인.
- 대상 파일: `index.html`만
- 2026-08-21: 감독모드가 조사 완료 — HTML min/max 4곳(3390/3394/3398/3402)과 이를 별도로 재강제하는 JS 클램프(`applyChange()`, 10925-10944) 둘 다 grep/Read로 확인. 기본값·최소치·다른 로직은 범위 밖으로 명시. 15:13 지시 발송.
- 2026-08-21: Gemini 구현 완료 — HTML max 속성 4곳(48/90/20/4.0) 및 `applyChange()` 내 JS 클램프 4곳 상향 완료. 정적 스크립트 파싱(6개 0건 에러) 및 클램핑/경계값 검증 완료.
- 2026-08-21: 감독모드가 직접 재검증 — (1) index.html:3390/3394/3398/3402의 HTML `max` 속성 4곳이 정확히 48/90/20/4.0으로 바뀌었고 `min`/`step`은 무손상임을 Read로 확인, (2) `applyChange()`의 JS 클램프 4곳(10928-10939)이 짝이 맞게 `Math.min(48/90/20/4.0, ...)`으로 정확히 일치함을 확인, (3) 구문 검증 독립 재실행(스크립트 6개, 에러 0건), (4) 임시 테스트 파일(`test_wo17_unit.js`) 잔존 없음, 다른 파일 예상 밖 변경 없음 확인. 순수 상수값 8곳 짝맞춤 변경이라 코드 대조만으로 정확성이 자명해 완료로 확정(사용자 재확인 불필요).

## 백로그 (이번 작업 범위 아님 — 별도 승인 필요)

- **SB-1**: ⚙️ 항목별 AI 설정 팝업 내 "전역 설정으로 초기화" 버튼 추가. (WO-1 Gemini 제안, 스펙 범위 밖으로 이번 Confirm에서 제외됨, 2026-08-05)
- **SB-2**: 신규 항목 추가 확인 후 저장/렌더링 파이프라인(`saveUserData`→`buildTreeView`→`populateEditScreen`)에 try-catch 기반 원자적 롤백 로직 추가. (WO-1 Gemini 제안, 공용 함수 호출 시퀀스 변경이라 스펙 범위 밖으로 이번 Confirm에서 제외됨, 2026-08-05)
- **SB-3**: 표 여백 패널에 "🔄 표준값(16줄/24px)으로 원터치 리셋" 버튼 추가. (WO-2 Gemini 제안, 스펙 범위 밖으로 이번 Confirm에서 제외됨, 2026-08-05)
- **SB-4**: 표 여백 퀵 프리셋 3종 버튼(촘촘히/표준/여유있게) 추가. (WO-2 Gemini 제안, 스펙 범위 밖으로 이번 Confirm에서 제외됨, 2026-08-05)
- **SB-5**: `showEditScreen()`이 복원 Promise를 대기하는 동안 커서를 `wait`로 바꾸거나 버튼 텍스트에 로딩 표시. (WO-13 Gemini 제안, 스펙 Red Team #6이 명시적으로 범위 밖 처리, 2026-08-21)
- **SB-6**: 데이터 복원 완료 시 트리 화면 선택 카운터("선택된 항목: N개") 실시간 동기화. (WO-13 Gemini 제안, 스펙 범위 밖으로 이번 Confirm에서 제외됨, 2026-08-21)

## 완료

(없음)
