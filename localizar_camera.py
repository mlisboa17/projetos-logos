#!/usr/bin/env python3
"""
Localizador de Câmera Intelbras
Encontra e configura automaticamente o IP correto da câmera
"""

import requests
from requests.auth import HTTPDigestAuth
import subprocess
import re
import threading
from concurrent.futures import ThreadPoolExecutor

class LocalizadorCamera:
    def __init__(self):
        self.auth = HTTPDigestAuth('admin', 'C@sa3863')
        self.cameras_encontradas = []
    
    def obter_redes_locais(self):
        """Obtém redes locais do sistema"""
        try:
            # Executar ipconfig para obter informações de rede
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp850')
            output = result.stdout
            
            # Extrair IPs locais
            ips = re.findall(r'Endereço IPv4.*?: (\d+\.\d+\.\d+\.\d+)', output)
            
            redes = set()
            for ip in ips:
                # Extrair rede (primeiros 3 octetos)
                partes = ip.split('.')
                if len(partes) == 4:
                    rede = '.'.join(partes[:3])
                    redes.add(rede)
            
            return list(redes)
            
        except Exception as e:
            print(f"Erro ao obter redes: {e}")
            # Redes padrão como fallback
            return ['192.168.1', '192.168.0', '192.168.68', '10.0.0', '172.16.0']
    
    def testar_ip(self, ip):
        """Testa um IP específico"""
        try:
            url = f'http://{ip}/cgi-bin/magicBox.cgi?action=getDeviceType'
            response = requests.get(url, auth=self.auth, timeout=2)
            
            if response.status_code == 200:
                # Testar snapshot também
                snapshot_url = f'http://{ip}/cgi-bin/snapshot.cgi'
                snap_resp = requests.get(snapshot_url, auth=self.auth, timeout=2)
                
                camera_info = {
                    'ip': ip,
                    'tipo': response.text.strip(),
                    'snapshot_ok': snap_resp.status_code == 200,
                    'snapshot_size': len(snap_resp.content) if snap_resp.status_code == 200 else 0
                }
                
                self.cameras_encontradas.append(camera_info)
                print(f"✅ CÂMERA ENCONTRADA: {ip} - {camera_info['tipo']}")
                
                return camera_info
                
        except:
            pass
        
        return None
    
    def varredura_completa(self):
        """Faz varredura completa para encontrar câmeras"""
        print("🔍 LOCALIZADOR DE CÂMERA INTELBRAS")
        print("=" * 50)
        
        # Obter redes locais
        redes = self.obter_redes_locais()
        print(f"🌐 Redes detectadas: {', '.join(redes)}")
        
        # IPs comuns para câmeras
        ips_comuns = [100, 101, 102, 136, 200, 201, 64, 65, 66, 10, 20, 30]
        
        # Gerar lista de IPs para testar
        ips_teste = []
        for rede in redes:
            for ip in ips_comuns:
                ips_teste.append(f"{rede}.{ip}")
        
        print(f"📡 Testando {len(ips_teste)} IPs...")
        print("⏳ Aguarde...")
        
        # Testar IPs em paralelo para ser mais rápido
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(self.testar_ip, ip) for ip in ips_teste]
            
            for i, future in enumerate(futures):
                if i % 10 == 0:
                    print(f"📊 Progresso: {i}/{len(ips_teste)}")
                future.result()
        
        # Mostrar resultados
        print("\n" + "=" * 50)
        print("📊 RESULTADO DA VARREDURA:")
        print("=" * 50)
        
        if self.cameras_encontradas:
            for i, camera in enumerate(self.cameras_encontradas, 1):
                print(f"\n🎯 CÂMERA {i}:")
                print(f"   📍 IP: {camera['ip']}")
                print(f"   📱 Tipo: {camera['tipo']}")
                print(f"   📸 Snapshot: {'✅ OK' if camera['snapshot_ok'] else '❌ Erro'}")
                
                if camera['snapshot_ok']:
                    print(f"   📊 Tamanho imagem: {camera['snapshot_size']} bytes")
                    
        else:
            print("❌ NENHUMA CÂMERA ENCONTRADA")
            print("\n💡 POSSÍVEIS SOLUÇÕES:")
            print("   1. Verificar se a câmera está ligada")
            print("   2. Verificar cabo de rede")
            print("   3. Verificar se está na mesma rede")
            print("   4. Testar credenciais (admin / C@sa3863)")
            print("   5. Verificar IP manual na interface da câmera")
        
        return self.cameras_encontradas
    
    def atualizar_sistema(self, novo_ip):
        """Atualiza o IP nos arquivos do sistema"""
        arquivos_sistema = [
            'verifik_reconhecimento_automatico.py',
            'verifik_streaming_basico.py',
            'verifik_funcional.py'
        ]
        
        for arquivo in arquivos_sistema:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                
                # Substituir IP antigo pelo novo
                conteudo_novo = conteudo.replace('192.168.5.136', novo_ip)
                
                if conteudo_novo != conteudo:
                    with open(arquivo, 'w', encoding='utf-8') as f:
                        f.write(conteudo_novo)
                    
                    print(f"✅ {arquivo} atualizado com IP {novo_ip}")
                    
            except Exception as e:
                print(f"⚠️ Erro ao atualizar {arquivo}: {e}")

def main():
    localizador = LocalizadorCamera()
    
    # Fazer varredura
    cameras = localizador.varredura_completa()
    
    if cameras:
        camera_escolhida = cameras[0]  # Usar a primeira encontrada
        ip_correto = camera_escolhida['ip']
        
        print(f"\n🎯 CÂMERA SELECIONADA: {ip_correto}")
        print(f"📱 Tipo: {camera_escolhida['tipo']}")
        
        # Perguntar se deve atualizar os arquivos
        resposta = input(f"\n❓ Atualizar sistemas com IP {ip_correto}? (s/n): ").lower().strip()
        
        if resposta in ['s', 'sim', 'y', 'yes']:
            localizador.atualizar_sistema(ip_correto)
            print(f"\n✅ SISTEMA ATUALIZADO!")
            print(f"🎯 Novo IP configurado: {ip_correto}")
            print("🚀 Pode executar o sistema normalmente agora!")
        else:
            print(f"\n📝 ANOTAÇÃO: Use o IP {ip_correto} no seu sistema")
    
    print("\n🏁 Localização concluída!")

if __name__ == "__main__":
    main()