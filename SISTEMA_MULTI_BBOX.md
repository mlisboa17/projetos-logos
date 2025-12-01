# Sistema de Múltiplos Bboxes - Detecção e Aprovação Individual

## 📋 Visão Geral

Sistema avançado para detectar e aprovar **múltiplos produtos em uma única imagem**, permitindo controle individual sobre cada detecção.

### Problema Resolvido
- ❌ **Antes**: Imagens com 4-6 produtos diferentes → sistema aprovava/rejeitava tudo junto
- ✅ **Agora**: Cada produto detectado pode ser aprovado/rejeitado/editado individualmente

---

## 🎯 Funcionalidades

### 1. Detecção Automática Multi-Produto
- YOLO detecta **todos os produtos** na imagem
- Cada produto recebe:
  - ✅ **Bbox individual** (coordenadas x, y, largura, altura)
  - ✅ **Confiança de detecção** (0-100%)
  - ✅ **Análise de forma** (lata/garrafa/caixa)
  - ✅ **Texto OCR** extraído do rótulo
  - ✅ **Produto sugerido** via IA multi-critério
  - ✅ **Confiança da sugestão** (0-100%)

### 2. Revisão Individual
- **Interface visual** com cards por produto
- **Cores por confiança**:
  - 🟢 Verde: ≥70% (alta confiança)
  - 🟡 Amarelo: 40-69% (média confiança)
  - 🔴 Vermelho: <40% (baixa confiança)

### 3. Ações Disponíveis
Por produto detectado:
- **Aprovar**: Salva no dataset com produto sugerido
- **Manual**: Seleciona outro produto da lista
- **Rejeitar**: Ignora este bbox

Global:
- **Aprovar Todos Alta Confiança**: Aprova automaticamente ≥70%

---

## 🚀 Como Usar

### Passo 1: Acessar Interface
```
http://localhost:8000/verifik/coleta/revisar-desconhecidos/
```

### Passo 2: Analisar Detecções
Cada imagem mostra:
```
┌──────────────────────────────────────┐
│  📷 Imagem com múltiplos bboxes      │
│  ┌──────┐  ┌──────┐  ┌──────┐       │
│  │ 🟢 1 │  │ 🟡 2 │  │ 🔴 3 │       │
│  └──────┘  └──────┘  └──────┘       │
└──────────────────────────────────────┘

Card Produto 1 (Verde - 85% confiança)
├─ Forma: lata
├─ OCR: HEINEKEN, 350ML, ORIGINAL
├─ Sugestão: HEINEKEN ORIGINAL 350ML
├─ Razão: Marca (HEINEKEN) + Volume (350ML) + Forma (lata)
└─ [✓ Aprovar] [✏️ Manual] [✗ Rejeitar]

Card Produto 2 (Amarelo - 52% confiança)
├─ Forma: garrafa
├─ OCR: HEINEKEN, LONG, NECK
├─ Sugestão: HEINEKEN LONG NECK 330ML
├─ Razão: Marca (HEINEKEN) + Forma (garrafa)
└─ [✓ Aprovar] [✏️ Manual] [✗ Rejeitar]
```

### Passo 3: Tomar Decisões
```javascript
// Aprovar produto específico
Clique em "Aprovar" no card do produto
→ Bbox é recortado e salvo em assets/dataset/train/PRODUTO/

// Alterar produto manualmente
Clique em "Manual" → Selecione produto correto → Confirme
→ Bbox salvo com produto escolhido

// Rejeitar detecção incorreta
Clique em "Rejeitar"
→ Bbox é ignorado, não salvo

// Aprovar em lote (alta confiança)
Clique em "Aprovar Todos Alta Confiança"
→ Todos bboxes ≥70% são salvos automaticamente
```

---

## 🔧 Arquitetura Técnica

### Backend (Django)

#### API de Detecção
```python
# /verifik/coleta/api/detectar-produtos/
POST { "imagem_id": 123 }

RESPONSE:
{
  "success": true,
  "bboxes": [
    {
      "x": 0.5,           # Centro X (normalizado 0-1)
      "y": 0.3,           # Centro Y (normalizado 0-1)
      "width": 0.2,       # Largura (normalizado)
      "height": 0.4,      # Altura (normalizado)
      "confidence": 0.85, # Confiança YOLO
      "forma": "lata",
      "ocr_texto": ["HEINEKEN", "350ML"],
      "produto_sugerido_id": 42,
      "confianca_sugestao": 85,
      "razao_sugestao": "Marca (HEINEKEN) + Volume (350ML) + Forma (lata)"
    }
  ]
}
```

