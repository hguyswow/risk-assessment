# TASK_SPEC — "완성본으로 저장/불러오기" (최종 보고서 미리보기 화면, 파일 기반)

- **상태**: `[작업 완료]` 🟢
- **작성일**: 2026-08-07
- **작성자**: Claude (감독 모드 조사/설계) / Gemini 3.6 Flash (구현/검수)
- **대상 파일**: `index.html`만

---

## 1. Context (왜 필요한가)

사용자가 "최종 완성본을 언제든 다시 열어볼 수 있고, 저장 후 다시 개선/변경해서 재사용 가능하도록" 저장 기능을 개선해달라고 요청했다.

**감독모드 사전 조사 결과**: 이 앱에는 이미 저장/불러오기 경로가 세 갈래 있다 — (1) 단일 슬롯 자동저장(`saveUserData()`, 항상 덮어씀), (2) `saveProject()`/`loadProject()` 쌍(스키마가 서로 안 맞고 아무 버튼에도 연결 안 된 죽은 코드), (3) "내보내기(DB)"/"불러오기(DB)"(`saveToDownload()`/`loadDataFromFile()`, 파일명 붙여 저장 가능하고 서로 스키마가 맞는 유일하게 정상 동작하는 쌍). 그런데 (3)조차도 `photoBoardData`(사진대지), `coverPageData`(표지), 인쇄 테마, 표 여백/셀 여백 설정(WO-2/WO-9, 전부 `localStorage`에만 있음)은 저장하지 않는다 — 그래서 "완성본"을 다시 열어도 사진대지·표지·인쇄 스타일·여백 설정은 복원되지 않고 다른 기기/새로고침 후엔 달라질 수 있다.

사용자 확정 답변(질문 결과):
- 저장 방식: **파일로 저장** (기존 "내보내기(DB)"와 유사한 방식).
- 버튼 위치: **최종 보고서 미리보기 화면**에 저장/불러오기 진입점 추가.

**설계 결정**: 새로운 병렬 저장 시스템을 만들지 않는다. 이미 정상 동작하는 (3) "내보내기(DB)"/"불러오기(DB)" 쌍(`saveToDownload()`, `loadDataFromFile()`, `#save-modal`, `#load-modal`)이 스키마도 맞고 파일 저장 UX(파일명 입력, 폴더 선택)도 이미 갖춰져 있으므로, **이 기존 함수들의 저장/복원 대상 데이터만 확장**하고, 최종 보고서 미리보기 화면에는 **같은 모달을 여는 버튼만 새로 추가**한다. (1), (2)는 이번 작업과 무관 — 건드리지 않는다.

---

## 2. 확인된 사실 (조사 결과, 파일:줄번호)

