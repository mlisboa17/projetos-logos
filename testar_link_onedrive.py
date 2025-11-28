"""
Script para testar o download do banco de dados do OneDrive
"""
import requests

# Link do OneDrive (mesmo do sistema)
LINK_ONEDRIVE_BANCO = "https://1drv.ms/u/c/4b131179ac59ef39/IQB1iIBzxE3-SJ899VUuBbzzAfIfOQD1btRyz0MV6PHK0o8?e=YY7jul"

def testar_link(url, metodo):
    """Testa um método de download"""
    print(f"\n{'='*70}")
    print(f"TESTANDO: {metodo}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, timeout=30, allow_redirects=True)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        # Verificar primeiros bytes
        primeiros_bytes = response.content[:20]
        print(f"Primeiros bytes: {primeiros_bytes}")
        
        # Verificar se é SQLite
        if response.content.startswith(b'SQLite format 3'):
            print("✅ ARQUIVO SQLITE VÁLIDO!")
            return True
        else:
            print("❌ NÃO É UM ARQUIVO SQLITE")
            # Mostrar início do conteúdo se for texto
            if 'text' in response.headers.get('Content-Type', ''):
                print(f"Início do conteúdo:\n{response.content[:500].decode('utf-8', errors='ignore')}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

# Testar diferentes URLs
link = LINK_ONEDRIVE_BANCO

print("\n" + "="*70)
print("TESTE DE DOWNLOAD DO BANCO DE DADOS DO ONEDRIVE")
print("="*70)

# Método 1: Link com &download=1
if '?e=' in link:
    base_link = link.split('?')[0]
    url1 = base_link + '?download=1'
    testar_link(url1, "Método 1: Base URL + ?download=1")

# Método 2: API OneDrive
if '/u/c/' in link:
    parts = link.split('/u/c/')
    if len(parts) > 1:
        rest = parts[1].split('?')[0]
        ids = rest.split('/')
        if len(ids) >= 2:
            encoded_id = ids[0] + '!' + ids[1]
            url2 = f"https://api.onedrive.com/v1.0/shares/u!{encoded_id}/root/content"
            testar_link(url2, "Método 2: OneDrive API")

# Método 3: Link original
testar_link(link, "Método 3: Link original completo")

print("\n" + "="*70)
print("TESTE CONCLUÍDO")
print("="*70)
print("\nSe nenhum método funcionou, você precisa:")
print("1. Abrir o OneDrive no navegador")
print("2. Clicar com botão direito no arquivo db.sqlite3")
print("3. Selecionar 'Compartilhar'")
print("4. Marcar 'Qualquer pessoa com o link pode EXIBIR'")
print("5. Clicar em '...' (mais opções)")
print("6. Selecionar 'Mais configurações de compartilhamento'")
print("7. Certificar que está marcado 'Permitir download'")
print("="*70)
