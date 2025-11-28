@echo off
REM ============================================================================
REM ADICIONAR EXCEÇÃO NO WINDOWS DEFENDER E MCAFEE
REM Execute como ADMINISTRADOR (botão direito → Executar como administrador)
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║         Adicionar Exceção de Antivírus - VerifiK                   ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.

REM Verificar se está rodando como admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERRO: Este script precisa ser executado como ADMINISTRADOR!
    echo.
    echo    Clique direito no arquivo e selecione "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo ✅ Executando como Administrador...
echo.

REM Adicionar exceção no Windows Defender
echo ══════════════════════════════════════════════════════════════════════
echo 1. WINDOWS DEFENDER
echo ══════════════════════════════════════════════════════════════════════
echo.
echo Adicionando pasta à lista de exclusões...

powershell -Command "Add-MpPreference -ExclusionPath 'C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\dist'"

if %errorLevel% equ 0 (
    echo ✅ Windows Defender: Exceção adicionada com sucesso!
) else (
    echo ⚠️  Windows Defender: Não foi possível adicionar automaticamente
    echo    Adicione manualmente: C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\dist
)

echo.
echo ══════════════════════════════════════════════════════════════════════
echo 2. MCAFEE
echo ══════════════════════════════════════════════════════════════════════
echo.
echo ⚠️  McAfee requer configuração MANUAL:
echo.
echo PASSO A PASSO (VERSÃO PORTUGUÊS):
echo ─────────────────────────────────────────────────────────────────────
echo.
echo 1. Clique no ícone do McAfee na bandeja do sistema (ao lado do relógio)
echo 2. Clique em "Segurança do PC" ou "Proteção de vírus e spyware"
echo 3. Clique em "Verificação em tempo real"
echo 4. Clique em "Arquivos excluídos" ou "Adicionar arquivo excluído"
echo 5. Clique no botão "Adicionar arquivo"
echo 6. Navegue até a pasta:
echo    C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\dist\
echo 7. Selecione: VerifiK_ColetaImagens_v2.exe
echo 8. Clique em "Abrir"
echo 9. Clique em "Aplicar" ou "Salvar"
echo.
echo ALTERNATIVA (se não encontrar):
echo ─────────────────────────────────────────────────────────────────────
echo 1. McAfee → Configurações (ícone de engrenagem)
echo 2. Real-Time Scanning → Arquivos excluídos
echo 3. Adicionar arquivo → Selecione o executável
echo 4. Salvar
echo.
echo ─────────────────────────────────────────────────────────────────────
echo.
echo 📋 Caminho para copiar:
echo C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\dist\VerifiK_ColetaImagens_v2.exe
echo.
echo ══════════════════════════════════════════════════════════════════════
echo.

set /p ABRIR_PASTA="Deseja abrir a pasta do executável para copiar o caminho? (S/N) "
if /i "%ABRIR_PASTA%"=="S" (
    explorer /select,"C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\dist\VerifiK_ColetaImagens_v2.exe"
)

echo.
echo ══════════════════════════════════════════════════════════════════════
echo 📝 RESUMO
echo ══════════════════════════════════════════════════════════════════════
echo.
echo ✅ Windows Defender: Configurado automaticamente
echo ⚠️  McAfee: Requer configuração manual (siga passos acima)
echo.
echo Após adicionar as exceções, o executável funcionará normalmente.
echo.

pause
