# TASK_SPEC — 사진대지(📸) 일자(날짜) 필드 사용자 편집 가능하게 수정

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-07
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만

---

## 1. Context (왜 필요한가)

사용자가 최종 보고서의 사진대지(📸) 페이지에 표시되는 "일자"가 바뀌지 않는다고 보고했다. 조사 결과 두 가지가 겹친 문제였다:
1. `photoBoardData` 객체에 애초에 `date` 필드가 없다.
2. 렌더링 함수가 `reportHeaderData.reportDate`라는, 실제로는 존재하지 않는 오타 필드명을 참조하고 있어 항상 `undefined`가 되고, `||` 폴백으로 매번 `new Date()`(오늘 날짜)가 강제로 들어간다. 즉 사용자가 뭘 입력하든 소용없이 항상 "오늘 날짜"만 찍힌다.
3. 설정 모달(📸 사진대지 설정)에는 애초에 날짜를 입력할 UI 자체가 없다.

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

- `photoBoardData` 정의 — [index.html:4232-4238](index.html#L4232-L4238). `date` 필드 없음.
  ```js
  let photoBoardData = { enabled: false, photo1: '', text1: '', photo2: '', text2: '' };
  ```
- `getPhotoBoardHTML()` — [index.html:5191-5235](index.html#L5191-L5235). 문제의 줄:
  ```js
  let reportDate = reportHeaderData.reportDate || new Date().toISOString().split('T')[0];
  ```
  ([index.html:5193](index.html#L5193)) — `reportHeaderData`(정의: [index.html:4224](index.html#L4224))의 실제 필드명은 `date`이지 `reportDate`가 아니다. 이 `reportDate` 변수는 [index.html:5211](index.html#L5211)과 [index.html:5229](index.html#L5229) 두 곳(사진1/사진2 각각의 "일자" 열)에서 그대로 출력된다.
- `openPhotoBoardModal()` — [index.html:5036-5047](index.html#L5036-L5047). 체크박스/텍스트1·2/사진 미리보기만 초기화, 날짜 관련 코드 없음.
- `savePhotoBoardModal()` — [index.html:5175-5189](index.html#L5175-L5189). 마찬가지로 날짜를 저장하는 코드가 없음.
- 사진대지 설정 모달 마크업 — [index.html:12518-12572](index.html#L12518-L12572) 부근. 체크박스([index.html:12524](index.html#L12524)) 바로 아래, 사진1/2 입력 폼(`#pb-forms`, [index.html:12529](index.html#L12529)) 시작 전에 날짜 입력을 넣을 자리가 있다.

---

## 3. 구체적인 구현 방법

### A. `photoBoardData`에 `date` 필드 추가
[index.html:4232-4238](index.html#L4232-L4238):
```js
let photoBoardData = {
    enabled: false,
    photo1: '',
    text1: '',
    photo2: '',
    text2: '',
    date: ''
};
```

### B. 설정 모달에 날짜 입력 추가
[index.html:12524-12527](index.html#L12524-L12527) (체크박스 블록) 바로 다음, `#pb-forms`([index.html:12529](index.html#L12529)) 시작 전에 삽입:
```html
<div style="margin-bottom: 20px;">
    <label style="font-size: 14px; font-weight: bold; display: block; margin-bottom: 6px;">📅 사진대지 일자</label>
    <input type="date" id="pb-date-input" style="padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
</div>
```
(활성화 체크박스와 무관하게 항상 보이도록 `#pb-forms` 밖에 둔다 — 날짜는 사진과 별개로 언제든 확인/수정 가능해야 하므로.)

### C. `openPhotoBoardModal()`에서 날짜 입력값 초기화
[index.html:5036-5047](index.html#L5036-L5047)에 추가:
```js
const pbDateInput = document.getElementById('pb-date-input');
if (pbDateInput) {
    pbDateInput.value = photoBoardData.date || reportHeaderData.date || new Date().toISOString().split('T')[0];
}
```
(`photoBoardData.date`가 비어있으면 보고서 헤더의 작성일을 기본값으로 보여줘서, 처음 여는 사용자가 빈 칸에 당황하지 않게 함.)

### D. `savePhotoBoardModal()`에서 날짜 값 저장
[index.html:5175-5189](index.html#L5175-L5189)에 추가 (다른 필드 저장 줄들과 같은 위치):
```js
const pbDateInput = document.getElementById('pb-date-input');
photoBoardData.date = pbDateInput ? pbDateInput.value : '';
```

### E. `getPhotoBoardHTML()`의 오타 수정 및 저장된 값 사용
[index.html:5193](index.html#L5193):
```js
// 변경 전: let reportDate = reportHeaderData.reportDate || new Date().toISOString().split('T')[0];
let reportDate = photoBoardData.date || reportHeaderData.date || new Date().toISOString().split('T')[0];
```

---

## 4. Red Team 체크포인트

1. **`openPhotoBoardModal()`/`savePhotoBoardModal()`의 다른 기존 필드(사진1/2, 텍스트1/2, 활성화 체크박스) 로직을 실수로 건드리지 않았는가?** 순수 추가만 할 것.
2. **날짜를 한 번도 설정한 적 없는 기존 사용자(기존 `user_data.json`에 `photoBoardData.date` 필드가 아예 없는 경우)도 크래시 없이 정상 동작하는가?** (C의 폴백 체인으로 방어되는지 확인.)
3. **저장된 날짜가 `saveUserData()`를 통해 실제로 영속화되는가?** (`savePhotoBoardModal()` 끝에 이미 `await saveUserData();`가 있음 — 이 기존 흐름을 그대로 타는지만 확인, 별도 저장 로직을 새로 만들지 말 것.)
4. **사진1/사진2 두 테이블 모두(5211, 5229) 동일한 수정된 날짜를 보여주는가?**
5. 이번 작업 범위를 벗어나는 것(예: 사진1/사진2에 서로 다른 날짜를 지정하는 기능 등)은 임의로 구현하지 말 것 — 사양은 단일 날짜 필드다.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. "📸 사진대지 설정" 모달을 열어 날짜 입력란이 보이는지, 기본값이 채워져 있는지 확인.
   b. 날짜를 오늘이 아닌 다른 날짜로 바꾸고 저장 → 최종 보고서 미리보기에서 사진대지 페이지의 "일자"가 방금 입력한 날짜로 정확히 바뀌었는지 확인.
   c. 앱을 재시작해도 그 날짜가 유지되는지 확인.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-11로 기록하고 완료 처리.
