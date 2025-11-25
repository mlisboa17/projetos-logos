# 🚀 Setup para Novos Usuários - Projeto Logos

**Bem-vindo ao Projeto Logos!** Este guia ajudará você a configurar o ambiente completo.

## 📦 O que ESTÁ no Git

✅ Código-fonte completo (Django + Scripts)  
✅ `detector_simples.py` (Detector híbrido YOLO+OCR)  
✅ Configurações do projeto  
✅ Banco de dados SQLite com 177 produtos (`db.sqlite3`)  
✅ `ONDE_PARAMOS.md` (Guia de referência rápida)

## ⚠️ O que NÃO ESTÁ no Git (Arquivos Grandes)

❌ Modelo YOLO treinado (`best.pt` - 22MB)  
❌ Dataset de treinamento completo (367MB)  
❌ Modelos base YOLOv8 (`yolov8n.pt`, `yolov8s.pt`)

## 🔧 Procedimento de Setup Completo

### 1️⃣ Clone o Repositório

```bash
git clone https://github.com/mlisboa17/projetos-logos.git
cd projetos-logos
```

### 2️⃣ Crie Ambiente Virtual Python

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3️⃣ Instale Dependências

```bash
pip install -r requirements.txt
```

### 4️⃣ Instale Tesseract OCR

**Windows:**
1. Baixar: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar em: `C:\Program Files\Tesseract-OCR\`
3. Adicionar ao PATH (ou configurar manualmente no código)

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-por tesseract-ocr-eng
```

### 5️⃣ Baixar Modelo YOLO Treinado

**Opção A: Usar modelo pré-treinado genérico (para começar)**
```bash
# O detector_simples.py usa automaticamente yolov8n.pt se best.pt não existir
# Será baixado automaticamente na primeira execução
```

**Opção B: Solicitar modelo treinado específico**
- Contate o administrador do projeto para obter `best.pt`
- Coloque em: `verifik/runs/treino_continuado/weights/best.pt`

**Opção C: Treinar seu próprio modelo**
```bash
python treinar_simples.py
# Requer dataset de treinamento
```

### 6️⃣ (Opcional) Dataset de Treinamento

Se você quer **treinar ou melhorar** o modelo:

**Opção 1: Solicitar dataset existente**
- Contate o administrador
- Extraia em: `verifik/dataset_treino/`

**Opção 2: Criar seu próprio dataset**
```bash
python detector_simples.py
# Use o detector para anotar novas fotos
# Salva em: dataset_corrigido/
```

### 7️⃣ Configurar Django

```bash
# Migrar banco de dados (caso não esteja incluído)
python manage.py migrate

# Criar superusuário (opcional)
python manage.py createsuperuser

# Rodar servidor
python manage.py runserver
```

### 8️⃣ Testar Sistema

```bash
# Testar detector
python detector_simples.py

# Testar detecção
python testar_deteccao.py

# Admin Django
# Acessar: http://localhost:8000/admin/
```

---

## 🎯 Workflows Comuns

### **Para Anotar Novas Fotos:**
```bash
python detector_simples.py
# 1. Selecione foto
# 2. Confirme produtos detectados
# 3. Corrija se necessário
# 4. Dados salvos em dataset_corrigido/
```

### **Para Treinar Modelo:**
```bash
# Com dataset novo
python treinar_incremental.py

# Treinamento simples
python treinar_simples.py

# Continuar treinamento existente
python continuar_treinamento.py
```

### **Para Detectar Produtos em Novas Fotos:**
```bash
python testar_deteccao.py
# ou use via API Django
```

---

## 📂 Estrutura de Arquivos Esperada

```
ProjetoLogus/
├── verifik/
│   ├── runs/
│   │   └── treino_continuado/
│   │       └── weights/
│   │           └── best.pt          # ⚠️ NÃO no Git - baixar separado
│   └── dataset_treino/               # ⚠️ NÃO no Git - opcional
│       ├── images/train/
│       └── labels/train/
├── dataset_corrigido/                # Criado automaticamente
│   ├── images/
│   └── labels/
├── detector_simples.py               # ✅ No Git
├── db.sqlite3                        # ✅ No Git
├── manage.py                         # ✅ No Git
└── requirements.txt                  # ✅ No Git
```

---

## 🔄 Para Contribuir com Melhorias

### 1. **Anotar Novas Fotos**
```bash
python detector_simples.py
# Salva em dataset_corrigido/
# Compartilhe com equipe
```

### 2. **Treinar Modelo Melhorado**
```bash
python treinar_incremental.py
# Gera novo best.pt
# Compartilhe com equipe
```

### 3. **Fazer Commit das Melhorias**
```bash
git add detector_simples.py  # Código atualizado
git add ONDE_PARAMOS.md      # Atualizar guia
git commit -m "feat: melhorias no detector X"
git push origin main
```

**NÃO faça commit de:**
- ❌ `best.pt` (muito grande - compartilhar separadamente)
- ❌ `dataset_treino/` (muito grande)
- ❌ `__pycache__/`
- ❌ `venv/`

---

## 🆘 Problemas Comuns

### **Erro: Tesseract não encontrado**
```python
# Edite o código e ajuste o caminho:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### **Erro: Django não carrega produtos_mae**
```bash
# Verifique DJANGO_SETTINGS_MODULE
set DJANGO_SETTINGS_MODULE=logos.settings
python detector_simples.py
```

### **Erro: Modelo YOLO não encontrado**
```bash
# Baixe modelo base (será feito automaticamente):
# https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### **Erro: Sem permissão para acessar câmera**
```python
# Edite settings.py e configure câmeras
```

---

## 📞 Contato e Suporte

- **Repositório:** https://github.com/mlisboa17/projetos-logos
- **Documentação:** Leia `ONDE_PARAMOS.md` e `DOCUMENTACAO_COMPLETA.md`
- **Issues:** Abra issue no GitHub para problemas

---

## 🎓 Recursos de Aprendizado

- **YOLO:** https://docs.ultralytics.com/
- **Tesseract:** https://github.com/tesseract-ocr/tesseract
- **Django:** https://docs.djangoproject.com/

---

**🎯 Resumo Rápido:**
1. Clone repo → 2. Instale Python deps → 3. Instale Tesseract → 4. Baixe/treine modelo → 5. Rode `detector_simples.py`!
