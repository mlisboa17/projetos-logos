"""
VerifiK - Sistema de Teste de Detecção de Produtos
Analisa uma foto e retorna:
- Produtos detectados com quantidade
- Produtos não reconhecidos
- Métricas de confiança
- Imagem anotada com detecções
"""

import os
import sys
import django
from pathlib import Path
import cv2
import numpy as np
from collections import defaultdict

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from ultralytics import YOLO
from verifik.models import ProdutoMae

# Configurações
MODELO_PATH = BASE_DIR / 'verifik' / 'verifik_yolov8.pt'
CONFIANCA_MINIMA = 0.25  # Threshold de confiança mínima


def carregar_modelo():
    """Carrega o modelo YOLO treinado"""
    if not MODELO_PATH.exists():
        print(f"❌ Modelo não encontrado em: {MODELO_PATH}")
        print("Execute primeiro: python treinar_modelo_yolo.py")
        sys.exit(1)
    
    print(f"📦 Carregando modelo: {MODELO_PATH}")
    modelo = YOLO(str(MODELO_PATH))
    print(f"✅ Modelo carregado com sucesso!")
    return modelo


def obter_mapeamento_classes():
    """Obtém mapeamento entre class_id e nome do produto"""
    produtos = ProdutoMae.objects.filter(
        imagens_treino__isnull=False
    ).distinct().order_by('id')
    
    mapeamento = {}
    for idx, produto in enumerate(produtos):
        mapeamento[idx] = {
            'id': produto.id,
            'nome': produto.marca,
            'descricao': produto.descricao_produto
        }
    
    return mapeamento


def analisar_foto(caminho_foto, modelo, mapeamento_classes, salvar_resultado=True):
    """
    Analisa uma foto e detecta produtos
    
    Args:
        caminho_foto: Caminho para a imagem
        modelo: Modelo YOLO carregado
        mapeamento_classes: Dicionário com mapeamento de classes
        salvar_resultado: Se True, salva imagem anotada
    
    Returns:
        dict com resultados da análise
    """
    if not os.path.exists(caminho_foto):
        print(f"❌ Foto não encontrada: {caminho_foto}")
        return None
    
    print(f"\n🔍 Analisando foto: {caminho_foto}")
    print("=" * 80)
    
    # Executar detecção
    resultados = modelo.predict(
        source=caminho_foto,
        conf=CONFIANCA_MINIMA,
        iou=0.45,
        verbose=False
    )
    
    # Processar resultados
    resultado = resultados[0]
    boxes = resultado.boxes
    
    # Contar detecções por produto
    contagem = defaultdict(lambda: {'quantidade': 0, 'confiancas': []})
    produtos_detectados = []
    
    for box in boxes:
        class_id = int(box.cls[0])
        confianca = float(box.conf[0])
        coords = box.xyxy[0].cpu().numpy()
        
        if class_id in mapeamento_classes:
            produto = mapeamento_classes[class_id]
            nome = produto['nome']
            
            contagem[nome]['quantidade'] += 1
            contagem[nome]['confiancas'].append(confianca)
            
            produtos_detectados.append({
                'nome': nome,
                'confianca': confianca,
                'bbox': coords.tolist()
            })
    
    # Calcular métricas
    total_detectado = len(boxes)
    produtos_unicos = len(contagem)
    confianca_media = np.mean([d['confianca'] for d in produtos_detectados]) if produtos_detectados else 0
    
    # Preparar resultado
    analise = {
        'total_detectado': total_detectado,
        'produtos_unicos': produtos_unicos,
        'confianca_media': confianca_media,
        'deteccoes': dict(contagem),
        'detalhes': produtos_detectados
    }
    
    # Exibir resultados
    exibir_resultados(analise)
    
    # Salvar imagem anotada
    if salvar_resultado:
        salvar_imagem_anotada(resultado, caminho_foto, analise)
    
    return analise


def exibir_resultados(analise):
    """Exibe resultados da análise de forma formatada"""
    print("\n📊 RESULTADOS DA ANÁLISE")
    print("=" * 80)
    print(f"Total de produtos detectados: {analise['total_detectado']}")
    print(f"Produtos únicos identificados: {analise['produtos_unicos']}")
    print(f"Confiança média: {analise['confianca_media']:.1%}")
    
    if analise['deteccoes']:
        print("\n🏷️  PRODUTOS DETECTADOS:")
        print("-" * 80)
        
        for nome, dados in sorted(analise['deteccoes'].items()):
            quantidade = dados['quantidade']
            confianca_media_produto = np.mean(dados['confiancas'])
            confianca_min = min(dados['confiancas'])
            confianca_max = max(dados['confiancas'])
            
            print(f"\n📦 {nome}")
            print(f"   Quantidade: {quantidade} unidade(s)")
            print(f"   Confiança média: {confianca_media_produto:.1%}")
            print(f"   Confiança (min/max): {confianca_min:.1%} / {confianca_max:.1%}")
    else:
        print("\n⚠️  Nenhum produto detectado!")
        print("   Possíveis causas:")
        print("   - Produtos na foto não foram treinados")
        print("   - Qualidade da imagem baixa")
        print("   - Produtos muito pequenos ou cortados")
    
    print("\n" + "=" * 80)


