# TASK_SPEC — WO-16 (WO-15 긴급 후속): 옛 input 리스너가 세부작업명/위험세부분류에 가짜 속성을 남겨 이동 로직을 무력화하는 문제 수정

작성일: 2026-08-21
작성자: Claude (감독 모드 조사/설계)
대상 파일: `index.html`만

---

## 1. Context (왜 필요한가)

WO-15(`TASK_SPEC_EditScreenCategoryFieldSave.md`)를 구현·검증했으나, 사용자가 실제 앱에서 재확인한 결과 **증상이 그대로 재현됨** — "위험세부분류"를 고쳐도 다시 원래 값으로 되돌아감. WO-15 자체의 코드(`moveItemToNewCategory`, `saveEdits()`의 분기)는 정확하지만, **다른 코드가 그 분기에 도달하기 전에 먼저 문제를 일으키고 있었다.**

## 2. 확인된 사실 (근본 원인, 파일:줄번호)

`dom.riskItemsTbody`에는 WO-15가 건드린 `saveEdits()`(체크포인트성 저장)와는 **별개로**, 훨씬 이전부터 있던 실시간 `input` 리스너가 하나 더 있다 — [index.html:8108-8172](index.html#L8108-L8172), 그중 문제 지점은 [index.html:8164-8171](index.html#L8164-L8171):

```js
// 텍스트 필드 변경 내용도 동기화 (세부작업명 등)
if (target.tagName === 'DIV' && target.isContentEditable) {
    const field = target.dataset.field;
    const item = findItemRefById(tr.dataset.id);
    if (item && field) {
        item[field] = target.innerText;   // ← 모든 contenteditable 필드에 조건 없이 실행
    }
}
```

이 리스너는 **모든 키 입력마다** 실행되며, `field`가 무엇이든(세부작업명/위험세부분류 포함) `hasOwnProperty` 검사 없이 무조건 `item[field] = ...`를 실행한다. 그 결과:

1. "위험세부분류" 칸에 한 글자만 쳐도 즉시 `item['위험세부분류'] = "..."`라는 **원래 없던 가짜 속성**이 항목 객체에 생겨버린다.
2. 이후(30초 자동저장 또는 화면 전환 시) `saveEdits()`가 실행될 때, `itemRef.hasOwnProperty('위험세부분류')`가 이제 **true**가 되어버려 WO-15가 추가한 `moveItemToNewCategory()` 분기(else if)에 영영 도달하지 못한다 — 대신 옛 분기(`itemRef[field] = value`)로 빠져서 이 가짜 속성에만 값을 계속 덮어쓸 뿐, `riskData` 트리 안에서 항목의 실제 위치는 전혀 바뀌지 않는다.
3. 화면에 표시되는 "위험세부분류" 텍스트는 `populateEditScreen()`이 매번 `getItemPath(id)`로 **실제 트리 경로**에서 다시 읽어오므로(WO-15 스펙 2.2 참고), 실제 위치가 안 바뀐 이상 항상 원래 이름 그대로 보인다 — "수정해도 원상복구된다"는 증상과 정확히 일치.

즉 WO-15의 로직 자체는 옳지만, 이 옛 리스너가 먼저 끼어들어 `saveEdits()`가 항상 "이미 자기 속성이 있다"고 착각하게 만들어 새 분기를 무력화시키고 있었다.

## 3. 구체적인 구현 방법

### A. 옛 리스너가 이 두 필드는 건드리지 않도록 제외

[index.html:8164-8171](index.html#L8164-L8171)을 아래로 교체:

```js
// 텍스트 필드 변경 내용도 동기화 (세부작업명 등)
// [WO-16] 세부작업명/위험세부분류는 riskData 트리 경로 자체이므로 여기서 건드리지 않는다.
// (saveEdits()의 moveItemToNewCategory()가 커밋 시점에 전담 처리 — WO-15 참고)
if (target.tagName === 'DIV' && target.isContentEditable) {
    const field = target.dataset.field;
    const item = findItemRefById(tr.dataset.id);
    if (item && field && field !== '세부작업명' && field !== '위험세부분류') {
        item[field] = target.innerText;
    }
}
```

### B. `saveEdits()`가 이 두 필드는 항상 이동 로직을 타도록 순서 변경 + 과거에 이미 잘못 생긴 가짜 속성 방어적 정리

[index.html:10233-10241](index.html#L10233-L10241) (WO-15가 만든 현재 코드)을 아래로 교체:

```js
row.querySelectorAll('[data-field]').forEach(el => {
    const field = el.dataset.field;
    const value = (el.tagName === 'INPUT' || el.tagName === 'SELECT') ? el.value : el.textContent;
    if (field === '세부작업명' || field === '위험세부분류') {
        moveItemToNewCategory(id, field, value);
        // [WO-16] 과거 리스너가 잘못 남겼을 수 있는 동명의 가짜 속성 정리 (있어도, 없어도 안전)
        delete itemRef[field];
    } else if (itemRef.hasOwnProperty(field)) {
        itemRef[field] = value;
    }
});
```

이렇게 하면 "세부작업명"/"위험세부분류"는 `hasOwnProperty` 상태와 무관하게 **항상** `moveItemToNewCategory()`로 가고, 혹시 이번 수정 전에 이미 편집을 시도해서 가짜 속성이 남아있는 기존 항목이 있어도(사용자가 이미 여러 번 시도해봤으므로 가능성 있음) `delete`로 정리되어 다음부터는 정상 동작한다.

---

## 4. Red Team 체크포인트

1. **A의 제외 조건이 다른 필드(위험발생및결과, 현재조치, 감소대책 등)의 실시간 동기화를 건드리지 않는가?** — `field !== '세부작업명' && field !== '위험세부분류'` 조건이므로 나머지 필드는 기존과 동일하게 매 키 입력마다 즉시 반영되어야 한다.
2. **B의 `delete itemRef[field]`가 실제로 그 필드를 쓰는 다른 곳에 부작용을 안 주는가?** — 이 두 필드는 leaf 항목의 정상 스키마에 원래 없는 것이므로(WO-15 스펙 2.2), 지워도 다른 로직(리포트 렌더링, AI 재생성 등)이 참조할 일이 없어야 한다. `위험발생및결과`/`현재조치`/`감소대책`/`위험성`/`개선후위험성` 등 실제 스키마 필드는 이 delete의 영향을 받지 않는지 재확인.
3. **기존 저장 데이터(`user_data.json`)에 이미 이 가짜 속성이 남아있는 항목이 있어도, 이번 수정 이후 그 항목을 다시 한번 편집→저장하면 정상적으로 정리되는가?** (완전 자동 마이그레이션은 범위 밖 — "다시 편집하면 고쳐진다" 정도면 충분, 사용자에게 별도 조치 요구 안 해도 됨을 확인만 할 것)
4. 이번 범위를 벗어나는 것(예: 앱 시작 시 전체 데이터를 스캔해서 가짜 속성을 일괄 정리하는 마이그레이션 로직 추가)은 임의로 구현하지 말고 제안으로만 보고.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. **반드시 실제 GUI로 검증할 것 (지난 WO-15는 Node 유닛 테스트만으로 검증해서 이 문제를 놓쳤음)**: `npm start`로 앱 실행 → "2. 선택 항목 편집" 화면 → "위험세부분류" 칸을 클릭해 텍스트를 새로 입력 → **30초를 기다리거나 화면1로 이동했다가 재진입** → 수정한 값이 실제로 남아있는지 확인.
3. "세부작업명" 칸도 동일하게 확인.
4. 같은 분류를 공유하던 다른 행이 있다면 영향 없는지 확인(WO-15 Red Team #1 재확인).
5. 위험발생및결과/현재조치/감소대책 등 다른 칸의 실시간 동기화(입력 즉시 반영되는 기존 동작)가 이번 수정으로 깨지지 않았는지 확인.
6. 위 전부 통과 후 `WORK_ORDER_master.md`에 WO-16으로 기록하고, WO-15 상태도 "WO-16으로 최종 수정 완료"로 갱신.
