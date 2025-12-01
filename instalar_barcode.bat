@echo off
echo ========================================
echo  INSTALACAO DO LEITOR DE CODIGO DE BARRAS
echo ========================================
echo.

echo [1/3] Instalando pyzbar (Python)...
pip install pyzbar
echo.

echo [2/3] Baixando Zbar DLL para Windows...
echo.
echo IMPORTANTE: Baixe o arquivo de:
echo https://sourceforge.net/projects/zbar/files/zbar/0.10/zbar-0.10-setup.exe/download
echo.
echo OU use chocolatey:
echo choco install zbar
echo.
start https://sourceforge.net/projects/zbar/files/zbar/0.10/zbar-0.10-setup.exe/download
echo.

echo [3/3] Verificando instalacao...
python -c "from pyzbar.pyzbar import decode; print('✓ pyzbar instalado com sucesso!')" 2>nul
if errorlevel 1 (
    echo ✗ pyzbar precisa do Zbar instalado no sistema
    echo.
    echo SOLUCAO:
    echo 1. Execute o instalador que abriu no navegador
    echo 2. Ou execute: choco install zbar
    echo 3. Reinicie o terminal
) else (
    echo ✓ Tudo pronto!
)

echo.
echo ========================================
echo  COMO FUNCIONA:
echo ========================================
echo.
echo A biblioteca pyzbar detecta codigos de barras:
echo - EAN-13 (produtos brasileiros)
echo - EAN-8  (produtos menores)
echo - CODE-128 (industrial)
echo - QR Code
echo.
echo Quando detectado, confianca = 99.99%%
echo (praticamente certeza absoluta!)
echo.
pause
