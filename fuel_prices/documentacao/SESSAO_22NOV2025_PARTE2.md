# SESSÃO 22/11/2025 - PARTE 2
## Sistema de Coleta de Preços Vibra Energia

---

## 📋 RESUMO DA SESSÃO

### Objetivo Principal
Implementar sistema de coleta de preços via interface web com seleção de postos pelo usuário.

---

## ✅ IMPLEMENTAÇÕES CONCLUÍDAS

### 1. **Dashboard Consolidado Melhorado**
- ✅ Removido código Vibra da exibição (mostra apenas nome do posto)
- ✅ Adicionado botão "Coletar Preços Agora" no cabeçalho
- ✅ Modal de seleção de postos implementado
- ✅ Checkbox "Selecionar Todos" funcional
- ✅ Cálculo automático de tempo estimado (2 min/posto)
- ✅ Aviso de tempo de resposta para o usuário

**Arquivo:** `fuel_prices/templates/fuel_prices/dashboard_consolidado.html`

### 2. **Adição de Todos os Postos no Banco**
- ✅ Script criado: `fuel_prices/adicionar_todos_postos.py`
- ✅ 11 postos do Grupo Lisboa adicionados:
  1. AP CASA CAIADA (04284939000186)
  2. POSTO ENSEADA DO NOR (00338804000103)
  3. POSTO REAL (24156978000105)
  4. POSTO AVENIDA (05428059000280)
  5. R J (08726064000186)
  6. GLOBO105 (41043647000188)
  7. POSTO BR SHOPPING (07018760000175)
  8. POSTO DOZE (52308604000101)
  9. POSTO VIP (03008754000186)
  10. P IGARASSU (04274378000134)
  11. CIDADE PATRIMONIO (05428059000107)

### 3. **Página Inicial do Sistema**
- ✅ Template criado: `fuel_prices/templates/home.html`
- ✅ Design com gradiente roxo e cards Bootstrap 5
- ✅ Link funcional para módulo Fuel Prices
- ✅ Cards para módulos futuros (Relatórios, Gestão)

### 4. **Correção de Rotas**
**Problema:** Link "Fuel Prices" na página principal do Logos com `href="#"`

**Solução:**
- ✅ Arquivo `templates/home.html` modificado
- ✅ Links `href="#"` alterados para `href="/fuel/"`
- ✅ Rota já existia em `logos/urls.py`: `path('fuel/', include('fuel_prices.urls'))`

### 5. **URLs Corrigidas**
**Arquivo:** `fuel_prices/urls.py`

**Antes (ERRADO):**
```python
path('', views.home, name='home'),
path('fuel/', views.dashboard_consolidado, name='dashboard_consolidado'),
path('fuel/executar-scraper/', views.executar_scraper, name='executar_scraper'),
```

**Depois (CORRETO):**
```python
path('', views.dashboard_consolidado, name='dashboard_consolidado'),
path('executar-scraper/', views.executar_scraper, name='executar_scraper'),
```

**Motivo:** App já montado em `/fuel/` no urls.py principal, não repetir prefixo.

### 6. **Scraper com Argumentos CLI**
**Arquivo:** `fuel_prices/scrapers/vibra_scraper.py`

**Funcionalidade:**
```python
if __name__ == '__main__':
    parser.add_argument('--cnpjs-file', help='Arquivo JSON com CNPJs')
    parser.add_argument('--cnpjs', nargs='+', help='Lista de CNPJs')
```

**Comportamento:**
1. Login com credenciais fixas: `95406/Apcc2350`
2. Troca para cada posto selecionado pelo usuário
3. Coleta preços apenas dos postos selecionados
4. **NÃO** adiciona Casa Caiada automaticamente

### 7. **Execução em Background**
**Arquivo:** `fuel_prices/views.py`

**Função:** `executar_scraper(request)`

