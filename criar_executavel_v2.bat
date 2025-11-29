@echo off
REM ============================================================================
REM   Criador de Executável - Sistema de Coleta v2 (Com Sincronização OneDrive)
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║    SETUP - Sistema de Coleta v2 com Sincronização Automática       ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo    Instale Python 3.8 ou superior
    pause
    exit /b 1
)

echo ✅ Python encontrado!
python --version
echo.

REM Atualizar pip
echo │ Atualizando pip...
python -m pip install --upgrade pip --quiet
echo ✅ Pip atualizado!
echo.

REM Instalar dependências
echo │ Instalando dependências...
echo    - Pillow (manipulação de imagens)
echo    - Requests (download do banco OneDrive)
echo    - PyInstaller (criar executável)

python -m pip install Pillow requests pyinstaller --quiet

echo ✅ Todas as dependências instaladas!
echo.

REM Criar executável
echo │ Criando executável...
echo    Isso pode levar alguns minutos...
echo.

pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "VerifiK_ColetaImagens_v2" ^
    --icon=NONE ^
    --add-data "LINK_BANCO_DADOS.txt;." ^
    sistema_coleta_standalone_v2.py

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo ✅ EXECUTÁVEL CRIADO COM SUCESSO!
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo 📁 Localização: dist\VerifiK_ColetaImagens_v2.exe
echo 📊 Tamanho:
dir dist\VerifiK_ColetaImagens_v2.exe | find "VerifiK"
echo.
echo 📋 PRÓXIMOS PASSOS:
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo 1. Vá para a pasta: dist\
echo 2. Copie o arquivo: VerifiK_ColetaImagens_v2.exe
echo 3. Cole em um pendrive ou compartilhe via rede
echo 4. Distribua para os funcionários
echo.
echo 🆕 NOVIDADES V2:
echo    - Sincroniza produtos automaticamente do OneDrive
echo    - Usuários NÃO podem adicionar produtos
echo    - Lista de produtos sempre atualizada
echo    - Botão "Atualizar Produtos" na interface
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo.
set /p ABRIR="Deseja abrir a pasta com o executável? (S/N) "
if /i "%ABRIR%"=="S" start explorer dist

echo.
echo Processo concluído!
pause
