#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
장비 설정 스크립트 템플릿 생성기
Python과 Jinja2를 사용하여 네트워크 장비 설정 스크립트를 자동 생성합니다.
"""

import argparse
import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python 3.6 이하 버전 호환성
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(
        description='네트워크 장비 설정 스크립트 템플릿 생성기',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py cisco --hostname SW-HQ-01 --ip 192.168.10.254 --mask 255.255.255.0 --vlan 100 --interface Gi1/0/1
  python main.py juniper --hostname JNPR-01 --ip 192.168.10.1 --mask 255.255.255.0 --vlan 100 --interface ge-0/0/0 --gateway 192.168.10.254
  python main.py fortinet --hostname FGT-01 --ip 192.168.10.1 --mask 255.255.255.0 --port port1
        """
    )
    
    parser.add_argument(
        'device_type',
        choices=['cisco', 'juniper', 'fortinet'],
        help='장비 타입 (cisco, juniper, fortinet 중 선택)'
    )
    
    parser.add_argument(
        '--hostname',
        required=True,
        help='장비 호스트 이름'
    )
    
    parser.add_argument(
        '--ip',
        '--mgmt-ip',
        dest='mgmt_ip',
        required=True,
        help='관리 IP 주소'
    )
    
    parser.add_argument(
        '--mask',
        '--mgmt-mask',
        dest='mgmt_mask',
        required=True,
        help='서브넷 마스크 (예: 255.255.255.0 또는 CIDR 형식)'
    )
    
    # Cisco 및 Juniper용 옵션
    parser.add_argument(
        '--vlan',
        '--mgmt-vlan',
        dest='mgmt_vlan',
        type=int,
        help='관리 VLAN ID (Cisco, Juniper용)'
    )
    
    parser.add_argument(
        '--interface',
        '--mgmt-interface',
        dest='mgmt_interface',
        help='관리 인터페이스 (Cisco, Juniper용, 예: Gi1/0/1, ge-0/0/0)'
    )
    
    # Juniper용 추가 옵션
    parser.add_argument(
        '--gateway',
        default='192.168.10.254',
        help='기본 게이트웨이 (Juniper용, 기본값: 192.168.10.254)'
    )
    
    # Fortinet용 옵션
    parser.add_argument(
        '--port',
        '--mgmt-port',
        dest='mgmt_port',
        help='관리 포트 이름 (Fortinet용, 예: port1)'
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """입력 인수의 유효성을 검증합니다."""
    errors = []
    
    if args.device_type in ['cisco', 'juniper']:
        if not args.mgmt_vlan:
            errors.append(f"{args.device_type} 장비는 --vlan 옵션이 필요합니다.")
        if not args.mgmt_interface:
            errors.append(f"{args.device_type} 장비는 --interface 옵션이 필요합니다.")
    
    if args.device_type == 'fortinet':
        if not args.mgmt_port:
            errors.append("Fortinet 장비는 --port 옵션이 필요합니다.")
    
    if errors:
        print("오류:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def convert_mask_to_cidr(mask):
    """서브넷 마스크를 CIDR 표기법으로 변환합니다."""
    if '/' in mask:
        # 이미 CIDR 형식인 경우
        return mask.split('/')[1]
    
    # 점으로 구분된 형식 (255.255.255.0)을 CIDR로 변환
    octets = mask.split('.')
    if len(octets) != 4:
        return None
    
    try:
        binary_str = ''.join([format(int(octet), '08b') for octet in octets])
        cidr = str(binary_str.count('1'))
        return cidr
    except ValueError:
        return None


def prepare_template_vars(args):
    """템플릿에 전달할 변수 딕셔너리를 준비합니다."""
    template_vars = {
        'hostname': args.hostname,
        'mgmt_ip': args.mgmt_ip,
        'mgmt_mask': args.mgmt_mask,
    }
    
    if args.device_type in ['cisco', 'juniper']:
        template_vars['mgmt_vlan'] = args.mgmt_vlan
        template_vars['mgmt_interface'] = args.mgmt_interface
    
    if args.device_type == 'juniper':
        template_vars['gateway'] = args.gateway
        cidr = convert_mask_to_cidr(args.mgmt_mask)
        if cidr:
            template_vars['mgmt_mask_cidr'] = cidr
        else:
            print("경고: 서브넷 마스크를 CIDR 형식으로 변환할 수 없습니다. 기본값 24를 사용합니다.", file=sys.stderr)
            template_vars['mgmt_mask_cidr'] = '24'
    
    if args.device_type == 'fortinet':
        template_vars['mgmt_port'] = args.mgmt_port
    
    return template_vars


def load_template(device_type, template_dir='config_templates'):
    """Jinja2 템플릿을 로드합니다."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    template_filename = f"{device_type}_base.j2"
    
    try:
        template = env.get_template(template_filename)
        return template
    except TemplateNotFound:
        print(f"오류: 템플릿 파일 '{template_filename}'을 찾을 수 없습니다.", file=sys.stderr)
        print(f"      '{template_dir}' 폴더를 확인해주세요.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"오류: 템플릿 로드 중 문제가 발생했습니다: {e}", file=sys.stderr)
        sys.exit(1)


def save_output(config_content, hostname, device_type, output_dir='output'):
    """생성된 설정 내용을 파일로 저장합니다."""
    # output 디렉토리 생성
    Path(output_dir).mkdir(exist_ok=True)
    
    # 파일명 생성: [hostname]_[device_type]_config.txt
    filename = f"{hostname}_{device_type}_config.txt"
    filepath = Path(output_dir) / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(config_content)
        return filepath
    except Exception as e:
        print(f"오류: 파일 저장 중 문제가 발생했습니다: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """메인 함수"""
    # 명령줄 인수 파싱
    args = parse_arguments()
    
    # 인수 유효성 검증
    validate_arguments(args)
    
    # 템플릿 변수 준비
    template_vars = prepare_template_vars(args)
    
    # 템플릿 로드
    template = load_template(args.device_type)
    
    # 템플릿 렌더링
    try:
        config_content = template.render(**template_vars)
    except Exception as e:
        print(f"오류: 템플릿 렌더링 중 문제가 발생했습니다: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 결과 저장
    output_path = save_output(config_content, args.hostname, args.device_type)
    
    # 성공 메시지 출력
    print(f"[SUCCESS] 설정 파일이 성공적으로 생성되었습니다: {output_path}")
    print(f"\n생성된 설정 내용:")
    print("-" * 60)
    print(config_content)
    print("-" * 60)


if __name__ == '__main__':
    main()


