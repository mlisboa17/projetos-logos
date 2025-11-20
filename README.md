# LOGUS - Ecossistema de Inovação Grupo Lisboa

![Logus](https://img.shields.io/badge/Status-Ativo-green)
![Versão](https://img.shields.io/badge/Vers%C3%A3o-1.0.0-blue)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-Propriet%C3%A1rio-red)

## 📋 Sobre o Projeto

**LOGUS** é o ecossistema de inovação tecnológica do **Grupo Lisboa**, desenvolvendo soluções inteligentes para os desafios do varejo. Cada projeto nasce da nossa experiência prática em postos de combustível e lojas de conveniência.

### 🌳 Estrutura do Ecossistema

```
LOGUS (Grupo Lisboa)
├── VerifiK - Sistema de Prevenção de Perdas por IA (Ativo)
├── Projeto 2 - Em planejamento
└── Projeto 3 - Em breve
```

### 🎯 Missão

Transformar problemas reais do varejo brasileiro em soluções tecnológicas de ponta, tornando o mercado mais eficiente, lucrativo e sustentável.

---

## 🚀 Projetos Ativos

### 1. VerifiK - Sistema de Prevenção de Perdas por IA

**Status**: ✅ Ativo (Em Desenvolvimento)

Sistema de Inteligência Artificial que detecta furtos internos em tempo real através de câmeras IP.

#### Problema que Resolve

- **Furto Interno**: Funcionários "esquecem" de registrar produtos
- **Erro de Registro**: Quantidade incorreta ou produto errado  
- **Falta de Visibilidade**: Impossível revisar todas as vendas manualmente

### 💰 Impacto Financeiro (VerifiK)

- **Perda média sem sistema**: 3-7% do faturamento
- **Perda média com sistema**: <1% do faturamento
- **ROI médio**: 60-90 dias
- **Redução de perdas**: 60-70%

---

## 🌐 Website Institucional

### Homepage LOGUS
- **Apresentação**: Grupo Lisboa e ecossistema de projetos
- **URL**: https://grupolisboa.com.br
- **Conteúdo**: Sobre o grupo + cards dos projetos

### Landing Page VerifiK
- **URL**: https://grupolisboa.com.br/verifik
- **Conteúdo**: Detalhamento completo do sistema de IA

---

## 🚀 Tecnologias Utilizadas

### Frontend (Websites)
- **HTML5** - Estrutura semântica
- **CSS3** - Design moderno (cores: ouro #C9A960 + verde #1B5E4D)
- **JavaScript ES6+** - Interatividade

### Backend (VerifiK - Em Desenvolvimento)
- **Python 3.11+** - Linguagem principal
- **FastAPI** - Framework web moderno e rápido
- **PostgreSQL** - Banco de dados relacional
- **Redis** - Cache e filas
- **Celery** - Tarefas assíncronas

### Inteligência Artificial
- **YOLOv8** - Detecção de objetos em tempo real
- **OpenCV** - Processamento de vídeo
- **PyTorch** - Framework de deep learning
- **TensorFlow** - Alternativa para modelos customizados

### Infraestrutura
- **Docker** - Containerização
- **Git/GitHub** - Controle de versão
- **Linux** - Servidor de produção

---

## 📁 Estrutura do Projeto

```
projetologos/
├── index.html                      # Homepage LOGUS (Grupo Lisboa)
├── verifik/
│   ├── index.html                  # Landing page VerifiK
│   └── assets/
│       ├── css/
│       │   └── style.css          # Estilos VerifiK
│       └── js/
│           └── main.js            # Scripts VerifiK
├── docs/
│   ├── README.txt                 # Documentação geral
│   ├── CONFIGURACOES_HARDWARE.txt # Guia de hardware (VerifiK)
│   └── POSICIONAMENTO_CAMERA.txt  # Instalação (VerifiK)
└── README.md                      # Este arquivo
```

---

## 🖥️ Hardware Recomendado

### Configuração Adequada (Recomendada)
- **Câmera**: Intelbras VIP 3430 Dome IA 4MP com PoE (R$ 730)
- **Switch**: Intelbras SF 400 Q+ PoE 4 portas (R$ 220)
- **Processamento**: PC com NVIDIA GTX 1650 ou superior
- **Cabo**: Cat6 até 30m (R$ 80)
- **Total**: ~R$ 1.090 (aproveitando PC existente)

### Por Caixa
- 1 câmera IP 4MP com PoE
- Processamento de 1-2 câmeras por GPU GTX 1650
- Distância ideal: 2-2.5m do balcão
- Ângulo: 30-45° para cobertura completa

---

## 🌐 Deploy da Landing Page

### Domínio
- **URL**: https://grupolisboa.com.br
- **Registro**: UOL Dominios
- **DNS**: ns1.dominios.uol.com.br

### Hospedagem UOL

#### 1️⃣ Acesso ao Painel
```
URL: https://painel.uolhost.uol.com.br
Login: [credenciais UOL]
```

#### 2️⃣ Upload via FTP
```bash
Host: grupolisboa.com.br
Porta: 21
Usuário: [seu usuário UOL]
Senha: [sua senha UOL]
Pasta destino: /public_html/
```

#### 3️⃣ Estrutura no Servidor
```
/public_html/
├── index.html
└── assets/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

#### 4️⃣ Upload via Gerenciador de Arquivos
1. Acesse o painel UOL Host
2. Vá em **Gerenciador de Arquivos**
3. Navegue até `/public_html/`
4. Faça upload de `index.html` e pasta `assets/`
5. Aguarde propagação DNS (até 24h)

---

## 🔧 Desenvolvimento Local

### Visualizar Landing Page
```bash
# Opção 1: Abrir direto no navegador
start index.html

# Opção 2: Servidor local Python
cd ProjetoLogus
python -m http.server 8000
# Acesse: http://localhost:8000

# Opção 3: Servidor local Node.js
npx http-server -p 8000
# Acesse: http://localhost:8000
```

### Estrutura de Arquivos
- `index.html` - Página única com todas as seções
- `assets/css/style.css` - Estilos completos (gradientes, animações, responsivo)
- `assets/js/main.js` - Scripts (menu mobile, scroll smooth, formulário, animações)

---

## 📊 Funcionalidades da Landing Page

### Seções Implementadas
- ✅ **Hero** - Apresentação impactante com estatísticas
- ✅ **Problema** - Cenários que o sistema resolve
- ✅ **Solução** - Como funciona a tecnologia VerifiK
- ✅ **Como Funciona** - 4 passos de instalação até uso
- ✅ **Diferenciais** - 6 pontos fortes do Logus
- ✅ **Planos** - 3 opções (Piloto, Profissional, Enterprise)
- ✅ **Depoimentos** - 3 casos de sucesso
- ✅ **CTA** - Call-to-action para demonstração
- ✅ **Contato** - Formulário funcional
- ✅ **Footer** - Links e informações

### Interatividade
- ✅ Menu mobile responsivo
- ✅ Scroll suave entre seções
- ✅ Animações on-scroll
- ✅ Validação de formulário
- ✅ Formatação automática de telefone
- ✅ Simulação de detecção em tempo real

---

## 🎨 Design System

### Cores
```css
--primary: #667eea        /* Roxo principal */
--secondary: #764ba2      /* Roxo escuro */
--accent: #f5576c         /* Rosa/vermelho */
--success: #10b981        /* Verde */
--warning: #f59e0b        /* Laranja */
--danger: #ef4444         /* Vermelho */
--dark-bg: #0f0f23        /* Fundo escuro */
--card-bg: #1a1a2e        /* Cards */
```

### Gradientes
```css
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
```

### Tipografia
- **Font**: Inter (Google Fonts)
- **Títulos**: 900 weight
- **Corpo**: 400-600 weight

---

## 📱 Responsividade

### Breakpoints
- **Desktop**: > 968px (layout completo)
- **Tablet**: 768px - 968px (grid ajustado)
- **Mobile**: < 768px (menu hamburger, coluna única)

### Testado em
- ✅ Chrome/Edge (desktop)
- ✅ Firefox (desktop)
- ✅ Safari (desktop)
- ⏳ Chrome Mobile (pendente)
- ⏳ Safari iOS (pendente)

---

## 🔐 Segurança & Privacidade

### LGPD Compliance
- Dados processados localmente
- Vídeos não saem da loja
- Formulário com consentimento
- Política de privacidade (em desenvolvimento)

### Próximos Passos
- [ ] Implementar HTTPS
- [ ] Adicionar certificado SSL
- [ ] Criar página de privacidade
- [ ] Implementar cookies consent

---

## 📈 Roadmap

### Fase 1 - Landing Page ✅
- [x] Design e estrutura
- [x] Responsividade
- [x] Interatividade
- [x] Formulário de contato

### Fase 2 - Backend API (Em Andamento)
- [ ] Setup FastAPI
- [ ] Integração com PostgreSQL
- [ ] Sistema de autenticação
- [ ] Endpoints de contato

### Fase 3 - Sistema de Detecção
- [ ] Integração com câmeras IP
- [ ] Modelo YOLOv8 treinado
- [ ] Comparação PDV vs Câmera
- [ ] Sistema de alertas

### Fase 4 - Dashboard
- [ ] Interface web React
- [ ] Visualização em tempo real
- [ ] Relatórios e análises
- [ ] Gerenciamento multi-loja

---

## 🤝 Equipe

### Grupo Lisboa
- **Domínio**: grupolisboa.com.br
- **Localização**: Recife, PE
- **Segmento**: Postos de combustível e conveniências

### Desenvolvimento
- Sistema desenvolvido especificamente para as necessidades do Grupo Lisboa
- Feedback inicial com diretoria antes de expansão

---

## 📞 Contato

- **Email**: contato@logus.com.br
- **Telefone**: (81) 9 9999-9999
- **WhatsApp**: [Link será adicionado]
- **Endereço**: Recife, PE

---

## 📄 Documentação Adicional

- [`README.txt`](README.txt) - Visão geral do projeto e modelo de negócio
- [`CONFIGURACOES_HARDWARE.txt`](CONFIGURACOES_HARDWARE.txt) - Guia completo de hardware
- [`POSICIONAMENTO_CAMERA.txt`](POSICIONAMENTO_CAMERA.txt) - Instruções de instalação

---

## 📝 Licença

© 2025 Logus - Grupo Lisboa. Todos os direitos reservados.

**Propriedade Intelectual**: Este projeto é propriedade exclusiva do Grupo Lisboa e não pode ser reproduzido, distribuído ou utilizado sem autorização expressa.

---

## 🚀 Quick Start

```bash
# 1. Clone o repositório
git clone [repository-url]
cd ProjetoLogus

# 2. Abra no navegador
start index.html

# 3. Para deploy na UOL
# - Acesse painel.uolhost.uol.com.br
# - Faça upload de index.html e assets/ para /public_html/
# - Aguarde propagação DNS

# 4. Acesse
https://grupolisboa.com.br
```

---

**Desenvolvido com ❤️ em Recife, PE**