#### API de Aprovação
```python
# /verifik/coleta/api/aprovar-bbox/
POST {
  "imagem_id": 123,
  "produto_id": 42,
  "bbox_data": {
    "x": 0.5,
    "y": 0.3,
    "width": 0.2,
    "height": 0.4
  }
}

RESPONSE:
{
  "success": true,
  "message": "Bbox salvo no dataset: HEINEKEN_350ML_20240115_143022.jpg",
  "nova_imagem_id": 456
}
```

#### Fluxo de Processamento
```
1. Recebe: imagem_id, produto_id, bbox_data
2. Carrega imagem original
3. Converte coordenadas normalizadas → pixels
4. Recorta região do bbox
5. Salva em assets/dataset/train/PRODUTO/
6. Cria entrada ImagemProdutoPendente
7. Retorna sucesso
```

### Frontend (JavaScript + Canvas)

#### Renderização de Bboxes
```javascript
// Desenha bboxes na imagem
function desenharBboxes(canvas, bboxes) {
  bboxes.forEach((bbox, idx) => {
    // Cor por confiança
    const cor = bbox.confianca_sugestao >= 70 ? '#00ff00' : // Verde
                bbox.confianca_sugestao >= 40 ? '#ffff00' : // Amarelo
                '#ff0000';                                   // Vermelho
    
    ctx.strokeStyle = cor;
    ctx.lineWidth = 4;
    ctx.strokeRect(x1, y1, width, height);
  });
}
```

#### Aprovação Individual
```javascript
async function aprovarBbox(imagemId, bboxIdx, produtoId, bboxData) {
  const response = await fetch('/verifik/coleta/api/aprovar-bbox/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      imagem_id: imagemId,
      produto_id: produtoId,
      bbox_data: bboxData
    })
  });
  
  if (response.ok) {
    // Remove card aprovado da interface
    document.getElementById(`bbox-card-${bboxIdx}`).remove();
  }
}
```

---

## 📊 Sistema de Pontuação IA

### Critérios de Sugestão
```python
score = 0

# 1. Marca no OCR (+25 pontos)
if marca_produto in ocr_texto:
    score += 25

# 2. Volume no OCR (+20 pontos)
if volume_produto in ocr_texto:
    score += 20

# 3. Forma compatível (+15 pontos)
if forma_detectada == forma_esperada:
    score += 15

# 4. Palavras-chave (+10 pontos)
for palavra in ["ORIGINAL", "ZERO", "LONG NECK"]:
    if palavra in ocr_texto:
        score += 10

# Confiança final: score / max_possivel * 100
```

### Limiares de Confiança
- **≥70%**: Alta confiança → bbox verde, aprovação recomendada
- **40-69%**: Média confiança → bbox amarelo, revisar manualmente
- **<40%**: Baixa confiança → bbox vermelho, provável erro

---

## 🗂️ Estrutura de Dados

### Banco de Dados
```python
# models.py
class ImagemProdutoPendente(models.Model):
    imagem = models.ImageField()           # Imagem original completa
    produto = models.ForeignKey()          # Produto associado
    bbox_data = models.JSONField()         # Array de bboxes
    status = models.CharField()            # pendente/aprovada/rejeitada
    aprovado_por = models.ForeignKey()     # Usuário que aprovou
    data_aprovacao = models.DateTimeField()
```

### Dataset
```
assets/dataset/train/
├── HEINEKEN_ORIGINAL_350ML/
│   ├── HEINEKEN_ORIGINAL_350ML_20240115_143022_123_bbox.jpg
│   ├── HEINEKEN_ORIGINAL_350ML_20240115_143105_124_bbox.jpg
│   └── ...
├── HEINEKEN_LONG_NECK_330ML/
│   └── ...
└── STELLA_ARTOIS_269ML/
    └── ...
```

---

## ⌨️ Atalhos de Teclado

| Tecla | Ação |
|-------|------|
| `A` | Aprovar bbox atual |
| `R` | Rejeitar bbox atual |
| `M` | Abrir seleção manual |
| `↑↓` | Navegar entre bboxes |
| `Enter` | Confirmar seleção manual |
| `Esc` | Cancelar ação |

---

## 🧪 Testes

### Teste Automatizado
```bash
python testar_multi_bbox.py
```

Executa:
1. ✅ Verifica carregamento do modelo YOLO
2. ✅ Busca imagens pendentes
3. ✅ Testa detecção em cada imagem
4. ✅ Mostra estatísticas do banco
5. ✅ Exibe instruções de uso

### Teste Manual
```bash
# 1. Iniciar servidor
python manage.py runserver

# 2. Acessar interface
http://localhost:8000/verifik/coleta/revisar-desconhecidos/

# 3. Verificar:
- Múltiplos bboxes aparecem na imagem?
- Cards mostram análise IA correta?
- Cores correspondem à confiança?
- Botões "Aprovar" salvam no dataset?
- "Aprovar Todos" funciona para ≥70%?
```

