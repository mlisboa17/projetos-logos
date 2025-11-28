"""
Testar link do Google Drive
"""
import requests

# Link original (visualização)
link_original = "https://drive.google.com/file/d/1N_eU1mQUJGX-G-RrenApfUM6Nfs0eA8V/view?usp=sharing"

# Extrair ID do arquivo
file_id = "1N_eU1mQUJGX-G-RrenApfUM6Nfs0eA8V"

# Converter para download direto
link_download = f"https://drive.google.com/uc?export=download&id={file_id}"

print("="*70)
print("TESTANDO GOOGLE DRIVE")
print("="*70)
print(f"\n📎 Link original (visualização):")
print(f"   {link_original}")
print(f"\n📥 Link convertido (download direto):")
print(f"   {link_download}")
print("\n" + "="*70)

# Testar download
print("Testando download...")
try:
    response = requests.get(link_download, timeout=30, allow_redirects=True)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"Content-Length: {len(response.content)} bytes ({len(response.content)/1024/1024:.2f} MB)")
    print(f"Primeiros 20 bytes: {response.content[:20]}")
    
    # Verificar se é SQLite
    if response.content.startswith(b'SQLite format 3'):
        print("\n✅ SUCESSO! Arquivo SQLite válido!")
        print(f"\n🎯 Use este link no sistema:")
        print(f'   LINK_ONEDRIVE_BANCO = "{link_download}"')
    else:
        print("\n❌ NÃO é um arquivo SQLite")
        # Verificar se é HTML (página de aviso do Google)
        if b'<html' in response.content[:1000].lower():
            print("\n⚠️ Google Drive retornou HTML")
            print("Possíveis causas:")
            print("1. Arquivo muito grande (>100MB) - Google pede confirmação")
            print("2. Link não está público")
            print("3. Necessita autenticação")
            
except Exception as e:
    print(f"\n❌ Erro: {e}")

print("="*70)
