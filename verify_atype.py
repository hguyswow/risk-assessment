import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open(r'D:\dev\dang\v5_build\index.html', encoding='utf-8') as f:
    lines = f.readlines()
print(f'총 라인: {len(lines)}')

checks = [
    ('CSS - 트리거 버튼 스타일',            '#assessment-type-trigger-btn {'),
    ('CSS - 모달 스타일',                    '#assessment-type-modal {'),
    ('CSS - atype-option-card',             '.atype-option-card {'),
    ('CSS - 모달 슬라이드 애니메이션',       'atype-slideUp'),
    ('HTML - 트리거 버튼',                  'assessment-type-trigger-btn'),
    ('HTML - 배지 레이블',                   'atype-badge-label'),
    ('HTML - 평가종류 모달',                 'assessment-type-modal'),
    ('HTML - 없음 카드',                    'atype-option-none'),
    ('HTML - 직접입력 카드',                'atype-option-custom'),
    ('HTML - 모달 직접입력 input',           'atype-modal-custom-input'),
    ('HTML - 확인 버튼',                    'atype-modal-confirm-btn'),
    ('JS - bindAssessmentTypeModal IIFE',   'bindAssessmentTypeModal'),
    ('JS - openModal 함수',                 'function openModal()'),
    ('JS - refreshTriggerBtn 함수',         'function refreshTriggerBtn()'),
    ('JS - selectCard 함수',               'function selectCard(val)'),
    ('JS - _restoreAssessmentType 정의',    'window._restoreAssessmentType = function'),
    ('JS - 복원 호출 (3곳 이상)',            'window._restoreAssessmentType) window._restoreAssessmentType'),
    ('보고서 h1 - assessmentType 조건부',   'reportHeaderData.assessmentType'),
    ('파일 끝 정상',                         '</html>'),
]
all_ok = True
for name, kw in checks:
    found = [i+1 for i, l in enumerate(lines) if kw in l]
    if found:
        print(f'  OK  L{found[0]:<7} {name}')
    else:
        print(f'  !! MISSING   {name}')
        all_ok = False

print()
print('최종:', 'ALL OK' if all_ok else 'ISSUES FOUND')
