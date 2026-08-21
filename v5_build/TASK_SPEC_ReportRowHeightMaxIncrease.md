# TASK_SPEC — WO-17: 최종 보고서 미리보기 "표 여백" 설정 4종 최대치를 현재의 2배로 상향

작성일: 2026-08-21
작성자: Claude (감독 모드 조사/설계)
대상 파일: `index.html`만

---

## 1. Context (왜 필요한가)

사용자 요청: 최종 보고서 미리보기 화면(`report-row-height-panel`, WO-2/WO-9로 추가된 "📏 표 여백" 설정)에서 인쇄 결과 여백을 조절해보려는데, 줄수/행높이/셀 여백/줄간격 4개 값의 최대치가 너무 낮게 제한돼 있어 원하는 만큼 조절이 안 됨. **현재 최대치의 2배**로 상향 요청(에러 없는 선에서).

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호) — 현재 min/max 4곳 + 이를 강제하는 JS 클램프

이 설정은 두 군데에서 **각각** 상한을 강제하고 있어, 둘 다 함께 바꿔야 한다. HTML `max` 속성만 올리고 JS 클램프를 안 바꾸면 입력값이 `change` 이벤트 시 도로 옛 최대치로 깎여버린다.

### 2.1 HTML `<input>` min/max ([index.html:3390](index.html#L3390), [3394](index.html#L3394), [3398](index.html#L3398), [3402](index.html#L3402))
| 설정 | id | 현재 min/max | 2배 상향 후 max |
|---|---|---|---|
| 줄수 | `report-target-lines-input` | min 6 / max **24** | **48** |
| 행높이(px) | `report-empty-row-height-input` | min 15 / max **45** | **90** |
| 셀 여백(px) | `report-cell-padding-input` | min 1 / max **10** | **20** |
| 줄간격 | `report-line-height-input` | min 1.0 / max **2.0** | **4.0** |

### 2.2 JS 클램프 — `initReportRowHeightPanel()`의 `applyChange()` ([index.html:10925-10944](index.html#L10925-L10944))
```js
lines = Math.min(24, Math.max(6, ...));          // → Math.min(48, ...)
height = Math.min(45, Math.max(15, ...));        // → Math.min(90, ...)
...
cellPadding = Math.min(10, Math.max(1, ...));    // → Math.min(20, ...)
lineHeightVal = Math.min(2.0, Math.max(1.0, ...)); // → Math.min(4.0, ...)
```
이 값을 입력창에서 바꿀 때마다(`change` 이벤트) 이 함수가 실행되어 값을 다시 이 범위로 깎아서 `localStorage`에 저장하고 `generateReport()`를 다시 부른다. min(하한)은 이번 요청 범위가 아니므로 그대로 둔다.

두 값을 실제로 소비하는 곳(`getReportRowSettings()` [10874-10881], `getReportCellStyleSettings()` [10884-10891])은 자체적으로 상한을 두지 않고 `localStorage`에 있는 값을 그대로 신뢰하므로, 위 2.1/2.2만 고치면 나머지는 자동으로 새 범위를 그대로 따라간다.

---

## 3. 구체적인 구현 방법

### A. HTML min/max 속성 4곳 상향
[index.html:3390](index.html#L3390): `max="24"` → `max="48"`
[index.html:3394](index.html#L3394): `max="45"` → `max="90"`
[index.html:3398](index.html#L3398): `max="10"` → `max="20"`
[index.html:3402](index.html#L3402): `max="2.0"` → `max="4.0"`
(각 줄의 `min`/`step`/다른 속성은 그대로 유지)

### B. JS 클램프 4곳 상향
[index.html:10928-10929](index.html#L10928-L10929):
```js
lines = Math.min(48, Math.max(6, Number.isFinite(lines) ? lines : 16));
height = Math.min(90, Math.max(15, Number.isFinite(height) ? height : 24));
```
[index.html:10938-10939](index.html#L10938-L10939):
```js
cellPadding = Math.min(20, Math.max(1, Number.isFinite(cellPadding) ? cellPadding : 4));
lineHeightVal = Math.min(4.0, Math.max(1.0, Number.isFinite(lineHeightVal) ? lineHeightVal : 1.4));
```

이번 범위는 **최대치 상향뿐** — 기본값(16/24/4/1.4), 최소치(6/15/1/1.0), 함수 구조, 이벤트 바인딩 등은 전혀 손대지 않는다.

---

## 4. Red Team 체크포인트

1. HTML `max`와 JS 클램프 상한이 **정확히 같은 값**으로 짝이 맞는지(24↔48, 45↔90, 10↔20, 2.0↔4.0) 재확인 — 한쪽만 바뀌면 UI 스피너로는 더 큰 값을 선택할 수 있어 보이는데 `change` 시 조용히 깎이는 혼란스러운 상태가 됨.
2. 극단값(줄수 48, 행높이 90px, 셀 여백 20px, 줄간격 4.0)을 실제로 입력해 인쇄 미리보기가 에러 없이 렌더링되는지 확인 — 표가 매우 길어지거나 줄 간격이 과도하게 벌어지는 것은 사용자가 의도한 정상 결과이므로 문제 아님, 콘솔 에러나 레이아웃 깨짐(넘침으로 인쇄 영역 밖으로 잘리는 것 자체는 브라우저 인쇄 특성상 정상)만 확인.
3. 기존에 이미 저장된 `localStorage` 값(예: 이전에 24로 저장돼 있던 사용자)이 이번 변경으로 깨지지 않는지 — 기존 값이 새 범위 안에 있으므로 그대로 유지되면 정상.
4. 이번 범위를 벗어나는 것(예: 슬라이더 UI로 교체, 프리셋 버튼 추가 등 SB 계열 제안)은 임의로 구현하지 말고 제안으로만 보고.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 → 최종 보고서 미리보기 화면 → "📏 표 여백" 패널에서 4개 입력값을 각각 새 최대치(48/90/20/4.0)까지 올려보고 정상 반영·에러 없음 확인.
3. 각 입력을 최대치보다 더 큰 값으로 강제 입력해도(직접 타이핑) `change` 시 새 최대치로 정확히 깎이는지 확인(하한도 동일하게 재확인).
4. 위 통과 후 `WORK_ORDER_master.md`에 WO-17로 기록하고 완료 처리.
