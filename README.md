# 🛠️ 장비 설정 스크립트 템플릿 생성기

Python과 Jinja2를 활용하여 네트워크 장비 설정 스크립트를 자동 생성하는 도구입니다. **CLI 버전**과 **웹 버전**을 모두 지원합니다.

## 📋 목차

- [기능](#기능)
- [요구사항](#요구사항)
- [설치 방법](#설치-방법)
- [웹 버전 사용법](#웹-버전-사용법)
- [CLI 버전 사용법](#cli-버전-사용법)
- [실행 예시](#실행-예시)
- [프로젝트 구조](#프로젝트-구조)

## ✨ 기능

- **다중 장비 지원**: Cisco, Arista, Alcatel-Lucent, HP, Juniper, Fortinet 장비 설정 스크립트 생성
- **웹 인터페이스**: 브라우저에서 간편하게 사용 가능한 웹 UI 제공
- **명령줄 인터페이스**: CLI를 통한 설정 파일 생성
- **템플릿 기반**: Jinja2 템플릿을 사용한 유연한 설정 생성
- **자동 파일 저장**: 생성된 설정을 `output` 폴더에 자동 저장
- **다운로드 기능**: 웹에서 생성된 설정 파일 다운로드 지원

## 📦 요구사항

- Python 3.7 이상
- Jinja2 3.1.2 이상
- Flask 3.0.0 이상 (웹 버전용)
- Click 8.1.7 이상 (CLI 버전용)

## 🚀 설치 방법

### 1. 가상 환경 설정 (권장)

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows CMD
python -m venv venv
venv\Scripts\activate.bat

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. 필요한 라이브러리 설치

```bash
pip install -r requirements.txt
```

또는 직접 설치:

```bash
pip install jinja2>=3.1.2 click>=8.1.7
```

## 🌐 웹 버전 사용법

### 1. 웹 서버 실행

```bash
python app.py
```

웹 서버가 시작되면 브라우저에서 `http://localhost:5000` 또는 `http://127.0.0.1:5000`으로 접속하세요.

### 2. 웹 인터페이스 사용

1. **제조사 선택**: 드롭다운에서 원하는 제조사를 선택합니다 (Cisco, Arista, Alcatel-Lucent, HP, Juniper, Fortinet)
2. **제품명 입력**: 장비의 호스트 이름을 입력합니다 (예: SW-HQ-01)
3. **네트워크 정보 입력**: 관리 IP 주소와 서브넷 마스크를 입력합니다
4. **추가 설정**: 제조사에 따라 필요한 추가 정보를 입력합니다
   - Cisco/Arista/Alcatel/HP/Juniper: VLAN ID, 관리 인터페이스
   - Fortinet: 관리 포트
5. **생성 버튼 클릭**: 설정 스크립트가 자동으로 생성됩니다
6. **복사 또는 다운로드**: 생성된 설정을 복사하거나 파일로 다운로드할 수 있습니다

### 웹 버전의 장점

- ✅ 직관적인 GUI 인터페이스
- ✅ 제조사별 필드 자동 표시/숨김
- ✅ 실시간 설정 미리보기
- ✅ 원클릭 복사 및 다운로드
- ✅ 반응형 디자인 (모바일 지원)

## 💻 CLI 버전 사용법

### 기본 명령 형식

```bash
python main.py <device_type> --hostname <호스트명> --ip <IP주소> --mask <서브넷마스크> [추가옵션]
```

### 필수 옵션

- `device_type`: 장비 타입 (`cisco`, `juniper`, `fortinet`)
- `--hostname`: 장비 호스트 이름
- `--ip` 또는 `--mgmt-ip`: 관리 IP 주소
- `--mask` 또는 `--mgmt-mask`: 서브넷 마스크 (예: `255.255.255.0`)

### 장비별 추가 옵션

#### Cisco
- `--vlan` 또는 `--mgmt-vlan`: 관리 VLAN ID (필수)
- `--interface` 또는 `--mgmt-interface`: 관리 인터페이스 (필수, 예: `Gi1/0/1`)

#### Arista
- `--vlan` 또는 `--mgmt-vlan`: 관리 VLAN ID (필수)
- `--interface` 또는 `--mgmt-interface`: 관리 인터페이스 (필수, 예: `Management1`)

#### Alcatel-Lucent
- `--vlan` 또는 `--mgmt-vlan`: 관리 VLAN ID (필수)
- `--interface` 또는 `--mgmt-interface`: 관리 인터페이스 (필수, 예: `1/1/1`)

#### HP (HPE)
- `--vlan` 또는 `--mgmt-vlan`: 관리 VLAN ID (필수)
- `--interface` 또는 `--mgmt-interface`: 관리 인터페이스 (필수, 예: `1`)

#### Juniper
- `--vlan` 또는 `--mgmt-vlan`: 관리 VLAN ID (필수)
- `--interface` 또는 `--mgmt-interface`: 관리 인터페이스 (필수, 예: `ge-0/0/0`)
- `--gateway`: 기본 게이트웨이 (선택, 기본값: `192.168.10.254`)

#### Fortinet
- `--port` 또는 `--mgmt-port`: 관리 포트 이름 (필수, 예: `port1`)

## 🎯 실행 예시

### 예시 1: Cisco 장비 설정 생성

```bash
python main.py cisco --hostname SW-HQ-01 --ip 192.168.10.254 --mask 255.255.255.0 --vlan 100 --interface Gi1/0/1
```

**생성된 파일**: `output/SW-HQ-01_cisco_config.txt`

**생성된 설정 내용**:
```
hostname SW-HQ-01
!
vlan 100
 name MANAGEMENT
!
interface Gi1/0/1
 no switchport
 ip address 192.168.10.254 255.255.255.0
 no shutdown
!
interface Vlan100
 ip address 192.168.10.254 255.255.255.0
 no shutdown
!
```

### 예시 2: Juniper 장비 설정 생성

```bash
python main.py juniper --hostname JNPR-01 --ip 192.168.10.1 --mask 255.255.255.0 --vlan 100 --interface ge-0/0/0 --gateway 192.168.10.254
```

**생성된 파일**: `output/JNPR-01_juniper_config.txt`

### 예시 3: Fortinet 장비 설정 생성

```bash
python main.py fortinet --hostname FGT-01 --ip 192.168.10.1 --mask 255.255.255.0 --port port1
```

**생성된 파일**: `output/FGT-01_fortinet_config.txt`

**생성된 설정 내용**:
```
config system global
    set hostname FGT-01
end
!
config system interface
    edit "port1"
        set ip 192.168.10.1 255.255.255.0
        set allowaccess ping https ssh snmp
        set type physical
    next
end
!
config system dns
    set primary 8.8.8.8
    set secondary 8.8.4.4
end
!
```

## 📁 프로젝트 구조

```
network-cursor/
│
├── app.py                       # Flask 웹 애플리케이션 (웹 버전)
├── main.py                      # CLI 메인 스크립트
├── requirements.txt             # Python 패키지 의존성
├── README.md                    # 프로젝트 문서
├── .gitignore                   # Git 무시 파일 목록
│
├── templates/                   # Flask HTML 템플릿
│   └── index.html              # 웹 UI 메인 페이지
│
├── static/                      # 정적 파일 (CSS, JS)
│   ├── style.css               # 스타일시트
│   └── script.js               # 클라이언트 사이드 JavaScript
│
├── config_templates/           # Jinja2 템플릿 폴더
│   ├── cisco_base.j2           # Cisco 템플릿
│   ├── arista_base.j2          # Arista 템플릿
│   ├── alcatel_base.j2         # Alcatel-Lucent 템플릿
│   ├── hp_base.j2              # HP 템플릿
│   ├── juniper_base.j2         # Juniper 템플릿
│   └── fortinet_base.j2        # Fortinet 템플릿
│
└── output/                      # 생성된 설정 파일 저장 폴더
    └── [hostname]_[device_type]_config.txt
```

## 🔧 고급 사용법

### 도움말 보기

```bash
python main.py --help
python main.py cisco --help
```

### 템플릿 커스터마이징

`config_templates/` 폴더의 `.j2` 파일을 수정하여 원하는 설정 형식으로 변경할 수 있습니다.

템플릿에서 사용 가능한 변수:
- `hostname`: 호스트 이름
- `mgmt_ip`: 관리 IP 주소
- `mgmt_mask`: 서브넷 마스크
- `mgmt_vlan`: 관리 VLAN ID (Cisco, Juniper)
- `mgmt_interface`: 관리 인터페이스 (Cisco, Juniper)
- `mgmt_port`: 관리 포트 (Fortinet)
- `gateway`: 기본 게이트웨이 (Juniper)
- `mgmt_mask_cidr`: CIDR 형식 서브넷 마스크 (Juniper)

## 🐛 문제 해결

### 템플릿 파일을 찾을 수 없음

- `config_templates` 폴더가 프로젝트 루트에 있는지 확인하세요.
- 템플릿 파일명이 `{device_type}_base.j2` 형식인지 확인하세요.

### 필수 옵션이 누락됨

- 각 장비 타입에 필요한 옵션을 확인하세요:
  - Cisco/Juniper: `--vlan`, `--interface` 필수
  - Fortinet: `--port` 필수

## 📝 라이선스

이 프로젝트는 자유롭게 사용 및 수정할 수 있습니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.


