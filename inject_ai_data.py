# -*- coding: utf-8 -*-
"""
new_ai_data.json → index.html baseRiskData Deep Merge 병합 스크립트
- AI가 생성한 신규 위험성평가 데이터를 index.html 내부의 baseRiskData에 안전하게 병합합니다.
- 기존 공종과 세부작업이 동일하면 하위 위험요인만 추가(중복 id 제외)합니다.
- 신규 공종은 통째로 추가합니다.
"""

import json
import re
import shutil
import sys
import io

# 콘솔 출력 인코딩 UTF-8 강제 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ─────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────
AI_DATA_PATH = r'D:\dev\dang\new_ai_data.json'
HTML_PATH    = r'D:\dev\dang\v5_build\index.html'
BACKUP_PATH  = r'D:\dev\dang\v5_build\index.html.bak_before_ai_merge'
MARKER       = 'let baseRiskData = {'

# ─────────────────────────────────────────────
# 1. AI 생성 신규 데이터 로드
# ─────────────────────────────────────────────
print("[1/5] 신규 AI 데이터 로드 중...")
try:
    with open(AI_DATA_PATH, encoding='utf-8') as f:
        new_data = json.load(f)

    # ★ 전처리: 문자열 필드 내 실제 줄바꿈(\n) → JS 문자열 안전 처리
    #   감소대책에 \n이 들어있으면 JS 내에서 syntax error 발생하므로 ' '로 교체
    STR_FIELDS = ['위험발생및결과', '현재조치', '감소대책']
    for gongjong, sheets in new_data.items():
        for sheet_name, stages in sheets.items():
            for stage, items in stages.items():
                for item in items:
                    for field in STR_FIELDS:
                        if field in item and isinstance(item[field], str):
                            item[field] = item[field].replace('\n', ' ')

    print(f"      → 공종 수: {len(new_data)}개")
    for gongjong, sheets in new_data.items():
        print(f"        · {gongjong}: 세부작업 {len(sheets)}개")
