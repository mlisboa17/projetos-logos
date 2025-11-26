@echo off
REM ============================================================================
REM   Instalar Pacote de Idioma Português para Tesseract
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║       Instalando Português (por) para Tesseract OCR             ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

set TESSDATA_DIR=C:\Program Files\Tesseract-OCR\tessdata

echo 📁 Diretório tessdata: %TESSDATA_DIR%
echo.

REM Verificar se diretório existe
if not exist "%TESSDATA_DIR%" (
    echo ❌ Diretório tessdata não encontrado!
    echo.
    echo Por favor, verifique se Tesseract está instalado em:
    echo C:\Program Files\Tesseract-OCR\
    pause
    exit /b 1
)

echo 📥 Baixando pacote de idioma português...
echo.

REM Baixar arquivo por.traineddata
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata' -OutFile '%TESSDATA_DIR%\por.traineddata'"

if errorlevel 1 (
    echo.
    echo ❌ Erro ao baixar arquivo!
    echo.
    echo Tente baixar manualmente:
    echo 1. Acesse: https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata
    echo 2. Salve em: %TESSDATA_DIR%\por.traineddata
    pause
    exit /b 1
)

echo.
echo ══════════════════════════════════════════════════════════════════
echo ✅ PORTUGUÊS INSTALADO COM SUCESSO!
echo ══════════════════════════════════════════════════════════════════
echo.
echo 📁 Arquivo: %TESSDATA_DIR%\por.traineddata
echo.

REM Verificar se arquivo foi criado
if exist "%TESSDATA_DIR%\por.traineddata" (
    echo 📊 Tamanho do arquivo:
    dir "%TESSDATA_DIR%\por.traineddata" | find "por.traineddata"
    echo.
    echo ✓ Instalação verificada!
) else (
    echo ❌ Arquivo não encontrado após download
)

echo.
echo 🔧 Para testar:
echo    python manage.py shell
echo    ^>^>^> from transcricao_caixa.ocr_processor import testar_tesseract
echo    ^>^>^> testar_tesseract()
echo.
pause
