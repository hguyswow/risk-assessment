# TASK_SPEC — 앱 시작 직후 "선택 완료 및 편집하기" 클릭 시 이전 내용이 안 뜨는 레이스 컨디션 수정

작성일: 2026-08-21
작성자: Claude (감독 모드 조사/설계)
대상 파일: `index.html`만

---

## 1. Context (왜 필요한가)

사용자 보고: "프로그램을 새로 시작하고 '선택 완료 및 편집' 버튼을 누르면 기존(지난 세션) 마지막 내용이 바로 뜨길 원한다. 그런데 현재는 아무것도 안 뜨고, 아무 항목이나 하나 추가해야 그제서야 이전 내용이 나타난다."

**감독모드 진단**: 앱 시작 시 `riskData`/`globalSelections`/`selectedGongjongs`를 IndexedDB에서 비동기로 복원하는 `checkAndShowInitialSetup()`과, 화면1의 "✏️ 선택 완료 및 편집하기" 버튼(`goto-edit-btn`)의 클릭 핸들러가 **서로를 기다리지 않는 구조**다:

1. `init()`이 동기적으로 `setupEventListeners()`(버튼 클릭 핸들러 연결 포함)를 실행한 뒤, **`await` 없이** `checkAndShowInitialSetup()`을 그냥 호출만 하고 넘어간다.
2. `checkAndShowInitialSetup()`은 내부에서 `await loadUserData()`(IndexedDB 읽기)로 인해 비동기로 완료된다 — 즉 `init()`이 이미 다 끝나서 버튼이 클릭 가능해진 뒤에도 한동안 계속 실행 중일 수 있다.
3. 사용자가 이 복원이 채 끝나기 전에 "선택 완료 및 편집하기"를 누르면, 그 순간 `globalSelections`/`selectedGongjongs`는 아직 초기값(빈 `Set`)이거나 복원 도중의 상태다. `showEditScreen()`은 편집화면으로 넘어가되(가드 조건에 따라), `populateEditScreen()`은 그 시점의(아직 비어있는) `globalSelections`만 훑으므로 표가 텅 빈 채로 렌더링된다.
4. 그 뒤 사용자가 매뉴얼 모드로 새 항목을 하나 추가하면(WO-1), 그 시점엔 `checkAndShowInitialSetup()`이 이미 완료되어 `globalSelections`가 이전 세션 항목들로 가득 찬 상태다. 추가 완료 핸들러가 `populateEditScreen()`을 다시 호출하므로, 새 항목 + 이전 항목들이 한꺼번에 나타난다 — 이게 바로 사용자가 본 "아무거나 추가해야 이전 내용이 나온다" 현상이다.

