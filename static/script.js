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
const vendorSelect = document.getElementById('vendor');
const hostnameInput = document.getElementById('hostname');
const mgmtIpInput = document.getElementById('mgmt_ip');
const mgmtMaskInput = document.getElementById('mgmt_mask');
const mgmtVlanInput = document.getElementById('mgmt_vlan');
const mgmtInterfaceInput = document.getElementById('mgmt_interface');
const mgmtPortInput = document.getElementById('mgmt_port');
const gatewayInput = document.getElementById('gateway');
const interfaceHelp = document.getElementById('interfaceHelp');

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

// 폼 제출 처리
configForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // 에러 메시지 숨기기
    errorMessage.style.display = 'none';
    resultArea.style.display = 'none';
    
    // 로딩 표시
    loading.style.display = 'block';
    generateBtn.disabled = true;
    
    // 폼 데이터 수집
    const formData = {
        vendor: vendorSelect.value,
        hostname: hostnameInput.value.trim(),
        mgmt_ip: mgmtIpInput.value.trim(),
        mgmt_mask: mgmtMaskInput.value.trim()
    };
    
    // 제조사별 필드 추가
    if (formData.vendor === 'fortinet') {
        formData.mgmt_port = mgmtPortInput.value.trim() || 'port1';
    } else {
        formData.mgmt_vlan = mgmtVlanInput.value || 100;
        formData.mgmt_interface = mgmtInterfaceInput.value.trim();
        formData.gateway = gatewayInput.value.trim() || '192.168.10.254';
    }
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentConfig = data.config;
            currentHostname = data.hostname;
            currentVendor = formData.vendor;
            
            // 결과 표시
            configOutput.textContent = data.config;
            resultArea.style.display = 'block';
            
            // 스크롤 이동
            resultArea.scrollIntoView({ behavior: 'smooth' });
        } else {
            showError(data.error || '설정 생성 중 오류가 발생했습니다.');
        }
    } catch (error) {
        showError('서버와 통신하는 중 오류가 발생했습니다: ' + error.message);
    } finally {
        loading.style.display = 'none';
        generateBtn.disabled = false;
    }
});

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

