import json

file_path = 'd:/dang/data/DATABASE20250617.json'

def get_measures(danger_text):
    danger = danger_text.lower()
    current_measure = "작업 전 안전교육 실시"
    improvement_measure = "작업공정별 관리감독자 배치"

    if "추락" in danger or "떨어짐" in danger:
        current_measure = "안전난간 설치 및 안전대 착용"
        improvement_measure = "추락방호망 설치 및 안전대 부착설비 점검"
    elif "전도" in danger or "넘어짐" in danger:
        current_measure = "통로 정리정돈 및 작업발판 고정"
        improvement_measure = "미끄럼방지 조치 및 평탄작업 실시"
    elif "충돌" in danger or "부딪힘" in danger:
        current_measure = "신호수 배치 및 경광등 설치"
        improvement_measure = "작업반경 내 출입금지 조치 및 유도자 배치"
    elif "낙하" in danger or "맞음" in danger:
        current_measure = "안전모 착용 및 낙하물방지망 설치"
        improvement_measure = "상부 작업 통제 및 양중기 안전점검"
    elif "감전" in danger:
        current_measure = "절연보호구 착용 및 접지 실시"
        improvement_measure = "누전차단기 설치 및 전선 피복 점검"
    elif "협착" in danger or "끼임" in danger:
        current_measure = "회전체 덮개 설치 및 장갑 사용 금지"
        improvement_measure = "비상정지장치 점검 및 방호장치 설치"
    elif "화재" in danger or "폭발" in danger:
        current_measure = "소화기 비치 및 화기작업 허가제 운영"
        improvement_measure = "가연물 격리 및 불티비산방지포 설치"
    elif "붕괴" in danger or "무너짐" in danger:
        current_measure = "지반 점검 및 거푸집 동바리 점검"
        improvement_measure = "구조검토 실시 및 계측관리"
    elif "질식" in danger or "중독" in danger:
        current_measure = "송기마스크 착용 및 환기 실시"
        improvement_measure = "산소농도 측정 및 밀폐공간 작업프로그램 수립"
    
    return current_measure, improvement_measure

def fill_missing(data):
    if isinstance(data, dict):
        if 'riskData' in data:
            fill_missing(data['riskData'])
        else:
            for key, value in data.items():
                if isinstance(value, list):
                    # Check if it's a list of risk items
                    if value and isinstance(value[0], dict) and '위험발생및결과' in value[0]:
                        for item in value:
                            danger = item.get('위험발생및결과', '')
                            cur, imp = get_measures(danger)
                            
                            if not item.get('현재조치'):
                                item['현재조치'] = cur
                            
                            if not item.get('감소대책'):
                                item['감소대책'] = imp
                            
                            # Ensure risk logic (from previous step) is maintained if we just added fields
                            # But strictly the previous script handled values, this handles strings.
                    else:
                        fill_missing(value)
                elif isinstance(value, dict):
                    fill_missing(value)
    elif isinstance(data, list):
        for item in data:
            fill_missing(item)

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)

    fill_missing(content)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    
    print("Successfully filled missing safety measures.")

except Exception as e:
    print(f"Error: {e}")
