# TASK_SPEC — WO-14 (진단 전용, 1단계): 편집화면 복원이 여전히 비어있는 근본 원인 확인

작성일: 2026-08-21
작성자: Claude (감독 모드 조사/설계)
대상 파일: `index.html`만
**주의: 이번 단계는 진단(로그 추가)만 한다. 동작을 바꾸는 수정은 하지 않는다.**

---

## 1. Context (왜 필요한가)

WO-13에서 "복원(`checkAndShowInitialSetup`)이 끝나기 전에 편집화면을 그려버리는 레이스"를 고쳤다(`window.appDataReadyPromise` + `showEditScreen()`에서 await). 코드 대조 결과 이 수정 자체는 스펙대로 정확히 반영돼 있다.

그런데 사용자가 `npm start`(개발 모드)로 재검증한 결과, 증상이 **똑같다** — 앱을 새로 시작하고 "선택 완료 및 편집하기"를 누르면 편집화면이 완전히 빈 채로 뜬다. `user_data.json`에는 실제로 `selections` 3건, `riskData` 40개 공종이 정상적으로 들어있는 것을 직접 확인했으므로 "애초에 저장된 데이터가 없다"는 아니다.

이는 WO-13이 고친 "타이밍" 문제가 아니라, **복원 로직 자체가 최종적으로 실패하고 있다**는 뜻이다. 감독모드가 코드를 정독해 가장 유력한 가설을 하나 세웠지만, 정적 분석만으로는 100% 확정할 수 없어 실제 실행 중 콘솔 로그로 확인이 필요하다.

## 2. 유력 가설 (확정 아님 — 로그로 검증 대상)

`checkAndShowInitialSetup()` ([index.html:5626-5692](index.html#L5626-L5692)):
```js
let userData = await loadUserData();               // ① IndexedDB
if (!userData || !userData.riskData) {              // ② 이 조건일 때만 파일 폴백
    userData = loadFromFile();
    ...
}
```
이 폴백 조건은 IndexedDB 결과가 **완전히 없을 때만** 파일(`user_data.json`)을 본다. 만약 IndexedDB에 `riskData`가 "존재는 하지만"(예: 과거의 빈 초기 상태, 또는 `selections`가 빈 배열인 오래된 스냅샷) 남아있다면, 이 조건은 `false`가 되어 파일 폴백은 아예 시도되지 않고, IndexedDB의 그 오래된/빈 값을 그대로 써버린다.

왜 이런 어긋남이 생길 수 있는가: `saveUserData()` ([index.html:4545-4605](index.html#L4545-L4605))는 파일 저장(①)과 IndexedDB 저장(②)을 각각 try-catch로 분리해서 수행한다. IndexedDB 저장만 조용히 실패해도(`idbSuccess=false`) 파일 저장이 성공했으면(`fileSuccess=true`) 토스트로 "⚠️ 로컬 백업 완료 - DB 에러"만 띄우고 앱은 계속 정상 동작하는 것처럼 보인다 — 사용자가 이 경고 토스트를 놓쳤을 가능성이 있다. 이 경우 파일에는 최신 데이터가, IndexedDB에는 오래된/빈 데이터가 남는 어긋남이 생긴다.

감독모드가 `%APPDATA%\risk-assessment-app\IndexedDB\file__0.indexeddb.leveldb`의 최신 로그 파일을 바이트 단위로 검사했을 때 `currentUserData`/`riskData`/`selections` 등 예상 문자열을 전혀 찾지 못했다 — 이는 위 가설과 일치할 수 있지만, LevelDB의 내부 압축/프레이밍 때문에 이 방법 자체가 위음성(실제로는 있는데 못 찾음)일 수 있어 **정적 증거로 확정하지 않는다.**

## 3. 이번 단계에서 할 일 — 임시 진단 로그만 추가

`checkAndShowInitialSetup()` 내부에, 동작을 전혀 바꾸지 않고 다음 지점에 `console.log`만 추가한다:

1. `let userData = await loadUserData();` 바로 다음 줄:
```js
console.log('[WO14진단] ① IndexedDB 로드 결과:', userData ? {
    hasRiskData: !!userData.riskData,
    riskDataKeys: userData.riskData ? Object.keys(userData.riskData).length : 0,
    selections: (userData.selections || []).length,
    modifiedAt: userData.modifiedAt
} : null);
```

2. 파일 폴백이 실제로 실행되는 `if (!userData || !userData.riskData) { ... }` 블록 안, `userData = loadFromFile();` 다음 줄:
```js
console.log('[WO14진단] ② 파일 폴백 결과:', userData ? {
    hasRiskData: !!userData.riskData,
    riskDataKeys: userData.riskData ? Object.keys(userData.riskData).length : 0,
    selections: (userData.selections || []).length,
    modifiedAt: userData.modifiedAt
} : null);
```

3. `globalSelections = new Set(userData.selections || []);` 다음 줄:
```js
console.log('[WO14진단] ③ 최종 반영:', {
    globalSelectionsSize: globalSelections.size,
    selectedGongjongsSize: selectedGongjongs.size,
    riskDataTopKeys: Object.keys(riskData).length
});
```

4. `catch (error)` 블록 맨 앞:
```js
console.error('[WO14진단] ④ catch 진입 — 복원 도중 예외 발생:', error);
```

그 외 `showEditScreen()`, `populateEditScreen()` 등 다른 함수는 **일절 건드리지 않는다.**

## 4. 재현 및 보고 절차

1. `npm start`로 앱 실행 (개발자 도구 콘솔 열어둘 것: `Ctrl+Shift+I` 등).
2. 완전히 종료 후 다시 `npm start`로 재시작.
3. 화면이 뜨자마자 "✏️ 선택 완료 및 편집하기"를 눌러 빈 화면이 재현되는지 확인.
4. **콘솔에 찍힌 `[WO14진단]` 로그 4줄(또는 그중 실제로 찍힌 것)을 한 글자도 요약/생략하지 말고 그대로 복사해서 보고서에 포함.**
5. 이번 단계는 진단 로그 추가만 하는 것이므로, Rule 9 "예상 접근/Red Team" 보고는 간단히(로그 추가가 기존 로직에 영향 없음만 확인) 해도 됨 — 이번엔 실제 수정 제안(③,④ 기능향상/안정화 제안)은 하지 말고 로그 결과만 보고할 것.

## 5. Red Team 체크포인트

1. 추가하는 것은 오직 `console.log`/`console.error` 4줄뿐이며, 기존 변수 할당·제어 흐름·리턴값에 **전혀 영향을 주지 않는지** 재확인.
2. 이 로그가 프로덕션 빌드에 남아있어도 기능상 문제는 없지만(콘솔 출력일 뿐), 원인 확정 후 실제 수정 스펙에서 정리(제거 또는 유지 결정)할 것이므로 이번 단계에서 미리 지우지 말 것.

## 6. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. 위 "4. 재현 및 보고 절차"의 콘솔 로그 원문을 그대로 보고서에 첨부.
3. 감독모드가 로그를 분석해 근본 원인을 확정한 뒤, 실제 수정을 위한 후속 TASK_SPEC(WO-14 2단계)을 별도로 작성한다. **이번 스펙만으로는 완료 처리하지 않는다.**
