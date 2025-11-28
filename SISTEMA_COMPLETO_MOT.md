# 🧠 SISTEMA INTELIGENTE DE RECONHECIMENTO E RASTREAMENTO DE PRODUTOS

## 📋 VISÃO GERAL DO SISTEMA

O VerifiK desenvolveu um sistema híbrido avançado que combina múltiplas tecnologias de IA para reconhecimento, rastreamento e controle de produtos de varejo. Este documento preserva todo o conhecimento adquirido pelo sistema.

---

## 🔧 ARQUITETURA DO SISTEMA

### 1. **SISTEMA HÍBRIDO DE DETECÇÃO**

#### **YOLO (You Only Look Once)**
- **Função**: Detecção primária de objetos treinados
- **Modelo**: `verifik_yolov8.pt`
- **Produtos Treinados**: 176 classes de produtos
- **Confiança Mínima**: 0.3
- **Status**: ✅ Ativo e funcional

#### **OCR (Optical Character Recognition)**
- **Engine**: Tesseract OCR
- **Localização**: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **Configuração**: Inglês para melhor performance
- **Uso**: Reconhecimento de texto em produtos e códigos de barras
- **Status**: ✅ Ativo e funcional

#### **Sistema de Código de Barras**
- **Métodos**: 
  - pyzbar (biblioteca nativa) - com fallback
  - OCR numérico (backup quando pyzbar falha)
- **Padrões Suportados**: EAN-13, UPC-A, EAN-8, códigos brasileiros
- **Status**: ✅ Ativo com fallback inteligente

---

## 📚 BASE DE CONHECIMENTO DE VAREJO

### **Marcas Conhecidas e Características Visuais**

```json
{
  "coca_cola": {
    "cores": ["vermelho", "branco"],
    "palavras_chave": ["COCA", "COLA", "COKE"],
    "formatos_comuns": ["lata_350ml", "garrafa_600ml", "garrafa_2l"]
  },
  "pepsi": {
    "cores": ["azul", "vermelho"],
    "palavras_chave": ["PEPSI", "COLA"],
    "formatos_comuns": ["lata_350ml", "garrafa_600ml"]
  },
  "guarana_antarctica": {
    "cores": ["verde", "vermelho"],
    "palavras_chave": ["GUARANÁ", "ANTARCTICA"],
    "formatos_comuns": ["lata_350ml", "garrafa_600ml"]
  },
  "skol": {
    "cores": ["azul", "branco"],
    "palavras_chave": ["SKOL", "CERVEJA"],
    "formatos_comuns": ["lata_350ml", "garrafa_600ml"]
  },
  "brahma": {
    "cores": ["vermelho", "dourado"],
    "palavras_chave": ["BRAHMA", "CERVEJA"],
    "formatos_comuns": ["lata_350ml", "garrafa_600ml"]
  },
  "nestle": {
    "cores": ["azul", "branco"],
    "palavras_chave": ["NESTLE", "LEITE"],
    "formatos_comuns": ["caixa_longa_vida", "lata_leite_condensado"]
  },
  "doritos": {
    "cores": ["laranja", "vermelho"],
    "palavras_chave": ["DORITOS", "NACHO"],
    "formatos_comuns": ["pacote_retangular"]
  },
  "oreo": {
    "cores": ["azul", "branco"],
    "palavras_chave": ["OREO", "BISCOITO"],
    "formatos_comuns": ["pacote_retangular"]
  }
}
```

### **Dimensões de Referência (em milímetros)**

```json
{
  "lata_refrigerante_350ml": {
    "altura": [120, 125],
    "diametro": [64, 68],
    "area_pixels_tipica": [3000, 8000],
    "aspect_ratio": [1.8, 1.9]
  },
  "garrafa_agua_500ml": {
    "altura": [195, 205],
    "diametro": [63, 67],
    "area_pixels_tipica": [8000, 15000],
    "aspect_ratio": [3.0, 3.2]
  },
  "pacote_biscoito": {
    "largura": [145, 155],
    "altura": [105, 115],
    "espessura": [25, 35],
    "area_pixels_tipica": [12000, 20000],
    "aspect_ratio": [0.7, 0.8]
  },
  "lata_cerveja_350ml": {
    "altura": [120, 125],
    "diametro": [64, 68],
    "area_pixels_tipica": [3000, 8000],
    "aspect_ratio": [1.8, 1.9]
  }
}
```

