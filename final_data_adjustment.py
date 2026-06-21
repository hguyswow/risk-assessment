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

def safe_int(val):
    if isinstance(val, int): return val
    if isinstance(val, str) and val.strip().isdigit(): return int(val)
    return 0

def process_item(item):
    # 1. Fill Missing Measures
    danger = item.get('위험발생및결과', '')
    cur_fill, imp_fill = get_measures(danger)
    
    # Check if empty or just whitespace
    if not item.get('현재조치') or not item.get('현재조치', '').strip():
        item['현재조치'] = cur_fill
    if not item.get('감소대책') or not item.get('감소대책', '').strip():
        item['감소대책'] = imp_fill

    # 2. Enforce Grade Rules
    p1 = safe_int(item.get('가능성', 0))
    s1 = safe_int(item.get('중대성', 0))
    
    # Ensure current risk is reasonable (max 5)
    if p1 > 5: p1 = 5
    if s1 > 5: s1 = 5
    
    # Current Grade
    r1 = p1 * s1
    
    # Get initial After values
    p2 = safe_int(item.get('개선후가능성', 0))
    s2 = safe_int(item.get('개선후중대성', 0))
    
    # If not set, initialize based on P1, S1
    if p2 == 0: p2 = max(1, p1 - 1)
    if s2 == 0: s2 = s1 # Severity usually stays, or reduces

    # NEW RULE: After Grade (p2 * s2) must be <= 3
    # Also P2 <= P1, S2 <= S1
    
    # Heuristic optimization to find best (P2, S2)
    # Priority: Reduce P2 first, then S2 if needed.
    # Constraints: 1 <= P2 <= P1, 1 <= S2 <= S1, P2*S2 <= 3
    
    # Start with current proposal
    if p2 > p1: p2 = p1
    if s2 > s1: s2 = s1
    
    # Loop to reduce until valid
    while (p2 * s2) > 3:
        # If we can reduce P2, do it
        if p2 > 1:
            p2 -= 1
        # If P2 is 1 and still > 3 (meaning S2 > 3), reduce S2
        elif s2 > 3:
            s2 = 3 # Force severity down to 3 if P is 1 (1*3=3 is ok)
            # If S2 was 4 or 5, we have to reduce it to 3 to meet the requirement.
            # (1, 4) = 4 > 3 -> Fail. So S2 must be <= 3.
        else:
            # Should not happen if logic is correct (1*1=1, 1*2=2, 1*3=3)
            break
            
    r2 = p2 * s2

    # Update item
    item['가능성'] = str(p1) if p1 > 0 else ""
    item['중대성'] = str(s1) if s1 > 0 else ""
    item['등급'] = str(r1) if r1 > 0 else ""
    
    item['개선후가능성'] = str(p2) if p2 > 0 else ""
    item['개선후중대성'] = str(s2) if s2 > 0 else ""
    item['개선후등급'] = str(r2) if r2 > 0 else ""

def process_data(data):
    if isinstance(data, dict):
        if 'riskData' in data:
            process_data(data['riskData'])
        else:
            for key, value in data.items():
                if isinstance(value, list):
                    if value and isinstance(value[0], dict) and '위험발생및결과' in value[0]:
                        for item in value:
                            process_item(item)
                    else:
                        process_data(value)
                elif isinstance(value, dict):
                    process_data(value)
    elif isinstance(data, list):
        for item in data:
            process_data(item)

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)

    process_data(content)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    
    print("Successfully enforced Grade <= 3 rule and filled missing data.")

except Exception as e:
    print(f"Error: {e}")
