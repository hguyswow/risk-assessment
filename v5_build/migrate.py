import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Edit table header
html = html.replace('''                            <th colspan="3" style="width:12%">현재 위험성</th>
                            <th style="width:15%">개선대책</th>
                            <th colspan="3" style="width:12%">개선 후 위험성</th>
                            <th style="width:5%">관리</th>
                        </tr>
                        <tr>
                            <th></th>
                            <th></th>
                            <th></th>
                            <th></th>
                            <th></th>
                            <th class="risk-col-edit">가능성</th>
                            <th class="risk-col-edit">중대성</th>
                            <th class="risk-col-edit">등급</th>
                            <th></th>
                            <th class="risk-col-edit">가능성</th>
                            <th class="risk-col-edit">중대성</th>
                            <th class="risk-col-edit">등급</th>
                            <th></th>
                        </tr>''',
'''                            <th style="width:8%">현재 위험성</th>
                            <th style="width:15%">개선대책</th>
                            <th style="width:8%">개선 후 위험성</th>
                            <th style="width:5%">관리</th>
                        </tr>''')

# 2. Event listeners
old_listeners = '''                // 현재 위험성 변경
                if (target.matches('.risk-calc')) {
                    const pInput = tr.querySelector('input[data-field="가능성"]');
                    const sInput = tr.querySelector('input[data-field="중대성"]');
                    const gradeInput = tr.querySelector('input[data-field="등급"]');

                    const p = parseInt(pInput.value) || 0;
                    const s = parseInt(sInput.value) || 0;
                    const grade = p * s;

                    gradeInput.value = grade;

                    // 데이터 동기화
                    const item = findItemRefById(tr.dataset.id);
                    if (item) {
                        item.가능성 = p;
                        item.중대성 = s;
                        item.등급 = grade;
                    }
                }

                // 개선 후 위험성 변경
                if (target.matches('.risk-calc-after')) {
                    const pInput = tr.querySelector('input[data-field="개선후가능성"]');
                    const sInput = tr.querySelector('input[data-field="개선후중대성"]');
                    const gradeInput = tr.querySelector('input[data-field="개선후등급"]');

                    const p = parseInt(pInput.value) || 0;
                    const s = parseInt(sInput.value) || 0;
                    const grade = p * s;

                    gradeInput.value = grade;

                    // 데이터 동기화
                    const item = findItemRefById(tr.dataset.id);
                    if (item) {
                        item.개선후가능성 = p;
                        item.개선후중대성 = s;
                        item.개선후등급 = grade;
                    }
                }'''

new_listeners = '''                // 현재 위험성 변경
                if (target.matches('.risk-select')) {
                    const level = target.value;
                    target.style = `width: 100%; padding: 5px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; ${getRiskStyle(level)}`;

                    // 데이터 동기화
                    const item = findItemRefById(tr.dataset.id);
                    if (item) {
                        item.위험성 = level;
                    }
                }

                // 개선 후 위험성 변경
                if (target.matches('.risk-select-after')) {
                    const level = target.value;
                    target.style = `width: 100%; padding: 5px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; ${getRiskStyle(level)}`;

                    // 데이터 동기화
                    const item = findItemRefById(tr.dataset.id);
                    if (item) {
                        item.개선후위험성 = level;
                    }
                }'''

html = html.replace(old_listeners, new_listeners)

# 3. createEditRow
old_row = '''        function createEditRow(itemData) {
            const tr = document.createElement('tr');
            tr.dataset.id = itemData.id;
            tr.innerHTML = `
                <td style="text-align: center;"><input type="checkbox" class="edit-row-checkbox" checked></td>
                <td><div contenteditable="true" data-field="세부작업명">${itemData.sebu}</div></td>
                <td><div contenteditable="true" data-field="위험세부분류">${itemData.wihum}</div></td>
                <td><div contenteditable="true" data-field="위험발생및결과">${itemData.위험발생및결과}</div></td>
                <td><div contenteditable="true" data-field="현재조치">${itemData.현재조치}</div></td>
                <td><input type="number" class="risk-calc" data-field="가능성" value="${itemData.가능성 || ''}"></td>
                <td><input type="number" class="risk-calc" data-field="중대성" value="${itemData.중대성 || ''}"></td>
                <td><input type="number" data-field="등급" value="${itemData.등급 || ''}" readonly></td>
                <td><div contenteditable="true" data-field="감소대책">${itemData.감소대책}</div></td>
                <td><input type="number" class="risk-calc-after" data-field="개선후가능성" value="${itemData.개선후가능성 || ''}"></td>
                <td><input type="number" class="risk-calc-after" data-field="개선후중대성" value="${itemData.개선후중대성 || ''}"></td>
                <td><input type="number" data-field="개선후등급" value="${itemData.개선후등급 || ''}" readonly></td>
                <td><button class="delete-btn" style="background-color: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">삭제</button></td>`;'''

