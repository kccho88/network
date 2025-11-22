// 제조사별 기본 설정값
const vendorDefaults = {
    cisco: {
        mgmt_vlan: 100,
        mgmt_interface: 'Gi1/0/1',
        gateway: '192.168.10.254',
        interfaceHelp: '예: Gi1/0/1, Fa0/1'
    },
    arista: {
        mgmt_vlan: 100,
        mgmt_interface: 'Management1',
        gateway: '192.168.10.254',
        interfaceHelp: '예: Management1, Ethernet1'
    },
    alcatel: {
        mgmt_vlan: 100,
        mgmt_interface: '1/1/1',
        gateway: '192.168.10.254',
        interfaceHelp: '예: 1/1/1, 1/2/1'
    },
    hp: {
        mgmt_vlan: 100,
        mgmt_interface: '1',
        gateway: '192.168.10.254',
        interfaceHelp: '예: 1, 2, A1'
    },
    juniper: {
        mgmt_vlan: 100,
        mgmt_interface: 'ge-0/0/0',
        gateway: '192.168.10.254',
        interfaceHelp: '예: ge-0/0/0, xe-0/0/0'
    },
    fortinet: {
        mgmt_port: 'port1',
        gateway: '192.168.10.254'
    }
};

// DOM 요소
const apiKeyInput = document.getElementById('apiKey');
const toggleApiKeyBtn = document.getElementById('toggleApiKey');
const requirementsInput = document.getElementById('requirements');
const vendorSelect = document.getElementById('vendor');
const hostnameInput = document.getElementById('hostname');
const mgmtIpInput = document.getElementById('mgmt_ip');
const mgmtMaskInput = document.getElementById('mgmt_mask');
const mgmtVlanInput = document.getElementById('mgmt_vlan');
const mgmtInterfaceInput = document.getElementById('mgmt_interface');
const mgmtPortInput = document.getElementById('mgmt_port');
const gatewayInput = document.getElementById('gateway');
const interfaceHelp = document.getElementById('interfaceHelp');
const mgmtIpRequired = document.getElementById('mgmt_ip_required');
const mgmtMaskRequired = document.getElementById('mgmt_mask_required');

const vlanFields = document.getElementById('vlanFields');
const interfaceFields = document.getElementById('interfaceFields');
const portFields = document.getElementById('portFields');
const gatewayFields = document.getElementById('gatewayFields');

const configForm = document.getElementById('configForm');
const resultArea = document.getElementById('resultArea');
const configOutput = document.getElementById('configOutput');
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('errorMessage');
const generateBtn = document.getElementById('generateBtn');
const resetBtn = document.getElementById('resetBtn');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');

let currentConfig = null;
let currentVendor = null;
let currentHostname = null;

// API 키 저장/로드
function saveApiKey(apiKey) {
    if (apiKey) {
        localStorage.setItem('openai_api_key', apiKey);
    }
}

function loadApiKey() {
    return localStorage.getItem('openai_api_key') || '';
}

