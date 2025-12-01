# 🔤 LEITOR DE NOMES - INSTRUÇÕES APÓS REINICIALIZAÇÃO

## 🎯 OBJETIVO
Sistema focado especificamente em **LER O NOME** da marca no rótulo dos produtos.

## 📁 ARQUIVOS CRIADOS

### 1. `leitor_de_nomes.py` 
- **Sistema principal** otimizado para leitura de nomes
- **OCR intensivo** com múltiplos preprocessamentos
- **Múltiplas regiões** de análise do rótulo
- **Correção automática** de erros comuns de OCR

### 2. `executar_leitor.py`
- **Executor simples** e direto
- **Abre resultado** automaticamente

## 🚀 COMO USAR (APÓS REINICIALIZAÇÃO)

### Passo 1: Abrir Prompt de Comando
```
Win + R → cmd → Enter
```

### Passo 2: Navegar para a pasta
```
cd "c:\Users\gabri\OneDrive\Área de Trabalho\verifiK_Biel\projetos-logos"
```

### Passo 3: Executar o leitor
```
python executar_leitor.py
```

## 🔧 O QUE O SISTEMA FAZ

### 1. **DETECTA** produtos com YOLO
### 2. **EXTRAI** múltiplas regiões do rótulo:
   - Topo central (onde geralmente fica a marca)
   - Centro para marca
   - Superior largo
   - Meio focado
   - Produto completo

### 3. **PREPROCESSA** cada região com 8 técnicas:
   - Original
   - Escala de cinza
   - Contraste alto
   - Threshold OTSU
   - Threshold adaptativo
   - Morfologia
   - Denoising
   - Blur + threshold

### 4. **APLICA OCR** com 7 configurações diferentes
   - Foco em maiúsculas
   - Linha única
   - Palavra única
   - Texto cru

### 5. **IDENTIFICA** marca por padrões conhecidos:
   - HEINEKEN (e variações: HEINE, NEKEN, etc.)
   - DEVASSA (e variações: DEVAS, EVASSA, etc.)
   - BUDWEISER, AMSTEL, STELLA, BRAHMA, SKOL, etc.

### 6. **CORRIGE** erros comuns de OCR:
   - 0→O, 1→I, 3→E, 5→S, etc.

## 📊 SAÍDAS GERADAS

- `resultado_leitura_nomes.jpg` - Imagem com nomes identificados
- `debug_produto_1.jpg` - Produto individual
- `debug_regiao_1_topo_centro.jpg` - Região do rótulo
- Console com textos encontrados pelo OCR

## 🎯 FOCO NO SEU CASO

Para a imagem que você tem (cerveja 473ml), o sistema vai:

1. ✅ **Detectar** a lata como produto
2. 🔍 **Focar** na região superior onde está o nome
3. 🔤 **Ler** o texto usando OCR otimizado  
4. 🎯 **Identificar** a marca (DEVASSA, HEINEKEN, etc.)
5. 📊 **Mostrar** resultado visual com o nome

## ⚡ EXECUÇÃO RÁPIDA

Se quiser testar rapidamente:
```
python leitor_de_nomes.py
```

O sistema está **100% focado em ler o nome da marca**!