# TASK_SPEC — WO-14 (2단계, 실제 수정): showEditScreen() DOM 삽입 크래시로 편집화면이 비어 보이는 문제 수정

작성일: 2026-08-21
작성자: Claude (감독 모드 조사/설계)
대상 파일: `index.html`만

---

## 1. Context (왜 필요한가) — 1단계 진단으로 확정된 근본 원인

WO-14 1단계 진단 로그로 근본 원인이 완전히 확정됐다. **데이터 복원 자체는 항상 정상 동작**한다(`checkAndShowInitialSetup()` → `globalSelections` 4개 정상 반영, 로그 `③ 최종 반영` 확인됨). 문제는 그 다음 `showEditScreen()` 내부에서 발생하는 **처리되지 않은 DOM 예외**다:

```
Uncaught (in promise) NotFoundError: Failed to execute 'insertBefore' on 'Node':
The node before which the new node is to be inserted is not a child of this node.
```

이 예외가 `populateEditScreen()`(표를 실제로 그리는 함수, `showEditScreen()` 안에서 이 삽입 코드보다 나중에 호출됨)에 도달하기 **전에** 스크립트를 중단시켜서, 데이터는 메모리에 다 있는데 표는 영영 그려지지 않는다. 이게 "선택 완료 및 편집" 클릭 시 빈 화면이 뜨는 진짜 원인이다.