// 페이지 로드 시 초기화
window.addEventListener('DOMContentLoaded', function() {
    // 저장된 API 키 불러오기
    const savedApiKey = loadApiKey();
    if (savedApiKey) {
        apiKeyInput.value = savedApiKey;
        // 저장된 API 키가 있으면 인증 완료 표시
        showApiKeyStatus(true);
    } else {
        showApiKeyStatus(false);
    }
    
    // 버튼 이벤트 리스너 등록 (DOM이 로드된 후)
    if (generateBtn) {
        console.log('generateBtn 찾음, 이벤트 리스너 등록');
        generateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('버튼 클릭됨 - generateConfig 호출 시작');
            try {
                if (typeof window.generateConfig === 'function') {
                    window.generateConfig(e);
                } else {
                    console.error('generateConfig 함수를 찾을 수 없습니다.');
                    alert('페이지가 완전히 로드되지 않았습니다. 잠시 후 다시 시도해주세요.');
                }
            } catch (error) {
                console.error('generateConfig 실행 중 오류:', error);
                alert('오류가 발생했습니다: ' + error.message);
            }
            return false;
        });
    } else {
        console.error('generateBtn을 찾을 수 없습니다. DOM이 아직 로드되지 않았을 수 있습니다.');
        // 재시도
        setTimeout(function() {
            const retryBtn = document.getElementById('generateBtn');
            if (retryBtn) {
                console.log('재시도: generateBtn 찾음');
                retryBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('버튼 클릭됨 (재시도)');
                    if (typeof window.generateConfig === 'function') {
                        window.generateConfig(e);
                    } else {
                        console.error('generateConfig 함수를 찾을 수 없습니다.');
                    }
                    return false;
                });
            }
        }, 500);
    }
    
    // 폼 제출 이벤트
    if (configForm) {
        if (!configForm.hasAttribute('data-submit-handled')) {
            configForm.setAttribute('data-submit-handled', 'true');
            configForm.addEventListener('submit', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('폼 제출됨');
                if (typeof window.generateConfig === 'function') {
                    window.generateConfig(e);
                } else {
                    console.error('generateConfig 함수를 찾을 수 없습니다.');
                }
                return false;
            });
        }
    }
});

// API 키 상태 표시 함수
function showApiKeyStatus(isSaved) {
    const apiKeySection = document.querySelector('.api-key-section');
    if (!apiKeySection) return;
    
    // 기존 상태 메시지 제거
    const existingStatus = apiKeySection.querySelector('.api-key-status');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    if (isSaved) {
        const statusDiv = document.createElement('div');
        statusDiv.className = 'api-key-status success-message';
        statusDiv.style.marginTop = '10px';
        statusDiv.style.padding = '10px';
        statusDiv.innerHTML = '✓ 저장된 API 키가 로드되었습니다. 바로 사용할 수 있습니다.';
        apiKeySection.appendChild(statusDiv);
    }
}

// API 키 표시/숨기기 토글
toggleApiKeyBtn.addEventListener('click', function() {
    if (apiKeyInput.type === 'password') {
        apiKeyInput.type = 'text';
        toggleApiKeyBtn.textContent = '🙈';
    } else {
        apiKeyInput.type = 'password';
        toggleApiKeyBtn.textContent = '👁️';
    }
});

// API 키 입력 시 자동 저장 및 검증
apiKeyInput.addEventListener('input', function() {
    const apiKey = this.value.trim();
    if (apiKey && apiKey.startsWith('sk-')) {
        saveApiKey(apiKey);
        showApiKeyStatus(true);
    }
});

apiKeyInput.addEventListener('blur', function() {
    const apiKey = this.value.trim();
    if (apiKey) {
        if (apiKey.startsWith('sk-')) {
            saveApiKey(apiKey);
            showApiKeyStatus(true);
        } else {
            showApiKeyStatus(false);
        }
    }
});

// 요구사항 입력 시 필수 필드 동적 처리
requirementsInput.addEventListener('input', function() {
    const hasRequirements = this.value.trim().length > 0;
    
    if (hasRequirements) {
        // 요구사항이 있으면 IP 필드 필수 해제
        mgmtIpInput.removeAttribute('required');
        mgmtMaskInput.removeAttribute('required');
        mgmtIpRequired.style.display = 'none';
        mgmtMaskRequired.style.display = 'none';
        mgmtIpInput.placeholder = '요구사항을 입력하면 자동 생성됩니다';
        mgmtMaskInput.placeholder = '요구사항을 입력하면 자동 생성됩니다';
    } else {
        // 요구사항이 없으면 IP 필드 필수
        mgmtIpInput.setAttribute('required', 'required');
        mgmtMaskInput.setAttribute('required', 'required');
        mgmtIpRequired.style.display = 'inline';
        mgmtMaskRequired.style.display = 'inline';
        mgmtIpInput.placeholder = '예: 192.168.10.254';
        mgmtMaskInput.placeholder = '예: 255.255.255.0';
    }
});

