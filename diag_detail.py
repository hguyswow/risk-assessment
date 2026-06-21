import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open(r'D:\dev\dang\v5_build\index.html', encoding='utf-8') as f:
    content = f.read()
lines = content.splitlines()

# 1. 토스트 함수 이름 확인
print('=== Toast 관련 함수/호출 ===')
for i, l in enumerate(lines, 1):
    if 'function' in l and 'oast' in l:
        print(f'  L{i}: {l.strip()[:100]}')
# 토스트 호출 위치도 표시
calls = [(i+1, l.strip()[:80]) for i,l in enumerate(lines) if 'showToast' in l or 'displayToast' in l or 'toast(' in l.lower()]
print(f'  토스트 호출 위치: {len(calls)}곳')
for lineno, text in calls[:5]:
    print(f'    L{lineno}: {text}')

print()

# 2. 위험발생및결과 누락 항목 탐색 (단순 방식)
print('=== 위험발생및결과 누락 항목 탐색 ===')
# id 가진 라인을 기준으로 다음 50줄 안에 위험발생및결과 있는지 확인
missing = []
for i, l in enumerate(lines):
    if '"id"' in l and '"위험발생및결과"' not in l:
        # 주변 50줄 체크
        chunk = '\n'.join(lines[i:i+50])
        if '"위험발생및결과"' not in chunk:
            item_id_m = re.search(r'"id"\s*:\s*"([^"]+)"', l)
            if item_id_m:
                missing.append((i+1, item_id_m.group(1)))

if missing:
    print(f'  !! 누락 의심 항목 {len(missing)}건:')
    for lineno, iid in missing[:10]:
        print(f'    L{lineno}: id={iid}')
        # 주변 5줄 출력
        for j in range(lineno-1, min(lineno+5, len(lines))):
            print(f'      L{j+1}: {lines[j].strip()[:80]}')
else:
    print('  OK 누락 항목 없음')

print()

# 3. 위험성 비정상 값 상세
print('=== 위험성 값 분포 ===')
risk_vals = re.findall(r'"위험성"\s*:\s*"([^"]*)"', content)
dist = {}
for v in risk_vals:
    dist[v] = dist.get(v, 0) + 1
for k, c in sorted(dist.items(), key=lambda x: -x[1]):
    status = 'OK' if k in ('상','중','하','') else '!!'
    print(f'  {status}  "{k}": {c}건')

after_vals = re.findall(r'"개선후위험성"\s*:\s*"([^"]*)"', content)
after_dist = {}
for v in after_vals:
    after_dist[v] = after_dist.get(v, 0) + 1
print('  --- 개선후위험성 ---')
for k, c in sorted(after_dist.items(), key=lambda x: -x[1]):
    status = 'OK' if k in ('상','중','하','') else '!!'
    print(f'  {status}  "{k}": {c}건')
