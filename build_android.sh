#!/bin/bash

# Script para compilar o VerifiK Mobile para Android
# Versão otimizada para coleta de imagens

echo "🚀 Iniciando compilação do VerifiK Mobile para Android..."
echo "=================================================="

# Verificar se o buildozer está instalado
if ! command -v buildozer &> /dev/null; then
    echo "❌ Buildozer não encontrado!"
    echo "📥 Instalando buildozer..."
    
    # Instalar dependências
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv git zip unzip default-jdk
    
    # Instalar buildozer
    pip3 install --user buildozer
    pip3 install --user cython
    
    echo "✅ Buildozer instalado!"
fi

# Verificar dependências do Android
echo "🔧 Verificando dependências do Android SDK..."

# Criar diretório .buildozer se não existir
mkdir -p ~/.buildozer

# Limpar builds anteriores (opcional)
read -p "🗑️ Deseja limpar builds anteriores? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Limpando builds anteriores..."
    buildozer android clean
fi

# Inicializar buildozer (se necessário)
if [ ! -f "buildozer.spec" ]; then
    echo "📝 Inicializando buildozer.spec..."
    buildozer init
fi

# Compilar versão debug
echo "🔨 Compilando APK de debug..."
buildozer android debug

# Verificar se a compilação foi bem-sucedida
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCESSO! APK compilado com sucesso!"
    echo "=================================================="
    echo "📱 Arquivo gerado: bin/VerifiK_Mobile___Coleta_de_Imagens-3.0.0-armeabi-v7a_arm64-v8a-debug.apk"
    echo ""
    echo "📋 Próximos passos:"
    echo "1. Copie o APK para seu dispositivo Android"
    echo "2. Ative 'Fontes desconhecidas' nas configurações"
    echo "3. Instale o APK"
    echo ""
    echo "🔧 Para compilar versão release (assinada):"
    echo "   buildozer android release"
    echo ""
    
    # Mostrar tamanho do arquivo
    APK_FILE=$(find bin/ -name "*.apk" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -f "$APK_FILE" ]; then
        APK_SIZE=$(du -h "$APK_FILE" | cut -f1)
        echo "📦 Tamanho do APK: $APK_SIZE"
    fi
    
else
    echo ""
    echo "❌ ERRO na compilação!"
    echo "=================================================="
    echo "🔍 Verifique os logs acima para identificar o problema."
    echo ""
    echo "💡 Possíveis soluções:"
    echo "1. buildozer android clean"
    echo "2. Verificar se todas as dependências estão instaladas"
    echo "3. Verificar conexão com internet"
    echo "4. Verificar espaço em disco"
    echo ""
fi

echo "🏁 Processo finalizado."