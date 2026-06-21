import sys

path = r'E:\dev\dang\v5_build\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. State data addition
state_init = """
let photoBoardData = {
    enabled: false,
    photo1: '',
    text1: '',
    photo2: '',
    text2: ''
};
"""
if 'let photoBoardData = {' not in content:
    target = 'let reportHeaderData = { siteName: "OO현장 신축공사", date: new Date().toISOString().slice(0, 10) };'
    content = content.replace(target, target + state_init)

# 2. JS logic addition
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
            await saveUserData();
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
    target2 = '// [New] 결재 설정 모달 관련 함수 (다중 서명 지원)'
    content = content.replace(target2, target2 + '\n' + js_logic)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fix script completed")
