# TASK_SPEC — 매뉴얼 모드 (편집화면 신규 항목 추가 + 항목별 AI 글자수 조절)

작성일: 2026-08-05
작성자: Claude (감독 모드 조사/설계)
대상 파일: `index.html` (편집화면/트리/AI 셀 재생성 로직), 필요시 `aiService.js`는 수정 없이 그대로 소비

---

## 1. Context (왜 필요한가)

"2. 선택 항목 편집" 화면(`#risk-assessment-screen`)은 현재 화면1의 트리에서 **체크한 항목만** 불러와 보여준다. 새 위험요인/작업/공종을 추가하려면 반드시 화면1(트리)로 돌아가 레벨별 "＋" 버튼을 눌러야 하는데, 이 흐름이 초보 사용자에게 직관적이지 않다.

사용자 요구사항:
1. 편집화면에서 **"매뉴얼 모드"**를 켜면, 그 화면 안에서 바로 새 항목을 추가할 수 있어야 한다.
2. 새 항목 추가 시 기존 DB 계층 구조(공종 → 세부작업명 → 위험세부분류 → 위험요인)에 맞춰 **단계별로 선택하거나 새로 입력**하도록 하여, 초보자도 실수 없이 기존 DB 구조에 자연스럽게 편입되도록 한다.
3. 매뉴얼 모드에서는 각 항목(행)의 AI 생성 결과 글자수(디테일 수준)를 **행 단위로 개별** 조절할 수 있어야 한다 (프리셋 + 숫자 직접 입력 둘 다).

