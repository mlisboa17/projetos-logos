#!/bin/bash
# ============================================================================
#   Script de Setup - Sistema de Coleta de Imagens VerifiK
#   Para Linux/Mac - Automatiza instalação e criação do executável
# ============================================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║    SETUP - Sistema de Coleta de Imagens VerifiK (Standalone)    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python não encontrado!"
    echo ""
    echo "Por favor, instale Python 3.8 ou superior:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-tk"
    echo "  Fedora: sudo dnf install python3 python3-pip python3-tkinter"
    echo "  Mac: brew install python-tk"
    exit 1
fi

echo "✓ Python encontrado!"
python3 --version
echo ""

# Atualizar pip
echo "⏳ Atualizando pip..."
python3 -m pip install --upgrade pip --quiet
echo "✓ Pip atualizado!"
echo ""

# Instalar dependências
echo "⏳ Instalando dependências..."
echo "   - Pillow (manipulação de imagens)"
python3 -m pip install pillow --quiet

echo "   - OpenCV (captura de webcam)"
python3 -m pip install opencv-python --quiet

echo "   - PyInstaller (criar executável)"
python3 -m pip install pyinstaller --quiet

echo "✓ Todas as dependências instaladas!"
echo ""

# Criar executável
echo "⏳ Criando executável..."
echo "   Isso pode levar alguns minutos..."
echo ""

python3 -m PyInstaller \
    --name=VerifiK_ColetaImagens \
    --onefile \
    --windowed \
    --clean \
    --noconfirm \
    --add-data="README_SISTEMA_COLETA.txt:." \
    sistema_coleta_standalone.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erro ao criar executável!"
    echo "Verifique se o arquivo sistema_coleta_standalone.py existe."
    exit 1
fi

echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "✅ EXECUTÁVEL CRIADO COM SUCESSO!"
echo "══════════════════════════════════════════════════════════════════"
echo ""
echo "📁 Localização: dist/VerifiK_ColetaImagens"
echo "📦 Tamanho: $(du -h dist/VerifiK_ColetaImagens | cut -f1)"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "══════════════════════════════════════════════════════════════════"
echo ""
echo "1. Vá para a pasta: dist/"
echo "2. Copie o arquivo: VerifiK_ColetaImagens"
echo "3. Distribua para os usuários"
echo ""
echo "💡 IMPORTANTE:"
echo "   - O executável NÃO precisa de instalação"
echo "   - Funciona em Linux com interface gráfica"
echo "   - Cada máquina terá seus dados locais"
echo "   - Use a função 'Exportar' para sincronizar"
echo ""
echo "══════════════════════════════════════════════════════════════════"
echo ""
echo "Processo concluído!"
