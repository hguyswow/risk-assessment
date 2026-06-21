const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

const tableHeaderOld = `                            <th colspan="3" style="width:12%">현재 위험성</th>
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
                        </tr>`;

const tableHeaderNew = `                            <th style="width:8%">현재 위험성</th>
                            <th style="width:15%">개선대책</th>
                            <th style="width:8%">개선 후 위험성</th>
                            <th style="width:5%">관리</th>
                        </tr>`;

html = html.replace(tableHeaderOld, tableHeaderNew);

const eventListenerOld = `                // 현재 위험성 변경
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
                }`;

const eventListenerNew = `                // 현재 위험성 변경
                if (target.matches('.risk-select')) {
                    const level = target.value;
                    target.style = \`width: 100%; padding: 5px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; \${getRiskStyle(level)}\`;

                    // 데이터 동기화
                    const item = findItemRefById(tr.dataset.id);
                    if (item) {
                        item.위험성 = level;
                    }
                }

                // 개선 후 위험성 변경
                if (target.matches('.risk-select-after')) {
                    const level = target.value;
                    target.style = \`width: 100%; padding: 5px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; \${getRiskStyle(level)}\`;

                    // 데이터 동기화
                    const item = findItemRefById(tr.dataset.id);
                    if (item) {
                        item.개선후위험성 = level;
                    }
                }`;

html = html.replace(eventListenerOld, eventListenerNew);

const createEditRowOld = `        function createEditRow(itemData) {
            const tr = document.createElement('tr');
            tr.dataset.id = itemData.id;
            tr.innerHTML = \`
                <td style="text-align: center;"><input type="checkbox" class="edit-row-checkbox" checked></td>
                <td><div contenteditable="true" data-field="세부작업명">\${itemData.sebu}</div></td>
                <td><div contenteditable="true" data-field="위험세부분류">\${itemData.wihum}</div></td>
                <td><div contenteditable="true" data-field="위험발생및결과">\${itemData.위험발생및결과}</div></td>
                <td><div contenteditable="true" data-field="현재조치">\${itemData.현재조치}</div></td>
                <td><input type="number" class="risk-calc" data-field="가능성" value="\${itemData.가능성 || ''}"></td>
                <td><input type="number" class="risk-calc" data-field="중대성" value="\${itemData.중대성 || ''}"></td>
                <td><input type="number" data-field="등급" value="\${itemData.등급 || ''}" readonly></td>
                <td><div contenteditable="true" data-field="감소대책">\${itemData.감소대책}</div></td>
                <td><input type="number" class="risk-calc-after" data-field="개선후가능성" value="\${itemData.개선후가능성 || ''}"></td>
                <td><input type="number" class="risk-calc-after" data-field="개선후중대성" value="\${itemData.개선후중대성 || ''}"></td>
                <td><input type="number" data-field="개선후등급" value="\${itemData.개선후등급 || ''}" readonly></td>
                <td><button class="delete-btn" style="background-color: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">삭제</button></td>\`;`;

const createEditRowNew = `        function getRiskStyle(level) {
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
            
            tr.innerHTML = \`
                <td style="text-align: center;"><input type="checkbox" class="edit-row-checkbox" checked></td>
                <td><div contenteditable="true" data-field="세부작업명">\${itemData.sebu || ''}</div></td>
                <td><div contenteditable="true" data-field="위험세부분류">\${itemData.wihum || ''}</div></td>
                <td><div contenteditable="true" data-field="위험발생및결과">\${itemData.위험발생및결과 || ''}</div></td>
                <td><div contenteditable="true" data-field="현재조치">\${itemData.현재조치 || ''}</div></td>
                <td>
                    <select class="risk-select" data-field="위험성" style="width: 100%; padding: 5px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; \${getRiskStyle(currentRisk)}">
                        <option value="상" \${currentRisk === '상' ? 'selected' : ''}>상</option>
                        <option value="중" \${currentRisk === '중' ? 'selected' : ''}>중</option>
                        <option value="하" \${currentRisk === '하' ? 'selected' : ''}>하</option>
                    </select>
                </td>
                <td><div contenteditable="true" data-field="감소대책">\${itemData.감소대책 || ''}</div></td>
                <td>
                    <select class="risk-select-after" data-field="개선후위험성" style="width: 100%; padding: 5px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; \${getRiskStyle(afterRisk)}">
                        <option value="상" \${afterRisk === '상' ? 'selected' : ''}>상</option>
                        <option value="중" \${afterRisk === '중' ? 'selected' : ''}>중</option>
                        <option value="하" \${afterRisk === '하' ? 'selected' : ''}>하</option>
                    </select>
                </td>
                <td><button class="delete-btn" style="background-color: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">삭제</button></td>\`;`;

