#!/usr/bin/env node
/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║       🔍 MiNOS License Verifier — 라이선스 검증 도구          ║
 * ║                      v1.0.0 (2026-07-08)                    ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * 사용법:
 *   node verifyLicense.js [라이선스파일.lic]
 *
 * 지정한 .lic 파일의 복호화 가능 여부, 필수 필드 존재, 만료 여부를
 * 한 번에 검증하고 내용을 안전하게 출력합니다.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { validateLicense } = require('./minosLicenseEngine');

const licFile = process.argv[2];

if (!licFile) {
  console.error('사용법: node verifyLicense.js [라이선스파일.lic]');
  process.exit(1);
}

const filePath = path.resolve(licFile);

if (!fs.existsSync(filePath)) {
  console.error(`❌ 파일을 찾을 수 없습니다: ${filePath}`);
  process.exit(1);
}

const licenseText = fs.readFileSync(filePath, 'utf8');

console.log('\n─────────────────────────────────────────');
console.log(`🔍 라이선스 파일 검증 중: ${path.basename(filePath)}`);
console.log('─────────────────────────────────────────');

const result = validateLicense(licenseText, ['apiKey', 'provider']);

if (result.valid) {
  const c = result.config;
  console.log('✅ 상태: 유효한 라이선스\n');
  console.log('📋 라이선스 상세 정보:');
  console.log(`   provider  : ${c.provider}`);
  console.log(`   apiKey    : ${c.apiKey.slice(0, 12)}...(보안 마스킹)`);
  console.log(`   modelName : ${c.modelName || '(없음)'}`);
  console.log(`   label     : ${c.label || '(없음)'}`);
  console.log(`   issuedAt  : ${c.issuedAt || '(없음)'}`);
  console.log(`   expiresAt : ${c.expiresAt || '무기한'}`);
} else {
  console.log('❌ 상태: 유효하지 않은 라이선스');
  console.log(`   사유: ${result.reason}`);
}

console.log('\n─────────────────────────────────────────\n');
