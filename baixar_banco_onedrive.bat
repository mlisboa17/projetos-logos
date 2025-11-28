@echo off
REM ============================================================================
REM   Download Autom�tico do Banco de Dados via OneDrive
REM ============================================================================

echo.
echo +------------------------------------------------------------------+
echo �         Download do Banco de Dados - VerifiK OneDrive           �
echo +------------------------------------------------------------------+
echo.

REM ============================================================================
REM CONFIGURE AQUI O LINK DO ONEDRIVE
REM ============================================================================
REM Substitua o link abaixo pelo link compartilhado do OneDrive
REM Para obter: Clique direito em db.sqlite3 > Compartilhar > Copiar link

set LINK_ONEDRIVE=http://192.168.68.102:8080/banco

REM ============================================================================

echo ?? Instru��es:
echo ----------------------------------------------------------------
echo.
echo 1. O navegador ser� aberto com o link do OneDrive
echo 2. Clique no bot�o "Baixar" ou "Download"
echo 3. Aguarde o download terminar
echo 4. Volte aqui e pressione qualquer tecla
echo.
echo ----------------------------------------------------------------
echo.

REM Verificar se o link foi configurado
if "%LINK_ONEDRIVE%"=="https://1drv.ms/SEU_LINK_AQUI" (
    echo ??  ATEN��O: Link do OneDrive n�o configurado!
    echo.
    echo Por favor, edite este arquivo e configure o LINK_ONEDRIVE
    echo na linha 15 com o link compartilhado do seu OneDrive.
    echo.
    echo Como obter o link:
    echo 1. Abra a pasta do projeto no OneDrive
    echo 2. Clique direito em db.sqlite3
    echo 3. Selecione "Compartilhar"
    echo 4. Copie o link gerado
    echo 5. Cole na linha 15 deste arquivo
    echo.
    pause
    exit /b 1
)

echo Abrindo OneDrive no navegador...
start "" "%LINK_ONEDRIVE%"

echo.
echo ? Aguardando download...
echo.
pause

REM Procurar arquivo baixado
echo.
echo ?? Procurando arquivo baixado...
echo.

set ARQUIVO_ENCONTRADO=0

REM Verificar em Downloads
if exist "%USERPROFILE%\Downloads\db.sqlite3" (
    echo ? Arquivo encontrado em Downloads!
    set ARQUIVO_ENCONTRADO=1
    set CAMINHO_ORIGEM=%USERPROFILE%\Downloads\db.sqlite3
)

REM Verificar varia��es de nome
if exist "%USERPROFILE%\Downloads\db.sqlite3 (1).sqlite3" (
    echo ? Arquivo encontrado em Downloads (vers�o duplicada)!
    set ARQUIVO_ENCONTRADO=1
    set CAMINHO_ORIGEM=%USERPROFILE%\Downloads\db.sqlite3 (1).sqlite3
)

if %ARQUIVO_ENCONTRADO%==0 (
    echo.
    echo ? Arquivo n�o encontrado automaticamente
    echo.
    echo Por favor, copie manualmente:
    echo    Origem: Pasta Downloads
    echo    Destino: %CD%\db.sqlite3
    echo.
    pause
    exit /b 1
)

REM Fazer backup se j� existir
if exist "db.sqlite3" (
    echo.
    echo ??  Banco de dados j� existe!
    echo.
    echo Deseja fazer backup antes de substituir? (S/N)
    set /p BACKUP=
    
    if /i "%BACKUP%"=="S" (
        set NOME_BACKUP=db_backup_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sqlite3
        set NOME_BACKUP=%NOME_BACKUP: =0%
        echo Criando backup: %NOME_BACKUP%
        copy /Y "db.sqlite3" "%NOME_BACKUP%"
        echo ? Backup criado!
    )
)

REM Copiar arquivo
echo.
echo ?? Copiando banco de dados...
copy /Y "%CAMINHO_ORIGEM%" "db.sqlite3"

if errorlevel 1 (
    echo ? Erro ao copiar arquivo!
    pause
    exit /b 1
)

echo ? Arquivo copiado com sucesso!

REM Remover arquivo de Downloads
del "%CAMINHO_ORIGEM%" 2>nul

REM Verificar tamanho do arquivo
echo.
echo ?? Informa��es do banco:
echo ----------------------------------------------------------------
dir db.sqlite3 | find "db.sqlite3"
echo.

echo ------------------------------------------------------------------
echo ? BANCO DE DADOS INSTALADO COM SUCESSO!
echo ------------------------------------------------------------------
echo.
echo ?? Localiza��o: %CD%\db.sqlite3
echo.
echo ?? Pr�ximos passos:
echo    1. Execute: python manage.py runserver
echo    2. Ou crie o execut�vel: criar_executavel.bat
echo.
echo ------------------------------------------------------------------
echo.
pause



