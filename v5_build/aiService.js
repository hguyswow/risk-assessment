// AI 서비스 모듈 (비-모듈 전역 바인딩 규격)

(function (global) {
  // Electron 메인 프로세스 위임 HTTP 요청 헬퍼 (CORS 및 WAF 우회)
  async function ipcFetch(url, options = {}) {
    const method = options.method || 'GET';
    const headers = options.headers || {};
    const body = options.body || null;
    const signal = options.signal || null;

    // Electron nodeIntegration=true 환경에서는 window.require 또는 전역 require 모두 지원
    const _req = (typeof window !== 'undefined' && typeof window.require === 'function')
      ? window.require
      : (typeof require !== 'undefined' ? require : null);

    if (_req) {
      try {
        const { ipcRenderer } = _req('electron');
        if (!ipcRenderer) throw new Error('ipcRenderer를 찾을 수 없습니다.');

        if (signal && signal.aborted) {
          throw new DOMException('The user aborted a request.', 'AbortError');
        }
        
        const result = await ipcRenderer.invoke('http-request', {
          url,
          method,
          headers,
          body
        });
        
        console.log('[ipcFetch] IPC 중계 성공:', url, 'status:', result.status);
        return {
          ok: result.ok,
          status: result.status,
          text: async () => result.body,
          json: async () => JSON.parse(result.body)
        };
      } catch (e) {
        if (e.name === 'AbortError') throw e;
        console.warn('[ipcFetch] IPC HTTP 요청 실패, 일반 fetch로 폴백합니다:', e.message);
      }
    } else {
      console.warn('[ipcFetch] Electron require를 찾을 수 없어 일반 fetch를 사용합니다.');
    }
    return fetch(url, options);
  }

  // AI 연동 설정 인터페이스 규격
  const defaultAIConfig = {
    provider: 'gemini',
    apiKey: '', // 보안을 위해 비워진 상태로 유지
    modelName: 'gemini-2.5-flash',
    endpointUrl: '',
    enabled: false,
    riskCount: 5,
    temp: 0.7,
    detailLevelRisk: 'high',
    enableQA: true
  };


  /**
   * 응답 텍스트에서 안전하게 JSON 객체/배열 부분만 도려내어 파싱하는 무결성 헬퍼
   */
  function extractJson(text) {
    let clean = text.replace(/```json/gi, '').replace(/```/g, '').trim();

    // [방어 조치 1] 제어 문자 정제 (AI가 간혹 삽입하는 BOM, 널 바이트 등 제거)
    clean = clean.replace(/[\x00-\x09\x0B\x0C\x0E-\x1F]/g, '');

    const firstBrace = clean.indexOf('{');
    const firstBracket = clean.indexOf('[');
    let startIdx = -1;
    let endChar = '';
    
    if (firstBrace !== -1 && (firstBracket === -1 || firstBrace < firstBracket)) {
      startIdx = firstBrace;
      endChar = '}';
    } else if (firstBracket !== -1 && (firstBrace === -1 || firstBracket < firstBrace)) {
      startIdx = firstBracket;
      endChar = ']';
    }
    
    if (startIdx !== -1) {
      const endIdx = clean.lastIndexOf(endChar);
      if (endIdx !== -1 && endIdx > startIdx) {
        clean = clean.substring(startIdx, endIdx + 1);
      }
    }

    // [방어 조치 2] try-catch 단계적 복구 파싱
    try {
      return JSON.parse(clean);
    } catch (e1) {
      console.warn('[extractJson] 1차 파싱 실패, 후행 쉼표 제거 후 재시도:', e1.message);
      try {
        // AI가 자주 범하는 trailing comma 제거 (예: [1,2,3,] → [1,2,3])
        const fixedTrailing = clean.replace(/,\s*([\]}])/g, '$1');
        return JSON.parse(fixedTrailing);
      } catch (e2) {
        console.error('[extractJson] 최종 파싱 실패. 원본 텍스트 일부:', clean.substring(0, 300));
        throw new Error('AI 응답 JSON 파싱 실패: ' + e2.message);
      }
    }
  }

  /**
   * AI API 통합 호출기
   */
  async function callAIAPI(prompt, config, temp = 0.4, signal = null) {
    if (config.provider === 'gemini') {
      return callGemini(prompt, config, temp, signal);
    } else if (config.provider === 'deepseek') {
      return callDeepSeek(prompt, config, temp, signal);
    } else if (config.provider === 'openrouter') {
      return callOpenRouter(prompt, config, temp, signal);
    } else if (config.provider === 'ollama') {
      return callOllama(prompt, config, temp, signal);
    } else if (config.provider === 'lmstudio') {
      return callLMStudio(prompt, config, temp, signal);
    }
    throw new Error("지원하지 않는 AI 프로바이더입니다.");
  }

  /**
   * Google Gemini API에서 실제로 사용 가능한 모델 목록을 동적으로 조회
   */
  async function fetchAvailableGeminiModels(apiKey) {
    try {
      const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`;
      const response = await ipcFetch(url, { signal: AbortSignal.timeout(8000) });
      if (!response.ok) return [];
      const data = await response.json();
      const models = (data.models || [])
        .filter(m => Array.isArray(m.supportedGenerationMethods) && m.supportedGenerationMethods.includes('generateContent'))
        .map(m => m.name.replace('models/', ''));
      console.log('[Gemini] 사용 가능한 모델 목록:', models);
      return models;
    } catch (e) {
      console.warn('[Gemini] 모델 목록 동적 조회 실패 (폴백 진행):', e.message);
      return [];
    }
  }

  /**
   * Google Gemini API 연동 (Failover 및 자동 모델 스위칭)
   */
  async function callGemini(prompt, config, temp, signal) {
    const requestedModel = config.modelName || 'gemini-2.5-flash';
    
    let activeKeys = [];
    if (Array.isArray(config.apiKeys) && config.apiKeys.length > 0) {
      activeKeys = config.apiKeys;
    } else {
      const singleKey = (config.apiKey || '').trim();
      if (singleKey) activeKeys = [singleKey];
    }
    
    if (activeKeys.length === 0) {
      throw new Error("Gemini API Key가 비어 있습니다. AI 설정 탭에서 API Key를 입력하세요.");
    }
    
    let lastError = null;
    let successModel = null;
    
    for (let keyIdx = 0; keyIdx < activeKeys.length; keyIdx++) {
      const currentKey = activeKeys[keyIdx];
      const isMultiKey = activeKeys.length > 1;
      
      if (isMultiKey) {
        console.info(`[Gemini] 등록된 ${activeKeys.length}개의 키 중 ${keyIdx + 1}번째 키로 API 호출을 시도합니다.`);
      }

      try {
        const availableModels = await fetchAvailableGeminiModels(currentKey);
        let candidateModels;
        
        if (availableModels.length > 0) {
          const preferenceOrder = [
            'gemini-2.5-flash',
            'gemini-2.5-flash-preview-05-20',
            'gemini-2.0-flash',
            'gemini-2.0-flash-exp',
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-flash-8b',
          ];

          const userModelAvailable = availableModels.includes(requestedModel);
          const preferredAvailable = preferenceOrder.filter(m => availableModels.includes(m));
          const otherAvailable = availableModels
            .filter(m => !preferenceOrder.includes(m) && m !== requestedModel)
            .slice(0, 3);

          if (userModelAvailable) {
            candidateModels = [requestedModel, ...preferredAvailable.filter(m => m !== requestedModel)];
          } else {
            console.warn(`[Gemini] 설정된 모델 '${requestedModel}'은 현재 이 API Key에서 지원되지 않습니다. 자동 대체합니다.`);
            candidateModels = [...preferredAvailable, ...otherAvailable];
          }
        } else {
          candidateModels = [
            requestedModel,
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-1.5-flash',
          ];
        }

        const uniqueModels = Array.from(new Set(candidateModels)).filter(Boolean);

        for (const currentModel of uniqueModels) {
          try {
            const url = `https://generativelanguage.googleapis.com/v1beta/models/${currentModel}:generateContent?key=${currentKey}`;
            const response = await ipcFetch(url, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                contents: [{ parts: [{ text: prompt }] }],
                generationConfig: {
                  temperature: temp,
                  responseMimeType: "application/json"
                }
              }),
              signal
            });

            if (!response.ok) {
              const text = await response.text();
              const err = new Error(`Gemini API Error ${response.status}: ${text}`);
              
              if (response.status === 429 || text.includes('RESOURCE_EXHAUSTED')) {
                if (isMultiKey && keyIdx < activeKeys.length - 1) {
                  console.warn(`[Gemini] ${keyIdx + 1}번째 키 사용량 초과 (429). 다음 키로 자동 전환합니다.`);
                  break; 
                }
                throw formatAIError(err, 'gemini');
              }
              throw err;
            }

            const data = await response.json();
            const content = data.candidates?.[0]?.content?.parts?.[0]?.text;
            if (content) {
              successModel = currentModel;
              if (currentModel !== requestedModel) {
                console.info(`[Gemini] '${requestedModel}' 대신 '${currentModel}'로 성공적으로 연결되었습니다.`);
                console.info(`[Gemini] '${requestedModel}' 대신 '${currentModel}'로 성공적으로 연결되었습니다.`);
              }
              global.dispatchEvent(new CustomEvent('gemini-model-resolved', { detail: { model: successModel } }));
              return content;
            }
          } catch (e) {
            console.warn(`[Gemini] 모델 '${currentModel}' 시도 실패:`, e.message);
            if (e.message.includes('무료 사용량 한도') || e.message.includes('Quota')) {
              throw e;
            }
            lastError = e;
            if (e.name === 'AbortError') throw e;
          }
        }
      } catch (e) {
        if (isMultiKey && keyIdx < activeKeys.length - 1) {
          lastError = e;
          continue;
        }
        throw e;
      }
    }

    throw formatAIError(lastError || new Error("Gemini API 호출에 모든 모델 및 API Key가 실패했습니다."), 'gemini');
  }

  /**
   * OpenRouter 연동 (DeepSeek 모델 등)
   */
  async function callOpenRouter(prompt, config, temp, signal) {
    const rawEndpoint = (config.endpointUrl || '').trim();
    const url = !rawEndpoint ? 'https://openrouter.ai/api/v1/chat/completions' : rawEndpoint;
    const model = config.modelName || 'deepseek/deepseek-chat';
    
    let activeKeys = [];
    if (Array.isArray(config.apiKeys) && config.apiKeys.length > 0) {
      activeKeys = config.apiKeys;
    } else {
      const singleKey = (config.apiKey || '').trim();
      if (singleKey) activeKeys = [singleKey];
    }
    
    if (activeKeys.length === 0) {
      throw new Error("OpenRouter API Key가 비어 있습니다. AI 설정 탭에서 API Key를 입력하세요.");
    }

    let lastError = null;

    for (let keyIdx = 0; keyIdx < activeKeys.length; keyIdx++) {
      const currentKey = activeKeys[keyIdx];
      const isMultiKey = activeKeys.length > 1;

      if (isMultiKey) {
        console.info(`[OpenRouter] 등록된 ${activeKeys.length}개의 키 중 ${keyIdx + 1}번째 키로 API 호출을 시도합니다.`);
      }

      try {
        let response;
        try {
          response = await ipcFetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${currentKey}`,
              "HTTP-Referer": "http://localhost:8081",
              "X-Title": "RiskAssessmentPro"
            },
            body: JSON.stringify({
              model: model,
              messages: [{ role: "user", content: prompt }],
              temperature: temp,
              response_format: { type: 'json_object' }
            }),
            signal
          });
        } catch (fetchErr) {
          throw fetchErr;
        }

        if (!response.ok) {
          const text = await response.text();
          
          const isAuthError = response.status === 401 || text.includes('invalid_api_key') || text.includes('authentication') || text.includes('401');
          const isQuotaOrBalanceError = response.status === 429 || response.status === 402 || text.includes('credit') || text.includes('balance') || text.includes('limit');

          if (isAuthError || isQuotaOrBalanceError) {
            const err = new Error(`OpenRouter API Error ${response.status}: ${text}`);
            if (isMultiKey && keyIdx < activeKeys.length - 1) {
              console.warn(`[OpenRouter] ${keyIdx + 1}번째 키 문제 발생 (${response.status}). 다음 키로 자동 전환합니다.`);
              throw err;
            }
            throw formatAIError(err, 'openrouter');
          }
          
          // JSON 모드 실패 시 일반 텍스트 모드로 재시도
          console.warn(`[OpenRouter] JSON 모드 호출 실패 (${response.status}). 일반 텍스트 모드로 재시도합니다.`);
          response = await ipcFetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${currentKey}`,
              "HTTP-Referer": "http://localhost:8081",
              "X-Title": "RiskAssessmentPro"
            },
            body: JSON.stringify({
              model: model,
              messages: [{ role: "user", content: prompt }],
              temperature: temp
            }),
            signal
          });

          if (!response.ok) {
            const textFinal = await response.text();
            const err = new Error(`OpenRouter API Error ${response.status}: ${textFinal}`);
            throw formatAIError(err, 'openrouter');
          }
        }

        const data = await response.json();
        return data.choices?.[0]?.message?.content || "";
      } catch (e) {
        lastError = e;
        if (e.name === 'AbortError') throw e;
        
        if (isMultiKey && keyIdx < activeKeys.length - 1) {
          continue;
        }
        throw e;
      }
    }

    throw formatAIError(lastError || new Error("OpenRouter API 호출에 모든 API Key가 실패했습니다."), 'openrouter');
  }

  /**
   * DeepSeek API 연동
   */
  async function callDeepSeek(prompt, config, temp, signal) {
    // endpointUrl이 localhost/loopback을 가리키는 경우 (LM Studio/Ollama URL 오염) 공식 API 강제 사용
    const rawEndpoint = (config.endpointUrl || '').trim();
    const isLocalhost = rawEndpoint && (rawEndpoint.includes('localhost') || rawEndpoint.includes('127.0.0.1') || rawEndpoint.includes('::1'));
    const url = (!rawEndpoint || isLocalhost) ? 'https://api.deepseek.com/chat/completions' : rawEndpoint;
    if (isLocalhost) {
      console.warn('[DeepSeek] endpointUrl이 로컬 주소로 설정되어 있어 공식 API로 자동 전환합니다:', rawEndpoint, '->', url);
    }
    const model = config.modelName || 'deepseek-chat';
    
    let activeKeys = [];
    if (Array.isArray(config.apiKeys) && config.apiKeys.length > 0) {
      activeKeys = config.apiKeys;
    } else {
      const singleKey = (config.apiKey || '').trim();
      if (singleKey) activeKeys = [singleKey];
    }
    
    if (activeKeys.length === 0) {
      throw new Error("DeepSeek API Key가 비어 있습니다. AI 설정 탭에서 API Key를 입력하세요.");
    }

    let lastError = null;

    for (let keyIdx = 0; keyIdx < activeKeys.length; keyIdx++) {
      const currentKey = activeKeys[keyIdx];
      const isMultiKey = activeKeys.length > 1;

      if (isMultiKey) {
        console.info(`[DeepSeek] 등록된 ${activeKeys.length}개의 키 중 ${keyIdx + 1}번째 키로 API 호출을 시도합니다.`);
      }

      try {
        let response;
        try {
          response = await ipcFetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${currentKey}`
            },
            body: JSON.stringify({
              model: model,
              messages: [{ role: "user", content: prompt }],
              temperature: temp,
              response_format: { type: 'json_object' }
            }),
            signal
          });
        } catch (fetchErr) {
          throw fetchErr;
        }

        if (!response.ok) {
          const text = await response.text();
          
          const isAuthError = response.status === 401 || text.includes('invalid_api_key') || text.includes('authentication');
          const isQuotaOrBalanceError = response.status === 429 || response.status === 402 || text.includes('insufficient_balance');

          if (isAuthError || isQuotaOrBalanceError) {
            const err = new Error(`DeepSeek API Error ${response.status}: ${text}`);
            if (isMultiKey && keyIdx < activeKeys.length - 1) {
              console.warn(`[DeepSeek] ${keyIdx + 1}번째 키 문제 발생 (${response.status}). 다음 키로 자동 전환합니다.`);
              throw err;
            }
            throw formatAIError(err, 'deepseek');
          }
          
          // JSON 모드 400 에러 또는 모델 파라미터 미지원 시 일반 텍스트 모드로 재시도
          console.warn(`[DeepSeek] JSON 모드 호출 실패 (${response.status}). 일반 텍스트 모드로 재시도합니다.`);
          response = await ipcFetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${currentKey}`
            },
            body: JSON.stringify({
              model: model,
              messages: [{ role: "user", content: prompt }],
              temperature: temp
            }),
            signal
          });

          if (!response.ok) {
            const textFinal = await response.text();
            const err = new Error(`DeepSeek API Error ${response.status}: ${textFinal}`);
            throw formatAIError(err, 'deepseek');
          }
        }

        const data = await response.json();
        return data.choices?.[0]?.message?.content || "";
      } catch (e) {
        lastError = e;
        if (e.name === 'AbortError') throw e;
        
        if (isMultiKey && keyIdx < activeKeys.length - 1) {
          continue;
        }
        throw e;
      }
    }

    throw formatAIError(lastError || new Error("DeepSeek API 호출에 모든 API Key가 실패했습니다."), 'deepseek');
  }

  /**
   * LM Studio 로컬 LLM 연동 (OpenAI 호환 API)
   */
  /**
   * LM Studio 현재 로드된 모델 자동 감지 헬퍼
   * LM Studio 0.4+ 전용 /models 형식: { models: [{ key, type, loaded_instances: [] }] }
   * loaded_instances 배열이 비어있지 않은 모델 = 실제 READY 상태
   */
  async function detectLMStudioModel(baseUrl, signal) {
    try {
      const modelsUrl = `${baseUrl}/models`;
      const res = await ipcFetch(modelsUrl, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal
      });
      if (!res.ok) {
        console.warn('[LM Studio] /models 응답 실패:', res.status);
        return null;
      }
      const data = await res.json();
      console.log('[LM Studio] /models 원본 응답:', JSON.stringify(data).slice(0, 300));

      // ── LM Studio 0.4+ 전용 형식: { models: [...] } ──────────────────
      if (Array.isArray(data.models)) {
        // loaded_instances가 1개 이상 = 현재 메모리에 로드된 상태
        const loadedLLM = data.models.find(m =>
          m.type === 'llm' &&
          Array.isArray(m.loaded_instances) &&
          m.loaded_instances.length > 0
        );
        if (loadedLLM) {
          // loaded_instances[0].id 가 있으면 그것을, 없으면 key 사용
          const modelId = (loadedLLM.loaded_instances[0] && loadedLLM.loaded_instances[0].id)
            ? loadedLLM.loaded_instances[0].id
            : loadedLLM.key;
          console.info(`[LM Studio] 로드된 모델 감지 성공: "${modelId}"`);
          return modelId;
        }
        // 로드된 모델 없음 → llm 타입 중 첫 번째라도 반환 (비어있어도)
        const firstLLM = data.models.find(m => m.type === 'llm');
        if (firstLLM) {
          console.warn(`[LM Studio] 현재 로드된 모델 없음. 목록 첫 번째 LLM 사용: "${firstLLM.key}"`);
          return firstLLM.key;
        }
      }

      // ── OpenAI 호환 형식 폴백: { data: [{ id }] } ────────────────────
      if (Array.isArray(data.data)) {
        const chatModel = data.data.find(m => m.id && !m.id.toLowerCase().includes('embed'));
        if (chatModel) return chatModel.id;
        if (data.data.length > 0) return data.data[0].id;
      }

      // ── 배열 직접 반환 폴백 ────────────────────────────────────────────
      if (Array.isArray(data)) {
        const chatModel = data.find(m => (m.id || m.key) && !(m.id || m.key).toLowerCase().includes('embed'));
        if (chatModel) return chatModel.id || chatModel.key;
      }

      console.warn('[LM Studio] 모델 목록에서 사용 가능한 LLM을 찾지 못했습니다.');
      return null;
    } catch (e) {
      console.warn('[LM Studio] 모델 목록 조회 실패:', e.message);
      return null;
    }
  }


  async function callLMStudio(prompt, config, temp, signal) {
    const baseUrl = (config.endpointUrl || 'http://localhost:1234/v1').replace(/\/+$/, '');
    const chatUrl = `${baseUrl}/chat/completions`;
    const apiKey = 'lm-studio';

    // ─── 모델 결정: 자동 감지 → 설정값 → 생략(null) ─────────────────────
    // LM Studio는 model 필드 생략 시 현재 로드된 모델을 자동 사용하므로
    // 감지 실패해도 null로 두면 정상 동작함
    let model = null;

    const detectedModel = await detectLMStudioModel(baseUrl, signal);
    if (detectedModel) {
      model = detectedModel;
      console.info(`[LM Studio] 자동 감지된 모델: "${model}"`);
    } else if ((config.modelName || '').trim()) {
      model = config.modelName.trim();
      console.info(`[LM Studio] 설정된 모델명 사용: "${model}"`);
    } else {
      console.info('[LM Studio] 모델명 생략 → LM Studio가 로드된 모델 자동 선택');
    }

    // ─── 요청 헬퍼: model이 null이면 body에서 model 키 자체를 제외 ────────
    const doRequest = async (useJsonMode) => {
      const body = {
        messages: [{ role: 'user', content: prompt }],
        temperature: temp
      };
      if (model) body.model = model;                           // null이면 생략
      if (useJsonMode) body.response_format = { type: 'json_object' };

      return await ipcFetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify(body),
        signal
      });
    };

    // ─── JSON 모드 시도 → 실패 시 텍스트 모드 폴백 ──────────────────────
    try {
      let response = await doRequest(true);

      if (!response.ok) {
        const errText = await response.text();
        const status = response.status;
        console.warn(`[LM Studio] JSON 모드 실패 (${status}): ${errText}`);

        if (status === 400 || status === 404 || status === 422) {
          console.info('[LM Studio] 텍스트 모드로 재시도합니다...');
          response = await doRequest(false);
          if (!response.ok) {
            const finalErr = await response.text();
            throw new Error(`LM Studio API Error ${response.status}: ${finalErr}`);
          }
        } else {
          throw new Error(`LM Studio API Error ${status}: ${errText}`);
        }
      }

      const data = await response.json();
      return data.choices?.[0]?.message?.content || '';
    } catch (e) {
      if (e.name === 'AbortError') throw e;
      throw formatAIError(e, 'lmstudio', baseUrl);
    }
  }



  /**
   * Ollama 로컬 LLM 연동
   */
  async function callOllama(prompt, config, temp, signal) {
    let baseUrl = config.endpointUrl ? config.endpointUrl.trim() : 'http://localhost:11434';
    let generateUrl = baseUrl;
    if (!generateUrl.endsWith('/api/generate')) {
      generateUrl = generateUrl.replace(/\/$/, '') + '/api/generate';
    }
    const model = config.modelName ? config.modelName.trim() : 'gemma2';

    const runGenerate = async (targetModel) => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 180000); // 3분 타임아웃

      if (signal) {
        if (signal.aborted) {
          controller.abort();
        } else {
          signal.addEventListener('abort', () => controller.abort());
        }
      }

      try {
        const response = await ipcFetch(generateUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: targetModel,
            prompt: prompt,
            stream: false,
            format: "json",
            options: {
              temperature: temp
            }
          }),
          signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
      } catch (err) {
        clearTimeout(timeoutId);
        throw err;
      }
    };

    try {
      let response = await runGenerate(model);

      if (!response.ok) {
        const text = await response.text();
        if (response.status === 404 || text.includes('not found')) {
          console.warn(`Ollama 모델 '${model}' 없음. 다른 모델 조회 시도.`);
          let tagsUrl = baseUrl.replace(/\/api\/generate$/, '').replace(/\/$/, '') + '/api/tags';
          try {
            const tagsRes = await ipcFetch(tagsUrl);
            if (tagsRes.ok) {
              const tagsData = await tagsRes.json();
              if (tagsData && Array.isArray(tagsData.models) && tagsData.models.length > 0) {
                const validModels = tagsData.models.filter(m => {
                  const nameLower = m.name.toLowerCase();
                  const familyLower = (m.details && m.details.family) ? m.details.family.toLowerCase() : "";
                  const isEmbedding = nameLower.includes('embed') || 
                                      nameLower.includes('bge-') || 
                                      nameLower.includes('minilm') ||
                                      nameLower.includes('rerank') ||
                                      nameLower.includes('colbert') ||
                                      familyLower.includes('embed') ||
                                      familyLower.includes('rerank') ||
                                      familyLower.includes('colbert');
                  return !isEmbedding;
                });

                if (validModels.length > 0) {
                  const fallbackModel = validModels[0].name;
                  console.log(`Auto-fallback: '${model}' -> '${fallbackModel}'`);
                  
                  global.dispatchEvent(new CustomEvent('ollama-model-resolved', { 
                    detail: { fallback: fallbackModel } 
                  }));

                  const retryResult = await runGenerate(fallbackModel);
                  response = retryResult;
                  if (!response.ok) {
                    const failText = await response.text();
                    throw new Error(`대체 모델 '${fallbackModel}'로 재시도 실패: ${failText}`);
                  }
                } else {
                  throw new Error("로컬 Ollama에 사용 가능한 LLM 텍스트 생성 모델이 없습니다.");
                }
              } else {
                throw new Error("로컬 Ollama에 사용 가능한 LLM 모델이 없습니다.");
              }
            }
          } catch (fallbackErr) {
            throw new Error(`Ollama 에러 (404): '${model}' 모델이 설치되어 있지 않습니다.\n[상세]: ${fallbackErr.message}`);
          }
        } else {
          throw new Error(`Ollama API Error ${response.status}: ${text}`);
        }
      }

      const data = await response.json();
      return data.response || "";
    } catch (e) {
      if (e.name === 'AbortError') {
        throw new Error("Ollama 생성 시간 초과 또는 사용자가 작업을 취소했습니다.");
      }
      if (e.message && (e.message.includes('Failed to fetch') || e.message.includes('NetworkError'))) {
        throw new Error(`Ollama 서버 연결 실패: 로컬 서버(${baseUrl})가 켜져 있는지 확인하세요.`);
      }
      throw e;
    }
  }

  /**
   * AI 연결 상태 테스트
   */
  async function testConnection(config) {
    const testPrompt = 'Reply with only this exact JSON text, nothing else: {"status":"ok"}';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    let resolvedModel = config.modelName;
    const geminiListener = (e) => { resolvedModel = e.detail.model; };
    const ollamaListener = (e) => { resolvedModel = e.detail.fallback; };
    
    global.addEventListener('gemini-model-resolved', geminiListener, { once: true });
    global.addEventListener('ollama-model-resolved', ollamaListener, { once: true });

    try {
      const responseText = await callAIAPI(testPrompt, config, 0.1, controller.signal);
      clearTimeout(timeoutId);
      
      global.removeEventListener('gemini-model-resolved', geminiListener);
      global.removeEventListener('ollama-model-resolved', ollamaListener);

      const cleanText = responseText.replace(/```json/g, '').replace(/```/g, '').trim();
      let isOk = false;
      try {
        const parsed = JSON.parse(cleanText);
        isOk = (parsed.status === 'ok' || parsed.status === 'OK');
      } catch {
        isOk = cleanText.toLowerCase().includes('"ok"') ||
               (cleanText.toLowerCase().includes('ok') && cleanText.length < 200);
      }
      return { success: isOk, usedModel: resolvedModel };
    } catch (e) {
      clearTimeout(timeoutId);
      global.removeEventListener('gemini-model-resolved', geminiListener);
      global.removeEventListener('ollama-model-resolved', ollamaListener);
      console.error('AI 연결 테스트 실패:', e);
      throw e;
    }
  }

  /**
   * 현황 데이터를 바탕으로 7단 위험성 평가서 자동 작성 요청
   */
  async function generateRiskAssessment(siteData, riskCount, config, history = [], signal = null) {
    const temp = typeof config.temp === 'number' ? config.temp : 0.7;
    const detailLevelRisk = config.detailLevelRisk || 'high';

    let riskVerbosity = "";
    if (detailLevelRisk === 'low') {
      riskVerbosity = "- 위험성평가서의 '위험발생및결과'(유해위험요인), '현재조치', '감소대책' 필드는 개조식으로 간결하게 1~2줄 내외로 핵심만 요약 기재하십시오.";
    } else if (detailLevelRisk === 'high') {
      riskVerbosity = "- 위험성평가서의 '위험발생및결과'는 구체적인 유해위험 상황과 부상을 기술하고, '현재조치'는 일반적인 안전 조치, '감소대책'은 현장에서 즉시 적용 가능한 물리적/공학적 수치 기준(예: 높이 2m 이상 시 안전대 걸이대 설치, 개구부 덮개 설치 등)과 구체적인 실무 대책을 풍부히 수록하여 4~5줄 이상의 상세한 서술식 장문으로 아주 자세하게 기재하십시오. 단, 법령명·시행령·시행규칙·조항 번호(예: 제OO조)는 절대 기재하지 마십시오.";
    } else {
      riskVerbosity = "- 위험성평가서의 각 필드는 안전 관리 서식 표준에 맞게 주요 유해위험요인과 감소 대책을 3줄 내외로 명확하고 성실하게 작성하십시오.";
    }

    let contextStr = `
[공사 현황 정보]
- 공사종류: ${siteData.constructionType || '미지정'}
- 하위 공종: ${siteData.mainWork || '미지정'}
- 주요 작업내용: ${siteData.detailWork || '미지정'}
- 사용 자재: ${siteData.materials || '미지정'}
- 투입 장비: ${siteData.equipments || '미지정'}
- 인원 구성: ${siteData.workers || '미지정'}
- 사용 공구: ${siteData.tools || '미지정'}
- 사용자 추가 고려사항: ${siteData.additionalConsiderations || '없음'}
`;

    if (siteData.dynamicFields && Object.keys(siteData.dynamicFields).length > 0) {
      contextStr += "\n[추가 정보 필드]\n";
      for (const [key, val] of Object.entries(siteData.dynamicFields)) {
        contextStr += `- ${key}: ${val}\n`;
      }
    }

    let historyStr = "";
    if (history && history.length > 0) {
      historyStr = "\n[이전 역질문 및 답변 대화 이력]\n";
      history.forEach(msg => {
        const roleName = msg.role === 'ai' ? 'AI(역질문)' : '사용자(답변)';
        historyStr += `- ${roleName}: ${msg.content}\n`;
      });
    }

    let qaInstruction = "";
    if (config.enableQA === false) {
      qaInstruction = `
★ [재질문 기능 비활성화]:
- 사용자가 재질문 기능을 비활성화했습니다. 정보가 부족하거나 애매하더라도 절대 되묻지 말고("need_more_info": false), 주어진 정보만을 바탕으로 가장 합리적이고 안전한 위험성평가를 즉시 완성하여 결과를 반환하십시오.
`;
    } else {
      qaInstruction = `
★ 중요 행동 규칙 (능동적 역질문/되묻기 알고리즘):
1. 만약 제공된 정보가 너무 빈약하여(예: 공사종류나 작업내용 등이 한두 단어에 불과하고 자재나 장비가 누락된 경우) 실제 건설현장에 실질적인 도움이 되는 고도의 위험성평가 및 감소대책을 수립하기에 중대하게 부족하다고 판단되는 경우, 최종 작성을 바로 시작하지 마십시오.
2. 대신, 사용자에게 구체적인 현장 맥락을 되물어볼 질문 리스트를 작성하여 "need_more_info": true 형식으로 반환하십시오.
3. 질문은 구체적이어야 하며, 상황에 따라 객관식(multiple_choice)과 주관식(short_answer)을 적절히 혼합하여 사용하십시오.
   - 객관식("type": "multiple_choice"): 사용자가 여러 개를 직관적이고 빠르게 체크/선택할 수 있도록 3~4개의 명확한 선택지("options": [...])를 함께 제시해 주십시오. (예: 깊이, 높이, 환경의 구체적인 범위 등)
   - 주관식("type": "short_answer"): 특이사항이나 상세 서술이 필요할 때 사용하십시오.
4. 질문 목록의 각 질문은 반드시 아래 형태의 JSON 객체여야 합니다:
   - 객관식 예시: { "id": "q1", "type": "multiple_choice", "question": "질문내용", "options": ["선택지1", "선택지2", ...] }
   - 주관식 예시: { "id": "q2", "type": "short_answer", "question": "질문내용" }
5. 만약 사용자가 이미 역질문에 답변한 대화 이력이 있고, 추가 정보가 입력되어 이제 상세히 위험성평가 작성이 가능해졌다면 더 이상 되묻지 말고 "need_more_info": false로 처리하고 데이터를 완성하십시오.
6. 입력 정보가 상세하고 충분할 경우 즉시 데이터를 완성하여 결과를 반환하십시오.
`;
    }

    const prompt = `
당신은 건설 현장 안전보건 관리 책임자이자 전문 위험성 평가관입니다.
제공된 [공사 현황 정보]를 바탕으로, '7단 정식 위험성 평가표'(총 ${riskCount}개 행)를 고신뢰성으로 안전하게 작성해야 합니다.

★ [초필수 규칙 - 현장 실무 중심 작성 가이드]:
1. 대한민국 건설 안전 관리 실무에서 통용되는 일반적인 안전 지침과 현장 관행을 바탕으로 작성하되, 현업 관리자와 근로자가 현장에서 즉시 적용하고 점검할 수 있는 현실적이고 물리적인 감소대책만을 엄격하게 제시해야 합니다.
2. 실제 건설현장 실무에서 적용 불가능한 탁상공론식 조치나 가상 기동 장비 등 비현실적인 해결책은 전면 배제하십시오.
3. 존재하지 않는 가공의 안전 기준 수치(예: 임의 조작된 허용 하중, 존재하지 않는 기온/풍속 기준)를 절대로 지어내지(Hallucination) 마십시오.

★★★ [절대 금지 규칙 - 법령/조항 인용 전면 금지]:
본 시스템은 법령 팩트체크 기능이 없으므로 허위 법령 인용에 따른 법적 책임 위험을 원천 차단합니다.
다음 항목들을 출력 텍스트에 절대 포함하지 마십시오:
- 법률명 (예: 산업안전보건법, 건설기술진흥법 등)
- 시행령, 시행규칙 명칭
- 조항 번호 (예: 제OO조, 제OO항, 제OO호)
- 고시, 지침, 기준 문서 번호
위반 시 허위 법령 유포로 간주됩니다. 대신, 구체적인 물리적 수치(높이, 하중, 거리 등)와 현장 실무 용어만으로 감소대책을 서술하십시오.

★ [출력 분량 및 글자수 제한 지침]:
1. '위험발생및결과'(유해위험요인) 필드의 텍스트는 공백 포함 반드시 최대 ${config.maxLenHazard || 50}자 이내로 핵심만 간결하고 명료하게 작성하십시오. (절대 초과 금지)
2. '감소대책'(개선대책) 필드의 텍스트는 공백 포함 반드시 최대 ${config.maxLenMeasure || 100}자 이내로 실무 핵심 대책 위주로 작성하십시오. (절대 초과 금지)
3. ${riskVerbosity}

${contextStr}
${historyStr}

------------------------------------
${qaInstruction}

------------------------------------
★ 출력 형식 제한 (JSON):
반드시 순수한 JSON 데이터만 답변하십시오. 부가설명이나 서론, 결론, 마크다운 코드 블록 기호(\`\`\`json ...)는 절대 포함하지 마십시오.

출력 JSON 스키마는 반드시 아래의 두 가지 분기 포맷 중 하나와 정확히 일치해야 합니다:

[분기 1: 정보가 부족하여 되물어볼 때]
{
  "need_more_info": true,
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice",
      "question": "구체적인 추가 정보 확인 객관식 질문",
      "options": ["선택지 1", "선택지 2", "선택지 3"]
    },
    {
      "id": "q2",
      "type": "short_answer",
      "question": "구체적인 추가 정보 확인 주관식 질문"
    }
  ]
}

[분기 2: 정보가 충분하여 최종 작성할 때]
{
  "need_more_info": false,
  "gongjong": "대표 대분류 공종명 (예: 사용자가 입력한 공사 종류와 주요 작업에 기초하여 '토목공사', '상수도공사', '철골공사', '가설공사' 등 실무적으로 구분이 뚜렷한 대분류 공종명을 2~10글자로 판단하여 기재. 단, 'AI 생성공종'이나 현장명 같은 수식어는 절대 제외하고 순수한 공종명만 쓸 것)",
  "risk_assessment": [
    {
      "sebu": "세부작업명 (예: 철골 부재 인양 및 고치)",
      "wihum": "위험세부분류. 해당 위험요인의 구체적인 유해인자나 작업 형태에 따라 분류하십시오. 예: '일반위험', '작업공구', '투입장비', 'MSDS/화학물질', '추락/낙하', '감전', '협착/끼임', '밀폐공간/가스', '전도/넘어짐' 등 내용과 밀접한 실무 안전 분류명 중 하나를 2~8글자로 동적 기재하십시오.",
      "위험발생및결과": "유해위험요인 (예: 크레인 샤클 체결 불량으로 부재가 낙하하여 하부 작업자 강타)",
      "현재조치": "현재 조치사항 (예: 작업구역 하부 통제 및 인양 로프 점검)",
      "위험성": "현재 위험성 등급 ('상', '중', '하' 중 선택)",
      "감소대책": "위험성 감소대책 (예: 샤클 안전핀 체결 여부를 관리자가 인양 전 육안 확인하고, 하부 통제구역 내 무단침입 방지를 위해 전담 신호수 상시 배치)",
      "개선후위험성": "개선 후 위험성 등급 ('중', '하' 중 선택. 반드시 현재 위험성보다 낮거나 같게 설정)"
    }
  ]
}

- "risk_assessment"는 사용자가 요청한 개수(총 ${riskCount}개 행)를 정확히 맞추어 생성해야 합니다.
- 위험등급("위험성", "개선후위험성")은 각 요인의 심각성과 빈도를 바탕으로 가장 타당한 값을 자동으로 판단하여 기입하십시오.
`;

    try {
      const responseText = await callAIAPI(prompt, config, temp, signal);
      // [PATCH] AI 위험요인 생성 결과 JSON 파싱 시 안전 슬라이싱 추출 헬퍼 적용
      const parsedData = extractJson(responseText);
      return parsedData;
    } catch (e) {
      console.error("AI 응답 해석 실패. 원본 응답:", e);
      throw new Error(`AI의 응답을 JSON 형태로 파싱하는 데 실패했습니다. 다시 시도해 주세요.\n[상세 에러]: ${e.message}`);
    }
  }

  /**
   * AI 오류 메시지를 친절한 한국어 안내 메시지로 가공
   */
  function formatAIError(err, provider) {
    const errMsg = err instanceof Error ? err.message : String(err);
    let friendlyMsg = errMsg;

    if (provider === 'gemini') {
      if (errMsg.includes('RESOURCE_EXHAUSTED') || errMsg.includes('429')) {
        friendlyMsg = "Gemini API 무료 사용량 한도(Quota)를 초과했습니다.\n\n[조치 방법]:\n1. 약 1~2분 정도 기다렸다가 다시 시도해 주세요.\n2. 구글 AI 스튜디오에서 결제가 등록된 API Key로 변경해 주세요.\n3. 다른 API Key를 사용해 주세요.";
      } else if (errMsg.includes('API_KEY_INVALID') || (errMsg.includes('400') && (errMsg.includes('API key') || errMsg.includes('key')))) {
        friendlyMsg = "유효하지 않은 Gemini API Key입니다. AI 설정 탭에 올바른 API Key를 입력하셨는지 확인해 주세요.";
      } else if (errMsg.includes('model') && (errMsg.includes('not found') || errMsg.includes('404'))) {
        friendlyMsg = "선택하신 Gemini 모델이 현재 활성화되어 있지 않거나 존재하지 않습니다. AI 설정 탭에서 모델명을 다시 확인하거나, 연결 테스트를 진행해 보세요.";
      } else {
        friendlyMsg = `Gemini API 호출 중 오류가 발생했습니다.\n[에러 내용]: ${errMsg}`;
      }
    } else if (provider === 'deepseek') {
      if (errMsg.includes('insufficient_balance') || errMsg.includes('402')) {
        friendlyMsg = `DeepSeek 계정의 잔액(Credit)이 부족하여 API를 사용할 수 없습니다.

[조치 방법]:
DeepSeek 플랫폼(platform.deepseek.com)에 로그인하신 후 크레딧을 충전해 주세요.`;
      } else if (errMsg.includes('invalid_api_key') || errMsg.includes('401')) {
        friendlyMsg = "유효하지 않은 DeepSeek API Key입니다. AI 설정 탭에 올바른 API Key를 입력하셨는지 확인해 주세요.";
      } else if (errMsg.includes('429') || errMsg.includes('Too Many Requests')) {
        friendlyMsg = "DeepSeek API 요청 빈도 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.";
      } else {
        friendlyMsg = `DeepSeek API 호출 중 오류가 발생했습니다.
[에러 내용]: ${errMsg}`;
      }
    } else if (provider === 'openrouter') {
      if (errMsg.includes('credit') || errMsg.includes('balance') || errMsg.includes('402') || errMsg.includes('429') || errMsg.includes('limit')) {
        friendlyMsg = `OpenRouter 계정의 잔액(Credit)이 부족하거나 호출 한도를 초과했습니다.

[조치 방법]:
OpenRouter 플랫폼(openrouter.ai)에 로그인하신 후 계정 잔액을 충전하거나 API Key의 한도(Limit) 설정을 상향해 주세요.`;
      } else if (errMsg.includes('401') || errMsg.includes('key') || errMsg.includes('auth')) {
        friendlyMsg = "유효하지 않은 OpenRouter API Key입니다. AI 설정 탭에 올바른 API Key를 입력하셨는지 확인해 주세요.";
      } else {
        friendlyMsg = `OpenRouter API 호출 중 오류가 발생했습니다.
[에러 내용]: ${errMsg}`;
      }
    } else if (provider === 'ollama') {
      if (errMsg.includes('Failed to fetch') || errMsg.includes('NetworkError')) {
        friendlyMsg = "로컬 Ollama 서버에 연결할 수 없습니다. Ollama 앱이 실행 중인지, 혹은 주소(http://localhost:11434)가 올바른지 확인해 주세요.";
      } else {
        friendlyMsg = `Ollama 호출 중 오류가 발생했습니다.
[에러 내용]: ${errMsg}`;
      }
    } else if (provider === 'lmstudio') {
      if (errMsg.includes('Failed to fetch') || errMsg.includes('NetworkError')) {
        friendlyMsg = "로컬 LM Studio 서버에 연결할 수 없습니다. LM Studio 앱이 실행 중이고 'Local Server'가 켜져 있는지, 그리고 주소(http://localhost:1234/v1)가 올바른지 확인해 주세요.";
      } else {
        friendlyMsg = `LM Studio 호출 중 오류가 발생했습니다.
[에러 내용]: ${errMsg}`;
      }
    }

    const newErr = new Error(friendlyMsg);
    newErr.originalError = err;
    return newErr;
  }

  /**
   * 특정 행의 특정 필드 및 그 하위 필드들을 상위 문맥에 맞춰 재생성
   */
  async function regenerateRiskField(field, siteData, rowData, config, signal = null) {
    const temp = typeof config.temp === 'number' ? config.temp : 0.7;
    const detailLevelRisk = config.detailLevelRisk || 'high';

    let riskVerbosity = "";
    if (detailLevelRisk === 'low') {
      riskVerbosity = "- 각 필드는 개조식으로 간결하게 1~2줄 내외로 핵심만 요약 기재하십시오.";
    } else if (detailLevelRisk === 'high') {
      riskVerbosity = "- '위험발생및결과'는 구체적인 유해위험 상황과 부상을 기술하고, '현재조치'는 일반적인 안전 조치, '감소대책'은 현장에서 즉시 적용 가능한 물리적/공학적 수치 기준(예: 높이 2m 이상 시 안전대 걸이대 설치 등)과 구체적인 실무 대책을 풍부히 수록하여 4~5줄 이상의 상세한 서술식 장문으로 아주 자세하게 기재하십시오. 단, 법령명·시행령·시행규칙·조항 번호(예: 제OO조)는 절대 기재하지 마십시오.";
    } else {
      riskVerbosity = "- 각 필드는 안전 관리 서식 표준에 맞게 주요 유해위험요인과 감소 대책을 3줄 내외로 명확하고 성실하게 작성하십시오.";
    }

    // 필드별 타겟 및 프롬프트 제약 설정
    let targetPrompt = "";
    let expectedJsonSchema = "";

    if (field === '세부작업명') {
      targetPrompt = `
[기존 정보]:
- 공사종류: ${siteData.constructionType || ''}
- 하위 공종: ${siteData.mainWork || ''}
- 주요 작업내용: ${siteData.detailWork || ''}
- 대분류 공종: ${siteData.gongjong || '미분류'}
- 사용자 추가 고려사항: ${siteData.additionalConsiderations || '없음'}

[요청]:
대분류 공종인 [${siteData.gongjong || '미분류'}] 및 하위 공종인 [${siteData.mainWork || ''}]에 실무적으로 가장 잘 어울리는 새로운 '세부작업명'(sebu)을 한 문장으로 제안해 주십시오.
또한, 새로 만들어진 세부작업명에 종속되는 하위 필드들('위험세부분류', '위험발생및결과', '현재조치', '감소대책')도 문맥과 안전 보건 지침에 부합하도록 일괄 새로 작성해 주십시오.
`;
      expectedJsonSchema = `
{
  "sebu": "새로 생성된 세부작업명 (예: 굴착기 버킷 교체 작업)",
  "wihum": "이에 맞는 위험세부분류 (예: 투입장비)",
  "위험발생및결과": "유해위험요인 (예: 버킷 연결핀 해체 중 안전핀이 튕겨 눈 부상)",
  "현재조치": "현재 조치사항 (예: 작업 전 보호구 착용 및 장비 시동 해제)",
  "감소대책": "감소대책 (예: 버킷 교체 시 유압 라인 잔압 해제 밸브를 열어 압력을 완전히 배출하고, 작업자는 비산 위험에 대비하여 보안경 및 안전장갑을 필수 착용하도록 현장 지도)"
}
`;
    } else if (field === '위험세부분류') {
      targetPrompt = `
[기존 정보]:
- 공사종류: ${siteData.constructionType || ''}
- 하위 공종: ${siteData.mainWork || ''}
- 주요 작업내용: ${siteData.detailWork || ''}
- 대분류 공종: ${siteData.gongjong || '미분류'}
- 세부작업명: ${rowData.sebu || ''}
- 사용자 추가 고려사항: ${siteData.additionalConsiderations || '없음'}

[요청]:
위 기존 정보를 바탕으로 가장 실무적인 새로운 '위험세부분류'(wihum)를 제안해 주십시오. (예: '일반위험', '작업공구', '투입장비', 'MSDS/화학물질', '추락/낙하', '감전', '협착/끼임' 등 중 어울리는 분류)
또한, 새로운 위험세부분류에 맞추어 하위 필드들('위험발생및결과', '현재조치', '감소대책')도 새로운 안전 지침에 적합하게 갱신해 주십시오.
`;
      expectedJsonSchema = `
{
  "wihum": "새로 생성된 위험세부분류 (예: 추락/낙하)",
  "위험발생및결과": "이에 종속되는 유해위험요인 (예: 고소 작업발판 끝단에서 몸을 내밀어 비계 핀 체결 중 중심을 잃고 2m 아래로 추락)",
  "현재조치": "현재 조치사항 (예: 추락방지망 설치 상태 점검 및 안전대 고리 체결 확인)",
  "감소대책": "감소대책 (예: 안전대 걸이대 높이를 작업자 어깨 높이 이상으로 상향 설치하고, 비계 외측 단부에는 안전난간 및 발끝막이판을 설치)"
}
`;
    } else if (field === '위험발생및결과') {
      targetPrompt = `
[기존 정보]:
- 공사종류: ${siteData.constructionType || ''}
- 하위 공종: ${siteData.mainWork || ''}
- 주요 작업내용: ${siteData.detailWork || ''}
- 대분류 공종: ${siteData.gongjong || '미분류'}
- 세부작업명: ${rowData.sebu || ''}
- 위험세부분류: ${rowData.wihum || ''}
- 사용자 추가 고려사항: ${siteData.additionalConsiderations || '없음'}

[요청]:
위 기존 정보를 바탕으로 가장 일어날 법한 실제 유해위험 사고 시나리오인 '유해위험요인(위험발생및결과)'(위험발생및결과)을 새로이 한 문장으로 구체적으로 기술해 주십시오.
또한, 새로이 만들어진 위험요인에 맞추어 하위 필드들('현재조치', '감소대책')도 적합하게 일괄 갱신해 주십시오.
`;
      expectedJsonSchema = `
{
  "위험발생및결과": "새로 생성된 유해위험요인 (예: 용접 작업 중 불티가 주변 인화 물질인 스티로폼 단열재로 비산하여 화재 및 연기 질식 사고 발생)",
  "현재조치": "현재 조치사항 (예: 작업장 인근 소화기 배치 및 가연물 정리정돈)",
  "감소대책": "감소대책 (예: 용접 작업 반경 10m 이내 가연물 전면 제거 및 화재감시자 상시 배치, 불꽃 불티 비산방지포 설치로 화재 요인 원천 차단)"
}
`;
    } else if (field === '현재조치') {
      targetPrompt = `
[기존 정보]:
- 공사종류: ${siteData.constructionType || ''}
- 하위 공종: ${siteData.mainWork || ''}
- 주요 작업내용: ${siteData.detailWork || ''}
- 대분류 공종: ${siteData.gongjong || '미분류'}
- 세부작업명: ${rowData.sebu || ''}
- 위험세부분류: ${rowData.wihum || ''}
- 유해위험요인: ${rowData.위험발생및결과 || ''}
- 사용자 추가 고려사항: ${siteData.additionalConsiderations || '없음'}

[요청]:
위 기존 정보를 바탕으로 작업 전 또는 현장에 기본적으로 취해야 하는 일반적인 '현재조치사항'(현재조치)을 한 문장으로 작성해 주십시오.
또한, 하위 필드인 '감소대책' 역시 새로 정의된 현재 조치와 위험 요인에 맞추어 한 단계 더 정밀하게 연동 갱신해 주십시오.
`;
      expectedJsonSchema = `
{
  "현재조치": "새로 생성된 현재 조치사항 (예: 전기 릴선 피복 손상 유무 및 누전차단기 정상 동작 여부 사전 점검)",
  "감소대책": "이에 부합하는 감소대책 (예: 손상된 피복은 즉시 폐기하고 규격품 케이블을 사용하며, 모든 임시 동력 분전반에는 감전 예방용 고감도 누전차단기를 의무 설치하고 월 1회 작동 시험 실시)"
}
`;
    } else if (field === '감소대책') {
      targetPrompt = `
[기존 정보]:
- 공사종류: ${siteData.constructionType || ''}
- 하위 공종: ${siteData.mainWork || ''}
- 주요 작업내용: ${siteData.detailWork || ''}
- 대분류 공종: ${siteData.gongjong || '미분류'}
- 세부작업명: ${rowData.sebu || ''}
- 위험세부분류: ${rowData.wihum || ''}
- 유해위험요인: ${rowData.위험발생및결과 || ''}
- 현재조치: ${rowData.현재조치 || ''}
- 현재위험성: ${rowData.위험성 || '중'}
- 사용자 추가 고려사항: ${siteData.additionalConsiderations || '없음'}

[요청]:
위 기존 정보들을 종합하여 위험 요인을 효과적으로 제어 및 근절할 수 있는 구체적이고 현장 적용이 가능한 '감소대책'(감소대책)을 새로 상세히 작성해 주십시오.
하위 필드가 없으므로, 오직 '감소대책' 하나만 새로 작성하여 아래 JSON으로 반환해 주십시오.
`;
      expectedJsonSchema = `
{
  "감소대책": "새로 생성된 감소대책 (예: 이동식 비계 바퀴에 스토퍼 잠금장치를 상시 체결하고 비계 상부에서 작업 중에는 비계 이동을 절대 금지하며, 아웃트리거를 4면에 견고히 설치하여 전도를 방지)"
}
`;
    }

    // [기존 코드 보존]
    /*
    const prompt = `
당신은 건설 현장 안전보건 관리 책임자이자 전문 위험성 평가관입니다.
[요청] 및 [기존 정보]를 분석하여 주어진 필드의 내용을 7단 위험성 평가 기준에 맞추어 실무적이고 안전하게 재생성하여 반환하십시오.

★ [초필수 규칙 - 법적 공신력 및 현장 현실성 가이드]:
1. 반드시 대한민국 법령 및 안전 보건 규칙(예: '산업안전보건기준에 관한 규칙', '산업안전보건법', '건설기술 진흥법')에 실존하는 정확한 안전 지침, 작업 허가 규정만을 기반으로 작성해야 합니다.
2. 실제 건설현장 실무에서 적용 불가능한 탁상공론식 조치나 가상 기동 장비 등 비현실적인 해결책은 전면 배제하고, 현업 관리자와 근로자가 현장에서 즉시 적용하고 점검할 수 있는 현실적이고 물리적인 감소대책만을 엄격하게 제시해야 합니다.
3. 법적 근거가 명확한 규칙 조항 번호(예: 규칙 제32조, 제42조 등)와 공인된 물리적 수치 기준(예: 높이 2m 이상 시 작업발판 설치 등)을 성실하게 인용하십시오.

★ [출력 분량 및 글자수 제한 지침]:
1. '위험발생및결과'(유해위험요인) 필드의 텍스트는 공백 포함 반드시 최대 ${config.maxLenHazard || 50}자 이내로 핵심만 간결하고 명료하게 작성하십시오. (절대 초과 금지)
2. '감소대책'(개선대책) 필드의 텍스트는 공백 포함 반드시 최대 ${config.maxLenMeasure || 100}자 이내로 실무 핵심 대책 위주로 작성하십시오. (절대 초과 금지)
3. ${riskVerbosity}

${targetPrompt}

------------------------------------
★ 출력 형식 제한 (JSON):
반드시 순수한 JSON 데이터만 답변하십시오. 부가설명이나 서론, 결론, 마크다운 코드 블록 기호(\`\`\`json ...)는 절대 포함하지 마십시오.

출력 JSON 스키마는 반드시 아래 포맷과 완벽히 일치해야 합니다:
${expectedJsonSchema}
`;
    */
    let updateInstructions = "";
    if (siteData && siteData.isUpdateProtocol) {
      updateInstructions = `
★ [갱신 프로토콜 특별 지침 - 우선순위 절대 준수]:
- 현재 작업은 기존에 작성된 위험성평가 테이블의 특정 행을 부분적으로 '재생성 및 갱신(Update)'하는 과정입니다.
- 최초 AI 생성 모달에 입력되어 있었던 [공사종류], [하위 공종], [주요 작업내용] 정보보다, **현재 대상 행의 [대분류 공종] 및 [세부작업명](sebu)이 가장 최신의 물리적 현실을 반영하는 최상위 맥락**입니다.
- 최초 폼 입력 정보(예: 토공사, 터파기 등)와 현재 행의 실제 값(예: 잠철 공사, 견출 공사, 코킹 등)이 서로 다르거나 충돌할 경우, **절대로 최초 입력 폼의 정보에 가중치를 두지 마십시오.**
- 오직 **현재 행의 [대분류 공종] 및 [세부작업명/위험세부분류]에 물리적·실무적으로 100% 매치되는 자연스럽고 정확한 안전대책**을 도출하십시오. (예: 견출/코킹 공종의 행이면 견출/코킹에 관한 유해위험요인과 추락/낙하 방지 대책을 수립해야 하며, 터파기 대책을 작성해서는 안 됩니다.)
`;
    }

    const prompt = `
당신은 건설 현장 안전보건 관리 책임자이자 전문 위험성 평가관입니다.
[요청] 및 [기존 정보]를 분석하여 주어진 필드의 내용을 7단 위험성 평가 기준에 맞추어 실무적이고 안전하게 재생성하여 반환하십시오.

${updateInstructions}

★ [초필수 규칙 - 현장 실무 중심 작성 가이드]:
1. 대한민국 건설 안전 관리 실무에서 통용되는 일반적인 안전 지침과 현장 관행을 바탕으로 작성하십시오.
2. 실제 건설현장 실무에서 적용 불가능한 탁상공론식 조치나 가상 기동 장비 등 비현실적인 해결책은 전면 배제하고, 현업 관리자와 근로자가 현장에서 즉시 적용하고 점검할 수 있는 현실적이고 물리적인 감소대책만을 엄격하게 제시해야 합니다.
3. 법령명·시행령·시행규칙·조항 번호(예: 제OO조, 산업안전보건법 등)는 절대 기재하지 마십시오. 구체적인 물리적 수치 기준(예: 높이 2m 이상 시 작업발판 설치 등)만 인용하십시오.

★ [출력 분량 및 글자수 제한 지침]:
1. '위험발생및결과'(유해위험요인) 필드의 텍스트는 공백 포함 반드시 최대 ${config.maxLenHazard || 50}자 이내로 핵심만 간결하고 명료하게 작성하십시오. (절대 초과 금지)
2. '감소대책'(개선대책) 필드의 텍스트는 공백 포함 반드시 최대 ${config.maxLenMeasure || 100}자 이내로 실무 핵심 대책 위주로 작성하십시오. (절대 초과 금지)
3. ${riskVerbosity}

${targetPrompt}

------------------------------------
★ 출력 형식 제한 (JSON):
반드시 순수한 JSON 데이터만 답변하십시오. 부가설명이나 서론, 결론, 마크다운 코드 블록 기호(\`\`\`json ...)는 절대 포함하지 마십시오.

출력 JSON 스키마는 반드시 아래 포맷과 완벽히 일치해야 합니다:
${expectedJsonSchema}
`;

    try {
      const responseText = await callAIAPI(prompt, config, temp, signal);
      // [PATCH] AI 필드 재생성 결과 JSON 파싱 시 안전 슬라이싱 추출 헬퍼 적용
      const parsedData = extractJson(responseText);
      return parsedData;
    } catch (e) {
      console.error("AI 필드 재생성 응답 해석 실패. 원본 응답:", e);
      throw new Error(`AI의 응답을 JSON 형태로 파싱하는 데 실패했습니다. 다시 시도해 주세요.\\n[상세 에러]: ${e.message}`);
    }
  }

  /**
   * 위험성평가 데이터 일괄 다국어 번역 수행
   */
  async function translateRiskAssessment(items, targetLang, config, signal = null) {
    const temp = 0.3; // 번역의 정확성 및 일관성을 위해 온도를 낮춤
    const langNames = {
      en: "English (영어)",
      zh: "Chinese (중국어)",
      vi: "Vietnamese (베트남어)",
      mn: "Mongolian (몽골어)"
    };
    const targetLangName = langNames[targetLang] || targetLang;

    /* [기존 코드 보존]
    const rawPayload = items.map((item, idx) => ({
      idx,
      sebu: item.sebu || '',
      wihum: item.wihum || '',
      위험발생및결과: item.위험발생및결과 || '',
      현재조치: item.현재조치 || '',
      감소대책: item.감소대책 || ''
    }));

    const prompt = `
당신은 건설 안전보건 분야에 전문화된 대한민국 번역가입니다.
제시된 위험성평가 데이터(JSON 배열)를 분석하여 각 필드의 내용을 자연스럽고 전문적인 [${targetLangName}]로 정확하게 1:1 대조 번역하십시오.

★ [번역 규칙 - 절대 준수]:
1. 임의로 위험성 내용을 창작하거나 안전 조치를 가공하여 추가하지 마십시오. 오직 원문 그대로 번역만 수행해야 합니다.
2. 텍스트 내의 수치 기준(예: 2m, 1.5m 등) 및 법적 조항(예: 규칙 제32조, 제42조 등)은 절대 변경하지 말고 그대로 번역어와 조화롭게 포함하여 유지하십시오.
3. 건설 분야 실무 장비 명칭(예: Table Lift, 스카이 장비, 굴착기 등)은 글로벌 표준 건설 용어 또는 현지 실무어로 명확하게 대칭 번역하십시오.
4. 부가적인 주석, 서론/결론, 백틱 기호(예: \`\`\`) 등은 최종 결과물에 절대로 포함하지 마십시오. 순수한 JSON 배열만 출력하십시오.

번역할 원본 데이터 (JSON):
${JSON.stringify(rawPayload, null, 2)}

반환할 JSON 구조 스키마 (배열):
[
  {
    "idx": 0,
    "sebu": "번역된 세부작업명",
    "wihum": "번역된 위험세부분류",
    "위험발생및결과": "번역된 유해위험요인",
    "현재조치": "번역된 현재 안전보건 조치",
    "감소대책": "번역된 감소대책"
  },
  ...
]
`;
    */

    // 번역에 필요한 텍스트 정보만 간소화하여 전송 (대분류 공종명 gongjong 추가)
    const rawPayload = items.map((item, idx) => ({
      idx,
      gongjong: item.gongjong || '',
      sebu: item.sebu || '',
      wihum: item.wihum || '',
      위험발생및결과: item.위험발생및결과 || '',
      현재조치: item.현재조치 || '',
      감소대책: item.감소대책 || ''
    }));

    const prompt = `
당신은 건설 안전보건 분야에 전문화된 대한민국 번역가입니다.
제시된 위험성평가 데이터(JSON 배열)를 분석하여 각 필드의 내용을 자연스럽고 전문적인 [${targetLangName}]로 정확하게 1:1 대조 번역하십시오.

★ [번역 규칙 - 절대 준수]:
1. 임의로 위험성 내용을 창작하거나 안전 조치를 가공하여 추가하지 마십시오. 오직 원문 그대로 번역만 수행해야 합니다.
2. 텍스트 내의 수치 기준(예: 2m, 1.5m 등) 등 원문에 포함된 수치는 절대 변경하지 말고 그대로 번역어와 조화롭게 포함하여 유지하십시오.
3. 건설 분야 실무 장비 명칭(예: Table Lift, 스카이 장비, 굴착기 등)은 글로벌 표준 건설 용어 또는 현지 실무어로 명확하게 대칭 번역하십시오.
4. 부가적인 주석, 서론/결론, 백틱 기호(예: \`\`\`) 등은 최종 결과물에 절대로 포함하지 마십시오. 순수한 JSON 배열만 출력하십시오.

번역할 원본 데이터 (JSON):
${JSON.stringify(rawPayload, null, 2)}

반환할 JSON 구조 스키마 (배열):
[
  {
    "idx": 0,
    "gongjong": "번역된 대분류 공종명",
    "sebu": "번역된 세부작업명",
    "wihum": "번역된 위험세부분류",
    "위험발생및결과": "번역된 유해위험요인",
    "현재조치": "번역된 현재 안전보건 조치",
    "감소대책": "번역된 감소대책"
  },
  ...
]
`;

    try {
      const responseText = await callAIAPI(prompt, config, temp, signal);
      // [PATCH] AI 다국어 번역 결과 JSON 파싱 시 안전 슬라이싱 추출 헬퍼 적용
      const parsedData = extractJson(responseText);
      return parsedData;
    } catch (e) {
      console.error("AI 다국어 번역 응답 해석 실패. 원본 응답:", e);
      throw new Error(`AI 다국어 번역 처리에 실패했습니다. 다시 시도해 주세요.\\n[상세]: ${e.message}`);
    }
  }

  /**
   * OpenRouter API Key 잔액 및 크레딧 사용량 조회
   */
  async function getOpenRouterKeyUsage(apiKey) {
    try {
      const url = 'https://openrouter.ai/api/v1/key';
      const response = await ipcFetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${apiKey}`
        },
        signal: AbortSignal.timeout(6000)
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const resData = await response.json();
      if (resData && resData.data) {
        return {
          success: true,
          label: resData.data.label,
          limit: resData.data.limit,
          usage: resData.data.usage,
          limit_remaining: resData.data.limit_remaining,
          is_active: resData.data.is_active
        };
      }
      throw new Error("올바른 응답 형식이 아닙니다.");
    } catch (e) {
      console.warn('[OpenRouter] 키 사용량 조회 실패:', e.message);
      return { success: false, error: e.message };
    }
  }

  // [기존 코드 보존]
  /*
  // 전역에 노출
  global.aiService = {
    defaultAIConfig,
    testConnection,
    generateRiskAssessment,
    regenerateRiskField
  };
  */
  // 전역에 노출
  global.aiService = {
    defaultAIConfig,
    testConnection,
    generateRiskAssessment,
    regenerateRiskField,
    translateRiskAssessment,
    getOpenRouterKeyUsage
  };

})(window);
