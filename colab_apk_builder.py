"""
NOTEBOOK GOOGLE COLAB - VerifiK Mobile APK Builder
Execute cada célula em sequência para gerar o APK
"""

# ===== CÉLULA 1: INSTALAÇÃO =====
!apt update
!apt install -y git zip unzip openjdk-11-jdk python3-pip
!pip3 install --upgrade pip
!pip3 install buildozer cython kivy[base] pyjnius plyer

# Configurar JAVA_HOME
import os
os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-11-openjdk-amd64'

print("✅ Ambiente configurado com sucesso!")

# ===== CÉLULA 2: UPLOAD DOS ARQUIVOS =====
from google.colab import files
import zipfile
import os

print("📤 Faça upload do pacote de build (pasta verifik_mobile_build_*)")
print("   Comprima a pasta em ZIP antes do upload")

# Upload do arquivo ZIP
uploaded = files.upload()

# Extrair ZIP
for filename in uploaded.keys():
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall('.')
    print(f"✅ Arquivos extraídos de {filename}")

# Listar arquivos
!ls -la

# ===== CÉLULA 3: CONFIGURAÇÃO ANDROID SDK =====
# Baixar Android SDK
!wget -q https://dl.google.com/android/repository/commandlinetools-linux-7583922_latest.zip
!unzip -q commandlinetools-linux-7583922_latest.zip
!mkdir -p /opt/android-sdk/cmdline-tools
!mv cmdline-tools /opt/android-sdk/cmdline-tools/latest

# Configurar variáveis
import os
os.environ['ANDROID_HOME'] = '/opt/android-sdk'
os.environ['PATH'] = f"{os.environ['PATH']}:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools"

# Aceitar licenças
!yes | /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager --licenses

print("✅ Android SDK configurado!")

# ===== CÉLULA 4: BUILD DO APK =====
import os

# Encontrar pasta do projeto
project_dirs = [d for d in os.listdir('.') if d.startswith('verifik_mobile_build_')]
if project_dirs:
    project_dir = project_dirs[0]
    print(f"📁 Entrando na pasta: {project_dir}")
    os.chdir(project_dir)
else:
    print("❌ Pasta do projeto não encontrada!")

# Limpar builds anteriores
!rm -rf .buildozer bin

# Inicializar buildozer
!buildozer init

# Compilar APK
print("🚀 Iniciando compilação do APK...")
print("⏱️ Isso pode levar 15-20 minutos...")
!buildozer android debug

# Verificar resultado
import glob
apk_files = glob.glob("bin/*.apk")
if apk_files:
    apk_file = apk_files[0]
    print(f"✅ APK compilado: {apk_file}")
    
    # Informações do APK
    import os
    size_mb = os.path.getsize(apk_file) / (1024*1024)
    print(f"📱 Tamanho: {size_mb:.1f} MB")
    
else:
    print("❌ Erro na compilação")

# ===== CÉLULA 5: DOWNLOAD DO APK =====
from google.colab import files
import glob
import os

# Encontrar APK
apk_files = glob.glob("bin/*.apk")
if apk_files:
    apk_file = apk_files[0]
    
    # Renomear para nome mais amigável
    new_name = "VerifiK_Mobile_v3.0.0.apk"
    os.rename(apk_file, new_name)
    
    print(f"📲 Baixando: {new_name}")
    files.download(new_name)
    
    print("🎉 APK pronto para instalação no Android!")
    print("")
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Transfira o APK para o celular")
    print("2. Habilite 'Fontes desconhecidas' nas configurações")
    print("3. Instale o APK")
    print("4. Abra o VerifiK Mobile")
    print("5. Teste a coleta de imagens!")
    
else:
    print("❌ APK não encontrado - verificar erros de compilação")

# ===== INFORMAÇÕES FINAIS =====
print("")
print("📱 VERIFIK MOBILE - ESPECIFICAÇÕES")
print("="*40)
print("📦 Versão: 3.0.0")
print("🤖 Android: 4.1+ (API 16+)")
print("💾 Tamanho: ~20-30 MB")
print("🏪 Produtos: 176 sincronizados")
print("📷 Câmera: Integrada")
print("💾 Banco: SQLite local")
print("📤 Export: JSON")
print("")
print("🎯 FUNCIONALIDADES:")
print("- Seleção de produtos (176 itens)")
print("- Captura de câmera nativa")
print("- Marcação touch na imagem")
print("- Anotações de texto")
print("- Salvamento local")
print("- Exportação JSON")
print("- Sincronização offline")