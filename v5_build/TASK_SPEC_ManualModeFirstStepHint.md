# TASK_SPEC — 매뉴얼 모드 진입 시 "➕ 새 항목 추가 (매뉴얼)" 버튼 하이라이트 + 안내 말풍선

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-07
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만

---

## 1. Context (왜 필요한가)

사용자가 스크린샷(편집화면, 매뉴얼 모드 ON, 표가 비어있는 상태)에서 `➕ 새 항목 추가 (매뉴얼)` 버튼을 빨간 원으로 표시하며: "매뉴얼 모드를 시작하면 뭘 할지 모르니, 표시한 해당 버튼을 먼저 누르도록 하이라이트나 안내 멘트를 띄워달라"고 요청했다.

**범위 결정**: WO-5(헤더 버튼 배지)는 "항상 노출되는 정적 추천 배지"였지만, 이번 건은 성격이 다르다 — **온보딩 첫 단계 안내**이므로, 사용자가 실제로 항목을 추가하고 나면(표에 항목이 하나라도 생기면) 더 이상 보일 필요가 없다. 매번 매뉴얼 모드로 들어올 때마다 표에 항목이 있어도 계속 깜빡이면 오히려 거슬리는 UX가 된다. 따라서 이번 하이라이트/말풍선은 **"매뉴얼 모드가 켜져 있고 + 편집 표가 비어있을 때"만** 보이고, 항목이 하나라도 생기면 자동으로 사라지는 조건부 표시로 설계한다(사용자가 명시적으로 "매뉴얼 모드 시작하면"이라고 했으므로, 상태 판단 기준은 "이제 막 시작해서 아직 아무것도 없는 상태"로 해석).

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 대상 버튼
`#manual-add-item-btn` — [index.html:3287](index.html#L3287). 편집화면 하단 액션바 안, `class="manual-mode-only"`가 이미 붙어 있어 매뉴얼 모드가 꺼져 있으면 `display:none`으로 자동으로 숨겨진다(기존 CSS `.manual-mode-only`/`.manual-mode-active .manual-mode-only` 규칙 그대로 적용됨 — 이번 작업에서 이 규칙은 건드릴 필요 없음. 즉 하이라이트/말풍선도 매뉴얼 모드가 꺼지면 부모 버튼과 함께 자동으로 안 보이게 되므로, JS 조건은 "표가 비어있는지"만 판단하면 된다).

### 2.2 표 렌더링의 단일 진입점
`populateEditScreen()` — [index.html:9822-9869](index.html#L9822-L9869). 매뉴얼 마법사로 항목을 추가한 직후(WO-1), `showEditScreen(true)`로 빈 상태 진입한 직후(WO-4), 트리에서 선택 후 편집화면 진입 시 등 **표 내용이 바뀌는 모든 경로가 결국 이 함수를 거쳐 다시 렌더링된다.** 함수 끝([index.html:9866-9869](index.html#L9866-L9869))에 `toggleAICellButtonsVisibility()` 호출이 있는 것처럼, 이번 하이라이트 갱신 함수도 같은 위치에 추가하면 모든 경로를 빠짐없이 커버할 수 있다.

### 2.3 매뉴얼 모드 토글의 change 핸들러
`initManualModeWizard()` 내부 — [index.html:10251-10258](index.html#L10251-L10258). 체크박스를 직접 클릭해 매뉴얼 모드를 켤 때는 `populateEditScreen()`이 다시 호출되지 않는다(단순히 `.manual-mode-active` 클래스만 토글). 따라서 **이 핸들러 안에도 하이라이트 갱신 함수를 별도로 호출해야** 한다 — 안 그러면 "이미 편집화면에서 표가 비어있는 채로 체크박스만 수동으로 켠 경우"에 하이라이트가 안 뜨는 사각지대가 생긴다.

### 2.4 재사용 가능한 기존 패턴
- WO-5에서 만든 `#header-manual-mode-btn`의 펄스+배지 기법(버튼에 `position: relative` + 자식 `<span>`으로 오버레이, `pointer-events: none`)을 그대로 재사용할 것 — 이번에도 버튼(`<button>`) 안에 블록 레벨 `<div>`를 넣지 말고 **반드시 `<span>`으로만 구성**할 것(버튼은 phrasing content만 담을 수 있는 HTML 규칙, WO-5도 이 규칙을 지켰음).
- `.sponsorship-tooltip` 말풍선 패턴 — [index.html:147-177](index.html#L147-L177). 어두운 배경(`#1e293b`) + 삼각형 화살표(`::before`, `border-color` 트릭)로 만든 말풍선 예시. 이번엔 버튼 **위쪽**에 뜨고 화살표가 **아래**를 가리켜야 하므로 방향만 반대로 뒤집어 적용.

---

## 3. 구체적인 구현 방법

### A. 버튼 마크업에 펄스 + 말풍선 힌트 추가
[index.html:3287](index.html#L3287)을 다음으로 교체:
```html
<button id="manual-add-item-btn" class="manual-mode-only" style="background-color: #2563eb; color: white; position: relative;">
    ➕ 새 항목 추가 (매뉴얼)
    <span id="manual-add-item-hint-bubble" style="display: none; position: absolute; bottom: calc(100% + 12px); left: 50%; transform: translateX(-50%); background: #1e293b; color: #e2e8f0; padding: 8px 14px; border-radius: 8px; font-size: 12.5px; font-weight: 600; white-space: nowrap; box-shadow: 0 8px 20px rgba(0,0,0,0.4); border: 1px solid #2563eb; pointer-events: none; z-index: 10;">
        👆 여기를 눌러 첫 항목을 추가해보세요!
        <span style="position: absolute; top: 100%; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-width: 7px; border-style: solid; border-color: #1e293b transparent transparent transparent;"></span>
    </span>
</button>
```
- 버튼 자체에 `position: relative` 추가(기존 `background-color`, `color`는 유지).
- 말풍선(`#manual-add-item-hint-bubble`)은 기본 `display: none` — JS로만 보이게 한다(항상 렌더링은 되어 있지만 평소엔 숨김).
- 펄스 애니메이션은 별도 클래스로 관리(아래 B 참고) — 인라인 `animation` 속성을 마크업에 바로 넣지 않고 클래스 토글 방식으로 하는 이유는, 표에 항목이 생기면 애니메이션도 함께 꺼야 하기 때문(WO-5는 늘 켜져 있어도 됐지만 이번엔 조건부로 꺼야 함).

### B. 새 펄스 키프레임 + 클래스 (기존 것들과 별도로 신설)
```css
@keyframes manualAddItemPulse {
    0% {
        box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.6);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(37, 99, 235, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
    }
}
.manual-add-item-highlight {
    animation: manualAddItemPulse 2.2s infinite;
}
```
(색은 버튼 자체의 배경색 `#2563eb`와 맞춤 — WO-5의 헤더 버튼용 보라색과는 다른, 이 버튼 고유의 파란색.) 기존 `@keyframes pulse`(2212번대)나 WO-5의 `@keyframes manualModeBtnPulse`는 그대로 두고 손대지 말 것.

### C. 표시/숨김 판단 함수 신설 및 두 지점에서 호출
```js
function updateManualAddHint() {
    const btn = document.getElementById('manual-add-item-btn');
    const hint = document.getElementById('manual-add-item-hint-bubble');
    if (!btn || !hint) return;
    const shouldShow = globalSelections.size === 0;
    hint.style.display = shouldShow ? 'block' : 'none';
    btn.classList.toggle('manual-add-item-highlight', shouldShow);
}
```
- `populateEditScreen()` 끝([index.html:9866-9869](index.html#L9866-L9869), `toggleAICellButtonsVisibility()` 호출 바로 다음)에 `if (typeof updateManualAddHint === 'function') { updateManualAddHint(); }` 추가.
- `initManualModeWizard()`의 토글 `change` 핸들러([index.html:10251-10258](index.html#L10251-L10258)) 끝에도 동일하게 `if (typeof updateManualAddHint === 'function') { updateManualAddHint(); }` 추가.
- 매뉴얼 모드가 꺼져 있을 때는 버튼 자체가 `.manual-mode-only` 규칙으로 안 보이므로, 이 함수는 "매뉴얼 모드 여부"는 판단할 필요 없이 **"표가 비어있는지"만** 보면 된다(2.1 참고) — 불필요한 조건을 추가하지 말 것.

---

## 4. Red Team 체크포인트

1. **`<button>` 안에 `<div>`를 넣지 않고 전부 `<span>`으로만 구성했는가?** HTML 표준상 버튼은 phrasing content만 담을 수 있다 — WO-5와 동일한 원칙.
2. **말풍선/펄스가 "표에 항목이 하나라도 생기면" 실제로 사라지는가?** 마법사로 항목을 하나 추가한 직후(`populateEditScreen()`이 재호출되는 시점) 바로 사라지는지 재현 확인.
3. **체크박스를 직접 클릭해 매뉴얼 모드를 켜는 경로(2.3)에서도 하이라이트가 정상적으로 뜨는가?** `showEditScreen(true)` 경로(WO-4 버튼)뿐 아니라, 이미 편집화면에 있는 상태에서 표가 비어있는 채로 체크박스만 수동으로 켰을 때도 확인.
4. **말풍선의 `pointer-events: none`이 제대로 적용되어, 말풍선 영역을 클릭해도 버튼 클릭(마법사 열기)이 정상 작동하는가?**
5. **기존 `@keyframes pulse`, WO-5의 `@keyframes manualModeBtnPulse` 둘 다 건드리지 않고 `manualAddItemPulse`를 별도로 신설했는가?**
6. **말풍선이 버튼 위쪽에 뜰 때 화면(액션바) 상단 경계를 벗어나 잘리지 않는가?** `.action-buttons`나 그 상위 컨테이너에 `overflow: hidden`이 없는지 확인하고, 실제 렌더링에서 말풍선이 화면 밖으로 잘리지 않는지 육안 확인.
7. 이번 작업 범위를 벗어나는 것(예: 다른 버튼에도 확대 적용, 완료 후 재방문 시 다시 안 뜨게 하는 영구 기억 로직 등)은 임의로 구현하지 말고 제안으로만 보고할 것.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트/스타일 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 화면1 헤더의 `🛠️ 매뉴얼로 시작` 버튼으로 빈 편집화면 진입 → `➕ 새 항목 추가 (매뉴얼)` 버튼에 파란 펄스 효과와 "👆 여기를 눌러 첫 항목을 추가해보세요!" 말풍선이 보이는지 확인.
   b. 말풍선을 통해 마법사를 열어 항목을 하나 추가 완료 → 편집화면으로 돌아왔을 때 펄스/말풍선이 사라졌는지 확인.
   c. 편집화면에서 표가 비어있는 채로(항목 추가 전) 매뉴얼 모드 체크박스를 직접 껐다 켰다 하며 하이라이트가 매번 정상적으로 나타나는지 확인.
   d. 이미 트리에서 항목을 선택해 표가 채워진 상태로 매뉴얼 모드를 켰을 때는 하이라이트가 뜨지 않는지 확인(표가 비어있지 않으므로).
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-6로 기록하고 완료 처리.
