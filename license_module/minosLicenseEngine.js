/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║         🛡️ MiNOS License Engine (Node.js 전용 모듈)          ║
 * ║                      v1.0.0 (2026-07-08)                    ║
 * ║    AES-256-CBC 대칭키 암호화 기반 범용 라이선스 발급/검증 모듈   ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * ▶ 환경: Node.js / Electron 메인 프로세스
 * ▶ 의존성: Node.js 내장 'crypto' 모듈만 사용 (외부 패키지 0개)
 * ▶ 용도: 암호화 라이선스 파일(.lic) 생성 및 검증
 *
 * ═══════════════════════════════════════════════════════════════
 * 동작 원리 요약:
 *   1. 라이선스 정보(JSON 객체)를 UTF-8 문자열로 직렬화
 *   2. SHA-256으로 비밀번호를 32바이트 AES 키로 파생
 *   3. 무작위 16바이트 IV 생성 후 AES-256-CBC로 암호화
 *   4. "IV(hex):암호문(hex)" 형식으로 결합하여 .lic 파일에 저장
 *   5. 복호화는 역순으로 진행
 * ═══════════════════════════════════════════════════════════════
 */

'use strict';

const crypto = require('crypto');

// ─── 설정 상수 ────────────────────────────────────────────────
/** @type {string} 기본 복호화 비밀번호 (배포 전 반드시 변경하세요!) */
const DEFAULT_SECRET = 'barim-safety-key-2026!';

/** @type {string} 암호화 알고리즘 */
const ALGORITHM = 'aes-256-cbc';

/** @type {number} IV(초기화 벡터) 바이트 길이 - AES 블록 크기 고정값 */
const IV_LENGTH = 16;

// ─── 핵심 암호화 함수 ────────────────────────────────────────

/**
 * 🔐 텍스트 암호화 (Encrypt)
 *
 * 임의의 IV를 생성하여 매번 다른 암호문을 생성합니다.
 * 동일한 입력값이라도 호출할 때마다 암호문이 달라집니다(재전송 공격 방지).
 *
 * @param   {string} text       암호화할 원본 평문 텍스트
 * @param   {string} [password] 암호화 비밀번호 (생략 시 DEFAULT_SECRET 사용)
 * @returns {string}            "iv(hex):cipherText(hex)" 형식의 암호화 문자열
 * @throws  {Error}             암호화 실패 시 상세 원인 포함 예외 발생
 *
 * @example
 * const encrypted = encrypt('{"apiKey":"sk-abc123"}', 'mySecret');
 * // → "a3f2...1b:9dce...ff"
 */
function encrypt(text, password = DEFAULT_SECRET) {
  try {
    // SHA-256으로 비밀번호를 정확히 32바이트 AES 키로 파생
    const key = crypto.createHash('sha256').update(password).digest();
    // 매 암호화마다 무작위 IV 생성 (재사용 금지)
    const iv = crypto.randomBytes(IV_LENGTH);

    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    // "iv:암호문" 형식으로 결합 (복호화 시 IV 필요)
    return iv.toString('hex') + ':' + encrypted;
  } catch (err) {
    throw new Error(`[MiNOS] 암호화 실패: ${err.message}`);
  }
}

/**
 * 🔓 텍스트 복호화 (Decrypt)
 *
 * encrypt()가 생성한 "iv:cipherText" 형식 문자열을 원본으로 복원합니다.
 * 비밀번호가 틀리거나 파일이 변조된 경우 예외를 발생시킵니다.
 *
 * @param   {string} encryptedText "iv(hex):cipherText(hex)" 형식의 암호화 문자열
 * @param   {string} [password]    복호화 비밀번호 (생략 시 DEFAULT_SECRET 사용)
 * @returns {string}               복호화된 원본 평문 텍스트
 * @throws  {Error}                비밀번호 불일치 또는 파일 손상 시 예외 발생
 *
 * @example
 * const plain = decrypt('a3f2...1b:9dce...ff', 'mySecret');
 * // → '{"apiKey":"sk-abc123"}'
 */
