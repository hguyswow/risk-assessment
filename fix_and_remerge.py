
# -*- coding: utf-8 -*-
"""
baseRiskData 복구 스크립트:
- 원본 백업에서 baseRiskData 추출
- 두 엑셀 JSON을 올바르게 병합
- index.html에 정상적으로 삽입
"""
import json, re, shutil

# 1. 두 엑셀 병합 JSON 로드
with open('V:/dev/dang/excel_merge_data.json', encoding='utf-8') as f:
    excel1 = json.load(f)  # 공정별 위험성평가표

with open('V:/dev/dang/excel2_merge_data.json', encoding='utf-8') as f:
    excel2 = json.load(f)  # 소규모 공종 위험성평가

# 2. 원본 백업에서 baseRiskData 추출 (첫 번째 병합 전 백업)
backup_path = 'V:/dev/dang/v5_build/index.html.bak_before_excel_merge'
with open(backup_path, encoding='utf-8') as f:
    original_html = f.read()

# baseRiskData 블록 위치 찾기
marker = 'let baseRiskData = {'
pos = original_html.find(marker)
start = pos + len(marker) - 1  # { 포함
depth, i = 0, start
while i < len(original_html):
    ch = original_html[i]
    if ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: break
    i += 1
end_pos = i

original_base_json_str = original_html[start:end_pos+1]
print(f"원본 baseRiskData JSON 길이: {len(original_base_json_str)}")

# 파싱 테스트
base_data = json.loads(original_base_json_str)
print(f"원본 baseRiskData 파싱 OK: {list(base_data.keys())}")

# 3. 두 엑셀 데이터를 base_data에 병합 (deep merge)
def deep_merge(base, new_data):
    """새 데이터를 base에 병합 - 기존 키는 보존, 신규 키만 추가"""
    for key, val in new_data.items():
        if key not in base:
            base[key] = val
            print(f"  [NEW] {key}")
        elif isinstance(base[key], dict) and isinstance(val, dict):
            deep_merge(base[key], val)
        # 이미 존재하면 스킵 (중복 방지)

print("\n=== 엑셀1 병합 (공정별 위험성평가표) ===")
deep_merge(base_data, excel1)

print("\n=== 엑셀2 병합 (소규모 공종) ===")
deep_merge(base_data, excel2)

# 4. 병합된 JSON 직렬화
merged_json_str = json.dumps(base_data, ensure_ascii=False, indent=12)
print(f"\n병합 후 JSON 길이: {len(merged_json_str)}")

# JSON 파싱 재검증
json.loads(merged_json_str)
print("병합 JSON 검증 OK!")

# 5. 원본 HTML에 삽입
new_html = original_html[:start] + merged_json_str + original_html[end_pos+1:]

# 6. 현재 index.html 백업 후 저장
shutil.copy('V:/dev/dang/v5_build/index.html',
            'V:/dev/dang/v5_build/index.html.bak_broken')
print("손상 버전 백업: index.html.bak_broken")

with open('V:/dev/dang/v5_build/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

final_size = len(new_html)
print(f"[OK] index.html 복구 완료! 최종 크기: {final_size:,} bytes ({final_size/1024:.1f} KB)")
