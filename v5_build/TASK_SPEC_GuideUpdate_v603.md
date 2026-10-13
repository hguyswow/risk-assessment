# TASK_SPEC — WO-18: 사용자 가이드(manual.html) 최신화 및 버전 6.0.2 → 6.0.3 통일

작성일: 2026-08-21
작성자: Claude (감독 모드 조사/설계)
대상 파일: `manual.html`, `package.json`, `index.html`(버전 문자열만)

---

## 1. Context (왜 필요한가)

이번 세션에서 WO-13~WO-17이 완료됐다(백업 커밋 `75ad369` 완료). 이 중 사용자가 실제로 화면에서 다르게 느낄 수 있는 항목은 **가이드 갱신이 필요**하고, 그 외(WO-13/14 같은 내부 크래시/타이밍 수정)는 사용자에게 보이는 동작 변화가 없으므로 가이드에 넣지 않는다. 또한 조사 중 **WO-9(셀 여백/줄간격 조절)가 애초에 가이드에 한 번도 반영된 적이 없었다는 것도 함께 확인**했다 — 이번 기회에 같이 보충한다.

WO-3의 선례(버전 통일 + 신규 기능 STEP 추가)를 그대로 따른다: `package.json`은 명세대로 상향, `index.html`은 버전 문자열만(로직 무변경), `manual.html`은 내용 갱신 + 버전 문자열.

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 가이드에 반영해야 할 실제 사용자 체감 변화
- **WO-15/16 (세부작업명/위험세부분류 인라인 편집)**: "2. 선택 항목 편집" 표에서 이 두 칸을 고쳐 쓰면, **그 항목 하나만** 새 분류로 이동한다(없는 이름이면 새로 생성됨). 같은 분류를 쓰던 다른 행은 영향 없음. → 가이드에 전혀 없던 내용, 신규 섹션 필요.
- **WO-17 (표 여백 최대치 2배)**: 기존 STEP 5-2가 "줄수 입력 (6~24줄)", "행높이 입력 (15~45px)"라고 옛 범위로 적혀있음([manual.html:494-495](manual.html#L494-L495)) → 새 범위(6~48줄, 15~90px)로 갱신 필요.
- **WO-9 (셀 여백/줄간격) — 이번에 함께 발견한 누락**: 실제 앱 UI에는 "셀 여백(px)"·"줄간격" 입력창이 이미 존재하는데([index.html:3396-3403](index.html#L3396-L3403)), STEP 5-2 가이드 본문에는 이 두 항목이 **한 번도 언급된 적이 없다**([manual.html:493-498](manual.html#L493-L498) 확인 — `<ul>` 안에 줄수/행높이 항목만 있고 셀여백/줄간격 없음). 이번에 같이 보충한다(WO-17로 범위가 1~20px, 1.0~4.0으로 상향됐으므로 그 값으로 바로 기재).
- WO-13/WO-14는 내부 버그 수정(빈 화면 → 정상 표시)이라 사용자가 "이런 절차를 따라야 한다"고 배울 게 없음 → 가이드 반영 대상 아님.

### 2.2 버전 문자열 위치 전수 (WO-3 때와 동일한 3파일 패턴)
- `package.json`: [package.json:3](package.json#L3) `"version": "6.0.2"`, [package.json:4](package.json#L4) `"description": "...v6.0.2..."`.
- `index.html`(로직 무변경, 문자열만): [index.html:3029](index.html#L3029), [3033](index.html#L3033), [3790](index.html#L3790), [4185](index.html#L4185) `APP_VERSION = "6.0.2"`. 이 4곳은 기존 프로젝트 컨벤션대로 `<!-- [기존 코드 백업] 이전값 -->` 주석을 남기고 그 아래 새 값을 적는 방식을 유지한다(3790번 줄처럼 이미 그렇게 되어있는 패턴 그대로 따름).
- `manual.html`: [manual.html:92](manual.html#L92), [97](manual.html#L97), [513](manual.html#L513) — **이 3곳만** "현재 가이드/앱 버전"을 나타내는 것이므로 6.0.3으로 바꾼다.

### 2.3 ⚠️ 바꾸면 안 되는 것 — manual.html의 "이 버전에서 추가됨" 이력 태그
[manual.html:187](manual.html#L187), [314](manual.html#L314), [414](manual.html#L414), [477](manual.html#L477), [490](manual.html#L490)에 있는 `(v6.0.2 신규 ✨)`, `(v6.0.2 고도화 ✨)` 같은 태그는 "그 기능이 6.0.2 때 추가/개선됐다"는 **이력 표시**다. 지금 6.0.3으로 올린다고 이 태그들을 일괄 치환하면 안 된다(그 기능들은 실제로 6.0.2에서 추가된 게 맞음). 오직 2.2의 3곳(현재 버전을 나타내는 표시)만 6.0.3으로 바꾸고, 이번에 **새로 추가하는 두 섹션**(3.A의 신규 STEP, 3.B의 갱신 항목)에만 `(v6.0.3 신규 ✨)`/`(v6.0.3 개선 ✨)` 태그를 새로 붙인다.

---

## 3. 구체적인 구현 방법

### A. `manual.html`에 신규 섹션 추가 — "STEP 3-2. 분류(세부작업명/위험세부분류) 직접 수정"

기존 STEP 3-1(매뉴얼 모드, [manual.html:412-431](manual.html#L412-L431)) 바로 뒤, STEP 4([manual.html:433](manual.html#L433)) 앞에 아래 블록을 새로 삽입:

```html
<!-- [v6.0.3 신규] 분류 인라인 편집 가이드 -->
<div class="step-box" style="border-left: 5px solid #8b5cf6; background-color: #faf5ff;">
    <h2 style="color: #7c3aed; border-left: none; padding-left: 0; background-color: #f3e8ff; border-radius: 5px; padding: 10px;">STEP 3-2. ✏️ 세부작업명 / 위험세부분류 직접 수정 (v6.0.3 신규 ✨)</h2>
    <p>"2. 선택 항목 편집" 표의 <strong>세부작업명</strong>과 <strong>위험세부분류</strong> 칸도 다른 칸처럼 클릭해서 바로 고쳐 쓸 수 있습니다.</p>
    <ul>
        <li><strong>이 항목만 이동:</strong> 이름을 고쳐서 저장하면, <strong>그 항목 한 줄만</strong> 새로 입력한 분류로 옮겨갑니다. 같은 분류를 함께 쓰던 다른 행들은 전혀 영향을 받지 않고 그대로 남습니다.</li>
        <li><strong>새 분류 자동 생성:</strong> 입력한 이름이 기존에 없던 이름이면, 그 자리에 새 분류가 자동으로 만들어지고 이 항목이 그 아래로 들어갑니다.</li>
        <li><strong>빈 칸으로 지우면 무시:</strong> 실수로 칸을 완전히 비우고 포커스를 옮기면, 항목이 사라지지 않도록 원래 분류가 그대로 유지됩니다.</li>
    </ul>
</div>
```

### B. `manual.html` STEP 5-2 본문 갱신 — [manual.html:490-498](manual.html#L490-L498)

전체를 아래로 교체:

```html
<!-- [v6.0.2 신규] 표 여백 조절 가이드 -->
<div class="step-box" style="border-left: 5px solid #10b981; background-color: #ecfdf5;">
    <h2 style="color: #059669; border-left: none; padding-left: 0; background-color: #d1fae5; border-radius: 5px; padding: 10px;">STEP 5-2. 📏 인쇄 미리보기 표 여백 조절 (v6.0.2 신규 ✨ / v6.0.3 범위 확대 ✨)</h2>
    <p>최종 보고서 미리보기 화면 상단 제어 바의 <strong>📏 표 여백</strong> 패널을 이용해 A4 인쇄물 표의 여백과 높이를 원하는 스타일대로 즉시 조절할 수 있습니다.</p>

    <ul>
        <li><strong>줄수 입력 (6~48줄):</strong> 목표 총 줄수를 지정합니다. 본문 내용이 부족할 경우 표 하단 빈 공간을 채우는 빈 행 개수가 자동 가감되어 A4 1페이지 분량에 맞춰 딱 정렬됩니다.</li>
        <li><strong>행높이 입력 (15~90px):</strong> 빈 행의 높이를 픽셀 단위로 직접 조절하여 인쇄물의 여백 감각을 섬세하게 맞출 수 있습니다.</li>
        <li><strong>셀 여백 입력 (1~20px):</strong> 내용이 채워진 행(비어있지 않은 행)의 상하 여백을 조절합니다. 내용이 많아 표가 이미 목표 줄수를 넘어선 경우, 빈 행 대신 이 셀 여백을 줄여서 인쇄 분량을 압축할 수 있습니다.</li>
        <li><strong>줄간격 입력 (1.0~4.0):</strong> 셀 안 텍스트의 줄과 줄 사이 간격(line-height)을 조절합니다. 글자가 빽빽해 보일 때 값을 높이면 가독성이 좋아집니다.</li>
        <li><strong>실시간 재렌더링 & 전 테마 완벽 적용:</strong> 수치 변경 즉시 미리보기가 자동 갱신되며, <strong>정석형 / 세련형 / 미래형</strong> 3개 인쇄 테마 전체에 동시 적용됩니다.</li>
        <li><strong>인쇄 출력 자동 제외:</strong> 해당 설정 조절 패널은 문서 출력 시(PDF/프린터) <code>.no-print</code> 규칙에 따라 인쇄물에서 깔끔하게 자동 제외됩니다.</li>
    </ul>
</div>
```
(바뀐 것: 제목에 "v6.0.3 범위 확대" 병기, 줄수/행높이 범위 숫자 갱신, 셀 여백·줄간격 항목 신규 추가 2개. 나머지 문구·구조는 그대로.)

### C. 버전 문자열 통일 — 6.0.2 → 6.0.3

**`package.json`**:
```json
"version": "6.0.3",
"description": "Risk Assessment Application v6.0.3 - 편집화면 데이터 복원/분류 편집 저장 안정화 및 표 여백 범위 확대",
```

**`index.html`** (2.2에 적힌 4곳, 기존 `[기존 코드 백업]` 주석 컨벤션 유지하며 6.0.2 → 6.0.3):
- [index.html:3029](index.html#L3029): `<span id="splash-version-title">v6.0.2</span>` → `v6.0.3`
- [index.html:3033](index.html#L3033): `id="splash-version-text">6.0.2</span>` → `6.0.3`
- [index.html:3790](index.html#L3790): `<strong>v6.0.2</strong>` → 그 위에 `<!-- [기존 코드 백업] <strong>v6.0.2</strong> -->` 주석을 남기고 `<strong>v6.0.3</strong>`
- [index.html:4185](index.html#L4185): `const APP_VERSION = "6.0.2";` → `"6.0.3"`

**`manual.html`** (2.2에 적힌 "현재 버전" 3곳만, 2.3의 이력 태그 5곳은 절대 건드리지 않음):
- [manual.html:92](manual.html#L92): `<h1>...(v6.0.2)</h1>` → `(v6.0.3)`
- [manual.html:97](manual.html#L97): `...(v6.0.2) 안내` → `(v6.0.3) 안내`
- [manual.html:513](manual.html#L513): `Version 6.0.2` → `Version 6.0.3`

---

## 4. Red Team 체크포인트

1. **manual.html의 이력 태그(2.3에 나열한 5곳, `(v6.0.2 신규 ✨)` 등)가 실수로 6.0.3으로 바뀌지 않았는가?** — grep으로 `v6.0.2`가 정확히 5곳(이력 태그) + 이번에 새로 쓴 STEP 5-2 제목의 "v6.0.2 신규" 부분(그대로 유지, 옆에 "v6.0.3 범위 확대"만 추가) 남아있는지 재확인.
2. STEP 3-2가 STEP 3-1과 STEP 4 사이에 정확히 들어갔는가(다른 STEP 번호 순서를 깨뜨리지 않는지)?
3. STEP 5-2의 나머지 문구(테마 적용 관련 언급 없음, 인쇄 제외 항목 등)가 이번 교체로 실수로 유실되지 않았는가?
4. `package.json`이 유효한 JSON으로 파싱되는가(트레일링 콤마 등 문법 오류 없는지)?
5. `index.html`의 버전 문자열 교체가 그 주변 로직(예: 원격 버전 비교 코드가 있다면)에 영향을 주지 않는가 — 이번 범위는 문자열 리터럴만 바꾸는 것이므로 그 주변 JS 로직은 절대 손대지 말 것.
6. 이번 범위를 벗어나는 것(예: WORKINFO.md 버전 언급, 다른 문서 파일)은 임의로 건드리지 말 것 — 이번 스펙은 `manual.html`/`package.json`/`index.html` 버전 문자열로 한정.

---

## 5. 검증 절차

1. 정적 검증: `index.html` 스크립트 블록 파싱 재실행(0건 에러), `node -e "JSON.parse(require('fs').readFileSync('package.json','utf-8'))"`로 `package.json` 파싱 확인.
2. `manual.html`에서 `grep -c "6.0.2"` / `grep -c "6.0.3"` 결과가 예상대로인지 확인(이력 태그 5곳은 6.0.2 유지, 현재버전 3곳 + 신규 태그 2곳은 6.0.3).
3. `npm start`로 앱 실행 → 스플래시 화면과 설정 화면에 v6.0.3이 뜨는지 육안 확인.
4. `help-btn`(사용 가이드)로 `manual.html`을 열어 새 STEP 3-2와 갱신된 STEP 5-2가 깨짐 없이 렌더링되는지 확인.
5. 위 통과 후 `WORK_ORDER_master.md`에 WO-18로 기록하고 완료 처리.
