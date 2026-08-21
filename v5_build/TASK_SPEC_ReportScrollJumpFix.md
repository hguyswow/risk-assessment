# TASK_SPEC — 표 여백(줄수/행높이) 조절 시 스크롤 위치가 최상단으로 튕기는 회귀 버그 수정

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-07
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만

---

## 1. Context (왜 필요한가)

WO-7(보고서 액션바 sticky 고정) 적용 후, 사용자가 스크롤을 내린 채 `줄수`/`행높이(px)` 값을 바꾸면 **화면이 그대로 최상단으로 튕겨 올라가버려서, 값이 실제로 바뀌는지 눈으로 확인할 수가 없고 "최대 치수가 어느 정도인지 감각도 안 잡힌다"**는 사용자 피드백이 접수되었다.

**원인 분석(감독모드 자체 확인, 새 조사가 아니라 직전 WO-7 설계 결함의 자기 수정)**: `syncReportPanelStickyOffset()`는 `.main-title-container`의 `getBoundingClientRect()`를 호출하는데, 이 호출은 브라우저가 **강제로 레이아웃을 즉시 재계산(synchronous reflow)**하게 만든다. 그런데 이 함수가 `generateReport()` 안에서 `dom.reportPreview.innerHTML = '';`로 보고서 내용을 **전부 지운 직후, 새 내용을 채우기 전**에 호출되고 있다([index.html:10654-10659](index.html#L10654-L10659)). 이 시점엔 문서가 순간적으로 텅 비어 매우 짧은 상태이므로, 강제 리플로우가 일어나면 브라우저가 현재 스크롤 위치를 새로(짧아진) 문서 높이에 맞춰 강제로 0 근처로 잘라버린다. 이후 내용이 다시 채워져 문서가 원래 길이로 돌아와도, 한 번 잘린 스크롤 위치는 자동으로 복구되지 않는다. **즉 WO-2의 표 여백 로직 자체는 멀쩡하며, WO-7에서 sticky 오프셋 동기화 호출을 잘못된 타이밍(내용을 지운 직후)에 넣은 것이 회귀 원인이다.**

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 문제의 호출 위치
`generateReport()` — [index.html:10649-10732](index.html#L10649-L10732) (살아있는 함수).
```js
function generateReport() {
    saveEdits();
    dom.selectionScreen.classList.add('hidden');
    dom.riskAssessmentScreen.classList.add('hidden');
    dom.reportPreviewScreen.classList.remove('hidden');
    dom.reportPreview.innerHTML = '';               // ← 내용 전부 삭제, 문서가 순간적으로 매우 짧아짐

    if (typeof syncReportPanelStickyOffset === 'function') {
        syncReportPanelStickyOffset();               // ← 바로 이 시점에 강제 리플로우 발생 → 스크롤 클램프
        setTimeout(syncReportPanelStickyOffset, 150);
    }
    ...
```
함수는 [index.html:10732](index.html#L10732)에서 닫히며, 그 직전([index.html:10724-10731](index.html#L10724-L10731))에 모든 보고서 페이지(`pageDiv`)와 사진대지(`pbDiv`)를 `dom.reportPreview`에 append하는 마지막 코드가 있다 — 즉 이 지점에서는 문서가 이미 다시 정상 높이로 돌아와 있다.

### 2.2 왜 "이동"만으로 충분한가
`syncReportPanelStickyOffset()`가 측정하는 값(`.main-title-container`의 `getBoundingClientRect().bottom`)은 보고서 내용(`#report-preview`)과 무관하게, 오직 상단 타이틀 바의 높이에만 좌우된다. 즉 이 함수를 **내용을 다 채운 뒤**에 호출해도 결과값은 동일하다 — 다만 호출 시점의 문서 높이가 달라질 뿐이다. 문서가 온전한 높이일 때 호출하면 강제 리플로우가 일어나도 스크롤 가능 영역이 줄어들지 않으므로 클램프가 발생하지 않는다.

---

## 3. 구체적인 구현 방법

### A. `syncReportPanelStickyOffset()` 호출을 함수 끝으로 이동
[index.html:10654-10659](index.html#L10654-L10659)에서 아래 블록을 **제거**:
```js
if (typeof syncReportPanelStickyOffset === 'function') {
    syncReportPanelStickyOffset();
    setTimeout(syncReportPanelStickyOffset, 150);
}
```
`dom.reportPreview.innerHTML = '';` 바로 다음 줄에서 삭제하고, 대신 [index.html:10731](index.html#L10731)(사진대지 `if` 블록이 끝나는 `}`)과 함수를 닫는 `}`([index.html:10732](index.html#L10732)) 사이에 동일한 블록을 그대로 옮겨 넣는다:
```js
            // ★ 사진대지 렌더링 추가
            if (photoBoardData && photoBoardData.enabled) {
                const pbDiv = document.createElement('div');
                pbDiv.className = 'photo-board-page';
                pbDiv.innerHTML = getPhotoBoardHTML(lang);
                dom.reportPreview.appendChild(pbDiv);
            }

            if (typeof syncReportPanelStickyOffset === 'function') {
                syncReportPanelStickyOffset();
                setTimeout(syncReportPanelStickyOffset, 150);
            }
        }
```
- 함수 내용(로직) 자체는 전혀 바꾸지 않는다 — **호출 위치만 이동**.
- `setTimeout(..., 150)` 지연 호출도 그대로 유지(창 폭 변경 등으로 레이아웃이 한 번 더 안정화될 시간을 주기 위한 기존 의도 보존).

---

## 4. Red Team 체크포인트

1. **이동 후에도 sticky 패널의 `top` 오프셋이 여전히 정확한가?** (보고서 화면 진입 시 타이틀 바 바로 아래에 정렬되는지 재확인 — WO-7의 기존 검증 시나리오를 다시 한번 통과해야 함.)
2. **스크롤을 내린 상태에서 `줄수`/`행높이(px)` 값을 바꿔도 더 이상 화면이 최상단으로 튕기지 않는가?** 이번 버그 리포트의 핵심 재현 시나리오 — 반드시 스크롤을 충분히 내린 상태에서 값을 바꿔가며 확인할 것.
3. **인쇄 테마 전환(`selectPrintTheme`)이나 다국어 번역 실행(`executeTranslation`)도 내부적으로 `generateReport()`를 다시 호출하는데, 이 경로들도 스크롤 점프가 함께 해결되는가?** (같은 함수를 고치는 것이므로 자동으로 해결되어야 하지만, 실제 재현 확인.)
4. 로직 자체(값 clamp, localStorage 저장, `getReportRowSettings()`)는 이번 수정과 무관하므로 절대 건드리지 말 것 — 순수하게 **호출 순서만** 바꾸는 작업이다.
5. 이번 작업 범위를 벗어나는 것(예: 스크롤 위치를 명시적으로 저장/복원하는 별도 로직 추가, sticky 오프셋 계산 방식 자체 변경 등)은 임의로 구현하지 말고 제안으로만 보고할 것 — 호출 위치 이동만으로 근본 원인이 해결되므로 추가 안전장치는 불필요하다.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 항목을 충분히 선택해 표가 화면보다 길어지도록 최종 보고서 생성 → 아래로 스크롤 → `행높이(px)` 값을 15에서 45 사이로 여러 번 바꿔가며, 화면이 튕기지 않고 스크롤 위치가 그대로 유지된 채 표의 빈 행 높이가 실시간으로 커지고 작아지는지 확인.
   b. `줄수`도 동일하게 스크롤 유지된 채 조절되는지 확인.
   c. 인쇄 테마를 바꾸거나 번역을 실행할 때도 스크롤이 유지되는지 확인 (Red Team #3).
   d. WO-7의 기존 시나리오(액션바가 타이틀 바 아래에 정확히 붙어 고정)가 여전히 정상인지 재확인 (Red Team #1).
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-8로 기록하고 완료 처리.
