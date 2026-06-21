
import json
import os
import sys

# Set encoding to utf-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

html_path = 'd:/dang/위험성평가실행 C7.html'
json_path = 'd:/dang/data/DATABASE20250617.json'

new_data = {
    "유리 공사": {
        "자재 반입 및 인양": [
            {
                "id": "WIN_GL_001",
                "위험발생및결과": "유리 파렛트 인양 중 와이어로프 파단으로 인한 자재 낙하",
                "현재조치": "인양용 전용 슬링벨트 사용",
                "감소대책": "인양 하중 사전 검토 및 신호수 배치, 하부 통제 철저",
                "가능성": "2", "중대성": "3", "등급": "6",
                "개선후가능성": "1", "개선후중대성": "3", "개선후등급": "3"
            },
            {
                "id": "WIN_GL_002",
                "위험발생및결과": "유리 운반 중 파손되어 파편에 의한 베임",
                "현재조치": "베임 방지용 장갑 착용",
                "감소대책": "유리 압착기 사용 및 보호구(베임방지 장갑, 팔토시) 착용 철저",
                "가능성": "2", "중대성": "2", "등급": "4",
                "개선후가능성": "1", "개선후중대성": "2", "개선후등급": "2"
            }
        ],
        "유리 끼우기 및 코킹": [
            {
                "id": "WIN_GL_003",
                "위험발생및결과": "고소 작업(외부 창호) 중 작업발판 미설치로 인한 추락",
                "현재조치": "안전벨트 착용",
                "감소대책": "비계 및 작업발판 견고한 설치, 안전대 부착설비 확보 후 작업",
                "가능성": "2", "중대성": "4", "등급": "8",
                "개선후가능성": "1", "개선후중대성": "4", "개선후등급": "4"
            },
            {
                "id": "WIN_GL_004",
                "위험발생및결과": "코킹 작업 중 유기용제(신너 등) 중독",
                "현재조치": "마스크 착용",
                "감소대책": "환기 조치 실시 및 유기화합물용 방독마스크 착용",
                "가능성": "2", "중대성": "2", "등급": "4",
                "개선후가능성": "1", "개선후중대성": "2", "개선후등급": "2"
            },
             {
                "id": "WIN_GL_005",
                "위험발생및결과": "유리 끼우기 중 유리 이탈로 인한 낙하사고",
                "현재조치": "2인 1조 작업",
                "감소대책": "하부 출입통제 구역 설정 및 감시자 배치",
                "가능성": "2", "중대성": "3", "등급": "6",
                "개선후가능성": "1", "개선후중대성": "3", "개선후등급": "3"
            }
        ]
    },
    "알루미늄(AL) 창호 공사": {
        "창호 프레임 설치": [
            {
                "id": "WIN_AL_001",
                "위험발생및결과": "창호 프레임 용접 작업 중 불티 비산으로 인한 화재",
                "현재조치": "소화기 비치",
                "감소대책": "불티비산방지포 설치 및 화기감시자 배치, 소화기 근접 비치",
                "가능성": "2", "중대성": "3", "등급": "6",
                "개선후가능성": "1", "개선후중대성": "3", "개선후등급": "3"
            },
            {
                "id": "WIN_AL_002",
                "위험발생및결과": "개구부 주변 작업 중 몸 균형 상실로 추락",
                "현재조치": "안전난간 설치",
                "감소대책": "개구부 덮개 또는 안전난간 설치 상태 확인 후 작업, 안전대 착용",
                "가능성": "2", "중대성": "4", "등급": "8",
                "개선후가능성": "1", "개선후중대성": "4", "개선후등급": "4"
            },
             {
                "id": "WIN_AL_003",
                "위험발생및결과": "프레임 인양 및 설치 중 손끼임",
                "현재조치": "협착주의 교육",
                "감소대책": "신호수 신호에 맞춰 작업 및 손 끼임 주의 표지 부착",
                "가능성": "2", "중대성": "2", "등급": "4",
                "개선후가능성": "1", "개선후중대성": "2", "개선후등급": "2"
            }
        ],
        "창짝(Sash) 설치": [
             {
                "id": "WIN_AL_004",
                "위험발생및결과": "무거운 창짝 운반 중 허리 부상 (요통)",
                "현재조치": "2인 1조 운반",
                "감소대책": "중량물 취급 요령 교육 및 기계적 운반구 사용 권장",
                "가능성": "2", "중대성": "2", "등급": "4",
                "개선후가능성": "1", "개선후중대성": "2", "개선후등급": "2"
            },
            {
                "id": "WIN_AL_005",
                "위험발생및결과": "전동공구(드릴 등) 사용 중 감전",
                "현재조치": "이중절연 공구 사용",
                "감소대책": "누전차단기 접속 확인 및 전선 피복 상태 점검",
                "가능성": "2", "중대성": "2", "등급": "4",
                "개선후가능성": "1", "개선후중대성": "2", "개선후등급": "2"
            }
        ]
    }
}

try:
    # 1. Update JSON File
    print("Loading JSON data...")
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    print("Adding Window Construction data...")
    if 'riskData' not in json_data:
        json_data['riskData'] = {}
    
    # Add or Merge '창호공사'
    if '창호공사' not in json_data['riskData']:
         json_data['riskData']['창호공사'] = new_data
         print("Created new category: 창호공사")
    else:
         json_data['riskData']['창호공사'].update(new_data)
         print("Updated existing category: 창호공사")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print("JSON file updated successfully.")

    # 2. Inject into HTML
    print("Loading HTML file...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract riskData object from JSON
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
