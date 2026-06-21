import sys, re

path = r'E:\dev\dang\v5_build\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. State data addition
state_init = """let photoBoardData = {
    enabled: false,
    photo1: '',
    text1: '',
    photo2: '',
    text2: ''
};
"""
# find where `let reportHeaderData` is
if 'let photoBoardData =' not in content:
    content = content.replace('let reportHeaderData = {};', 'let reportHeaderData = {};\n' + state_init)

# 2. saveUserData addition
save_old = """                    headerData: reportHeaderData,"""
save_new = """                    headerData: reportHeaderData,
                    photoBoardData: photoBoardData,"""
if 'photoBoardData: photoBoardData' not in content:
    content = content.replace(save_old, save_new)

# 3. loadProject addition
load_old = """                reportHeaderData = userData.headerData || {};"""
load_new = """                reportHeaderData = userData.headerData || {};
                photoBoardData = userData.photoBoardData || {enabled: false, photo1: '', text1: '', photo2: '', text2: ''};"""
if 'photoBoardData = userData.photoBoardData' not in content:
    content = content.replace(load_old, load_new)

# 4. Action button addition
btn_old = """                <button id="save-manual-btn" style="background-color: #17a2b8;">💾 저장</button>"""
btn_new = """                <button id="save-manual-btn" style="background-color: #17a2b8;">💾 저장</button>
                <button id="photo-board-settings-btn" style="background-color: #6f42c1; color: white;" onclick="openPhotoBoardModal()">📸 사진대지 설정</button>"""
if 'photo-board-settings-btn' not in content:
    content = content.replace(btn_old, btn_new)

# 5. CSS addition
css_old = """</style>"""
css_new = """
        /* 사진대지 모달 및 인쇄 스타일 */
        @page portrait_page {
            size: A4 portrait;
            margin: 1cm;
        }
        .photo-board-page {
            page: portrait_page;
            page-break-before: always;
            width: 100%;
            font-family: 'Malgun Gothic', sans-serif;
            box-sizing: border-box;
            background: white;
            color: black;
        }
        .pb-title {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            letter-spacing: 5px;
        }
        .pb-container {
            border: 2px solid #000;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .pb-item {
            width: 100%;
        }
        .pb-photo-box {
            width: 100%;
            height: 350px;
            border: 1px solid #000;
            border-bottom: none;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            background-color: white;
        }
        .pb-photo-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        .pb-table {
            width: 100%;
            border-collapse: collapse;
        }
        .pb-table th, .pb-table td {
            border: 1px solid #000;
            padding: 8px;
            text-align: center;
            font-size: 14px;
        }
        .pb-table th {
            width: 15%;
            background-color: #f2f2f2 !important;
            -webkit-print-color-adjust: exact;
            color: black;
        }
        .pb-table td {
            text-align: left;
        }
        .pb-table .pb-center {
            text-align: center;
        }
        
        #photo-board-modal .modal-content {
            max-width: 700px;
        }
        .pb-upload-area {
            border: 1px dashed #ccc;
            padding: 10px;
            text-align: center;
            margin-bottom: 10px;
            cursor: pointer;
            background: #f9f9f9;
            height: 200px;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            overflow: hidden;
        }
        .pb-upload-area img {
            max-width: 100%;
            max-height: 100%;
            display: none;
        }
</style>
"""
if '.photo-board-page {' not in content:
    content = content.replace(css_old, css_new)

