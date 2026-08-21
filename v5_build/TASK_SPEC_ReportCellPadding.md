# TASK_SPEC — 보고서 표 내용 셀 상하 여백/줄간격 사용자 조절 (실제 페이지 압축 목적)

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-07
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만

---

## 1. Context (왜 필요한가)

WO-2의 "행높이(px)" 설정은 **빈 채움 행에만** 적용된다. 그런데 사용자가 실제로 원하는 건 "내용이 많아서 이미 여러 줄로 늘어난 실제 데이터 행"의 위아래 여백을 줄여서 페이지 전체 길이를 압축하는 것이다. 사용자의 말을 그대로 인용하면: "현재 내용이 많은 줄에 여백을 두고 페이지 여백을 좀 줄여보려는 것이다... 현재 시스템은 글자 줄에 맞추어 자동으로 표 높이가 적용되는 부분이 있다... 표 내부의 상하 여백을 조절하여 표 높이 또는 줄간격을 조절하는 것이 더 현실적일 것 같다."

**감독모드 원인 확인**: `개선대책`처럼 텍스트가 긴 필드는 셀 안에서 자동 줄바꿈되어 여러 줄이 되고, 그 행의 실제 렌더링 높이는 셀의 `padding`(현재 하드코딩 4~5px)과 `line-height`(현재 하드코딩 없음/1.4/1.5, 테마마다 다름)에 의해 결정된다. 이 값들이 전부 코드에 고정되어 있어 사용자가 조절할 방법이 없었다 — WO-2가 손댄 "빈 행 높이"와는 완전히 별개의 문제다.

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 실제 데이터 셀의 padding/line-height 하드코딩 위치 (3개 테마, 유해위험요인·현재조치·감소대책 3개 필드만 해당)
- **Classic**: [index.html:10777-10780](index.html#L10777-L10780) — `padding: 4px;`만 있고 **`line-height`는 아예 지정돼 있지 않음**(브라우저 기본값 적용, 대략 1.15~1.2).
- **Modern**: [index.html:11161-11167](index.html#L11161-L11167) — `padding:5px;font-size:9pt;line-height:1.4;`.
- **Future**: [index.html:11356-11362](index.html#L11356-L11362) — `padding:5px;font-size:9pt;line-height:1.5;` (일부 `letter-spacing:-0.2px;` 포함, 손대지 말 것).

이 3개 필드(위험발생및결과/현재조치/감소대책)만 손보면 된다 — 세부작업명/위험세부분류/위험성 배지 셀은 짧은 한 줄 라벨이라 행 전체 높이(테이블 행 높이는 가장 큰 셀 기준으로 정해짐)에 영향을 주지 않으므로 건드릴 필요 없음(범위 최소화).

### 2.2 기존 설정 패널과 헬퍼 재사용
- `getReportRowSettings()` — [index.html:10821-10828](index.html#L10821-L10828). WO-2가 만든 "빈 행" 전용 설정 헬퍼 — **이 함수 자체는 건드리지 않는다.** 이번엔 완전히 별개의 새 헬퍼 `getReportCellStyleSettings()`를 만든다(빈 행 설정과 내용 셀 설정을 섞으면 나중에 헷갈림).
- `initReportRowHeightPanel()` — [index.html:10842-10871](index.html#L10842-L10871). `linesInput`/`heightInput` 2개를 다루는 기존 `applyChange` 패턴이 있다 — 이번 신규 입력 2개도 **같은 함수 안에 확장**해서 넣는다(새 init 함수를 따로 만들지 말 것 — 이미 이 함수가 리사이즈 리스너 등록, 패널 초기화를 전담하고 있으므로 여기 넣는 게 일관적).
- 패널 마크업 — `행높이(px)` 입력란이 끝나는 지점 [index.html:3378-3379](index.html#L3378-L3379) 바로 다음에 새 입력 2개를 이어 붙인다. `.report-preview-actions-panel`은 이미 `flex-wrap: wrap !important;`가 걸려있어([index.html:584](index.html#L584)) 입력이 늘어나도 줄바꿈되어 레이아웃이 깨지지 않는다(확인 완료).

---

## 3. 구체적인 구현 방법

### A. 새 설정 읽기 헬퍼 (`getReportRowSettings()` 근처에 나란히 추가)
```js
function getReportCellStyleSettings() {
    const cellPadding = parseInt(localStorage.getItem('reportCellPadding'), 10);
    const lineHeight = parseFloat(localStorage.getItem('reportLineHeight'));
    return {
        cellPadding: (Number.isFinite(cellPadding) && cellPadding > 0) ? cellPadding : 4,
        lineHeight: (Number.isFinite(lineHeight) && lineHeight > 0) ? lineHeight : 1.4
    };
}
```

### B. 패널에 입력 2개 추가
[index.html:3378-3379](index.html#L3378-L3379) 다음에:
```html
<label style="font-size:12px; font-weight:600; display:flex; align-items:center; gap:4px; cursor:pointer;">
    셀 여백(px)
    <input type="number" id="report-cell-padding-input" min="1" max="10" step="1" style="width:52px;">
</label>
<label style="font-size:12px; font-weight:600; display:flex; align-items:center; gap:4px; cursor:pointer;">
    줄간격
    <input type="number" id="report-line-height-input" min="1.0" max="2.0" step="0.1" style="width:56px;">
</label>
```

### C. `initReportRowHeightPanel()` 확장 (새 함수 만들지 않고 기존 함수에 통합)
[index.html:10842-10871](index.html#L10842-L10871)을 아래처럼 확장:
```js
function initReportRowHeightPanel() {
    const linesInput = document.getElementById('report-target-lines-input');
    const heightInput = document.getElementById('report-empty-row-height-input');
    const cellPaddingInput = document.getElementById('report-cell-padding-input');
    const lineHeightInput = document.getElementById('report-line-height-input');

    window.removeEventListener('resize', syncReportPanelStickyOffset);
    window.addEventListener('resize', syncReportPanelStickyOffset);

    if (!linesInput || !heightInput) return;

    const settings = getReportRowSettings();
    linesInput.value = settings.targetLines;
    heightInput.value = settings.emptyRowHeight;

    const cellSettings = getReportCellStyleSettings();
    if (cellPaddingInput) cellPaddingInput.value = cellSettings.cellPadding;
    if (lineHeightInput) lineHeightInput.value = cellSettings.lineHeight;

    const applyChange = () => {
        let lines = parseInt(linesInput.value, 10);
        let height = parseInt(heightInput.value, 10);
        lines = Math.min(24, Math.max(6, Number.isFinite(lines) ? lines : 16));
        height = Math.min(45, Math.max(15, Number.isFinite(height) ? height : 24));
        linesInput.value = lines;
        heightInput.value = height;
        localStorage.setItem('reportTargetLines', lines);
        localStorage.setItem('reportEmptyRowHeight', height);

        if (cellPaddingInput && lineHeightInput) {
            let cellPadding = parseInt(cellPaddingInput.value, 10);
            let lineHeightVal = parseFloat(lineHeightInput.value);
            cellPadding = Math.min(10, Math.max(1, Number.isFinite(cellPadding) ? cellPadding : 4));
            lineHeightVal = Math.min(2.0, Math.max(1.0, Number.isFinite(lineHeightVal) ? lineHeightVal : 1.4));
            cellPaddingInput.value = cellPadding;
            lineHeightInput.value = lineHeightVal;
            localStorage.setItem('reportCellPadding', cellPadding);
            localStorage.setItem('reportLineHeight', lineHeightVal);
        }

        if (typeof generateReport === 'function') {
            generateReport();
        }
    };
    linesInput.addEventListener('change', applyChange);
    heightInput.addEventListener('change', applyChange);
    if (cellPaddingInput) cellPaddingInput.addEventListener('change', applyChange);
    if (lineHeightInput) lineHeightInput.addEventListener('change', applyChange);
}
```
(기존 `linesInput`/`heightInput` clamp 로직은 그대로 보존 — 새 입력 2개의 clamp만 추가.)

### D. 3개 테마 렌더러의 하드코딩 padding/line-height를 설정값으로 치환
각 렌더러 함수 상단(예: `totalEstimatedLines` 계산 시작 전, 또는 3개 `<td>`를 만드는 템플릿 리터럴 직전)에서 `const { cellPadding, lineHeight } = getReportCellStyleSettings();`를 한 번 선언하고, 아래처럼 치환:

- **Classic** [index.html:10777-10780](index.html#L10777-L10780):
  ```js
  <td style="border: 1px solid black; padding: ${cellPadding}px; font-size: 9pt; line-height: ${lineHeight};">${item.위험발생및결과}</td>
  <td style="border: 1px solid black; padding: ${cellPadding}px; font-size: 9pt; line-height: ${lineHeight};">${item.현재조치 || ''}</td>
  ... (위험성 배지 셀은 그대로 유지) ...
  <td style="border: 1px solid black; padding: ${cellPadding}px; font-size: 9pt; line-height: ${lineHeight};">${item.감소대책 || ''}</td>
  ```
  (Classic은 원래 `line-height`가 없었으므로 **새로 추가**하는 것 — 기존에 없던 속성을 넣는다고 당황하지 말 것.)

- **Modern** [index.html:11161-11167](index.html#L11161-L11167): `padding:5px` → `padding:${cellPadding}px`, `line-height:1.4` → `line-height:${lineHeight}` (위험발생및결과/현재조치/감소대책 3곳만).

- **Future** [index.html:11356-11362](index.html#L11356-L11362): `padding:5px` → `padding:${cellPadding}px`, `line-height:1.5` → `line-height:${lineHeight}` (위험발생및결과/현재조치/감소대책 3곳만, `letter-spacing:-0.2px;`가 붙은 줄은 그 속성은 그대로 두고 padding/line-height만 치환).

- 세부작업명/위험세부분류/위험성 배지/개선후위험성 셀들의 `padding`은 **건드리지 않는다**(2.1에서 설명한 대로 범위 밖 — 이 셀들은 짧은 라벨이라 행 전체 높이에 영향을 주지 않고, 굳이 건드리면 diff만 커짐).

---

## 4. Red Team 체크포인트

1. **3개 테마(Classic/Modern/Future) 전부, 3개 필드(위험발생및결과/현재조치/감소대책)씩 총 9곳을 빠짐없이 치환했는가?** 하나라도 빠지면 그 테마/필드만 예전처럼 고정된 채로 남는다.
2. **Classic에는 원래 `line-height`가 없었으므로, 다른 속성을 실수로 지우지 않고 순수하게 `line-height: ${lineHeight};`를 추가만 했는가?**
3. **`cellPadding`/`lineHeight` clamp 범위(1~10px, 1.0~2.0)를 벗어난 값(0, 음수, 문자열 등)을 입력해도 `getReportCellStyleSettings()`의 기본값(4px/1.4)으로 안전하게 폴백되는가?**
4. **WO-2의 `getReportRowSettings()`(빈 행 설정)와 이번 `getReportCellStyleSettings()`(내용 셀 설정)가 서로 섞이지 않고 완전히 독립적으로 동작하는가?** 특히 localStorage 키(`reportCellPadding`, `reportLineHeight`)가 기존 키(`reportTargetLines`, `reportEmptyRowHeight`)와 겹치지 않는지 확인.
5. **세부작업명/위험세부분류/위험성 배지 등 다른 셀들의 padding은 건드리지 않았는가?** (2.1에서 명시한 범위 제한 준수.)
6. **값 변경 시 `generateReport()`가 재호출되어 즉시 반영되는가**, 그리고 WO-8에서 고친 스크롤 유지 동작이 이번에도 정상 작동하는가(같은 `generateReport()` 흐름을 타므로 자동으로 되어야 하지만 실제 확인).
7. 이번 작업 범위를 벗어나는 것(예: 세부작업명 등 라벨 셀까지 조절 가능하게 확장, 빈 행 설정과 통합 UI로 재설계 등)은 임의로 구현하지 말고 제안으로만 보고할 것.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 개선대책이 긴(여러 줄로 늘어나는) 항목이 포함된 보고서를 생성 → 새 `셀 여백(px)`을 1로, `줄간격`을 1.0으로 낮춰가며 해당 행의 실제 높이가 눈에 띄게 줄어드는지 확인.
   b. 3개 인쇄 테마(정석형/세련형/미래형) 모두에서 동일하게 적용되는지 확인.
   c. 값을 조절해도 스크롤 위치가 유지된 채(WO-8) 실시간으로 반영되는지 확인.
   d. 빈 행이 있는 상태(줄수를 높게 설정)에서 "행높이(px)"와 새 "셀 여백/줄간격"이 서로 간섭 없이 독립적으로 동작하는지 확인 — 빈 행은 여전히 빈 행 높이 설정을, 내용 행은 새 셀 여백/줄간격 설정을 따라야 함.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-9로 기록하고 완료 처리.
