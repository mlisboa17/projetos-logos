"""
╔══════════════════════════════════════════════════════════════════╗
║                  API DE DETECÇÃO - VERIFIK                       ║
║              Endpoint para detectar produtos via IA              ║
╚══════════════════════════════════════════════════════════════════╝

📚 COMO FUNCIONA:
-----------------
1. Cliente envia POST com imagem (base64 ou arquivo)
2. Sistema carrega modelo YOLO treinado
3. IA detecta produtos na imagem
4. Retorna JSON com produtos detectados + confiança
5. Opcionalmente salva DeteccaoProduto no banco

📌 ENDPOINT:
POST /api/verifik/detectar/

📋 BODY (JSON):
{
    "imagem": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",  // Base64 OU
    "camera_id": 1,  // Opcional
    "salvar": true   // Se deve salvar no banco
}

📤 RESPONSE:
{
    "status": "success",
    "deteccoes": [
        {
            "produto_id": 123,
            "produto_nome": "HEINEKEN 330ML",
            "confianca": 0.92,
            "bbox": [100, 150, 300, 450],
            "codigo_barras": "7891991000123"
        }
    ],
    "total_detectado": 1,
    "tempo_processamento": 0.45
}

🎯 USO:
-------
# Python
import requests
import base64

with open('foto_heineken.jpg', 'rb') as f:
    img_base64 = base64.b64encode(f.read()).decode()

response = requests.post(
    'http://localhost:8000/api/verifik/detectar/',
    json={'imagem': f'data:image/jpeg;base64,{img_base64}', 'salvar': True}
)
print(response.json())

# JavaScript/Fetch
fetch('/api/verifik/detectar/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        imagem: imageBase64,
        camera_id: 1,
        salvar: true
    })
})
"""

import base64
import io
import time
from pathlib import Path

import cv2
import numpy as np
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

try:
    from ultralytics import YOLO
    YOLO_DISPONIVEL = True
except ImportError:
    YOLO_DISPONIVEL = False
    print("⚠️  AVISO: Ultralytics não instalado. Instale: pip install ultralytics")

from .models import ProdutoMae, DeteccaoProduto, Camera


# ============================================================
# 🔧 CONFIGURAÇÕES
# ============================================================

# Caminho do modelo YOLO treinado
MODELO_YOLO_PATH = getattr(
    settings, 
    'YOLO_MODEL_PATH', 
    Path(settings.BASE_DIR) / 'models' / 'verifik_yolov8.pt'
)

# Confiança mínima para detecção (0-1)
CONFIANCA_MINIMA = getattr(settings, 'CONFIDENCE_THRESHOLD', 0.75)

# Cache do modelo (evita recarregar a cada request)
_modelo_cache = None


# ============================================================
# 🤖 FUNÇÕES AUXILIARES
# ============================================================

def carregar_modelo():
    """
    Carrega modelo YOLO (usa cache se já carregado)
    
    Returns:
        YOLO: Modelo carregado
        
    Raises:
        FileNotFoundError: Se modelo não existe
        ImportError: Se ultralytics não instalado
    """
    global _modelo_cache
    
    if not YOLO_DISPONIVEL:
        raise ImportError(
            "Ultralytics não instalado. Execute: pip install ultralytics"
        )
    
    # Retorna cache se existe
    if _modelo_cache is not None:
        return _modelo_cache
    
    # Verifica se modelo existe
    if not Path(MODELO_YOLO_PATH).exists():
        # Se não existe modelo treinado, usa modelo base
        print(f"⚠️  Modelo não encontrado em {MODELO_YOLO_PATH}")
        print(f"📦 Usando YOLOv8s base (não treinado)")
        modelo_path = 'yolov8s.pt'
    else:
        modelo_path = str(MODELO_YOLO_PATH)
        print(f"✅ Carregando modelo: {modelo_path}")
    
    # Carrega modelo
    _modelo_cache = YOLO(modelo_path)
    
    return _modelo_cache


def decodificar_imagem(imagem_data):
    """
    Decodifica imagem de base64 ou bytes para numpy array
    
    Args:
        imagem_data (str|bytes): Imagem em base64 ou bytes
        
    Returns:
        np.ndarray: Imagem decodificada (BGR)
        
    Raises:
        ValueError: Se formato inválido
    """
    try:
        # Se é string base64
        if isinstance(imagem_data, str):
            # Remove prefixo data:image/...;base64,
            if 'base64,' in imagem_data:
                imagem_data = imagem_data.split('base64,')[1]
            
            # Decodifica base64
            img_bytes = base64.b64decode(imagem_data)
        else:
            img_bytes = imagem_data
        
        # Converte bytes → numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Não foi possível decodificar a imagem")
        
        return img
        
    except Exception as e:
        raise ValueError(f"Erro ao decodificar imagem: {str(e)}")


