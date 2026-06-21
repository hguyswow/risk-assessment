import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open(r'D:\dev\dang\v5_build\index.html', encoding='utf-8') as f:
    content = f.read()

checks = [
    ('상단 저장 버튼 제거 확인',      'header-save-btn',             False),
    ('결재설정 버튼 유지',             'open-approval-settings-btn',  True),
    ('불러오기 버튼 유지',             'header-load-btn',             True),
    ('JS headerSaveBtn 코드 제거',     'headerSaveBtn',               False),
    ('JS headerLoadBtn 변수 정의',     'headerLoadBtn',               True),
    ('하단 내보내기(DB) 버튼 유지',    'export-data-btn',             True),
    ('하단 저장(DB) 버튼 유지',        'save-data-btn',               True),
]

scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', content, re.IGNORECASE)
open_cnt  = sum(b.count('{') for b in scripts)
close_cnt = sum(b.count('}') for b in scripts)

print('=== 검증 결과 ===')
all_ok = True
for name, keyword, expect in checks:
    found = keyword in content
    ok    = (found == expect)
    status = 'OK' if ok else '!!'
    flag   = '존재' if found else '없음'
    print(f'  {status}  {name} ({flag})')
    if not ok:
        all_ok = False

# 중괄호 균형
brace_ok = (open_cnt == close_cnt)
print(f'  {"OK" if brace_ok else "!!"} JS 중괄호 균형: 열림:{open_cnt} / 닫힘:{close_cnt}')
if not brace_ok:
    all_ok = False

print()
print('최종:', 'ALL OK' if all_ok else 'ISSUES FOUND')
