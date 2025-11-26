# 🔧 Instalação e Configuração do Tesseract OCR

## 📥 Windows

### 1. Download do Tesseract

Baixe o instalador oficial:
https://github.com/UB-Mannheim/tesseract/wiki

Versão recomendada: **tesseract-ocr-w64-setup-5.3.3.20231005.exe**

### 2. Instalar

1. Execute o instalador
2. **IMPORTANTE:** Durante a instalação, marque:
   - ✅ "Portuguese" (Português)
   - ✅ "Add to PATH"
3. Caminho padrão: `C:\Program Files\Tesseract-OCR\`

### 3. Verificar Instalação

Abra PowerShell e execute:
```powershell
tesseract --version
```

Deve mostrar algo como:
```
tesseract 5.3.3
 leptonica-1.83.1
  libgif 5.2.1 : libjpeg 8d (libjpeg-turbo 2.1.5.1) : libpng 1.6.40 : libtiff 4.5.1 : zlib 1.2.13 : libwebp 1.3.2 : libopenjp2 2.5.0
```

### 4. Instalar Dependências Python

```powershell
cd projetos-logos
pip install pytesseract pillow
```

### 5. Configurar Caminho (se necessário)

Se o Tesseract não foi adicionado ao PATH, edite `ocr_processor.py`:

```python
processor = TesseractOCRProcessor(
    tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'
)
```

## 🐧 Linux (Ubuntu/Debian)

```bash
# Instalar Tesseract
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-por

# Verificar
tesseract --version

# Instalar dependências Python
pip install pytesseract pillow
```

## 🍎 macOS

```bash
# Usando Homebrew
brew install tesseract tesseract-lang

# Verificar
tesseract --version

# Instalar dependências Python
pip install pytesseract pillow
```

## ✅ Testar Instalação

### No Django Shell:

```python
python manage.py shell

from transcricao_caixa.ocr_processor import testar_tesseract

sucesso, mensagem = testar_tesseract()
print(mensagem)
```

Deve retornar:
```
Tesseract instalado: 5.3.3
```

### Teste Rápido com Imagem:

```python
from transcricao_caixa.ocr_processor import TesseractOCRProcessor

ocr = TesseractOCRProcessor()
resultado = ocr.extrair_texto('caminho/para/sua/imagem.jpg')

print("Texto:", resultado['texto'])
print("Confiança:", resultado['confianca'], "%")
```

## 🎯 Otimização para Documentos Fiscais

### Melhores Resultados:

1. **Qualidade da Imagem:**
   - Mínimo 300 DPI
   - Fundo branco/claro
   - Texto escuro
   - Sem desfoque

2. **Tipos de Arquivo:**
   - ✅ PNG (melhor)
   - ✅ JPEG (bom)
   - ⚠️ PDF (converter para PNG primeiro)

3. **Pré-processamento Automático:**
   O sistema já aplica automaticamente:
   - Conversão para escala de cinza
   - Aumento de contraste
   - Nitidez
   - Binarização

## 🔍 Parâmetros do Tesseract

No arquivo `ocr_processor.py`, você pode ajustar:

```python
# PSM (Page Segmentation Mode)
--psm 6  # Assume um bloco único de texto (padrão)
--psm 4  # Assume uma única coluna de texto variável
--psm 3  # Automático (mais lento)

# OEM (OCR Engine Mode)
--oem 3  # Padrão, baseado em LSTM (melhor)
--oem 1  # Neural nets LSTM apenas
--oem 0  # Legacy apenas (mais rápido, menos preciso)
```

## 📊 Melhorar Precisão

### Se a precisão estiver baixa:

1. **Aumentar contraste:**
```python
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(2.5)  # Era 2, aumentar para 2.5
```

2. **Ajustar binarização:**
```python
threshold = 130  # Era 150, diminuir para capturar mais texto
```

3. **Usar modo diferente:**
```python
self.config_padrao = '--oem 3 --psm 4'  # Tentar PSM 4
```

## 🚨 Troubleshooting

### Erro: "tesseract is not installed"
```powershell
# Adicionar ao PATH manualmente
$env:Path += ";C:\Program Files\Tesseract-OCR"
```

### Erro: "Failed loading language 'por'"
```bash
# Windows: Reinstalar e marcar Portuguese
# Linux: sudo apt install tesseract-ocr-por
```

### Confiança muito baixa (<50%)
- Verifique qualidade da imagem
- Tente preprocessamento manual
- Considere usar Google Vision API

## 📈 Próximos Passos

Após instalar:

1. ✅ Testar com documento real
2. ✅ Ajustar preprocessamento se necessário
3. ✅ Criar tipos de documento no admin
4. ✅ Fazer upload e processar primeiro documento
5. ✅ Avaliar precisão e decidir se precisa Google Vision API

---

**Instalação concluída?** Execute:
```powershell
cd projetos-logos
pip install pytesseract pillow
python manage.py shell
>>> from transcricao_caixa.ocr_processor import testar_tesseract
>>> testar_tesseract()
```
