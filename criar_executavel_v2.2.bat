@echo off
echo ═══════════════════════════════════════════════════════════
echo   CRIANDO EXECUTAVEL VerifiK v2.2 - RESPONSIVO
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
pyinstaller --onefile --windowed --name "VerifiK_ColetaImagens_v2.2_Responsivo" sistema_coleta_standalone_v2.py

echo.
echo ═══════════════════════════════════════════════════════════
if exist "dist\VerifiK_ColetaImagens_v2.2_Responsivo.exe" (
    echo ✅ SUCESSO!
    echo.
    echo 📂 Executável criado em: dist\VerifiK_ColetaImagens_v2.2_Responsivo.exe
    echo.
    echo 📊 Tamanho do arquivo:
    dir "dist\VerifiK_ColetaImagens_v2.2_Responsivo.exe" | find "VerifiK"
    echo.
    echo 🎉 NOVIDADES v2.2:
    echo    ✅ Interface responsiva - adapta a qualquer resolução
    echo    ✅ Janela centralizada automaticamente
    echo    ✅ Scrollbar no painel direito para telas pequenas
    echo    ✅ Larguras mínimas garantidas
    echo    ✅ Funciona em monitores 1366x768 ou maiores
    echo.
    echo 📋 TESTE EM OUTRA MÁQUINA:
    echo    1. Copie o arquivo .exe para outro computador
    echo    2. Execute direto (sem instalação)
    echo    3. Todos os painéis devem aparecer completos
    echo.
) else (
    echo ❌ ERRO ao criar executável!
    echo Verifique as mensagens de erro acima
)
echo ═══════════════════════════════════════════════════════════
pause