# 6. Modal HTML addition
modal_html = """
    <!-- 사진대지 설정 모달 -->
    <div id="photo-board-modal" class="modal">
        <div class="modal-content">
            <h2>📸 사진대지 설정</h2>
            <div style="margin-bottom: 20px; border-bottom: 1px solid #ddd; padding-bottom: 15px;">
                <label style="font-weight: bold; font-size: 16px; cursor: pointer;">
                    <input type="checkbox" id="pb-enable-checkbox" style="transform: scale(1.5); margin-right: 10px;" onchange="togglePbForms(this.checked)">
                    보고서 인쇄 시 사진대지 포함 (A4 세로)
                </label>
            </div>
            
            <div id="pb-forms" style="display: none;">
                <div style="display: flex; gap: 20px;">
                    <!-- 사진 1 -->
                    <div style="flex: 1; border: 1px solid #ddd; padding: 10px; border-radius: 8px;">
                        <h3 style="font-size: 16px; margin-top: 0; text-align: center;">사진 1</h3>
                        <div class="pb-upload-area" id="pb-upload-area-1" onclick="document.getElementById('pb-file-1').click()">
                            <span id="pb-placeholder-1">클릭하여 사진 추가</span>
                            <img id="pb-preview-1" src="" alt="사진 1">
                        </div>
                        <input type="file" id="pb-file-1" accept="image/*" style="display: none;" onchange="handlePbImageUpload(this, 1)">
                        <div style="text-align: center; margin-bottom: 5px;">
                            <button type="button" onclick="clearPbImage(1)" style="padding: 4px 8px; font-size: 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">사진 지우기</button>
                        </div>
                        <div>
                            <label style="font-size: 12px; font-weight: bold;">내용:</label>
                            <input type="text" id="pb-text-1" style="width: 100%; padding: 8px; border: 1px solid #ccc; box-sizing: border-box;" placeholder="사진 1에 대한 설명">
                        </div>
                    </div>
                    
                    <!-- 사진 2 -->
                    <div style="flex: 1; border: 1px solid #ddd; padding: 10px; border-radius: 8px;">
                        <h3 style="font-size: 16px; margin-top: 0; text-align: center;">사진 2</h3>
                        <div class="pb-upload-area" id="pb-upload-area-2" onclick="document.getElementById('pb-file-2').click()">
                            <span id="pb-placeholder-2">클릭하여 사진 추가</span>
                            <img id="pb-preview-2" src="" alt="사진 2">
                        </div>
                        <input type="file" id="pb-file-2" accept="image/*" style="display: none;" onchange="handlePbImageUpload(this, 2)">
                        <div style="text-align: center; margin-bottom: 5px;">
                            <button type="button" onclick="clearPbImage(2)" style="padding: 4px 8px; font-size: 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">사진 지우기</button>
                        </div>
                        <div>
                            <label style="font-size: 12px; font-weight: bold;">내용:</label>
                            <input type="text" id="pb-text-2" style="width: 100%; padding: 8px; border: 1px solid #ccc; box-sizing: border-box;" placeholder="사진 2에 대한 설명">
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="action-buttons" style="margin-top: 20px; text-align: right;">
                <button onclick="closePhotoBoardModal()" style="background-color: #6c757d; color: white;">취소</button>
                <button onclick="savePhotoBoardModal()" style="background-color: #28a745; color: white;">저장 및 닫기</button>
            </div>
        </div>
    </div>
"""
if 'id="photo-board-modal"' not in content:
    content = content.replace('</body>', modal_html + '\n</body>')

