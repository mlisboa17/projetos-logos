"""
Recursos Online para Melhorar Detecção de Produtos - VerifiK
Dataset públicos, APIs e bibliotecas especializadas
"""

# ============================================================
# 📦 DATASETS PÚBLICOS DE PRODUTOS DE VAREJO
# ============================================================

DATASETS_PRODUTOS = {
    # 1. GROCERIES DATASET (Mais usado)
    "grozi_120": {
        "nome": "Grozi-120 Dataset",
        "url": "https://grozi.calit2.net/",
        "produtos": 120,
        "imagens": "680K+",
        "tipo": "Produtos de supermercado",
        "uso": "Treinamento YOLO para produtos comuns",
        "download": "Gratuito"
    },
    
    # 2. SKU-110K (Muito completo)
    "sku_110k": {
        "nome": "SKU-110K Dataset",
        "url": "https://github.com/eg4000/SKU110K_CVPR19",
        "produtos": "11,000 SKUs",
        "imagens": "11,762",
        "tipo": "Produtos em prateleiras densas",
        "uso": "Detecção em ambientes aglomerados",
        "download": "GitHub + Google Drive"
    },
    
    # 3. FMCG (Fast-Moving Consumer Goods)
    "fmcg_dataset": {
        "nome": "FMCG Product Dataset",
        "url": "https://www.kaggle.com/datasets/diyer22/retail-product-checkout-dataset",
        "produtos": "200+ produtos",
        "imagens": "Milhares",
        "tipo": "Checkout de supermercado",
        "uso": "Simular caixa de supermercado",
        "download": "Kaggle"
    },
    
    # 4. RETAIL PRODUCT DETECTION
    "retail_product": {
        "nome": "Retail Product Detection",
        "url": "https://www.kaggle.com/datasets/rajkumarl/grocery-store-dataset",
        "produtos": "Frutas, legumes, bebidas",
        "imagens": "5,000+",
        "tipo": "Mercearia geral",
        "uso": "Variedade de produtos",
        "download": "Kaggle"
    },
    
    # 5. DEEP RETAIL (Academia)
    "deep_retail": {
        "nome": "DeepRetail Dataset",
        "url": "https://docs.exponea.com/docs/deep-retail",
        "produtos": "Cosméticos e higiene",
        "imagens": "10,000+",
        "tipo": "Farmácia/Drogaria",
        "uso": "Produtos de higiene pessoal",
        "download": "Requisição acadêmica"
    },
    
    # 6. OPEN IMAGES V7 (Google)
    "open_images": {
        "nome": "Open Images V7 - Retail Products",
        "url": "https://storage.googleapis.com/openimages/web/index.html",
        "produtos": "Centenas de categorias",
        "imagens": "9M (filtrado: produtos)",
        "tipo": "Dataset massivo com produtos",
        "uso": "Transfer learning",
        "download": "AWS CLI ou gsutil"
    }
}

# ============================================================
# 🔌 APIs DE RECONHECIMENTO DE PRODUTOS
# ============================================================

APIS_PRODUTOS = {
    # 1. OPEN FOOD FACTS (Gratuita)
    "open_food_facts": {
        "url": "https://world.openfoodfacts.org/",
        "tipo": "Alimentos e bebidas",
        "database": "2.8M+ produtos",
        "recursos": [
            "Código de barras",
            "Imagens de produtos",
            "Ingredientes",
            "Informações nutricionais",
            "Marcas e categorias"
        ],
        "api": "https://world.openfoodfacts.org/api/v2/product/{barcode}",
        "gratuito": True,
        "instalacao": "pip install openfoodfacts"
    },
    
    # 2. UPC ITEM DB (Freemium)
    "upc_itemdb": {
        "url": "https://www.upcitemdb.com/",
        "tipo": "Produtos gerais (UPC/EAN)",
        "database": "1.5M+ produtos",
        "recursos": [
            "Busca por código de barras",
            "Imagens de produtos",
            "Descrições detalhadas",
            "Categorias"
        ],
        "api": "https://api.upcitemdb.com/prod/trial/lookup?upc={code}",
        "gratuito": "100 req/dia grátis",
        "instalacao": "requests HTTP"
    },
    
    # 3. GOOGLE VISION PRODUCT SEARCH (Pago)
    "google_vision": {
        "url": "https://cloud.google.com/vision/product-search",
        "tipo": "Busca visual de produtos",
        "recursos": [
            "Reconhecimento de produtos por imagem",
            "Detecção de logos",
            "OCR em embalagens",
            "Similar product search"
        ],
        "custo": "$1.50/1000 imagens",
        "api": "Cloud Vision API",
        "instalacao": "pip install google-cloud-vision"
    },
    
    # 4. AMAZON REKOGNITION (Pago)
    "amazon_rekognition": {
        "url": "https://aws.amazon.com/rekognition/",
        "tipo": "Detecção de objetos e produtos",
        "recursos": [
            "Custom Labels para produtos",
            "Detecção de logos",
            "Text in Image"
        ],
        "custo": "$1.00/1000 imagens",
        "api": "AWS SDK",
        "instalacao": "pip install boto3"
    },
    
    # 5. BARCODE LOOKUP (Freemium)
    "barcode_lookup": {
        "url": "https://www.barcodelookup.com/",
        "tipo": "Informações de produtos por código",
        "database": "800M+ códigos de barras",
        "recursos": [
            "UPC, EAN, ISBN",
            "Dados de produtos",
            "Imagens",
            "Preços"
        ],
        "api": "https://api.barcodelookup.com/v3/products?barcode={code}",
        "gratuito": "100 req/dia",
        "instalacao": "requests HTTP"
    }
}

