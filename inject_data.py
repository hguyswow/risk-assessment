
import json
import os

html_path = 'd:/dang/위험성평가실행 C7.html'
json_path = 'd:/dang/data/DATABASE20250617.json'

print("Loading JSON data...")
with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# Extract riskData object
risk_data_obj = json_data.get('riskData', {})
# Convert to formatted string, preserving 'let baseRiskData = ' context
new_data_str = json.dumps(risk_data_obj, indent=4, ensure_ascii=False)

print("Loading HTML file...")
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Define markers
start_marker = 'let baseRiskData = {'
end_marker = 'let riskData ='

start_idx = html_content.find(start_marker)
end_idx = html_content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Error: Could not find start or end markers in HTML.")
    exit(1)

print(f"Found markers at {start_idx} and {end_idx}")

# Construct new content
# We replace from start_marker to end_marker
# start_marker is "let baseRiskData = {"
# We want to keep "let baseRiskData = " and then insert property list?
# No, simpler to replace the whole block.

# "let baseRiskData = " length is 19
prefix = html_content[:start_idx] + "let baseRiskData = "
suffix = ";\n\n        " + html_content[end_idx:] # Ensure simplified termination and formatting

new_html = prefix + new_data_str + suffix

print("Writing updated HTML...")
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print("HTML updated successfully.")
