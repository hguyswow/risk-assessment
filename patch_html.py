import json
import re

html_path = 'd:/dang/위험성평가실행 C7.html'
json_path = 'd:/dang/data/DATABASE20250617.json'

try:
    # 1. Read the JSON Data
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Check if 'riskData' is at root or needs extraction
    if 'riskData' in json_data:
        base_risk_data = json_data['riskData']
    else:
        base_risk_data = json_data # Assuming root is riskData if not present
        
    json_string = json.dumps(base_risk_data, ensure_ascii=False, indent=4)

    # 2. Read the HTML
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 3. Replace baseRiskData
    # Regex to find: let baseRiskData = { ... };
    # We look for `let baseRiskData = {` until `};`
    # Be careful with nested braces. Since the original file is formatted, we can match broad structure.
    # A safer way might be to identify the specific start and end lines or use a robust regex.
    # The original file has:
    # let baseRiskData = {
    #    ...
    # };
    
    # Let's try to find the start and end of the object literal or just key off the variable name.
    # Since we know the structure of the existing variable is likely simple in the provided code snippet (lines 828-850),
    # we can replace everything from `let baseRiskData = {` to the first `};` that follows.
    
    pattern = r'(let baseRiskData = )\{[\s\S]*?\};'
    replacement = f'let baseRiskData = {json_string};'
    
    new_html_content = re.sub(pattern, replacement, html_content, count=1)
    
    if new_html_content == html_content:
        print("Warning: Could not find 'let baseRiskData = { ... };' to replace.")
    else:
        print("Successfully replaced baseRiskData.")

    # 4. Update CSS for input fields
    # Find `.editing-table td > input[type="number"] {` and inject improved styles
    css_pattern = r'(\.editing-table td > input\[type="number"\] \{\s*)([^}]*)(\})'
    
    def css_replacer(match):
        original_styles = match.group(2)
        new_styles = original_styles + '\n            font-weight: bold;\n            font-size: 13px;\n            color: #000;\n            background-color: #fff;'
        return match.group(1) + new_styles + match.group(3)

    new_html_content_css = re.sub(css_pattern, css_replacer, new_html_content)
    
    if new_html_content_css == new_html_content:
         print("Warning: Could not find CSS to update.")
    else:
         print("Successfully updated CSS.")

    # 5. Write back
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html_content_css)
        
    print("HTML file updated successfully.")

except Exception as e:
    print(f"Error: {e}")
