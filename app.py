#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
장비 설정 스크립트 템플릿 생성기 - 웹 버전
Flask를 사용한 웹 인터페이스
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from openai import OpenAI

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 지원하는 제조사 목록
SUPPORTED_VENDORS = {
    'cisco': 'Cisco',
    'arista': 'Arista',
    'alcatel': 'Alcatel-Lucent',
    'hp': 'HP (HPE)',
    'juniper': 'Juniper',
    'fortinet': 'Fortinet'
}

# 제조사별 기본 설정값
DEFAULT_CONFIGS = {
    'cisco': {
        'mgmt_vlan': 100,
        'mgmt_interface': 'Gi1/0/1',
        'gateway': '192.168.10.254'
    },
    'arista': {
        'mgmt_vlan': 100,
        'mgmt_interface': 'Management1',
        'gateway': '192.168.10.254'
    },
    'alcatel': {
        'mgmt_vlan': 100,
        'mgmt_interface': '1/1/1',
        'gateway': '192.168.10.254'
    },
    'hp': {
        'mgmt_vlan': 100,
        'mgmt_interface': '1',
        'gateway': '192.168.10.254'
    },
    'juniper': {
        'mgmt_vlan': 100,
        'mgmt_interface': 'ge-0/0/0',
        'gateway': '192.168.10.254'
    },
    'fortinet': {
        'mgmt_port': 'port1',
        'gateway': '192.168.10.254'
    }
}


def convert_mask_to_cidr(mask):
    """서브넷 마스크를 CIDR 표기법으로 변환합니다."""
    if '/' in mask:
        return mask.split('/')[1]
    
    octets = mask.split('.')
    if len(octets) != 4:
        return '24'  # 기본값
    
    try:
        binary_str = ''.join([format(int(octet), '08b') for octet in octets])
        cidr = str(binary_str.count('1'))
        return cidr
    except ValueError:
        return '24'  # 기본값


def load_template(vendor, template_dir='config_templates'):
    """Jinja2 템플릿을 로드합니다."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    template_filename = f"{vendor}_base.j2"
    
    try:
        template = env.get_template(template_filename)
        return template
    except TemplateNotFound:
        raise ValueError(f"템플릿 파일 '{template_filename}'을 찾을 수 없습니다.")
    except Exception as e:
        raise ValueError(f"템플릿 로드 중 문제가 발생했습니다: {e}")


def prepare_template_vars(vendor, form_data):
    """템플릿에 전달할 변수 딕셔너리를 준비합니다."""
    defaults = DEFAULT_CONFIGS.get(vendor, {})
    
    template_vars = {
        'hostname': form_data.get('hostname', ''),
        'mgmt_ip': form_data.get('mgmt_ip', ''),
        'mgmt_mask': form_data.get('mgmt_mask', '255.255.255.0'),
    }
    
    # CIDR 변환
    mask = template_vars['mgmt_mask']
    template_vars['mgmt_mask_cidr'] = convert_mask_to_cidr(mask)
    
    # 제조사별 특정 변수 설정
    if vendor in ['cisco', 'arista', 'alcatel', 'hp', 'juniper']:
        template_vars['mgmt_vlan'] = int(form_data.get('mgmt_vlan', defaults.get('mgmt_vlan', 100)))
        template_vars['mgmt_interface'] = form_data.get('mgmt_interface', defaults.get('mgmt_interface', ''))
        template_vars['gateway'] = form_data.get('gateway', defaults.get('gateway', '192.168.10.254'))
    
    if vendor == 'fortinet':
        template_vars['mgmt_port'] = form_data.get('mgmt_port', defaults.get('mgmt_port', 'port1'))
    
    return template_vars


def analyze_requirements_and_generate_ips(vendor, requirements, api_key):
    """요구사항을 분석하여 IP 정보를 자동 생성합니다."""
    try:
        client = OpenAI(api_key=api_key)
        vendor_name = SUPPORTED_VENDORS.get(vendor, vendor)
        
        analysis_prompt = f"""당신은 {vendor_name} 네트워크 장비 설정 전문가입니다. 
사용자의 요구사항을 분석하여 필요한 네트워크 정보(IP 주소, 서브넷, VLAN, 인터페이스 등)를 자동으로 생성해주세요.

사용자 요구사항:
{requirements}

