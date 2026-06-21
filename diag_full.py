"""
위험성 평가 앱 종합 진단 스크립트
- HTML 구조 무결성
- baseRiskData DB 오류 (중복 ID, 누락 필드, 위험성 값 오류 등)
- 주요 JS 함수 존재 여부
- 이벤트 바인딩 대상 DOM 매핑
- 파일 크기 / 라인 수
"""
import io, sys, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILEPATH = r'D:\dev\dang\v5_build\index.html'

print("=" * 64)
print("  위험성 평가 앱 종합 진단 리포트")
print("=" * 64)

with open(FILEPATH, encoding='utf-8') as f:
    content = f.read()
lines = content.splitlines()

# ──────────────────────────────────────────────
# 1. 파일 기본 정보
# ──────────────────────────────────────────────
print(f"\n[1] 파일 기본 정보")
print(f"  총 라인 수  : {len(lines):,}")
print(f"  파일 크기   : {len(content.encode('utf-8')):,} bytes ({len(content.encode('utf-8'))/1024/1024:.2f} MB)")

# ──────────────────────────────────────────────
# 2. HTML 구조 검사
# ──────────────────────────────────────────────
print(f"\n[2] HTML 구조 검사")
errs = []
if content.count('<html') != 1:
    errs.append(f'<html> 태그 수 이상: {content.count("<html")}')
if content.count('</html>') != 1:
    errs.append(f'</html> 태그 수 이상: {content.count("</html>")}')
if content.count('<head') != 1:
    errs.append(f'<head> 태그 수 이상: {content.count("<head")}')
if content.count('<body') != 1:
    errs.append(f'<body> 태그 수 이상: {content.count("<body")}')
if content.count('<script') != content.count('</script>'):
    errs.append(f'<script> 짝 불일치: {content.count("<script")} vs {content.count("</script>")}')
if content.count('<style') != content.count('</style>'):
    errs.append(f'<style> 짝 불일치: {content.count("<style")} vs {content.count("</style>")}')

if errs:
    for e in errs:
        print(f"  !! {e}")
else:
    print(f"  OK  기본 HTML 구조 정상")

# ──────────────────────────────────────────────
# 3. 필수 DOM ID 존재 여부
# ──────────────────────────────────────────────
print(f"\n[3] 필수 DOM ID 존재 여부")
required_ids = [
    'site-name-input', 'date-input', 'assessment-type-trigger-btn',
    'assessment-type-modal', 'atype-badge-label', 'atype-modal-custom-input',
    'atype-modal-confirm-btn', 'atype-modal-cancel-btn', 'atype-modal-close-btn',
    'open-approval-settings-btn', 'header-save-btn', 'header-load-btn',
    'tree-container', 'col-reset-btn',
    'approval-settings-modal', 'category-modal',
    'zoom-out-btn', 'zoom-in-btn', 'zoom-level-text',
    'column-count-select',
]
missing_ids = []
for rid in required_ids:
    if f'id="{rid}"' not in content and f"id='{rid}'" not in content:
        missing_ids.append(rid)
        print(f"  !! MISSING id: {rid}")
    else:
        print(f"  OK  #{rid}")

# ──────────────────────────────────────────────
# 4. 필수 JS 함수 존재 여부
# ──────────────────────────────────────────────
print(f"\n[4] 필수 JS 함수 존재 여부")
required_fns = [
    'function saveUserData',
    'function loadUserData',
    'function buildTreeView',
    'function getReportHTML',
    'function showApprovalSettingsModal',
    'function saveApprovalSettings',
    'function setupEventListeners',
    'function openDB',
    'function bindAssessmentTypeModal',
    'window._restoreAssessmentType',
    'function showToast',
    'function saveProject',
]
missing_fns = []
for fn in required_fns:
    if fn not in content:
        missing_fns.append(fn)
        print(f"  !! MISSING: {fn}")
    else:
        print(f"  OK  {fn}")

# ──────────────────────────────────────────────
# 5. baseRiskData DB 추출 및 무결성 검사
# ──────────────────────────────────────────────
print(f"\n[5] baseRiskData DB 무결성 검사")

# baseRiskData 블록 추출
m = re.search(r'const baseRiskData\s*=\s*(\{[\s\S]+?\});\s*\n\s*(//|let |const |var |function )', content)
if not m:
    # 더 넓은 범위 시도
    m = re.search(r'const baseRiskData\s*=\s*\{', content)
    if m:
        print(f"  !! baseRiskData 블록 경계 자동 추출 실패 — 부분 분석으로 전환")
        db_found = False
    else:
        print(f"  !! baseRiskData 블록을 찾을 수 없습니다")
        db_found = False
else:
    db_found = True

