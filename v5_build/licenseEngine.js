/**
 * 🛡️ License Encryption & Decryption Engine
 * (AES-256-CBC 대칭키 암호화 기반 범용 모듈)
 * 
 * - Node.js 내장 'crypto' 모듈을 사용하여 외부 라이브러리 의존성 없이 즉시 작동합니다.
 * - 다른 데스크톱/백엔드 프로그램에서도 완벽히 재사용 가능합니다.
 */

const crypto = require('crypto');

const DEFAULT_SECRET = 'barim-safety-key-2026!'; // 기본 복호화 암호 키
const ALGORITHM = 'aes-256-cbc';
const IV_LENGTH = 16; // AES 블록 크기 고정

/**
 * 1. 텍스트 암호화 (Encrypt)
 * @param {string} text 암호화할 원본 텍스트
 * @param {string} password 암호화에 사용할 비밀번호 (생략 시 기본 비밀번호 사용)
 * @returns {string} 16진수 암호화 문자열 (iv + cipherText 결합형)
 */
function encrypt(text, password = DEFAULT_SECRET) {
  try {
    // 32바이트 길이의 Key 생성 (SHA-256 해시 활용)
    const key = crypto.createHash('sha256').update(password).digest();
    const iv = crypto.randomBytes(IV_LENGTH);
    
    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    // 복호화 시 IV가 필요하므로, 암호문 앞에 IV(16진수 32자)를 붙여서 하나로 저장
    return iv.toString('hex') + ':' + encrypted;
  } catch (err) {
    throw new Error(`암호화 실패: ${err.message}`);
  }
}

/**
 * 2. 텍스트 복호화 (Decrypt)
 * @param {string} encryptedText 암호화된 16진수 문자열 (iv:cipherText)
 * @param {string} password 복호화에 사용할 비밀번호 (생략 시 기본 비밀번호 사용)
 * @returns {string} 복호화된 원본 텍스트
 */
function decrypt(encryptedText, password = DEFAULT_SECRET) {
  try {
    const parts = encryptedText.split(':');
    if (parts.length !== 2) {
      throw new Error("올바른 암호화 파일 포맷이 아닙니다.");
    }
    
    const iv = Buffer.from(parts[0], 'hex');
    const encrypted = parts[1];
    
    const key = crypto.createHash('sha256').update(password).digest();
    
    const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  } catch (err) {
    throw new Error(`복호화 실패 (암호 비밀번호가 일치하지 않거나 파일이 손상되었습니다): ${err.message}`);
  }
}

/**
 * 3. 객체를 암호화하여 라이선스 텍스트 파일로 저장하는 헬퍼
 * @param {object} configObj 라이선스 정보 객체 (예: { provider, apiKey, modelName })
 * @param {string} password 비밀번호
 * @returns {string} 암호화된 파일 텍스트 내용
 */
function packLicense(configObj, password = DEFAULT_SECRET) {
  const jsonStr = JSON.stringify(configObj);
  return encrypt(jsonStr, password);
}

/**
 * 4. 라이선스 텍스트를 읽어 객체로 변환해주는 헬퍼
 * @param {string} licenseText 암호화된 라이선스 파일 본문
 * @param {string} password 비밀번호
 * @returns {object} 복호화된 라이선스 정보 객체
 */
function unpackLicense(licenseText, password = DEFAULT_SECRET) {
  const decryptedJson = decrypt(licenseText, password);
  return JSON.parse(decryptedJson);
}

module.exports = {
  encrypt,
  decrypt,
  packLicense,
  unpackLicense
};
