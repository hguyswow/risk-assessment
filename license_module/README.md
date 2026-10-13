# 🛡️ MiNOS License Engine — 통합 설명서 (v1.0.0)

AES-256-CBC 대칭키 암호화 기반의 **범용 라이선스 발급·검증 모듈**입니다.  
외부 패키지 의존성 없이 Node.js / 브라우저 환경 모두에서 즉시 작동합니다.

---

## 📁 모듈 구성 파일

| 파일명 | 환경 | 역할 |
| :--- | :--- | :--- |
| `minosLicenseEngine.js` | **Node.js** / Electron 메인 | 암호화 + 복호화 + 검증 (핵심 엔진) |
| `minosLicenseEngine.web.js` | **브라우저** / Electron 렌더러 | 복호화 + 검증 전용 (Web Crypto API) |
| `makeLicense.js` | Node.js CLI | 대화형 라이선스 발급 도구 |
| `verifyLicense.js` | Node.js CLI | 라이선스 파일 검증 도구 |

---

## ⚙️ 동작 원리

```
[라이선스 발급 흐름 - 개발자 PC]                [라이선스 검증 흐름 - 사용자 PC]
─────────────────────────────────              ─────────────────────────────────
라이선스 정보 객체 (JSON)                        .lic 파일 불러오기 (FileReader)
       ↓ JSON.stringify()                               ↓
  UTF-8 평문 문자열                         "iv(hex):cipherText(hex)" 형식 파싱
       ↓ SHA-256(비밀번호) → 32바이트 AES 키             ↓ SHA-256(비밀번호) → AES 키
       ↓ crypto.randomBytes(16) → 무작위 IV             ↓ IV 분리
  AES-256-CBC 암호화                          AES-256-CBC 복호화
       ↓                                               ↓
"iv(hex):cipherText(hex)"                      UTF-8 평문 → JSON.parse()
       ↓ fs.writeFileSync()                            ↓
  .lic 파일 저장                              라이선스 객체 획득 및 앱 활성화
```

---

## 🚀 빠른 시작

### 1. 라이선스 발급 (개발자 PC에서 실행)

#### 방법 A: 대화형 CLI 사용 (가장 쉬움)

```bash
node makeLicense.js output.lic
```

실행 후 프롬프트에 따라 정보를 입력합니다:
```
AI 프로바이더 [openrouter/gemini/deepseek/ollama] (기본: openrouter): openrouter
API Key (필수): sk-or-v1-abc123...
모델명 (기본: deepseek/deepseek-chat): deepseek/deepseek-chat
라이선스 소유자 레이블 (선택): 홍길동 건설 현장
만료일 [YYYY-MM-DD 형식, 빈 칸이면 무기한]: 2027-07-08
```

#### 방법 B: makeLicense.js 직접 편집 모드

`makeLicense.js` 상단의 설정을 수정합니다:
```js
const DIRECT_MODE = true; // true 로 변경

const ISSUE_CONFIG = {
  provider:   'openrouter',
  apiKey:     'sk-or-v1-실제API키입력',
  modelName:  'deepseek/deepseek-chat',
  label:      '홍길동 건설',
  issuedAt:   '2026-07-08',
  expiresAt:  '2027-07-08',  // 무기한이면 빈 문자열 ''
};
```
```bash
node makeLicense.js minos_license.lic
```

#### 방법 C: 코드에서 직접 호출

```js
const { packLicense } = require('./minosLicenseEngine');
const fs = require('fs');

const licText = packLicense({
  provider:  'openrouter',
  apiKey:    'sk-or-v1-abc...',
  modelName: 'deepseek/deepseek-chat',
  expiresAt: '2027-07-08'
});

fs.writeFileSync('minos_license.lic', licText, 'utf8');
```

---

### 2. 라이선스 검증 (개발자 도구)

```bash
node verifyLicense.js minos_license.lic
```

정상 출력 예시:
```
✅ 상태: 유효한 라이선스

📋 라이선스 상세 정보:
   provider  : openrouter
   apiKey    : sk-or-v1-abc...(보안 마스킹)
   modelName : deepseek/deepseek-chat
   label     : 홍길동 건설
   issuedAt  : 2026-07-08
   expiresAt : 2027-07-08
```

---

## 🔧 다른 프로그램에 적용하는 방법

### ① Node.js / Electron 메인 프로세스