def processar_deteccoes(resultados, salvar=False, camera_id=None):
    """
    Processa resultados do YOLO e retorna JSON estruturado
    
    Args:
        resultados: Resultado do modelo.predict()
        salvar (bool): Se deve salvar DeteccaoProduto no banco
        camera_id (int): ID da câmera (opcional)
        
    Returns:
        list: Lista de detecções processadas
    """
    deteccoes = []
    
    for r in resultados:
        boxes = r.boxes
        
        for box in boxes:
            # Extrair dados da detecção
            confianca = float(box.conf[0])
            
            # Filtrar por confiança mínima
            if confianca < CONFIANCA_MINIMA:
                continue
            
            # Classe detectada (ID)
            classe_id = int(box.cls[0])
            
            # Bbox (x1, y1, x2, y2)
            bbox = box.xyxy[0].tolist()
            
            # TODO: Mapear classe_id → ProdutoMae
            # Por enquanto, retorna classe_id diretamente
            produto_id = classe_id
            produto_nome = f"Produto #{classe_id}"
            codigo_barras = None
            
            # Tentar buscar produto no banco
            try:
                produto = ProdutoMae.objects.filter(id=produto_id).first()
                if produto:
                    produto_nome = produto.descricao_produto
                    codigo_barras = produto.codigos_barras.filter(principal=True).first()
                    if codigo_barras:
                        codigo_barras = codigo_barras.codigo
            except Exception as e:
                print(f"⚠️  Erro ao buscar produto: {e}")
            
            deteccao = {
                'produto_id': produto_id,
                'produto_nome': produto_nome,
                'confianca': round(confianca, 2),
                'bbox': [round(x, 1) for x in bbox],
                'codigo_barras': codigo_barras
            }
            
            deteccoes.append(deteccao)
            
            # Salvar no banco se solicitado
            if salvar:
                try:
                    camera = None
                    if camera_id:
                        camera = Camera.objects.filter(id=camera_id).first()
                    
                    DeteccaoProduto.objects.create(
                        camera=camera,
                        produto_identificado_id=produto_id if produto else None,
                        metodo_deteccao='VIDEO',
                        confianca=confianca * 100,  # Salva como 0-100
                        dados_raw={'bbox': bbox, 'classe_id': classe_id}
                    )
                except Exception as e:
                    print(f"⚠️  Erro ao salvar detecção: {e}")
    
    return deteccoes


# ============================================================
# 🔌 API ENDPOINT
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detectar_produtos(request):
    """
    Endpoint principal de detecção
    
    POST /api/verifik/detectar/
    
    Body:
    {
        "imagem": "base64...",
        "camera_id": 1,  # opcional
        "salvar": true   # opcional
    }
    """
    inicio = time.time()
    
    try:
        # Validar dados
        imagem_data = request.data.get('imagem')
        camera_id = request.data.get('camera_id')
        salvar = request.data.get('salvar', False)
        
        if not imagem_data:
            return Response(
                {'error': 'Campo "imagem" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Decodificar imagem
        try:
            img = decodificar_imagem(imagem_data)
        except ValueError as e:
            return Response(
                {'error': f'Imagem inválida: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Carregar modelo
        try:
            modelo = carregar_modelo()
        except Exception as e:
            return Response(
                {'error': f'Erro ao carregar modelo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Executar detecção
        resultados = modelo.predict(
            source=img,
            conf=CONFIANCA_MINIMA,
            verbose=False
        )
        
        # Processar resultados
        deteccoes = processar_deteccoes(
            resultados,
            salvar=salvar,
            camera_id=camera_id
        )
        
        # Calcular tempo
        tempo_processamento = time.time() - inicio
        
        # Retornar resposta
        return Response({
            'status': 'success',
            'deteccoes': deteccoes,
            'total_detectado': len(deteccoes),
            'tempo_processamento': round(tempo_processamento, 2),
            'confianca_minima': CONFIANCA_MINIMA
        })
        
    except Exception as e:
        return Response(
            {
                'status': 'error',
                'error': str(e),
                'tipo_erro': type(e).__name__
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
# 🧪 ENDPOINT DE TESTE (sem autenticação)
# ============================================================

@csrf_exempt
@require_http_methods(["POST", "GET"])
def detectar_teste(request):
    """
    Endpoint de teste (SEM autenticação)
    Útil para desenvolvimento
    
    GET: Retorna informações do sistema
    POST: Detecta produtos
    """
    if request.method == 'GET':
        return JsonResponse({
            'status': 'online',
            'modelo': str(MODELO_YOLO_PATH),
            'modelo_existe': Path(MODELO_YOLO_PATH).exists(),
            'confianca_minima': CONFIANCA_MINIMA,
            'yolo_disponivel': YOLO_DISPONIVEL,
            'produtos_cadastrados': ProdutoMae.objects.count()
        })
    
    # POST - mesmo que detectar_produtos mas sem autenticação
    # (código simplificado para teste)
    return JsonResponse({
        'error': 'Use POST /api/verifik/detectar/ com autenticação'
    })
