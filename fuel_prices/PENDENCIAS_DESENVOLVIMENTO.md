# 📋 PENDÊNCIAS E MELHORIAS - PROJETO LOGOS

**Data:** 23 de Novembro de 2025  
**Última Atualização:** 23/11/2025

---

## 🎯 PROPÓSITO PRINCIPAL (NÃO MUDAR!)

### **VerifiK = Anti-Fraude PDV**
```
PROBLEMA REAL (25 anos de experiência Grupo Lisboa):
- Funcionários do caixa registram produtos mais baratos
- Maior perda das conveniências = fraude no PDV
- Cliente pega Heineken → Caixa registra Skol
- Prejuízo: R$ 10.000-50.000/mês em 11 lojas
```

**Solução VerifiK (MANTER):**
1. Câmera monitora produtos na mão do cliente
2. IA detecta: "Cliente pegou Heineken"
3. Sistema compara com PDV: "Registrou Skol" ❌
4. Incidente automático + alerta gestor
5. Evidência em vídeo (prova)

---

## 🔴 PRIORIDADE CRÍTICA (Bloqueadores - Fazer AGORA)

### **1. API de Detecção VerifiK** ⏰ 6h
**Status:** ❌ Não existe  
**Impacto:** Sistema não funciona sem isso  
**Descrição:**
```python
POST /api/verifik/detectar/
- Recebe: Imagem (foto ou frame de vídeo)
- Processa: YOLO detecta produtos
- Retorna: JSON com produtos detectados + confiança
- Salva: DeteccaoProduto no banco (opcional)
```

**Implementação:**
- [ ] Criar view `detectar_produtos()` em `verifik/views.py`
- [ ] Carregar modelo YOLO treinado
- [ ] Processar imagem e detectar
- [ ] Mapear classes YOLO → ProdutoMae
- [ ] Retornar JSON estruturado
- [ ] Adicionar rota em `verifik/urls.py`
- [ ] Testar com Heineken 330ml

**Bloqueio:** Sem isso, câmeras não detectam nada!

---

### **2. Dashboard Unificado** ⏰ 20h
**Status:** ❌ Não existe  
**Impacto:** Cliente precisa entrar em 3 sistemas  
**Descrição:**
Criar `/dashboard/` que mostra TUDO em uma tela:
- Resumo Fuel Prices (preços hoje, alertas)
- Resumo VerifiK (detecções hoje, incidentes abertos)
- Gráficos rápidos
- Alertas pendentes
- Ações rápidas

**Implementação:**
- [ ] Criar app `dashboard/`
- [ ] View com queries de todos módulos
- [ ] Template responsivo
- [ ] Cards com estatísticas
- [ ] Gráficos Chart.js
- [ ] Link no menu principal

**Bloqueio:** "Single pane of glass" é o diferencial #1!

---

### **3. Alertas Automáticos (Email + WhatsApp)** ⏰ 15h
**Status:** ❌ Modelos existem, mas não envia nada  
**Impacto:** Gestor não fica sabendo dos incidentes  
**Descrição:**
- Fuel Prices: PriceAlert dispara quando preço muda
- VerifiK: Incidente dispara quando fraude detectada
- Enviar via Email E WhatsApp (prioridade WhatsApp)

**Implementação:**
- [ ] Configurar SMTP Gmail em `settings.py`
- [ ] Integrar Twilio/Evolution API para WhatsApp
- [ ] Criar task/command `verificar_alertas.py`
- [ ] Template de email HTML bonito
- [ ] Template mensagem WhatsApp (curto e direto)
- [ ] Cron job rodar a cada 5 minutos
- [ ] Logs de envio

**Bloqueio:** Alerta que não avisa = inútil!

---

### **4. Conferência de Recebimento de Mercadorias (NF-e)** ⏰ 25h
**Status:** ❌ Não existe  
**Impacto:** Evita prejuízo no recebimento (produtos errados, faltando)  
**Descrição:**
Cliente terá uma área dedicada para **RECEBER MERCADORIAS** e o **VerifiK irá CONFERIR** automaticamente se os produtos vieram corretos comparando com a Nota Fiscal.