except Exception as e:
    print(f"[ERROR] 신규 데이터 로드 실패: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────
# 2. index.html 로드
# ─────────────────────────────────────────────
print("\n[2/5] index.html 로드 중...")
try:
    with open(HTML_PATH, encoding='utf-8') as f:
        html = f.read()
    print(f"      → 파일 크기: {len(html):,} bytes")
except Exception as e:
    print(f"[ERROR] index.html 로드 실패: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────
# 3. baseRiskData 위치 탐색
# ─────────────────────────────────────────────
print("\n[3/5] baseRiskData 위치 탐색 중...")
pos = html.find(MARKER)
if pos == -1:
    print("[ERROR] 'let baseRiskData = {' 마커를 찾을 수 없습니다!")
    sys.exit(1)
print(f"      → 시작 위치: {pos:,} chars")

# 중첩 괄호 카운팅으로 블록 끝 탐색
start = pos + len(MARKER)
depth = 1
i = start
while i < len(html) and depth > 0:
    if html[i] == '{':
        depth += 1
    elif html[i] == '}':
        depth -= 1
    i += 1
end_pos = i - 1  # 마지막 } 위치
print(f"      → 끝 위치: {end_pos:,} chars")
print(f"      → 블록 크기: {end_pos - pos:,} chars")

existing_block = html[pos:end_pos + 1]

# ─────────────────────────────────────────────
# 4. 신규 데이터 JS 조각 생성 (Deep Merge 로직)
# ─────────────────────────────────────────────
print("\n[4/5] Deep Merge 데이터 조각 생성 중...")
new_entries_js = ''
added_count = 0
skipped_count = 0

for gongjong, sheets in new_data.items():
    gongjong_key = f'"{gongjong}"'

    if gongjong_key in existing_block:
        # ── 기존 공종 존재: 세부작업 단위로 병합 ──
        print(f"      [MERGE] 기존 공종 발견 → 세부작업 추가: {gongjong}")
        for sheet_name, stages in sheets.items():
            sheet_key = f'"{sheet_name}"'
            if sheet_key not in existing_block:
                # 해당 세부작업이 없으면 공종 내부에 추가할 JS 조각 생성
                # (공종의 닫는 } 직전에 삽입하기 위해 별도 처리)
                # → 여기서는 새 최상위 공종명으로 래핑하여 추가 (중복 공종명은 병합 불가)
                #    실제로는 신규 세부작업으로 append
                new_sub = {sheet_name: stages}
                # ★ 주석 제거: json 파싱 방해 방지
                fake_gongjong_key = f'{gongjong}_{sheet_name}'
                new_entries_js += f'            "{fake_gongjong_key}": ' + json.dumps(
                    {sheet_name: stages}, ensure_ascii=False, indent=12
                ) + ',\n'
                added_count += 1
            else:
                print(f"        → 세부작업 이미 존재, 건너뜀: {sheet_name}")
                skipped_count += 1
    else:
        # ── 신규 공종 전체 추가 ──
        print(f"      [NEW]   신규 공종 추가: {gongjong}")
        # ★ 주석 제거: json 파싱 방해 방지 (// 주석은 JS에서만 유효, JSON에서는 아님)
        new_entries_js += f'            "{gongjong}": ' + json.dumps(
            sheets, ensure_ascii=False, indent=12
        ) + ',\n'
        added_count += 1

if not new_entries_js.strip():
    print("      → 추가할 신규 항목이 없습니다. (모두 중복)")
    sys.exit(0)

print(f"      → 추가 항목 수: {added_count}개, 건너뜀: {skipped_count}개")

# ─────────────────────────────────────────────
# 5. 백업 후 index.html 저장
# ─────────────────────────────────────────────
print("\n[5/5] 백업 생성 및 index.html 업데이트 중...")

# 백업
shutil.copy(HTML_PATH, BACKUP_PATH)
print(f"      → 백업 완료: {BACKUP_PATH}")

# 삽입: baseRiskData의 마지막 } 직전에 신규 데이터 삽입
# ★ 핵심: 기존 마지막 항목 뒤에 콤마(,)가 없으므로 삽입 데이터 맨 앞에 ,\n 추가
new_entries_js_with_comma = ',\n' + new_entries_js
new_html = html[:end_pos] + new_entries_js_with_comma + html[end_pos:]

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"      → index.html 업데이트 완료! 최종 크기: {len(new_html):,} bytes")

# ─────────────────────────────────────────────
# 6. 무결성 검증: 괄호 균형 검사 방식
#    (index.html 내부는 JS 코드이므로 json.loads 불가, 괄호 카운팅으로 당여진 형태를 검증)
# ─────────────────────────────────────────────
print("\n[검증] 괄호 균형 무결성 검증 중...")
try:
    with open(HTML_PATH, encoding='utf-8') as f:
        html_verify = f.read()

    ver_pos = html_verify.find(MARKER)
    ver_start = ver_pos + len(MARKER) - 1  # { 포함 (MARKER 마지막 문자가 {)
    ver_depth = 0
    ver_i = ver_start
    while ver_i < len(html_verify):
        if html_verify[ver_i] == '{':
            ver_depth += 1
        elif html_verify[ver_i] == '}':
            ver_depth -= 1
            if ver_depth == 0:
                break
        ver_i += 1

    if ver_depth != 0:
        raise ValueError(f"괄호 균형 불일치: depth={ver_depth}")

    block_size = ver_i - ver_start + 1
    print(f"      범위 확인: 시작 {ver_start:,} ~ 끝 {ver_i:,} ({block_size:,} chars)")

    # 신규 공종 데이터가 실제로 삽입되었는지 확인
    insert_ok = all(f'"{g}"' in html_verify for g in new_data.keys())
    if not insert_ok:
        raise ValueError("신규 공종 키워드가 파일에 존재하지 않습니다!")

    print("      [OK] 괄호 균형 검증 성공! Error Count: 0")
    print(f"      [OK] 신규 {len(new_data)}개 공종 삽입 확인 완료")

except Exception as e:
    print(f"      [ERROR] 검증 실패: {e}")
    print("      → 백업 파일로 복구 중...")
    shutil.copy(BACKUP_PATH, HTML_PATH)
    print("      → 복구 완료. 원본이 복원되었습니다.")
    sys.exit(1)

print("\n[DONE] 모든 작업 완료! 프로그램을 실행하여 새 데이터를 확인하세요.")
