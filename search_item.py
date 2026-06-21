import json

path = 'd:/dang/data/DATABASE20250617.json'

try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    found = False
    
    # Simple recursive search
    stack = [data]
    while stack:
        curr = stack.pop()
        if isinstance(curr, dict):
            for k, v in curr.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and '사다리 위 작업 중 추락' in item.get('위험발생및결과', ''):
                            print(f"Found Item: {item}")
                            found = True
                else:
                    stack.append(v)
    
    if not found:
        print("Item NOT found.")

except Exception as e:
    print(f"Error: {e}")