html = html.replace(createEditRowOld, createEditRowNew);

const reportRowOld = `                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">\${item.가능성 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">\${item.중대성 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">\${item.등급 || ''}</td>
                        <td style="border: 1px solid black; padding: 4px; font-size: 9pt;">\${item.감소대책 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">\${item.개선후가능성 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">\${item.개선후중대성 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt;">\${item.개선후등급 || ''}</td>`;

const reportRowNew = `                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt; font-weight: bold; \${item.위험성==='상'?'color:red;':(item.위험성==='중'?'color:orange;':'color:green;')}">\${item.위험성 || ''}</td>
                        <td style="border: 1px solid black; padding: 4px; font-size: 9pt;">\${item.감소대책 || ''}</td>
                        <td style="text-align:center; border: 1px solid black; padding: 4px; font-size: 9pt; font-weight: bold; \${item.개선후위험성==='상'?'color:red;':(item.개선후위험성==='중'?'color:orange;':'color:green;')}">\${item.개선후위험성 || ''}</td>`;

html = html.replace(reportRowOld, reportRowNew);

html = html.replace(/"가능성":\s*"[^"]*",\s*"중대성":\s*"[^"]*",\s*"등급":\s*"(\d+)",\s*"개선후가능성":\s*"[^"]*",\s*"개선후중대성":\s*"[^"]*",\s*"개선후등급":\s*"(\d+)"/g, (match, grade, afterGrade) => {
    let risk = '하';
    let afterRisk = '하';
    if(parseInt(grade) >= 9) risk = '상';
    else if(parseInt(grade) >= 4) risk = '중';
    if(parseInt(afterGrade) >= 9) afterRisk = '상';
    else if(parseInt(afterGrade) >= 4) afterRisk = '중';
    return '"위험성": "' + risk + '",\n                            "개선후위험성": "' + afterRisk + '"';
});

html = html.replace(/"가능성":\s*"",\s*"중대성":\s*"",\s*"등급":\s*"",\s*"개선후가능성":\s*"",\s*"개선후중대성":\s*"",\s*"개선후등급":\s*""/g, '"위험성": "",\n                            "개선후위험성": ""');

const emptyRowOld = `                    <tr style="height: 25px;">
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
                    </tr>`;

const emptyRowNew = `                    <tr style="height: 25px;">
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                        <td style="border: 1px solid black; padding: 4px;">&nbsp;</td>
                    </tr>`;
html = html.replace(emptyRowOld, emptyRowNew);

const reportHeaderOld = `                                <th colspan="3" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt;">현재 위험성</th>
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
                            </tr>`;

const reportHeaderNew = `                                <th rowspan="2" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt; width: 8%;">현재 위험성</th>
                                <th rowspan="2" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt; width: 23%;">개선대책</th>
                                <th rowspan="2" style="border: 1px solid black; background-color: #f0f0f0; text-align: center; padding: 4px; font-weight: bold; font-size: 9pt; width: 8%;">개선 후 위험성</th>
                            </tr>`;
html = html.replace(reportHeaderOld, reportHeaderNew);

const loadDataMatch = `                    data = JSON.parse(rawData);
                    parseSuccess = true;
                    console.log('✅ JSON 파싱 성공');

                    // 2단계: 파일 형식 확인 및 데이터 추출
                    let targetRiskData = null;`;

const loadDataReplace = `                    data = JSON.parse(rawData);
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
                    let targetRiskData = null;`;

html = html.replace(loadDataMatch, loadDataReplace);

fs.writeFileSync('index.html', html, 'utf8');
console.log('Migration script completed successfully.');