---

## 🎯 SISTEMA MOT (MULTI-OBJECT TRACKING)

### **Funcionalidades do MOT**

#### **Rastreamento Individual**
- **Track ID**: Identificador único para cada produto detectado
- **UUID**: Identificador universal único (8 caracteres)
- **Histórico de Posições**: Até 50 posições anteriores
- **Histórico de Confiança**: Tracking da confiança ao longo do tempo
- **Estado do Track**: Ativo, Perdido, Removido

#### **Características Calculadas**
- **Velocidade Média**: Pixels por frame
- **Direção de Movimento**: Horizontal ou Vertical
- **Área Média**: Área da bounding box ao longo do tempo
- **Tempo de Vida**: Tempo total na tela
- **Tempo na Zona**: Tempo dentro da zona de controle

#### **Zona de Passagem**
- **Definição**: Centro da imagem (50% da área total)
- **Função**: Detectar quando produtos atravessam área de controle
- **Validação**: Verificação de entrada e saída da zona
- **Registro**: Histórico de todas as passagens detectadas

### **Como a IA Marca e Rastreia o Produto (MOT)**

#### **1. Criação de Track**
```python
# Quando um produto é detectado pela primeira vez:
novo_tracker = ProductTracker(
    track_id=próximo_id_único,
    deteccao_inicial=deteccao,
    timestamp=tempo_atual
)

# O tracker recebe:
- UUID único de 8 caracteres
- Cor específica para visualização
- Histórico vazio pronto para receber dados
- Estado inicial: ATIVO
```

#### **2. Associação Frame a Frame**
```python
# Para cada novo frame:
for cada_deteccao_atual:
    melhor_track = None
    menor_distancia = infinito
    
    for cada_track_existente:
        distancia = calcular_distancia_euclidiana(
            centro_track, 
            centro_deteccao
        )
        
        if distancia < max_distancia_permitida:
            if distancia < menor_distancia:
                melhor_track = track_existente
                menor_distancia = distancia

# Se encontrou track compatível:
if melhor_track:
    melhor_track.adicionar_deteccao(deteccao_atual)
else:
    # Criar novo track
    criar_novo_track(deteccao_atual)
```

#### **3. Marcação Visual Inteligente**
- **Cores Únicas**: Cada track recebe uma cor da paleta de 10 cores
- **Trajetória**: Linha conectando as últimas 50 posições
- **ID Visível**: Número do track exibido na tela
- **Estado Visual**: Indicadores de passagem, velocidade, direção

#### **4. Cálculo de Características**
```python
def atualizar_caracteristicas_track():
    # Velocidade média (pixels por frame)
    velocidades = []
    for i in range(1, len(historico_centros)):
        distancia = calcular_distancia(
            historico_centros[i-1], 
            historico_centros[i]
        )
        velocidades.append(distancia)
    
    velocidade_media = sum(velocidades) / len(velocidades)
    
    # Direção predominante
    dx = ultimo_centro.x - primeiro_centro.x
    dy = ultimo_centro.y - primeiro_centro.y
    
    if abs(dx) > abs(dy):
        direcao = "HORIZONTAL"
    else:
        direcao = "VERTICAL"
    
    # Tempo na tela
    tempo_vida = timestamp_atual - timestamp_criacao
```

