# Instalação do Albumentations no Windows

## Problema
O Albumentations requer Microsoft Visual C++ 14.0+ para compilar dependências (simsimd, scikit-image).

## Solução 1: Instalar Build Tools (RECOMENDADO)

### Passo 1: Download
Baixe o instalador:
https://visualstudio.microsoft.com/visual-cpp-build-tools/

### Passo 2: Instalação
1. Execute o instalador
2. Selecione: **"Desenvolvimento para Desktop com C++"**
3. Certifique-se que está marcado:
   - MSVC v143 - VS 2022 C++ x64/x86 build tools
   - Windows 10 SDK (ou 11)
4. Clique em "Instalar" (~6 GB de espaço)

### Passo 3: Reiniciar Terminal
Após instalação, feche e abra novamente o PowerShell/CMD

### Passo 4: Instalar Albumentations
```powershell
pip install albumentations
```

## Solução 2: Usar Conda (ALTERNATIVA)

Se você usa Anaconda/Miniconda, os pacotes já vêm pré-compilados:

```powershell
conda install -c conda-forge albumentations
```

## Solução 3: Wheels Pré-compilados (RÁPIDO)

Baixar wheels (.whl) pré-compilados:

### Para Python 3.14:
```powershell
# Instalar dependências problemáticas via wheels
pip install scikit-image --only-binary :all:
pip install albumentations
```

### Se não funcionar, use Christoph Gohlke's wheels:
https://www.lfd.uci.edu/~gohlke/pythonlibs/

1. Baixe o arquivo .whl apropriado para sua versão do Python
2. Instale: `pip install nome_do_arquivo.whl`

## Verificar Instalação

```python
python -c "import albumentations; print('Albumentations instalado com sucesso!')"
```

## Após Instalação

Execute o treinamento completo com data augmentation:

```powershell
cd C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus

# Opção 1: Via comando Django (requer verifik em INSTALLED_APPS)
python manage.py treinar_incremental --only-new --epochs 50

# Opção 2: Via script direto
python -c "from fuel_prices.verifik.management.commands.treinar_incremental import Command; Command().handle(only_new=True, epochs=50)"
```

## Benefícios do Albumentations

Quando instalado, você terá:
- **8x mais dados** (1 original + 7 augmentações)
- **10 tipos de transformações**:
  - HorizontalFlip (espelhamento)
  - Rotate (rotação ±15°)
  - ShiftScaleRotate (translação + escala + rotação)
  - RandomBrightnessContrast (brilho/contraste)
  - HueSaturationValue (cores)
  - GaussNoise (ruído)
  - GaussianBlur/MotionBlur (desfoque)
  - Sharpen/Emboss (nitidez)
  - RandomShadow (sombras)
- **Melhor generalização** do modelo
- **Maior precisão** em condições variadas

## Status Atual

- ✅ Pipeline de augmentation implementado
- ✅ Comando Django criado
- ✅ Interface VerifiK com anotação canvas
- ⏳ **Aguardando instalação do compilador C++**
- 🔄 Treinamento atual: modo simplificado (sem augmentation)
