@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  VerifiK Sistema de Coleta v2.4 - Instalador Automático   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📦 Verificando requisitos do sistema...
echo.

REM Verifica se está executando como Administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  ATENÇÃO: Este instalador precisa de privilégios de Administrador!
    echo.
    echo Por favor, clique com o botão direito no arquivo e selecione
    echo "Executar como Administrador"
    echo.
    pause
    exit /b 1
)

echo ✅ Privilégios de Administrador verificados
echo.

REM Verifica se o Visual C++ já está instalado
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Visual C++ Redistributable já instalado
    goto :skip_vcredist
)

echo 📥 Baixando Microsoft Visual C++ Redistributable...
echo.

REM Cria pasta temporária
set TEMP_DIR=%TEMP%\VerifiK_Instalacao
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM Baixa o instalador do Visual C++
powershell -Command "& {Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%TEMP_DIR%\vc_redist.x64.exe'}"

if %errorLevel% neq 0 (
    echo ❌ Erro ao baixar o Visual C++ Redistributable
    echo.
    echo Por favor, baixe manualmente de:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    pause
    exit /b 1
)

echo ✅ Download concluído
echo.
echo 🔧 Instalando Visual C++ Redistributable...
echo    (Isso pode levar alguns minutos)
echo.

REM Instala silenciosamente
"%TEMP_DIR%\vc_redist.x64.exe" /quiet /norestart

if %errorLevel% neq 0 (
    echo ⚠️  A instalação encontrou problemas, mas pode ter sido bem-sucedida
) else (
    echo ✅ Visual C++ Redistributable instalado com sucesso
)

REM Limpa arquivos temporários
del /f /q "%TEMP_DIR%\vc_redist.x64.exe" >nul 2>&1
rmdir "%TEMP_DIR%" >nul 2>&1

:skip_vcredist

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              ✅ INSTALAÇÃO CONCLUÍDA!                      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 🚀 O VerifiK está pronto para usar!
echo.
echo Para executar o sistema:
echo 1. Duplo clique em: VerifiK_ColetaImagens_v2.4_Responsivo.exe
echo 2. Aguarde alguns segundos para o sistema iniciar
echo.
echo 📋 Novidades da v2.4 (Responsivo):
echo    • Busca de produtos não empurra botões
echo    • Nomes completos nas anotações
echo    • Canvas maior para trabalhar
echo    • Campo de observações expandido
echo.
echo ❓ Problemas? Veja o arquivo INSTALACAO_VERIFIK.md
echo.
pause