#### **5. Detecção de Passagem por Zona**
```python
def verificar_passagem_zona(tracker):
    centro_atual = tracker.centro_atual
    zona_controle = zona_passagem_central
    
    # Verificar se está dentro da zona
    if ponto_dentro_da_zona(centro_atual, zona_controle):
        # Verificar histórico - veio de fora?
        centros_anteriores = tracker.historico_centros[-3:]
        
        veio_de_fora = any(
            not ponto_dentro_da_zona(centro, zona_controle)
            for centro in centros_anteriores[:-1]
        )
        
        if veio_de_fora and not tracker.passou_zona:
            # PASSAGEM DETECTADA!
            tracker.passou_zona = True
            registrar_passagem(tracker)
            exibir_alerta_passagem(tracker)
```

#### **6. Limpeza Inteligente de Tracks**
```python
def limpar_tracks_perdidos():
    for track_id, tracker in tracks_ativos:
        # Critérios para remoção:
        muito_tempo_sem_deteccao = (
            tracker.frames_sem_deteccao > 30
        )
        
        muito_antigo = (
            time.now() - tracker.timestamp_criacao > 300  # 5 min
        )
        
        saiu_da_imagem = verificar_se_saiu_da_imagem(tracker)
        
        if any([muito_tempo_sem_deteccao, muito_antigo, saiu_da_imagem]):
            remover_track(track_id)
            log_remocao(tracker)
```

### **Configurações de Tracking**

```python
CONFIGURACOES_MOT = {
    "max_distancia_tracking": 150,  # pixels máximos para associação
    "frames_sem_deteccao_max": 30,  # frames antes de marcar como perdido
    "confianca_tracking_min": 0.4,  # confiança mínima para iniciar track
    "tempo_vida_track_max": 300,    # segundos máximos de vida do track
    "cores_tracking": [             # cores para visualização
        (255, 0, 0),    # Vermelho
        (0, 255, 0),    # Verde
        (0, 0, 255),    # Azul
        (255, 255, 0),  # Ciano
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Amarelo
        (128, 0, 128),  # Roxo
        (255, 165, 0),  # Laranja
        (0, 128, 128),  # Teal
        (128, 128, 0)   # Olive
    ]
}
```

---

## 🌐 INTEGRAÇÃO COM BASES EXTERNAS

### **OpenFoodFacts API**
- **URL Base**: `https://world.openfoodfacts.org/api/v0/product/{codigo}.json`
- **Dados Obtidos**:
  - Nome do produto
  - Marca
  - Categoria
  - Ingredientes
  - País de origem
  - Nutriscore
- **Cache Local**: `openfoodfacts_cache.json`
- **Status**: ✅ Integrado com cache inteligente

### **Base de Dados Local**
- **Arquivo**: `mobile_simulator.db`
- **Tabela Principal**: `produtos`
- **Campos Utilizados**:
  - `descricao_produto`
  - `categoria`
  - `marca`
  - `id`
- **Total de Produtos**: 100+ produtos carregados

### **Padrões de Código de Barras Brasileiros**
```python
PADROES_CODIGO_BRASIL = {
    "prefixos_validos": ["789", "790"],
    "marcas_por_prefixo": {
        "78910001": "Coca-Cola Brasil",
        "78910000": "Nestlé Brasil", 
        "78919910": "AmBev (Antarctica/Skol)",
        "78900001": "Unilever Brasil"
    }
}
```

---

## 🧠 SISTEMA DE APRENDIZADO DE FORMATOS

### **Aprendizado Adaptativo**
- **Arquivo**: `formatos_aprendidos.json`
- **Funcionamento**: 
  1. Sistema detecta produto pela primeira vez
  2. Registra dimensões, área e aspect ratio
  3. Para detecções futuras, compara com padrões aprendidos
  4. Valida se nova detecção é compatível com formato conhecido
- **Tolerâncias**:
  - Área: ±50%
  - Aspect Ratio: ±30%
- **Limite**: Máximo 10 exemplos por classe de produto

### **Validação Inteligente**
```python
def validar_objeto_inteligente(x1, y1, x2, y2, confianca, classe):
    # Verificações realizadas:
    # 1. Dimensões físicas realistas
    # 2. Proporções corretas
    # 3. Área dentro dos limites esperados  
    # 4. Comparação com conhecimento de produtos reais
    # 5. Validação contra aprendizado anterior
```

