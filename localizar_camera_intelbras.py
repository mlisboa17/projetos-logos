#!/usr/bin/env python3
"""
Script para localizar câmeras Intelbras na rede local
Faz varredura de IPs e identifica dispositivos Intelbras
"""

import socket
import threading
import requests
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
import time

class IntelbrasScanner:
    def __init__(self):
        self.found_devices = []
        self.timeout = 3
        
    def get_network_range(self):
        """Detecta a faixa de rede local"""
        try:
            # Obter IP local
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
            output = result.stdout
            
            # Procurar por IPv4 Address
            ipv4_pattern = r'IPv4 Address[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
            matches = re.findall(ipv4_pattern, output)
            
            for ip in matches:
                if not ip.startswith('127.') and not ip.startswith('169.254.'):
                    # Converter para faixa de rede (ex: 192.168.1.x)
                    parts = ip.split('.')
                    network_base = f"{parts[0]}.{parts[1]}.{parts[2]}"
                    print(f"🌐 Rede detectada: {network_base}.x")
                    return network_base
                    
        except Exception as e:
            print(f"❌ Erro ao detectar rede: {e}")
            
        # Fallback para redes comuns
        return "192.168.1"
    
    def check_port_open(self, ip, port):
        """Verifica se uma porta está aberta"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_http_service(self, ip, port=80):
        """Verifica serviço HTTP e tenta identificar Intelbras"""
        try:
            url = f"http://{ip}:{port}"
            response = requests.get(url, timeout=self.timeout, allow_redirects=False)
            
            # Headers e conteúdo que indicam Intelbras
            intelbras_indicators = [
                'intelbras', 'mibo', 'dahua', 'web service',
                'ipc', 'nvr', 'dvr', 'camera', 'security'
            ]
            
            content = response.text.lower()
            headers = str(response.headers).lower()
            server = response.headers.get('Server', '').lower()
            
            is_intelbras = any(indicator in content or indicator in headers or indicator in server 
                             for indicator in intelbras_indicators)
            
            return {
                'status_code': response.status_code,
                'server': server,
                'title': self.extract_title(content),
                'is_intelbras': is_intelbras,
                'content_length': len(content)
            }
            
        except requests.RequestException:
            return None
    
    def extract_title(self, html):
        """Extrai título da página HTML"""
        try:
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if title_match:
                return title_match.group(1).strip()
        except:
            pass
        return ""
    
    def scan_ip(self, ip):
        """Escaneia um IP específico"""
        # Portas comuns de câmeras Intelbras
        common_ports = [80, 8080, 8000, 8899, 37777, 554, 9000]
        
        device_info = {
            'ip': ip,
            'open_ports': [],
            'services': {},
            'is_camera': False,
            'device_type': 'Unknown'
        }
        
        # Verificar se o IP responde (ping básico)
        if not self.check_port_open(ip, 80) and not self.check_port_open(ip, 8080):
            return None
        
        print(f"🔍 Verificando {ip}...")
        
        # Verificar portas
        for port in common_ports:
            if self.check_port_open(ip, port):
                device_info['open_ports'].append(port)
                
                # Verificar serviço HTTP nas portas web
                if port in [80, 8080, 8000, 8899, 9000]:
                    http_info = self.check_http_service(ip, port)
                    if http_info:
                        device_info['services'][port] = http_info
                        
                        if http_info['is_intelbras']:
                            device_info['is_camera'] = True
                            device_info['device_type'] = 'Intelbras Camera/DVR/NVR'
        
        if device_info['open_ports']:
            return device_info
        return None
    
    def scan_network(self, network_base="192.168.1", max_workers=50):
        """Escaneia toda a rede"""
        print(f"\n🚀 Iniciando varredura da rede {network_base}.1-254")
        print("=" * 60)
        
        ips_to_scan = [f"{network_base}.{i}" for i in range(1, 255)]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.scan_ip, ips_to_scan))
        
        # Filtrar resultados válidos
        self.found_devices = [device for device in results if device is not None]
        
        return self.found_devices
    
    def print_results(self):
        """Exibe resultados encontrados"""
        print(f"\n📊 RESULTADOS DA VARREDURA")
        print("=" * 60)
        
        if not self.found_devices:
            print("❌ Nenhum dispositivo encontrado na rede")
            return
        
        intelbras_devices = [d for d in self.found_devices if d['is_camera']]
        other_devices = [d for d in self.found_devices if not d['is_camera']]
        
        if intelbras_devices:
            print(f"\n🎯 CÂMERAS INTELBRAS ENCONTRADAS ({len(intelbras_devices)}):")
            print("-" * 50)
            
            for device in intelbras_devices:
                print(f"\n📷 IP: {device['ip']}")
                print(f"   Tipo: {device['device_type']}")
                print(f"   Portas: {', '.join(map(str, device['open_ports']))}")
                
                for port, service in device['services'].items():
                    print(f"   Porta {port}: {service['title'] or 'Serviço Web'}")
                    if service['server']:
                        print(f"   Servidor: {service['server']}")
                
                # URLs de acesso
                web_ports = [p for p in device['open_ports'] if p in [80, 8080, 8000, 8899, 9000]]
                if web_ports:
                    for port in web_ports:
                        url = f"http://{device['ip']}" + (f":{port}" if port != 80 else "")
                        print(f"   🌐 Acesso: {url}")
        
        if other_devices:
            print(f"\n💻 OUTROS DISPOSITIVOS ({len(other_devices)}):")
            print("-" * 40)
            
            for device in other_devices:
                print(f"\n🔧 IP: {device['ip']}")
                print(f"   Portas: {', '.join(map(str, device['open_ports']))}")
                
                for port, service in device['services'].items():
                    if service and service['title']:
                        print(f"   Porta {port}: {service['title']}")

def main():
    print("🔍 LOCALIZADOR DE CÂMERAS INTELBRAS")
    print("=" * 40)
    
    scanner = IntelbrasScanner()
    
    # Detectar rede
    network = scanner.get_network_range()
    
    print(f"\n🌐 Escaneando rede: {network}.x")
    print("⏳ Isso pode levar alguns minutos...")
    
    start_time = time.time()
    
    # Escanear rede
    devices = scanner.scan_network(network)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️ Varredura concluída em {duration:.1f} segundos")
    
    # Exibir resultados
    scanner.print_results()
    
    # Dicas adicionais
    print(f"\n💡 DICAS:")
    print("- Verifique se as câmeras estão ligadas e conectadas à rede")
    print("- Algumas câmeras podem usar IPs diferentes (ex: 192.168.0.x)")
    print("- Credenciais padrão Intelbras: admin/admin ou admin/(vazio)")
    print("- Para RTSP: rtsp://IP:554/cam/realmonitor?channel=1&subtype=0")

if __name__ == "__main__":
    main()