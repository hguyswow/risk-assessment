import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open(r'D:\dev\dang\v5_build\index.html', encoding='utf-8') as f:
    lines = f.readlines()

keywords = ['renderReport', 'report-preview', 'generateReport', 'printReport', 'buildReport',
            'generate-report', 'report_preview', 'innerHTML.*table', 'report.*thead']
for i, line in enumerate(lines, 1):
    for k in keywords:
        import re
        if re.search(k, line, re.IGNORECASE):
            print(f'L{i}: {line.rstrip()[:110]}')
            break
