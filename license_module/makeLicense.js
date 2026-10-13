#!/usr/bin/env node
/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          🔑 MiNOS License CLI — 라이선스 발급 도구            ║
 * ║                      v1.0.0 (2026-07-08)                    ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * 사용법:
 *   node makeLicense.js [출력파일명.lic]
 *
 * 대화형 프롬프트를 통해 라이선스 정보를 입력받아
 * 암호화된 .lic 파일을 생성합니다.
 *
 * ─── 직접 코드 수정으로 발급하는 방법 ─────────────────────────
 * 아래 ISSUE_CONFIG 객체를 직접 편집하고 실행해도 됩니다.
 * ───────────────────────────────────────────────────────────────
 */

'use strict';

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { packLicense, validateLicense, DEFAULT_SECRET } = require('./minosLicenseEngine');

// ─── 1) 직접 편집 발급 방법: 아래 객체 수정 후 실행 ───────────
// (대화형 입력을 원하면 DIRECT_MODE = false 로 변경)
const DIRECT_MODE = false;

const ISSUE_CONFIG = {
  provider:   'openrouter',         // 'openrouter' | 'gemini' | 'deepseek' | 'ollama'
  apiKey:     'sk-or-v1-여기에입력', // 발급할 API Key
  modelName:  'deepseek/deepseek-chat', // 사용할 모델명
  label:      '바림종합건설 라이선스',    // 라이선스 소유자 식별 레이블 (선택)
  issuedAt:   new Date().toISOString().split('T')[0], // 발급일 (자동)
  expiresAt:  '',                   // 만료일 (예: '2027-07-08', 빈 값이면 무기한)
};

const OUTPUT_FILE = process.argv[2] || 'minos_license.lic';

// ─── 2) 발급 실행 ─────────────────────────────────────────────

async function issueLicense(config, outputPath) {
  console.log('\n─────────────────────────────────────────');
  console.log('🔐  MiNOS 라이선스 발급 시작...');
  console.log('─────────────────────────────────────────');
  console.log('📋 발급 내용:');
  Object.entries(config).forEach(([k, v]) => {
    const display = k === 'apiKey' ? v.slice(0, 12) + '...(보안 마스킹)' : v || '(없음)';
    console.log(`   ${k}: ${display}`);
  });

  // 만료일이 있으면 미래인지 검증
  if (config.expiresAt) {
    const exp = new Date(config.expiresAt);
    if (isNaN(exp.getTime())) {
      console.error('\n❌ 만료일 형식이 올바르지 않습니다. (예: 2027-07-08)');
      process.exit(1);
    }
    if (exp <= new Date()) {
      console.error('\n❌ 만료일이 과거입니다. 미래 날짜를 입력하세요.');
      process.exit(1);
    }
  }

  try {
    const licenseText = packLicense(config, DEFAULT_SECRET);
    fs.writeFileSync(outputPath, licenseText, 'utf8');

    console.log('\n✅ 라이선스 파일 생성 완료!');
    console.log(`📁 저장 경로: ${path.resolve(outputPath)}`);
    console.log(`📏 파일 크기: ${Buffer.byteLength(licenseText, 'utf8')} bytes`);

    // 생성 직후 자가 검증
    console.log('\n🔍 발급 자가 검증 중...');
    const fileContent = fs.readFileSync(outputPath, 'utf8');
    const result = validateLicense(fileContent, ['apiKey', 'provider']);
    if (result.valid) {
      console.log('✅ 자가 검증 통과! 라이선스가 정상입니다.');
      console.log(`   - provider: ${result.config.provider}`);
      console.log(`   - modelName: ${result.config.modelName}`);
      console.log(`   - expiresAt: ${result.config.expiresAt || '무기한'}`);
    } else {
      console.error('❌ 자가 검증 실패:', result.reason);
    }
  } catch (err) {
    console.error('\n❌ 라이선스 발급 실패:', err.message);
    process.exit(1);
  }

  console.log('\n─────────────────────────────────────────\n');
}

async function interactiveIssue() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const ask = (q) => new Promise(resolve => rl.question(q, resolve));

  console.log('\n╔══════════════════════════════════════╗');
  console.log('║  🔑 MiNOS 대화형 라이선스 발급 도구  ║');
  console.log('╚══════════════════════════════════════╝\n');

  const provider = (await ask('AI 프로바이더 [openrouter/gemini/deepseek/ollama] (기본: openrouter): ')).trim() || 'openrouter';
  const apiKey   = (await ask('API Key (필수): ')).trim();
  const modelName = (await ask('모델명 (기본: deepseek/deepseek-chat): ')).trim() || 'deepseek/deepseek-chat';
  const label     = (await ask('라이선스 소유자 레이블 (선택): ')).trim();
  const expiresAt = (await ask('만료일 [YYYY-MM-DD 형식, 빈 칸이면 무기한]: ')).trim();

  rl.close();

  if (!apiKey) {
    console.error('\n❌ API Key는 필수 입력 항목입니다.');
    process.exit(1);
  }

  const config = {
    provider,
    apiKey,
    modelName,
    label: label || undefined,
    issuedAt: new Date().toISOString().split('T')[0],
    expiresAt: expiresAt || undefined
  };

  await issueLicense(config, OUTPUT_FILE);
}

// ─── 3) 진입점 ────────────────────────────────────────────────
if (DIRECT_MODE) {
  issueLicense(ISSUE_CONFIG, OUTPUT_FILE);
} else {
  interactiveIssue();
}
