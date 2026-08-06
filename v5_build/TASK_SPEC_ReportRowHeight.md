# TASK_SPEC — 인쇄 미리보기 표 여백 조절 (목표 줄수 + 빈 행 높이 사용자 설정)

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-05
- **작성자**: Claude (감독 모드 조사/설계)
- **대상 파일**: `index.html` (보고서 렌더링부만 — `aiService.js`, `main.js` 등 다른 파일은 무관)

---

## 1. Context (왜 필요한가)

사용자가 최종 보고서 인쇄 미리보기를 확인한 결과, 항목 수가 적은 공종의 페이지에서 표 하단에 불필요한 빈 칸/빈 공간이 과도하게 남아 인쇄물 완성도가 떨어진다는 피드백을 주었다(스크린샷 첨부 확인). 조사 결과 원인은 "한 페이지 = 16줄"이라는 목표치를 채우기 위해 부족한 줄 수만큼 고정 높이의 빈 행을 자동 삽입하는 로직이며, 이 값들이 전부 하드코딩되어 있어 사용자가 조절할 방법이 없었다.

사용자 확정 답변(질문 결과):
- 조절 대상: **목표 줄 수(현재 16 고정) + 빈 행 높이(px) 둘 다**
- UI 위치: **보고서 미리보기 화면 액션바에 상시 노출** (기존 "인쇄 스타일"/"다국어 번역" 패널과 같은 줄)
- 적용 범위: **정석형/세련형/미래형 3개 인쇄 테마에 공통 값 1개** (테마별 개별 저장 아님)

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 보고서 렌더링 구조
- `generateReport()` — [index.html:10516-10594](index.html#L10516-L10594). `globalSelections`에서 항목을 모아 공종별로 그룹화 후, 공종마다 `getReportHTML(gongjong, items, lang)`을 호출해 `<div class="page">`를 만들어 `#report-preview`에 append.
- `getReportHTML()`은 테마 디스패처 — [index.html:10683-10688](index.html#L10683-L10688). `window.currentPrintTheme`(localStorage `printTheme`)에 따라 아래 3개 렌더러 중 하나를 호출:
  - `getReportHTML_Classic(gongjong, items, lang)` — [index.html:10691](index.html#L10691) 이하
  - `getReportHTML_Modern(gongjong, items, lang)` — [index.html:10904](index.html#L10904) 이하
  - `getReportHTML_Future(gongjong, items, lang)` — [index.html:11091](index.html#L11091) 이하
  (참고: [index.html:10598-10653](index.html#L10598-L10653)의 `getReportHTML(gongjong, items)`는 `/* ... */`로 주석 처리된 옛 백업 코드이며 실행되지 않는다 — 절대 건드리지 말 것.)

### 2.2 빈 행 채움 로직 (3곳 모두 동일 패턴, 하드코딩)
각 함수는 실제 항목들의 텍스트 길이를 18자/줄 기준으로 추정해 `totalEstimatedLines`를 누적한 뒤, 목표 줄수(16, 하드코딩)에서 부족한 만큼 빈 `<tr>`을 추가한다:

- **Classic**: `const targetTotalLines = 16;` / `<tr style="height: 25px;">` — [index.html:10781, 10785](index.html#L10781-L10785)
- **Modern**: `const emptyRowCount = Math.max(0, 16 - totalEstimatedLines);` / `<tr style="height:24px;">` — [index.html:10991, 10994](index.html#L10991-L10994)
- **Future**: `const emptyRowCount = Math.max(0, 16 - totalEstimatedLines);` / `<tr style="height:24px;">` — [index.html:11185, 11188](index.html#L11185-L11188)

이 두 값(목표 줄수, 빈 행 높이)을 조절할 수 있는 UI는 코드 전체에 존재하지 않는다 (grep 재확인 완료).

### 2.3 기존 유사 설정 UI 패턴 (재사용 대상)
- 인쇄 테마 선택 패널 마크업 — [index.html:3274-3289](index.html#L3274-L3289), 클래스 `.print-theme-panel.no-print` — [index.html:594-649](index.html#L594-L649)
- 다국어 번역 패널 마크업 — [index.html:3290-3300](index.html#L3290-L3300), 클래스 `.translation-panel` — [index.html:650-678](index.html#L650-L678)
- 두 패널 모두 `.report-preview-actions-panel`(= `.action-buttons.report-preview-actions-panel`, [index.html:3271](index.html#L3271)) 내부에 위치.
- 테마 변경 시 즉시 재렌더링하는 기존 패턴: `window.selectPrintTheme(theme)` — localStorage 저장 → 클래스 갱신 → `generateReport()` 호출 — [index.html:10659-10680](index.html#L10659-L10680). 새 설정도 동일 패턴(저장 → `generateReport()` 재호출)을 따를 것.
- `@media print`에서 `.action-buttons` 전체가 `display:none`으로 숨겨짐 — [index.html:1736-1747](index.html#L1736-L1747). 즉 `.report-preview-actions-panel` 하위에 새 컨트롤을 넣으면 실제 인쇄 시 자동으로 숨겨지므로 별도 `no-print` 클래스는 필수는 아니나, 기존 `print-theme-panel`처럼 붙여도 무방.

---

## 3. 구체적인 구현 방법

### A. 공통 설정 읽기 헬퍼 함수 신설
```js
function getReportRowSettings() {
    const targetLines = parseInt(localStorage.getItem('reportTargetLines'), 10);
    const emptyRowHeight = parseInt(localStorage.getItem('reportEmptyRowHeight'), 10);
    return {
        targetLines: (Number.isFinite(targetLines) && targetLines > 0) ? targetLines : 16,
        emptyRowHeight: (Number.isFinite(emptyRowHeight) && emptyRowHeight > 0) ? emptyRowHeight : 24
    };
}
```
- 기본값: `targetLines=16`(기존 Classic/Modern/Future 공통값 유지), `emptyRowHeight=24`(Modern/Future 기존값과 동일; Classic은 기존 25px에서 24px로 통일됨 — 3테마 공통 값 1개로 하기로 한 사용자 결정에 따른 의도된 변경이므로 버그 아님).
- 위치: `getReportHTML()` 디스패처 함수 바로 위 등 3개 렌더러가 모두 참조할 수 있는 곳에 정의.

### B. 3개 렌더러의 하드코딩 값 치환
- Classic [index.html:10781](index.html#L10781): `const targetTotalLines = 16;` → `const { targetLines: targetTotalLines, emptyRowHeight } = getReportRowSettings();`
- Classic [index.html:10785](index.html#L10785): `<tr style="height: 25px;">` → `<tr style="height: ${emptyRowHeight}px;">`
- Modern [index.html:10991](index.html#L10991): `const emptyRowCount = Math.max(0, 16 - totalEstimatedLines);` → `const { targetLines, emptyRowHeight } = getReportRowSettings(); const emptyRowCount = Math.max(0, targetLines - totalEstimatedLines);`
- Modern [index.html:10994](index.html#L10994): `<tr style="height:24px;">` → `<tr style="height:${emptyRowHeight}px;">`
- Future [index.html:11185](index.html#L11185), [11188](index.html#L11188): 위와 동일한 방식으로 치환.

### C. 설정 UI 패널 추가
`.report-preview-actions-panel` 내부, 기존 `translation-control-panel` div 바로 다음([index.html:3300](index.html#L3300) 이후)에 새 패널 삽입:
```html
<div class="report-row-height-panel no-print" id="report-row-height-panel">
    <span class="theme-label">📏 표 여백:</span>
    <label style="font-size:12px; font-weight:600; display:flex; align-items:center; gap:4px;">
        줄수
        <input type="number" id="report-target-lines-input" min="6" max="24" step="1" style="width:52px;">
    </label>
    <label style="font-size:12px; font-weight:600; display:flex; align-items:center; gap:4px;">
        행높이(px)
        <input type="number" id="report-empty-row-height-input" min="15" max="45" step="1" style="width:56px;">
    </label>
</div>
```
- CSS는 기존 `.print-theme-panel`/`.translation-panel`([index.html:594-678](index.html#L594-L678))과 시각적으로 통일되도록 `.report-row-height-panel`에 동일 톤의 배경/테두리/폰트 스타일을 추가하고, number input에도 `.translation-panel select`와 유사한 다크 배경/흰 글자 스타일을 적용.

### D. 이벤트 바인딩
기존 `savedTheme` 복원 로직 부근([index.html:7629-7635](index.html#L7629-L7635), `init()` 함수 내부)에 아래 초기화/바인딩 코드 추가:
```js
(function initReportRowHeightPanel() {
    const linesInput = document.getElementById('report-target-lines-input');
    const heightInput = document.getElementById('report-empty-row-height-input');
    if (!linesInput || !heightInput) return;

    const settings = getReportRowSettings();
    linesInput.value = settings.targetLines;
    heightInput.value = settings.emptyRowHeight;

    const applyChange = () => {
        let lines = parseInt(linesInput.value, 10);
        let height = parseInt(heightInput.value, 10);
        lines = Math.min(24, Math.max(6, Number.isFinite(lines) ? lines : 16));
        height = Math.min(45, Math.max(15, Number.isFinite(height) ? height : 24));
        linesInput.value = lines;
        heightInput.value = height;
        localStorage.setItem('reportTargetLines', lines);
        localStorage.setItem('reportEmptyRowHeight', height);
        generateReport();
    };
    linesInput.addEventListener('change', applyChange);
    heightInput.addEventListener('change', applyChange);
})();
```
- `change` 이벤트(입력 완료 후) 사용 — 매 키 입력마다 재렌더링하지 않도록(기존 `ai-max-len-hazard` 등 숫자 입력 UX와 동일 원칙).
- `generateReport()`는 `globalSelections`가 비어 있으면 안내 문구만 표시하고 조용히 종료하므로([index.html:10546-10549](index.html#L10546-L10549)) 보고서 미리보기 화면이 아닌 다른 화면에서 값이 바뀌어도 안전.

---

## 4. Red Team 체크포인트 (Gemini는 착수 전 스스로 점검할 것)

1. **범위 오염 방지**: JS 로직에서 최종 저장 전 반드시 `Math.min/Math.max`로 clamp할 것 — HTML `min`/`max` 속성은 브라우저/Electron 환경에 따라 강제되지 않는 경우가 있어 사용자가 0, 음수, 비정상적으로 큰 값(예: 9999)을 입력하면 빈 행이 수백 개 생성되어 인쇄물이 수십 페이지로 폭증할 수 있다.
2. **주석 처리된 옛 `getReportHTML(gongjong, items)`([index.html:10598-10653](index.html#L10598-L10653))는 절대 수정하지 말 것** — 죽은 코드이며 이번 작업과 무관.
3. 3개 렌더러(Classic/Modern/Future) 모두 동일한 `getReportRowSettings()`를 호출하도록 빠짐없이 수정했는지 확인 — 하나라도 누락하면 그 테마만 예전처럼 여백이 조절되지 않는 버그가 남는다.
4. 설정 변경 시 `generateReport()`가 호출되어 **즉시** 미리보기에 반영되는지 확인 — 값만 저장되고 재렌더링을 안 하면 사용자가 "적용이 안 된다"고 오인할 수 있다.
5. 이 설정은 편집화면(`#risk-assessment-screen`)의 표나 WO-1 매뉴얼 모드 기능과는 완전히 무관한 별도 영역이다. 편집화면 쪽 코드는 절대 건드리지 말 것.
6. localStorage 키(`reportTargetLines`, `reportEmptyRowHeight`)가 다른 기존 키와 충돌하지 않는지 확인 (`printTheme`, `manualModeEnabled` 등과 이름이 겹치지 않음 — 이미 확인됨).
7. 앱을 재시작해도 입력창에 마지막 설정값이 정확히 복원되는지 확인 (localStorage 저장/로드 왕복 검증).
8. 이번 작업 범위를 벗어나는 기능 제안(예: 테마별 개별 저장, 자동 페이지 맞춤 계산 등)이 떠오르면 절대 임의로 구현하지 말고 "작업 전 의견 보고서"에 제안으로만 적을 것.

---

## 5. 검증 절차 (감독모드에서 Claude가 직접 재실행하여 확인)

1. 정적 구문 검증: `index.html` 스크립트 블록 파싱 재실행, 오류 0건 확인. `node -c aiService.js`(변경 없을 예정이지만 회귀 확인 차 재실행).
2. `npm start`로 앱 실행 후 수동 시나리오:
   a. 항목 몇 개만 선택한 상태로 최종 보고서 생성 → 미리보기 화면에서 `📏 표 여백` 패널의 `줄수`/`행높이(px)` 입력값이 기본 16 / 24로 보이는지 확인.
   b. `줄수`를 8로 낮춤 → 표 하단 빈 칸이 확연히 줄어드는지 확인.
   c. `행높이(px)`를 40으로 올림 → 남은 빈 행들이 더 두꺼워지는지 확인.
   d. 인쇄 테마를 정석형→세련형→미래형으로 전환하며 동일한 줄수/행높이 값이 3개 테마 모두에 일관되게 적용되는지 확인.
   e. 값을 비정상적으로 크게(예: 9999) 입력해보고 clamp되어 6~24, 15~45 범위 내로 강제되는지 확인 (Red Team #1 실제 재현 확인).
   f. 앱 재시작 후 편집했던 설정값이 그대로 복원되는지 확인.
   g. 실제 "PDF 미리보기 및 인쇄"를 눌러 인쇄 미리보기에서도 조절된 여백이 반영되는지, `📏 표 여백` 패널 자체는 인쇄물에 나타나지 않는지 확인.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`의 WO-2 상태를 완료로 변경.