---

## 📊 MÉTRICAS E ESTATÍSTICAS MOT

### **Estatísticas do Sistema**
- **Total de Tracks Criados**: Contador incremental
- **Tracks Ativos**: Número atual de produtos sendo rastreados
- **Produtos Identificados**: Classes únicas detectadas
- **Passagens Detectadas**: Número de produtos que atravessaram a zona
- **Tempo de Operação**: Tempo desde inicialização

### **Performance do Sistema**
- **FPS de Processamento**: Dependente do hardware
- **Precisão YOLO**: Baseada no modelo treinado
- **Taxa de Reconhecimento OCR**: Variável por qualidade da imagem
- **Sucesso de Tracking**: Baseado na continuidade das detecções

### **Estatísticas Exibidas em Tempo Real**
```
MOT Stats:
Tracks Ativos: 3
Total Tracks: 15
Passagens: 7
Produtos ID: 5
```

---

## 🔄 FLUXO DE PROCESSAMENTO COMPLETO

### **Pipeline Híbrido + MOT**
1. **Captura de Imagem**: Da câmera IP Intelbras
2. **Detecção YOLO**: Produtos treinados
3. **Processamento OCR**: Texto e códigos numéricos  
4. **Detecção de Código de Barras**: pyzbar + OCR backup
5. **Busca em Bases**: Local → OpenFoodFacts → Padrões conhecidos
6. **Reconhecimento de Marcas**: Base de conhecimento de varejo
7. **Combinação Inteligente**: Fusão de todas as fontes
8. **⭐ APLICAÇÃO MOT**: Rastreamento multi-objeto
9. **Validação**: Aprendizado de formatos + dimensões reais
10. **Visualização**: Desenho com tracks coloridos e trajetórias
11. **Registro**: Atualização de listas e históricos

### **Priorização de Fontes**
1. **YOLO** (produtos treinados) - Alta confiança
2. **Código de Barras** (produtos descobertos) - Muito alta confiança
3. **OCR + Marca Conhecida** - Média-alta confiança
4. **OCR + Base Treinada** - Média confiança
5. **Produtos Genéricos** - Baixa confiança

---

## 🎯 CASOS DE USO MOT IMPLEMENTADOS

### **1. Produto Entra na Cena**
- Sistema detecta pela primeira vez
- Cria Track com ID único e cor
- Inicia histórico de posições
- Começa cálculo de características

### **2. Produto se Move na Cena**
- MOT associa novas detecções ao track existente
- Atualiza trajetória e estatísticas
- Desenha trilha de movimento
- Calcula velocidade e direção

### **3. Produto Passa pela Zona de Controle**
- Sistema detecta entrada na zona central
- Verifica se realmente atravessou (não só entrou)
- Marca como "PASSOU" com indicador visual verde
- Registra no histórico de passagens

### **4. Produto Sai da Cena ou é Perdido**
- Track não recebe detecções por vários frames
- Sistema marca como perdido
- Após timeout, remove da memória
- Mantém no histórico para estatísticas

---

## 💾 ARQUIVOS DE PERSISTÊNCIA

### **Caches e Dados Salvos**
- `formatos_aprendidos.json`: Padrões de formato por classe
- `openfoodfacts_cache.json`: Cache de produtos da API externa
- `mobile_simulator.db`: Base de dados principal
- `pesquisa_bibliotecas_varejo.json`: Resultado de pesquisas de APIs

### **Configurações Ativas**
- YOLO: ✅ Habilitado
- OCR: ✅ Habilitado  
- Código de Barras: ✅ Habilitado
- OpenFoodFacts: ✅ Habilitado
- Base Conhecimento: ✅ Habilitado
- Aprendizado: ✅ Habilitado
- **MOT Tracking: ✅ Habilitado**

---

## 🔧 CONFIGURAÇÕES TÉCNICAS

### **Câmera IP**
- **Modelo**: Intelbras VIP-3430-D-IA
- **IP**: 192.168.68.108
- **Autenticação**: HTTPDigestAuth
- **Usuário**: admin
- **Resolução**: Configurável via API

