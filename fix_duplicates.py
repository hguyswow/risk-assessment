
import json
import os
import sys

# Set encoding to utf-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

file_path = 'd:/dang/data/DATABASE20250617.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

risk_data = data.get('riskData', {})
id_map = {}
duplicates = []
modified_count = 0

def traverse(obj, path=[]):
    global modified_count
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict) and 'id' in item:
                title = item.get('위험발생및결과', '')
                curr_id = item['id']
                
                # Check for the reported items
                if "토치" in title:
                    print(f"Found '토치': {title} (ID: {curr_id}) Path: {' > '.join(path)}")

                # Check for duplicates
                if curr_id in id_map:
                    print(f"Duplicate ID found: {curr_id}")
                    print(f"  Existing: {id_map[curr_id]}")
                    print(f"  New: {title} (Path: {' > '.join(path)})")
                    
                    # Generate new ID
                    new_id = f"{curr_id}_{modified_count + 1}"
                    item['id'] = new_id
                    print(f"  -> Changed ID to: {new_id}")
                    modified_count += 1
                else:
                    id_map[curr_id] = f"{title} (Path: {' > '.join(path)})"

    elif isinstance(obj, dict):
        for k, v in obj.items():
            traverse(v, path + [k])

print("Scanning for duplicates and specific items...")
traverse(risk_data)

if modified_count > 0:
    print(f"\nFixed {modified_count} duplicate IDs.")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("File saved successfully.")
    except Exception as e:
        print(f"Error saving file: {e}")
else:
    print("\nNo duplicate IDs found.")
