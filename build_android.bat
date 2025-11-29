@echo off
title VerifiK Mobile - Compilador Android

echo.
echo ===============================================
echo 🚀 VerifiK Mobile - Compilador para Android
echo ===============================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo 📥 Instale Python 3.8+ primeiro: https://python.org
    pause
    exit /b 1
)

REM Verificar se buildozer está instalado
buildozer --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Buildozer não encontrado!
    echo 📥 Instalando buildozer...
    pip install buildozer
    pip install cython
    
    if errorlevel 1 (
        echo ❌ Erro ao instalar buildozer
        pause
        exit /b 1
    )
    echo ✅ Buildozer instalado!
)

echo.
echo 🔧 Verificando ambiente de desenvolvimento...

REM Verificar se buildozer.spec existe
if not exist "buildozer.spec" (
    echo ❌ Arquivo buildozer.spec não encontrado!
    echo 📝 Execute 'buildozer init' primeiro
    pause
    exit /b 1
)

REM Verificar se main.py existe
if not exist "main.py" (
    echo ❌ Arquivo main.py não encontrado!
    echo 📝 Certifique-se de que o arquivo principal do app existe
    pause
    exit /b 1
)

echo ✅ Ambiente OK!
echo.

REM Perguntar sobre limpeza
set /p clean="🗑️ Deseja limpar builds anteriores? (s/N): "
if /i "%clean%"=="s" (
    echo 🧹 Limpando builds anteriores...
    buildozer android clean
)

echo.
echo 🔨 Iniciando compilação do APK...
echo ⏳ Isso pode levar alguns minutos na primeira vez...
echo.

REM Compilar APK debug
buildozer android debug

if errorlevel 1 (
    echo.
    echo ❌ ERRO na compilação!
    echo ===============================================
    echo 🔍 Verifique os logs acima para identificar o problema.
    echo.
    echo 💡 Possíveis soluções:
    echo 1. buildozer android clean
    echo 2. Verificar conexão com internet
    echo 3. Verificar espaço em disco (mín. 5GB)
    echo 4. Executar como administrador
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ SUCESSO! APK compilado com sucesso!
echo ===============================================
echo 📱 Procure o arquivo .apk na pasta 'bin\'
echo.
echo 📋 Próximos passos:
echo 1. Copie o APK para seu dispositivo Android
echo 2. Ative 'Fontes desconhecidas' nas configurações
echo 3. Instale o APK tocando nele
echo.
echo 🔧 Para compilar versão release ^(assinada^):
echo    buildozer android release
echo.

REM Mostrar arquivos APK gerados
if exist "bin\*.apk" (
    echo 📦 Arquivos APK encontrados:
    dir /b bin\*.apk
    echo.
)

echo 🏁 Processo finalizado.
pause