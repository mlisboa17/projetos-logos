@echo off
echo ========================================
echo Instalando Tesseract OCR para Windows
echo ========================================
echo.

echo Verificando se Tesseract ja esta instalado...
where tesseract >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Tesseract ja esta instalado!
    tesseract --version
    goto :install_python
)

echo.
echo [ATENCAO] Tesseract OCR nao encontrado!
echo.
echo Por favor, instale manualmente:
echo 1. Baixe de: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Instale o Tesseract-OCR-w64-setup-5.3.3.exe
echo 3. Adicione ao PATH: C:\Program Files\Tesseract-OCR
echo.
echo Pressione qualquer tecla para abrir o site de download...
pause >nul
start https://github.com/UB-Mannheim/tesseract/wiki
echo.

:install_python
echo.
echo Instalando biblioteca Python pytesseract...
pip install pytesseract pillow opencv-python
echo.

echo ========================================
echo Instalacao concluida!
echo ========================================
echo.
echo IMPORTANTE: Configure o caminho do Tesseract em views_coleta.py:
echo pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
echo.
pause
