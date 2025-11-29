# 🚀 SCRAPER VIBRA - EXECUTÁVEL STANDALONE

## 📋 Visão Geral

Este é um sistema independente que coleta preços de combustíveis do portal Vibra Energia e alimenta automaticamente o sistema principal Fuel Prices.

### ✨ Características

- **🔧 Completamente Independente**: Não precisa do Django instalado
- **🤖 Automação Completa**: Login automático, navegação e extração de dados
- **📡 Integração Automática**: Envia dados direto para o sistema principal
- **💾 Backup Local**: Salva cópia dos dados coletados
- **🎯 Seleção Flexível**: Processar todos os postos ou apenas específicos

## 🛠️ Como Criar o Executável

### 1. Preparação
```bash
cd "C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus"
```

### 2. Executar o Script de Criação
```bash
criar_executavel_scraper.bat
```

O script irá:
- ✅ Verificar Python e pip
- ✅ Instalar PyInstaller (se necessário)  
- ✅ Instalar dependências (playwright, requests)
- ✅ Baixar browser Chromium
- ✅ Gerar executável em `dist/ScraperVibra.exe`

## 🚀 Como Usar o Executável

### 1. Preparar o Sistema Principal
Certifique-se que o sistema Django está rodando:
```bash
cd "C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus"
python manage.py runserver
```

### 2. Executar o Scraper
Duplo clique em `dist/ScraperVibra.exe` ou execute via cmd:
```bash
ScraperVibra.exe
```

### 3. Selecionar Opção
```
🚀 SCRAPER VIBRA ENERGIA - EXECUTÁVEL STANDALONE
============================================================

Selecione uma opção:
1. Executar TODOS os postos (11 postos)
2. Executar postos específicos  
3. Executar apenas Casa Caiada (teste)
0. Sair

Digite sua opção (0-3): 
```

## 📊 Postos Disponíveis

| Código | Nome | CNPJ |
|--------|------|------|
| 95406 | AP CASA CAIADA | 04284939000186 |
| 107469 | POSTO ENSEADA DO NOR | 00338804000103 |
| 11236 | POSTO REAL | 24156978000105 |
| 1153963 | POSTO AVENIDA | 05428059000280 |
| 124282 | R J | 08726064000186 |
| 14219 | GLOBO105 | 41043647000188 |
| 156075 | POSTO BR SHOPPING | 07018760000175 |
| 1775869 | POSTO DOZE | 52308604000101 |
| 5039 | POSTO VIP | 03008754000186 |
| 61003 | P IGARASSU | 04274378000134 |
| 94762 | CIDADE PATRIMONIO | 05428059000107 |

## 🔄 Fluxo de Funcionamento

### 1. Coleta de Dados
- 🔑 Login automático no portal Vibra (Casa Caiada = posto master)
- 🏢 Alternância entre postos via CNPJ
- 📦 Extração de produtos (Etanol, Gasolina, Diesel, ARLA, GNV)
- 💰 Captura de preços, prazos e bases de distribuição

### 2. Envio para Sistema Principal
- 📡 POST para `http://127.0.0.1:8000/fuel/api/scraper-data/`
- 🎯 Criação/atualização automática de postos
- 💾 Salvamento de preços no banco Django
- ✅ Confirmação de recebimento

### 3. Backup e Logs
- 💾 Backup local: `backup_scraper_YYYYMMDD_HHMMSS.json`
- 📝 Logs detalhados com timestamps
- 🔍 Relatório final de sucessos/erros

## 🌐 APIs do Sistema Principal

### Receber Dados do Scraper
```
POST /fuel/api/scraper-data/
Content-Type: application/json

{
  "posto": {
    "codigo_vibra": "95406",
    "cnpj": "04284939000186", 
    "razao_social": "AUTO POSTO CASA CAIADA LTDA",
    "nome_fantasia": "AP CASA CAIADA"
  },
  "produtos": [
    {
      "nome": "ETANOL COMUM",
      "preco": "Preço: R$ 3,6377",
      "prazo": "30 dias",
      "base": "Base Suape"
    }
  ],
  "modalidade": "FOB"
}
```

### Verificar Status do Sistema
```
GET /fuel/api/status/

Response:
{
  "status": "online",
  "sistema": "Fuel Prices - Sistema Principal",
  "database": "conectado",
  "estatisticas": {
    "postos_ativos": 11,
    "precos_ultima_semana": 150
  }
}
```

## 🎯 Vantagens do Executável

### ✅ **Independência Total**
- Não precisa do Python instalado na máquina de destino
- Não precisa do Django ou dependências pesadas
- Arquivo único (.exe) de ~100MB

### ✅ **Facilidade de Distribuição**
- Copie o .exe para qualquer pasta
- Execute em qualquer Windows
- Sem configuração adicional

### ✅ **Automação Completa**
- Login automático com credenciais
- Navegação inteligente entre postos
- Tratamento de erros robusto
- Envio automático para sistema principal

### ✅ **Monitoramento**
- Logs detalhados em tempo real
- Backup local dos dados
- Relatório final de execução
- Interface amigável no terminal

## 🛡️ Tratamento de Erros

- **Sistema Principal Offline**: Salva backup local e informa
- **Erro de Login**: Tenta novamente e reporta
- **Posto Indisponível**: Pula e continua com próximo
- **Produto sem Preço**: Ignora produto e continua
- **Timeout de Rede**: Retry automático

## 🔧 Configurações Avançadas

### Alterar URL do Sistema Principal
Edite no arquivo `scraper_standalone.py`:
```python
self.api_url_base = "http://SEU_SERVIDOR:8000/api"
```

### Alterar Credenciais
```python
scraper = VibraScraperStandalone(
    username='SEU_USUARIO',
    password='SUA_SENHA', 
    headless=True  # False = mostrar navegador
)
```

## 📁 Estrutura de Arquivos

```
ProjetoLogus/
├── scraper_standalone.py          # Código principal do scraper
├── requirements_scraper.txt       # Dependências mínimas
├── scraper_vibra.spec            # Configuração PyInstaller  
├── criar_executavel_scraper.bat  # Script de criação
├── fuel_prices/
│   └── api_scraper.py            # APIs para receber dados
└── dist/
    └── ScraperVibra.exe          # Executável final
```

## 🎉 Resultado Final

Após a execução bem-sucedida:
- 📊 Dashboard Fuel Prices atualizado automaticamente
- 💾 Dados salvos no banco Django
- 🕒 Histórico de preços disponível
- 📈 Gráficos e análises atualizados

O executável é uma solução completa e independente para manter o sistema Fuel Prices sempre atualizado com os preços mais recentes do portal Vibra Energia!