---

## 🐛 Troubleshooting

### Problema: Nenhum bbox detectado
**Causa**: Modelo YOLO não encontrou objetos
**Solução**:
```python
# Ajustar confiança mínima
results = model.predict(img, conf=0.15)  # Padrão: 0.25
```

### Problema: OCR retorna texto vazio
**Causa**: Tesseract não instalado
**Solução**:
```bash
# Executar instalador
instalar_ocr.bat

# Verificar caminho
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Problema: Bbox não salva no dataset
**Causa**: Permissões de pasta
**Solução**:
```bash
# Criar pasta manualmente
mkdir -p assets/dataset/train/PRODUTO

# Verificar permissões
icacls assets /grant Users:(OI)(CI)F
```

### Problema: Cores dos bboxes incorretas
**Causa**: JavaScript não calcula confiança
**Solução**:
```javascript
// Verificar no console
console.log('Confiança:', bbox.confianca_sugestao);

// Ajustar limiares
const cor = bbox.confianca_sugestao >= 60 ? 'green' : 'yellow';
```

---

## 📈 Métricas de Performance

### Tempo de Processamento
- **Detecção YOLO**: ~200-400ms por imagem
- **OCR Tesseract**: ~100-200ms por bbox
- **Classificação Forma**: ~10-20ms por bbox
- **Sugestão IA**: ~50-100ms (comparação com DB)
- **Total médio**: ~500-800ms por imagem com 3-4 produtos

### Acurácia Esperada
- **Detecção de objetos**: 85-95% (YOLO treinado)
- **Sugestão de produto**:
  - Alta confiança (≥70%): 90% de acertos
  - Média confiança (40-69%): 60-70% de acertos
  - Baixa confiança (<40%): 30-40% de acertos

---

## 🔄 Workflow Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Upload de Imagem                                         │
│    /verifik/coleta/enviar-fotos/                           │
│    → Upload foto com múltiplos produtos                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Detecção Automática (Opcional)                          │
│    Botão "Detectar Automaticamente"                        │
│    → YOLO encontra produtos e sugere classificações        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Salvar como DESCONHECIDO                                │
│    Se não aprovado no upload                               │
│    → Produto = "FAMILIA_HEINEKEN_MANUAL"                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Revisão Multi-Bbox                                       │
│    /verifik/coleta/revisar-desconhecidos/                  │
│    → Sistema detecta múltiplos produtos                     │
│    → Mostra cards individuais com análise IA                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Aprovação Individual                                     │
│    Para cada bbox:                                          │
│    ✓ Aprovar → Salva no dataset                            │
│    ✏️ Manual → Seleciona outro produto                      │
│    ✗ Rejeitar → Ignora                                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Dataset Atualizado                                       │
│    assets/dataset/train/PRODUTO/                           │
│    → Imagens recortadas prontas para treino                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Exemplos de Uso

### Cenário 1: Foto com 4 HEINEKEN diferentes
```
Imagem: foto_prateleira_heineken.jpg
Produtos detectados:
  1. HEINEKEN ORIGINAL 350ML (85% confiança) → Aprovar ✓
  2. HEINEKEN ZERO 350ML (78% confiança) → Aprovar ✓
  3. HEINEKEN LONG NECK 330ML (62% confiança) → Manual → Corrigir para HEINEKEN 330ML
  4. Produto desconhecido (23% confiança) → Rejeitar ✗

Resultado:
- 2 produtos salvos automaticamente
- 1 produto corrigido manualmente
- 1 detecção falsa rejeitada
```

### Cenário 2: Usar "Aprovar Todos Alta Confiança"
```
Imagem: lote_heineken_original.jpg
Produtos detectados:
  1. HEINEKEN ORIGINAL 350ML (92% confiança)
  2. HEINEKEN ORIGINAL 350ML (88% confiança)
  3. HEINEKEN ORIGINAL 350ML (81% confiança)
  4. HEINEKEN ORIGINAL 350ML (73% confiança)

Ação: Clique em "Aprovar Todos Alta Confiança"
→ Todos 4 produtos salvos em lote (≥70%)
```

---

## 🎓 Próximos Passos

- [ ] Implementar edição de bbox (arrastar/redimensionar)
- [ ] Adicionar histórico de aprovações
- [ ] Exportar relatório de revisões
- [ ] Integrar com pipeline de treino YOLO
- [ ] Adicionar validação de duplicatas
- [ ] Sistema de pontuação por revisor

---

## 📞 Suporte

**Documentação técnica completa**: `DETECCAO_IA.md`
**Histórico de desenvolvimento**: `HISTORICO_DESENVOLVIMENTO.md`
**Script de teste**: `testar_multi_bbox.py`
