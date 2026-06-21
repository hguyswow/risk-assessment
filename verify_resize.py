import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open(r'D:\dev\dang\v5_build\index.html', encoding='utf-8') as f:
    content = f.read()
lines = content.splitlines()
print(f'총 라인: {len(lines)}')

# 핵심 체크
checks = [
    ('_reportCols 배열 정의',     "_reportCols = ["),
    ('_totalPx px합계 계산',       "_reportCols.forEach"),
    ('_rw 헬퍼 - 기본값 처리',    "if (!_totalPx) return fallback"),
    ('인쇄 th - _rw 세부작업명',  "_rw('세부작업명'"),
    ('인쇄 th - _rw 유해위험요인', "_rw('유해위험요인'"),
    ('인쇄 th - _rw 개선대책',    "_rw('개선대책'"),
    ('nextTh 역보정 (표 너비 고정)', "nextTh = (thIdx"),
    ('파일 끝 정상',               '</html>'),
]
all_ok = True
for name, kw in checks:
    found = [i+1 for i, l in enumerate(lines) if kw in l]
    if found:
        print(f'  OK  L{found[0]:<7} {name}')
    else:
        print(f'  !! MISSING   {name}')
        all_ok = False

# 실제 _rw 코드 스니펫 출력
print()
print('--- _rw 헬퍼 실제 코드 (L19530~19545) ---')
for l in lines[19529:19546]:
    print(' ', l)

print()
print('최종:', 'ALL OK' if all_ok else 'ISSUES FOUND')