### 2.1 저장 함수 — `saveToDownload()` [index.html:11864-11933](index.html#L11864-L11933)
현재 저장되는 필드([index.html:11883-11890](index.html#L11883-L11890)):
```js
const dataToSave = {
    riskData: riskData,
    selections: [...globalSelections],
    selectedGongjongs: [...selectedGongjongs],
    headerData: reportHeaderData,
    savedAt: new Date().toISOString(),
    version: APP_VERSION
};
```
`photoBoardData`, `coverPageData`, 인쇄 테마(`localStorage.getItem('printTheme')`), 표 여백/셀 여백 설정(`localStorage`의 `reportTargetLines`/`reportEmptyRowHeight`/`reportCellPadding`/`reportLineHeight`)이 전부 빠져있다.

### 2.2 불러오기 함수 — `loadDataFromFile()` [index.html:11939-12148](index.html#L11939-L12148)
번호가 매겨진 단계별 구조(1단계 파싱 → ... → 6단계 헤더 데이터 복원[index.html:12042-12074](index.html#L12042-L12074) → 7단계 `saveUserData()`[index.html:12076-12083](index.html#L12076-L12083) → 8단계 UI 업데이트[index.html:12085-12097](index.html#L12085-L12097))로, 각 단계가 개별 `try-catch`로 방어되어 한 단계가 실패해도 나머지는 계속 진행되는 견고한 패턴이다. 6단계와 7단계 사이([index.html:12074](index.html#L12074)~[index.html:12076](index.html#L12076))가 새 "6-1단계"를 끼워넣기 정확히 좋은 위치.

### 2.3 저장/불러오기 모달 — 이미 완성되어 재사용 가능
- `#save-modal`([index.html:3510-3540](index.html#L3510-L3540)) → `showSaveModal()`([index.html:11836-11855](index.html#L11836-L11855)) → 확인 버튼(`data-action="save-download"`, [index.html:8248-8250](index.html#L8248-L8250)) → `saveToDownload()`.
- `#load-modal`([index.html:3542](index.html#L3542) 부근) → `showLoadModal()`([index.html:11857-11860](index.html#L11857-L11860)) → 파일 선택 시 `loadDataFromFile()`.
- 모달 제목이 이미 "📁 데이터 저장"/"📂 데이터 불러오기"로 범용적이라, "완성본" 전용 새 모달을 또 만들 필요가 없다 — **그대로 재사용**.

### 2.4 새 버튼 삽입 위치
`#report-preview-screen`의 액션바 첫 번째 `<div>`([index.html:3349-3356](index.html#L3349-L3356)), `🖨️ PDF 미리보기 및 인쇄` 버튼([index.html:3351](index.html#L3351)) 바로 다음.

### 2.5 `photoBoardData`/`coverPageData`는 `let`으로 선언된 모듈 스코프 변수
[index.html:4224](index.html#L4224)(`reportHeaderData`), [index.html:4232](index.html#L4232)(`photoBoardData`) 전부 `let`으로 선언되어 있어, 불러오기 시 `= {...}`로 재할당하거나 스프레드로 병합하는 것 모두 안전하게 가능하다(재선언이 아니라 재할당이므로 스코프 문제 없음).

---

## 3. 구체적인 구현 방법

### A. `saveToDownload()`의 `dataToSave`에 필드 추가
[index.html:11883-11890](index.html#L11883-L11890):
```js
const dataToSave = {
    riskData: riskData,
    selections: [...globalSelections],
    selectedGongjongs: [...selectedGongjongs],
    headerData: reportHeaderData,
    photoBoardData: photoBoardData,
    coverPageData: coverPageData,
    printTheme: localStorage.getItem('printTheme') || 'classic',
    reportLayoutSettings: {
        targetLines: localStorage.getItem('reportTargetLines'),
        emptyRowHeight: localStorage.getItem('reportEmptyRowHeight'),
        cellPadding: localStorage.getItem('reportCellPadding'),
        lineHeight: localStorage.getItem('reportLineHeight')
    },
    savedAt: new Date().toISOString(),
    version: APP_VERSION
};
```

### B. `loadDataFromFile()`에 "6-1단계" 추가
6단계(헤더 데이터, [index.html:12042-12074](index.html#L12042-L12074)) 블록이 끝난 직후, 7단계(`// 7단계: 사용자 데이터 저장`, [index.html:12076](index.html#L12076)) 시작 전에 삽입:
```js
// 6-1단계: 사진대지/표지/인쇄 레이아웃 설정 복원 (완성본 저장분에만 존재 — 구버전 파일은 이 필드들이 없어도 안전하게 건너뜀)
try {
    if (data.photoBoardData && typeof data.photoBoardData === 'object') {
        photoBoardData = { ...photoBoardData, ...data.photoBoardData };
    }
    if (data.coverPageData && typeof data.coverPageData === 'object') {
        coverPageData = { ...coverPageData, ...data.coverPageData };
    }
    if (data.printTheme) {
        localStorage.setItem('printTheme', data.printTheme);
        window.currentPrintTheme = data.printTheme;
    }
    if (data.reportLayoutSettings && typeof data.reportLayoutSettings === 'object') {
        const rls = data.reportLayoutSettings;
        if (rls.targetLines) localStorage.setItem('reportTargetLines', rls.targetLines);
        if (rls.emptyRowHeight) localStorage.setItem('reportEmptyRowHeight', rls.emptyRowHeight);
        if (rls.cellPadding) localStorage.setItem('reportCellPadding', rls.cellPadding);
        if (rls.lineHeight) localStorage.setItem('reportLineHeight', rls.lineHeight);
    }
    console.log('✅ 사진대지/표지/인쇄 설정 복원 완료');
} catch (extraError) {
    console.error('⚠️ 추가 설정 복원 중 오류:', extraError);
    // 이 단계 실패는 무시하고 계속 진행 (기존 단계들과 동일한 방어 패턴)
}
```
(기존 1~10단계와 동일한 "try-catch로 감싸고 실패해도 계속 진행" 스타일을 그대로 따를 것 — 새로운 에러 처리 패턴을 발명하지 말 것.)

### C. 최종 보고서 미리보기 화면에 버튼 2개 추가
[index.html:3351](index.html#L3351) (`🖨️ PDF 미리보기 및 인쇄` 버튼) 바로 다음:
```html
<button id="save-complete-report-btn" title="현재 상태를 완성본 파일로 저장합니다 (사진대지·표지·인쇄 설정 포함)" onclick="showSaveModal()">💾 완성본으로 저장</button>
<button id="load-complete-report-btn" title="저장해둔 완성본 파일을 불러옵니다" onclick="showLoadModal()">📂 완성본 불러오기</button>
```
(새 JS 함수를 만들지 않고 기존 `showSaveModal()`/`showLoadModal()`을 그대로 호출 — 2.3 참고.)

---

## 4. Red Team 체크포인트

1. **구버전(이번 필드 추가 전) 파일을 불러와도 크래시 없이 정상 동작하는가?** `data.photoBoardData` 등이 `undefined`인 옛날 파일 → 6-1단계의 `if (data.xxx && ...)` 가드로 조용히 건너뛰는지 확인.
2. **`photoBoardData`/`coverPageData` 복원이 스프레드(`{...현재값, ...불러온값}`)로 되어 있어, 불러온 파일에 일부 필드만 있어도 나머지 기존 필드가 사라지지 않는가?**
3. **인쇄 테마 복원 시 `localStorage`뿐 아니라 `window.currentPrintTheme`도 같이 갱신되는가?** (WO-2/WO-7 조사 당시 확인한 바, 테마는 두 곳에 상태가 있음 — 하나만 갱신하면 다음 `generateReport()` 호출 시 반영 안 되는 사각지대 발생.)
4. **기존 "내보내기(DB)"/"불러오기(DB)" 흐름(화면1 헤더 버튼)이 이번 필드 추가로 인해 깨지지 않는가?** (같은 함수를 확장하는 것이므로 회귀 위험이 가장 큼 — 반드시 재현 테스트.)
5. **`saveProject()`/`loadProject()`(죽은 코드)나 `gongjong-save-modal`(부분 저장)은 이번 작업과 무관하므로 전혀 건드리지 않았는가?**
6. **새 버튼 2개가 `showSaveModal()`/`showLoadModal()`을 그대로 호출하고, 별도의 새 모달이나 새 저장 로직을 만들지 않았는가?** (2.3의 설계 결정 준수.)
7. 이번 작업 범위를 벗어나는 것(예: `saveProject`/`loadProject` 수리, 앱 내부 "완성본 목록" UI, 자동 버전 관리 등)은 임의로 구현하지 말고 제안으로만 보고할 것.

---

## 5. 검증 절차

1. 정적 검증: index.html 스크립트 블록 파싱 재실행, 오류 0건 확인.
2. `npm start`로 앱 실행 후:
   a. 항목을 선택하고 사진대지(날짜 포함, WO-11 이후)와 표지 정보를 채운 뒤, 인쇄 테마를 "세련형"으로, 표 여백 값도 기본값과 다르게 바꾼 상태에서 최종 보고서 미리보기 화면의 `💾 완성본으로 저장` 클릭 → 파일명 입력 → 저장.
   b. 앱을 재시작(또는 다른 프로필처럼 `localStorage`/데이터를 초기화 후)하고, `📂 완성본 불러오기`로 방금 저장한 파일을 불러온다.
   c. 불러온 뒤 최종 보고서를 다시 생성했을 때 사진대지 날짜, 표지 정보, 인쇄 테마(세련형), 표 여백 값이 저장 당시와 동일하게 복원되는지 확인.
   d. 기존 화면1의 "내보내기(DB)"로 저장한 파일도 여전히 정상적으로 "불러오기(DB)"에서 열리는지 확인 (회귀 확인, Red Team #4).
   e. WO-2 이전(이번 필드가 없는) 예전 저장 파일이 있다면 그것도 에러 없이 불러와지는지 확인 (Red Team #1) — 없으면 신규 저장 파일에서 `photoBoardData`/`printTheme`/`reportLayoutSettings` 키를 수동으로 지운 사본으로 테스트.
3. 위 확인이 전부 끝난 뒤에만 `WORK_ORDER_master.md`에 WO-12로 기록하고 완료 처리.
