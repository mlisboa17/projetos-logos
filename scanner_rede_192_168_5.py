#!/usr/bin/env python3
"""
Scanner específico para a rede 192.168.5.x
Busca por câmeras Intelbras e outros dispositivos de rede
"""

import socket
import requests
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
import time

def check_port_open(ip, port, timeout=2):
    """Verifica se uma porta específica está aberta"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def check_device(ip):
    """Verifica se um IP tem serviços ativos"""
    print(f"🔍 Verificando {ip}...")
    
    # Portas comuns de câmeras e dispositivos de rede
    ports_to_check = [80, 8080, 8000, 8899, 554, 37777, 9000, 443, 22, 23, 21]
    open_ports = []
    services = {}
    
    for port in ports_to_check:
        if check_port_open(ip, port):
            open_ports.append(port)
            
            # Para portas web, tentar identificar o serviço
            if port in [80, 8080, 8000, 8899, 9000, 443]:
                try:
                    protocol = 'https' if port == 443 else 'http'
                    url = f"{protocol}://{ip}" + (f":{port}" if (port != 80 and port != 443) else "")
                    
                    response = requests.get(url, timeout=3, allow_redirects=False, verify=False)
                    
                    # Extrair título
                    title = ""
                    title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()
                    
                    # Verificar indicadores de câmera/DVR
                    content_lower = response.text.lower()
                    server = response.headers.get('Server', '').lower()
                    
                    is_camera = any(keyword in content_lower or keyword in server for keyword in 
                                   ['intelbras', 'camera', 'dvr', 'nvr', 'surveillance', 'mibo', 'dahua', 'hikvision'])
                    
                    services[port] = {
                        'title': title,
                        'server': server,
                        'url': url,
                        'is_camera': is_camera,
                        'status_code': response.status_code
                    }
                    
                except Exception as e:
                    services[port] = {'error': str(e), 'url': url}
    
    if open_ports:
        return {
            'ip': ip,
            'open_ports': open_ports,
            'services': services
        }
    return None

def scan_network_range():
    """Escaneia a rede 192.168.5.x"""
    print("🚀 SCANNER DE REDE 192.168.5.x")
    print("=" * 50)
    print("🔍 Procurando por câmeras Intelbras e outros dispositivos...")
    print("⏳ Aguarde, isso pode levar alguns minutos...\n")
    
    # IPs para escanear (192.168.5.1 até 192.168.5.254)
    ips_to_scan = [f"192.168.5.{i}" for i in range(1, 255)]
    
    devices_found = []
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_device, ips_to_scan))
    
    devices_found = [device for device in results if device is not None]
    
    return devices_found

def print_results(devices):
    """Exibe os resultados encontrados"""
    print("\n" + "=" * 60)
    print("📊 RESULTADOS DA VARREDURA")
    print("=" * 60)
    
    if not devices:
        print("❌ Nenhum dispositivo encontrado na rede 192.168.5.x")
        print("\n💡 Possíveis motivos:")
        print("   • Câmeras desligadas ou desconectadas")
        print("   • Firewall bloqueando o scanner")
        print("   • Câmeras em outra faixa de rede")
        return
    
    cameras = []
    other_devices = []
    
    for device in devices:
        is_camera = any(service.get('is_camera', False) for service in device['services'].values())
        if is_camera:
            cameras.append(device)
        else:
            other_devices.append(device)
    
    # Exibir câmeras encontradas
    if cameras:
        print(f"\n🎯 CÂMERAS/DVR/NVR ENCONTRADAS ({len(cameras)}):")
        print("-" * 50)
        
        for device in cameras:
            print(f"\n📷 IP: {device['ip']}")
            print(f"   Portas abertas: {', '.join(map(str, device['open_ports']))}")
            
            for port, service in device['services'].items():
                if 'error' not in service:
                    print(f"   🌐 {service['url']}")
                    if service['title']:
                        print(f"      Título: {service['title']}")
                    if service['server']:
                        print(f"      Servidor: {service['server']}")
                    if service['is_camera']:
                        print(f"      ✅ DISPOSITIVO DE VIGILÂNCIA DETECTADO!")
    
    # Exibir outros dispositivos
    if other_devices:
        print(f"\n💻 OUTROS DISPOSITIVOS DE REDE ({len(other_devices)}):")
        print("-" * 45)
        
        for device in other_devices:
            print(f"\n🔧 IP: {device['ip']}")
            print(f"   Portas: {', '.join(map(str, device['open_ports']))}")
            
            for port, service in device['services'].items():
                if 'error' not in service and service['url']:
                    print(f"   🌐 {service['url']}")
                    if service['title']:
                        print(f"      {service['title']}")

def main():
    start_time = time.time()
    
    devices = scan_network_range()
    
    end_time = time.time()
    print(f"\n⏱️ Varredura concluída em {end_time - start_time:.1f} segundos")
    
    print_results(devices)
    
    print(f"\n💡 INFORMAÇÕES ÚTEIS:")
    print("🔑 Credenciais padrão Intelbras:")
    print("   • Usuário: admin | Senha: admin")
    print("   • Usuário: admin | Senha: (vazio)")
    print("   • Usuário: admin | Senha: 123456")
    
    print(f"\n📺 Para acesso RTSP (streaming):")
    print("   • rtsp://IP:554/cam/realmonitor?channel=1&subtype=0")
    print("   • rtsp://admin:senha@IP:554/cam/realmonitor?channel=1&subtype=0")
    
    print(f"\n🌐 Seu IP atual: 192.168.5.57")

if __name__ == "__main__":
    main()