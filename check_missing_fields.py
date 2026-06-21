import json

file_path = 'd:/dang/data/DATABASE20250617.json'

def find_missing_fields(data, missing_list):
    if isinstance(data, dict):
        if 'riskData' in data:
            find_missing_fields(data['riskData'], missing_list)
        else:
            for key, value in data.items():
                if isinstance(value, list):
                     # Check if it's a list of risk items
                    if value and isinstance(value[0], dict) and '위험발생및결과' in value[0]:
                        for item in value:
                            missing = []
                            if not item.get('현재조치'): missing.append('현재조치')
                            if not item.get('감소대책'): missing.append('감소대책')
                            
                            if missing:
                                missing_list.append({
                                    'path': key, # This might be the leaf key
                                    'id': item.get('id'),
                                    'danger': item.get('위험발생및결과'),
                                    'missing': missing
                                })
                    else:
                        find_missing_fields(value, missing_list)
                elif isinstance(value, dict):
                    find_missing_fields(value, missing_list)

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)

    missing_items = []
    find_missing_fields(content, missing_items)

    print(f"Total items with missing fields: {len(missing_items)}")
    for i, item in enumerate(missing_items[:10]): # Show first 10
        print(f"Item {i+1}: {item}")

except Exception as e:
    print(f"Error: {e}")