def salvar_imagem_anotada(resultado, caminho_original, analise):
    """Salva imagem com detecções anotadas"""
    # Carregar imagem original
    img = cv2.imread(caminho_original)
    
    # Desenhar detecções
    for deteccao in analise['detalhes']:
        x1, y1, x2, y2 = map(int, deteccao['bbox'])
        confianca = deteccao['confianca']
        nome = deteccao['nome']
        
        # Cor baseada na confiança (verde = alta, amarelo = média, vermelho = baixa)
        if confianca >= 0.7:
            cor = (0, 255, 0)  # Verde
        elif confianca >= 0.5:
            cor = (0, 255, 255)  # Amarelo
        else:
            cor = (0, 165, 255)  # Laranja
        
        # Desenhar retângulo
        cv2.rectangle(img, (x1, y1), (x2, y2), cor, 2)
        
        # Preparar texto
        texto = f"{nome} {confianca:.1%}"
        
        # Fundo para o texto
        (w_text, h_text), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(img, (x1, y1 - h_text - 10), (x1 + w_text, y1), cor, -1)
        
        # Texto
        cv2.putText(img, texto, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (0, 0, 0), 1, cv2.LINE_AA)
    
    # Adicionar sumário no topo
    info_texto = f"Detectados: {analise['total_detectado']} | Produtos: {analise['produtos_unicos']} | Confianca: {analise['confianca_media']:.1%}"
    cv2.rectangle(img, (10, 10), (len(info_texto) * 10 + 10, 40), (0, 0, 0), -1)
    cv2.putText(img, info_texto, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 
               0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Salvar
    nome_arquivo = Path(caminho_original).stem
    caminho_saida = BASE_DIR / 'verifik' / f'{nome_arquivo}_resultado.jpg'
    cv2.imwrite(str(caminho_saida), img)
    
    print(f"\n💾 Imagem anotada salva em: {caminho_saida}")
    print(f"   Abra para visualizar as detecções!")


def exibir_produtos_treinados():
    """Exibe lista de produtos treinados disponíveis"""
    print("\n🎓 PRODUTOS TREINADOS NO MODELO:")
    print("=" * 80)
    
    produtos = ProdutoMae.objects.filter(
        imagens_treino__isnull=False
    ).distinct().order_by('marca')
    
    if produtos.exists():
        for idx, produto in enumerate(produtos, 1):
            num_imagens = produto.imagens_treino.count()
            print(f"{idx}. {produto.marca} - {produto.descricao_produto} ({num_imagens} imagens)")
    else:
        print("⚠️  Nenhum produto treinado ainda!")
    
    print("=" * 80)


def main():
    """Função principal"""
    print("\n" + "=" * 80)
    print("🔍 VERIFIK - SISTEMA DE TESTE DE DETECÇÃO DE PRODUTOS")
    print("=" * 80)
    
    # Exibir produtos treinados
    exibir_produtos_treinados()
    
    # Carregar modelo
    modelo = carregar_modelo()
    mapeamento = obter_mapeamento_classes()
    
    print(f"\n✅ Modelo pronto! Classes carregadas: {len(mapeamento)}")
    
    # Solicitar caminho da foto
    print("\n" + "-" * 80)
    caminho_foto = input("📸 Digite o caminho da foto para análise: ").strip().strip('"')
    
    if not caminho_foto:
        print("❌ Caminho não fornecido!")
        return
    
    # Analisar foto
    analise = analisar_foto(caminho_foto, modelo, mapeamento, salvar_resultado=True)
    
    if analise:
        print("\n✅ Análise concluída com sucesso!")
        
        # Oferecer análise de outra foto
        print("\n" + "-" * 80)
        continuar = input("Deseja analisar outra foto? (s/n): ").strip().lower()
        
        while continuar == 's':
            caminho_foto = input("📸 Digite o caminho da foto: ").strip().strip('"')
            if caminho_foto:
                analisar_foto(caminho_foto, modelo, mapeamento, salvar_resultado=True)
            
            continuar = input("\nAnalisar outra foto? (s/n): ").strip().lower()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Análise cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante análise: {e}")
        import traceback
        traceback.print_exc()
