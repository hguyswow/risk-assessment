import json
import os

file_path = 'd:/dang/data/DATABASE20250617.json'

def refine_data():
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle structural variations
        if 'riskData' in data:
            risk_data = data['riskData']
        else:
            risk_data = data

        count_grade_adjusted = 0
        count_measures_filled = 0

        # Helper to traverse the nested dictionary
        stack = [(risk_data, [])] # (current_node, path)
        
        while stack:
            current, path = stack.pop()
            
            if isinstance(current, dict):
                for key, value in current.items():
                    if isinstance(value, list) and len(value) > 0 and 'id' in value[0]:
                        # Helper for safe int conversion
                        def safe_int(val, default=1):
                            if not val: return default
                            try:
                                return int(val)
                            except ValueError:
                                return default

                        for item in value:
                            # 1. Enforce Grade Limit (Max 3)
                            p2 = safe_int(item.get('개선후가능성', '1'))
                            s2 = safe_int(item.get('개선후중대성', '1'))
                            grade2 = p2 * s2
                            
                            if grade2 > 3:
                                # First, try to reduce Possibility to 1
                                p2 = 1
                                # If still > 3 (meaning S2 > 3), cap Severity at 3
                                if p2 * s2 > 3:
                                    s2 = 3
                                
                                item['개선후가능성'] = str(p2)
                                item['개선후중대성'] = str(s2)
                                item['개선후등급'] = str(p2 * s2)
                                count_grade_adjusted += 1

                            # 2. Fill Missing Measures
                            current_measure = item.get('현재조치', '').strip()
                            improvement_measure = item.get('감소대책', '').strip()
                            risk_desc = item.get('위험발생및결과', '')

                            if not current_measure:
                                # Simple keyword-based filling or default
                                if '추락' in risk_desc:
                                    item['현재조치'] = "안전난간 설치 상태 확인"
                                elif '감전' in risk_desc:
                                    item['현재조치'] = "절연 보호구 착용 확인"
                                elif '화재' in risk_desc:
                                    item['현재조치'] = "화기 작업 허가서 작성"
                                else:
                                    item['현재조치'] = "작업 전 안전교육 및 TBM 실시"
                                count_measures_filled += 1
                            
                            if not improvement_measure:
                                if '추락' in risk_desc:
                                    item['감소대책'] = "안전대 부착설비 설치 및 체결 철저"
                                elif '감전' in risk_desc:
                                    item['감소대책'] = "노전차단기 설치 및 접지 상태 점검"
                                elif '화재' in risk_desc:
                                    item['감소대책'] = "소화기 비치 및 화기감시자 배치"
                                else:
                                    item['감소대책'] = "작업 절차서 준수 및 관리감독 강화"
                                count_measures_filled += 1

                    else:
                        stack.append((value, path + [key]))
            elif isinstance(current, list):
                 # Should have been handled in the loop above if it was a list of items
                 pass

        # Save updated JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Refinement Complete.")
        print(f" - Grades Adjusted (to <= 3): {count_grade_adjusted}")
        print(f" - Measures Filled: {count_measures_filled}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    refine_data()