# ============================================================
# 🧠 MODELOS PRÉ-TREINADOS ESPECIALIZADOS
# ============================================================

MODELOS_ESPECIALIZADOS = {
    # 1. RETAIL PRODUCT DETECTOR (TensorFlow Hub)
    "retail_detector_tfhub": {
        "url": "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1",
        "framework": "TensorFlow",
        "uso": "Detecção de produtos em prateleiras",
        "instalacao": "pip install tensorflow tensorflow-hub",
        "codigo": """
import tensorflow_hub as hub
detector = hub.load("https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1")
"""
    },
    
    # 2. DETECTRON2 RETAIL (Facebook AI)
    "detectron2_retail": {
        "url": "https://github.com/facebookresearch/detectron2",
        "framework": "PyTorch",
        "uso": "Instance segmentation de produtos",
        "instalacao": "pip install detectron2",
        "codigo": """
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
cfg = get_cfg()
cfg.merge_from_file("configs/COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
predictor = DefaultPredictor(cfg)
"""
    },
    
    # 3. YOLO-RETAIL (Especializado)
    "yolo_retail": {
        "url": "https://github.com/ultralytics/yolov8",
        "framework": "Ultralytics",
        "uso": "YOLOv8 fine-tuned para retail",
        "instalacao": "pip install ultralytics",
        "codigo": """
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
# Fine-tune com dataset de varejo
model.train(data='retail_dataset.yaml', epochs=100)
"""
    },
    
    # 4. MMDETECTION RETAIL
    "mmdetection": {
        "url": "https://github.com/open-mmlab/mmdetection",
        "framework": "PyTorch",
        "uso": "Framework completo para detecção",
        "instalacao": "pip install mmdet",
        "codigo": """
from mmdet.apis import init_detector, inference_detector
config = 'configs/faster_rcnn/faster_rcnn_r50_fpn_1x_coco.py'
checkpoint = 'checkpoints/faster_rcnn_r50_fpn_1x_coco.pth'
model = init_detector(config, checkpoint, device='cuda:0')
"""
    }
}

# ============================================================
# 📚 BIBLIOTECAS ESPECIALIZADAS EM RETAIL
# ============================================================

BIBLIOTECAS_RETAIL = {
    "pyzbar": {
        "funcao": "Leitura de códigos de barras",
        "instalacao": "pip install pyzbar",
        "uso": """
from pyzbar import pyzbar
import cv2

image = cv2.imread('produto.jpg')
barcodes = pyzbar.decode(image)
for barcode in barcodes:
    print(f"Código: {barcode.data.decode('utf-8')}")
"""
    },
    
    "opencv_contrib": {
        "funcao": "Detecção de logos e padrões",
        "instalacao": "pip install opencv-contrib-python",
        "uso": """
import cv2
# Template matching para logos
template = cv2.imread('logo_coca.jpg', 0)
image = cv2.imread('prateleira.jpg', 0)
result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
"""
    },
    
    "easyocr": {
        "funcao": "OCR em embalagens (preços, validade)",
        "instalacao": "pip install easyocr",
        "uso": """
import easyocr
reader = easyocr.Reader(['pt','en'])
results = reader.readtext('produto.jpg')
for detection in results:
    print(f"Texto: {detection[1]}")
"""
    },
    
    "pillow_simd": {
        "funcao": "Processamento rápido de imagens",
        "instalacao": "pip install pillow-simd",
        "uso": "Substituição drop-in do Pillow com 4-6x mais performance"
    },
    
    "scikit_image": {
        "funcao": "Análise de características de produtos",
        "instalacao": "pip install scikit-image",
        "uso": """
from skimage import feature
# HOG features para classificação
features = feature.hog(image, orientations=9, pixels_per_cell=(8, 8))
"""
    }
}

# ============================================================
# 🎯 TÉCNICAS DE MELHORIA
# ============================================================

TECNICAS_MELHORIA = {
    "data_augmentation": {
        "biblioteca": "Albumentations",
        "tecnicas": [
            "Rotação",
            "Flip horizontal/vertical",
            "Mudança de brilho/contraste",
            "Blur",
            "Ruído",
            "Crop/Resize",
            "Mudança de perspectiva"
        ],
        "beneficio": "Multiplica dataset 10-20x"
    },
    
    "transfer_learning": {
        "modelos_base": [
            "YOLOv8 (Ultralytics)",
            "EfficientDet (Google)",
            "Faster R-CNN (Facebook)",
            "RetinaNet"
        ],
        "beneficio": "Aprende com milhões de imagens já treinadas"
    },
    
    "ensemble_models": {
        "estrategia": "Combinar múltiplos modelos",
        "modelos": [
            "YOLO (velocidade)",
            "Faster R-CNN (precisão)",
            "Logo Detector (marcas)"
        ],
        "beneficio": "Reduz falsos positivos/negativos"
    },
    
    "hard_negative_mining": {
        "estrategia": "Treinar com exemplos difíceis",
        "exemplos": [
            "Produtos parcialmente visíveis",
            "Múltiplos produtos juntos",
            "Iluminação ruim",
            "Ângulos extremos"
        ],
        "beneficio": "Modelo mais robusto"
    }
}

