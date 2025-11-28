@echo off
echo ============================================
echo  TESTANDO EXECUTAVEL SCRAPER VIBRA
echo ============================================
echo.

echo [INFO] Verificando se o sistema principal está rodando...
curl -s http://127.0.0.1:8000/fuel/api/status/ >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Sistema principal não está rodando
    echo.
    echo 💡 SOLUÇÃO:
    echo    1. Abra outro terminal
    echo    2. Navegue até: C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus
    echo    3. Execute: python manage.py runserver
    echo    4. Aguarde aparecer "Starting development server at http://127.0.0.1:8000/"
    echo    5. Execute este teste novamente
    echo.
    pause
    exit /b 1
)

echo ✅ Sistema principal está rodando

echo.
echo [INFO] Verificando executável...
if not exist "dist\ScraperVibra.exe" (
    echo ❌ ERRO: Executável não encontrado
    echo    Execute: pyinstaller --onefile --console --name=ScraperVibra scraper_standalone.py
    pause
    exit /b 1
)

echo ✅ Executável encontrado

for %%A in ("dist\ScraperVibra.exe") do echo ✅ Tamanho: %%~zA bytes (~%%~zA:~0,2%MB)

echo.
echo 🚀 EXECUTANDO TESTE DO SCRAPER...
echo    (Selecione opção 3 - Apenas Casa Caiada para teste)
echo.

REM Executar o scraper
dist\ScraperVibra.exe

echo.
echo ✅ Teste concluído!
pause