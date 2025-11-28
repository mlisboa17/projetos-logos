#!/usr/bin/env python3
"""
Teste Específico do Sistema de Foco da Câmera Intelbras
Testa isoladamente o controle de foco para debug
"""

import requests
from requests.auth import HTTPDigestAuth
import time

class TesteFocoIntelbras:
    def __init__(self):
        self.camera_ip = "192.168.5.136"
        self.camera_user = "admin"
        self.camera_pass = "C@sa3863"
        self.auth = HTTPDigestAuth(self.camera_user, self.camera_pass)
        
    def testar_conexao_camera(self):
        """Testa conexão básica com a câmera"""
        try:
            print("🔌 Testando conexão com câmera...")
            
            url = f"http://{self.camera_ip}/cgi-bin/magicBox.cgi?action=getDeviceType"
            response = requests.get(url, auth=self.auth, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Conexão OK: {response.text.strip()}")
                return True
            else:
                print(f"❌ Erro de conexão: {response.status_code}")
                return False
        except Exception as e:
            print(f"💥 Erro na conexão: {e}")
            return False
    
    def obter_configuracao_foco_atual(self):
        """Obtém configuração atual do foco"""
        try:
            print("📋 Obtendo configuração atual do foco...")
            
            url = f"http://{self.camera_ip}/cgi-bin/configManager.cgi?action=getConfig&name=VideoInOptions"
            response = requests.get(url, auth=self.auth, timeout=10)
            
            if response.status_code == 200:
                config = response.text
                print(f"📄 Configuração atual (primeiras linhas):")
                linhas = config.split('\n')[:10]
                for linha in linhas:
                    if 'Focus' in linha:
                        print(f"  🎯 {linha.strip()}")
                return True
            else:
                print(f"❌ Erro ao obter config: {response.status_code}")
                return False
        except Exception as e:
            print(f"💥 Erro ao obter config: {e}")
            return False
    
    def testar_ajuste_foco(self, valor_foco):
        """Testa ajuste de foco com valor específico"""
        try:
            print(f"\n🔧 Testando ajuste de foco para: {valor_foco}")
            
            # 1. Ativar modo manual
            url_manual = f"http://{self.camera_ip}/cgi-bin/configManager.cgi?action=setConfig&VideoInOptions[0].FocusMode=1"
            print(f"📡 Ativando modo manual...")
            print(f"   URL: {url_manual}")
            
            response_manual = requests.get(url_manual, auth=self.auth, timeout=10)
            print(f"   Resposta: {response_manual.status_code}")
            print(f"   Conteúdo: {response_manual.text.strip()}")
            
            if response_manual.status_code == 200:
                print("✅ Modo manual ativado")
                
                # 2. Aguardar um pouco
                time.sleep(1)
                
                # 3. Definir valor do foco
                url_foco = f"http://{self.camera_ip}/cgi-bin/configManager.cgi?action=setConfig&VideoInOptions[0].FocusRect.Value={valor_foco}"
                print(f"📡 Definindo valor do foco...")
                print(f"   URL: {url_foco}")
                
                response_foco = requests.get(url_foco, auth=self.auth, timeout=10)
                print(f"   Resposta: {response_foco.status_code}")
                print(f"   Conteúdo: {response_foco.text.strip()}")
                
                if response_foco.status_code == 200:
                    print(f"✅ Foco ajustado para {valor_foco}")
                    return True
                else:
                    print(f"❌ Erro ao definir foco: {response_foco.status_code}")
            else:
                print(f"❌ Erro ao ativar modo manual: {response_manual.status_code}")
            
            return False
            
        except Exception as e:
            print(f"💥 Erro no teste de foco: {e}")
            return False
    
    def testar_foco_automatico(self):
        """Testa retorno ao foco automático"""
        try:
            print(f"\n🎯 Testando retorno ao foco automático...")
            
            url_auto = f"http://{self.camera_ip}/cgi-bin/configManager.cgi?action=setConfig&VideoInOptions[0].FocusMode=0"
            print(f"📡 Ativando modo automático...")
            print(f"   URL: {url_auto}")
            
            response = requests.get(url_auto, auth=self.auth, timeout=10)
            print(f"   Resposta: {response.status_code}")
            print(f"   Conteúdo: {response.text.strip()}")
            
            if response.status_code == 200:
                print("✅ Foco automático ativado")
                return True
            else:
                print(f"❌ Erro ao ativar foco automático: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"💥 Erro no foco automático: {e}")
            return False
    
    def executar_teste_completo(self):
        """Executa teste completo do sistema de foco"""
        print("🧪 INICIANDO TESTE COMPLETO DO SISTEMA DE FOCO")
        print("=" * 60)
        
        # 1. Teste de conexão
        if not self.testar_conexao_camera():
            print("💥 FALHA: Não foi possível conectar à câmera")
            return False
        
        # 2. Obter configuração atual
        self.obter_configuracao_foco_atual()
        
        # 3. Testar diferentes valores de foco
        focos_teste = [5000, 6000, 6500, 7000, 7500]
        
        print(f"\n🎯 Testando {len(focos_teste)} valores de foco...")
        
        for i, foco in enumerate(focos_teste):
            print(f"\n--- Teste {i+1}/{len(focos_teste)} ---")
            
            sucesso = self.testar_ajuste_foco(foco)
            
            if sucesso:
                print(f"✅ Foco {foco}: SUCESSO")
                time.sleep(3)  # Aguardar câmera ajustar
            else:
                print(f"❌ Foco {foco}: FALHOU")
                
            time.sleep(1)  # Pausa entre testes
        
        # 4. Voltar ao automático
        print(f"\n🔄 Finalizando...")
        self.testar_foco_automatico()
        
        print("\n" + "=" * 60)
        print("🧪 TESTE COMPLETO FINALIZADO")
        print("📊 Verifique visualmente se o foco da câmera mudou durante os testes")
        
        return True

if __name__ == "__main__":
    teste = TesteFocoIntelbras()
    teste.executar_teste_completo()