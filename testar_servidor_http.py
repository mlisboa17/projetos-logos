"""
Teste direto do servidor HTTP local
"""
import requests

URL_SERVIDOR = "http://192.168.68.102:8080/banco"

print("="*70)
print("TESTANDO SERVIDOR HTTP LOCAL")
print("="*70)
print(f"URL: {URL_SERVIDOR}\n")

try:
    response = requests.get(URL_SERVIDOR, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"Content-Length: {len(response.content)} bytes ({len(response.content)/1024/1024:.2f} MB)")
    print(f"Primeiros 20 bytes: {response.content[:20]}")
    
    if response.content.startswith(b'SQLite format 3'):
        print("\n✅ SUCESSO! Arquivo SQLite válido baixado!")
        print(f"\nEste link funciona perfeitamente:")
        print(f'LINK_ONEDRIVE_BANCO = "{URL_SERVIDOR}"')
    else:
        print("\n❌ Arquivo não é SQLite válido")
        
except requests.exceptions.ConnectionError:
    print("❌ ERRO: Não foi possível conectar ao servidor")
    print("Certifique-se que o servidor está rodando")
    print("Execute: python servidor_banco_http.py")
except Exception as e:
    print(f"❌ ERRO: {e}")

print("="*70)
