import json

html_path = 'd:/dang/위험성평가실행 C7.html'
json_path = 'd:/dang/data/DATABASE20250617.json'

try:
    # 1. Read JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        
    if 'riskData' in json_data:
        data_to_embed = json_data['riskData']
    else:
        data_to_embed = json_data
        
    # Ensure it is a valid dict
    if not isinstance(data_to_embed, dict):
        raise ValueError("riskData is not a dictionary")

    json_string = json.dumps(data_to_embed, ensure_ascii=False, indent=4)

    # 2. Read HTML
    with open(html_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = -1
    end_idx = -1

    for i, line in enumerate(lines):
        if 'let baseRiskData =' in line:
            start_idx = i
        if 'let riskData = JSON.parse' in line:
            end_idx = i
            break # Stop at the first occurrence after baseRiskData (which should be this one)

    print(f"Found block: {start_idx} to {end_idx}")

    if start_idx == -1 or end_idx == -1:
        raise ValueError("Could not find start or end markers in HTML")
    
    if start_idx >= end_idx:
         # Maybe end_idx was found before start_idx if loop continued? 
         # But we iterate in order.
         # Actually, if 'let riskData =' appears BEFORE baseRiskData? No.
         # Let's double check.
         raise ValueError(f"Invalid indices: {start_idx} >= {end_idx}")

    # 3. Construct new content
    # valid_lines_before = lines[:start_idx]
    # valid_lines_after = lines[end_idx:]
    
    # We want to keep the line "let baseRiskData = ..." but replace its content? 
    # Or replace the whole definition.
    # The original file has:
    # let baseRiskData = {
    #    ...
    # };
    #
    # let riskData = ...
    
    # So we should replace from start_idx up to end_idx (exclusive of end_idx).
    # New content:
    # let baseRiskData = {json_string}; // semicolon
    # \n
    
    new_block = f"        let baseRiskData = {json_string};\n\n"
    
    new_lines = lines[:start_idx] + [new_block] + lines[end_idx:]
    
    # 4. Write back
    with open(html_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("Successfully re-injected baseRiskData.")

except Exception as e:
    print(f"Error: {e}")
