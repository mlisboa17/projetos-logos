@echo off
chcp 65001 >nul
color 0B

echo.
echo ╔═════════════════════════════════════════════════════════════════════════════╗
echo ║    SETUP - Sistema de Coleta v2.1 - Interface Aprimorada                   ║
echo ╚═════════════════════════════════════════════════════════════════════════════╝
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado! Instale Python 3.x primeiro.
    pause
    exit /b 1
)

echo ✅ Python encontrado!
python --version
echo.

REM Atualizar pip
echo 🔧 Atualizando pip...
python -m pip install --upgrade pip --quiet
echo ✅ Pip atualizado!
echo.

REM Instalar dependências
echo 🔧 Instalando dependências...
echo    - Pillow (manipulação de imagens)
echo    - Requests (download do banco Google Drive)
echo    - OpenCV (webcam)
echo    - PyInstaller (criar executável)
python -m pip install Pillow requests opencv-python pyinstaller --quiet
echo ✅ Todas as dependências instaladas!
echo.

REM Criar executável
echo 🔧 Criando executável v2.1...
echo    Isso pode levar alguns minutos...
echo.

pyinstaller --onefile --windowed --name "VerifiK_ColetaImagens_v2.1" sistema_coleta_standalone_v2.py

if errorlevel 1 (
    echo.
    echo ❌ Erro ao criar executável!
    pause
    exit /b 1
)

echo.
echo ═════════════════════════════════════════════════════════════════════════════
echo ✅ EXECUTÁVEL v2.1 CRIADO COM SUCESSO!
echo ═════════════════════════════════════════════════════════════════════════════
echo.
echo 📍 Localização: dist\VerifiK_ColetaImagens_v2.1.exe
echo 📊 Tamanho:
dir dist\VerifiK_ColetaImagens_v2.1.exe | find "VerifiK"
echo.
echo 📋 PRÓXIMOS PASSOS:
echo ═════════════════════════════════════════════════════════════════════════════
echo 1. Vá para a pasta: dist\
echo 2. Copie o arquivo: VerifiK_ColetaImagens_v2.1.exe
echo 3. Cole em um pendrive ou compartilhe via rede
echo 4. Distribua para os funcionários
echo.
echo ✨ NOVIDADES V2.1:
echo    - Área de foto MAIOR (800px mínimo)
echo    - Cores VIBRANTES nos retângulos (15 cores distintas)
echo    - Labels com fundo colorido e texto branco
echo    - Confirmação ao fechar com dados não salvos
echo    - Sincronização AUTOMÁTICA no início
echo    - Interface otimizada
echo.
echo ═════════════════════════════════════════════════════════════════════════════
echo.
set /p ABRIR="Deseja abrir a pasta com o executável? (S/N) "
if /i "%ABRIR%"=="S" explorer dist

echo.
echo Processo concluído!
pause
