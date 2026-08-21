# TASK_SPEC — 최종 보고서 미리보기 화면 직접 편집 (유해위험요인/현재조치/개선대책)

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-07
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만

---

## 1. Context (왜 필요한가)

사용자가 WO-9(셀 여백/줄간격 조절)를 확인해보고 만족한 뒤, "이 화면(최종 보고서 미리보기)에서 출력된 내용을 사용자가 바로 편집할 수 있게 하면 어떨까, 직관적이라 오히려 장점일 것 같다"고 제안했다. 지금은 편집을 하려면 "⬅️ 편집 화면으로" 버튼을 눌러 별도의 편집 화면으로 돌아가야 하는데, 미리보기 화면에서 오탈자나 문구를 바로 고칠 수 있으면 왕복이 줄어든다.

사용자 확정 답변(질문 결과):
- 편집 범위: **유해위험요인 / 현재조치 / 개선대책 3개 텍스트 필드만** (위험등급 드롭다운, 헤더 정보 등은 이번 범위 밖).
- 다국어 번역본 표시 중: **편집 비활성화** (한국어 원본일 때만 편집 가능, 번역어 선택 시에는 셀이 읽기 전용으로 유지됨).

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 현재 구조의 근본적 제약
`getReportHTML_Classic/Modern/Future` 3개 렌더러는 `riskData`를 읽어 **매번 완전히 새로운 HTML 문자열**을 만들어 `innerHTML`로 주입한다(WO-9까지 이미 검증됨). 지금 이 템플릿 안의 `<td>`들은 순수 텍스트 보간(`${item.위험발생및결과}` 등)일 뿐, 어떤 `riskData` 항목에 대응하는지 식별할 방법(`data-id` 등)이 전혀 없다. 편집을 가능하게 하려면:
1. 해당 `<td>`에 `contenteditable="true"`와 `data-id`/`data-field`를 심어 식별 가능하게 만들고,
2. 사용자가 셀 밖으로 포커스를 옮기는 시점(`blur`)에 그 값을 `riskData`의 실제 항목 객체에 반영한 뒤 저장해야 한다.

