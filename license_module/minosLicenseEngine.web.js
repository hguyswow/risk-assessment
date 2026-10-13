/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║      🌐 MiNOS License Engine (브라우저/Web 전용 모듈)          ║
 * ║                      v1.0.0 (2026-07-08)                    ║
 * ║    Web Crypto API (AES-256-CBC) 기반 범용 라이선스 검증 모듈    ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * ▶ 환경: 브라우저, Electron 렌더러 프로세스, WebView
 * ▶ 의존성: 브라우저 내장 window.crypto.subtle 만 사용 (외부 패키지 0개)
 * ▶ 용도: 사용자 클라이언트(브라우저)에서 .lic 파일 복호화 및 검증
 *
 * ⚠️  주의: 암호화(packLicense)는 Node.js 전용 모듈(minosLicenseEngine.js)에서만
 *          수행하세요. 브라우저 측은 복호화(unpackLicense)만 사용합니다.
 *
 * ═══════════════════════════════════════════════════════════════
 * Node.js 엔진과의 호환성:
 *   - 동일한 DEFAULT_SECRET, AES-256-CBC, IV:CipherText 포맷을 공유합니다.
 *   - Node.js에서 발급한 .lic 파일을 이 모듈로 그대로 복호화할 수 있습니다.
 * ═══════════════════════════════════════════════════════════════
 */

'use strict';