즉 **데이터 자체는 정상적으로 복원되고 있다.** 문제는 순서 보장이 없어서, 복원이 끝나기 전에 편집화면 진입 로직이 그 시점의 스냅샷만 보고 렌더링해버리는 것.

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 초기화 순서 — await 없는 fire-and-forget 호출
`init()` — [index.html:5516-5563](index.html#L5516-L5563 부근). 관련 줄:
```js
// 이벤트 리스너 설정
setupEventListeners();

// 저장된 사용자 데이터 확인 후 초기 설정 모달 표시
checkAndShowInitialSetup();
```
`checkAndShowInitialSetup()`은 `async` 함수인데 여기서 **`await` 없이 호출**되고 있다. 즉 `init()`은 이 복원 작업이 끝나길 기다리지 않고 즉시 반환된다.

### 2.2 비동기 복원 함수
`checkAndShowInitialSetup()` — [index.html:5626-5692](index.html#L5626-L5692 부근). `await loadUserData()`로 IndexedDB를 읽은 뒤(`loadUserData()` 자체도 `async`, [index.html:4608-4634](index.html#L4608-L4634 부근)), `riskData`, `globalSelections = new Set(userData.selections || [])`, `selectedGongjongs = new Set(userData.selectedGongjongs || [])` 등을 순서대로 재할당하고 마지막에 `startApplication()`을 호출한다.

### 2.3 초기값 — 복원 전에는 전부 비어있음/샘플 데이터
[index.html:4221](index.html#L4221) `let riskData = JSON.parse(JSON.stringify(baseRiskData));` (샘플 데이터), [index.html:4224](index.html#L4224) `let globalSelections = new Set();`, [index.html:4225](index.html#L4225) `let selectedGongjongs = new Set();` — 복원 전에는 전부 빈 값/샘플 데이터다.

### 2.4 문제의 진입점 — `showEditScreen()`
`showEditScreen(allowEmpty = false)` — [index.html:9160](index.html#L9160 부근). `globalSelections`/`selectedGongjongs`/`riskData`를 즉시(동기적으로) 읽어 `populateEditScreen()`을 호출한다. 이 함수는 위 3개 전역 변수가 **이미 최종 복원된 상태라고 그냥 가정**하고 있다 — 실제로 그런지 확인하는 로직이 없다.
`goto-edit-btn`의 클릭 핸들러(`() => showEditScreen()`, WO-4에서 이벤트 객체 누출 방지를 위해 화살표 함수로 감쌈)와, `#header-manual-mode-btn`의 클릭 핸들러(`showEditScreen(true)`, WO-4) 둘 다 이 함수를 호출하므로 동일한 레이스에 노출되어 있다.

### 2.5 왜 "항목 추가"가 문제를 "고쳐"주는 것처럼 보이는가
WO-1의 마법사 확인 핸들러(`initManualModeWizard()` 내부)는 새 항목을 `riskData`에 넣고 `globalSelections.add(newItem.id)`를 한 뒤 `populateEditScreen()`을 다시 호출한다. 이 시점엔 `checkAndShowInitialSetup()`이 이미 완료돼 있을 가능성이 매우 높다(사용자가 마법사 4단계를 다 채우는 데 걸리는 시간이 IndexedDB 읽기보다 훨씬 김) — 그래서 재렌더링 시 이전 세션 항목들이 전부 다시 보이는 것이다. 이는 **우연히 타이밍이 늦어져서 문제가 감춰지는 것**이지, 근본 수정이 아니다.

---

## 3. 구체적인 구현 방법

### A. 복원 완료를 추적 가능한 Promise로 노출
[index.html:5562](index.html#L5562) 부근:
```js
// 변경 전: checkAndShowInitialSetup();
window.appDataReadyPromise = checkAndShowInitialSetup();
```
(`checkAndShowInitialSetup()`은 이미 `async function`이므로 호출 시 자동으로 Promise를 반환한다 — 그 반환값을 전역에서 참조 가능하게 담아두기만 하면 된다. 함수 내부 로직은 전혀 손댈 필요 없음.)

### B. `showEditScreen()`이 그 Promise를 기다리도록 수정
[index.html:9160](index.html#L9160) 부근을 `async` 함수로 변경:
```js
async function showEditScreen(allowEmpty = false) {
    if (window.appDataReadyPromise) {
        try {
            await window.appDataReadyPromise;
        } catch (e) {
            console.error('앱 데이터 복원 대기 중 오류(무시하고 계속 진행):', e);
        }
    }

    if (!allowEmpty && globalSelections.size === 0 && selectedGongjongs.size === 0) {
        alert('보고서에 포함할 위험요인이나 공종을 하나 이상 선택해주세요.');
        return;
    }
    // ... 이하 기존 로직 100% 동일하게 유지 ...
}
```
- `showEditScreen`을 `async`로 바꿔도 **기존 호출부는 전혀 손댈 필요 없다** — `() => showEditScreen()`, `showEditScreen(true)`, `showEditScreen()` 등 전부 반환되는 Promise를 그냥 무시하고 호출하는 형태라, 함수가 `async`가 되어도 호출 문법은 동일하게 동작한다(그냥 "fire and forget"으로 호출되고, 내부적으로 완료될 때까지 기다렸다가 DOM을 갱신할 뿐).
- `window.appDataReadyPromise`가 아직 없는 극히 이례적인 상황(예: 초기화 흐름이 바뀌어 이 변수가 설정되기 전에 호출되는 경우)에도 안전하게 그냥 통과하도록 `if (window.appDataReadyPromise)` 가드를 둔다.
- `try/catch`로 감싸는 이유: `checkAndShowInitialSetup()`이 내부적으로 이미 모든 에러를 자체적으로 처리하고 있지만(2.2 참고), 혹시 모를 reject 상황에서도 `showEditScreen()`이 멈추지 않고 계속 진행되도록 방어.

---

## 4. Red Team 체크포인트

1. **정말로 레이스가 원인인지, 다른 원인(예: `riskData`/`globalSelections` 복원 자체가 실패하는 로직 버그)은 아닌지 착수 전에 한 번 더 확인할 것.** 확인 방법: `loadUserData()` 안에 임시로 `await new Promise(r => setTimeout(r, 2000));`을 넣어 복원을 2초 지연시킨 뒤, 그 2초 안에 "선택 완료 및 편집"을 눌러 정말 빈 화면이 뜨는지, 2초 뒤 다시 들어가면 정상인지 재현해볼 것(재현 후 반드시 지연 코드는 제거).
2. **`showEditScreen`을 `async`로 바꾸는 것이 기존 호출부(`goto-edit-btn`, `#header-manual-mode-btn`, 그 외 직접 호출부)를 깨뜨리지 않는가?** 전부 반환값을 사용하지 않는 형태인지 재확인.
3. **`window.appDataReadyPromise`가 reject되는 경우(예: IndexedDB 완전 접근 불가)에도 `showEditScreen()`이 무한 대기하지 않고 계속 진행되는가?** (`checkAndShowInitialSetup()` 자체가 이미 모든 내부 에러를 잡아 항상 정상적으로 resolve하도록 설계돼 있음 — 2.2 참고 — 하지만 `try/catch`로 한 번 더 방어.)
4. **앱이 완전히 로드된 후(복원이 끝난 뒤) 클릭하는 일반적인 경우에는 체감 지연이 전혀 없는가?** (이미 resolve된 Promise를 `await`하는 것은 사실상 즉시 통과되므로 정상 사용에는 지장이 없어야 한다.)
5. **`checkAndShowInitialSetup()` 함수 내부 로직 자체는 한 글자도 건드리지 않았는가?** — 이번 수정은 순수하게 "호출부에서 Promise를 잡아두고, 소비하는 쪽에서 기다리기"만 하는 것이지 복원 로직 자체를 바꾸는 게 아니다.
6. 이번 작업 범위를 벗어나는 것(예: 로딩 스피너 UI 추가, `init()`의 다른 흐름 변경, 트리 화면 자체의 로딩 상태 처리 등)은 임의로 구현하지 말고 제안으로만 보고할 것.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 항목을 몇 개 선택/편집해서 저장된 상태를 만들어 둔다(정상적인 사용 흐름으로 한 번 저장).
   b. 앱을 완전히 종료했다가 재시작한다.
   c. 화면이 뜨자마자(트리가 그려지기를 기다리지 않고) 최대한 빠르게 "✏️ 선택 완료 및 편집하기"를 클릭 — 예전 세션의 항목들이 바로 표에 나타나는지 확인(더 이상 빈 화면이 뜨지 않아야 함).
   d. 반대로 저장된 데이터가 하나도 없는 완전히 새 설치 상태(또는 데이터를 초기화한 상태)에서 아무것도 선택하지 않고 "선택 완료 및 편집하기"를 누르면 여전히 "하나 이상 선택해주세요" 경고가 정상적으로 뜨는지 확인(회귀 확인 — Red Team #2와 연결).
   e. `🛠️ 매뉴얼로 시작` 버튼(WO-4)도 동일하게, 앱 시작 직후 빠르게 눌러도 정상적으로(매뉴얼 모드 ON + 편집화면, 이전 항목이 있다면 그것도 함께) 진입하는지 확인.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 새 항목(WO-13)으로 기록하고 완료 처리.
