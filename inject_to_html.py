
# -*- coding: utf-8 -*-
"""
excel_merge_data.json → index.html baseRiskData 끝에 병합 삽입 스크립트
"""
import json
import re

# 1. 병합 데이터 로드
with open('V:/dev/dang/excel_merge_data.json', encoding='utf-8') as f:
    new_data = json.load(f)

# 2. index.html 로드
with open('V:/dev/dang/v5_build/index.html', encoding='utf-8') as f:
    html = f.read()

# 3. baseRiskData 끝 위치 찾기 (let baseRiskData = { ... };)
#    baseRiskData의 닫는 부분을 찾아서 그 직전에 신규 공종 삽입
# baseRiskData는 let baseRiskData = { 로 시작하며 }; 로 끝남
# 전략: "let baseRiskData = {" 다음부터 마지막 closing }; 전에 삽입

marker = 'let baseRiskData = {'
pos = html.find(marker)
if pos == -1:
    print("[ERROR] baseRiskData를 찾을 수 없습니다!")
    exit(1)

print(f"[OK] baseRiskData 위치: {pos}")

# baseRiskData 블록의 끝 }; 찾기 (중첩 괄호 카운팅)
start = pos + len(marker)
depth = 1
i = start
while i < len(html) and depth > 0:
    if html[i] == '{':
        depth += 1
    elif html[i] == '}':
        depth -= 1
    i += 1

end_pos = i - 1  # 마지막 } 위치
print(f"[OK] baseRiskData 끝 위치: {end_pos}")
print(f"[OK] baseRiskData 길이: {end_pos - pos} chars")

# 4. 신규 공종 JS 조각 생성
# 기존 공종 목록 파악 (중복 방지는 공종명으로만 체크 - 세부작업 수준 병합은 단순화)
existing_block = html[pos:end_pos+1]

new_entries_js = ''
for gongjong, sheets in new_data.items():
    # 이미 해당 공종명이 baseRiskData에 있는지 확인
    search_key = f'"{gongjong}"'
    if search_key in existing_block:
        # 기존 공종 존재 - 세부작업 추가
        print(f"[MERGE] 기존 공종에 병합: {gongjong}")
        # 간단 처리: 기존 공종 블록 끝에 추가 세부작업을 삽입
        # 여기서는 새로운 공종 키로 추가 (신규 서브공종으로 처리)
        for sheet_name, wihums in sheets.items():
            new_subkey = f"{sheet_name}(신규)"
            # 이 서브공종이 기존에 없는 경우만 삽입할 JS 조각 생성
            sheet_entries = {}
            for wihum_label, items in wihums.items():
                sheet_entries[wihum_label] = items
            
            # 기존 공종 내 해당 세부공종이 없을 경우에만 추가 (단순 문자열 체크)
            if f'"{sheet_name}"' not in existing_block:
                new_entries_js += f'\n                // [엑셀 병합] {gongjong} - {sheet_name}\n'
                new_entries_js += f'                "{sheet_name}": ' + json.dumps(sheet_entries, ensure_ascii=False, indent=24) + ',\n'
    else:
        # 신규 공종 전체 추가
        print(f"[NEW] 신규 공종 추가: {gongjong}")
        gongjong_data = {}
        for sheet_name, wihums in sheets.items():
            gongjong_data[sheet_name] = {}
            for wihum_label, items in wihums.items():
                gongjong_data[sheet_name][wihum_label] = items
        
        new_entries_js += f'\n            // ===== [엑셀 병합] 신규공종: {gongjong} =====\n'
        new_entries_js += f'            "{gongjong}": ' + json.dumps(gongjong_data, ensure_ascii=False, indent=12) + ',\n'

if not new_entries_js.strip():
    print("[SKIP] 추가할 신규 항목이 없습니다.")
else:
    # 5. baseRiskData 닫는 } 직전에 삽입
    insert_pos = end_pos
    # 삽입: 마지막 } 앞에 새 데이터 추가
    new_html = html[:insert_pos] + new_entries_js + html[insert_pos:]
    
    # 6. 백업 후 저장
    import shutil
    shutil.copy('V:/dev/dang/v5_build/index.html', 'V:/dev/dang/v5_build/index.html.bak_before_excel_merge')
    print("[OK] 백업 저장: index.html.bak_before_excel_merge")
    
    with open('V:/dev/dang/v5_build/index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print("[OK] index.html 업데이트 완료!")
    print(f"[OK] 신규 항목 추가: {new_entries_js.count('\"id\": \"EX')}개")
