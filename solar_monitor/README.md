# ☀️ Solar Monitor - Monitoramento de Usinas Solares

Sistema de monitoramento em tempo real das usinas solares do Grupo Lisboa.

## 📋 Funcionalidades

### ✅ Implementado

- **Dashboard em Tempo Real**
  - Visualização de todas as usinas ativas
  - Estatísticas gerais (capacidade instalada, potência atual, energia do dia)
  - Status online/offline de cada usina
  - Alertas pendentes

- **Models Completos**
  - `UsinaSolar`: Cadastro de usinas com localização GPS, capacidade, dados do inversor
  - `LeituraUsina`: Leituras em tempo real (potência, energia, temperatura, tensão, etc.)
  - `AlertaUsina`: Sistema de alertas com níveis (info, aviso, alerta, crítico)
  - `RelatorioMensal`: Relatórios consolidados mensais

- **Admin Interface**
  - Interface administrativa completa para gestão de usinas
  - Visualização de leituras com filtros e busca
  - Gestão de alertas com ações em massa
  - Relatórios mensais

- **APIs JSON**
  - `/api/usina/<id>/realtime/`: Dados em tempo real de uma usina
  - `/api/status-geral/`: Status de todas as usinas

## 🚀 Como Usar

### 1. Aplicar Migrations

```bash
python manage.py makemigrations solar_monitor
python manage.py migrate solar_monitor
```

### 2. Popular Dados de Teste

```bash
python populate_solar_data.py
```

Isso criará:
- 3 usinas solares (Matriz, Filial Norte, Filial Sul)
- ~270 leituras históricas (últimos 7 dias)
- 3 alertas de exemplo

### 3. Acessar o Sistema

1. Inicie o servidor:
```bash
python manage.py runserver
```

2. Faça login no sistema (usa o mesmo login do ProjetoLogos)

3. Acesse o dashboard:
```
http://localhost:8000/solar/
```

4. Acesse o admin:
```
http://localhost:8000/admin/solar_monitor/
```

## 📊 Estrutura de Dados

### UsinaSolar
- Nome, localização, capacidade (kWp)
- Coordenadas GPS (latitude, longitude)
- Data de instalação
- Informações do inversor (marca, modelo, API)
- Status ativo/inativo

### LeituraUsina
- Potência atual (kW)
- Energia gerada acumulada (kWh)
- Energia do dia (kWh)
- Irradiância solar (W/m²)
- Temperatura dos módulos e ambiente (°C)
- Dados elétricos (tensão, corrente, frequência)
- Eficiência e fator de potência
- CO₂ evitado e economia estimada (calculados automaticamente)
- Status (online, offline, manutenção, alerta, erro)

### AlertaUsina
- Tipo: informação, aviso, alerta, crítico
- Categoria: produção, temperatura, tensão, comunicação, eficiência, manutenção
- Título e descrição
- Status de resolução
- Timestamp e observações

### RelatorioMensal
- Energia total gerada no mês
- Média diária
- Potência pico
- Horas de sol pico
- CO₂ evitado total
- Economia total
- Eficiência média
- Dias offline

## 🔗 Integração com Sistema Existente

O `solar_monitor` está integrado ao sistema ProjetoLogos:

- ✅ Usa o mesmo sistema de autenticação (`@login_required`)
- ✅ Compartilha o modelo de usuários (`accounts.User`)
- ✅ URLs configuradas em `/solar/`
- ✅ Adicionado ao `INSTALLED_APPS` em `logos/settings.py`

## 🎨 URLs Disponíveis

```python
/solar/                              # Dashboard principal
/solar/usina/<id>/                   # Detalhes de uma usina
/solar/relatorios/                   # Relatórios mensais
/solar/alertas/                      # Gestão de alertas
/solar/api/usina/<id>/realtime/      # API JSON - dados em tempo real
/solar/api/status-geral/             # API JSON - status todas as usinas
```

## 📱 Views Criadas

1. **dashboard**: Página principal com resumo de todas as usinas
2. **usina_detalhes**: Detalhes completos de uma usina específica
3. **relatorios**: Página de relatórios mensais (com filtros)
4. **alertas**: Gestão de alertas (pendentes, resolvidos, todos)
5. **api_leituras_realtime**: API JSON para gráficos em tempo real
6. **api_status_geral**: API JSON para overview de todas as usinas

## 🔮 Próximos Passos

### Para Implementar

- [ ] Criar template `usina_detalhes.html` (gráficos de geração)
- [ ] Criar template `relatorios.html` (tabelas e exportação PDF)
- [ ] Criar template `alertas.html` (lista filtrada e resolução)
- [ ] Integração com API real dos inversores (Fronius, SMA, Huawei)
- [ ] Gráficos interativos com Chart.js ou Plotly
- [ ] WebSocket para atualização em tempo real (sem refresh)
- [ ] Exportação de relatórios (PDF, Excel)
- [ ] Sistema de notificações por e-mail/SMS
- [ ] Dashboard mobile responsivo
- [ ] Previsão de geração (machine learning)
- [ ] Comparação de performance entre usinas
- [ ] Integração com dados meteorológicos

### Integrações Sugeridas

1. **APIs de Inversores**
   - Fronius Solar API
   - SMA Sunny Portal
   - Huawei FusionSolar

2. **Dados Meteorológicos**
   - OpenWeatherMap
   - INMET (dados brasileiros)

3. **Notificações**
   - SendGrid (e-mail)
   - Twilio (SMS)
   - Telegram Bot

## 💡 Exemplos de Uso

### Criar Leitura via Python

```python
from solar_monitor.models import UsinaSolar, LeituraUsina
from decimal import Decimal

usina = UsinaSolar.objects.first()

leitura = LeituraUsina.objects.create(
    usina=usina,
    potencia_atual_kw=Decimal('125.5'),
    energia_gerada_kwh=Decimal('850.2'),
    energia_dia_kwh=Decimal('420.8'),
    irradiancia_w_m2=Decimal('850.0'),
    temperatura_modulo_c=Decimal('45.5'),
    status='online'
)
```

### Criar Alerta

```python
from solar_monitor.models import AlertaUsina

alerta = AlertaUsina.objects.create(
    usina=usina,
    tipo='critico',
    categoria='comunicacao',
    titulo='Perda de comunicação',
    descricao='Inversor não está respondendo há 30 minutos'
)
```

### Consultar Dados via API

```bash
# Status de todas as usinas
curl http://localhost:8000/solar/api/status-geral/

# Dados em tempo real de uma usina
curl http://localhost:8000/solar/api/usina/1/realtime/
```

## 📝 Notas Técnicas

- Auto-refresh do dashboard a cada 30 segundos
- Índices de banco de dados otimizados para consultas rápidas
- Cálculos automáticos de CO₂ e economia no método `save()`
- Suporte a múltiplos fusos horários (`USE_TZ = True`)
- Soft delete possível (campo `ativa` em UsinaSolar)

## 🎯 Métricas do Sistema

Após popular os dados de teste:
- ✅ 3 usinas cadastradas
- ✅ 1.130 kWp de capacidade total instalada
- ✅ 274 leituras históricas (7 dias)
- ✅ 3 alertas pendentes

---

**Desenvolvido para o Grupo Lisboa** | Parte do ecossistema ProjetoLogos
