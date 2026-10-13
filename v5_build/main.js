const { app, BrowserWindow, Menu, ipcMain, shell } = require('electron');
const path = require('path');
const os = require('os');
const fs = require('fs');

// [PATCH] 샌드박스 및 캐시 권한 오류 우회 (액세스 거부 캐시 락 방지)
app.commandLine.appendSwitch('no-sandbox');
app.commandLine.appendSwitch('disable-gpu-sandbox');
app.commandLine.appendSwitch('disable-http-cache');
app.commandLine.appendSwitch('disable-gpu-shader-disk-cache');

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
    
    // 개발 모드 디버깅을 위해 개발자 도구 강제 활성화
    // mainWindow.webContents.openDevTools();

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
        try {
            await win.webContents.executeJavaScript("window.__mainPrintZoom = document.body.style.zoom; document.body.style.zoom = '1';");
        } catch (e) {}
        // [기존 코드 보존] const pdfData = await win.webContents.printToPDF({ printBackground: true });
        const pdfData = await win.webContents.printToPDF({
            printBackground: true,
            preferCSSPageSize: true
        });
        try {
            await win.webContents.executeJavaScript("if (window.__mainPrintZoom !== undefined) { document.body.style.zoom = window.__mainPrintZoom; delete window.__mainPrintZoom; }");
            win.webContents.send('pdf-done');
        } catch (e) {}
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

// [ADD] 업데이트 파일 다운로드 핸들러
ipcMain.handle('download-update', async (event, { url }) => {
    const https = require('https');
    const http = require('http');
    const { URL } = require('url');
    
    const parsedUrl = new URL(url);
    const isHttps = parsedUrl.protocol === 'https:';
    const httpModule = isHttps ? https : http;
    
    const tempDir = os.tmpdir();
    const downloadPath = path.join(tempDir, 'RiskAssessmentPro_Setup_Latest.exe');
    
    // 이전 다운로드 파일 제거
    if (fs.existsSync(downloadPath)) {
        try { fs.unlinkSync(downloadPath); } catch(e){}
    }

    const win = BrowserWindow.fromWebContents(event.sender);
    
    return new Promise((resolve) => {
        function downloadFile(targetUrl) {
            const reqUrl = new URL(targetUrl);
            const options = {
                hostname: reqUrl.hostname,
                port: reqUrl.port || (reqUrl.protocol === 'https:' ? 443 : 80),
                path: reqUrl.pathname + reqUrl.search,
                method: 'GET',
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            };
            
            httpModule.get(options, (res) => {
                // 리다이렉트 처리 (구글 드라이브 다운로드 시 필수)
                if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                    let nextUrl = res.headers.location;
                    if (!nextUrl.startsWith('http')) {
                        nextUrl = new URL(nextUrl, targetUrl).href;
                    }
                    downloadFile(nextUrl);
                    return;
                }
                
                if (res.statusCode !== 200) {
                    resolve({ ok: false, error: `HTTP 상태 오류: ${res.statusCode}` });
                    return;
                }
                
                const totalBytes = parseInt(res.headers['content-length'], 10) || 0;
                let downloadedBytes = 0;
                
                const fileStream = fs.createWriteStream(downloadPath);
                res.pipe(fileStream);
                
                res.on('data', (chunk) => {
                    downloadedBytes += chunk.length;
                    if (totalBytes > 0) {
                        const progress = Math.round((downloadedBytes / totalBytes) * 100);
                        win.webContents.send('download-progress', { progress, downloadedBytes, totalBytes });
                    } else {
                        // Content-Length 가 없는 경우 용량만 전송
                        win.webContents.send('download-progress', { progress: -1, downloadedBytes, totalBytes: 0 });
                    }
                });
                
                fileStream.on('finish', () => {
                    fileStream.close();
                    resolve({ ok: true, path: downloadPath });
                });
                
                fileStream.on('error', (err) => {
                    fs.unlink(downloadPath, () => {});
                    resolve({ ok: false, error: `파일 저장 오류: ${err.message}` });
                });
            }).on('error', (err) => {
                resolve({ ok: false, error: `네트워크 다운로드 오류: ${err.message}` });
            });
        }
        
        downloadFile(url);
    });
});

// [ADD] 다운로드 완료된 인스톨러 실행 핸들러
ipcMain.handle('execute-installer', async (event, { filePath }) => {
    const { exec } = require('child_process');
    if (!fs.existsSync(filePath)) {
        return { ok: false, error: '인스톨러 파일을 찾을 수 없습니다.' };
    }
    
    // Windows 환경에서 인스톨러 실행 후 현재 앱 종료
    exec(`"${filePath}"`, (err) => {
        if (err) {
            console.error('인스톨러 실행 오류:', err);
        }
    });
    
    // 인스톨러 실행 명령어 직후 일렉트론 앱을 즉시 종료하여 설치 패치가 정상적으로 진행되도록 함
    setTimeout(() => {
        app.quit();
    }, 1000);
    
    return { ok: true };
});