**Fluxo:**
1. Fornecedor entrega mercadorias
2. Cliente posiciona produtos na área de conferência (com câmera)
3. Upload XML da NF-e no sistema
4. VerifiK detecta produtos via câmera (YOLO)
5. Sistema compara: **NF-e vs Produtos Detectados**
6. Alerta divergências:
   - ❌ Produto na nota MAS NÃO veio físico (falta)
   - ❌ Produto físico MAS NÃO está na nota (excesso)
   - ❌ Quantidade divergente (nota: 10 un, detectado: 8 un)
7. Gera relatório de conferência com evidências (foto/vídeo)
8. Aceitar/Rejeitar recebimento

**Benefícios:**
- Evita aceitar mercadoria errada
- Prova visual contra fornecedor
- Automatiza conferência manual
- Reduz tempo de recebimento (de 30min → 5min)

**Implementação:**
- [ ] Criar modelo `RecebimentoMercadoria`
  - NF-e (XML upload)
  - Data/hora recebimento
  - Fornecedor
  - Status (conferindo, aprovado, rejeitado)
- [ ] Criar modelo `ItemNFe` (parseado do XML)
  - Produto (descrição, código, quantidade)
  - Valor unitário
- [ ] Criar modelo `ConferenciaItem`
  - ItemNFe FK
  - Quantidade detectada (via IA)
  - Status (OK, faltando, excesso)
  - Evidência (foto/frame)
- [ ] Parser XML NF-e → extrair produtos
- [ ] Tela "Nova Conferência" (upload XML)
- [ ] Tela "Área de Conferência" (câmera ativa)
  - Detecção em tempo real (YOLO)
  - Marcar produtos conforme detecta
  - Contador visual (5/10 detectados)
- [ ] Algoritmo de matching (NF-e ↔ Detecção)
  - Por código de barras (preferencial)
  - Por descrição (ML/similaridade)
- [ ] Relatório de divergências
  - Lista faltantes (vermelho)
  - Lista excedentes (amarelo)
  - Lista OK (verde)
  - Botão: Aceitar / Rejeitar / Contestar
- [ ] Integração com sistema fornecedor (opcional)
  - Enviar contestação automática
  - PDF relatório com evidências
- [ ] Histórico de recebimentos
  - Filtrar por fornecedor, período, status
  - Métricas: % divergências por fornecedor

**Bloqueio:** Evita prejuízo milionário em recebimento errado!

---

### **5. Treinar 20 Produtos YOLO** ⏰ 30h
**Status:** ⏳ Heineken 330ml em andamento (24 imagens)  
**Impacto:** Só detecta 1 produto = sistema incompleto  
**Prioridade:** PRODUTOS MAIS FURTADOS (experiência 25 anos)

**Lista sugerida (ajustar conforme sua realidade):**

**Cervejas (alto valor):**
1. ✅ Heineken 330ml Long Neck
2. ⏳ Heineken 600ml
3. ⏳ Stella Artois 330ml
4. ⏳ Corona 330ml
5. ⏳ Budweiser 330ml
6. ⏳ Skol Pilsen 269ml
7. ⏳ Brahma Duplo Malte 350ml

**Destilados (maior prejuízo):**
8. ⏳ Whisky Red Label
9. ⏳ Whisky Black Label
10. ⏳ Jack Daniels
11. ⏳ Vodka Smirnoff
12. ⏳ Gin Tanqueray

**Energéticos/Isotônicos:**
13. ⏳ Red Bull 250ml
14. ⏳ Monster 473ml
15. ⏳ Gatorade 500ml

**Cigarros (alto furto):**
16. ⏳ Marlboro Red
17. ⏳ Marlboro Gold
18. ⏳ Lucky Strike

**Outros:**
19. ⏳ Redbull Tropical (específico)
20. ⏳ Barrinha Lacta (teste baixo valor)

**Implementação:**
- [ ] Fotografar 20-30 imagens de cada produto (vários ângulos)
- [ ] Upload no admin VerifiK
- [ ] Script treinar_todos_produtos.py
- [ ] Testar acurácia (mínimo 85%)
- [ ] Ajustar se necessário

