# Script PowerShell para instalação rápida do Albumentations
# Execute como Administrador para melhores resultados

Write-Host "=== INSTALAÇÃO ALBUMENTATIONS ===" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version
Write-Host "✓ $pythonVersion" -ForegroundColor Green
Write-Host ""

# Método 1: Tentar com pip direto (pode funcionar se já tiver Visual Studio)
Write-Host "Método 1: Tentando instalação direta..." -ForegroundColor Yellow
pip install --only-binary :all: scikit-image
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ scikit-image instalado com sucesso" -ForegroundColor Green
    pip install albumentations
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Albumentations instalado com sucesso!" -ForegroundColor Green
        python -c "import albumentations; print('✓ Importação bem-sucedida!')"
        exit 0
    }
} else {
    Write-Host "✗ Instalação direta falhou" -ForegroundColor Red
}

Write-Host ""
Write-Host "Método 2: Verificando Visual Studio Build Tools..." -ForegroundColor Yellow

# Verificar se Build Tools está instalado
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswhere) {
    $vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($vsPath) {
        Write-Host "✓ Visual Studio Build Tools encontrado em: $vsPath" -ForegroundColor Green
        Write-Host "Tentando instalação novamente..." -ForegroundColor Yellow
        pip install albumentations
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Albumentations instalado com sucesso!" -ForegroundColor Green
            python -c "import albumentations; print('✓ Importação bem-sucedida!')"
            exit 0
        }
    }
}

Write-Host "✗ Visual Studio Build Tools não encontrado" -ForegroundColor Red
Write-Host ""
Write-Host "=== AÇÃO NECESSÁRIA ===" -ForegroundColor Yellow
Write-Host "Para instalar Albumentations, você precisa do Visual C++ Build Tools." -ForegroundColor White
Write-Host ""
Write-Host "Opções:" -ForegroundColor Cyan
Write-Host "1. Instalar Build Tools (6GB, RECOMENDADO):" -ForegroundColor White
Write-Host "   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Gray
Write-Host "   - Selecionar: 'Desenvolvimento para Desktop com C++'" -ForegroundColor Gray
Write-Host "   - Após instalar, execute: pip install albumentations" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Usar Anaconda/Miniconda (se disponível):" -ForegroundColor White
Write-Host "   - conda install -c conda-forge albumentations" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Continuar sem augmentation (atual):" -ForegroundColor White
Write-Host "   - Use: python treinar_simples.py" -ForegroundColor Gray
Write-Host "   - Limitação: sem multiplicação de dados" -ForegroundColor Gray
Write-Host ""

# Abrir página de download
$response = Read-Host "Deseja abrir a página de download do Build Tools? (S/N)"
if ($response -eq 'S' -or $response -eq 's') {
    Start-Process "https://visualstudio.microsoft.com/visual-cpp-build-tools/"
    Write-Host "✓ Página aberta no navegador" -ForegroundColor Green
    Write-Host "Após a instalação, execute novamente: pip install albumentations" -ForegroundColor Yellow
}