**Implementação:**
```python
import threading

def run_scraper_background(cnpjs, status_dict):
    # Executa scraper em thread separada
    # Não bloqueia resposta HTTP
    
thread = threading.Thread(target=run_scraper_background, args=(cnpjs, status))
thread.daemon = True
thread.start()

return JsonResponse({
    'status': 'started',
    'tempo_estimado': len(cnpjs) * 2
})
```

**Vantagens:**
- ✅ Resposta imediata ao usuário (1-2 segundos)
- ✅ Scraper roda em background
- ✅ Não trava navegador
- ✅ Sem timeout HTTP

### 8. **Mensagens de Erro Detalhadas**
**Template:** `dashboard_consolidado.html`

**Mensagens implementadas:**
```javascript
// Sucesso
alert('✅ Coleta iniciada em background!\n\n' +
      '📊 Postos selecionados: X\n' +
      '⏱️ Tempo estimado: Y minutos\n\n' +
      '⚠️ Se houver erro, verifique console do servidor.');

// Erro de comunicação
alert('❌ Erro de comunicação:\n\n' +
      'Possíveis causas:\n' +
      '• Servidor Django não está rodando\n' +
      '• Problema de conexão\n' +
      '• Erro no código do scraper');
```

**Logs no servidor:**
```python
print("🚀 Iniciando scraper para X posto(s)...")
print("✅ Scraper concluído. Importando dados...")
print("✅ Importação concluída com sucesso!")
print("❌ Erro no scraper:", error)
```

---

## ⚠️ PROBLEMA ATUAL (NÃO RESOLVIDO)

### **UnicodeEncodeError no Windows**

**Erro:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f3af' in position 2
```

**Causa:** Console do Windows (cmd/PowerShell) usa encoding `cp1252`, não suporta emojis UTF-8.

**Linha do erro:**
```python
print(f"\n🎯 Processando {len(postos_selecionados)} posto(s) selecionado(s)")
```

**Tentativa de correção:**
```python
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

**Status:** ⏳ Correção aplicada mas não testada

**Solução alternativa (se não funcionar):**
Remover todos os emojis dos prints no `vibra_scraper.py`:
```python
# Trocar
print("🎯 Processando...")
# Por
print("[INFO] Processando...")
```

---

## 🗂️ ESTRUTURA DE ARQUIVOS

```
ProjetoLogus/
├── logos/
│   └── urls.py                          # path('fuel/', include('fuel_prices.urls'))
├── templates/
│   └── home.html                        # Página principal (corrigido href="/fuel/")
├── fuel_prices/
│   ├── models.py                        # PostoVibra, PrecoVibra
│   ├── views.py                         # executar_scraper(), dashboard_consolidado()
│   ├── urls.py                          # Rotas corrigidas (sem prefixo 'fuel/')
│   ├── adicionar_todos_postos.py        # Script para adicionar 11 postos
│   ├── scrapers/
│   │   └── vibra_scraper.py             # Aceita --cnpjs-file, encoding UTF-8
│   └── templates/
│       ├── home.html                    # Página inicial do módulo
│       └── fuel_prices/
│           └── dashboard_consolidado.html  # Modal de seleção, botão scraper
└── import_vibra_data.py                 # Importa JSON para banco
```

---

## 🔧 COMANDOS ÚTEIS

### Iniciar servidor
```powershell
cd c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus
python manage.py runserver
```

### Adicionar todos os postos
```powershell
python fuel_prices\adicionar_todos_postos.py
```

### Executar scraper manualmente (teste)
```powershell
python fuel_prices\scrapers\vibra_scraper.py
```

### Importar dados manualmente
```powershell
python import_vibra_data.py
```

---

## 🌐 URLs DO SISTEMA

| URL | Descrição |
|-----|-----------|
| http://127.0.0.1:8000/ | Página principal Logos |
| http://127.0.0.1:8000/fuel/ | Dashboard consolidado |
| http://127.0.0.1:8000/fuel/executar-scraper/ | Endpoint do scraper (POST) |
| http://127.0.0.1:8000/fuel/por-produto/ | Dashboard por produto |
| http://127.0.0.1:8000/fuel/por-posto/ | Dashboard por posto |
| http://127.0.0.1:8000/admin/ | Django Admin |

