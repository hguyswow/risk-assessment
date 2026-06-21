
import json
import os
import sys

# Set encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

html_path = 'd:/dang/위험성평가실행 C7.html'
json_path = 'd:/dang/data/DATABASE20250617.json'

new_sub_data = {
    "금속창호(방화문) 설치": [
        {
            "id": "WIN_MT_001",
            "위험발생및결과": "방화문(중량물) 운반 중 낙하로 인한 협착(발끼임)",
            "현재조치": "안전화 착용",
            "감소대책": "2인 1조 운반, 안전화 착용 철저, 이동 경로상 장애물 제거",
            "가능성": "2", "중대성": "3", "등급": "6",
            "개선후가능성": "1", "개선후중대성": "3", "개선후등급": "3"
        },
        {
            "id": "WIN_MT_002",
            "위험발생및결과": "방화문 문틀 용접 작업 중 화재 발생",
            "현재조치": "소화기 비치",
            "감소대책": "용접 불티 비산방지포 설치, 화재감시자 배치, 소화기 근접 비치",
            "가능성": "2", "중대성": "4", "등급": "8",
            "개선후가능성": "1", "개선후중대성": "4", "개선후등급": "4"
        },
        {
            "id": "WIN_MT_003",
            "위험발생및결과": "문틀과 문짝 조립 시 손끼임",
            "현재조치": "작업용 장갑 착용",
            "감소대책": "손끼임 주의, 문짝 하부 고임목 사용, 신호에 맞춰 작업",
            "가능성": "2", "중대성": "2", "등급": "4",
            "개선후가능성": "1", "개선후중대성": "2", "개선후등급": "2"
        },
        {
            "id": "WIN_MT_004",
            "위험발생및결과": "그라인더 절단 작업 중 파편 비산으로 인한 안구 손상",
            "현재조치": "보안경 착용",
            "감소대책": "보안경 및 방진마스크 착용, 그라인더 덮개 부착 상태 확인",
            "가능성": "2", "중대성": "3", "등급": "6",
            "개선후가능성": "1", "개선후중대성": "3", "개선후등급": "3"
        }
    ]
}

try:
    # 1. Update JSON File
    print("Loading JSON data...")
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Ensure '창호공사' exists (it should from previous step)
    if 'riskData' not in json_data:
        json_data['riskData'] = {}
    
    if '창호공사' not in json_data['riskData']:
        print("Note: '창호공사' category not found. Creating it...")
        json_data['riskData']['창호공사'] = {}

    print("Adding Metal Window data...")
    json_data['riskData']['창호공사'].update(new_sub_data)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print("JSON file updated successfully.")

    # 2. Inject into HTML
    print("Loading HTML file...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract riskData
    risk_data_obj = json_data.get('riskData', {})
    new_data_str = json.dumps(risk_data_obj, indent=4, ensure_ascii=False)

    start_marker = 'let baseRiskData = {'
    end_marker = 'let riskData ='

    start_idx = html_content.find(start_marker)
    end_idx = html_content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print("Error: Could not find markers in HTML.")
        sys.exit(1)

    prefix = html_content[:start_idx] + "let baseRiskData = "
    suffix = ";\n\n        " + html_content[end_idx:]

    new_html = prefix + new_data_str + suffix

    print("Writing updated HTML...")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print("HTML updated successfully with new data.")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
