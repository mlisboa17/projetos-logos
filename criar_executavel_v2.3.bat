@echo off
echo ═══════════════════════════════════════════════════════════
echo   CRIANDO EXECUTAVEL VerifiK v2.3 - PASTA COMPARTILHADA
echo ═══════════════════════════════════════════════════════════
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo Instale Python 3.x de https://www.python.org/
    pause
    exit /b 1
)

echo ✅ Python encontrado!
echo.

REM Atualizar pip
echo 📦 Atualizando pip...
python -m pip install --upgrade pip --quiet

REM Instalar dependências
echo 📦 Instalando Pillow...
pip install Pillow --quiet

echo 📦 Instalando Requests...
pip install requests --quiet

echo 📦 Instalando OpenCV...
pip install opencv-python --quiet

echo 📦 Instalando PyInstaller...
pip install pyinstaller --quiet

echo.
echo 🔧 Compilando executável...
echo ⏱️  Isso pode levar alguns minutos...
echo.

REM Criar executável
pyinstaller --onefile --windowed --name "VerifiK_ColetaImagens_v2.3_Compartilhado" sistema_coleta_standalone_v2.py

echo.
echo ═══════════════════════════════════════════════════════════
if exist "dist\VerifiK_ColetaImagens_v2.3_Compartilhado.exe" (
    echo ✅ SUCESSO!
    echo.
    echo 📂 Executável criado em: dist\VerifiK_ColetaImagens_v2.3_Compartilhado.exe
    echo.
    echo 📊 Tamanho do arquivo:
    dir "dist\VerifiK_ColetaImagens_v2.3_Compartilhado.exe" | find "VerifiK"
    echo.
    echo 🎉 NOVIDADES v2.3:
    echo    ✅ Exportação para pasta compartilhada (Google Drive/OneDrive)
    echo    ✅ Sincronização automática com a nuvem
    echo    ✅ Detecção automática de pastas sincronizadas
    echo    ✅ Interface responsiva (adapta a qualquer tela)
    echo    ✅ Scrollbar no painel direito
    echo.
    echo 📋 CONFIGURAÇÃO RECOMENDADA:
    echo    1. Instale Google Drive para Desktop
    echo    2. Crie pasta: C:\Users\SEU_NOME\Google Drive\VerifiK
    echo    3. Configure PASTA_EXPORTACAO_DRIVE no código
    echo    4. Recompile este executável
    echo.
    echo 📄 Leia: CONFIGURAR_PASTA_DRIVE.txt para instruções detalhadas
    echo.
) else (
    echo ❌ ERRO ao criar executável!
    echo Verifique as mensagens de erro acima
)
echo ═══════════════════════════════════════════════════════════
pause