// 제조사 선택 시 필드 표시/숨김 처리
vendorSelect.addEventListener('change', function() {
    const vendor = this.value;
    currentVendor = vendor;
    
    // 모든 필드 숨기기
    vlanFields.style.display = 'none';
    interfaceFields.style.display = 'none';
    portFields.style.display = 'none';
    gatewayFields.style.display = 'none';
    
    // 기본값 초기화
    mgmtVlanInput.value = '';
    mgmtInterfaceInput.value = '';
    mgmtPortInput.value = '';
    gatewayInput.value = '192.168.10.254';
    
    if (!vendor) return;
    
    const defaults = vendorDefaults[vendor];
    if (!defaults) return;
    
    // Fortinet인 경우
    if (vendor === 'fortinet') {
        portFields.style.display = 'flex';
        gatewayFields.style.display = 'flex';
        mgmtPortInput.value = defaults.mgmt_port || 'port1';
        gatewayInput.value = defaults.gateway || '192.168.10.254';
    } else {
        // 다른 제조사인 경우
        vlanFields.style.display = 'flex';
        interfaceFields.style.display = 'flex';
        gatewayFields.style.display = 'flex';
        
        mgmtVlanInput.value = defaults.mgmt_vlan || 100;
        mgmtInterfaceInput.value = defaults.mgmt_interface || '';
        gatewayInput.value = defaults.gateway || '192.168.10.254';
        
        if (defaults.interfaceHelp) {
            interfaceHelp.textContent = defaults.interfaceHelp;
        }
    }
});

