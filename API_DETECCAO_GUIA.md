# 🎯 API DE DETECÇÃO VERIFIK - GUIA RÁPIDO

## ✅ O QUE FOI CRIADO

1. **`verifik/api_deteccao.py`** - Endpoint principal de detecção
2. **`verifik/api_urls.py`** - URLs da API
3. **`testar_api_deteccao.py`** - Script de teste

---

## 🚀 COMO USAR

### **1. Adicionar rotas ao `logos/urls.py`**

Adicione estas linhas:

```python
# logos/urls.py
from django.urls import path, include

urlpatterns = [
    # ... outras rotas ...
    
    # API VerifiK
    path('api/verifik/', include('verifik.api_urls')),
]
```

### **2. Instalar dependências**

```bash
pip install ultralytics opencv-python pillow
```

### **3. Iniciar servidor**

```bash
python manage.py runserver
```

### **4. Testar API**

```bash
python testar_api_deteccao.py
```

---

## 📋 ENDPOINTS DISPONÍVEIS

### **POST /api/verifik/detectar/**
Detecta produtos em uma imagem

**Headers:**
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

**Body:**
```json
{
    "imagem": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "camera_id": 1,
    "salvar": true
}
```

**Response:**
```json
{
    "status": "success",
    "deteccoes": [
        {
            "produto_id": 123,
            "produto_nome": "HEINEKEN 330ML",
            "confianca": 0.92,
            "bbox": [100.5, 150.2, 300.8, 450.1],
            "codigo_barras": "7891991000123"
        }
    ],
    "total_detectado": 1,
    "tempo_processamento": 0.45,
    "confianca_minima": 0.75
}
```

### **GET /api/verifik/detectar/teste/**
Verifica status da API (sem autenticação)

**Response:**
```json
{
    "status": "online",
    "modelo": "models/verifik_yolov8.pt",
    "modelo_existe": false,
    "confianca_minima": 0.75,
    "yolo_disponivel": true,
    "produtos_cadastrados": 177
}
```

---

## 🧪 EXEMPLO DE USO (Python)

```python
import requests
import base64

# 1. Obter token JWT (faça login antes)
token = "seu_token_jwt_aqui"

# 2. Ler imagem
with open('foto_heineken.jpg', 'rb') as f:
    img_base64 = base64.b64encode(f.read()).decode()

# 3. Fazer request
response = requests.post(
    'http://localhost:8000/api/verifik/detectar/',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'imagem': f'data:image/jpeg;base64,{img_base64}',
        'camera_id': 1,
        'salvar': True
    }
)

# 4. Ver resultado
data = response.json()
print(f"Detectados: {data['total_detectado']} produtos")
for det in data['deteccoes']:
    print(f"  - {det['produto_nome']}: {det['confianca']*100:.0f}%")
```

---

## 🧪 EXEMPLO DE USO (JavaScript/Fetch)

```javascript
// 1. Capturar imagem da câmera
const canvas = document.getElementById('canvas');
const imageBase64 = canvas.toDataURL('image/jpeg');

// 2. Fazer request
fetch('/api/verifik/detectar/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + localStorage.getItem('token'),
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        imagem: imageBase64,
        camera_id: 1,
        salvar: true
    })
})
.then(res => res.json())
.then(data => {
    console.log(`Detectados: ${data.total_detectado} produtos`);
    data.deteccoes.forEach(det => {
        console.log(`- ${det.produto_nome}: ${(det.confianca*100).toFixed(0)}%`);
    });
});
```

---

## ⚙️ CONFIGURAÇÕES (settings.py)

```python
# Caminho do modelo YOLO treinado
YOLO_MODEL_PATH = BASE_DIR / 'models' / 'verifik_yolov8.pt'

# Confiança mínima (0-1)
CONFIDENCE_THRESHOLD = 0.75
```

---

## 📝 PRÓXIMOS PASSOS

1. ✅ **API criada** ← VOCÊ ESTÁ AQUI
2. ⏳ **Treinar modelo YOLO** com produtos reais
3. ⏳ **Testar com fotos** de Heineken, Coca-Cola, etc
4. ⏳ **Integrar com câmeras** ao vivo (streaming)
5. ⏳ **Criar interface web** para teste visual

---

## 🐛 TROUBLESHOOTING

### Erro: "Ultralytics não instalado"
```bash
pip install ultralytics
```

### Erro: "Modelo não encontrado"
- Normal! Use modelo base primeiro: `yolov8s.pt`
- Depois treine com seus produtos

### Erro: "Servidor não rodando"
```bash
python manage.py runserver
```

### Erro: "Token inválido"
- Obtenha token JWT via `/api/token/`
- Ou use endpoint de teste sem autenticação

---

**🎉 API PRONTA! Agora precisa treinar o modelo com produtos reais.**
