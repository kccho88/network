#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
장비 설정 스크립트 템플릿 생성기 - 웹 버전
Flask를 사용한 웹 인터페이스
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

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


def generate_config(vendor, form_data):
    """설정 파일을 생성합니다."""
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
        data = request.get_json()
        
        vendor = data.get('vendor', '').lower()
        if vendor not in SUPPORTED_VENDORS:
            return jsonify({
                'success': False,
                'error': f'지원하지 않는 제조사입니다: {vendor}'
            }), 400
        
        # 필수 필드 검증
        required_fields = ['hostname', 'mgmt_ip', 'mgmt_mask']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'필수 필드가 누락되었습니다: {field}'
                }), 400
        
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
        
        # 설정 생성
        config_content, error = generate_config(vendor, data)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 500
        
        return jsonify({
            'success': True,
            'config': config_content,
            'vendor': SUPPORTED_VENDORS[vendor],
            'hostname': data.get('hostname')
        })
        
    except Exception as e:
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

