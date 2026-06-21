import sys, re

path = r'E:\dev\dang\v5_build\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update CSS
css_old = """        .photo-board-page {
            page: portrait_page;
            page-break-before: always;
            width: 100%;
            font-family: 'Malgun Gothic', sans-serif;
            box-sizing: border-box;
            background: white;
            color: black;
        }"""
css_new = """        .photo-board-page {
            page: portrait_page;
            page-break-before: always;
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            font-family: 'Malgun Gothic', sans-serif;
            box-sizing: border-box;
            background: white;
            color: black;
        }
        @media print {
            .photo-board-page {
                max-width: none;
                margin: 0;
                box-shadow: none;
            }
        }"""
content = content.replace(css_old, css_new)

# Update pb-photo-box height
box_old = """        .pb-photo-box {
            width: 100%;
            height: 350px;"""
box_new = """        .pb-photo-box {
            width: 100%;
            height: 440px;"""
content = content.replace(box_old, box_new)

# Update img object-fit
img_old = """        .pb-photo-box img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }"""
img_new = """        .pb-photo-box img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }"""
content = content.replace(img_old, img_new)


# 2. Add paste event listener
paste_logic = """
        // --- 사진대지 클립보드 붙여넣기 로직 ---
        document.addEventListener('paste', function(e) {
            const modal = document.getElementById('photo-board-modal');
            if (!modal || modal.style.display === 'none') return; // 모달이 열려있을 때만 동작

            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
            let imageFile = null;
            for (let index in items) {
                const item = items[index];
                if (item.kind === 'file' && item.type.indexOf('image/') !== -1) {
                    imageFile = item.getAsFile();
                    break;
                }
            }

            if (imageFile) {
                // 비어있는 곳 찾기
                let targetIndex = 1;
                const src1 = document.getElementById('pb-preview-1').src;
                const src2 = document.getElementById('pb-preview-2').src;
                
                if (src1 && src1.startsWith('data:image')) {
                    if (!src2 || !src2.startsWith('data:image')) {
                        targetIndex = 2; // 1번이 차있고 2번이 비어있으면 2번
                    } else {
                        targetIndex = 2; // 둘 다 차있으면 2번을 덮어씀
                    }
                }

                // 이미지 리사이징 로직 직접 호출
                const reader = new FileReader();
                reader.onload = function(evt) {
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
                        setPbPreview(targetIndex, dataUrl);
                        showSaveToast('사진 ' + targetIndex + '에 붙여넣기 완료!');
                    }
                    img.src = evt.target.result;
                }
                reader.readAsDataURL(imageFile);
            }
        });
"""
if '사진대지 클립보드 붙여넣기 로직' not in content:
    target = 'async function savePhotoBoardModal()'
    content = content.replace(target, paste_logic + '\n        ' + target)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Update completed!")
