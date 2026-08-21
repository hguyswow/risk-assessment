# TASK_SPEC — WO-15: 편집화면 "세부작업명"/"위험세부분류" 칸 편집이 저장 안 되고 원래 값으로 되돌아가는 문제 수정

작성일: 2026-08-21
작성자: Claude (감독 모드 조사/설계)
대상 파일: `index.html`만

---

## 1. Context (왜 필요한가)

사용자 보고(스크린샷): "2. 선택 항목 편집" 표에서 "위험세부분류" 칸을 클릭해 직접 입력해도 저장이 안 되고, 다시 기존 값으로 돌아간다.

**감독모드 진단**: 이 두 칸은 사실 일반 텍스트 필드가 아니라, `riskData`의 중첩 구조(`공종 → 세부작업명 → 위험세부분류 → [항목배열]`)에서 **이 항목이 속한 경로(키) 이름**을 보여주는 것이다. 그런데 저장 로직(`saveEdits()`)은 "항목 객체가 그 필드를 자기 속성으로 갖고 있을 때만" 값을 반영하도록 되어 있어서, 이 두 필드는 조건이 항상 거짓이 되어 **입력값이 조용히 버려진다.** 사용자에게 알림도 없이 그냥 무시되고, 다음 렌더링 시 원래 분류명이 다시 나타나 "저장이 안 됐다"로 보인다.