다음 형식으로 JSON을 반환해주세요 (설명 없이 JSON만):
{{
    "hostname": "생성된 호스트명",
    "mgmt_ip": "관리 IP 주소",
    "mgmt_mask": "서브넷 마스크 (예: 255.255.255.0)",
    "mgmt_vlan": 관리 VLAN ID (숫자),
    "mgmt_interface": "관리 인터페이스명",
    "gateway": "기본 게이트웨이 IP",
    "additional_configs": [
        {{
            "type": "vlan",
            "vlan_id": VLAN ID,
            "name": "VLAN 이름",
            "ip": "IP 주소",
            "subnet": "서브넷 마스크"
        }},
        {{
            "type": "interface",
            "name": "인터페이스명",
            "ip": "IP 주소",
            "subnet": "서브넷 마스크",
            "description": "설명"
        }},
        {{
            "type": "routing",
            "protocol": "프로토콜명 (OSPF, EIGRP 등)",
            "network": "네트워크 주소",
            "area": "OSPF Area (해당되는 경우)"
        }}
    ]
}}

요구사항에서 명시되지 않은 정보는 적절한 기본값을 생성하세요.
IP 주소는 사설 IP 대역(10.x.x.x, 192.168.x.x, 172.16-31.x.x)을 사용하세요."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"당신은 {vendor_name} 네트워크 장비 설정 전문가입니다. 사용자 요구사항을 분석하여 필요한 네트워크 정보를 JSON 형식으로 생성합니다."
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        if not response or not response.choices or len(response.choices) == 0:
            return None, "ChatGPT API 응답이 비어있습니다."
        
        response_content = response.choices[0].message.content.strip()
        if not response_content:
            return None, "ChatGPT API 응답 내용이 비어있습니다."
        
        try:
            ip_info = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            print(f"응답 내용: {response_content[:500]}")  # 처음 500자만 출력
            return None, f"IP 정보 파싱 오류: {str(e)}. 응답 형식이 올바르지 않습니다."
        
        return ip_info, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"요구사항 분석 오류: {error_msg}")
        import traceback
        traceback.print_exc()
        return None, f"요구사항 분석 오류: {error_msg}"