("아무 항목이나 추가하면 그제서야 이전 내용이 나온다"던 원래 증상도 이걸로 설명된다 — 매뉴얼 모드 마법사의 완료 콜백은 `populateEditScreen()`을 이 크래시 지점을 거치지 않고 **직접** 호출하기 때문에 우회로 성공했던 것.)

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 문제의 코드
[index.html:9210-9307](index.html#L9210-L9307), `showEditScreen()` 내부, `if (!document.querySelector('.grade-limit-settings'))` 블록:

```js
const container = document.getElementById('risk-assessment-screen');   // L9213
...
const tableContainer = document.querySelector('#risk-items-container-table');  // L9297
if (tableContainer && tableContainer.parentNode) {
    tableContainer.parentNode.insertBefore(settingDiv, tableContainer);
} else if (container) {
    const h2 = container.querySelector('h2');
    if (h2 && h2.nextSibling) {
        container.insertBefore(settingDiv, h2.nextSibling);   // 💥 여기서 크래시
    } else {
        container.appendChild(settingDiv);
    }
}
```

### 2.2 왜 항상 이 경로로 빠지는가
`#risk-items-container-table`이라는 id를 가진 엘리먼트는 **파일 전체에 이 querySelector 자기 자신 한 곳 말고는 존재하지 않는다** (grep 확인 완료). 즉 `tableContainer`는 언제나 `null`이고, 첫 번째 `if` 분기는 절대 성공하지 않으며 항상 `else if (container)` 폴백으로 빠진다.

### 2.3 왜 항상 크래시하는가 — 진짜 DOM 구조
[index.html:3290-3296](index.html#L3290-L3296):
```html
<div id="risk-assessment-screen" class="container hidden">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2 style="margin: 0;">✏️ 2. 선택 항목 편집</h2>
        <label ...>...매뉴얼 모드...</label>
    </div>
    <div class="editing-table-wrapper">
```
`h2`는 `#risk-assessment-screen`(`container`)의 **직계 자식이 아니다** — 그 안의 flex `<div>` 래퍼 자식이다. 따라서 `h2.parentNode`는 그 `<div>`이지 `container`가 아니다. `container.insertBefore(settingDiv, h2.nextSibling)`를 호출하면 두 번째 인자(`h2.nextSibling`, 즉 매뉴얼모드 `<label>`)가 `container`의 자식이 아니므로 브라우저가 `NotFoundError`를 던진다.

### 2.4 왜 딱 한 번(첫 클릭)만 문제가 되는 것처럼 보였는가
이 블록 전체가 `if (!document.querySelector('.grade-limit-settings'))`로 감싸여 있다 — 즉 앱 켜고 나서 딱 한 번만 실행 시도된다. 그런데 크래시로 인해 `settingDiv`가 실제로 DOM에 붙는 데 항상 실패하므로, `.grade-limit-settings`는 영원히 생기지 않는다 → `showEditScreen()`을 다시 호출할 때마다(화면1로 돌아갔다 재진입 등) **매번 다시 크래시한다.**

---

## 3. 구체적인 구현 방법

### A. `insertBefore` 대상을 실제 부모로 정정 + 전체를 try-catch로 방어

[index.html:9296-9307](index.html#L9296-L9307) 블록을 아래로 교체:

```js
// 테이블 바로 위에 삽입
try {
    const tableContainer = document.querySelector('#risk-items-container-table');
    if (tableContainer && tableContainer.parentNode) {
        tableContainer.parentNode.insertBefore(settingDiv, tableContainer);
    } else if (container) {
        const h2 = container.querySelector('h2');
        if (h2 && h2.parentNode) {
            h2.parentNode.insertBefore(settingDiv, h2.nextSibling);
        } else {
            container.appendChild(settingDiv);
        }
    }
} catch (e) {
    console.error('[showEditScreen] 위험성 랜덤 설정 UI 삽입 실패(무시하고 계속 진행):', e);
}
```

바뀐 것: `container.insertBefore(settingDiv, h2.nextSibling)` → `h2.parentNode.insertBefore(settingDiv, h2.nextSibling)` (실제 부모 기준으로 삽입하므로 더 이상 `NotFoundError`가 나지 않는다). 그리고 이 삽입 로직 전체를 `try-catch`로 감싼다 — 이 UI(위험성 랜덤 설정 박스)는 부가 기능이므로, 혹시 앞으로 다른 이유로 DOM 구조가 또 바뀌어도 이 삽입 하나 때문에 `populateEditScreen()` 호출 자체가 막히는 일이 다시는 없도록 한다.

### B. WO-14 1단계에서 추가한 임시 진단 로그 전부 제거

`TASK_SPEC_EditScreenStillEmpty_Diagnostic.md` 지시로 추가했던 `[WO14진단] ①~⑥` `console.log`/`console.error` 라인들을 전부 제거한다(원인이 확정됐으므로 더 이상 필요 없음). 위치: `checkAndShowInitialSetup()` 내부 4곳, `populateEditScreen()` 시작부/매칭결과 계산부 2곳. 다른 로직·변수는 그대로 둔다(로그 줄만 삭제).

---

## 4. Red Team 체크포인트

1. **정말 이 수정만으로 편집화면에 이전 데이터가 뜨는가?** — `h2.parentNode.insertBefore(...)`가 실제로 예외 없이 통과하고, 그 아래 `populateEditScreen()` 호출까지 정상 도달하는지 콘솔에 에러가 없는 것으로 확인.
2. **`settingDiv`(위험성 랜덤 설정 박스)가 화면에서 원래 의도한 위치(표 바로 위, 헤더 바로 아래)에 여전히 자연스럽게 보이는가?** — 부모가 `container`에서 `h2`의 실제 부모(flex 헤더 `div`)로 바뀌었으므로 시각적 위치가 미묘하게 달라질 수 있음. 레이아웃이 깨지지 않는지 육안 확인.
3. **`.grade-limit-settings` 가드(한 번만 삽입) 로직 자체는 이번 수정과 무관하게 정상 동작하는가?** — 즉 이제 크래시가 안 나므로 삽입이 실제로 성공하고, 이후 `showEditScreen()`을 다시 호출해도 중복 삽입되지 않는지 확인.
4. **try-catch로 감쌌다고 해서 원래 존재하던 다른 정상 동작(랜덤 적용 버튼, %입력, `recalcPct` 등 3310번 줄 이후 로직)이 실행 안 되는 경로가 생기지 않는가?** — try 블록은 삽입 부분만 감싸고, 그 이후의 퍼센트 로직 코드는 try 블록 밖에 그대로 남아있어야 한다(이 스펙의 교체 범위는 9296-9307 줄까지만).
5. WO14진단 로그를 지우면서 실수로 그 옆의 실제 로직(`globalSelections = new Set(...)` 등)까지 지우지 않았는지 재확인.
6. 이번 범위를 벗어나는 것(예: `#risk-items-container-table`을 실제로 만들어서 첫 번째 분기를 살리는 것, `.grade-limit-settings` UI 자체의 재배치/리디자인)은 임의로 하지 말고 제안으로만 보고.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 → 완전 종료 → 재시작 → 콘솔 열어둔 채로 즉시 "✏️ 선택 완료 및 편집하기" 클릭.
   - 콘솔에 `NotFoundError`가 더 이상 나타나지 않는지 확인.
   - 표에 이전 세션의 선택 항목(현재 `user_data.json` 기준 4개)이 실제로 렌더링되는지 확인.
3. 화면1로 돌아갔다가 다시 "선택 완료 및 편집하기"를 눌러도(=`showEditScreen()` 재호출) 정상적으로 표가 뜨는지 확인 (가드 로직 회귀 확인).
4. `🛠️ 매뉴얼로 시작` 버튼(WO-4, `showEditScreen(true)`)도 동일하게 크래시 없이 진입하는지 확인.
5. 저장된 데이터가 전혀 없는 상태(빈 selections)에서 아무것도 선택하지 않고 "선택 완료 및 편집하기"를 누르면 여전히 "하나 이상 선택해주세요" 경고가 정상적으로 뜨는지 확인(회귀 확인).
6. 위 전부 통과 후 `WORK_ORDER_master.md`의 WO-13/WO-14를 완료로 갱신.