사용자 확정 답변(질문 결과):
- 모드 진입 방식: **전역 토글 스위치** (편집화면 상단 ON/OFF, 켜졌을 때만 신규 UI 노출)
- 신규 항목 추가 UI: **단계별 마법사 모달** (공종→세부작업명→위험세부분류→내용 입력 순 팝업)
- DB 반영 범위: **영구 반영** (트리/riskData에도 저장되어 이후 다른 보고서에서도 재사용 가능)
- 글자수 조절 방식: **프리셋 + 숫자 직접 입력 둘 다 제공**

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 편집화면 마크업
- `#risk-assessment-screen`, 헤더 `<h2>✏️ 2. 선택 항목 편집</h2>` — [index.html:3218-3246](index.html#L3218-L3246)
- 테이블 바디: `<tbody id="risk-items-container-tbody">` — [index.html:3236](index.html#L3236)
- 액션 버튼 영역(⬅️ 선택 화면으로 / 💾 저장 / 📸 사진대지 설정 / 📄 최종 보고서 생성 / ↔️ 열 너비 초기화) — [index.html:3239-3245](index.html#L3239-L3245)

### 2.2 데이터 구조 (riskData)
`riskData[공종][세부작업명][위험세부분류] = [ {id, 위험발생및결과, 현재조치, 감소대책, ...위험도 필드} , ... ]` 형태의 중첩 객체.
- 경로 탐색: `getItemPath(id, data, path)` — [index.html:9562-9575](index.html#L9562-L9575)
- 리프 아이템 참조 조회: `findItemRefById(id, data)` — [index.html:9547-9560](index.html#L9547-L9560)

### 2.3 편집화면 렌더링
`populateEditScreen()` — [index.html:9577-9631](index.html#L9577-L9631)
- **`globalSelections`(Set, 리프 id 모음)를 순회하며 렌더링한다.** 즉 `riskData`에 항목이 있어도 `globalSelections`에 id가 없으면 편집화면에 나타나지 않는다. → 신규 항목을 마법사로 추가할 때 **반드시 `globalSelections.add(newId)`도 함께 호출해야** 편집화면에 즉시/영구적으로 보인다.
- 행 DOM 생성: `createEditRow(itemData)` — [index.html:9647](index.html#L9647) 이하. `itemData.위험성`(기본 '중'), `itemData.개선후위험성`(기본 '하') 필드를 읽어 select에 반영 ([index.html:9651-9652](index.html#L9651-L9652)).

### 2.4 기존 "신규 항목 추가" 로직 (트리 화면 전용, 재사용 대상)
`handleAdd(parentNode)` — [index.html:8365-8421](index.html#L8365-L8421)
- 레벨 매핑: `['공종', '세부작업', '위험세분류', '위험요인']`
- 레벨 -1(신규 공종): `riskData[newName] = {}` — 중복 시 alert로 차단 ([index.html:8375](index.html#L8375))
- 리프(위험요인) 신규 시: `id: \`CUST_${Date.now()}\`` 로 아래 필드의 객체를 배열에 push ([index.html:8384-8397](index.html#L8384-L8397)):
  ```
  { id, 위험발생및결과, 현재조치, 감소대책, 가능성, 중대성, 등급, 개선후가능성, 개선후중대성, 개선후등급 }
  ```
  ⚠️ **주의**: 이 스키마는 `가능성/중대성/등급` 계열 필드를 쓰지만, 편집화면 렌더(`createEditRow`)는 `위험성`/`개선후위험성` 필드를 읽는다(2.3 참고). 새 마법사로 리프를 만들 때는 편집화면이 실제로 읽는 필드명(`위험성`, `개선후위험성`)을 반드시 함께 채워야 한다. **Gemini는 착수 전 실제 `riskData`(또는 `user_data.json`) 안의 기존 리프 샘플 1~2개를 직접 열어 실제 사용 필드명을 재확인할 것.**
- 신규 공종/세부작업명/위험세부분류 이름 중복 시 alert로 차단하는 패턴 — [index.html:8375](index.html#L8375), [index.html:8400](index.html#L8400)
- 추가 후 `await saveUserData()` → `buildTreeView()` → 편집화면 열려있으면 `populateEditScreen()` 재호출 — [index.html:8406-8419](index.html#L8406-L8419)

### 2.5 AI 셀 재생성 호출부
`ai-cell-btn` 클릭 핸들러 내부 — 대략 [index.html:9750-9852](index.html#L9750-L9852)
- 실제 AI 호출: `window.aiService.regenerateRiskField(fieldName, siteData, rowData, aiActiveConfig)` — [index.html:9792](index.html#L9792)
- `aiActiveConfig`는 **전역 단일 설정 객체**이며, 여기에 행별 오버라이드를 적용해 넘기려면 **얕은 복사 후 override**해서 전달해야 한다 (전역 객체를 직접 mutate하면 다른 행/이후 생성에도 영향을 줌).

### 2.6 이미 존재하는 전역 AI 글자수/디테일 설정 (재사용 대상)
- 디테일 프리셋 select `#ai-detail-level-select` (간결/보통/상세) — [index.html:3770-3776](index.html#L3770-L3776), 로드 [index.html:6165](index.html#L6165), 저장 → `aiActiveConfig.detailLevelRisk` [index.html:6343](index.html#L6343)
- 숫자 글자수 입력 `#ai-max-len-hazard`(유해위험요인, 기본 50) / `#ai-max-len-measure`(감소대책, 기본 100) — [index.html:3780-3786](index.html#L3780-L3786), 로드 [index.html:6166-6167](index.html#L6166-L6167), 저장 → `aiActiveConfig.maxLenHazard` / `aiActiveConfig.maxLenMeasure` [index.html:6345-6350](index.html#L6345-L6350)
- 이 값들은 `aiService.js`의 프롬프트 생성부에서 그대로 소비됨:
  - 디테일 프리셋 텍스트 분기 — [aiService.js:810-818](aiService.js#L810-L818), [aiService.js:1027-1033](aiService.js#L1027-L1033)
  - 글자수 지침 삽입 — [aiService.js:889-892](aiService.js#L889-L892), [aiService.js:1164-1167](aiService.js#L1164-L1167), [aiService.js:1201-1204](aiService.js#L1201-L1204)
  - `config.maxLenHazard`/`config.maxLenMeasure` 값이 프롬프트 문자열에 직접 삽입됨 — [aiService.js:890-891](aiService.js#L890-L891), [aiService.js:1165-1166](aiService.js#L1165-L1166), [aiService.js:1202-1203](aiService.js#L1202-L1203)

**결론: `aiService.js`는 수정할 필요가 없다.** `regenerateRiskField()` 호출 시 넘기는 4번째 인자(config)에 행별 override 값을 담아 전달하기만 하면 기존 프롬프트 로직이 그대로 소비한다.

### 2.7 저장/영속화
- `saveEdits()` — 편집화면 각 행의 `[data-field]` 값을 `riskData` 참조객체(`itemRef`)에 write-back 후 `saveUserData()` 호출 — [index.html:9881-9897](index.html#L9881-L9897)
- `saveUserData()` — IndexedDB + `user_data.json` 이중 저장 (WORKINFO.md 2026-06-25 항목 참고)

---

## 3. 구체적인 구현 방법

### A. 매뉴얼 모드 전역 토글
1. 편집화면 헤더 영역(`<h2>✏️ 2. 선택 항목 편집</h2>`, [index.html:3220](index.html#L3220)) 옆에 토글 UI 추가:
   ```html
   <label class="manual-mode-toggle">
     <input type="checkbox" id="manual-mode-toggle-checkbox"> 🛠️ 매뉴얼 모드
   </label>
   ```
2. 상태를 `localStorage.setItem('manualModeEnabled', 'true'/'false')`로 저장, 앱 로드 시 복원.
3. 토글 change 시 `#risk-assessment-screen`에 `manual-mode-active` 클래스를 추가/제거. 이후 B, C에서 추가하는 모든 신규 UI 요소는 `.manual-mode-active .manual-mode-only { display: inline-block; }` / 기본 `.manual-mode-only { display: none; }` 규칙으로 노출 제어.

### B. 신규 항목 추가 마법사 모달
1. 편집화면 액션 버튼 영역([index.html:3239-3245](index.html#L3239-L3245))에 버튼 추가:
   ```html
   <button id="manual-add-item-btn" class="manual-mode-only">➕ 새 항목 추가 (매뉴얼)</button>
   ```
2. 신규 모달 `#manual-add-item-modal` (기존 모달 스타일 class 재사용, 예: `.modal .modal-content`) 을 4단계로 구성:
   - **STEP 1 공종**: `<select id="manual-add-gongjong-select">`에 `Object.keys(riskData)` 나열 + 마지막 옵션 `➕ 새 공종 직접 입력`(선택 시 텍스트 input 노출)
   - **STEP 2 세부작업명**: STEP1에서 고른 공종 기준 `Object.keys(riskData[공종])` 나열 + `➕ 새로 입력` 옵션. STEP1 select의 `onchange`로 이 목록을 다시 빌드(체이닝).
   - **STEP 3 위험세부분류**: STEP1/2 결과 기준 `Object.keys(riskData[공종][세부작업명])` 나열 + `➕ 새로 입력` 옵션. STEP2 변경 시 재빌드.
   - **STEP 4 내용 입력**: 유해위험요인(`위험발생및결과`), 현재조치, 감소대책 텍스트 입력 + 현재위험성/개선후위험성 select(상/중/하). 기존 `showDetailEditModal()` ([index.html:8424-8465](index.html#L8424-L8465))의 필드 구성을 참고해 동일한 라벨/스타일로 통일.
3. "확인" 클릭 시 한 번에 다음을 수행 (모두 확인 버튼 클릭 시점에만 실행 — 중간 단계에서 `riskData`를 미리 건드리지 말 것, Red Team #7 참고):
   - 공종이 새 이름이면 `riskData[newGongjong] = {}` 생성, 기존 이름과 중복이면 `handleAdd()`와 동일하게 alert로 차단.
   - 세부작업명이 새 이름이면 `riskData[공종][newSebu] = {}` 생성 (중복 체크 포함).
   - 위험세부분류가 새 이름이면 `riskData[공종][세부작업명][newWihum] = []` 생성 (중복 체크 포함).
   - 리프 아이템 생성: `id: \`CUST_${Date.now()}\`` 로 **2.4의 주의사항대로** `위험성`/`개선후위험성` 필드를 포함해 push.
   - `globalSelections.add(newItemId)` 호출 (필수 — 2.3 참고).
   - `await saveUserData()` → `buildTreeView()` → `dom.riskItemsTbody.innerHTML=''; populateEditScreen();` 순으로 호출해 편집화면에 즉시 반영.
   - 새로 추가된 행으로 스크롤 + 하이라이트 (기존 `handleEdit()`의 패턴 [index.html:8487-8490](index.html#L8487-L8490) 재사용 가능).

### C. 항목별 AI 생성 글자수/디테일 개별 조절
1. `createEditRow()`([index.html:9647](index.html#L9647))에서 렌더링하는 각 행에, 매뉴얼 모드일 때만 보이는 "⚙️" 아이콘 버튼을 유해위험요인/감소대책 셀의 `.edit-cell-container` 안에 `manual-mode-only` 클래스로 추가.
2. 클릭 시 작은 팝오버(또는 공용 모달)로 아래 컨트롤 노출, 기본값은 전역 `aiActiveConfig` 값을 상속:
   - 상세도 프리셋 select (간결/보통/상세) — 전역 `#ai-detail-level-select`와 동일한 3옵션 구성
   - 숫자 입력 2개: 유해위험요인 최대 글자수, 감소대책 최대 글자수 (전역 `#ai-max-len-hazard`/`#ai-max-len-measure`와 동일한 min/max 범위)
3. 설정값은 해당 `<tr>`의 `dataset`에 저장: `tr.dataset.rowDetailLevel`, `tr.dataset.rowMaxLenHazard`, `tr.dataset.rowMaxLenMeasure`. 동시에 `itemRef`(riskData 리프 객체)에도 같은 키로 저장해 `saveUserData()` 시 영구 보존되도록 한다 (새로고침/재시작 후에도 행별 설정 유지).
4. `ai-cell-btn` 클릭 핸들러 내부, `window.aiService.regenerateRiskField(...)` 호출 직전([index.html:9792](index.html#L9792))에 아래처럼 행별 override를 적용한 **복사본**을 만들어 전달:
   ```js
   const rowConfig = { ...aiActiveConfig };
   if (tr.dataset.rowDetailLevel)   rowConfig.detailLevelRisk = tr.dataset.rowDetailLevel;
   if (tr.dataset.rowMaxLenHazard)  rowConfig.maxLenHazard  = parseInt(tr.dataset.rowMaxLenHazard, 10);
   if (tr.dataset.rowMaxLenMeasure) rowConfig.maxLenMeasure = parseInt(tr.dataset.rowMaxLenMeasure, 10);
   const response = await window.aiService.regenerateRiskField(fieldName, siteData, rowData, rowConfig);
   ```
   전역 `aiActiveConfig` 객체 자체는 절대 mutate하지 말 것.
5. `aiService.js`는 수정하지 않는다 (2.6 결론 참고).

---

## 4. Red Team 체크포인트 (Gemini는 착수 전 스스로 이 목록을 점검하고, "작업 전 의견 보고서"에 각 항목 대응 방안을 포함할 것)

1. 신규 공종/세부작업명/위험세부분류 이름 중복 시 `handleAdd()`와 동일하게 alert로 차단하는가? (해당 계층 키 존재 여부 체크)
2. 마법사로 추가한 새 리프 item의 id를 `globalSelections`에 추가했는가? — 누락 시 저장 후 재방문 시 편집화면에서 사라지는 버그 발생.
3. 새 리프 아이템에 편집화면 렌더가 실제로 읽는 필드명(`위험성`, `개선후위험성`)을 포함시켰는가? 착수 전 `riskData`/`user_data.json`의 기존 리프 데이터를 직접 열어 실제 필드명을 재확인했는가?
4. 행별 오버라이드 적용 시 전역 `aiActiveConfig` 객체를 직접 mutate하지 않고 `{...aiActiveConfig}`로 복사 후 override했는가?
5. 매뉴얼 모드 토글 OFF 상태에서 새로 추가한 모든 UI(버튼, ⚙️ 아이콘, 마법사 모달 트리거)가 완전히 숨겨지는가? 기존 레이아웃(열 너비 등)에 영향이 없는가?
6. 마법사 모달에서 중간 단계까지 진행 후 "취소"하면 `riskData`에 어떤 변경도 남지 않는가? (일괄 반영은 반드시 마지막 "확인" 클릭 시 한 번에)
7. 기존 `handleAdd()` / `showInputModal()` / `showDetailEditModal()` 로직 중 재사용 가능한 부분은 재사용했는가, 불필요한 중복 구현을 만들지 않았는가?
8. 이번 작업 범위를 벗어나는 기능 제안(예: 다른 화면 개선, 무관한 리팩터링)은 절대 이번 변경에 포함하지 않고 별도 제안으로만 보고했는가?

---

## 5. 검증 절차 (감독모드에서 Claude가 직접 재실행하여 확인, Gemini 보고를 그대로 신뢰하지 않음)

1. 정적 구문 검증: 기존 검증 스크립트(`scratch/verify_html_js.py` 등, 존재 확인 필요) 재실행하여 오류 0건 확인. 없으면 `node -e` 등으로 `<script>` 블록 추출 후 구문 체크.
2. `npm start`로 앱 직접 실행 후 수동 시나리오:
   a. 편집화면 진입 → 매뉴얼 모드 토글 ON → 신규 버튼/UI가 나타나는지 확인.
   b. "새 항목 추가" 클릭 → 신규 공종/신규 세부작업명/신규 위험세부분류/신규 위험요인 입력 → 확인 → 편집화면 표에 새 행이 즉시 나타나는지 확인.
   c. 앱 재시작(또는 새로고침) 후에도 해당 항목이 편집화면 및 화면1 트리에 남아있는지 확인 (`globalSelections`/`riskData` 영구 반영 검증 — DevTools에서 `riskData` 직접 조회).
   d. 신규/기존 행에서 ⚙️ 클릭 → 글자수를 전역값과 다르게 설정 후 🪄 재생성 → 실제 생성된 텍스트 길이가 설정값 근사치인지 확인.
   e. 같은 화면의 다른 행(오버라이드 미설정)에서 🪄 재생성 시 전역 설정값이 그대로 사용되는지 확인 (행별 오버라이드가 전역 설정을 오염시키지 않았는지 교차검증).
   f. 매뉴얼 모드 토글 OFF → 추가 UI가 모두 사라지는지 확인.
   g. 회귀 확인: 기존 흐름(화면1 트리에서 체크 → 편집화면 진입 → 일반 AI 일괄생성)이 이번 변경으로 깨지지 않았는지 확인.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`의 상태를 완료로 변경하고, 무엇을 어떻게 재검증했는지 한 줄로 기록.
