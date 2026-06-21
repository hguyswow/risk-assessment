
# -*- coding: utf-8 -*-
"""
엑셀 추출 CSV → index.html의 baseRiskData에 병합할 JS 조각 생성 스크립트
"""
import csv
import json
import re

# 위험성 등급 변환 (★ 개수 기반 → 상중하)
def star_to_level(star_str, p=None, s=None):
    stars = star_str.count('★')
    p_val = int(p) if p and p.isdigit() else 0
    s_val = int(s) if s and s.isdigit() else 0
    score = p_val * s_val if p_val and s_val else 0
    
    if stars >= 3 or score >= 9:
        return '상'
    elif stars == 2 or score >= 4:
        return '중'
    else:
        return '하'

def after_level(level):
    """개선 후는 현재보다 같거나 낮게"""
    if level == '상':
        return '중'
    return '하'

# 시트명 → 공종명 매핑
sheet_to_gongjong = {
    '트랜치설치': '전기공사',
    '판넬설치': '전기공사',
    '분리대설치': '가설공사',
    '기물반출': '철거공사',
    '계단철거': '철거공사',
    '주방철거': '철거공사',
    '슬라브커팅': '철거공사',
    '방수작업': '방수공사',
    '브레이스보강': '구조보강공사',
    '고정철물': '구조보강공사',
    '기중기': '장비작업',
    '굴착기': '장비작업',
    '파이프설치': '설비공사',
    '철판보강': '구조보강공사',
    '시트보강': '구조보강공사',
    '덕트설치': '설비공사',
    '덕트철거': '철거공사',
    '연수기이설': '설비공사',
    '헷더 증설': '설비공사',
    '전기배관설치': '전기공사',
    '전기배관철거': '전기공사',
    '분전반설치': '전기공사',
    '전등설치': '전기공사',
}

# 유해위험요인 정규화 (중복 제거용 key)
def normalize(text):
    return re.sub(r'\s+', ' ', text.strip().replace('\n', ' ').replace('-', '').strip())

# CSV 읽기
rows = []
with open('V:/dev/dang/excel_extracted.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"총 행: {len(rows)}")

# 공종 → 세부작업 → [(위험요인, 현재조치, 개선대책, 위험성, 개선후위험성)] 구조 생성
from collections import defaultdict, OrderedDict

data = defaultdict(lambda: defaultdict(list))
seen = set()  # 중복 체크용

for row in rows:
    sheet = row['Sheet'].strip()
    sebu = row['세부작업'].strip()
    wihum_text = row['유해위험요인'].strip()
    p = row['가능성'].strip()
    s = row['중대성'].strip()
    star = row['위험성'].strip()
    daecheck = row['개선대책'].strip()

    if not wihum_text or wihum_text in ('유해위험요인 및 위험성', '유해위험요인', '★', '`'):
        continue

    gongjong = sheet_to_gongjong.get(sheet, sheet)
    wihum_norm = normalize(wihum_text)
    
    # 중복 체크 (같은 공종 내 동일 요인)
    dup_key = f"{gongjong}|{wihum_norm}"
    if dup_key in seen:
        continue
    seen.add(dup_key)

    level = star_to_level(star, p, s)
    after = after_level(level)

    # 세부작업 처리
    if not sebu or sebu in ('작업전', '작업중', '작업후'):
        sebu_label = sheet  # 시트명을 세부작업명으로
        wihum_label = sebu if sebu else '작업위험요인'  # 작업전/중/후를 위험 소분류로
    else:
        sebu_label = sebu
        wihum_label = '일반위험요인'

    data[gongjong][sheet].append({
        'sebu': sebu_label,
        'wihum': wihum_label,
        'wihum_text': wihum_text,
        'daechaek': daecheck,
        'level': level,
        'after': after,
    })

# JS 코드 생성
print("\n=== 공종별 항목 수 ===")
for g, v in sorted(data.items()):
    total = sum(len(items) for items in v.values())
    print(f"  {g}: {total}개 (세부작업: {list(v.keys())})")

# JS 조각 생성
js_output = {}
id_counter = 90000

for gongjong, sheets in data.items():
    js_output[gongjong] = {}
    for sheet_name, items in sheets.items():
        wihum_map = defaultdict(list)
        for item in items:
            wihum_map[item['wihum']].append(item)
        
        for wihum_label, w_items in wihum_map.items():
            arr = []
            for item in w_items:
                arr.append({
                    'id': f"EX{id_counter}",
                    '위험발생및결과': item['wihum_text'],
                    '현재조치': '',
                    '감소대책': item['daechaek'],
                    '위험성': item['level'],
                    '개선후위험성': item['after'],
                })
                id_counter += 1
            
            sebu_key = sheet_name
            if sebu_key not in js_output[gongjong]:
                js_output[gongjong][sebu_key] = {}
            js_output[gongjong][sebu_key][wihum_label] = arr

# JSON으로 저장 (나중에 index.html에 삽입)
with open('V:/dev/dang/excel_merge_data.json', 'w', encoding='utf-8') as f:
    json.dump(js_output, f, ensure_ascii=False, indent=2)

print("[OK] excel_merge_data.json 저장 완료")
print("[OK] 총 신규 항목 ID 할당: EX90000 ~ EX" + str(id_counter-1) + " (" + str(id_counter-90000) + "개)")
