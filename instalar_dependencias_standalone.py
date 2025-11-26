# Instalação de dependências para o sistema standalone
# Execute este arquivo antes de criar o executável

import subprocess
import sys

print("╔══════════════════════════════════════════════════════════════╗")
print("║   INSTALAÇÃO - Sistema de Coleta de Imagens (Standalone)    ║")
print("╚══════════════════════════════════════════════════════════════╝")
print()

pacotes = [
    'pillow',           # Manipulação de imagens
    'opencv-python',    # Captura de webcam
    'pyinstaller',      # Criar executável
]

print("📦 Instalando pacotes necessários...")
print()

for pacote in pacotes:
    print(f"⏳ Instalando {pacote}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pacote])
        print(f"   ✓ {pacote} instalado com sucesso!")
    except:
        print(f"   ⚠️ Erro ao instalar {pacote}")
    print()

print("=" * 60)
print("✅ Instalação concluída!")
print()
print("📋 Próximos passos:")
print("   1. Execute: python criar_executavel_coleta.py")
print("   2. O executável será criado na pasta 'dist'")
print("   3. Copie VerifiK_ColetaImagens.exe para um pendrive")
print("   4. Distribua para os funcionários!")
