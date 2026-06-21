import sys, os

# 1. Update main.js
main_path = r'E:\dev\dang\v5_build\main.js'
with open(main_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

main_content = main_content.replace(
    "const { app, BrowserWindow, Menu } = require('electron');",
    "const { app, BrowserWindow, Menu, ipcMain, shell } = require('electron');"
)
main_content = main_content.replace(
    "const path = require('path');",
    "const path = require('path');\nconst os = require('os');\nconst fs = require('fs');"
)

ipc_logic = """
// PDF 미리보기 IPC 이벤트 리스너
ipcMain.on('print-to-pdf', async (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    try {
        const pdfData = await win.webContents.printToPDF({
            printBackground: true
        });
        const tempPath = path.join(os.tmpdir(), `report_preview_${Date.now()}.pdf`);
        fs.writeFileSync(tempPath, pdfData);
        shell.openPath(tempPath);
    } catch (error) {
        console.error('Failed to generate PDF', error);
    }
});
"""

if 'ipcMain.on(\'print-to-pdf\'' not in main_content:
    main_content += '\n' + ipc_logic

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_content)

# 2. Update index.html
html_path = r'E:\dev\dang\v5_build\index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Update button text
btn_old = '<button id="print-pdf-btn">🖨️ 브라우저 인쇄 (PDF 저장 가능)</button>'
btn_new = '<button id="print-pdf-btn" style="background-color: #007bff; color: white;">🖨️ PDF 미리보기 및 인쇄</button>'
html_content = html_content.replace(btn_old, btn_new)

# Update onclick logic
js_old = "document.getElementById('print-pdf-btn').onclick = () => window.print();"
js_new = "document.getElementById('print-pdf-btn').onclick = () => require('electron').ipcRenderer.send('print-to-pdf');"
html_content = html_content.replace(js_old, js_new)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("PDF logic injection complete!")
