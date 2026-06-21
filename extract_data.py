import sys, re

path = r'D:\dev\dang\v5_build\index.html'
out_path = r'D:\dev\dang\v5_build\data.js'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('let baseRiskData = {')
if start_idx == -1:
    print("Cannot find baseRiskData")
    sys.exit(1)

brace_count = 0
end_idx = -1
in_string = False
escape = False
quote_char = ''

for i in range(start_idx + 19, len(content)):
    c = content[i]
    if escape:
        escape = False
        continue
    if c == '\\':
        escape = True
        continue
    
    if in_string:
        if c == quote_char:
            in_string = False
    else:
        if c in ('"', "'", '`'):
            in_string = True
            quote_char = c
        elif c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break

if end_idx == -1:
    print("Cannot find end of baseRiskData")
    sys.exit(1)

data_str = content[start_idx:end_idx+1]
if content[end_idx+1] == ';':
    end_idx += 1
    data_str += ';'

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(data_str + '\n')

new_content = content[:start_idx] + "/* baseRiskData는 외부 data.js 파일에서 로드됨 */" + content[end_idx+1:]

script_idx = new_content.rfind('<script>', 0, start_idx)
if script_idx != -1:
    new_content = new_content[:script_idx] + '<script src="data.js"></script>\n    ' + new_content[script_idx:]
else:
    print("Cannot find <script> tag before baseRiskData")

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Extraction successful! Saved to data.js")