### **Thresholds de Confiança**
- YOLO: 0.3 (30%)
- OCR: 0.7 (70%)
- Similaridade Texto: 0.6 (60%)
- **Tracking MOT: 0.4 (40%)**

### **Dependências Python Completas**
```
ultralytics>=8.0.0
pytesseract>=0.3.13
opencv-python>=4.5.0
pillow>=8.0.0
requests>=2.25.0
sqlite3 (built-in)
pyzbar>=0.1.9 (com fallback)
uuid (built-in)
collections (built-in)
datetime (built-in)
```

---

## 📈 EVOLUTION PATH DO SISTEMA

### **Versão Atual: Sistema Híbrido Completo + MOT**
- ✅ Detecção YOLO + OCR + Código de Barras
- ✅ Integração com bases externas (OpenFoodFacts)
- ✅ Base de conhecimento de varejo
- ✅ **Sistema MOT avançado com rastreamento visual**
- ✅ **Detecção automática de passagem por zona**
- ✅ **Cálculo de características de movimento**
- ✅ Aprendizado adaptativo de formatos
- ✅ Validação inteligente com dimensões reais
- ✅ Interface responsiva com controles completos

### **Próximas Evoluções Possíveis**
- 🔄 **Análise de padrões de movimento suspeitos**
- 🔄 **Alertas automáticos para múltiplas passagens**
- 🔄 **Relatórios de fluxo de produtos**
- 🔄 Integração com mais APIs de produtos
- 🔄 Sistema de alertas em tempo real
- 🔄 Integração com sistemas de segurança
- 🔄 Machine Learning para comportamentos anômalos

---

## 📋 CHECKLIST DE FUNCIONALIDADES

### **Detecção e Reconhecimento**
- [x] YOLO para produtos treinados
- [x] OCR para texto em produtos
- [x] Detecção de código de barras
- [x] Busca em base de dados local
- [x] Integração OpenFoodFacts
- [x] Reconhecimento de marcas conhecidas
- [x] Padrões de código brasileiro

### **⭐ Rastreamento (MOT)**
- [x] **Criação de tracks únicos com UUID**
- [x] **Associação inteligente de detecções**
- [x] **Cálculo de trajetória e movimento**
- [x] **Detecção automática de passagem por zona**
- [x] **Visualização de tracks coloridos**
- [x] **Estatísticas MOT em tempo real**
- [x] **Limpeza automática de tracks perdidos**
- [x] **Histórico completo de movimentos**

### **Aprendizado e Validação**
- [x] Aprendizado de formatos
- [x] Validação com dimensões reais
- [x] Cache inteligente
- [x] Persistência de dados

### **Interface e Visualização**
- [x] **Visualização de tracks com cores únicas**
- [x] **Trajetórias de movimento visíveis**
- [x] **Indicadores de passagem por zona**
- [x] **Estatísticas MOT na tela**
- [x] Informações completas por produto
- [x] Controles de sistema
- [x] Lista responsiva de produtos

---

## 🏆 RESUMO DO SISTEMA MOT

O sistema MOT (Multi-Object Tracking) implementado no VerifiK é capaz de:

1. **🎯 Rastrear** produtos individualmente com IDs únicos
2. **🌈 Marcar** visualmente cada produto com cor específica  
3. **📏 Calcular** características de movimento (velocidade, direção)
4. **🚪 Detectar** quando produtos passam pela zona de controle
5. **📊 Gerar** estatísticas em tempo real
6. **🧹 Limpar** automaticamente tracks perdidos
7. **💾 Persistir** histórico completo de movimentos

Este sistema permite um controle preciso e inteligente do fluxo de produtos, essencial para sistemas de segurança e monitoramento de varejo.

---

*Este documento preserva todo o conhecimento adquirido pelo sistema VerifiK para reconhecimento e rastreamento inteligente de produtos com sistema MOT avançado. Última atualização: 28/11/2025*