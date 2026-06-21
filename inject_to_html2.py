
# -*- coding: utf-8 -*-
"""
1-2 소규모 공종 위험성평가 엑셀 → baseRiskData 병합 스크립트
"""
import csv, json, re, shutil

def score_to_level(p, s):
    try:
        score = int(p) * int(s)
    except:
        score = 0
    if score >= 9: return '상'
    if score >= 4: return '중'
    return '하'

def after_level(level):
    if level == '상': return '중'
    return '하'

def normalize(text):
    return re.sub(r'\s+', ' ', text.strip().replace('-', '').strip())

# CSV 읽기
rows = []
with open('V:/dev/dang/excel2_extracted.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        rows.append(row)
print(f"총 행: {len(rows)}")

# 데이터 구조화
from collections import defaultdict
data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
seen = set()

for row in rows:
    gongjong = row['공종'].strip()
    sebu = row['세부작업'].strip() or '일반작업'
    wihum_cat = row['위험소분류'].strip() or '일반위험요인'
    wihum_text = row['유해위험요인'].strip()
    p = row['가능성'].strip()
    s = row['중대성'].strip()
    daecheck = row['개선대책'].strip()

    if not wihum_text or len(wihum_text) < 3:
        continue
    # 중복 제거
    dup_key = gongjong + '|' + normalize(wihum_text)
    if dup_key in seen:
        continue
    seen.add(dup_key)

    level = score_to_level(p, s)
    after = after_level(level)
    data[gongjong][sebu][wihum_cat].append({
        'wihum_text': wihum_text,
        'daechaek': daecheck,
        'level': level,
        'after': after,
    })

print("\n=== 공종별 통계 ===")
id_counter = 91000
js_output = {}
for gongjong, sebus in sorted(data.items()):
    total = sum(len(items) for s in sebus.values() for items in s.values())
    print(f"  {gongjong}: {total}개")
    js_output[gongjong] = {}
    for sebu, wihum_cats in sebus.items():
        js_output[gongjong][sebu] = {}
        for wihum_cat, items in wihum_cats.items():
            arr = []
            for item in items:
                arr.append({
                    'id': f"EX2_{id_counter}",
                    '위험발생및결과': item['wihum_text'],
                    '현재조치': '',
                    '감소대책': item['daechaek'],
                    '위험성': item['level'],
                    '개선후위험성': item['after'],
                })
                id_counter += 1
            js_output[gongjong][sebu][wihum_cat] = arr

# JSON 저장
with open('V:/dev/dang/excel2_merge_data.json', 'w', encoding='utf-8') as f:
    json.dump(js_output, f, ensure_ascii=False, indent=2)
print("[OK] excel2_merge_data.json 저장 완료")
print(f"[OK] 총 항목: {id_counter - 91000}개 (EX2_91000 ~ EX2_{id_counter-1})")

# index.html에 병합
with open('V:/dev/dang/v5_build/index.html', encoding='utf-8') as f:
    html = f.read()

marker = 'let baseRiskData = {'
pos = html.find(marker)
start = pos + len(marker)
depth, i = 1, start
while i < len(html) and depth > 0:
    if html[i] == '{': depth += 1
    elif html[i] == '}': depth -= 1
    i += 1
end_pos = i - 1
existing_block = html[pos:end_pos+1]

new_entries_js = ''
for gongjong, sebus in js_output.items():
    search_key = f'"{gongjong}"'
    if search_key in existing_block:
        # 기존 공종 - 세부작업 단위로 신규만 추가
        for sebu, wihum_cats in sebus.items():
            sebu_key = f'"{sebu}"'
            if sebu_key not in existing_block:
                new_entries_js += f'\n            // [소규모공종 병합] {gongjong} > {sebu}\n'
                new_entries_js += f'            "{sebu}": ' + json.dumps(wihum_cats, ensure_ascii=False, indent=12) + ',\n'
                print(f"  [MERGE_SUB] {gongjong} > {sebu}")
        else:
            print(f"  [SKIP] {gongjong}: 모든 세부작업 기존 존재")
    else:
        new_entries_js += f'\n            // ===== [소규모공종 병합] 신규: {gongjong} =====\n'
        new_entries_js += f'            "{gongjong}": ' + json.dumps(sebus, ensure_ascii=False, indent=12) + ',\n'
        print(f"  [NEW] {gongjong}: 신규 공종 추가")

if new_entries_js.strip():
    shutil.copy('V:/dev/dang/v5_build/index.html',
                'V:/dev/dang/v5_build/index.html.bak_before_excel2_merge')
    new_html = html[:end_pos] + new_entries_js + html[end_pos:]
    with open('V:/dev/dang/v5_build/index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)
    print("[OK] index.html 업데이트 완료!")
else:
    print("[SKIP] 추가할 신규 항목 없음")
