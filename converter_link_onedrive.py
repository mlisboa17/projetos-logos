"""
Converte link de compartilhamento do OneDrive para link de download direto
"""
import base64
import urllib.parse

def converter_link_onedrive(link_compartilhamento):
    """
    Converte link de compartilhamento do OneDrive para download direto
    
    Entrada: https://1drv.ms/u/c/xxx/xxx?e=xxx
    Saída: https://api.onedrive.com/v1.0/shares/u!xxx/root/content
    """
    print(f"Link original: {link_compartilhamento}")
    
    # Codificar o link em base64
    link_bytes = link_compartilhamento.encode('utf-8')
    link_base64 = base64.b64encode(link_bytes).decode('utf-8')
    
    # Remover padding '=' e substituir caracteres
    link_base64 = link_base64.rstrip('=')
    link_base64 = link_base64.replace('/', '_').replace('+', '-')
    
    # Criar URL da API do OneDrive
    download_url = f"https://api.onedrive.com/v1.0/shares/u!{link_base64}/root/content"
    
    print(f"\nLink de download direto:")
    print(download_url)
    
    return download_url

# Testar com o link fornecido
link = "https://1drv.ms/u/c/4b131179ac59ef39/IQB1iIBzxE3-SJ899VUuBbzzAXeJg9ZaBeYd0yF4i7q3NNo?e=0BgSfc"
download_link = converter_link_onedrive(link)

print("\n" + "="*70)
print("Testando o link convertido...")
print("="*70)

import requests

try:
    response = requests.get(download_link, timeout=30, allow_redirects=True)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"Content-Length: {len(response.content)} bytes")
    print(f"Primeiros bytes: {response.content[:20]}")
    
    if response.content.startswith(b'SQLite format 3'):
        print("\n✅ SUCESSO! Link convertido funciona!")
        print(f"\nUse este link no sistema:")
        print(download_link)
    else:
        print("\n❌ Link convertido não funcionou")
        print("O link precisa ter permissão de download público")
        
except Exception as e:
    print(f"\n❌ Erro: {e}")
