#!/usr/bin/env python3
"""
Testador de APIs Intelbras
Mapeia e testa todos os endpoints disponíveis
"""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import time
import json

class IntelbrasAPITester:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{ip}"
        self.session = requests.Session()
        self.auth_basic = HTTPBasicAuth(username, password)
        self.auth_digest = HTTPDigestAuth(username, password)
        
    def test_all_apis(self):
        """Testa todas as APIs conhecidas da Intelbras"""
        
        print("=" * 70)
        print(f"🔍 TESTANDO APIs INTELBRAS - {self.ip}")
        print("=" * 70)
        
        # APIs de informação do dispositivo
        info_apis = [
            ("Device Type", "/cgi-bin/magicBox.cgi?action=getDeviceType"),
            ("Machine Name", "/cgi-bin/magicBox.cgi?action=getMachineName"),
            ("System Info", "/cgi-bin/magicBox.cgi?action=getSystemInfo"),
            ("Software Version", "/cgi-bin/magicBox.cgi?action=getSoftwareVersion"),
            ("Hardware Version", "/cgi-bin/magicBox.cgi?action=getHardwareVersion"),
            ("Serial Number", "/cgi-bin/magicBox.cgi?action=getSerialNo"),
            ("Current Time", "/cgi-bin/global.cgi?action=getCurrentTime"),
            ("General Config", "/cgi-bin/configManager.cgi?action=getConfig&name=General"),
            ("Network Config", "/cgi-bin/configManager.cgi?action=getConfig&name=Network"),
            ("Video Options", "/cgi-bin/configManager.cgi?action=getConfig&name=VideoInOptions"),
            ("Encode Config", "/cgi-bin/configManager.cgi?action=getConfig&name=Encode"),
            ("Storage Config", "/cgi-bin/configManager.cgi?action=getConfig&name=Storage"),
        ]
        
        print("\n📋 INFORMAÇÕES DO DISPOSITIVO:")
        print("-" * 50)
        
        for name, endpoint in info_apis:
            result = self.test_endpoint(name, endpoint)
            if result['success']:
                print(f"✅ {name:<20} | {result['response'][:80]}...")
            else:
                print(f"❌ {name:<20} | {result['error']}")
        
        # APIs de captura de imagem  
        snapshot_apis = [
            ("Snapshot Padrão", "/cgi-bin/snapshot.cgi?channel=1&subtype=0"),
            ("Snapshot Auth", "/cgi-bin/snapshot.cgi?chn=1&u={}&p={}".format(self.username, self.password)),
            ("MagicBox Snapshot", "/cgi-bin/magicBox.cgi?action=getSnapshot&channel=1&subtype=0"),
            ("Config Snapshot", "/cgi-bin/configManager.cgi?action=attachFileProc&name=Snap&channel=1&subtype=0"),
            ("Streaming Picture", "/Streaming/Channels/101/picture"),
            ("Hi3510 Snap", "/cgi-bin/hi3510/snap.cgi?&-usr={}&-pwd={}".format(self.username, self.password)),
            ("ONVIF Snapshot", "/onvif-http/snapshot?Profile_1"),
        ]
        
        print("\n📸 APIS DE CAPTURA:")
        print("-" * 50)
        
        for name, endpoint in snapshot_apis:
            result = self.test_snapshot_endpoint(name, endpoint)
            if result['success']:
                print(f"✅ {name:<20} | {result['content_type']} | {result['size']} bytes")
            else:
                print(f"❌ {name:<20} | {result['error']}")
        
        # APIs de controle PTZ
        ptz_apis = [
            ("PTZ Info", "/cgi-bin/ptz.cgi?action=getCurrentProtocolCaps&channel=1"),
            ("PTZ Status", "/cgi-bin/ptz.cgi?action=getStatus&channel=1"),
            ("PTZ Config", "/cgi-bin/configManager.cgi?action=getConfig&name=PTZ"),
        ]
        
        print("\n🎛️  CONTROLE PTZ:")
        print("-" * 50)
        
        for name, endpoint in ptz_apis:
            result = self.test_endpoint(name, endpoint)
            if result['success']:
                print(f"✅ {name:<20} | Resposta: {len(result['response'])} chars")
            else:
                print(f"❌ {name:<20} | {result['error']}")
        
        # URLs RTSP
        rtsp_urls = [
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=1", 
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/h264Preview_01_main",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/h264Preview_01_sub",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/live/1/main",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/live/1/sub"
        ]
        
        print("\n🎥 URLs RTSP DISPONÍVEIS:")
        print("-" * 50)
        
        for i, url in enumerate(rtsp_urls, 1):
            print(f"{i}. {url}")
        
        # Testar capacidades específicas
        print("\n🔧 CAPACIDADES ESPECIAIS:")
        print("-" * 50)
        
        self.test_advanced_features()
        
    def test_endpoint(self, name, endpoint):
        """Testa um endpoint HTTP"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            for auth_method in [self.auth_basic, self.auth_digest]:
                try:
                    response = self.session.get(url, auth=auth_method, timeout=10)
                    
                    if response.status_code == 200:
                        return {
                            'success': True,
                            'response': response.text.strip(),
                            'auth_method': type(auth_method).__name__
                        }
                        
                except Exception:
                    continue
            
            return {'success': False, 'error': 'Falha na autenticação'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_snapshot_endpoint(self, name, endpoint):
        """Testa endpoint de captura especificamente"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            for auth_method in [self.auth_basic, self.auth_digest]:
                try:
                    response = self.session.get(url, auth=auth_method, timeout=15, stream=True)
                    
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if (response.status_code == 200 and 
                        ('image' in content_type or 'jpeg' in content_type) and
                        len(response.content) > 2000):
                        
                        return {
                            'success': True,
                            'content_type': content_type,
                            'size': len(response.content),
                            'auth_method': type(auth_method).__name__
                        }
                        
                except Exception:
                    continue
            
            return {'success': False, 'error': 'Sem imagem válida'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_advanced_features(self):
        """Testa recursos avançados"""
        
        # Testar Motion Detection
        motion_endpoint = "/cgi-bin/configManager.cgi?action=getConfig&name=MotionDetect"
        result = self.test_endpoint("Motion Detection", motion_endpoint)
        
        if result['success']:
            print("✅ Detecção de Movimento: Suportada")
        else:
            print("❌ Detecção de Movimento: Não disponível")
        
        # Testar Audio
        audio_endpoint = "/cgi-bin/configManager.cgi?action=getConfig&name=AudioInOptions"  
        result = self.test_endpoint("Audio Config", audio_endpoint)
        
        if result['success']:
            print("✅ Configuração de Áudio: Disponível")
        else:
            print("❌ Configuração de Áudio: Não disponível")
        
        # Testar Recording
        record_endpoint = "/cgi-bin/configManager.cgi?action=getConfig&name=Record"
        result = self.test_endpoint("Recording Config", record_endpoint)
        
        if result['success']:
            print("✅ Configuração de Gravação: Disponível")
        else:
            print("❌ Configuração de Gravação: Não disponível")
        
        # Testar Smart Features
        smart_endpoints = [
            ("Face Detection", "/cgi-bin/configManager.cgi?action=getConfig&name=FaceDetection"),
            ("Perimeter Protection", "/cgi-bin/configManager.cgi?action=getConfig&name=VideoAnalyseRule"),
            ("People Counting", "/cgi-bin/configManager.cgi?action=getConfig&name=PeopleNumber"),
        ]
        
        for name, endpoint in smart_endpoints:
            result = self.test_endpoint(name, endpoint)
            if result['success']:
                print(f"✅ {name}: Suportado")
            else:
                print(f"❌ {name}: Não disponível")
    
    def save_api_report(self):
        """Salva relatório das APIs"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"intelbras_api_report_{timestamp}.txt"
        
        print(f"\n💾 Salvando relatório em: {filename}")
        
        # Aqui você poderia implementar a lógica para salvar
        # todos os resultados em um arquivo de relatório

def main():
    # Configuração da câmera
    camera_ip = "192.168.5.136"
    username = "admin"
    password = "C@sa3863"
    
    tester = IntelbrasAPITester(camera_ip, username, password)
    tester.test_all_apis()
    
    print("\n" + "=" * 70)
    print("🎯 TESTE CONCLUÍDO!")
    print("=" * 70)

if __name__ == "__main__":
    main()