```js
const { validateLicense } = require('./minosLicenseEngine');
const fs = require('fs');

const licText = fs.readFileSync('minos_license.lic', 'utf8');
const result = validateLicense(licText, ['apiKey', 'provider']);

if (result.valid) {
  const config = result.config;
  // → AI 기능 활성화, API Key 주입 등
} else {
  console.error('라이선스 오류:', result.reason);
}
```

### ② 브라우저 / HTML (Electron 렌더러)

```html
<script src="minosLicenseEngine.web.js"></script>
<script>
document.getElementById('lic-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const reader = new FileReader();
  reader.onload = async (evt) => {
    const result = await MiNOSLicenseEngine.validateLicense(
      evt.target.result, ['apiKey', 'provider']
    );
    if (result.valid) {
      console.log('라이선스 유효:', result.config);
    } else {
      alert('라이선스 오류: ' + result.reason);
    }
  };
  reader.readAsText(file);
});
</script>
```

### ③ Express.js 백엔드 서버에서 검증

```js
const express = require('express');
const { validateLicense } = require('./minosLicenseEngine');
const app = express();
app.use(express.text());

app.post('/api/verify-license', (req, res) => {
  const result = validateLicense(req.body, ['apiKey', 'provider']);
  if (result.valid) {
    res.json({ ok: true, provider: result.config.provider });
  } else {
    res.status(403).json({ ok: false, reason: result.reason });
  }
});
```

---

## 📦 라이선스 객체 스키마 (권장 필드)

```js
{
  // 필수 필드
  "provider":   "openrouter",              // AI 프로바이더 식별자
  "apiKey":     "sk-or-v1-abc...",         // API Key (핵심 데이터)
  "modelName":  "deepseek/deepseek-chat",  // 사용할 AI 모델명

  // 선택 필드
  "label":      "홍길동 현장 라이선스",       // 소유자/현장 식별 레이블
  "issuedAt":   "2026-07-08",              // 발급일 (ISO 8601)
  "expiresAt":  "2027-07-08",              // 만료일 (없으면 무기한)
  "maxUsage":   1000,                      // 최대 사용 횟수 (커스텀 확장 가능)
  "features":   ["ai-gen", "translate"]   // 허용 기능 목록 (커스텀 확장 가능)
}
```

> **💡 TIP**: `expiresAt`은 `validateLicense()`가 자동으로 검사합니다.
> `maxUsage`, `features` 등 커스텀 필드는 `result.config`에서 꺼내 앱 로직에 적용하세요.

---

## 🔐 보안 설계 철학 및 주의사항

| 항목 | 내용 |
| :--- | :--- |
| **암호화 알고리즘** | AES-256-CBC (현재 산업 표준, NIST 승인) |
| **키 파생 방식** | SHA-256(비밀번호) → 32바이트 고정 AES 키 |
| **IV 정책** | 매 발급마다 무작위 16바이트 IV 생성 (동일 내용도 매번 다른 암호문) |
| **파일 포맷** | `iv_hex:ciphertext_hex` 단일 라인 텍스트 (UTF-8) |
| **비밀번호 보관** | `DEFAULT_SECRET`은 배포 전 반드시 프로덕션 전용 값으로 변경하세요 |
| **클라이언트 암호화 금지** | 브라우저 엔진(`web.js`)은 복호화 전용. 발급(암호화)은 서버/개발자 PC에서만 수행하세요 |
| **라이선스 유출 대응** | 유출된 API Key는 OpenRouter 콘솔에서 즉시 삭제하면 라이선스 파일이 무효화됩니다 |

> ⚠️ **핵심 경고**:
> `DEFAULT_SECRET`이 소스코드에 노출된 채로 오픈소스 배포하지 마세요.
> 프로덕션 배포 시 환경변수 또는 별도 설정 파일에서 비밀번호를 로드하도록 개선을 권장합니다.

---

## 🧪 테스트 실행 방법

```bash
node -e "
const { packLicense, validateLicense } = require('./minosLicenseEngine');
const t = packLicense({ provider:'openrouter', apiKey:'sk-test', expiresAt:'2099-12-31' });
const r = validateLicense(t, ['apiKey']);
console.log(r.valid ? '✅ 테스트 통과!' : '❌ 실패: ' + r.reason);
"
```

---

*MiNOS License Engine — Built by hguyswow | 2026-07-08*
