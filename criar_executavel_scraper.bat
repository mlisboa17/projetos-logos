@echo off
echo ============================================
echo  CRIANDO EXECUTAVEL DO SCRAPER VIBRA
echo ============================================
echo.

REM Verificar se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale o Python primeiro.
    pause
    exit /b 1
)

echo [1/6] Verificando Python...
echo ✓ Python encontrado

REM Verificar se pip está disponível
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: pip nao encontrado.
    pause
    exit /b 1
)

echo [2/6] Verificando pip...
echo ✓ pip encontrado

REM Instalar PyInstaller se necessário
echo [3/6] Verificando PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo   Instalando PyInstaller...
    pip install pyinstaller
) else (
    echo ✓ PyInstaller já está instalado
)

REM Instalar dependências do scraper
echo [4/6] Instalando dependências...
pip install -r requirements_scraper.txt

REM Instalar browsers do Playwright
echo [5/6] Instalando browsers do Playwright...
python -m playwright install chromium

REM Gerar executável
echo [6/6] Gerando executável...
pyinstaller scraper_vibra.spec --clean --noconfirm

REM Verificar se foi criado
if exist "dist\ScraperVibra.exe" (
    echo.
    echo ============================================
    echo   ✅ EXECUTAVEL CRIADO COM SUCESSO!
    echo ============================================
    echo.
    echo 📁 Localização: dist\ScraperVibra.exe
    echo 📏 Tamanho: 
    for %%A in ("dist\ScraperVibra.exe") do echo    %%~zA bytes
    echo.
    echo 🚀 COMO USAR:
    echo    1. Certifique-se que o sistema principal está rodando
    echo    2. Execute: dist\ScraperVibra.exe
    echo    3. Siga as instruções na tela
    echo.
    echo 💡 DICA: Copie o arquivo .exe para qualquer pasta
    echo    O executável é completamente independente!
) else (
    echo.
    echo ❌ ERRO: Executável não foi criado
    echo    Verifique os erros acima
)

echo.
pause