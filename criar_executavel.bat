@echo off
REM ============================================================================
REM   Script de Setup - Sistema de Coleta de Imagens VerifiK
REM   Automatiza todo o processo de instalação e criação do executável
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║    SETUP - Sistema de Coleta de Imagens VerifiK (Standalone)    ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale Python 3.8 ou superior:
    echo https://www.python.org/downloads/
    echo.
    echo Certifique-se de marcar "Add Python to PATH" durante a instalação!
    pause
    exit /b 1
)

echo ✓ Python encontrado!
python --version
echo.

REM Atualizar pip
echo ⏳ Atualizando pip...
python -m pip install --upgrade pip --quiet
echo ✓ Pip atualizado!
echo.

REM Instalar dependências
echo ⏳ Instalando dependências...
echo    - Pillow (manipulação de imagens)
python -m pip install pillow --quiet

echo    - OpenCV (captura de webcam)
python -m pip install opencv-python --quiet

echo    - PyInstaller (criar executável)
python -m pip install pyinstaller --quiet

echo ✓ Todas as dependências instaladas!
echo.

REM Criar executável
echo ⏳ Criando executável...
echo    Isso pode levar alguns minutos...
echo.

python -m PyInstaller ^
    --name=VerifiK_ColetaImagens ^
    --onefile ^
    --windowed ^
    --clean ^
    --noconfirm ^
    --add-data="README_SISTEMA_COLETA.txt;." ^
    sistema_coleta_standalone.py

if errorlevel 1 (
    echo.
    echo ❌ Erro ao criar executável!
    echo Verifique se o arquivo sistema_coleta_standalone.py existe.
    pause
    exit /b 1
)

echo.
echo ══════════════════════════════════════════════════════════════════
echo ✅ EXECUTÁVEL CRIADO COM SUCESSO!
echo ══════════════════════════════════════════════════════════════════
echo.
echo 📁 Localização: dist\VerifiK_ColetaImagens.exe
echo 📦 Tamanho: 
dir dist\VerifiK_ColetaImagens.exe | find "VerifiK"
echo.
echo 📋 PRÓXIMOS PASSOS:
echo ══════════════════════════════════════════════════════════════════
echo.
echo 1. Vá para a pasta: dist\
echo 2. Copie o arquivo: VerifiK_ColetaImagens.exe
echo 3. Cole em um pendrive ou compartilhe via rede
echo 4. Distribua para os funcionários
echo.
echo 💡 IMPORTANTE:
echo    - O executável NÃO precisa de instalação
echo    - Funciona em qualquer Windows 7 ou superior
echo    - Cada máquina terá seus dados locais
echo    - Use a função "Exportar" para sincronizar
echo.
echo ══════════════════════════════════════════════════════════════════
echo.

REM Abrir pasta dist
echo Deseja abrir a pasta com o executável? (S/N)
set /p ABRIR=
if /i "%ABRIR%"=="S" explorer dist

echo.
echo Processo concluído!
pause