(function (global) {

  // ─── 설정 상수 ──────────────────────────────────────────────
  /** @type {string} 기본 복호화 비밀번호 (Node.js 엔진과 반드시 동일해야 합니다) */
  const DEFAULT_SECRET = 'barim-safety-key-2026!';

  // ─── 내부 헬퍼 ──────────────────────────────────────────────

  /**
   * 비밀번호 문자열로부터 AES-256 CryptoKey 객체 파생
   * @param {string} password 비밀번호
   * @returns {Promise<CryptoKey>}
   */
  async function _deriveKey(password) {
    const encoder = new TextEncoder();
    const pwBytes = encoder.encode(password);
    // SHA-256으로 32바이트 키 파생 (Node.js createHash('sha256')와 동일 결과)
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', pwBytes);
    return await window.crypto.subtle.importKey(
      'raw',
      hashBuffer,
      { name: 'AES-CBC', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * 16진수 문자열을 Uint8Array로 변환
   * @param {string} hex
   * @returns {Uint8Array}
   */
  function _hexToBytes(hex) {
    const result = new Uint8Array(hex.length / 2);
    for (let i = 0; i < hex.length; i += 2) {
      result[i / 2] = parseInt(hex.substring(i, i + 2), 16);
    }
    return result;
  }

  /**
   * Uint8Array를 16진수 문자열로 변환
   * @param {Uint8Array} bytes
   * @returns {string}
   */
  function _bytesToHex(bytes) {
    return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // ─── 핵심 암복호화 함수 ────────────────────────────────────

  /**
   * 🔐 텍스트 암호화 (브라우저 환경, Async)
   *
   * @param   {string} text       암호화할 평문
   * @param   {string} [password] 비밀번호
   * @returns {Promise<string>}   "iv(hex):cipherText(hex)" 형식 암호문
   *
   * @example
   * const enc = await encrypt('{"apiKey":"sk-abc"}', 'mySecret');
   */
  async function encrypt(text, password = DEFAULT_SECRET) {
    try {
      const key = await _deriveKey(password);
      const ivBytes = window.crypto.getRandomValues(new Uint8Array(16));
      const encoded = new TextEncoder().encode(text);

      const encryptedBuffer = await window.crypto.subtle.encrypt(
        { name: 'AES-CBC', iv: ivBytes },
        key,
        encoded
      );

      return _bytesToHex(ivBytes) + ':' + _bytesToHex(new Uint8Array(encryptedBuffer));
    } catch (err) {
      throw new Error(`[MiNOS Web] 암호화 실패: ${err.message}`);
    }
  }

  /**
   * 🔓 텍스트 복호화 (브라우저 환경, Async)
   *
   * @param   {string} encryptedText "iv(hex):cipherText(hex)" 형식의 암호문
   * @param   {string} [password]    비밀번호
   * @returns {Promise<string>}      복호화된 원본 평문
   *
   * @example
   * const plain = await decrypt(encryptedText, 'mySecret');
   */
  async function decrypt(encryptedText, password = DEFAULT_SECRET) {
    try {
      const parts = encryptedText.trim().split(':');
      if (parts.length !== 2) {
        throw new Error('파일 포맷이 올바르지 않습니다. (iv:cipherText 구조 아님)');
      }

      const ivBytes = _hexToBytes(parts[0]);
      const cipherBytes = _hexToBytes(parts[1]);

      const key = await _deriveKey(password);

      const decryptedBuffer = await window.crypto.subtle.decrypt(
        { name: 'AES-CBC', iv: ivBytes },
        key,
        cipherBytes
      );

      return new TextDecoder().decode(decryptedBuffer);
    } catch (err) {
      throw new Error(`[MiNOS Web] 복호화 실패 (비밀번호 불일치 또는 파일 손상): ${err.message}`);
    }
  }

  /**
   * 📦 JSON 객체를 암호화하여 라이선스 문자열로 직렬화 (packLicense)
   *
   * @param   {object} configObj  라이선스 정보 객체
   * @param   {string} [password] 비밀번호
   * @returns {Promise<string>}   암호화된 라이선스 문자열
   */
  async function packLicense(configObj, password = DEFAULT_SECRET) {
    return await encrypt(JSON.stringify(configObj), password);
  }

  /**
   * 📂 라이선스 문자열을 복호화하여 JSON 객체로 역직렬화 (unpackLicense)
   *
   * @param   {string} licenseText 암호화된 라이선스 파일 본문
   * @param   {string} [password]  비밀번호
   * @returns {Promise<object>}    복호화된 라이선스 정보 객체
   *
   * @example
   * const config = await unpackLicense(fileContent);
   * console.log(config.apiKey);
   */
  async function unpackLicense(licenseText, password = DEFAULT_SECRET) {
    const decryptedJson = await decrypt(licenseText, password);
    return JSON.parse(decryptedJson);
  }

  /**
   * ✅ 라이선스 유효성 검사 헬퍼 (validateLicense)
   *
   * @param   {string}   licenseText    암호화된 라이선스 파일 본문
   * @param   {string[]} [requiredFields] 필수 필드 목록 (기본: ['apiKey'])
   * @param   {string}   [password]     비밀번호
   * @returns {Promise<{ valid: boolean, config: object|null, reason: string }>}
   *
   * @example
   * const result = await validateLicense(fileText, ['apiKey', 'modelName']);
   * if (result.valid) startApp(result.config);
   */
  async function validateLicense(licenseText, requiredFields = ['apiKey'], password = DEFAULT_SECRET) {
    try {
      const config = await unpackLicense(licenseText, password);

      for (const field of requiredFields) {
        if (!config[field]) {
          return { valid: false, config: null, reason: `필수 필드 누락: '${field}'` };
        }
      }

      if (config.expiresAt) {
        const expiry = new Date(config.expiresAt);
        if (isNaN(expiry.getTime())) {
          return { valid: false, config: null, reason: '만료일(expiresAt) 형식이 올바르지 않습니다.' };
        }
        if (new Date() > expiry) {
          return { valid: false, config: null, reason: `라이선스 만료됨 (만료일: ${config.expiresAt})` };
        }
      }

      return { valid: true, config, reason: '유효한 라이선스' };
    } catch (err) {
      return { valid: false, config: null, reason: err.message };
    }
  }

  // ─── 전역 노출 (브라우저 window 객체에 바인딩) ─────────────
  global.MiNOSLicenseEngine = {
    DEFAULT_SECRET,
    encrypt,
    decrypt,
    packLicense,
    unpackLicense,
    validateLicense
  };

  // CommonJS 환경 지원 (Electron 렌더러 등)
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = global.MiNOSLicenseEngine;
  }

})(typeof window !== 'undefined' ? window : global);