// 설정 생성 함수 (전역으로 선언)
window.generateConfig = async function(e) {
    console.log('generateConfig 함수 호출됨', new Date().toISOString());
    
    // 이벤트가 있으면 기본 동작 방지
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // DOM 요소를 함수 내에서 다시 찾기 (안전하게)
    const generateBtnEl = document.getElementById('generateBtn');
    const loadingEl = document.getElementById('loading');
    const errorMessageEl = document.getElementById('errorMessage');
    const resultAreaEl = document.getElementById('resultArea');
    const vendorSelectEl = document.getElementById('vendor');
    const apiKeyInputEl = document.getElementById('apiKey');
    const requirementsInputEl = document.getElementById('requirements');
    const hostnameInputEl = document.getElementById('hostname');
    const mgmtIpInputEl = document.getElementById('mgmt_ip');
    const mgmtMaskInputEl = document.getElementById('mgmt_mask');
    const mgmtVlanInputEl = document.getElementById('mgmt_vlan');
    const mgmtInterfaceInputEl = document.getElementById('mgmt_interface');
    const mgmtPortInputEl = document.getElementById('mgmt_port');
    const gatewayInputEl = document.getElementById('gateway');
    
    // 필수 DOM 요소 확인
    if (!generateBtnEl || !loadingEl || !errorMessageEl || !vendorSelectEl) {
        console.error('필수 DOM 요소를 찾을 수 없습니다:', {
            generateBtn: !!generateBtnEl,
            loading: !!loadingEl,
            errorMessage: !!errorMessageEl,
            vendorSelect: !!vendorSelectEl
        });
        // alert 대신 콘솔에만 표시하고 조용히 실패
        console.error('페이지가 완전히 로드되지 않았습니다. 잠시 후 다시 시도해주세요.');
        return;
    }
    
    // 에러 메시지 숨기기
    if (errorMessageEl) errorMessageEl.style.display = 'none';
    if (resultAreaEl) resultAreaEl.style.display = 'none';
    
    // 기본 검증
    if (!vendorSelectEl.value) {
        showError('제조사를 선택해주세요.');
        vendorSelectEl.focus();
        return;
    }
    
    // 로딩 표시
    if (loadingEl) {
        loadingEl.style.display = 'block';
        const loadingMessage = document.getElementById('loadingMessage');
        if (loadingMessage) {
            const requirements = requirementsInputEl ? requirementsInputEl.value.trim() : '';
            if (requirements) {
                loadingMessage.textContent = '요구사항을 분석하고 IP 정보를 생성하는 중...';
            } else {
                loadingMessage.textContent = '설정 스크립트를 생성하는 중...';
            }
        }
    }
    if (generateBtnEl) {
        generateBtnEl.disabled = true;
    }
    
    // API 키 검증
    const apiKey = apiKeyInputEl ? apiKeyInputEl.value.trim() : '';
    if (!apiKey) {
        showError('ChatGPT API 키를 입력해주세요.');
        if (apiKeyInputEl) apiKeyInputEl.focus();
        if (loadingEl) loadingEl.style.display = 'none';
        if (generateBtnEl) generateBtnEl.disabled = false;
        return;
    }
    
    // API 키 형식 간단 검증
    if (!apiKey.startsWith('sk-')) {
        showError('올바른 OpenAI API 키 형식이 아닙니다. (sk-로 시작해야 합니다)');
        if (apiKeyInputEl) apiKeyInputEl.focus();
        if (loadingEl) loadingEl.style.display = 'none';
        if (generateBtnEl) generateBtnEl.disabled = false;
        return;
    }
    
    // API 키 저장 (이미 저장되어 있어도 다시 저장)
    saveApiKey(apiKey);
    
    // 폼 데이터 수집
    const requirements = requirementsInputEl ? requirementsInputEl.value.trim() : '';
    const formData = {
        api_key: apiKey,
        vendor: vendorSelectEl.value,
        hostname: hostnameInputEl ? (hostnameInputEl.value.trim() || 'Device-01') : 'Device-01',
        requirements: requirements
    };
    
    console.log('전송할 데이터:', { ...formData, api_key: '***' }); // API 키는 숨김
    
    // 요구사항이 없는 경우에만 IP 정보 포함
    if (!requirements) {
        formData.mgmt_ip = mgmtIpInputEl ? mgmtIpInputEl.value.trim() : '';
        formData.mgmt_mask = mgmtMaskInputEl ? mgmtMaskInputEl.value.trim() : '';
        
        // 필수 필드 검증
        if (!formData.mgmt_ip || !formData.mgmt_mask) {
            showError('관리 IP 주소와 서브넷 마스크를 입력하거나 설정 요구사항을 입력해주세요.');
            if (loadingEl) loadingEl.style.display = 'none';
            if (generateBtnEl) generateBtnEl.disabled = false;
            return;
        }
    } else {
        // 요구사항이 있으면 IP 정보는 선택사항 (자동 생성됨)
        if (mgmtIpInputEl && mgmtIpInputEl.value.trim()) {
            formData.mgmt_ip = mgmtIpInputEl.value.trim();
        }
        if (mgmtMaskInputEl && mgmtMaskInputEl.value.trim()) {
            formData.mgmt_mask = mgmtMaskInputEl.value.trim();
        }
    }
    
    // 제조사별 필드 추가
    if (formData.vendor === 'fortinet') {
        formData.mgmt_port = mgmtPortInputEl ? (mgmtPortInputEl.value.trim() || 'port1') : 'port1';
    } else {
        formData.mgmt_vlan = mgmtVlanInputEl ? (mgmtVlanInputEl.value || 100) : 100;
        formData.mgmt_interface = mgmtInterfaceInputEl ? mgmtInterfaceInputEl.value.trim() : '';
        formData.gateway = gatewayInputEl ? (gatewayInputEl.value.trim() || '192.168.10.254') : '192.168.10.254';
    }
    
    try {
        // 타임아웃 설정 (60초)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000);
        
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // 응답 상태 확인
        if (!response.ok) {
            let errorMessage = `서버 오류 (${response.status})`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                errorMessage = await response.text() || errorMessage;
            }
            throw new Error(errorMessage);
        }
        
        // JSON 파싱
        let data;
        try {
            data = await response.json();
        } catch (e) {
            throw new Error('서버 응답을 파싱할 수 없습니다: ' + e.message);
        }
        
        if (data.success) {
            currentConfig = data.config;
            currentHostname = data.hostname;
            currentVendor = formData.vendor;
            
            // 결과 표시
            const configOutputEl = document.getElementById('configOutput');
            if (configOutputEl) {
                configOutputEl.textContent = data.config;
            }
            if (resultAreaEl) {
                resultAreaEl.style.display = 'block';
                // 스크롤 이동
                resultAreaEl.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            showError(data.error || '설정 생성 중 오류가 발생했습니다.');
        }
    } catch (error) {
        console.error('전체 오류:', error);
        if (error.name === 'AbortError') {
            showError('요청 시간이 초과되었습니다. (60초) ChatGPT API 응답이 지연되고 있습니다. 다시 시도해주세요.');
        } else if (error.message) {
            showError('오류 발생: ' + error.message);
        } else {
            showError('알 수 없는 오류가 발생했습니다. 브라우저 콘솔을 확인해주세요.');
        }
    } finally {
        if (loading) {
            loading.style.display = 'none';
        }
        if (generateBtn) {
            generateBtn.disabled = false;
        }
        const loadingMsg = document.getElementById('loadingMessage');
        if (loadingMsg) {
            loadingMsg.textContent = '설정 스크립트를 생성하는 중...';
        }
    }
}; // window.generateConfig 함수 끝