new_row = '''        function getRiskStyle(level) {
            if (level === '상') return 'color: white; background-color: #e74c3c;';
            if (level === '중') return 'color: white; background-color: #f39c12;';
            if (level === '하') return 'color: white; background-color: #27ae60;';
            return 'background-color: #fff;';
        }

        function createEditRow(itemData) {
            const tr = document.createElement('tr');
            tr.dataset.id = itemData.id;
            
            const currentRisk = itemData.위험성 || '중';
            const afterRisk = itemData.개선후위험성 || '하';
            
            tr.innerHTML = `
                <td style="text-align: center;"><input type="checkbox" class="edit-row-checkbox" checked></td>
                <td><div contenteditable="true" data-field="세부작업명">${itemData.sebu || ''}</div></td>
                <td><div contenteditable="true" data-field="위험세부분류">${itemData.wihum || ''}</div></td>
                <td><div contenteditable="true" data-field="위험발생및결과">${itemData.위험발생및결과 || ''}</div></td>
                <td><div contenteditable="true" data-field="현재조치">${itemData.현재조치 || ''}</div></td>
                <td>
                    <select class="risk-select" data-field="위험성" style="width: 100%; padding: 5px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; ${getRiskStyle(currentRisk)}">
                        <option value="상" ${currentRisk === '상' ? 'selected' : ''}>상</option>
                        <option value="중" ${currentRisk === '중' ? 'selected' : ''}>중</option>
                        <option value="하" ${currentRisk === '하' ? 'selected' : ''}>하</option>
                    </select>
                </td>
                <td><div contenteditable="true" data-field="감소대책">${itemData.감소대책 || ''}</div></td>
                <td>
                    <select class="risk-select-after" data-field="개선후위험성" style="width: 100%; padding: 5px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; ${getRiskStyle(afterRisk)}">
                        <option value="상" ${afterRisk === '상' ? 'selected' : ''}>상</option>
                        <option value="중" ${afterRisk === '중' ? 'selected' : ''}>중</option>
                        <option value="하" ${afterRisk === '하' ? 'selected' : ''}>하</option>
                    </select>
                </td>
                <td><button class="delete-btn" style="background-color: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">삭제</button></td>`;'''

html = html.replace(old_row, new_row)

# 4. Report Rows
old_report_row = '''                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">${item.가능성 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">${item.중대성 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">${item.등급 || ''}</td>
                        <td style="border: 1px solid black; padding: 4px; font-size: 9pt;">${item.감소대책 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">${item.개선후가능성 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">${item.개선후중대성 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">${item.개선후등급 || ''}</td>'''

new_report_row = '''                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt; font-weight: bold; ${item.위험성==='상'?'color:red;':(item.위험성==='중'?'color:orange;':'color:green;')}">${item.위험성 || ''}</td>
                        <td style="border: 1px solid black; padding: 4px; font-size: 9pt;">${item.감소대책 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt; font-weight: bold; ${item.개선후위험성==='상'?'color:red;':(item.개선후위험성==='중'?'color:orange;':'color:green;')}">${item.개선후위험성 || ''}</td>'''

html = html.replace(old_report_row, new_report_row)

# 5. Report empty rows
old_empty = '''                    <tr style="height: 25px;">
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                    </tr>'''

new_empty = '''                    <tr style="height: 25px;">
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                    </tr>'''

html = html.replace(old_empty, new_empty)

# 6. Report Header
old_rep_head = '''                                <th colspan="3" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt;">현재 위험성</th>
                                <th rowspan="2" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt; width: 15%;">개선대책</th>
                                <th colspan="3" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt;">개선 후 위험성</th>
                            </tr>
                            <tr>
                                <th style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 8pt; width: 4%;">가능성</th>
                                <th style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 8pt; width: 4%;">중대성</th>
                                <th style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 8pt; width: 4%;">등급</th>
                                <th style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 8pt; width: 4%;">가능성</th>
                                <th style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 8pt; width: 4%;">중대성</th>
                                <th style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 8pt; width: 4%;">등급</th>
                            </tr>'''

