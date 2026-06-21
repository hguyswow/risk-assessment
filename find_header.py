import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open(r'D:\dev\dang\v5_build\index.html', encoding='utf-8') as f:
    lines = f.readlines()

targets = [
    'reportHeaderData',
    'headerData',
    'siteName',
    'assessmentType',
    'report-header',
    '위험성 평가서',
    'h1.*위험성',
    'header-form',
    'header.*input',
]
import re
for i, line in enumerate(lines, 1):
    for t in targets:
        if re.search(t, line, re.IGNORECASE):
            print(f'L{i}: {line.rstrip()[:110]}')
            break
