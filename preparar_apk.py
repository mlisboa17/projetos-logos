#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Preparador de APK Android - VerifiK Mobile
Prepara todos os arquivos necessários para build do APK
"""

import os
import shutil
import json
from datetime import datetime

def verificar_arquivos_build():
    """Verifica se todos os arquivos necessários estão prontos"""
    
    print("🔍 VERIFICANDO ARQUIVOS PARA BUILD APK\n")
    
    arquivos_necessarios = {
        'main.py': 'App principal Kivy',
        'verifik.kv': 'Interface mobile',
        'buildozer.spec': 'Configuração Android', 
        'mobile_simulator.db': 'Base de produtos sincronizada',
        'build_android.sh': 'Script de build Linux',
        'compilar_apk_colab.txt': 'Instruções Google Colab'
    }
    
    arquivos_ok = []
    arquivos_faltando = []
    
    for arquivo, descricao in arquivos_necessarios.items():
        if os.path.exists(arquivo):
            tamanho = os.path.getsize(arquivo)
            print(f"✅ {arquivo:<25} - {descricao} ({tamanho} bytes)")
            arquivos_ok.append(arquivo)
        else:
            print(f"❌ {arquivo:<25} - {descricao} (FALTANDO)")
            arquivos_faltando.append(arquivo)
    
    print(f"\n📊 RESUMO:")
    print(f"   ✅ Arquivos OK: {len(arquivos_ok)}")
    print(f"   ❌ Arquivos faltando: {len(arquivos_faltando)}")
    
    return len(arquivos_faltando) == 0

def criar_pacote_build():
    """Cria pacote para build do APK"""
    
    if not verificar_arquivos_build():
        print("\n❌ Não é possível criar pacote - arquivos faltando!")
        return False
    
    print("\n📦 CRIANDO PACOTE PARA BUILD...\n")
    
    # Criar diretório do pacote
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pasta_build = f"verifik_mobile_build_{timestamp}"
    
    if os.path.exists(pasta_build):
        shutil.rmtree(pasta_build)
    
    os.makedirs(pasta_build)
    
    # Arquivos essenciais para build
    arquivos_build = [
        'main.py',
        'verifik.kv', 
        'buildozer.spec',
        'mobile_simulator.db'
    ]
    
    # Copiar arquivos
    for arquivo in arquivos_build:
        origem = arquivo
        destino = os.path.join(pasta_build, arquivo)
        shutil.copy2(origem, destino)
        print(f"📄 Copiado: {arquivo}")
    
    # Criar README para o build
    readme_content = f"""# VerifiK Mobile - Build Package
    
## 📱 COMO COMPILAR O APK

### Opção 1: Google Colab (Recomendado)
1. Abra: https://colab.research.google.com
2. Faça upload destes arquivos
3. Execute o notebook de build
4. Download do APK gerado

### Opção 2: Linux/WSL
```bash
# Instalar dependências
sudo apt update
sudo apt install python3-pip git
pip3 install buildozer cython

# Compilar APK
buildozer android debug
```

## 📋 Arquivos inclusos:
- main.py (App Kivy principal)
- verifik.kv (Interface mobile)
- buildozer.spec (Configuração Android)
- mobile_simulator.db (Base com 176 produtos)

## 🎯 Resultado esperado:
- APK: bin/verifik_coleta-3.0.0-armeabi-v7a-debug.apk
- Tamanho: ~20-30 MB
- Compatibilidade: Android 4.1+

Criado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
"""
    
    with open(os.path.join(pasta_build, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Criar script de build rápido
    script_build = """#!/bin/bash

echo "Compilando VerifiK Mobile APK..."
echo "Versao: 3.0.0"
echo ""

# Verificar buildozer
if ! command -v buildozer &> /dev/null; then
    echo "Buildozer nao encontrado. Instalando..."
    pip3 install buildozer cython
fi

# Limpar builds anteriores
echo "Limpando builds anteriores..."
rm -rf .buildozer
rm -rf bin

# Compilar APK
echo "Iniciando compilacao..."
buildozer android debug

# Verificar resultado
if [ -f "bin/*.apk" ]; then
    echo "APK compilado com sucesso!"
    ls -la bin/
else
    echo "Erro na compilacao"
    exit 1
fi

echo ""
echo "VerifiK Mobile APK esta pronto!"
echo "Instale no Android e teste a coleta de imagens."
"""
    
    with open(os.path.join(pasta_build, 'build_apk.sh'), 'w', encoding='utf-8') as f:
        f.write(script_build)
    
    # Tornar executável
    os.chmod(os.path.join(pasta_build, 'build_apk.sh'), 0o755)
    
    print(f"\n✅ PACOTE CRIADO: {pasta_build}")
    print(f"📁 Tamanho total: {get_folder_size(pasta_build):.1f} MB")
    
    return True

def get_folder_size(folder_path):
    """Calcula tamanho da pasta em MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)

def mostrar_opcoes_build():
    """Mostra opções para build do APK"""
    
    print("\n" + "="*60)
    print("🚀 OPÇÕES PARA GERAR APK ANDROID")
    print("="*60)
    
    print("""
📱 OPÇÃO 1: GOOGLE COLAB (Mais Fácil)
   1. Vá para: https://colab.research.google.com
   2. Crie novo notebook
   3. Faça upload do pacote de build
   4. Execute células de instalação e build
   5. Download do APK gerado
   ⏱️  Tempo: 15-20 minutos
   
📱 OPÇÃO 2: WSL LINUX (Mais Rápido)  
   1. Instale WSL: wsl --install
   2. Entre no Ubuntu: wsl
   3. Navegue: cd /mnt/c/Users/mlisb/OneDrive/Desktop/ProjetoLogus
   4. Execute: ./build_apk.sh
   ⏱️  Tempo: 5-10 minutos (após setup)
   
📱 OPÇÃO 3: GITHUB ACTIONS (Automático)
   1. git add . && git commit -m "APK build"
   2. git push origin main  
   3. Aguarde build automático
   4. Download via GitHub Releases
   ⏱️  Tempo: 10-15 minutos
""")

def main():
    """Função principal"""
    print("📱 PREPARADOR DE APK - VerifiK Mobile")
    print("="*50)
    
    # Verificar arquivos
    if verificar_arquivos_build():
        print("\n🎉 Todos os arquivos estão prontos para build!")
        
        # Criar pacote
        if criar_pacote_build():
            mostrar_opcoes_build()
            
            print("\n🎯 PRÓXIMO PASSO:")
            print("   Escolha uma das opções acima para gerar o APK")
            print("   📲 Em ~15 minutos você terá o app no celular!")
        
    else:
        print("\n❌ Alguns arquivos estão faltando.")
        print("   Execute primeiro: python sincronizar_produtos.py")

if __name__ == "__main__":
    main()