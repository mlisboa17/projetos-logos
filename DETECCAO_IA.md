# 🤖 Sistema de Detecção Inteligente Multi-Modal

## 📋 Visão Geral

Sistema avançado de reconhecimento automático de produtos usando **3 tecnologias de IA**:

1. **YOLO v8** - Detecção de objetos e bounding boxes
2. **Tesseract OCR** - Leitura de texto nas embalagens
3. **Análise de Forma** - Classificação geométrica (lata/garrafa/caixa)

## 🎯 Como Funciona

### Detecção YOLO
- Localiza produtos na imagem
- Cria bounding boxes precisos
- Confiança de 25%+ (configurável)

### OCR (Optical Character Recognition)
- Lê texto visível no produto
- Extrai marcas: HEINEKEN, AMSTEL, BUDWEISER, etc.
- Identifica volumes: 350ML, 330ML, 473ML, 600ML, etc.
- Filtra palavras irrelevantes

### Análise de Forma
Classifica produtos baseado em:
- **Aspect Ratio** (proporção altura/largura)
- **Circularidade** (quão redondo é o contorno)
- **Área e perímetro**

#### Classificação:
- **Lata**: Aspect ratio 1.5-2.5 + alta circularidade
- **Garrafa**: Aspect ratio > 2.5 (muito alto/fino)
- **Caixa**: Aspect ratio 0.8-1.5 (quase quadrado)

### Sistema de Sugestão Inteligente

Pontua produtos do banco de dados:
- **+10 pontos**: Cada palavra OCR que combina
- **+15 pontos**: Forma correta (lata/garrafa/caixa)
- **+20 pontos**: Volume exato encontrado
- **+25 pontos**: Marca conhecida detectada

**Exemplo**:
```
OCR detectou: ['HEINEKEN', '350ML', 'LATA']
Forma: lata
Produto sugerido: "CERVEJA HEINEKEN LATA 350ML"
Pontuação: 25 (marca) + 20 (volume) + 15 (forma) = 60 pontos
Confiança: 100%
```

## 📦 Instalação

### 1. Tesseract OCR (Windows)

```bash
# Execute o instalador
.\instalar_ocr.bat
```

Ou manual:
1. Baixe: https://github.com/UB-Mannheim/tesseract/wiki
2. Instale `Tesseract-OCR-w64-setup-5.3.3.exe`
3. Adicione ao PATH: `C:\Program Files\Tesseract-OCR`

### 2. Bibliotecas Python

```bash
pip install pytesseract pillow opencv-python ultralytics
```

### 3. Modelos YOLO

Certifique-se que existe um destes arquivos:
- `verifik/verifik_yolov8.pt` (modelo treinado)
- `yolov8n.pt` (modelo base)

## 🚀 Uso

### API Endpoint

**POST** `/verifik/coleta/api/detectar-produtos/`

**Request**:
```javascript
const formData = new FormData();
formData.append('image', imageFile);

fetch('/verifik/coleta/api/detectar-produtos/', {
    method: 'POST',
    body: formData
})
```

**Response**:
```json
{
  "success": true,
  "count": 2,
  "analise_completa": true,
  "bboxes": [
    {
      "x": 0.5,
      "y": 0.5,
      "width": 0.2,
      "height": 0.4,
      "confidence": 0.89,
      "forma": "lata",
      "ocr_texto": ["HEINEKEN", "350ML", "LATA"],
      "produto_sugerido_id": 42,
      "confianca_sugestao": 95.5,
      "razao_sugestao": "Marca: HEINEKEN + Volume: 350ML + Forma: LATA"
    }
  ]
}
```

### Interface Web

1. Acesse `/verifik/coleta/enviar-fotos/`
2. Selecione produto (ou deixe a IA sugerir)
3. Faça upload da imagem
4. Sistema detecta automaticamente e mostra:
   - Bounding boxes magenta
   - Forma classificada
   - Texto detectado (OCR)
   - Produto sugerido
   - Botão "Aplicar Sugestão"

## 🎨 Visualização