---

## 📊 FLUXO DE EXECUÇÃO DO SCRAPER

```mermaid
1. Usuário acessa /fuel/
2. Clica "Coletar Preços Agora"
3. Seleciona postos (1 a 11)
4. Vê tempo estimado (N × 2 minutos)
5. Clica "Iniciar Coleta"
   ↓
6. JavaScript: POST /fuel/executar-scraper/
   ↓
7. View: Cria thread background
8. View: Retorna {status: 'started'} (imediato)
   ↓
9. Thread: Executa python vibra_scraper.py --cnpjs-file temp.json
10. Thread: Login com 95406/Apcc2350
11. Thread: Para cada posto selecionado:
    - Troca para posto
    - Coleta preços
    - Salva em JSON
   ↓
12. Thread: Executa import_vibra_data.py
13. Thread: Importa JSON para banco Django
   ↓
14. Frontend: setTimeout(() => location.reload(), tempo_estimado)
15. Usuário vê dados atualizados
```

---

## 🐛 PROBLEMAS CONHECIDOS

### 1. ⚠️ **Encoding UTF-8 no Windows** (ATUAL)
- **Status:** Em correção
- **Impacto:** Scraper não executa
- **Solução:** Remover emojis ou configurar stdout UTF-8

### 2. ⚠️ **Posto Real intermitente**
- **Sintoma:** Às vezes retorna 0 produtos
- **Causa:** Menu aparece ao invés de lista de produtos
- **Solução futura:** Aumentar wait time ou adicionar retry

### 3. ✅ **Database save async** (RESOLVIDO)
- **Solução atual:** Script `import_vibra_data.py` separado
- **Funciona:** Sim, via import manual após scraping

---

## 📝 PRÓXIMOS PASSOS

### Imediato (Prioridade Alta)
1. ✅ Testar correção de encoding UTF-8
2. ⏳ Se falhar: Remover emojis dos prints
3. ⏳ Testar scraper via web com 2-3 postos
4. ⏳ Verificar importação automática após scraper

### Curto Prazo
5. ⏳ Adicionar indicador visual de progresso (websocket ou polling)
6. ⏳ Implementar retry automático para postos que falharem
7. ⏳ Aumentar timeout para Posto Real
8. ⏳ Testar com todos os 11 postos simultaneamente

### Médio Prazo
9. ⏳ Implementar histórico de coletas
10. ⏳ Gráficos de variação de preços
11. ⏳ Alertas de preço (email/WhatsApp)
12. ⏳ Agendamento automático (Celery + Redis)

---

## 💡 OBSERVAÇÕES IMPORTANTES

1. **Login único:** Sistema faz login UMA VEZ com Casa Caiada (95406), depois troca para postos selecionados. Casa Caiada NÃO é processado automaticamente.

2. **Background execution:** Scraper roda em thread daemon. Se servidor Django reiniciar, thread é perdida.

3. **Timeout:** 10 minutos por execução completa (600s). Se 11 postos × 2 min = 22 min, pode dar timeout.

4. **Auto-reload:** Página recarrega após `tempo_estimado + 15s`. Usuário pode recarregar manualmente antes.

5. **Logs:** Todos os logs aparecem no console do servidor Django, não no navegador.

---

## 🔒 CREDENCIAIS

**Portal Vibra Energia:**
- URL: https://cn.vibraenergia.com.br/login/
- Usuário: `95406` (Casa Caiada)
- Senha: `Apcc2350`

---

## 📞 CONTATO/REFERÊNCIAS

**Sessão anterior:** `SESSAO_21NOV2025.txt`
**Configuração de acesso:** `CONFIG_ACESSO.txt`

---

**Data:** 22/11/2025 01:40
**Status:** Sistema funcional, pendente correção de encoding UTF-8
**Próxima ação:** Testar scraper via web após correção de encoding