if not db_found:
    # ID 기반 부분 분석
    all_ids = re.findall(r'"id"\s*:\s*"([^"]+)"', content)
    print(f"  총 항목 수 (id 기준): {len(all_ids)}")
    dup_ids = [x for x in all_ids if all_ids.count(x) > 1]
    dup_ids = list(set(dup_ids))
    if dup_ids:
        print(f"  !! 중복 ID 발견 ({len(dup_ids)}개): {dup_ids[:10]}")
    else:
        print(f"  OK  중복 ID 없음")

    # 위험성 값 검사
    valid_risk = {'상', '중', '하', ''}
    bad_risk = re.findall(r'"위험성"\s*:\s*"([^"]*)"', content)
    bad_risk_vals = [v for v in bad_risk if v not in valid_risk]
    if bad_risk_vals:
        print(f"  !! 위험성 비정상 값 ({len(bad_risk_vals)}개): {list(set(bad_risk_vals))[:5]}")
    else:
        print(f"  OK  위험성 값 모두 정상 (상/중/하, 총 {len(bad_risk)}개)")

    bad_after = re.findall(r'"개선후위험성"\s*:\s*"([^"]*)"', content)
    bad_after_vals = [v for v in bad_after if v not in valid_risk]
    if bad_after_vals:
        print(f"  !! 개선후위험성 비정상 값 ({len(bad_after_vals)}개): {list(set(bad_after_vals))[:5]}")
    else:
        print(f"  OK  개선후위험성 값 모두 정상 (총 {len(bad_after)}개)")

    # 누락 필드 검사 (위험발생및결과 없는 id)
    items_section = re.findall(r'\{[^{}]*"id"\s*:\s*"[^"]*"[^{}]*\}', content, re.DOTALL)
    missing_field_count = 0
    for item in items_section:
        if '"위험발생및결과"' not in item:
            missing_field_count += 1
    if missing_field_count:
        print(f"  !! 위험발생및결과 누락 항목 수: {missing_field_count}")
    else:
        print(f"  OK  위험발생및결과 필드 모두 존재 (검사 항목: {len(items_section)}개)")
else:
    print(f"  OK  baseRiskData 블록 추출 성공 — 상세 분석 수행")

# ──────────────────────────────────────────────
# 6. 중요 이벤트 바인딩 검사
# ──────────────────────────────────────────────
print(f"\n[6] 이벤트 바인딩 검사")
bindings = [
    ('assessment-type-trigger-btn', 'openModal'),
    ('atype-modal-confirm-btn',     'confirmSelection'),
    ('header-save-btn',             'saveProject'),
    ('open-approval-settings-btn',  'showApprovalSettingsModal'),
]
for el_id, fn_name in bindings:
    found = el_id in content and fn_name in content
    status = 'OK ' if found else '!!'
    print(f"  {status}  #{el_id} → {fn_name}")

# ──────────────────────────────────────────────
# 7. localStorage 키 일관성 검사
# ──────────────────────────────────────────────
print(f"\n[7] localStorage 키 검사")
ls_keys = re.findall(r"localStorage\.(?:getItem|setItem|removeItem)\(['\"]([^'\"]+)['\"]", content)
ls_key_counts = {}
for k in ls_keys:
    ls_key_counts[k] = ls_key_counts.get(k, 0) + 1
for k, cnt in sorted(ls_key_counts.items()):
    print(f"  OK  '{k}' 사용 {cnt}회")

# ──────────────────────────────────────────────
# 8. 공종(최상위) 목록
# ──────────────────────────────────────────────
print(f"\n[8] baseRiskData 공종 목록")
# 공종명: baseRiskData의 최상위 key
gong_pattern = re.findall(r'(?:baseRiskData\[|baseRiskData\s*=\s*\{|,\s*\n\s*)"([^"]{2,30})":\s*\{', content)
# 더 간단한 방법: 'items' 배열 위 레벨의 key들
gong_names = re.findall(r'"([^"]{2,30})":\s*\{\s*"items"', content)
gong_names = list(dict.fromkeys(gong_names))  # 순서 유지 중복 제거
print(f"  공종 수: {len(gong_names)}개")
for g in gong_names:
    # 해당 공종의 items 수 계산
    pat = f'"{re.escape(g)}"' + r'\s*:\s*\{[\s\S]*?"items"\s*:\s*\[([^\]]*(?:\[[^\]]*\])*[^\]]*)\]'
    m2 = re.search(pat, content)
    item_cnt = content[content.find(f'"{g}"'):].count('"id"')
    # 대략적 카운트
    print(f"    • {g}")

# ──────────────────────────────────────────────
# 9. JS 문법 간이 검사 (괄호 균형)
# ──────────────────────────────────────────────
print(f"\n[9] JS 괄호 균형 검사 (<script> 블록)")
script_blocks = re.findall(r'<script[^>]*>([\s\S]*?)</script>', content, re.IGNORECASE)
total_open = total_close = 0
for blk in script_blocks:
    total_open  += blk.count('{')
    total_close += blk.count('}')
diff = total_open - total_close
if diff == 0:
    print(f"  OK  중괄호 균형 정상 (열림:{total_open} / 닫힘:{total_close})")
else:
    print(f"  !! 중괄호 불균형! {{열림:{total_open} / 닫힘:{total_close} / 차이:{diff:+d}}}")

# ──────────────────────────────────────────────
# 최종 요약
# ──────────────────────────────────────────────
issues = len(errs) + len(missing_ids) + len(missing_fns)
print(f"\n{'=' * 64}")
if issues == 0:
    print(f"  ✅  최종 결과: 이상 없음 (Error Count: 0)")
else:
    print(f"  ⚠️  최종 결과: 이슈 {issues}건 발견 — 위 항목 확인 필요")
print(f"{'=' * 64}\n")
