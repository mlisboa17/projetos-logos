#!/usr/bin/env python3
"""
Explorador Completo da API Intelbras
Mapeia todas as funcionalidades disponíveis na câmera
"""

import requests
from requests.auth import HTTPDigestAuth
import json
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import re

class IntelbrasAPIExplorer:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username  
        self.password = password
        self.base_url = f"http://{ip}"
        self.session = requests.Session()
        self.auth = HTTPDigestAuth(username, password)
        self.capabilities = {}
        
    def explore_all_apis(self):
        """Explora todas as APIs disponíveis"""
        
        print("🎯 EXPLORADOR COMPLETO DA API INTELBRAS")
        print(f"📷 Câmera: {self.ip} | User: {self.username}")
        print("=" * 70)
        
        # 1. Informações básicas do dispositivo
        print("\n📋 1. INFORMAÇÕES DO DISPOSITIVO")
        print("-" * 50)
        self.get_device_info()
        
        # 2. Configurações de vídeo
        print("\n🎥 2. CONFIGURAÇÕES DE VÍDEO") 
        print("-" * 50)
        self.get_video_config()
        
        # 3. Capacidades de snapshot/captura
        print("\n📸 3. CAPACIDADES DE CAPTURA")
        print("-" * 50)
        self.test_snapshot_capabilities()
        
        # 4. Streaming e RTSP
        print("\n🎬 4. STREAMING E RTSP")
        print("-" * 50)
        self.get_streaming_info()
        
        # 5. PTZ (Pan/Tilt/Zoom) se disponível
        print("\n🎛️ 5. CONTROLE PTZ")
        print("-" * 50)
        self.test_ptz_capabilities()
        
        # 6. Detecção inteligente
        print("\n🤖 6. ANÁLISE INTELIGENTE")
        print("-" * 50)
        self.test_smart_features()
        
        # 7. Gravação e armazenamento
        print("\n💾 7. GRAVAÇÃO E STORAGE") 
        print("-" * 50)
        self.test_recording_features()
        
        # 8. Configurações de rede
        print("\n🌐 8. CONFIGURAÇÕES DE REDE")
        print("-" * 50)
        self.get_network_config()
        
        # 9. Eventos e alarmes
        print("\n🚨 9. EVENTOS E ALARMES")
        print("-" * 50)
        self.test_event_capabilities()
        
        # 10. APIs de controle
        print("\n⚙️ 10. CONTROLES AVANÇADOS")
        print("-" * 50)
        self.test_control_apis()
        
        # Resumo final
        self.generate_summary()
    
    def api_call(self, endpoint, description=""):
        """Faz chamada para API e retorna resultado"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, auth=self.auth, timeout=10)
            
            success = response.status_code == 200
            content = response.text if success else f"Error {response.status_code}"
            
            status = "✅" if success else "❌"
            print(f"{status} {description:<30} | {endpoint}")
            
            if success and len(content) > 100:
                print(f"   📄 Resposta: {len(content)} chars | {content[:80]}...")
            elif success:
                print(f"   📄 Resposta: {content}")
            
            return {'success': success, 'content': content, 'status': response.status_code}
            
        except Exception as e:
            print(f"❌ {description:<30} | Erro: {str(e)[:50]}")
            return {'success': False, 'error': str(e)}
    
    def get_device_info(self):
        """Obtém informações básicas do dispositivo"""
        
        device_apis = [
            ("/cgi-bin/magicBox.cgi?action=getDeviceType", "Tipo do Dispositivo"),
            ("/cgi-bin/magicBox.cgi?action=getMachineName", "Nome da Máquina"),
            ("/cgi-bin/magicBox.cgi?action=getSerialNo", "Número de Série"),
            ("/cgi-bin/magicBox.cgi?action=getSoftwareVersion", "Versão do Software"),
            ("/cgi-bin/magicBox.cgi?action=getHardwareVersion", "Versão do Hardware"),
            ("/cgi-bin/magicBox.cgi?action=getSystemInfo", "Informações do Sistema"),
            ("/cgi-bin/global.cgi?action=getCurrentTime", "Data/Hora Atual"),
            ("/cgi-bin/magicBox.cgi?action=getProductDefinition", "Definição do Produto")
        ]
        
        device_info = {}
        for endpoint, desc in device_apis:
            result = self.api_call(endpoint, desc)
            if result['success']:
                device_info[desc] = result['content']
        
        self.capabilities['device_info'] = device_info
    
    def get_video_config(self):
        """Configurações de vídeo disponíveis"""
        
        video_apis = [
            ("/cgi-bin/configManager.cgi?action=getConfig&name=VideoInOptions", "Opções de Entrada de Vídeo"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=Encode", "Configurações de Codificação"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=VideoWidget", "Widgets de Vídeo"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=VideoColor", "Configurações de Cor"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=VideoStandard", "Padrão de Vídeo"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle", "Títulos dos Canais")
        ]
        
        video_config = {}
        for endpoint, desc in video_apis:
            result = self.api_call(endpoint, desc)
            if result['success']:
                video_config[desc] = result['content']
        
        self.capabilities['video_config'] = video_config
    
    def test_snapshot_capabilities(self):
        """Testa capacidades de captura"""
        
        snapshot_apis = [
            ("/cgi-bin/snapshot.cgi", "Snapshot Básico"),
            ("/cgi-bin/snapshot.cgi?channel=1&subtype=0", "Snapshot Alta Qualidade"),
            ("/cgi-bin/snapshot.cgi?channel=1&subtype=1", "Snapshot Baixa Qualidade"),
            ("/cgi-bin/magicBox.cgi?action=getSnapshot&channel=1", "MagicBox Snapshot"),
            ("/Streaming/Channels/101/picture", "Streaming Picture"),
            ("/cgi-bin/configManager.cgi?action=attachFileProc&name=Snap", "Config Snapshot")
        ]
        
        working_snapshots = []
        for endpoint, desc in snapshot_apis:
            result = self.api_call(endpoint, desc)
            if result['success'] and 'image' in str(result.get('content', '')):
                working_snapshots.append(endpoint)
        
        self.capabilities['snapshot_urls'] = working_snapshots
        print(f"   🎯 URLs de snapshot funcionais: {len(working_snapshots)}")
    
    def get_streaming_info(self):
        """Informações de streaming"""
        
        stream_apis = [
            ("/cgi-bin/configManager.cgi?action=getConfig&name=VideoInMode", "Modo de Entrada"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=Streaming", "Configurações de Stream"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=NetWork.RTSP", "Configurações RTSP"),
        ]
        
        for endpoint, desc in stream_apis:
            self.api_call(endpoint, desc)
        
        # URLs RTSP padrão
        rtsp_urls = [
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=1",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/h264Preview_01_main",
            f"rtsp://{self.username}:{self.password}@{self.ip}:554/live/1/main"
        ]
        
        print("   📡 URLs RTSP disponíveis:")
        for i, url in enumerate(rtsp_urls, 1):
            print(f"      {i}. {url}")
        
        self.capabilities['rtsp_urls'] = rtsp_urls
    
    def test_ptz_capabilities(self):
        """Testa capacidades PTZ"""
        
        ptz_apis = [
            ("/cgi-bin/ptz.cgi?action=getCurrentProtocolCaps&channel=1", "Capacidades PTZ"),
            ("/cgi-bin/ptz.cgi?action=getStatus&channel=1", "Status PTZ"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=PTZ", "Configuração PTZ"),
            ("/cgi-bin/ptz.cgi?action=getPresets&channel=1", "Presets PTZ")
        ]
        
        ptz_available = False
        for endpoint, desc in ptz_apis:
            result = self.api_call(endpoint, desc)
            if result['success'] and 'protocol' in result['content'].lower():
                ptz_available = True
        
        if ptz_available:
            print("   🎯 Controles PTZ disponíveis:")
            ptz_commands = [
                "Up", "Down", "Left", "Right", "ZoomIn", "ZoomOut", 
                "FocusIn", "FocusOut", "IrisIn", "IrisOut"
            ]
            for cmd in ptz_commands:
                print(f"      • {cmd}")
        
        self.capabilities['ptz_available'] = ptz_available
    
    def test_smart_features(self):
        """Testa recursos de análise inteligente"""
        
        smart_apis = [
            ("/cgi-bin/configManager.cgi?action=getConfig&name=MotionDetect", "Detecção de Movimento"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=VideoAnalyseRule", "Regras de Análise"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=FaceDetection", "Detecção Facial"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=PeopleNumber", "Contagem de Pessoas"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=CrossLineDetection", "Detecção de Linha"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=CrossRegionDetection", "Detecção de Região"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=LeftDetection", "Detecção de Objeto Abandonado"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=TakenAwayDetection", "Detecção de Objeto Removido"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=FaceRecognition", "Reconhecimento Facial"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=NumberStat", "Estatísticas Numéricas")
        ]
        
        smart_features = []
        for endpoint, desc in smart_apis:
            result = self.api_call(endpoint, desc)
            if result['success'] and len(result['content']) > 50:
                smart_features.append(desc)
        
        self.capabilities['smart_features'] = smart_features
        print(f"   🤖 Recursos inteligentes disponíveis: {len(smart_features)}")
    
    def test_recording_features(self):
        """Testa recursos de gravação"""
        
        record_apis = [
            ("/cgi-bin/configManager.cgi?action=getConfig&name=Record", "Configurações de Gravação"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=Storage", "Configurações de Storage"),
            ("/cgi-bin/recordManager.cgi?action=getRecordList", "Lista de Gravações"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=RecordMode", "Modo de Gravação"),
            ("/cgi-bin/magicBox.cgi?action=getRecordList", "Lista MagicBox")
        ]
        
        for endpoint, desc in record_apis:
            self.api_call(endpoint, desc)
    
    def get_network_config(self):
        """Configurações de rede"""
        
        network_apis = [
            ("/cgi-bin/configManager.cgi?action=getConfig&name=Network", "Configuração de Rede"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=NetWork.WiFi", "Configuração WiFi"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=NetWork.DDNS", "Configuração DDNS"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=NetWork.FTP", "Configuração FTP"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=NetWork.Email", "Configuração Email")
        ]
        
        for endpoint, desc in network_apis:
            self.api_call(endpoint, desc)
    
    def test_event_capabilities(self):
        """Testa capacidades de eventos"""
        
        event_apis = [
            ("/cgi-bin/configManager.cgi?action=getConfig&name=Alarm", "Configurações de Alarme"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=AlarmServer", "Servidor de Alarmes"),
            ("/cgi-bin/eventManager.cgi?action=getCurrentEvents", "Eventos Atuais"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=VideoLoss", "Perda de Vídeo"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=AudioDetect", "Detecção de Áudio")
        ]
        
        for endpoint, desc in event_apis:
            self.api_call(endpoint, desc)
    
    def test_control_apis(self):
        """Testa APIs de controle"""
        
        control_apis = [
            ("/cgi-bin/configManager.cgi?action=getConfig&name=General", "Configurações Gerais"),
            ("/cgi-bin/userManager.cgi?action=getUserList", "Lista de Usuários"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=AccessControl", "Controle de Acesso"),
            ("/cgi-bin/magicBox.cgi?action=reboot", "Reiniciar (CUIDADO!)"),
            ("/cgi-bin/configManager.cgi?action=getConfig&name=System", "Configurações do Sistema")
        ]
        
        for endpoint, desc in control_apis:
            if "reboot" not in endpoint:  # Não executar reboot
                self.api_call(endpoint, desc)
            else:
                print(f"⚠️  {desc:<30} | {endpoint} (NÃO EXECUTADO)")
    
    def generate_summary(self):
        """Gera resumo das capacidades"""
        
        print("\n" + "=" * 70)
        print("📊 RESUMO DAS CAPACIDADES DA CÂMERA INTELBRAS")
        print("=" * 70)
        
        # Informações básicas
        if 'device_info' in self.capabilities:
            print("\n📋 INFORMAÇÕES DO DISPOSITIVO:")
            for key, value in self.capabilities['device_info'].items():
                if value and len(value) < 100:
                    print(f"   • {key}: {value}")
        
        # URLs funcionais
        if 'snapshot_urls' in self.capabilities:
            print(f"\n📸 URLS DE CAPTURA FUNCIONAIS: {len(self.capabilities['snapshot_urls'])}")
            for url in self.capabilities['snapshot_urls']:
                print(f"   • {url}")
        
        # RTSP
        if 'rtsp_urls' in self.capabilities:
            print(f"\n🎬 URLS RTSP: {len(self.capabilities['rtsp_urls'])}")
            for url in self.capabilities['rtsp_urls'][:2]:  # Mostrar apenas as principais
                print(f"   • {url}")
        
        # PTZ
        if self.capabilities.get('ptz_available'):
            print("\n🎛️ PTZ: ✅ Disponível")
        else:
            print("\n🎛️ PTZ: ❌ Não disponível")
        
        # Recursos inteligentes
        smart_count = len(self.capabilities.get('smart_features', []))
        print(f"\n🤖 ANÁLISE INTELIGENTE: {smart_count} recursos detectados")
        if smart_count > 0:
            for feature in self.capabilities['smart_features'][:5]:
                print(f"   • {feature}")
        
        # Salvar relatório
        self.save_capabilities_report()
    
    def save_capabilities_report(self):
        """Salva relatório completo"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intelbras_api_capabilities_{timestamp}.json"
        
        report = {
            'camera_ip': self.ip,
            'timestamp': timestamp,
            'capabilities': self.capabilities
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Relatório salvo: {filename}")
            
        except Exception as e:
            print(f"\n❌ Erro ao salvar relatório: {e}")

def main():
    # Configurações da câmera
    camera_ip = "192.168.5.136"
    username = "admin"
    password = "C@sa3863"
    
    # Criar explorador
    explorer = IntelbrasAPIExplorer(camera_ip, username, password)
    
    # Explorar todas as APIs
    explorer.explore_all_apis()
    
    print(f"\n🎯 EXPLORAÇÃO CONCLUÍDA!")
    print("📋 Consulte o arquivo JSON gerado para detalhes completos")

if __name__ == "__main__":
    main()