### 2.2 재사용할 기존 함수/패턴
- `findItemRefById(id, data = riskData)` — [index.html:9825](index.html#L9825). 이미 존재하는, id로 `riskData` 안의 리프 항목 참조를 찾는 함수 — 그대로 재사용.
- `saveUserData()` — [index.html:4527](index.html#L4527). IndexedDB + `user_data.json` 이중 저장 함수 — 그대로 재사용.
- `dom.reportPreview` — [index.html:5500](index.html#L5500), `#report-preview` 엘리먼트 캐시. 새 이벤트 리스너를 여기에 위임(delegation) 방식으로 붙인다.
- **`blur`/`focus` 이벤트는 버블링되지 않는다** — `dom.reportPreview.addEventListener('blur', handler, true)`처럼 반드시 캡처링(capture) 단계로 등록해야 위임이 동작한다(WO-1 편집화면의 `input` 이벤트 위임과는 다른 주의점 — 착수 전 반드시 인지할 것).

### 2.3 렌더러 함수 시그니처와 대상 셀 (WO-9에서 이미 다룬 동일 9곳)
`getReportHTML_Classic(gongjong, items, lang = 'ko')` [index.html:10920](index.html#L10920), `_Modern` [index.html:11134](index.html#L11134), `_Future` [index.html:11323](index.html#L11323) — 세 함수 모두 이미 `lang` 매개변수를 받고 있다. 대상 `<td>` 9곳(위험발생및결과/현재조치/감소대책 × 3테마)은 WO-9가 `${cellPadding}`/`${lineHeight}`를 심어둔 바로 그 위치다(Classic 약 10976-10980, Modern 약 11201-11207, Future 약 11397-11403 — WO-9 이후 재확인 필요, 정확한 현재 줄번호는 착수 시 재조회할 것).

### 2.4 번역 편집 비활성화 판단 기준
`generateReport()`에서 이미 `const lang = window.currentLang || 'ko';`를 계산해 각 렌더러에 넘기고 있다. 각 렌더러 내부에서 `const isEditableLang = (lang === 'ko');`로 판단하면 된다 — 새로운 전역 상태 없이 기존에 넘어오는 `lang` 인자만으로 충분하다.

### 2.5 빈 채움 행(WO-2)은 대상이 아님
`riskData` 항목이 아닌 순수 레이아웃용 빈 `<tr>`(WO-2가 만든 필러 행)에는 `item.id`가 존재하지 않는다 — 이 행들은 애초에 대상이 아니므로 건드릴 필요 없음(자연히 제외됨).

---

## 3. 구체적인 구현 방법

### A. 3개 렌더러의 대상 9개 `<td>`에 편집 속성 추가
각 렌더러 상단(WO-9가 `const { cellPadding, lineHeight } = getReportCellStyleSettings();`를 선언한 바로 다음 줄)에 추가:
```js
const isEditableLang = (lang === 'ko');
```
그리고 대상 9개 `<td>`를 예시처럼 수정(Classic 기준, Modern/Future도 동일 원리로 각자의 마크업 문법에 맞춰 적용):
```js
<td contenteditable="${isEditableLang ? 'true' : 'false'}" data-id="${item.id}" data-field="위험발생및결과" class="${isEditableLang ? 'report-editable-cell' : ''}" style="border: 1px solid black; padding: ${cellPadding}px; font-size: 9pt; line-height: ${lineHeight};">${item.위험발생및결과}</td>
```
현재조치/감소대책도 `data-field` 값만 각각 `"현재조치"`/`"감소대책"`로 바꿔 동일하게 적용. (`위험성`/`개선후위험성` 배지 셀, `세부작업명`/`위험세부분류` 라벨 셀은 이번 범위 밖 — 건드리지 않음.)

### B. 편집 가능 셀의 시각적 구분용 CSS 신설
```css
.report-editable-cell {
    cursor: text;
    transition: background-color 0.15s ease;
}
.report-editable-cell:hover {
    background-color: rgba(59, 130, 246, 0.06);
}
.report-editable-cell:focus {
    outline: 2px dashed #2563eb;
    outline-offset: -2px;
    background-color: rgba(59, 130, 246, 0.1);
}
```
(`:hover`/`:focus` 상태 기반이라 인쇄 시(`@media print`)에는 자연히 아무 흔적도 남지 않는다 — 별도로 인쇄 CSS를 건드릴 필요 없음. 착수 전 실제로 인쇄 미리보기에서 흔적이 없는지 확인만 할 것.)

### C. 편집 커밋 이벤트 위임 (신규 함수)
```js
function initReportPreviewInlineEdit() {
    if (!dom.reportPreview) return;
    dom.reportPreview.addEventListener('blur', async (e) => {
        const target = e.target;
        if (!target.matches || !target.matches('.report-editable-cell')) return;
        const id = target.dataset.id;
        const field = target.dataset.field;
        if (!id || !field) return;

        const itemRef = findItemRefById(id);
        if (!itemRef) return;

        const newValue = target.textContent.trim();
        if (itemRef[field] === newValue) return; // 변경 없으면 저장 생략

        itemRef[field] = newValue;
        await saveUserData();
        if (typeof showSaveToast === 'function') {
            showSaveToast('✏️ 수정 내용이 저장되었습니다.', 'success', 1200);
        }
    }, true); // ★ capture 필수 — blur는 버블링되지 않음 (2.2 참고)
}
```
`init()` 또는 `DOMContentLoaded` 시점, 다른 `init*Panel()` 함수들이 호출되는 위치에 `if (typeof initReportPreviewInlineEdit === 'function') initReportPreviewInlineEdit();` 한 줄 추가.

### D. 번역본 표시 중 안내
번역 실행(`executeTranslation()`) 완료 시점 또는 `handleLangChange()`에서, `lang !== 'ko'`이면 (선택) 짧은 안내 토스트 한 번(`"번역본은 읽기 전용입니다. 수정하려면 한국어(원본)으로 전환하세요."`)을 띄우는 것은 **선택 사항** — 필수는 아님. Gemini 판단에 맡기되, 넣더라도 매번 반복 노출되지 않게 할 것.

---

## 4. Red Team 체크포인트

1. **`blur` 이벤트가 캡처링(`true`) 단계로 등록되어 있는가?** 버블링 단계로 등록하면 위임이 전혀 동작하지 않는다(가장 흔한 실수).
2. **번역어(한국어 아닌 언어) 상태에서는 실제로 `contenteditable`이 `"false"`로 렌더링되어 셀을 클릭해도 편집이 안 되는가?** 3개 테마 모두 재확인.
3. **9개 대상 셀 전부(3테마×3필드) 빠짐없이 `data-id`/`data-field`/`contenteditable`을 갖는가?** 하나라도 빠지면 그 셀만 편집해도 저장이 안 되는 조용한 실패가 발생한다.
4. **`findItemRefById(id)`가 못 찾는 경우(이론상 없어야 하지만) 조용히 무시하고 크래시하지 않는가?** null 가드 확인.
5. **`itemRef[field] === newValue`일 때 불필요한 `saveUserData()` 호출을 생략하는가?** (매 blur마다 무조건 저장하면 아무 것도 안 바꾸고 클릭만 했다 나가도 저장이 도는 낭비가 생긴다.)
6. **편집 중(포커스 상태)에 다른 설정(테마 전환, 행높이 조절 등)을 바꿔서 `generateReport()`가 재호출되어도, 그 직전에 blur가 먼저 발생해 편집 내용이 유실 없이 저장되는가?** (테마 버튼이나 다른 입력을 클릭하면 브라우저가 자동으로 이전 포커스 요소를 blur시키므로 이론상 안전하지만, 실제 재현 확인 필수.)
7. **인쇄 미리보기(PDF)에 편집 가능 셀의 점선 아웃라인이나 호버 배경 등 편집 UI 흔적이 전혀 나타나지 않는가?**
8. **편집화면(`#risk-assessment-screen`)이나 WO-1 매뉴얼 모드 관련 코드는 이번 작업과 무관하므로 전혀 건드리지 않았는가?**
9. 이번 작업 범위를 벗어나는 것(위험등급 드롭다운, 헤더 정보, 번역본 편집 지원 등)은 임의로 구현하지 말고 제안으로만 보고할 것.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트/스타일 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 최종 보고서 생성(한국어 원본) → 유해위험요인/현재조치/개선대책 셀을 클릭해 텍스트를 수정 → 다른 곳을 클릭(blur) → 저장 토스트가 뜨는지, 앱을 재시작해도 수정 내용이 유지되는지 확인.
   b. 편집화면으로 돌아가 봐도 방금 미리보기에서 고친 내용이 반영되어 있는지 확인(같은 `riskData` 참조를 공유하므로 당연히 반영돼야 함).
   c. 다국어 번역(예: 영어) 실행 후 같은 셀을 클릭 — 편집이 안 되는지(텍스트 커서가 안 생기거나 수정해도 반영 안 되는지) 확인.
   d. 한국어(원본)으로 다시 전환 → 편집이 다시 가능해지는지 확인.
   e. 인쇄 테마를 바꾸거나 표 여백 값을 조절하는 도중에도 편집 중이던 내용이 유실되지 않는지 확인 (Red Team #6).
   f. `🖨️ PDF 미리보기 및 인쇄`로 인쇄 미리보기를 열어, 점선/호버 등 편집 UI 흔적이 전혀 없는 깔끔한 문서로 보이는지 확인.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-10으로 기록하고 완료 처리.
