# LOGOS Platform - Planos e Preços

## Arquitetura Multi-Tenant (SaaS)

O LOGOS é uma plataforma **multi-tenant** (multi-inquilino), permitindo servir tanto o **Grupo Lisboa** quanto **outros clientes externos**.

### Conceito Multi-Tenant

Cada empresa cliente (Organization) possui:
- ✅ Seus próprios dados isolados
- ✅ Usuários independentes
- ✅ Lojas/postos separados
- ✅ Integrações ERP próprias
- ✅ Personalização (logo, cores, domínio)

**Exemplo:**
- `dashboard.grupolisboa.com.br` → Grupo Lisboa
- `dashboard.redesulpostos.com.br` → Rede Sul Postos
- `dashboard.xyzconveniencia.com.br` → XYZ Conveniências

---

## Planos de Assinatura

### 🆓 FREE (Trial)
**R$ 0/mês - 30 dias**

- ✅ 1 loja/posto
- ✅ 5 usuários
- ✅ 2 câmeras VerifiK
- ✅ 1 integração ERP
- ✅ Dashboard de preços (Vibra)
- ✅ Suporte por email

**Ideal para:** Testar a plataforma

---

### 💼 BASIC
**R$ 497/mês**

- ✅ **3 lojas/postos**
- ✅ **15 usuários**
- ✅ **8 câmeras VerifiK**
- ✅ **3 integrações ERP**
- ✅ Dashboard completo
- ✅ Relatórios básicos
- ✅ Suporte prioritário

**Ideal para:** Pequenas redes (1-3 lojas)

---

### 🚀 PROFESSIONAL
**R$ 1.497/mês**

- ✅ **10 lojas/postos**
- ✅ **50 usuários**
- ✅ **40 câmeras VerifiK**
- ✅ **10 integrações ERP**
- ✅ Dashboard avançado
- ✅ Relatórios personalizados
- ✅ API access
- ✅ White-label (logo, cores)
- ✅ Domínio customizado
- ✅ Suporte telefônico

**Ideal para:** Redes médias (4-10 lojas)

---

### 🏢 ENTERPRISE
**Preço customizado**

- ✅ **Lojas ilimitadas**
- ✅ **Usuários ilimitados**
- ✅ **Câmeras ilimitadas**
- ✅ **ERPs ilimitados**
- ✅ Tudo do Professional +
- ✅ **Suporte dedicado 24/7**
- ✅ **Onboarding personalizado**
- ✅ **Treinamento da equipe**
- ✅ **SLA garantido 99.9%**
- ✅ **Backup dedicado**
- ✅ **Servidor dedicado (opcional)**

**Ideal para:** Grandes redes (10+ lojas) e holdings

---

## ERPs Suportados

### Postos de Combustível
- ✅ **WebPostos** (usado por Postos Lisboa)
- ✅ **Linx Sistemas** (líder no setor)
- ✅ **SAP Business One**
- ✅ **TOTVS Protheus**
- ✅ Sistema customizado (via API)

### Varejo/Conveniência
- ✅ **Bling ERP** (e-commerce + PDV)
- ✅ **Tiny ERP**
- ✅ **Omie**
- ✅ **Conta Azul**
- ✅ **Sankhya**
- ✅ **Senior Sistemas**

### Delivery/Food Service
- ✅ **iFood** (integração oficial)
- ✅ **Uber Eats**
- ✅ **Rappi**
- ✅ **Zé Delivery** (portal parceiro)

### Franquias
- ✅ **Portal Subway** (franqueado)
- ✅ Outros portais de franquia

---

## Recursos por Módulo

### 📊 Dashboard Central
- Visão unificada de todas as lojas
- Métricas em tempo real
- Comparação de preços (combustíveis)
- Alertas automáticos

### 🔗 ERP Hub
- Acesso único a todos os ERPs
- Single Sign-On (SSO)
- Sincronização automática
- Dados consolidados

### 📹 VerifiK (Prevenção de Perdas)
- Detecção de produtos via IA
- Comparação PDV vs Câmera
- Alertas de discrepância
- Relatórios de perdas

### 💰 Gestão Financeira
- Contas a pagar/receber
- Fluxo de caixa consolidado
- Relatórios por empresa
- Comparação multi-lojas

### 👥 RH Centralizado
- Folha de pagamento
- Controle de ponto
- Gestão de funcionários
- Relatórios por loja

---

## Modelo de Negócio

### Para Grupo Lisboa
- **Uso interno gratuito** (plano ENTERPRISE)
- **ROI:** Economia em licenças múltiplas de ERP
- **Eficiência:** Gestão centralizada de 6 empresas

### Para Clientes Externos
- **Receita recorrente** (MRR - Monthly Recurring Revenue)
- **Escalável:** Custo marginal baixo por cliente
- **Vertical:** Foco em postos, conveniências, delivery

### Projeção de Receita (Ano 1)

**Mês 1-3:** Grupo Lisboa (interno) + 5 clientes trial
**Mês 4-6:** 10 clientes pagantes (média R$ 800/mês)
**Mês 7-12:** 30 clientes pagantes (R$ 24.000/mês)

**MRR Ano 1:** R$ 24.000/mês
**ARR Ano 1:** R$ 288.000/ano

---

## Próximos Passos

### Fase 1: MVP (30 dias)
- [x] Landing page
- [x] Dashboard básico
- [x] Autenticação JWT
- [ ] Multi-tenant database
- [ ] Onboarding automático
- [ ] Integração 1 ERP (Linx ou Bling)

### Fase 2: Beta (60 dias)
- [ ] VerifiK integrado
- [ ] 3+ ERPs integrados
- [ ] White-label básico
- [ ] Gateway de pagamento
- [ ] 5 clientes beta

### Fase 3: Launch (90 dias)
- [ ] Todos ERPs principais
- [ ] Marketing digital
- [ ] Site comercial
- [ ] Vendas ativas
- [ ] Suporte estruturado

---

## Tecnologia

**Frontend:**
- Bootstrap 5 (responsivo)
- JavaScript vanilla
- Templates white-label

**Backend:**
- FastAPI (Python 3.14)
- PostgreSQL (multi-tenant)
- JWT authentication
- Celery + Redis (tarefas assíncronas)

**IA/ML:**
- YOLOv8 (detecção de objetos)
- OpenCV (processamento de vídeo)

**Infraestrutura:**
- UOL Host (inicial)
- AWS/Azure (escala)
- CDN para assets
- Backup diário

---

## Segurança Multi-Tenant

✅ **Isolamento de dados** - Cada org só acessa seus dados
✅ **Row-level security** - Filtros automáticos por organization_id
✅ **Credenciais criptografadas** - APIs keys e senhas encrypted
✅ **Audit log** - Rastreamento de todas as ações
✅ **Rate limiting** - Proteção contra abuso
✅ **HTTPS obrigatório** - SSL/TLS em produção