**Tempo:** 1h fotografia/produto + 30min treino = 30h total

---

## 🟡 PRIORIDADE ALTA (Melhoram Venda - 30 dias)

### **5. Cache de Códigos de Barras** ⏰ 6h
**Status:** ❌ Não existe  
**Impacto:** Performance ruim  
**Descrição:**
Buscar código de barras no banco a cada detecção é lento.
Criar cache em memória/Redis.

**Implementação:**
- [ ] Redis ou cache Django
- [ ] Carregar todos códigos na inicialização
- [ ] Lookup O(1) ao invés de query
- [ ] Invalidar cache ao adicionar produto novo

---

### **6. Exportação Relatórios (Excel/PDF)** ⏰ 10h
**Status:** ❌ Não existe  
**Impacto:** Cliente quer dados fora do sistema  
**Descrição:**
- Relatório mensal incidentes VerifiK
- Relatório semanal preços Fuel
- Exportar Excel (pandas/openpyxl)
- Exportar PDF (weasyprint/reportlab)

**Implementação:**
- [ ] Botão "Exportar" nas listagens
- [ ] View gerar_relatorio_excel()
- [ ] View gerar_relatorio_pdf()
- [ ] Templates bonitos
- [ ] Download automático

---

### **7. Onboarding Wizard** ⏰ 20h
**Status:** ❌ Não existe  
**Impacto:** Cliente não sabe configurar  
**Descrição:**
Wizard ao primeiro login:
1. Bem-vindo ao LOGOS
2. Escolher módulos (Fuel, VerifiK, ambos)
3. Cadastrar lojas/postos
4. Configurar câmeras (se VerifiK)
5. Upload 10 fotos produtos
6. Configurar alertas (WhatsApp)
7. Pronto! Tour guiado

**Implementação:**
- [ ] Detectar primeiro login
- [ ] Multi-step form (5 passos)
- [ ] Progress bar
- [ ] Salvar preferências
- [ ] Redirect para dashboard

---

## 🟢 PRIORIDADE MÉDIA (60-90 dias)

### **8. App Mobile React Native** ⏰ 80h
**Status:** ❌ Não existe  
**Impacto:** Gestor quer ver alertas no celular  
**Descrição:**
App nativo iOS/Android:
- Login
- Dashboard (resumo)
- Alertas push
- Ver incidentes (foto/vídeo)
- Aprovar/rejeitar incidente
- Ver preços combustíveis

**Implementação:**
- [ ] Setup React Native
- [ ] Autenticação JWT
- [ ] Telas principais (5-6)
- [ ] Push notifications (Firebase)
- [ ] Build iOS/Android
- [ ] Publicar App Store/Play Store

---