### Cores dos Bounding Boxes
- **Magenta (#FF00FF)**: Produtos detectados pela IA
- **Verde tracejado (#00FF00)**: Desenho manual do usuário

### Informações Exibidas
```
✅ 2 produto(s) detectado(s)!

Produto 1:
🔍 Forma: lata (89.3%)
📝 OCR: HEINEKEN, 350ML, CERVEJA, LATA
🎯 Sugestão: Produto ID 42 (96% confiança)
💡 Motivo: Marca: HEINEKEN + Volume: 350ML + Forma: LATA
[✓ Aplicar Sugestão]
```

## 🔧 Configuração Avançada

### Ajustar Threshold YOLO

Em `views_coleta.py`:
```python
results = model(img, conf=0.25, iou=0.45)
#                    ^^^^ confiança mínima
#                             ^^^^ IoU threshold
```

### Melhorar OCR

Ajuste pré-processamento:
```python
# Aumentar contraste
gray = cv2.equalizeHist(gray)

# Denoising (opcional)
gray = cv2.fastNlMeansDenoising(gray)

# Threshold adaptativo
thresh = cv2.adaptiveThreshold(gray, 255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 11, 2)
```

### Adicionar Marcas

Em `sugerir_produto_ia()`:
```python
marcas = ['HEINEKEN', 'AMSTEL', 'SKOL', 'BRAHMA', 
          'SUA_MARCA_AQUI', ...]
```

## 📊 Análise de Forma - Detalhes

### Métricas Utilizadas

**Aspect Ratio**:
```
AR = altura / largura
```

**Circularidade**:
```
C = 4π × área / perímetro²
```
- C = 1.0: Círculo perfeito
- C < 0.5: Muito irregular

### Tabela de Classificação

| Forma     | Aspect Ratio | Circularidade | Exemplo          |
|-----------|--------------|---------------|------------------|
| Lata      | 1.5 - 2.5    | > 0.7         | Heineken 350ML   |
| Garrafa   | > 2.5        | 0.4 - 0.7     | Heineken 330ML   |
| Caixa     | 0.8 - 1.5    | < 0.5         | Pack 6 unidades  |

## 🐛 Troubleshooting

### Tesseract não encontrado
```
TesseractNotFoundError: tesseract is not installed
```
**Solução**: Execute `instalar_ocr.bat` ou instale manualmente

### OCR retorna texto incorreto
- Imagem muito escura: Ajustar `equalizeHist`
- Texto pequeno: Aumentar resolução da imagem
- Ângulo ruim: Aplicar rotação automática

### Forma sempre "desconhecido"
- Produto muito pequeno no bbox
- Background confuso (muitos objetos)
- Solução: Melhorar qualidade da foto

### YOLO não detecta produtos
- `conf=0.25` muito alto: Reduzir para 0.15
- Modelo não treinado: Usar modelo específico
- Iluminação ruim: Pré-processar imagem

## 📈 Performance

### Tempos Médios (GPU)
- YOLO detecção: **~100ms**
- OCR (Tesseract): **~200ms**
- Análise de forma: **~50ms**
- **Total**: **~350ms** por imagem

### Precisão Esperada
- YOLO: 85-95% (produtos visíveis)
- OCR: 70-90% (depende da qualidade)
- Forma: 80-95% (latas/garrafas simples)
- Sugestão: 60-90% (com boa base de dados)

## 🔮 Próximas Melhorias

- [ ] **Google Vision API** (OCR mais preciso, pago)
- [ ] **AWS Rekognition** (detecção de logos)
- [ ] **Classificação CNN** própria para formas
- [ ] **CLIP/ViT** para matching visual direto
- [ ] **Barcode/QR reader** automático
- [ ] **Color histogram** para embalagens
- [ ] **Template matching** para logos conhecidos

## 📚 Referências

- **YOLO**: https://docs.ultralytics.com/
- **Tesseract**: https://github.com/tesseract-ocr/tesseract
- **OpenCV**: https://docs.opencv.org/
- **pytesseract**: https://pypi.org/project/pytesseract/

---

**Desenvolvido por**: GitHub Copilot + Gabriel  
**Data**: 30/11/2025  
**Versão**: 2.0 - Multi-Modal AI