# ============================================================
# 📊 SCRIPT DE EXEMPLO - INTEGRAÇÃO COMPLETA
# ============================================================

EXEMPLO_INTEGRACAO = """
# Combinar múltiplas fontes para melhor detecção

from ultralytics import YOLO
from pyzbar import pyzbar
import requests
import cv2

class DetectorProdutosAvancado:
    def __init__(self):
        self.yolo = YOLO('verifik_yolov8.pt')
        self.api_openfoodfacts = "https://world.openfoodfacts.org/api/v2/product/"
    
    def detectar(self, imagem_path):
        # 1. Detecção visual com YOLO
        resultados_yolo = self.yolo.predict(imagem_path)
        
        # 2. Leitura de código de barras
        imagem = cv2.imread(imagem_path)
        barcodes = pyzbar.decode(imagem)
        
        produtos_encontrados = []
        
        # 3. Combinar informações
        for barcode in barcodes:
            codigo = barcode.data.decode('utf-8')
            
            # Buscar informações na API
            response = requests.get(f"{self.api_openfoodfacts}{codigo}")
            if response.status_code == 200:
                dados = response.json()
                produto = {
                    'codigo': codigo,
                    'nome': dados['product']['product_name'],
                    'marca': dados['product'].get('brands', ''),
                    'categoria': dados['product'].get('categories', ''),
                    'imagem_referencia': dados['product'].get('image_url', ''),
                    'fonte': 'OpenFoodFacts + Barcode'
                }
                produtos_encontrados.append(produto)
        
        # 4. Adicionar detecções YOLO
        for result in resultados_yolo:
            for box in result.boxes:
                produto = {
                    'nome': result.names[int(box.cls[0])],
                    'confianca': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist(),
                    'fonte': 'YOLO Visual'
                }
                produtos_encontrados.append(produto)
        
        return produtos_encontrados

# Uso
detector = DetectorProdutosAvancado()
produtos = detector.detectar('camera_frame.jpg')
print(f"Encontrados {len(produtos)} produtos")
"""

# ============================================================
# 🚀 PLANO DE AÇÃO RECOMENDADO
# ============================================================

PLANO_ACAO = """
✅ FASE 1 - DADOS (2-3 dias)
1. Download SKU-110K dataset (mais realista para varejo)
2. Download Grozi-120 (produtos comuns brasileiros)
3. Coletar imagens próprias com câmera Intelbras
4. Aplicar data augmentation com Albumentations (10x multiplicação)

✅ FASE 2 - TREINAMENTO (3-5 dias)
1. Fine-tune YOLOv8n com dataset combinado
2. Treinar com 100-200 épocas
3. Validar com split 80/20
4. Ajustar hiperparâmetros (conf, iou)

✅ FASE 3 - INTEGRAÇÃO (2-3 dias)
1. Integrar pyzbar para código de barras
2. Conectar com OpenFoodFacts API
3. Implementar validação inteligente (dimensões reais)
4. Adicionar detecção de logos (fallback)

✅ FASE 4 - OTIMIZAÇÃO (2-3 dias)
1. Ensemble com múltiplos modelos
2. Hard negative mining
3. Testes em condições reais
4. Ajustes finos de confiança

TOTAL ESTIMADO: 10-14 dias para sistema robusto
"""

if __name__ == "__main__":
    print("="*70)
    print("📦 RECURSOS PARA MELHORAR DETECÇÃO DE PRODUTOS")
    print("="*70)
    
    print("\n📊 DATASETS DISPONÍVEIS:")
    for nome, dados in DATASETS_PRODUTOS.items():
        print(f"\n  • {dados['nome']}")
        print(f"    URL: {dados['url']}")
        print(f"    Produtos: {dados['produtos']}")
        print(f"    Imagens: {dados['imagens']}")
    
    print("\n\n🔌 APIs RECOMENDADAS:")
    for nome, dados in APIS_PRODUTOS.items():
        print(f"\n  • {dados['url']}")
        print(f"    Tipo: {dados['tipo']}")
        if 'database' in dados:
            print(f"    Database: {dados['database']}")
    
    print("\n\n🧠 MODELOS PRÉ-TREINADOS:")
    for nome, dados in MODELOS_ESPECIALIZADOS.items():
        print(f"\n  • {dados['url']}")
        print(f"    Framework: {dados['framework']}")
        print(f"    Uso: {dados['uso']}")
    
    print("\n\n" + "="*70)
    print("💡 Recomendação: Comece com SKU-110K + OpenFoodFacts + YOLOv8")
    print("="*70)