**사용자 확인**: 편집 방식에 대해 두 가지 대안(①이 항목만 새 분류로 이동 / ②분류명 자체를 바꿔 같은 분류를 쓰는 모든 항목에 영향) 중 **①(이 항목만 이동)**을 명시적으로 선택함. 이 스펙은 그 방식으로만 구현한다.

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 문제의 저장 로직
`saveEdits()` — [index.html:10190-10210](index.html#L10190-L10210):
```js
function saveEdits() {
    document.querySelectorAll('#risk-items-container-tbody tr[data-id]').forEach(row => {
        const id = row.dataset.id;
        let itemRef = findItemRefById(id);
        if (itemRef) {
            ...
            row.querySelectorAll('[data-field]').forEach(el => {
                const field = el.dataset.field;
                const value = (el.tagName === 'INPUT' || el.tagName === 'SELECT') ? el.value : el.textContent;
                if (itemRef.hasOwnProperty(field)) {
                    itemRef[field] = value;
                }
            });
        }
    });
    saveUserData();
}
```

### 2.2 "세부작업명"/"위험세부분류"는 항목 객체의 속성이 아니다
`createEditRow(itemData)` — [index.html:9951](index.html#L9951), [index.html:9957](index.html#L9957):
```js
<div contenteditable="true" data-field="세부작업명" ...>${itemData.sebu || ''}</div>
...
<div contenteditable="true" data-field="위험세부분류" ...>${itemData.wihum || ''}</div>
```
`itemData.sebu`/`itemData.wihum`은 `populateEditScreen()`이 `getItemPath(id)`로 얻은 **경로의 일부**를 매 렌더링마다 임시로 얹어준 것([index.html:9868-9879](index.html#L9868-L9879) 부근, `{ ...itemRef, sebu, wihum }`)이지, `itemRef` 자체(실제 저장되는 객체)의 속성이 아니다. `createManualLeafItem()`([index.html:10213-10233](index.html#L10213-L10233))을 포함해 전체 파일에서 leaf 항목 객체가 `세부작업명`/`위험세부분류`를 자기 속성으로 갖는 곳은 0건(grep 확인). 그래서 `itemRef.hasOwnProperty('세부작업명')`/`hasOwnProperty('위험세부분류')`는 항상 `false`다.

### 2.3 이 버그가 실제로 트리거되는 경로
`dom.riskItemsTbody`의 `input` 리스너([index.html:8267-8272](index.html#L8267-L8272))가 이 두 칸을 포함한 모든 `contenteditable` 셀의 키 입력마다 `triggerAutoSave()`([index.html:4534-4541](index.html#L4534-L4541))를 걸어 **30초 후 자동으로 `saveEdits()`를 실행**한다. 또한 화면 전환 시(`showSelectionScreen()` [index.html:9155](index.html#L9155))에도 즉시 `saveEdits()`가 호출된다. 두 경로 모두 위 2.1의 버그를 그대로 통과한다.

### 2.4 경로 조회/조작에 쓸 수 있는 기존 유틸
- `getItemPath(id)` — [index.html:9845-9858](index.html#L9845-L9858): id가 속한 `[공종, 세부작업명, 위험세부분류]` 배열을 반환.
- `findItemRefById(id)` — [index.html:9830-9843](index.html#L9830-L9843): id에 해당하는 실제 항목 객체 참조를 반환.

---

## 3. 구체적인 구현 방법 (①이 항목만 새 분류로 이동)

### A. 새 헬퍼 함수 추가 — `moveItemToNewCategory(id, field, newValue)`

`getItemPath`/`findItemRefById` 정의 바로 아래([index.html:9858](index.html#L9858) 다음 줄)에 추가:

```js
// [WO-15] 편집화면에서 세부작업명/위험세부분류를 고쳐 썼을 때, 그 항목만 새 분류 경로로 이동시킨다.
// (같은 분류를 공유하는 다른 항목에는 영향을 주지 않음 — 이 항목의 소속만 바뀐다.)
function moveItemToNewCategory(id, field, newValue) {
    newValue = (newValue || '').trim();
    if (!newValue) return; // 빈 값으로 지우면 무시하고 기존 분류 유지 (분류 미아 방지)

    const path = getItemPath(id);
    if (!path || path.length < 3) return;
    const [gongjong, sebu, wihum] = path;

    const newSebu = field === '세부작업명' ? newValue : sebu;
    const newWihum = field === '위험세부분류' ? newValue : wihum;
    if (newSebu === sebu && newWihum === wihum) return; // 변경 없음

    const oldArr = riskData[gongjong] && riskData[gongjong][sebu] && riskData[gongjong][sebu][wihum];
    if (!Array.isArray(oldArr)) return;
    const idx = oldArr.findIndex(item => item.id == id);
    if (idx === -1) return;

    const [item] = oldArr.splice(idx, 1);

    // 비게 된 옛 분류 노드 정리 (빈 분류가 트리에 남지 않도록)
    if (oldArr.length === 0) {
        delete riskData[gongjong][sebu][wihum];
        if (Object.keys(riskData[gongjong][sebu]).length === 0) {
            delete riskData[gongjong][sebu];
        }
    }

    if (!riskData[gongjong][newSebu]) riskData[gongjong][newSebu] = {};
    if (!riskData[gongjong][newSebu][newWihum]) riskData[gongjong][newSebu][newWihum] = [];
    riskData[gongjong][newSebu][newWihum].push(item);
}
```

### B. `saveEdits()`의 필드 반영 루프에 분기 추가

[index.html:10199-10205](index.html#L10199-L10205)를 아래로 교체:

```js
row.querySelectorAll('[data-field]').forEach(el => {
    const field = el.dataset.field;
    const value = (el.tagName === 'INPUT' || el.tagName === 'SELECT') ? el.value : el.textContent;
    if (itemRef.hasOwnProperty(field)) {
        itemRef[field] = value;
    } else if (field === '세부작업명' || field === '위험세부분류') {
        moveItemToNewCategory(id, field, value);
    }
});
```

- `id`는 이 `forEach` 콜백 바깥(줄 10192)에서 이미 `row.dataset.id`로 선언돼 있으므로 그대로 재사용.
- 한 행에서 "세부작업명"과 "위험세부분류"를 동시에 고쳤어도, DOM 순서상 "세부작업명" 칸이 먼저 처리되고 그 다음 "위험세부분류" 칸이 처리된다. `moveItemToNewCategory`는 매번 `getItemPath(id)`로 **그 시점의 최신 위치**를 다시 조회하므로, 두 번 연달아 호출돼도 최종적으로 두 필드 변경이 정확히 함께 반영된다(순서 의존성 없음).

---

## 4. Red Team 체크포인트

1. **다른 항목(같은 분류를 공유하던 형제 항목들)이 이 변경으로 영향을 받지 않는가?** — `oldArr.splice(idx, 1)`은 편집된 항목 하나만 배열에서 꺼내는 것이므로, 같은 배열에 남아있던 나머지 항목들은 그대로 원래 분류에 남아야 한다.
2. **빈 문자열로 지웠을 때(사용자가 칸을 완전히 비운 경우) 항목이 분류 없는 곳으로 사라지지 않는가?** — `newValue`가 빈 문자열이면 즉시 `return`하여 기존 분류를 그대로 유지해야 한다(스펙 3-A에 이미 반영).
3. **`세부작업명`과 `위험세부분류`를 동시에 고쳤을 때 최종 경로가 두 변경 모두 반영된 위치로 정확히 이동하는가?** (3-B의 설명 참고 — 순서와 무관하게 최신 경로를 매번 재조회하므로 안전해야 함, 실제 npm start로 재현 확인 필요.)
4. **옛 분류 노드가 비었을 때 정리되는 로직이, 다른 곳에서 그 이제는-없는 세부작업명/위험세부분류 이름에 의존하는 코드(예: 트리뷰 렌더러, `getAllItemIdsInGongjong`)를 깨뜨리지 않는가?** — 트리뷰는 `buildTreeView()`가 `riskData`를 매번 다시 읽으므로, 빈 노드가 삭제된 채로 다시 그려지는 것이 정상이어야 한다. 화면3(선택 화면)으로 돌아가서 트리가 깨지지 않는지 확인.
5. **`공종` 자체를 바꾸는 기능은 이번 범위에 없다** — `field`가 `'세부작업명'`/`'위험세부분류'`일 때만 분기하며, `공종`(1단계)은 손대지 않는다. 표에 "공종" 편집 칸 자체가 없는지도 재확인(있다면 이번 스펙 범위 밖이므로 건드리지 말 것).
6. 이번 범위를 벗어나는 것(예: "분류명 자체 변경" 옵션을 함께 만드는 것, 이동 시 사용자에게 확인창 띄우기, 트리뷰에 새 분류 자동 펼치기 등)은 임의로 구현하지 말고 제안으로만 보고할 것.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 → "2. 선택 항목 편집" 화면 진입 → 한 행의 "위험세부분류" 칸을 클릭해 새 이름으로 수정 → 화면1로 돌아갔다가 다시 편집화면 재진입 → 수정한 이름이 그대로 남아있는지 확인 (더 이상 원래 값으로 안 돌아가야 함).
3. 같은 분류를 공유하던 다른 행이 있다면(스크린샷의 "가시설설치(띠 스트러트등)" 같은 공통 세부작업명 아래 여러 위험세부분류 행), 그 행들은 변경 없이 그대로인지 확인 (Red Team #1 회귀 확인).
4. "세부작업명" 칸도 동일하게 수정 → 저장되는지 확인 (이 필드도 같은 버그를 공유하고 있었으므로 반드시 함께 확인).
5. 빈 값으로 지웠다가 포커스를 옮겨봐도 항목이 사라지지 않고 기존 분류에 남아있는지 확인.
6. 화면1(트리)로 돌아가서 트리 구조가 새 분류명을 반영해 정상적으로 보이는지, 옛 분류가 항목이 0개면 트리에서 사라졌는지 확인.
7. 위 전부 통과 후 `WORK_ORDER_master.md`에 WO-15로 기록하고 완료 처리.
