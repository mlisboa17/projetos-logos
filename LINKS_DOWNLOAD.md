# 📦 LINKS DE DOWNLOAD - Arquivos Grandes

**Última atualização:** 25/11/2025

## 🔗 Links para Download

### 🚀 Notebook Google Colab (TREINAR COM GPU GRATUITA)
**Descrição:** Notebook completo para treinar modelo YOLO com GPU T4 gratuita  
**Link direto:** https://colab.research.google.com/github/mlisboa17/projetos-logos/blob/main/treinar_google_colab.ipynb  
**Arquivo local:** `treinar_google_colab.ipynb`

### 📊 Dataset de Treinamento (315 MB compactado)
**Descrição:** Dataset completo com imagens anotadas de 177 produtos  
**Localização no projeto:** `verifik/dataset_treino/`  
**Arquivo:** `dataset_treino.zip`  
**Link Google Drive:** ✅ DISPONÍVEL (solicite acesso ao administrador)  
**Instruções:** Baixe e extraia na pasta `verifik/` do projeto

### 🤖 Modelo YOLO Treinado (22 MB)
**Descrição:** Modelo YOLOv8 treinado com produtos_mae (25/11/2025)  
**Localização no projeto:** `verifik/runs/treino_continuado/weights/best.pt`  
**Link Google Drive:** [ADICIONAR LINK AQUI]  
**Link OneDrive:** [ADICIONAR LINK AQUI]

### 📦 Modelos Base YOLOv8
**yolov8n.pt (6 MB):** Modelo nano (rápido)  
**Link oficial:** https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

**yolov8s.pt (22 MB):** Modelo small (balanceado)  
**Link oficial:** https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt

---

## 📥 Como Fazer Upload (Para Mantenedor)

### Google Drive:
```bash
# 1. Compactar dataset
tar -czf dataset_treino.tar.gz verifik/dataset_treino/

# 2. Upload para Google Drive
# - Acesse drive.google.com
# - Faça upload de dataset_treino.tar.gz
# - Clique com botão direito → Obter link → Qualquer pessoa com o link
# - Cole o link acima

# 3. Compactar modelo
tar -czf modelo_best_20251125.tar.gz verifik/runs/treino_continuado/weights/best.pt

# 4. Upload e compartilhar link
```

### OneDrive (Alternativa):
- Mesma lógica, mas usando OneDrive

---

## 📥 Como Baixar (Para Novo Usuário)

### 1. Baixar Dataset:
```bash
# Baixe do Google Drive e extraia:
cd C:\Users\SEU_USUARIO\OneDrive\Desktop\ProjetoLogus
tar -xzf dataset_treino.tar.gz
# Ou descompacte manualmente com WinRAR/7zip
```

### 2. Baixar Modelo Treinado:
```bash
# Baixe do Google Drive e extraia:
tar -xzf modelo_best_20251125.tar.gz
# Ou coloque manualmente em:
# verifik/runs/treino_continuado/weights/best.pt
```

---

## 🖥️ Para Treinar em Máquina Robusta

### Cenário 1: Máquina Local Potente
```bash
# 1. Clone o repositório
git clone https://github.com/mlisboa17/projetos-logos.git
cd projetos-logos

# 2. Baixe dataset do Google Drive
# Extraia em verifik/dataset_treino/

# 3. Configure Python
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 4. Treine (usará GPU se disponível)
python treinar_incremental.py
# ou
python treinar_simples.py

# 5. Novo modelo salvo em:
# verifik/runs/treino_NOVA_DATA/weights/best.pt
```

### Cenário 2: Google Colab (GPU Gratuita)
```python
# Notebook Colab:

# 1. Montar Google Drive
from google.colab import drive
drive.mount('/content/drive')

# 2. Clone repo
!git clone https://github.com/mlisboa17/projetos-logos.git
%cd projetos-logos

# 3. Baixar dataset do Google Drive
!gdown --id SEU_ID_AQUI -O dataset_treino.tar.gz
!tar -xzf dataset_treino.tar.gz

# 4. Instalar dependências
!pip install -r requirements.txt

# 5. Treinar
!python treinar_simples.py

# 6. Copiar modelo treinado para Drive
!cp verifik/runs/*/weights/best.pt /content/drive/MyDrive/
```

### Cenário 3: AWS/Azure/Vast.ai (Cloud GPU)
```bash
# 1. SSH na máquina
ssh usuario@IP_MAQUINA

# 2. Clone repo
git clone https://github.com/mlisboa17/projetos-logos.git
cd projetos-logos

# 3. Baixar dataset
wget "LINK_GOOGLE_DRIVE" -O dataset_treino.tar.gz
tar -xzf dataset_treino.tar.gz

# 4. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Treinar (verificar GPU)
python treinar_simples.py

# 6. Baixar modelo treinado
scp usuario@IP_MAQUINA:projetos-logos/verifik/runs/*/weights/best.pt ./
```

---

## 🔄 Fluxo de Trabalho Completo

### Máquina Local (Anotação):
1. `python detector_simples.py` → Anotar fotos
2. Salva em `dataset_corrigido/`
3. Upload para Google Drive

### Máquina Robusta (Treinamento):
1. Baixar dataset do Google Drive
2. `python treinar_incremental.py`
3. Upload novo `best.pt` para Google Drive

### Máquina Local (Deploy):
1. Baixar `best.pt` atualizado
2. Testar: `python testar_deteccao.py`
3. Deploy no sistema

---

## 📊 Estimativa de Recursos

### Para Treinamento:
- **GPU Recomendada:** NVIDIA GTX 1660 ou superior
- **RAM:** 16GB mínimo, 32GB recomendado
- **Disco:** 10GB livres
- **Tempo:** ~30min a 2h (depende do dataset e GPU)

### Google Colab:
- **GPU:** Tesla T4 (gratuito)
- **RAM:** 12GB
- **Limite:** 12h de sessão contínua
- **Custo:** Grátis!

---

## 🆘 Troubleshooting

### Problema: "CUDA out of memory"
```python
# Edite treinar_simples.py e reduza batch_size:
model.train(data='config.yaml', epochs=50, batch=8)  # Era 16
```

### Problema: "No GPU detected"
```bash
# Verificar GPU
python -c "import torch; print(torch.cuda.is_available())"

# Se False, treinar em CPU (mais lento)
python treinar_simples.py --device cpu
```

---

## 📌 Checklist Rápido

Máquina Local (Anotação):
- [ ] Anotar fotos com `detector_simples.py`
- [ ] Compactar `dataset_corrigido/`
- [ ] Upload para Google Drive

Máquina Robusta (Treinamento):
- [ ] Baixar dataset do Google Drive
- [ ] Extrair em `verifik/dataset_treino/`
- [ ] Rodar `treinar_incremental.py`
- [ ] Upload `best.pt` para Google Drive

Máquina Local (Deploy):
- [ ] Baixar `best.pt` atualizado
- [ ] Colocar em `verifik/runs/treino_continuado/weights/`
- [ ] Testar detecção
- [ ] Commit código atualizado (sem `best.pt`)
