#!/usr/bin/env python3
"""
Script para testar acesso à câmera Intelbras
IP: 192.168.5.136
Credenciais: admin / C@sa3863
"""

import requests
import base64
from requests.auth import HTTPBasicAuth
import json

class IntelbrasCamera:
    def __init__(self, ip="192.168.5.136", username="admin", password="C@sa3863"):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{ip}"
        
    def test_basic_access(self):
        """Testa acesso básico à câmera"""
        print(f"🔍 Testando acesso à câmera {self.ip}")
        print("=" * 50)
        
        try:
            # Teste sem autenticação
            response = requests.get(self.base_url, timeout=10)
            print(f"✅ Resposta HTTP: {response.status_code}")
            
            if "login" in response.text.lower() or "password" in response.text.lower():
                print("🔐 Interface de login detectada")
                
            # Teste com autenticação básica
            auth_response = requests.get(
                self.base_url, 
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=10
            )
            print(f"🔑 Com autenticação: {auth_response.status_code}")
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Erro no acesso: {e}")
            return False
    
    def test_common_paths(self):
        """Testa caminhos comuns da câmera Intelbras"""
        print(f"\n📂 Testando caminhos comuns...")
        
        common_paths = [
            "/",
            "/login.htm",
            "/index.htm",
            "/main.htm",
            "/viewer.htm",
            "/cgi-bin/main-cgi",
            "/cgi-bin/hi3510/param.cgi?cmd=getserverinfo",
            "/cgi-bin/hi3510/param.cgi?cmd=getdeviceinfo",
            "/web/index.html",
            "/doc/script?",
            "/ISAPI/System/deviceInfo",
            "/api/v1/system/deviceinfo"
        ]
        
        working_paths = []
        
        for path in common_paths:
            try:
                url = f"{self.base_url}{path}"
                response = requests.get(
                    url,
                    auth=HTTPBasicAuth(self.username, self.password),
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"✅ {path} - Status: {response.status_code}")
                    working_paths.append(path)
                elif response.status_code == 401:
                    print(f"🔐 {path} - Requer autenticação")
                elif response.status_code == 404:
                    print(f"❌ {path} - Não encontrado")
                else:
                    print(f"⚠️ {path} - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {path} - Erro: {str(e)[:50]}...")
        
        return working_paths
    
    def get_device_info(self):
        """Tenta obter informações do dispositivo"""
        print(f"\n📋 Obtendo informações do dispositivo...")
        
        info_endpoints = [
            "/cgi-bin/hi3510/param.cgi?cmd=getdeviceinfo",
            "/cgi-bin/hi3510/param.cgi?cmd=getserverinfo", 
            "/ISAPI/System/deviceInfo",
            "/api/v1/system/deviceinfo",
            "/cgi-bin/main-cgi?action=getDeviceInfo"
        ]
        
        for endpoint in info_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(
                    url,
                    auth=HTTPBasicAuth(self.username, self.password),
                    timeout=5
                )
                
                if response.status_code == 200 and response.text.strip():
                    print(f"✅ Informações obtidas de: {endpoint}")
                    print(f"📄 Conteúdo: {response.text[:200]}...")
                    return response.text
                    
            except Exception as e:
                continue
        
        print("❌ Não foi possível obter informações do dispositivo")
        return None
    
    def test_rtsp_urls(self):
        """Lista URLs RTSP comuns para teste"""
        print(f"\n📺 URLs RTSP para teste:")
        print("-" * 30)
        
        rtsp_urls = [
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=1",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/h264Preview_01_main",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/h264Preview_01_sub",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/live/1/1",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/live/1/2",
            f"rtsp://{self.ip}:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
        ]
        
        for i, url in enumerate(rtsp_urls, 1):
            print(f"{i}. {url}")
        
        return rtsp_urls
    
    def generate_access_summary(self):
        """Gera resumo de acesso"""
        print(f"\n📋 RESUMO DE ACESSO À CÂMERA")
        print("=" * 50)
        print(f"🌐 IP da Câmera: {self.ip}")
        print(f"👤 Usuário: {self.username}")
        print(f"🔑 Senha: {self.password}")
        print(f"🔗 Interface Web: {self.base_url}")
        print(f"📹 Porta RTSP: 554")
        print(f"🔌 Porta P2P: 37777")
        
        print(f"\n💻 Para integração com VerifiK:")
        print(f"1. URL de captura: {self.base_url}/cgi-bin/snapshot.cgi")
        print(f"2. Stream RTSP: rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0")
        print(f"3. API de controle: {self.base_url}/cgi-bin/main-cgi")

def main():
    print("🎥 TESTE DE ACESSO À CÂMERA INTELBRAS")
    print("=" * 60)
    
    # Inicializar câmera com credenciais fornecidas
    camera = IntelbrasCamera()
    
    # Testar acesso básico
    if camera.test_basic_access():
        print("✅ Câmera acessível!")
        
        # Testar caminhos comuns
        working_paths = camera.test_common_paths()
        
        # Obter informações do dispositivo
        device_info = camera.get_device_info()
        
        # Mostrar URLs RTSP
        rtsp_urls = camera.test_rtsp_urls()
        
        # Gerar resumo
        camera.generate_access_summary()
        
    else:
        print("❌ Não foi possível acessar a câmera")
        print("💡 Verifique:")
        print("   • Se a câmera está ligada")
        print("   • Se as credenciais estão corretas")
        print("   • Se há firewall bloqueando")

if __name__ == "__main__":
    main()