function decrypt(encryptedText, password = DEFAULT_SECRET) {
  try {
    const parts = encryptedText.trim().split(':');
    if (parts.length !== 2) {
      throw new Error('파일 포맷이 올바르지 않습니다. (iv:cipherText 구조 아님)');
    }

    const iv = Buffer.from(parts[0], 'hex');
    const cipherText = parts[1];

    const key = crypto.createHash('sha256').update(password).digest();
    const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);

    let decrypted = decipher.update(cipherText, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  } catch (err) {
    throw new Error(`[MiNOS] 복호화 실패 (비밀번호 불일치 또는 파일 손상): ${err.message}`);
  }
}

// ─── 라이선스 헬퍼 함수 ──────────────────────────────────────

/**
 * 📦 JSON 객체를 암호화하여 라이선스 문자열로 직렬화 (packLicense)
 *
 * 라이선스 발급 시 사용합니다.
 * configObj는 어떤 구조의 JSON도 가능합니다.
 *
 * @param   {object} configObj  라이선스에 담을 정보 객체
 * @param   {string} [password] 암호화 비밀번호
 * @returns {string}            암호화된 라이선스 문자열 (.lic 파일에 저장할 내용)
 *
 * @example
 * const licText = packLicense({
 *   provider: 'openrouter',
 *   apiKey: 'sk-or-v1-abc...',
 *   modelName: 'deepseek/deepseek-chat',
 *   issuedAt: '2026-07-08',
 *   expiresAt: '2027-07-08'   // 선택적 유효기간
 * });
 */
function packLicense(configObj, password = DEFAULT_SECRET) {
  const jsonStr = JSON.stringify(configObj);
  return encrypt(jsonStr, password);
}

/**
 * 📂 라이선스 문자열을 복호화하여 JSON 객체로 역직렬화 (unpackLicense)
 *
 * 사용자가 제출한 .lic 파일을 검증/파싱 시 사용합니다.
 *
 * @param   {string} licenseText 암호화된 라이선스 파일 본문
 * @param   {string} [password]  복호화 비밀번호
 * @returns {object}             복호화된 라이선스 정보 객체
 *
 * @example
 * const config = unpackLicense(fs.readFileSync('minos.lic', 'utf8'));
 * console.log(config.apiKey); // → "sk-or-v1-abc..."
 */
function unpackLicense(licenseText, password = DEFAULT_SECRET) {
  const decryptedJson = decrypt(licenseText, password);
  return JSON.parse(decryptedJson);
}

/**
 * ✅ 라이선스 유효성 검사 헬퍼 (validateLicense)
 *
 * 복호화 성공 여부와 필수 필드 존재 여부, 만료일 검사를 한 번에 수행합니다.
 *
 * @param   {string}   licenseText 암호화된 라이선스 파일 본문
 * @param   {string[]} [requiredFields] 필수 필드 목록 (기본: ['apiKey'])
 * @param   {string}   [password]  복호화 비밀번호
 * @returns {{ valid: boolean, config: object|null, reason: string }}
 *
 * @example
 * const result = validateLicense(licText, ['apiKey', 'modelName']);
 * if (!result.valid) {
 *   console.error('라이선스 오류:', result.reason);
 * } else {
 *   console.log('유효한 라이선스:', result.config);
 * }
 */
function validateLicense(licenseText, requiredFields = ['apiKey'], password = DEFAULT_SECRET) {
  try {
    const config = unpackLicense(licenseText, password);

    // 필수 필드 존재 검사
    for (const field of requiredFields) {
      if (!config[field]) {
        return { valid: false, config: null, reason: `필수 필드 누락: '${field}'` };
      }
    }

    // 만료일 검사 (expiresAt 필드가 있을 경우에만)
    if (config.expiresAt) {
      const expiry = new Date(config.expiresAt);
      if (isNaN(expiry.getTime())) {
        return { valid: false, config: null, reason: '만료일(expiresAt) 형식이 올바르지 않습니다.' };
      }
      if (new Date() > expiry) {
        return { valid: false, config: null, reason: `라이선스가 만료되었습니다. (만료일: ${config.expiresAt})` };
      }
    }

    return { valid: true, config, reason: '유효한 라이선스' };
  } catch (err) {
    return { valid: false, config: null, reason: err.message };
  }
}

// ─── 모듈 내보내기 ────────────────────────────────────────────
module.exports = {
  DEFAULT_SECRET,
  encrypt,
  decrypt,
  packLicense,
  unpackLicense,
  validateLicense
};
