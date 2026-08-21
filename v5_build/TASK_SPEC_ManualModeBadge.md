# TASK_SPEC — "🛠️ 매뉴얼로 시작" 버튼 주목 효과 + "초보자 추천" 배지

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-06
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만 (CSS + 버튼 마크업)

---

## 1. Context (왜 필요한가)

WO-4에서 만든 화면1 헤더의 `🛠️ 매뉴얼로 시작` 버튼을 사용자가 실제로 써보고 "초보자에게 특히 좋을 것 같다"며, 이 버튼에 (1) 살짝 주목을 끄는 시각 효과와 (2) "초보자 추천" 같은 문구가 함께 보이길 요청했다.

**범위 결정(임의 확장 방지용 명시)**: 이번 요청은 순수 시각적 폴리시(polish)다. 클릭 시 동작(토글 ON + 편집화면 이동)은 WO-4에서 이미 완성되어 있으므로 손대지 않는다. "한 번 써본 사용자에겐 배지를 숨긴다" 같은 상태 기억/조건부 로직은 사용자가 요청하지 않았으므로 이번 범위에 넣지 않는다 — 상시 노출되는 단순한 시각 효과 + 텍스트 배지로만 구현한다.

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 대상 버튼
`#header-manual-mode-btn` — [index.html:3111](index.html#L3111) (WO-4에서 신설). `.header-buttons` 플렉스 행([index.html:401-411](index.html#L401-L411), `flex-wrap: nowrap`, `overflow` 속성 없음 — 자식이 버튼 경계 밖으로 살짝 튀어나와도 잘리지 않음, 확인 완료) 안에서 `📂 불러오기` 바로 다음, 마지막 위치에 있다.

### 2.2 재사용 가능한 기존 패턴 (참고용, 그대로 재사용하지는 않음)
- `@keyframes pulse` — [index.html:2212-2227](index.html#L2212-L2227). 주석에 `[New] Guide Button Pulse Animation`이라고 적혀 있어 원래 안내 버튼용으로 만들어진 듯하지만, **실제로 `animation: pulse`를 적용하는 셀렉터가 코드 전체에 하나도 없다(직접 확인 완료, 죽은 CSS)**. 색상이 청록색(`rgba(23, 162, 184, ...)`)으로 하드코딩되어 있어 이번 버튼의 보라색 브랜드 컬러와 맞지 않는다. **이 키프레임을 고쳐 쓰지 말고, 그대로 둔 채 새 키프레임을 따로 만들 것** (다른 곳에서 나중에 이 값을 재사용하려 할 가능성을 남겨두고, 손대는 범위를 최소화하기 위함).
- `#help-btn`("📘 사용 가이드 (초보자용)", [index.html:3059-3062](index.html#L3059-L3062))이 바로 이 프로젝트에서 이미 쓰고 있는 "버튼 라벨에 (초보자용) 텍스트를 붙이는" 관례다. 이번엔 사용자가 별도의 "멘트"를 원했으므로, 버튼 본문 텍스트에 붙이기보다 **코너에 작은 배지(칩)**로 분리해서 더 눈에 띄게 한다(2.3의 `.atype-badge` 패턴 참고).
- `.atype-badge`(평가종류 버튼의 배지) — [index.html:755-763](index.html#L755-L763). 작은 알약형 배지 스타일(`border-radius: 12px; padding: 1px 9px; font-size: 12px; font-weight: 700;`)의 기존 예시 — 새 배지도 비슷한 형태(더 작은 사이즈)로 통일감 있게 만들 것.

### 2.3 매뉴얼 모드 브랜드 컬러
WO-1(마법사 모달 확인 버튼 등)과 WO-3(가이드 STEP 3-1 헤딩)에서 이미 `#8b5cf6`/`#7c3aed`(보라 계열)를 "매뉴얼 모드" 전용 색으로 일관되게 써왔다. 새 펄스 효과도 이 색 계열로 맞출 것.

---

## 3. 구체적인 구현 방법

### A. 새 펄스 키프레임 추가 (기존 `@keyframes pulse` 근처에 별도로 신설)
```css
@keyframes manualModeBtnPulse {
    0% {
        box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.55);
    }
    70% {
        box-shadow: 0 0 0 9px rgba(139, 92, 246, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(139, 92, 246, 0);
    }
}
```
(스케일 확대 없이 박스섀도우 링만 은은하게 퍼지는 형태 — 클릭 영역이나 레이아웃이 흔들리지 않게 하기 위함. 주기는 2~2.5초 정도로 느긋하게, 너무 산만하지 않게.)

### B. 버튼에 애니메이션 + 배지 적용
[index.html:3111](index.html#L3111)의 `#header-manual-mode-btn`을 다음과 같이 수정:
```html
<button id="header-manual-mode-btn" class="btn-gray" title="트리 선택 없이 매뉴얼 모드로 바로 시작합니다" style="position: relative; white-space: nowrap !important; flex-shrink: 0 !important; padding: 0 12px !important; background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important; color: #ffffff !important; animation: manualModeBtnPulse 2.2s infinite;">
    🛠️ 매뉴얼로 시작
    <span style="position: absolute; top: -9px; right: -6px; background: #f59e0b; color: #ffffff; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); white-space: nowrap; pointer-events: none;">초보자 추천</span>
</button>
```
- 기존 인라인 스타일(`white-space`, `flex-shrink`, `padding`, `background`, `color`)은 그대로 유지하고 `position: relative;`와 `animation: ...;`만 추가.
- 배지는 버튼의 자식 `<span>`으로 넣는다(래퍼 `<div>`를 새로 만들지 않음 — `<button>`은 인라인 자식을 담을 수 있으므로 구조 변경 최소화).
- 배지 색은 버튼의 보라색과 대비되는 앰버(`#f59e0b`)로 — 시각적으로 "추천 딱지"처럼 확실히 도드라지게.
- `pointer-events: none`을 배지에 반드시 넣어 배지 위를 클릭해도 버튼 클릭으로 그대로 인식되게 할 것(배지가 버튼 클릭을 가로채지 않도록).

---

## 4. Red Team 체크포인트

1. **기존 `@keyframes pulse`(2212-2227줄)를 고쳐 쓰지 않고 새 키프레임(`manualModeBtnPulse`)을 별도로 추가했는가?** 기존 걸 고치면 나중에 그 키프레임을 재사용하려는 다른 작업과 충돌할 여지가 생긴다.
2. **배지에 `pointer-events: none`이 적용되어, 배지 텍스트 부분을 클릭해도 버튼의 `onclick`(WO-4에서 만든 매뉴얼 모드 진입 로직)이 정상 작동하는가?** 직접 배지 위를 클릭해 편집화면으로 넘어가는지 재현 테스트할 것.
3. **`position: relative;` 추가가 `.header-buttons` 플렉스 레이아웃(다른 3개 버튼과의 정렬/간격)을 깨지 않는가?** `position: relative`는 일반적으로 flex 아이템 크기 계산에 영향을 주지 않지만, 실제 화면에서 4개 버튼이 여전히 한 줄에 나란히, 줄바꿈 없이 배치되는지 육안 확인.
4. **배지가 버튼 경계 밖으로 살짝 튀어나오는데(`top: -9px; right: -6px`), 인접한 헤더 영역(위쪽 border-top이나 오른쪽 여백)에 가려지거나 잘리지 않는가?** 2.1에서 `.header-buttons`에 `overflow` 제한이 없음을 이미 확인했지만, 실제 렌더링에서 화면 최우측 여백이 부족해 배지가 화면 밖으로 잘리지는 않는지 확인.
5. **애니메이션이 과하지 않은가?** 스케일 변형 없이 그림자 링만 부드럽게 퍼지는 정도로, 안전관리자가 업무 중 계속 봐야 하는 화면에서 거슬리지 않는 수준인지 확인. 과하면 주기를 늘리거나(예: 3s) 투명도를 낮출 것.
6. 이번 작업 범위를 벗어나는 것(클릭 후 동작 변경, 배지 숨김/기억 로직, 다른 버튼에도 확대 적용 등)은 임의로 구현하지 말고 제안으로만 보고할 것.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트/스타일 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 화면1 헤더에서 `🛠️ 매뉴얼로 시작` 버튼에 은은한 펄스(그림자 링) 효과가 반복되는지, 우측 상단에 앰버색 `초보자 추천` 배지가 보이는지 육안 확인.
   b. 배지 텍스트 부분을 직접 클릭해도 정상적으로 편집화면(매뉴얼 모드 ON)으로 이동하는지 확인 (Red Team #2 재현).
   c. 다른 헤더 버튼들(AI 생성/서명설정/불러오기)과 줄바꿈 없이 한 줄에 나란히 배치되는지 확인 (Red Team #3 재현).
   d. 배지가 화면이나 다른 요소에 잘리지 않고 온전히 보이는지 확인 (Red Team #4 재현).
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-5로 기록하고 완료 처리.