def generate_config_with_chatgpt(vendor, form_data, api_key):
    """ChatGPT API를 사용하여 설정 파일을 생성합니다."""
    try:
        client = OpenAI(api_key=api_key)
        
        vendor_name = SUPPORTED_VENDORS.get(vendor, vendor)
        requirements = form_data.get('requirements', '').strip()
        
        # 요구사항이 있는 경우 IP 정보 자동 생성
        if requirements:
            ip_info, error = analyze_requirements_and_generate_ips(vendor, requirements, api_key)
            if error:
                return None, error
            
            # 생성된 IP 정보로 form_data 업데이트
            form_data['hostname'] = ip_info.get('hostname', form_data.get('hostname', ''))
            form_data['mgmt_ip'] = ip_info.get('mgmt_ip', form_data.get('mgmt_ip', ''))
            form_data['mgmt_mask'] = ip_info.get('mgmt_mask', form_data.get('mgmt_mask', '255.255.255.0'))
            form_data['mgmt_vlan'] = ip_info.get('mgmt_vlan', form_data.get('mgmt_vlan', 100))
            form_data['mgmt_interface'] = ip_info.get('mgmt_interface', form_data.get('mgmt_interface', ''))
            form_data['gateway'] = ip_info.get('gateway', form_data.get('gateway', '192.168.10.254'))
            form_data['_generated_ip_info'] = ip_info  # 추가 정보 저장
        
        hostname = form_data.get('hostname', '')
        mgmt_ip = form_data.get('mgmt_ip', '')
        mgmt_mask = form_data.get('mgmt_mask', '255.255.255.0')
        
        # 제조사별 프롬프트 구성
        prompt_parts = [
            f"다음 정보를 바탕으로 {vendor_name} 네트워크 장비의 완전한 설정 스크립트를 생성해주세요.",
            f"\n기본 장비 정보:",
            f"- 호스트명: {hostname}",
            f"- 관리 IP 주소: {mgmt_ip}",
            f"- 서브넷 마스크: {mgmt_mask}",
        ]
        
        # 제조사별 추가 정보
        if vendor in ['cisco', 'arista', 'alcatel', 'hp', 'juniper']:
            mgmt_vlan = form_data.get('mgmt_vlan', DEFAULT_CONFIGS[vendor].get('mgmt_vlan', 100))
            mgmt_interface = form_data.get('mgmt_interface', DEFAULT_CONFIGS[vendor].get('mgmt_interface', ''))
            gateway = form_data.get('gateway', DEFAULT_CONFIGS[vendor].get('gateway', '192.168.10.254'))
            
            prompt_parts.extend([
                f"- 관리 VLAN ID: {mgmt_vlan}",
                f"- 관리 인터페이스: {mgmt_interface}",
                f"- 기본 게이트웨이: {gateway}",
            ])
        elif vendor == 'fortinet':
            mgmt_port = form_data.get('mgmt_port', DEFAULT_CONFIGS[vendor].get('mgmt_port', 'port1'))
            prompt_parts.append(f"- 관리 포트: {mgmt_port}")
        
        # 요구사항이 있는 경우 추가 정보 포함
        if requirements:
            prompt_parts.append(f"\n사용자 요구사항:\n{requirements}")
            
            if '_generated_ip_info' in form_data:
                ip_info = form_data['_generated_ip_info']
                if ip_info.get('additional_configs'):
                    prompt_parts.append("\n생성된 네트워크 구성:")
                    for config in ip_info['additional_configs']:
                        if config['type'] == 'vlan':
                            prompt_parts.append(f"- VLAN {config.get('vlan_id')} ({config.get('name', '')}): {config.get('ip')}/{config.get('subnet', '255.255.255.0')}")
                        elif config['type'] == 'interface':
                            prompt_parts.append(f"- 인터페이스 {config.get('name')}: {config.get('ip')}/{config.get('subnet', '255.255.255.0')} - {config.get('description', '')}")
                        elif config['type'] == 'routing':
                            prompt_parts.append(f"- 라우팅 프로토콜: {config.get('protocol')} - 네트워크: {config.get('network')}")
        
        prompt_parts.extend([
            f"\n생성 요구사항:",
            f"1. {vendor_name} 장비의 표준 CLI 명령어 형식을 정확히 사용하세요.",
            f"2. 호스트명, 관리 IP, 서브넷 마스크 설정을 포함하세요.",
            f"3. 관리 인터페이스/VLAN 설정을 포함하세요.",
            f"4. 기본 게이트웨이 설정을 포함하세요 (해당되는 경우).",
            f"5. 요구사항에 명시된 모든 VLAN, 인터페이스, 라우팅 설정을 포함하세요.",
            f"6. 주석은 '!' 또는 '#' 기호를 사용하세요.",
            f"7. 실제 장비에 적용 가능한 정확한 명령어만 생성하세요.",
            f"8. 불필요한 설명이나 마크다운 형식 없이 순수 CLI 명령어만 출력하세요.",
            f"9. 모든 인터페이스를 활성화(no shutdown)하세요.",
            f"10. 완전하고 실행 가능한 전체 설정 스크립트를 생성하세요.",
            f"\n설정 스크립트:",
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # ChatGPT API 호출
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"당신은 {vendor_name} 네트워크 장비 설정 전문가입니다. 사용자가 제공한 정보와 요구사항을 바탕으로 완전하고 정확한 CLI 설정 스크립트를 생성합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            if not response or not response.choices or len(response.choices) == 0:
                return None, "ChatGPT API 응답이 비어있습니다."
            
            config_content = response.choices[0].message.content.strip()
            
            if not config_content:
                return None, "ChatGPT API 응답 내용이 비어있습니다."
            
            # 마크다운 코드 블록 제거 (있는 경우)
            if config_content.startswith("```"):
                lines = config_content.split("\n")
                # 첫 번째와 마지막 코드 블록 라인 제거
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                config_content = "\n".join(lines)
            
            return config_content, None
            
        except Exception as api_error:
            error_msg = str(api_error)
            print(f"ChatGPT API 호출 오류: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # API 키 관련 오류인지 확인
            if "api" in error_msg.lower() or "key" in error_msg.lower() or "401" in error_msg or "403" in error_msg:
                return None, f"ChatGPT API 키 오류: {error_msg}. API 키를 확인해주세요."
            elif "rate limit" in error_msg.lower() or "429" in error_msg:
                return None, f"ChatGPT API 사용량 초과: {error_msg}. 잠시 후 다시 시도해주세요."
            else:
                return None, f"ChatGPT API 오류: {error_msg}"
        
    except Exception as e:
        error_msg = str(e)
        print(f"설정 생성 함수 오류: {error_msg}")
        import traceback
        traceback.print_exc()
        return None, f"설정 생성 오류: {error_msg}"


def generate_config(vendor, form_data):
    """템플릿 기반 설정 파일을 생성합니다 (백업용)."""
    try:
        # 템플릿 로드
        template = load_template(vendor)
        
        # 템플릿 변수 준비
        template_vars = prepare_template_vars(vendor, form_data)
        
        # 템플릿 렌더링
        config_content = template.render(**template_vars)
        
        return config_content, None
    except Exception as e:
        return None, str(e)


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html', vendors=SUPPORTED_VENDORS)


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """설정 파일 생성 API"""
    try:
        # JSON 파싱
        try:
            data = request.get_json()
            if data is None:
                return jsonify({
                    'success': False,
                    'error': '요청 데이터가 없습니다.'
                }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'요청 데이터 파싱 오류: {str(e)}'
            }), 400
        
        # API 키 검증
        api_key = data.get('api_key', '').strip()
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'ChatGPT API 키가 필요합니다.'
            }), 400
        
        vendor = data.get('vendor', '').lower()
        if vendor not in SUPPORTED_VENDORS:
            return jsonify({
                'success': False,
                'error': f'지원하지 않는 제조사입니다: {vendor}'
            }), 400
        
        # 요구사항이 없는 경우에만 필수 필드 검증
        requirements = data.get('requirements', '').strip()
        if not requirements:
            required_fields = ['hostname', 'mgmt_ip', 'mgmt_mask']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'필수 필드가 누락되었습니다: {field} (또는 설정 요구사항을 입력하세요)'
                    }), 400
        else:
            # 요구사항이 있는 경우 호스트명만 필수
            if not data.get('hostname'):
                data['hostname'] = 'Device-01'  # 기본값 설정
        
        # 제조사별 필수 필드 검증
        if vendor in ['cisco', 'arista', 'alcatel', 'hp', 'juniper']:
            if not data.get('mgmt_vlan') and not DEFAULT_CONFIGS[vendor].get('mgmt_vlan'):
                return jsonify({
                    'success': False,
                    'error': f'{SUPPORTED_VENDORS[vendor]} 장비는 관리 VLAN이 필요합니다.'
                }), 400
        
        if vendor == 'fortinet':
            if not data.get('mgmt_port') and not DEFAULT_CONFIGS[vendor].get('mgmt_port'):
                return jsonify({
                    'success': False,
                    'error': 'Fortinet 장비는 관리 포트가 필요합니다.'
                }), 400
        
        # ChatGPT API를 사용하여 설정 생성
        try:
            config_content, error = generate_config_with_chatgpt(vendor, data, api_key)
            
            if error:
                print(f"ChatGPT API 오류: {error}")  # 디버깅용
                return jsonify({
                    'success': False,
                    'error': error
                }), 500
            
            if not config_content:
                return jsonify({
                    'success': False,
                    'error': '설정 스크립트 생성에 실패했습니다. 응답이 비어있습니다.'
                }), 500
            
            return jsonify({
                'success': True,
                'config': config_content,
                'vendor': SUPPORTED_VENDORS[vendor],
                'hostname': data.get('hostname')
            })
        except Exception as e:
            print(f"설정 생성 중 오류: {str(e)}")  # 디버깅용
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'설정 생성 중 오류가 발생했습니다: {str(e)}'
            }), 500
        
    except Exception as e:
        print(f"API 처리 중 오류: {str(e)}")  # 디버깅용
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'서버 오류: {str(e)}'
        }), 500


@app.route('/api/download', methods=['POST'])
def api_download():
    """설정 파일 다운로드"""
    try:
        data = request.get_json()
        
        config_content = data.get('config', '')
        hostname = data.get('hostname', 'device')
        vendor = data.get('vendor', 'unknown')
        
        if not config_content:
            return jsonify({
                'success': False,
                'error': '설정 내용이 없습니다.'
            }), 400
        
        # 임시 파일 생성
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{hostname}_{vendor}_config.txt"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return send_file(
            str(filepath),
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'파일 생성 오류: {str(e)}'
        }), 500


@app.route('/api/vendor-config', methods=['GET'])
def api_vendor_config():
    """제조사별 기본 설정값 반환"""
    vendor = request.args.get('vendor', '').lower()
    
    if vendor not in SUPPORTED_VENDORS:
        return jsonify({
            'success': False,
            'error': '지원하지 않는 제조사입니다.'
        }), 400
    
    defaults = DEFAULT_CONFIGS.get(vendor, {})
    
    return jsonify({
        'success': True,
        'vendor': vendor,
        'config': defaults
    })


if __name__ == '__main__':
    # templates 폴더 생성
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    Path('output').mkdir(exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

