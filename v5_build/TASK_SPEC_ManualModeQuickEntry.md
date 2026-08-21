# TASK_SPEC — 화면1 헤더 "🛠️ 매뉴얼" 버튼: 트리 선택 없이 매뉴얼 모드로 즉시 진입

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-06
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만

---

## 1. Context (왜 필요한가)

사용자가 실제 앱을 써보고 나서, "생각해보니 오히려 직관적인 인터페이스라서 초보자들이 사용하기 쉬운 방법일 수 있다"며 다음을 요청했다: 화면1(선택 화면) 상단 헤더의 `📂 불러오기` 버튼 오른쪽에 새 버튼을 만들고, 누르면 트리에서 항목을 하나도 선택하지 않은 상태여도 곧바로 편집화면(`#risk-assessment-screen`)으로 이동하면서 매뉴얼 모드가 켜진 상태로 시작하게 한다. 즉, 복잡한 트리 탐색 없이 "매뉴얼 버튼 → 빈 편집화면(매뉴얼 모드 ON) → ➕ 새 항목 추가 마법사로 하나씩 채워나가기"라는 완전히 새로운 진입 경로를 만드는 것.

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 버튼 삽입 위치
화면1 헤더의 우측 버튼 그룹 — 살아있는 코드는 [index.html:3103-3112](index.html#L3103-L3112) (바로 위 [index.html:3095-3102](index.html#L3095-L3102)는 `[기존 코드 백업]`으로 주석 처리된 죽은 코드이므로 건드리지 말 것). 순서: `🤖 AI 기능 활성화` 체크박스 → `🤖 AI 생성` → `🖊️ 서명설정` → `📂 불러오기`([index.html:3110](index.html#L3110)). 사용자가 스크린샷에서 화살표로 가리킨 위치는 이 `📂 불러오기` 버튼 바로 오른쪽.

### 2.2 편집화면 진입 로직과 두 가지 차단 지점
`showEditScreen()` — [index.html:9106-9336](index.html#L9106-L9336). `goto-edit-btn`(화면1의 "✏️ 선택 완료 및 편집하기" 버튼)의 클릭 핸들러로 연결됨 — [index.html:9824](index.html#L9824) 부근 `document.getElementById('goto-edit-btn').onclick = showEditScreen;`(정확한 현재 줄 번호는 착수 시 재확인).

**차단 지점 A**: [index.html:9107-9110](index.html#L9107-L9110)
```js
if (globalSelections.size === 0 && selectedGongjongs.size === 0) {
    alert('보고서에 포함할 위험요인이나 공종을 하나 이상 선택해주세요.');
    return;
}
```
새 버튼은 이 가드를 우회해서 빈 상태로도 편집화면에 진입할 수 있어야 한다.

**차단 지점 B (더 중요, 놓치기 쉬움)**: `showEditScreen()`은 함수 끝([index.html:9335](index.html#L9335))에서 무조건 `populateEditScreen()`을 호출하는데, 그 함수 시작부([index.html:9792-9798](index.html#L9792-L9798))에 다음과 같은 **"임시" 디버그 알림이 아직 살아있다**:
```js
function populateEditScreen() {
    // 디버깅용 로그 및 알림 (임시)
    console.log("populateEditScreen called. GlobalSelections size:", globalSelections.size);

    if (globalSelections.size === 0) {
        alert("선택된 항목이 없습니다! (GlobalSelections size is 0)\n화면 왼쪽 트리에서 항목들을 체크했는지 확인해주세요.");
    }
    ...
```
차단 지점 A를 우회해도 이 알림이 그대로 남아있으면, 매뉴얼 버튼을 누를 때마다 "선택된 항목이 없습니다!" 경고창이 튀어나와 새 기능의 UX를 망친다. **이 디버그 블록(주석 2줄 포함, 알림 블록 전체)은 이번 작업에서 반드시 제거해야 한다.** (현재 구조상 `showEditScreen()`의 차단 지점 A가 항상 먼저 막기 때문에 이 alert는 사실상 도달 불가능한 죽은 코드였다 — 이번에 A를 우회하는 새 경로가 생기면서 처음으로 실제 도달 가능해지므로 반드시 같이 정리해야 한다.)

### 2.3 함수 시그니처 변경 시 흔한 함정 (Red Team 사전 경고)
`document.getElementById('goto-edit-btn').onclick = showEditScreen;` 형태로 함수 참조를 그대로 꽂아두면, 브라우저가 클릭 시 `MouseEvent` 객체를 `showEditScreen`의 **첫 번째 인자**로 자동 전달한다. 만약 `showEditScreen(allowEmpty = false)`처럼 매개변수를 추가하면, 기존 `goto-edit-btn`도 클릭할 때마다 `allowEmpty`에 `MouseEvent`(항상 truthy)가 들어가 **차단 지점 A가 무력화되어, 기존 정상 동작(선택 없이 편집화면 진입 차단)까지 같이 깨진다.** 반드시 `onclick = () => showEditScreen();` 형태로 감싸서 이벤트 객체가 새어 들어가지 않게 해야 한다.

### 2.4 매뉴얼 모드 토글 재사용
`#manual-mode-toggle-checkbox`의 `change` 이벤트 핸들러(`initManualModeWizard()` 내부)가 이미 "localStorage 저장 + `#risk-assessment-screen`에 `.manual-mode-active` 클래스 토글"을 전담하고 있다. 새 버튼에서 이 로직을 중복 구현하지 말고, 체크박스를 `checked = true`로 설정한 뒤 `dispatchEvent(new Event('change'))`로 기존 핸들러를 그대로 재사용할 것.

---

## 3. 구체적인 구현 방법

### A. `showEditScreen()`에 `allowEmpty` 매개변수 추가
```js
function showEditScreen(allowEmpty = false) {
    if (!allowEmpty && globalSelections.size === 0 && selectedGongjongs.size === 0) {
        alert('보고서에 포함할 위험요인이나 공종을 하나 이상 선택해주세요.');
        return;
    }
    ... (이하 기존 로직 그대로)
```

### B. 기존 `goto-edit-btn` 바인딩을 이벤트 인자 누출 방지 형태로 수정
```js
document.getElementById('goto-edit-btn').onclick = () => showEditScreen();
```

### C. `populateEditScreen()`의 디버그 alert/log 블록 제거
[index.html:9793-9798](index.html#L9793-L9798)의 `// 디버깅용 로그 및 알림 (임시)` 주석, `console.log(...)`, `if (globalSelections.size === 0) { alert(...) }` 블록을 통째로 삭제. (바로 아래 `if (failCount > 0) { alert(...) }` 등 다른 알림 로직은 그대로 유지 — 이건 실제 조회 실패 시 나오는 유효한 에러 알림이므로 건드리지 말 것.)

### D. 새 버튼 마크업 추가
[index.html:3110](index.html#L3110) `📂 불러오기` 버튼 바로 다음에:
```html
<button id="header-manual-mode-btn" class="btn-gray" title="트리 선택 없이 매뉴얼 모드로 바로 시작합니다" style="white-space: nowrap !important; flex-shrink: 0 !important; padding: 0 12px !important; background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important; color: #ffffff !important;">🛠️ 매뉴얼로 시작</button>
```
(배경색은 기존 매뉴얼 모드 브랜드 컬러 `#8b5cf6`/`#7c3aed`와 통일 — 매뉴얼 모드 토글, 마법사 확인 버튼, `manual.html` STEP 3-1 헤딩에서 이미 쓰인 톤.)

### E. 새 버튼 클릭 핸들러
기존 헤더 버튼들이 바인딩되는 위치(예: `open-ai-generator-btn`, `header-load-btn` 등이 바인딩되는 `init()` 함수 안)에 함께 추가:
```js
const headerManualModeBtn = document.getElementById('header-manual-mode-btn');
if (headerManualModeBtn) {
    headerManualModeBtn.onclick = () => {
        const manualToggle = document.getElementById('manual-mode-toggle-checkbox');
        if (manualToggle && !manualToggle.checked) {
            manualToggle.checked = true;
            manualToggle.dispatchEvent(new Event('change'));
        }
        showEditScreen(true);
    };
}
```
- 이미 매뉴얼 모드가 켜져 있으면(재방문 등) 다시 끄지 않고 그대로 둔다(`!manualToggle.checked`로만 분기).
- 이미 트리에서 항목을 선택해둔 상태에서 이 버튼을 눌러도 기존 선택은 그대로 유지된 채 편집화면으로 들어간다 — 특별히 막거나 초기화할 필요 없음.
- 마법사 모달을 자동으로 열지는 않는다. "매뉴얼 모드가 켜진 편집화면"까지만 이동시키고, `➕ 새 항목 추가` 클릭은 사용자가 직접 하게 둔다(요청 문구가 "매뉴얼 모드 화면으로 진행"이지 "마법사를 열어라"가 아님).

---

## 4. Red Team 체크포인트

1. **`showEditScreen`에 매개변수를 추가하면서 기존 `goto-edit-btn`의 동작이 깨지지 않는가?** 반드시 화살표 함수로 감싸 이벤트 객체가 `allowEmpty`로 새어 들어가지 않는지 확인(2.3 참고). 실제로 트리에서 아무것도 선택하지 않은 채 기존 "✏️ 선택 완료 및 편집하기" 버튼을 눌러 여전히 경고창이 뜨고 편집화면으로 넘어가지 않는지 반드시 재현 테스트할 것.
2. **`populateEditScreen()`의 디버그 alert 제거 시, 바로 아래 있는 다른 유효한 알림(`failCount > 0` 등 조회 실패 알림)까지 실수로 같이 지우지 않았는가?** 정확히 2.2에 인용된 블록만 삭제.
3. 매뉴얼 버튼으로 빈 상태 진입 시 편집화면 표(`#risk-items-container-tbody`)가 완전히 빈 채로(크래시 없이) 정상 렌더링되는가? (`populateEditScreen()`이 `itemsByGongjong`이 빈 객체일 때 `for...in` 루프를 그냥 안 돌고 넘어가는지 확인.)
4. 매뉴얼 버튼 클릭 시 `#manual-mode-toggle-checkbox`의 기존 `change` 핸들러가 실제로 실행되어 `localStorage`(`manualModeEnabled`)와 `.manual-mode-active` 클래스가 정상 반영되는가? (새 코드에서 로직을 중복 구현하지 않고 기존 핸들러를 재사용했는지 확인 — 2.4 참고.)
5. 새 버튼 스타일이 `header-buttons` 플렉스 행 안에서 다른 3개 버튼과 함께 줄바꿈 없이 자연스럽게 배치되는가(기존 버튼들처럼 `white-space: nowrap; flex-shrink: 0` 유지).
6. 이번 작업 범위를 벗어나는 것(예: 마법사 자동 오픈, 트리 화면 자체의 다른 개편 등)은 임의로 구현하지 말고 제안으로만 보고할 것.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 화면1에서 아무 항목도 선택하지 않은 채 새 `🛠️ 매뉴얼로 시작` 버튼 클릭 → 편집화면으로 이동하고, 표가 비어있는 채(에러/알림 없이) 뜨는지, 상단 `🛠️ 매뉴얼 모드` 토글이 자동으로 ON 상태인지, `➕ 새 항목 추가 (매뉴얼)` 버튼이 보이는지 확인.
   b. `⬅️ 선택 화면으로` 눌러 되돌아간 뒤, 이번엔 트리에서 항목을 하나도 선택하지 않고 기존 `✏️ 선택 완료 및 편집하기` 버튼을 클릭 → 여전히 "하나 이상 선택해주세요" 경고가 뜨고 편집화면으로 넘어가지 않는지(회귀 확인, Red Team #1).
   c. 트리에서 항목을 몇 개 선택한 뒤 새 `🛠️ 매뉴얼로 시작` 버튼을 클릭 → 선택했던 항목들이 그대로 편집화면에 나타나면서 매뉴얼 모드도 켜지는지 확인.
   d. (b)에서 정상적으로 넘어간 경우와, 이미 매뉴얼 모드가 켜진 상태에서 새 버튼을 다시 누르는 경우 모두 예외 없이 동작하는지 확인.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-4로 기록하고 완료 처리.
