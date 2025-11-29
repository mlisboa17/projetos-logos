# 🔍 CONTROLE DE FOCO PARA CÓDIGOS DE BARRAS

## 🎯 **SISTEMA DE FOCO IMPLEMENTADO**

### ✅ **PROBLEMA RESOLVIDO**
**Antes**: Câmera com foco fixo, dificuldade para ler códigos de barras
**Agora**: Controle automático e manual de foco otimizado para códigos de barras

---

## 🔧 **RECURSOS IMPLEMENTADOS**

### 1. **🔍 DETECÇÃO DE CÓDIGOS DE BARRAS**
```python
def detectar_codigo_barras_area(self, image):
    # Análise de variação horizontal em cada linha
    # Detecta padrões de barras com alta variação
    # Retorna qualidade da detecção (0-1)
```

**Como funciona**:
- Converte imagem para escala de cinza
- Analisa variação de pixels horizontalmente
- Identifica padrões típicos de códigos de barras
- Calcula qualidade da detecção

### 2. **🎛️ CONTROLE DE FOCO AUTOMÁTICO**
```python
def ajustar_foco_camera(self, valor_foco):
    # API: VideoInOptions[0].FocusMode=1 (manual)
    # API: VideoInOptions[0].FocusRect.Value=6500 (valor)
```

**Valores de foco**:
- **0-8191**: Faixa completa da câmera
- **6500**: Otimizado para códigos de barras (próximo)
- **5000**: Valor médio (objetos distantes)
- **7000-7500**: Foco bem próximo (códigos pequenos)

### 3. **🤖 AJUSTE AUTOMÁTICO INTELIGENTE**
```python
def ajustar_foco_para_barcode(self, barcode_areas):
    # Se qualidade < 0.6, tenta diferentes focos
    # Focos teste: [6500, 7000, 6000, 7500, 5500]
    # Máximo 3 tentativas antes de voltar ao automático
```

---

## 🎮 **CONTROLES DA INTERFACE**

### 🔍 **Botão "🔍" - Foco Manual para Códigos**
- **Função**: Ajusta foco para valor 6500 (otimizado para códigos)
- **Quando usar**: Produtos com códigos de barras visíveis
- **Status**: "🔍 Foco para códigos"

### 🎯 **Botão "🎯" - Foco Automático**  
- **Função**: Volta ao foco automático da câmera
- **Quando usar**: Para detecção geral de produtos
- **Status**: "🎯 Foco automático ativo"

---

## 📈 **MELHORIAS DE DETECÇÃO**

### ✅ **Antes vs Depois**

| Aspecto | Antes | Depois |
|---------|--------|--------|
| **Foco** | Fixo automático | Adaptável para códigos |
| **Códigos de barras** | Não detectava | Detecta + ajusta foco |
| **Confiança** | Só por cores | +15% se código detectado |
| **Feedback** | Básico | "📱" indica código detectado |
| **Controles** | Automático apenas | Manual + Automático |

### 🎯 **Sistema Inteligente**
- **Detecção**: Identifica áreas com possíveis códigos
- **Qualidade**: Avalia clareza dos códigos (0-100%)
- **Ajuste**: Muda foco automaticamente se qualidade baixa
- **Fallback**: Volta ao automático após tentativas

---

## 🔧 **COMO USAR O SISTEMA DE FOCO**

### 📱 **Para Códigos de Barras**
1. **Posicionar produto** com código de barras visível
2. **Clicar 🔍** para foco manual otimizado
3. **Verificar detecção** - deve aparecer ícone 📱
4. **Aguardar análise** - sistema ajusta automaticamente

### 🎯 **Para Produtos Gerais**  
1. **Clicar 🎯** para foco automático
2. **Deixar câmera** ajustar foco automaticamente
3. **Sistema detecta** por cores e formas
4. **Foco adapta** conforme necessário

### ⚡ **Detecção Automática**
- **Auto habilitado**: Sistema ajusta foco automaticamente
- **Qualidade baixa**: Tenta 3 valores diferentes de foco
- **Intervalo**: Ajustes a cada 3-5 segundos (não spam)
- **Reset**: Volta ao automático se não melhorar

---

