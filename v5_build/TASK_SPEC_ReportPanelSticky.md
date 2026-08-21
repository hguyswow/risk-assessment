# TASK_SPEC — 보고서 미리보기 액션바(표 여백 조절 포함) 스크롤 시 상단 고정

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-07
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만

---

## 1. Context (왜 필요한가)

사용자가 WO-2(표 여백 조절)를 실제로 써보면서 스크린샷과 함께 두 가지를 지적했다:
1. "여백과 칸 조절 기능이 스크롤 다운시 사라져버려 실시간 확인하며 조절하기가 힘들다" — `📏 표 여백` 컨트롤이 있는 액션바가 일반 문서 흐름(sticky 아님)에 있어서, 보고서 내용을 보려고 아래로 스크롤하면 컨트롤 자체가 화면 밖으로 사라진다. 그러니 값을 바꾸면서 표가 실제로 어떻게 바뀌는지 동시에 볼 수 없다.
2. "현재 실제 동작하는지도 잘 모르겠다" — 위 1번이 원인일 가능성이 크다. 컨트롤과 결과 표를 동시에 볼 수 없으니 값을 바꿔도 반영되는지 체감이 안 된다.

**감독모드 사전 확인**: WO-2 로직(`getReportRowSettings()`, `initReportRowHeightPanel()`의 `change` 이벤트 → `generateReport()` 재호출) 자체는 이번 대화에서 이미 코드 레벨로 검증 완료된 상태이며, 이번 세션의 다른 작업(WO-3~6)은 전부 화면1/편집화면 쪽만 건드렸고 보고서 미리보기 패널 로직은 손대지 않았다. 즉 **"실제로 안 되는" 버그가 아니라 "눈으로 확인하기 어려운" UX 문제일 가능성이 높다** — 이번 작업으로 패널을 고정시키면 값 변경과 표 변화를 동시에 볼 수 있게 되어 2번 의문도 자연히 해소될 것으로 판단한다. 코드 로직 자체를 다시 뜯어고치지 않는다(범위 오버 방지).

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 현재 구조
- `.main-title-container` — [index.html:106-119](index.html#L106-L119). 앱 전체 상단(공사명/회사명 등이 아니라 앱 타이틀 바)에 이미 `position: sticky; top: -20px; z-index: 1000;`이 적용되어 있다. 이 요소는 화면1/편집화면/보고서 미리보기 화면 전부의 공통 상위 요소로, 어느 화면에 있든 스크롤해도 상단에 고정된다(사용자 스크린샷 맨 위에 살짝 보이는 회사명 표시 영역이 바로 이것). **이미 검증된 sticky 패턴이 프로젝트에 존재한다 — 새로 발명할 필요 없이 그대로 응용.**
- `.report-preview-actions-panel` — CSS 정의 [index.html:580-591](index.html#L580-L591), 마크업은 `#report-preview-screen` 안, `<div class="action-buttons report-preview-actions-panel">`. 사용자가 스크린샷에서 빨간 원으로 표시한 `📏 표 여백` 컨트롤이 이 패널 안에 있으며, 같은 줄에 `편집 화면으로`/`PDF 미리보기 및 인쇄`/`표지 포함`/`인쇄 스타일`/`다국어 번역` 버튼들도 함께 있다. **현재 이 패널은 sticky가 아니라 일반 문서 흐름에 있어서 스크롤하면 그대로 같이 스크롤되어 사라진다.**
- `generateReport()` — [index.html:10646](index.html#L10646) 이하 (살아있는 함수. [index.html:10597](index.html#L10597)의 동명 함수는 `/* ... */` 주석 처리된 죽은 백업 코드이므로 건드리지 말 것). 보고서 미리보기 화면을 표시하고 내용을 렌더링하는 진입점.

### 2.2 왜 단순히 `position: sticky`만 추가하면 안 되는가
`.main-title-container`가 이미 `top: -20px`로 화면 최상단에 고정되어 있으므로, `.report-preview-actions-panel`도 `position: sticky; top: 0;`으로만 두면 **두 sticky 요소가 겹쳐버린다**(액션바가 타이틀 바 뒤에 가려지거나 겹쳐 보임). `.report-preview-actions-panel`의 `top` 값은 `.main-title-container`의 실제 렌더링된 높이만큼 아래로 내려줘야 정확히 그 밑에 이어 붙는다. 이 높이는 로고 유무, 회사명 길이에 따른 줄바꿈 등으로 고정 픽셀 값이 아니라 **런타임에 실제로 측정**해야 한다(하드코딩하면 로고를 켜고 끄는 사용자 설정 등에서 어긋날 수 있음).

---

## 3. 구체적인 구현 방법

### A. CSS: `.report-preview-actions-panel`을 sticky로 전환
[index.html:580-591](index.html#L580-L591)의 기존 규칙에 다음을 추가(기존 `display/align-items/gap/padding/background/border-radius/border/box-shadow`는 그대로 유지):
```css
.report-preview-actions-panel {
    /* ...기존 속성 그대로... */
    position: sticky !important;
    z-index: 500 !important;
}
```
(`top` 값은 고정 숫자로 넣지 않는다 — B에서 JS가 인라인 `style.top`으로 동적으로 채운다. CSS에는 `top` 선언을 아예 넣지 말거나, 안전한 폴백으로 `top: 90px !important;` 정도만 넣어두고 JS가 즉시 덮어쓰게 할 것.)

### B. JS: `.main-title-container` 실측 높이로 `top` 오프셋 동기화
새 함수 신설:
```js
function syncReportPanelStickyOffset() {
    const titleEl = document.querySelector('.main-title-container');
    const panel = document.querySelector('.report-preview-actions-panel');
    if (!titleEl || !panel) return;
    const offset = titleEl.getBoundingClientRect().bottom;
    if (offset > 0) {
        panel.style.top = offset + 'px';
    }
}
```
- `generateReport()`([index.html:10646](index.html#L10646)) 안에서, 함수 시작 부분 실행 후(화면 전환 직후) 호출: `syncReportPanelStickyOffset();`. 렌더 직후 바로 호출 1회 + 레이아웃이 완전히 자리잡을 시간을 주기 위해 `setTimeout(syncReportPanelStickyOffset, 150);`도 한 번 더 호출(이 프로젝트의 다른 모달 포커스 로직에서도 쓰는 150ms 지연 패턴과 동일한 관례).
- `window.addEventListener('resize', syncReportPanelStickyOffset);`를 `init()` 또는 앱 초기화 시점에 한 번 등록(창 크기 조절 시 타이틀 바 높이가 달라질 수 있으므로).

### C. 인쇄 시 영향 없음 확인(코드 변경 불필요, 확인만)
`@media print`에서 `.action-buttons`(→ `.report-preview-actions-panel`도 포함)가 이미 `display: none !important;` 처리되어 있으므로([index.html:1736-1747](index.html#L1736-L1747) 인근, 기존 규칙), sticky 속성 추가가 인쇄물에 영향을 주지 않는다. 이 규칙을 건드릴 필요는 없고, 착수 전 실제로 그런지 다시 한 번 확인만 할 것.

---

## 4. Red Team 체크포인트

1. **`.report-preview-actions-panel`의 `top`이 `.main-title-container`의 실제 높이와 정확히 맞아떨어져, 두 sticky 바가 겹치지 않고 자연스럽게 위아래로 붙어 고정되는가?** 로고가 있는 상태/없는 상태, 회사명이 긴 경우(줄바꿈 발생) 등 실제 화면에서 확인.
2. **`z-index: 500`이 `.main-title-container`의 `z-index: 1000`보다 낮아 타이틀 바 아래로 자연스럽게 깔리는가?** (겹칠 때 액션바가 타이틀 바를 덮어써서 타이틀이 안 보이는 사고 방지.) 동시에 보고서 본문 내용(표, 이미지 등)보다는 위에 그려져야 함.
3. **인쇄(PDF 미리보기 및 인쇄) 시 이 패널이 여전히 인쇄물에 노출되지 않는가?** (기존 `.action-buttons` 숨김 규칙이 sticky 추가로 무력화되지 않는지 실제 인쇄 미리보기로 확인.)
4. **보고서 내용이 화면 높이보다 짧아서 스크롤이 아예 필요 없는 경우에도 레이아웃이 깨지지 않는가?** (sticky는 스크롤이 없으면 일반 요소처럼 동작해야 정상.)
5. **`syncReportPanelStickyOffset()`가 `.main-title-container`나 `.report-preview-actions-panel`이 아직 DOM에 없는 시점(다른 화면이 활성일 때 등)에 호출돼도 에러 없이 조용히 반환되는가?** (null 체크 확인.)
6. 이번 작업 범위를 벗어나는 것(예: 표 여백 조절 로직 자체의 재작성, 다른 화면 패널까지 확대 적용 등)은 임의로 구현하지 말고 제안으로만 보고할 것 — 이번 스펙은 순수 "패널이 스크롤 중에도 보이게" 하는 레이아웃 수정이다.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트/스타일 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 항목을 충분히 선택해(표가 화면 높이보다 길어지도록) 최종 보고서 생성 → 아래로 스크롤 → `📏 표 여백` 등 액션바가 화면 상단(타이틀 바 바로 아래)에 그대로 고정되어 보이는지 확인.
   b. 스크롤한 채로 `줄수`/`행높이(px)` 값을 바꿔가며, 하단에 보이는 표의 빈 행 개수/높이가 **즉시 실시간으로** 바뀌는지 확인 — 이걸로 "실제 동작하는지" 의문이 해소되는지 확인.
   c. 인쇄 테마를 바꾸거나 다국어 번역을 실행해도 고정된 액션바 안에서 정상 동작하는지 확인.
   d. `🖨️ PDF 미리보기 및 인쇄`를 눌러 실제 인쇄 미리보기에는 이 액션바가 나타나지 않는지 확인.
   e. 창 크기를 조절해봐도 액션바와 타이틀 바가 겹치지 않고 계속 정렬 상태를 유지하는지 확인.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-7로 기록하고, 동시에 이번 검증으로 WO-2의 "수동검증 대기" 상태도 함께 해소되었는지 최종 판단.
