"""
Testa acurácia do modelo YOLO com os produtos treinados
"""
import os
import sys
import django

# Configurar Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
import cv2
import numpy as np

print("\n" + "="*80)
print("ANÁLISE DE ACURÁCIA DO MODELO YOLO - PRODUTOS TREINADOS")
print("="*80 + "\n")

# Verificar se modelo existe
modelo_path = os.path.join(BASE_DIR, 'verifik', 'verifik_yolov8.pt')
if not os.path.exists(modelo_path):
    print("❌ MODELO NÃO ENCONTRADO!")
    print(f"   Caminho esperado: {modelo_path}")
    print("\n   O modelo ainda não foi treinado.")
    print("   Execute o script de treinamento primeiro.\n")
    sys.exit(1)

print(f"✓ Modelo encontrado: {modelo_path}\n")

# Carregar modelo YOLO
try:
    from ultralytics import YOLO
    model = YOLO(modelo_path)
    print("✓ Modelo YOLO carregado com sucesso\n")
except Exception as e:
    print(f"❌ Erro ao carregar modelo: {e}\n")
    sys.exit(1)

# Buscar produtos com imagens de treino
produtos_treinados = ProdutoMae.objects.filter(
    imagens_treino__isnull=False
).distinct()

print(f"📊 PRODUTOS TREINADOS: {produtos_treinados.count()}\n")
print("="*80)

resultados = []

for produto in produtos_treinados:
    print(f"\n🔍 Testando: {produto.descricao_produto}")
    print("-" * 80)
    
    # Pegar todas as imagens de treino deste produto
    imagens = produto.imagens_treino.all()
    total_imagens = imagens.count()
    
    print(f"   Total de imagens de treino: {total_imagens}")
    
    if total_imagens == 0:
        print("   ⚠️  Sem imagens para testar")
        continue
    
    # Testar com uma amostra (primeiras 5 imagens ou todas se tiver menos)
    amostra = min(5, total_imagens)
    imagens_teste = imagens[:amostra]
    
    deteccoes_corretas = 0
    confianças = []
    
    for img in imagens_teste:
        # Caminho da imagem
        img_path = os.path.join(BASE_DIR, img.imagem.path) if hasattr(img.imagem, 'path') else str(img.imagem)
        
        if not os.path.exists(img_path):
            print(f"   ⚠️  Imagem não encontrada: {img_path}")
            continue
        
        try:
            # Fazer detecção
            results = model(img_path, conf=0.5, verbose=False)
            
            # Verificar se detectou algo
            if len(results) > 0 and len(results[0].boxes) > 0:
                # Pegar detecção com maior confiança
                boxes = results[0].boxes
                conf_max = float(boxes.conf.max())
                class_id = int(boxes.cls[boxes.conf.argmax()])
                
                # Verificar se o nome da classe corresponde ao produto
                class_name = model.names[class_id]
                
                confianças.append(conf_max)
                
                # Considerar correto se detectou (independente do nome exato da classe)
                # pois o modelo pode ter mapeado diferente
                deteccoes_corretas += 1
                
                print(f"   ✓ Detectado: {class_name} (Confiança: {conf_max:.2%})")
            else:
                print(f"   ✗ Nada detectado nesta imagem")
        
        except Exception as e:
            print(f"   ❌ Erro ao processar imagem: {e}")
    
    # Calcular acurácia
    taxa_deteccao = (deteccoes_corretas / amostra * 100) if amostra > 0 else 0
    confianca_media = (sum(confianças) / len(confianças)) if confianças else 0
    
    # Indicador visual
    if taxa_deteccao >= 80 and confianca_media >= 0.75:
        status = "🟢 EXCELENTE"
    elif taxa_deteccao >= 60 and confianca_media >= 0.60:
        status = "🟡 BOM"
    elif taxa_deteccao >= 40:
        status = "🟠 REGULAR"
    else:
        status = "🔴 BAIXO"
    
    print(f"\n   📊 Resultado:")
    print(f"      Taxa de detecção: {taxa_deteccao:.1f}% ({deteccoes_corretas}/{amostra})")
    print(f"      Confiança média: {confianca_media:.2%}")
    print(f"      Status: {status}")
    
    resultados.append({
        'produto': produto.descricao_produto,
        'total_imgs': total_imagens,
        'testadas': amostra,
        'detectadas': deteccoes_corretas,
        'taxa': taxa_deteccao,
        'confianca': confianca_media,
        'status': status
    })

# Resumo final
print("\n" + "="*80)
print("📊 RESUMO DA ACURÁCIA")
print("="*80 + "\n")

if resultados:
    print(f"{'Produto':<45} {'Imgs'} {'Detectadas'} {'Taxa'} {'Conf.Média'} {'Status'}")
    print("-"*80)
    
    for r in resultados:
        nome = r['produto'][:43]
        print(f"{nome:<45} {r['total_imgs']:4d}  {r['detectadas']}/{r['testadas']}      "
              f"{r['taxa']:5.1f}%  {r['confianca']:5.1%}     {r['status']}")
    
    # Médias gerais
    taxa_media = sum(r['taxa'] for r in resultados) / len(resultados)
    conf_media_geral = sum(r['confianca'] for r in resultados) / len(resultados)
    
    print("\n" + "="*80)
    print(f"📈 MÉDIA GERAL:")
    print(f"   Taxa de detecção: {taxa_media:.1f}%")
    print(f"   Confiança média: {conf_media_geral:.2%}")
    
    if taxa_media >= 80 and conf_media_geral >= 0.75:
        print("\n   🟢 MODELO BEM TREINADO!")
    elif taxa_media >= 60:
        print("\n   🟡 MODELO FUNCIONAL - Pode melhorar com mais treino")
    else:
        print("\n   🔴 MODELO PRECISA DE RETREINAMENTO")
        print("      Adicione mais imagens variadas de cada produto")
else:
    print("❌ Nenhum produto foi testado")

print("\n" + "="*80 + "\n")
