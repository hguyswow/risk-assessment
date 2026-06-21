import sys

main_path = r'E:\dev\dang\v5_build\main.js'
with open(main_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

main_content = main_content.replace(
    "console.error('Failed to generate PDF', error);",
    "console.error('Failed to generate PDF', error);\n        win.webContents.send('pdf-error', error.message || 'Unknown error');"
)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_content)

html_path = r'E:\dev\dang\v5_build\index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

ipc_error_handler = """
    try {
        require('electron').ipcRenderer.on('pdf-error', (e, msg) => {
            alert('PDF 뷰어 실행 실패: ' + msg);
        });
    } catch(e) {}
"""
if 'pdf-error' not in html_content:
    html_content = html_content.replace(
        "alert('PDF 미리보기 호출 오류: ' + err.message);",
        "alert('PDF 미리보기 호출 오류: ' + err.message);\n    }\n" + ipc_error_handler + "    try {"
    )
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

print("Error tracking injected")