new_rep_head = '''                                <th rowspan="2" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt; width: 8%;">현재 위험성</th>
                                <th rowspan="2" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt; width: 23%;">개선대책</th>
                                <th rowspan="2" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt; width: 8%;">개선 후 위험성</th>
                            </tr>'''

html = html.replace(old_rep_head, new_rep_head)

# 7. Migration Logic
old_mig = '''                    data = JSON.parse(rawData);
                    parseSuccess = true;
                    console.log('✅ JSON 파싱 성공');

                    // 2단계: 파일 형식 확인 및 데이터 추출
                    let targetRiskData = null;'''

new_mig = '''                    data = JSON.parse(rawData);
                    parseSuccess = true;
                    console.log('✅ JSON 파싱 성공');

                    // [마이그레이션] 상중하 판단법 변환 (구버전 호환)
                    const migrateData = (dataObj) => {
                        for (const gongjong in dataObj) {
                            for (const sebu in dataObj[gongjong]) {
                                for (const wihum in dataObj[gongjong][sebu]) {
                                    if(Array.isArray(dataObj[gongjong][sebu][wihum])) {
                                        dataObj[gongjong][sebu][wihum].forEach(item => {
                                            if (item.등급 !== undefined && !item.위험성) {
                                                const grade = parseInt(item.등급) || 0;
                                                if (grade >= 9) item.위험성 = "상";
                                                else if (grade >= 4) item.위험성 = "중";
                                                else item.위험성 = "하";
                                            }
                                            if (item.개선후등급 !== undefined && !item.개선후위험성) {
                                                const afterGrade = parseInt(item.개선후등급) || 0;
                                                if (afterGrade >= 9) item.개선후위험성 = "상";
                                                else if (afterGrade >= 4) item.개선후위험성 = "중";
                                                else item.개선후위험성 = "하";
                                            }
                                        });
                                    }
                                }
                            }
                        }
                    };
                    
                    if(data.riskData) migrateData(data.riskData);
                    else migrateData(data); // 레거시 포맷

                    // 2단계: 파일 형식 확인 및 데이터 추출
                    let targetRiskData = null;'''

html = html.replace(old_mig, new_mig)

# If carriage returns were different, we should fix that
# Actually, let's normalize everything to \n for replace, and then write back
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('\\r\\n', '\\n')

# RE-DO all replacements on normalized string
old_row = old_row.replace('\\r\\n', '\\n')
new_row = new_row.replace('\\r\\n', '\\n')
html = html.replace(old_row, new_row)

old_listeners = old_listeners.replace('\\r\\n', '\\n')
new_listeners = new_listeners.replace('\\r\\n', '\\n')
html = html.replace(old_listeners, new_listeners)

old_report_row = old_report_row.replace('\\r\\n', '\\n')
new_report_row = new_report_row.replace('\\r\\n', '\\n')
html = html.replace(old_report_row, new_report_row)

old_empty = old_empty.replace('\\r\\n', '\\n')
new_empty = new_empty.replace('\\r\\n', '\\n')
html = html.replace(old_empty, new_empty)

old_rep_head = old_rep_head.replace('\\r\\n', '\\n')
new_rep_head = new_rep_head.replace('\\r\\n', '\\n')
html = html.replace(old_rep_head, new_rep_head)

old_mig = old_mig.replace('\\r\\n', '\\n')
new_mig = new_mig.replace('\\r\\n', '\\n')
html = html.replace(old_mig, new_mig)

old_h = '''                            <th colspan="3" style="width:12%">현재 위험성</th>
                            <th style="width:15%">개선대책</th>
                            <th colspan="3" style="width:12%">개선 후 위험성</th>
                            <th style="width:5%">관리</th>
                        </tr>
                        <tr>
                            <th></th>
                            <th></th>
                            <th></th>
                            <th></th>
                            <th></th>
                            <th class="risk-col-edit">가능성</th>
                            <th class="risk-col-edit">중대성</th>
                            <th class="risk-col-edit">등급</th>
                            <th></th>
                            <th class="risk-col-edit">가능성</th>
                            <th class="risk-col-edit">중대성</th>
                            <th class="risk-col-edit">등급</th>
                            <th></th>
                        </tr>'''
new_h = '''                            <th style="width:8%">현재 위험성</th>
                            <th style="width:15%">개선대책</th>
                            <th style="width:8%">개선 후 위험성</th>
                            <th style="width:5%">관리</th>
                        </tr>'''
old_h = old_h.replace('\\r\\n', '\\n')
new_h = new_h.replace('\\r\\n', '\\n')
html = html.replace(old_h, new_h)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Python Migration finished.")
