# -*- coding: utf-8 -*-
"""삽입 데이터 JSON 문법 사전 검증 스크립트"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'D:\dev\dang\new_ai_data.json', encoding='utf-8') as f:
    new_data = json.load(f)

# 전처리: 실제 줄바꿈 제거
STR_FIELDS = ['위험발생및결과', '현재조치', '감소대책']
for gongjong, sheets in new_data.items():
    for sheet_name, stages in sheets.items():
        for stage, items in stages.items():
            for item in items:
                for field in STR_FIELDS:
                    if field in item and isinstance(item[field], str):
                        item[field] = item[field].replace('\n', ' ')

# 삽입될 JS 조각 생성
new_entries_js = ''
for gongjong, sheets in new_data.items():
    new_entries_js += f'\n            // ===== [AI 병합] 신규 공종: {gongjong} =====\n'
    new_entries_js += f'            "{gongjong}": ' + json.dumps(
        sheets, ensure_ascii=False, indent=12
    ) + ',\n'

# 마지막 쉼표 제거 후 래핑하여 검증
test_body = new_entries_js.rstrip().rstrip(',')
test_obj = '{' + test_body + '\n}'
try:
    json.loads(test_obj)
    print('[OK] 삽입 데이터 자체 JSON 문법 정상!')
except json.JSONDecodeError as e:
    print(f'[ERROR] 삽입 데이터 오류: {e}')
    print('오류 위치 주변:')
    print(repr(test_obj[max(0,e.pos-150):e.pos+150]))

# 실제 병합 후 전체 블록 검증
with open(r'D:\dev\dang\v5_build\index.html', encoding='utf-8') as f:
    html = f.read()

MARKER = 'let baseRiskData = {'
pos = html.find(MARKER)
start = pos + len(MARKER)
depth = 1
i = start
while i < len(html) and depth > 0:
    if html[i] == '{': depth += 1
    elif html[i] == '}': depth -= 1
    i += 1
end_pos = i - 1

# 콤마 + 신규 데이터 삽입 후 전체 블록 추출
new_html = html[:end_pos] + ',\n' + new_entries_js + html[end_pos:]

# 재탐색
new_pos = new_html.find(MARKER)
new_start = new_pos + len(MARKER) - 1
ver_depth = 0
ver_i = new_start
while ver_i < len(new_html):
    if new_html[ver_i] == '{': ver_depth += 1
    elif new_html[ver_i] == '}':
        ver_depth -= 1
        if ver_depth == 0: break
    ver_i += 1

merged_block = new_html[new_start:ver_i+1]
print(f'\n병합 후 블록 길이: {len(merged_block):,}')

try:
    json.loads(merged_block)
    print('[OK] 병합 후 전체 블록 JSON 문법 정상!')
except json.JSONDecodeError as e:
    print(f'[ERROR] 병합 블록 오류: {e}')
    print('오류 위치 주변:')
    print(repr(merged_block[max(0,e.pos-200):e.pos+200]))
