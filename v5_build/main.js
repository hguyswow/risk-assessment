const { app, BrowserWindow, Menu, ipcMain, shell } = require('electron');
const path = require('path');
const os = require('os');
const fs = require('fs');

// [PATCH] 샌드박스 권한 오류 우회 (액세스 거부 캐시 락 방지)
app.commandLine.appendSwitch('no-sandbox');
app.commandLine.appendSwitch('disable-gpu-sandbox');

function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        webPreferences: {
            nodeIntegration: true, // For file system access specific logic if needed, but safer to use false + preload
            contextIsolation: false, // Keeping false for now to support existing code's direct usage of APIs if any, though standard HTML5 File/Localstorage is fine.
            // NOTE: For v5.0 security focus, we should eventually move to contextIsolation: true and a preload script.
            // However, the current code relies on simple browser APIs.
            // File System Access API (window.showDirectoryPicker) works in Electron if customized or we rely on HTML5 input.
        },
        icon: path.join(__dirname, 'icon.ico') // Icon if available
    });

    mainWindow.loadFile('index.html');
    mainWindow.maximize();

    // Menu.setApplicationMenu(null); // Uncomment to hide menu bar
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') app.quit();
});


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
        win.webContents.send('pdf-error', error.message || 'Unknown error');
    }
});

// [CORS & WAF 우회] 렌더러 프로세스를 대신해 Node.js 환경에서 HTTP 요청을 중계하는 핸들러
ipcMain.handle('http-request', async (event, { url, method = 'POST', headers = {}, body = null }) => {
    const { URL } = require('url');
    return new Promise((resolve) => {
        try {
            const parsedUrl = new URL(url);
            const isHttps = parsedUrl.protocol === 'https:';
            const httpModule = isHttps ? require('https') : require('http');
            
            const cleanHeaders = { ...headers };
            // 브라우저 렌더러가 강제로 삽입하는 Origin 헤더를 WAF 차단 방지를 위해 완벽히 제거
            Object.keys(cleanHeaders).forEach(key => {
                if (key.toLowerCase() === 'origin') {
                    delete cleanHeaders[key];
                }
            });
            
            // [IPv6 vs IPv4 호환 패치]
            // Node.js 18+에서 'localhost'를 DNS 조회하면 IPv6(::1)가 우선 반환되는데,
            // LM Studio / Ollama 등 로컬 서버는 IPv4(127.0.0.1)만 리스닝하므로 ECONNREFUSED 발생.
            // 'localhost' → '127.0.0.1' 강제 치환으로 IPv4로만 연결 보장.
            const rawHostname = parsedUrl.hostname;
            const hostname = (rawHostname === 'localhost') ? '127.0.0.1' : rawHostname;
            
            const options = {
                hostname: hostname,
                port: parsedUrl.port || (isHttps ? 443 : 80),
                path: parsedUrl.pathname + parsedUrl.search,
                method: method.toUpperCase(),
                headers: cleanHeaders,
                family: 4  // IPv4 강제 사용 (::1 IPv6 연결 시도 방지)
            };
            
            const req = httpModule.request(options, (res) => {
                let resBody = '';
                res.on('data', (chunk) => { resBody += chunk; });
                res.on('end', () => {
                    resolve({
                        ok: res.statusCode >= 200 && res.statusCode < 300,
                        status: res.statusCode,
                        body: resBody
                    });
                });
            });
            
            req.on('error', (err) => {
                resolve({
                    ok: false,
                    status: 0,
                    body: JSON.stringify({ error: err.message })
                });
            });
            
            if (body) {
                req.write(body);
            }
            req.end();
        } catch (e) {
            resolve({
                ok: false,
                status: 0,
                body: JSON.stringify({ error: e.message })
            });
        }
    });
});

