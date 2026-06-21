import json
import os

file_path = 'd:/dang/data/DATABASE20250617.json'

def adjust_risk_item(item):
    # Helper to safe convert to int, default 0
    def safe_int(val):
        if isinstance(val, int): return val
        if isinstance(val, str) and val.strip().isdigit(): return int(val)
        return 0

    p1 = safe_int(item.get('가능성', 0))
    s1 = safe_int(item.get('중대성', 0))
    
    p2 = safe_int(item.get('개선후가능성', 0))
    s2 = safe_int(item.get('개선후중대성', 0))

    # Rule 1: Cap at 5 (User said "usually do not exceed 5")
    # If 0, we might leave it or default to 1? Let's assume if it exists it should be >=1.
    # If it was 0/empty, we probably shouldn't invent values, but if it's > 5 we cap.
    if p1 > 5: p1 = 5
    if s1 > 5: s1 = 5
    if p2 > 5: p2 = 5
    if s2 > 5: s2 = 5

    # Rule 2: Risk after improvement <= Current Risk
    # We enforce simplistic rule: P2 <= P1 and S2 <= S1 to guarantee R2 <= R1
    # Actually, sometimes S reduces and P stays same, or P reduces.
    # But R2 must be <= R1.
    # Common pattern in existing data: P reduces to 1, S stays same or reduces.
    
    # Let's ensure P2 is not > P1
    if p2 > p1: p2 = p1
    # Let's ensure S2 is not > S1
    if s2 > s1: s2 = s1

    # Recalculate Grades
    r1 = p1 * s1
    r2 = p2 * s2

    # Update item
    item['가능성'] = str(p1) if p1 > 0 else ""
    item['중대성'] = str(s1) if s1 > 0 else ""
    item['등급'] = str(r1) if r1 > 0 else ""
    
    item['개선후가능성'] = str(p2) if p2 > 0 else ""
    item['개선후중대성'] = str(s2) if s2 > 0 else ""
    item['개선후등급'] = str(r2) if r2 > 0 else ""

    return item

def process_data(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "riskData":
                process_data(value)
            elif isinstance(value, list):
                # This could be the list of items
                # check if items look like risk items
                if value and isinstance(value[0], dict) and '가능성' in value[0]:
                    for item in value:
                        adjust_risk_item(item)
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

    # The structure starts with implicit root or explicit keys.
    # Based on previous `view_file`, it has "riskData" key.
    if 'riskData' in content:
        process_data(content['riskData'])
    else:
        # Fallback if structure is flat for some reason
        process_data(content)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    
    print("Successfully adjusted risk data values.")

except Exception as e:
    print(f"Error: {e}")