// 복사 버튼
copyBtn.addEventListener('click', function() {
    if (!currentConfig) return;
    
    navigator.clipboard.writeText(currentConfig).then(function() {
        copyBtn.textContent = '복사됨!';
        setTimeout(function() {
            copyBtn.textContent = '복사';
        }, 2000);
    }).catch(function(err) {
        alert('복사에 실패했습니다: ' + err);
    });
});

// 다운로드 버튼
downloadBtn.addEventListener('click', async function() {
    if (!currentConfig || !currentHostname || !currentVendor) return;
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                config: currentConfig,
                hostname: currentHostname,
                vendor: currentVendor
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentHostname}_${currentVendor}_config.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const data = await response.json();
            showError(data.error || '다운로드 중 오류가 발생했습니다.');
        }
    } catch (error) {
        showError('다운로드 중 오류가 발생했습니다: ' + error.message);
    }
});

// 이벤트 리스너는 DOMContentLoaded 내부에서 등록됨

// 초기화 버튼
resetBtn.addEventListener('click', function() {
    configForm.reset();
    resultArea.style.display = 'none';
    errorMessage.style.display = 'none';
    currentConfig = null;
    currentVendor = null;
    currentHostname = null;
    
    // 필드 숨기기
    vlanFields.style.display = 'none';
    interfaceFields.style.display = 'none';
    portFields.style.display = 'none';
    gatewayFields.style.display = 'none';
    
    // 저장된 API 키 복원
    const savedApiKey = loadApiKey();
    if (savedApiKey) {
        apiKeyInput.value = savedApiKey;
        showApiKeyStatus(true);
    } else {
        showApiKeyStatus(false);
    }
});

// 에러 메시지 표시
function showError(message) {
    errorMessage.textContent = '오류: ' + message;
    errorMessage.style.display = 'block';
    errorMessage.scrollIntoView({ behavior: 'smooth' });
}

// IP 주소 유효성 검사 (간단한 형식 체크)
mgmtIpInput.addEventListener('blur', function() {
    const ip = this.value.trim();
    if (ip && !/^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/.test(ip)) {
        this.setCustomValidity('올바른 IP 주소 형식을 입력하세요 (예: 192.168.1.1)');
    } else {
        this.setCustomValidity('');
    }
});

