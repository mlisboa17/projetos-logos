#!/usr/bin/env python3
"""
Diagnóstico Completo da Câmera Intelbras
Testa todas as possibilidades de conexão
"""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import socket
import time

def testar_conectividade_basica():
    """Testa conectividade básica"""
    print("🔍 TESTE 1: Conectividade Básica")
    print("=" * 50)
    
    ip = "192.168.5.136"
    portas = [80, 554, 8080, 443]
    
    for porta in portas:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            resultado = sock.connect_ex((ip, porta))
            sock.close()
            
            if resultado == 0:
                print(f"✅ Porta {porta}: ABERTA")
            else:
                print(f"❌ Porta {porta}: FECHADA")
        except Exception as e:
            print(f"❌ Porta {porta}: ERRO - {e}")
    
    print()

def testar_ping():
    """Testa ping"""
    print("🔍 TESTE 2: Ping")
    print("=" * 50)
    
    import subprocess
    import sys
    
    try:
        if sys.platform == "win32":
            result = subprocess.run(["ping", "-n", "3", "192.168.5.136"], 
                                  capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(["ping", "-c", "3", "192.168.5.136"], 
                                  capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ PING: Câmera responde")
            print(f"Output: {result.stdout}")
        else:
            print("❌ PING: Câmera não responde")
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ PING: Erro - {e}")
    
    print()

def testar_urls_http():
    """Testa URLs HTTP detalhadamente"""
    print("🔍 TESTE 3: URLs HTTP Detalhado")
    print("=" * 50)
    
    ip = "192.168.5.136"
    username = "admin"
    password = "C@sa3863"
    
    # URLs mais básicas primeiro
    urls_teste = [
        # Básicas
        f"http://{ip}/",
        f"http://{ip}/cgi-bin/",
        
        # Snapshot APIs
        f"http://{ip}/cgi-bin/snapshot.cgi",
        f"http://{ip}/cgi-bin/snapshot.cgi?channel=1",
        f"http://{ip}/cgi-bin/snapshot.cgi?channel=1&subtype=0",
        f"http://{ip}/cgi-bin/snapshot.cgi?chn=1&u={username}&p={password}",
        
        # MagicBox
        f"http://{ip}/cgi-bin/magicBox.cgi?action=getSnapshot",
        f"http://{ip}/cgi-bin/magicBox.cgi?action=getSnapshot&channel=1&subtype=0",
        f"http://{ip}/cgi-bin/magicBox.cgi?action=getDeviceType",
        
        # Outros formatos
        f"http://{ip}/Streaming/Channels/101/picture",
        f"http://{ip}/Streaming/Channels/1/picture", 
        f"http://{ip}/cgi-bin/hi3510/snap.cgi?&-usr={username}&-pwd={password}",
        
        # Config Manager
        f"http://{ip}/cgi-bin/configManager.cgi?action=attachFileProc&name=Snap&channel=1&subtype=0",
        
        # ONVIF
        f"http://{ip}/onvif-http/snapshot?Profile_1",
    ]
    
    session = requests.Session()
    auth_methods = [
        ("Basic Auth", HTTPBasicAuth(username, password)),
        ("Digest Auth", HTTPDigestAuth(username, password)),
        ("No Auth", None)
    ]
    
    for url in urls_teste:
        print(f"\n🔗 Testando: {url}")
        
        for auth_name, auth in auth_methods:
            try:
                response = session.get(url, auth=auth, timeout=10)
                
                content_type = response.headers.get('content-type', 'N/A')
                content_length = len(response.content)
                
                print(f"  {auth_name}: Status {response.status_code} | "
                      f"Type: {content_type} | Size: {content_length}b")
                
                # Se parece uma imagem
                if (response.status_code == 200 and 
                    ('image' in content_type.lower() or 'jpeg' in content_type.lower()) and
                    content_length > 2000):
                    
                    print(f"  ✅ SUCESSO! Imagem válida encontrada!")
                    print(f"     URL: {url}")
                    print(f"     Auth: {auth_name}")
                    print(f"     Size: {content_length} bytes")
                    
                    # Salvar amostra para verificação
                    with open("teste_camera_sample.jpg", "wb") as f:
                        f.write(response.content)
                    print(f"     Amostra salva: teste_camera_sample.jpg")
                    return True
                    
            except requests.exceptions.Timeout:
                print(f"  {auth_name}: TIMEOUT")
            except requests.exceptions.ConnectionError:
                print(f"  {auth_name}: CONNECTION ERROR")
            except Exception as e:
                print(f"  {auth_name}: ERRO - {str(e)[:50]}")
    
    return False

def testar_credenciais():
    """Testa diferentes combinações de credenciais"""
    print("\n🔍 TESTE 4: Credenciais Alternativas")  
    print("=" * 50)
    
    ip = "192.168.5.136"
    url_base = f"http://{ip}/cgi-bin/magicBox.cgi?action=getDeviceType"
    
    credenciais = [
        ("admin", "C@sa3863"),
        ("admin", "admin"),
        ("admin", ""),
        ("", ""),
        ("user", "user"),
        ("guest", "guest"),
        ("intelbras", "intelbras"),
    ]
    
    for user, pwd in credenciais:
        try:
            response = requests.get(
                url_base, 
                auth=HTTPBasicAuth(user, pwd), 
                timeout=5
            )
            
            print(f"User: '{user}' | Pass: '{pwd}' | Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ CREDENCIAIS VÁLIDAS: {user}/{pwd}")
                print(f"Resposta: {response.text[:100]}")
                return user, pwd
                
        except Exception as e:
            print(f"User: '{user}' | Pass: '{pwd}' | ERRO: {str(e)[:30]}")
    
    return None, None

def verificar_rede_local():
    """Verifica configuração de rede local"""
    print("\n🔍 TESTE 5: Configuração de Rede")
    print("=" * 50)
    
    try:
        import subprocess
        import re
        
        # Pegar configuração de rede (Windows)
        result = subprocess.run(["ipconfig"], capture_output=True, text=True)
        
        # Procurar adaptadores ativos
        lines = result.stdout.split('\n')
        current_adapter = ""
        
        for line in lines:
            if "Adaptador" in line or "adapter" in line.lower():
                current_adapter = line.strip()
                print(f"\n📡 {current_adapter}")
                
            if "IPv4" in line or "IP Address" in line:
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    local_ip = ip_match.group(1)
                    print(f"   IP Local: {local_ip}")
                    
                    # Verificar se está na mesma rede da câmera
                    camera_network = "192.168.5"
                    local_network = ".".join(local_ip.split(".")[:3])
                    
                    if local_network == camera_network:
                        print(f"   ✅ Mesma rede da câmera ({camera_network}.x)")
                    else:
                        print(f"   ⚠️  Rede diferente! Local: {local_network}.x | Câmera: {camera_network}.x")
        
    except Exception as e:
        print(f"❌ Erro ao verificar rede: {e}")

def main():
    print("🎯 DIAGNÓSTICO COMPLETO - CÂMERA INTELBRAS")
    print("🎯 IP: 192.168.5.136 | User: admin | Pass: C@sa3863")
    print("=" * 60)
    
    # Testes sequenciais
    testar_conectividade_basica()
    testar_ping()
    verificar_rede_local()
    
    # Teste principal de URLs
    if testar_urls_http():
        print("\n🎉 SUCESSO! Conexão estabelecida com a câmera!")
        print("✅ Uma imagem de amostra foi salva como 'teste_camera_sample.jpg'")
    else:
        print("\n❌ FALHA! Não foi possível conectar à câmera")
        print("\n🔧 Possíveis soluções:")
        print("1. Verificar se a câmera está ligada")
        print("2. Confirmar IP da câmera (192.168.5.136)")  
        print("3. Testar credenciais diferentes")
        print("4. Verificar se está na mesma rede")
        print("5. Tentar acessar pelo navegador: http://192.168.5.136")
        
        # Teste de credenciais alternativas
        user, pwd = testar_credenciais()
        if user:
            print(f"\n✅ Credenciais alternativas funcionam: {user}/{pwd}")

if __name__ == "__main__":
    main()