### **9. ~~Integração NF-e (PlugNotas/TecnoSpeed)~~ → MOVIDO PARA #4**
**Status:** ✅ Já incluído na funcionalidade de **Conferência de Recebimento**  
**Descrição:** Parser XML NF-e está implementado dentro do módulo de conferência (item #4 Crítico)

---

### **10. Multi-tenancy Real (Isolamento de Dados)** ⏰ 20h
**Status:** ⏳ Organization existe, mas não isola tudo  
**Impacto:** Segurança + escalabilidade  
**Descrição:**
- Cada empresa vê APENAS seus dados
- Queryset filtering automático
- Permissões granulares
- Usuários não vazam entre orgs

**Implementação:**
- [ ] Middleware tenant-aware
- [ ] Override QuerySet padrão
- [ ] Testes isolamento
- [ ] Admin por organização

---

## ⚪ BAIXA PRIORIDADE (Nice to have)

### **11. Testes Automatizados** ⏰ 30h
- Unit tests (models, views)
- Integration tests (API)
- E2E tests (Selenium/Playwright)
- Coverage > 80%

### **12. Documentação API (Swagger)** ⏰ 8h
- OpenAPI spec
- Swagger UI
- Exemplos de uso
- Autenticação

### **13. Analytics/Métricas** ⏰ 15h
- Google Analytics
- Mixpanel/Amplitude
- Dashboard métricas internas
- A/B testing

---

## 💡 MÓDULOS ADICIONAIS (Sugestões Copilot - Análise Futura)

### **A. Conferência Rápida de Estoque** ⏰ 40h
**Ideia:** Usar mesma IA do VerifiK para outro caso de uso  
**Problema:** Recebimento mercadoria demora 30-45min  
**Solução:**
1. Funcionário tira foto do pallet
2. IA detecta e conta produtos
3. Compara com nota fiscal
4. Alerta divergências
5. Atualiza estoque

**Vantagem:**
- Aproveita código VerifiK existente
- Mesmo modelo YOLO
- Mercado adicional (pequenos clientes)
- Preço mais baixo R$ 199-299/mês

**Quando fazer:** Após VerifiK anti-fraude consolidado (100+ clientes)

---

### **B. GED Básico (Gestão Documentos)** ⏰ 30h
**Problema:** RH de 11 lojas = muito papel  
**Solução:**
- Upload documentos funcionários (PDF)
- Alertas vencimento (CNH, ASO, etc)
- Busca rápida
- Categorização

**Quando fazer:** Após módulos core prontos

---

### **C. Conciliação Bancária** ⏰ 80h
**Problema:** Fechar caixa é manual  
**Solução:**
- Importar OFX banco
- Comparar com vendas
- Detectar divergências
- Relatório fechamento

**Quando fazer:** Após 50+ clientes (justifica investimento)

---

## 📊 RESUMO EXECUTIVO

### **Próximos 30 dias (105h investidas):**
```
✅ API VerifiK Detecção (6h) → BLOQUEADOR
✅ Dashboard Unificado (20h) → DIFERENCIAL
✅ Alertas WhatsApp (15h) → CRÍTICO
✅ Conferência Recebimento NF-e (25h) → EVITA PREJUÍZO MILHÕES
✅ Treinar 20 produtos (30h) → CORE PRODUCT
✅ Cache códigos barras (6h) → PERFORMANCE
✅ Exportação relatórios (10h) → BÁSICO

Total: 112h = PRODUTO VENDÁVEL + CONFERÊNCIA
```

### **Meses 2-3 (100h):**
```
✅ Onboarding wizard (20h)
✅ App mobile (80h)
✅ Multi-tenancy (20h)

Total: 120h = PRODUTO ESCALÁVEL
(NF-e já incluída em Conferência Recebimento)
```

### **Após consolidação:**
```
⏳ Conferência estoque (40h) → Novo mercado
⏳ GED básico (30h) → Cross-sell
⏳ Conciliação bancária (80h) → Premium
```

---

## 🎯 FOCO ATUAL

**OBJETIVO:** VerifiK funcionando 100% para:
1. **Anti-fraude PDV** (problema original - 25 anos experiência)
2. **Conferência de Recebimento** (novo módulo - evita prejuízo milhões)

**Validação com Grupo Lisboa:**
- ✅ 11 conveniências
- ✅ 25 anos experiência
- ✅ Problema #1 confirmado: furto PDV funcionário
- ✅ Prejuízo PDV: R$ 10-50k/mês
- ✅ **NOVO:** Problema #2 identificado: recebimento errado de fornecedor
- ✅ **NOVO:** Prejuízo recebimento: R$ 5-20k/mês (produtos faltando, divergências NF-e)
- ✅ **ROI combinado:** R$ 15-70k/mês economizado
- ✅ ROI claro: Pegar 1 funcionário desonesto = R$ 5-10k/mês
- ✅ **ROI adicional:** Evitar 1 recebimento errado/mês = R$ 5-20k economizado

**Após validação → Vender para outros grupos com mesmo problema!**

---

## 📝 OBSERVAÇÕES

1. **NÃO** mudar propósito VerifiK anti-fraude
2. **MANTER** foco em detecção PDV
3. **ADICIONAR** módulos complementares depois
4. **PRIORIZAR** o que bloqueia venda
5. **VALIDAR** com Grupo Lisboa antes de escalar

---

**Última atualização:** 23/11/2025  
**Responsável:** Marcos Lisboa  
**Copilot:** GitHub Copilot (Assistente)