## 📊 **FEEDBACK VISUAL DO SISTEMA**

### 🔍 **Indicadores de Códigos de Barras**
```
📱 CERVEJA (85%) 📱    # Código detectado com alta confiança  
🔍 REFRIGERANTE (65%)  # Ajustando foco para código
❓ AGUA (30%)          # Código detectado mas baixa qualidade
```

### 🎯 **Status de Foco**
```
🔍 Foco para códigos               # Manual ativo
🎯 Foco automático ativo           # Automático ativo  
🔍 Ajustando foco para códigos...  # Sistema ajustando
⚠️ Erro ao ajustar foco           # Problema de conexão
```

---

## ⚙️ **CONFIGURAÇÕES TÉCNICAS**

### 🎛️ **Parâmetros de Foco**
```python
self.foco_para_barcode = 6500   # Valor otimizado para códigos
self.foco_atual = 5000          # Valor padrão médio  
self.ultimo_ajuste_foco = 0     # Controle de intervalo
self.tentativas_foco = 0        # Contador de tentativas
```

### 📏 **Limites de Qualidade**
```python
qualidade > 0.7  # 🎯 Alta confiança
qualidade > 0.4  # 🔍 Média confiança  
qualidade < 0.6  # Precisa ajustar foco
avg_variation > 25  # Mínimo para detectar código
```

### 🔗 **APIs da Câmera Utilizadas**
```bash
# Ativar foco manual
/cgi-bin/configManager.cgi?action=setConfig&VideoInOptions[0].FocusMode=1

# Definir valor do foco  
/cgi-bin/configManager.cgi?action=setConfig&VideoInOptions[0].FocusRect.Value=6500

# Voltar ao foco automático
/cgi-bin/configManager.cgi?action=setConfig&VideoInOptions[0].FocusMode=0
```

---

## 🚀 **RESULTADOS ESPERADOS**

### ✅ **Melhorias na Leitura**
- **Códigos nítidos**: Foco otimizado para distância ideal
- **Detecção precisa**: +15% confiança quando código detectado
- **Ajuste automático**: Sistema tenta melhorar qualidade sozinho
- **Controle manual**: Usuário pode forçar foco específico

### 📈 **Casos de Uso Otimizados**
1. **Produtos próximos**: Foco 6500-7000 para códigos pequenos
2. **Produtos médios**: Foco 6000-6500 para códigos normais  
3. **Produtos distantes**: Foco automático ou manual 5000-5500
4. **Códigos danificados**: Sistema tenta múltiplos focos

---

## 🎯 **COMO TESTAR O FOCO**

### 📱 **Teste com Código de Barras**
1. **Pegar produto** com código de barras visível
2. **Ativar detecção**: Marcar "🤖 Auto" e "Código Barras"
3. **Usar foco manual**: Clicar "🔍"
4. **Posicionar produto**: ~20-30cm da câmera
5. **Verificar**: Deve aparecer "📱" no resultado

### 🔄 **Teste Automático**
1. **Ativar foco auto**: Clicar "🎯"  
2. **Posicionar código**: Bem próximo (borrado)
3. **Aguardar**: Sistema deve ajustar automaticamente
4. **Observar**: Status muda para "🔍 Ajustando foco..."
5. **Resultado**: Código fica mais nítido

---

## 🎉 **SISTEMA COMPLETO FUNCIONANDO**

### ✅ **Recursos Ativos**
- 🔍 **Detecção de códigos de barras** por variação de pixels
- 🎛️ **Controle manual de foco** com valores otimizados  
- 🤖 **Ajuste automático** quando qualidade baixa
- 📱 **Feedback visual** com ícones de códigos
- 🎯 **Foco automático** da câmera quando necessário
- ⚙️ **Interface intuitiva** com botões simples

### 🚀 **Próximos Passos Sugeridos**
1. **Testar diferentes produtos** com códigos variados
2. **Ajustar valores** de foco conforme necessário
3. **Integrar OCR**: `pip install pytesseract` para ler texto dos códigos
4. **Base de códigos**: Cadastrar códigos reais no sistema
5. **Histórico**: Log de códigos lidos com sucesso

**🎯 Sistema agora otimizado para leitura precisa de códigos de barras!**