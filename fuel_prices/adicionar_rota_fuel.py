"""
Script para adicionar automaticamente a rota do fuel_prices no urls.py principal
"""
import os
import sys

# Caminho do arquivo urls.py principal (LOGOS)
URLS_FILE = r"c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\logos\urls.py"

# Linha a ser adicionada
ROTA_FUEL = "    path('fuel/', include('fuel_prices.urls')),"

def adicionar_rota():
    """Adiciona rota do fuel no urls.py principal"""
    
    # Verificar se arquivo existe
    if not os.path.exists(URLS_FILE):
        print(f"❌ Arquivo não encontrado: {URLS_FILE}")
        print("\n🔍 Procurando arquivo urls.py...")
        
        # Tentar encontrar o arquivo
        base_dir = r"c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus"
        for root, dirs, files in os.walk(base_dir):
            if 'urls.py' in files and 'fuel_prices' not in root and 'migrations' not in root:
                print(f"✓ Encontrado: {os.path.join(root, 'urls.py')}")
        
        sys.exit(1)
    
    print(f"📂 Lendo arquivo: {URLS_FILE}")
    
    # Ler arquivo
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    # Verificar se já existe
    conteudo = ''.join(linhas)
    if "fuel_prices.urls" in conteudo:
        print("✅ Rota do fuel_prices já existe no arquivo!")
        print("\n📋 Conteúdo atual do urlpatterns:")
        em_urlpatterns = False
        for linha in linhas:
            if 'urlpatterns' in linha:
                em_urlpatterns = True
            if em_urlpatterns:
                print(linha.rstrip())
            if em_urlpatterns and ']' in linha:
                break
        return
    
    # Verificar se tem 'include' no import
    tem_include = False
    for i, linha in enumerate(linhas):
        if 'from django.urls import' in linha and 'include' in linha:
            tem_include = True
            break
        elif 'from django.urls import' in linha and 'include' not in linha:
            # Adicionar include ao import
            linhas[i] = linha.rstrip().rstrip(')').rstrip() + ', include)\n'
            tem_include = True
            print("✓ Adicionado 'include' ao import")
            break
    
    if not tem_include:
        # Adicionar import completo
        for i, linha in enumerate(linhas):
            if 'from django.contrib import admin' in linha:
                linhas.insert(i + 1, "from django.urls import path, include\n")
                print("✓ Adicionado import: from django.urls import path, include")
                break
    
    # Encontrar urlpatterns e adicionar rota
    adicionado = False
    for i, linha in enumerate(linhas):
        if 'urlpatterns = [' in linha or 'urlpatterns=[' in linha:
            # Encontrar onde inserir (antes do último ']')
            nivel = 0
            pos_inserir = i + 1
            
            for j in range(i, len(linhas)):
                if '[' in linhas[j]:
                    nivel += linhas[j].count('[')
                if ']' in linhas[j]:
                    nivel -= linhas[j].count(']')
                    if nivel == 0:
                        pos_inserir = j
                        break
            
            # Inserir antes do último ']'
            linhas.insert(pos_inserir, f"{ROTA_FUEL}\n")
            adicionado = True
            print(f"✓ Rota adicionada na linha {pos_inserir + 1}")
            break
    
    if not adicionado:
        print("❌ Não foi possível encontrar 'urlpatterns' no arquivo")
        sys.exit(1)
    
    # Salvar arquivo
    with open(URLS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    
    print(f"\n✅ Arquivo atualizado com sucesso!")
    print(f"\n📋 Nova estrutura do urlpatterns:")
    
    em_urlpatterns = False
    for linha in linhas:
        if 'urlpatterns' in linha:
            em_urlpatterns = True
        if em_urlpatterns:
            print(linha.rstrip())
        if em_urlpatterns and ']' in linha:
            break
    
    print("\n🎯 Acesso disponível em:")
    print("   http://localhost:8000/fuel/")
    print("   http://localhost:8000/fuel/por-posto/")
    print("\n⚠️  IMPORTANTE: Se quiser acesso via /logus/fuel/, edite manualmente")
    print("   conforme instruções no arquivo CONFIG_ACESSO.txt")

if __name__ == '__main__':
    try:
        adicionar_rota()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