# 7. JS logic addition
js_logic = """
        // --- 사진대지 로직 ---
        function openPhotoBoardModal() {
            document.getElementById('pb-enable-checkbox').checked = photoBoardData.enabled;
            togglePbForms(photoBoardData.enabled);
            
            document.getElementById('pb-text-1').value = photoBoardData.text1 || '';
            document.getElementById('pb-text-2').value = photoBoardData.text2 || '';
            
            setPbPreview(1, photoBoardData.photo1);
            setPbPreview(2, photoBoardData.photo2);
            
            document.getElementById('photo-board-modal').style.display = 'block';
        }

        function closePhotoBoardModal() {
            document.getElementById('photo-board-modal').style.display = 'none';
        }

        function togglePbForms(enabled) {
            document.getElementById('pb-forms').style.display = enabled ? 'block' : 'none';
        }

        function setPbPreview(index, dataUrl) {
            const preview = document.getElementById('pb-preview-' + index);
            const placeholder = document.getElementById('pb-placeholder-' + index);
            if (dataUrl) {
                preview.src = dataUrl;
                preview.style.display = 'block';
                placeholder.style.display = 'none';
            } else {
                preview.src = '';
                preview.style.display = 'none';
                placeholder.style.display = 'inline';
            }
        }
        
        function clearPbImage(index) {
            document.getElementById('pb-file-' + index).value = '';
            setPbPreview(index, null);
        }

        function handlePbImageUpload(input, index) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = new Image();
                    img.onload = function() {
                        // 캔버스를 이용한 리사이징/압축 (Max 1200px)
                        const canvas = document.createElement('canvas');
                        let width = img.width;
                        let height = img.height;
                        const max_size = 1200;
                        if (width > height) {
                            if (width > max_size) {
                                height *= max_size / width;
                                width = max_size;
                            }
                        } else {
                            if (height > max_size) {
                                width *= max_size / height;
                                height = max_size;
                            }
                        }
                        canvas.width = width;
                        canvas.height = height;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0, width, height);
                        const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
                        setPbPreview(index, dataUrl);
                    }
                    img.src = e.target.result;
                }
                reader.readAsDataURL(file);
            }
        }

        async function savePhotoBoardModal() {
            photoBoardData.enabled = document.getElementById('pb-enable-checkbox').checked;
            photoBoardData.text1 = document.getElementById('pb-text-1').value;
            photoBoardData.text2 = document.getElementById('pb-text-2').value;
            
            const src1 = document.getElementById('pb-preview-1').src;
            photoBoardData.photo1 = src1.startsWith('data:image') ? src1 : '';
            
            const src2 = document.getElementById('pb-preview-2').src;
            photoBoardData.photo2 = src2.startsWith('data:image') ? src2 : '';
            
            closePhotoBoardModal();
            showSaveToast('사진대지 설정이 적용되었습니다.');
            await saveUserData(); // 바로 DB 저장
        }

        function getPhotoBoardHTML() {
            let siteName = reportHeaderData.siteName || '';
            let reportDate = reportHeaderData.reportDate || new Date().toISOString().split('T')[0];
            
            return `
                <div class="pb-title">사 진 대 지</div>
                <div class="pb-container">
                    <div class="pb-item">
                        <div class="pb-photo-box">
                            ${photoBoardData.photo1 ? `<img src="${photoBoardData.photo1}">` : ''}
                        </div>
                        <table class="pb-table">
                            <tr>
                                <th>내 용</th>
                                <td colspan="3">${photoBoardData.text1 || ''}</td>
                            </tr>
                            <tr>
                                <th>현장명</th>
                                <td class="pb-center">${siteName}</td>
                                <th>일 자</th>
                                <td class="pb-center" style="width: 25%;">${reportDate}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="pb-item">
                        <div class="pb-photo-box">
                            ${photoBoardData.photo2 ? `<img src="${photoBoardData.photo2}">` : ''}
                        </div>
                        <table class="pb-table">
                            <tr>
                                <th>내 용</th>
                                <td colspan="3">${photoBoardData.text2 || ''}</td>
                            </tr>
                            <tr>
                                <th>현장명</th>
                                <td class="pb-center">${siteName}</td>
                                <th>일 자</th>
                                <td class="pb-center" style="width: 25%;">${reportDate}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            `;
        }
"""
if 'function openPhotoBoardModal()' not in content:
    content = content.replace('// --- 모달 관련 함수 ---', '// --- 모달 관련 함수 ---\n' + js_logic)

# 8. Report integration
report_old = """            Object.keys(itemsByGongjong).forEach((gongjong, index) => {
                const pageDiv = document.createElement('div');
                pageDiv.className = 'page';
                pageDiv.innerHTML = getReportHTML(gongjong, itemsByGongjong[gongjong]);
                dom.reportPreview.appendChild(pageDiv);
            });"""

report_new = """            Object.keys(itemsByGongjong).forEach((gongjong, index) => {
                const pageDiv = document.createElement('div');
                pageDiv.className = 'page';
                pageDiv.innerHTML = getReportHTML(gongjong, itemsByGongjong[gongjong]);
                dom.reportPreview.appendChild(pageDiv);
            });
            
            // ★ 사진대지 렌더링 추가
            if (photoBoardData && photoBoardData.enabled) {
                const pbDiv = document.createElement('div');
                pbDiv.className = 'photo-board-page';
                pbDiv.innerHTML = getPhotoBoardHTML();
                dom.reportPreview.appendChild(pbDiv);
            }"""

if 'pbDiv.className = \'photo-board-page\'' not in content:
    content = content.replace(report_old, report_new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Injection complete!")
