"""
Script para testar o sistema de múltiplos bboxes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ImagemProdutoPendente, ProdutoMae
from verifik.views_coleta import detectar_produtos_api, get_yolo_model
from django.test import RequestFactory
import json

def main():
    print("=" * 80)
    print("TESTE DO SISTEMA DE MÚLTIPLOS BBOXES")
    print("=" * 80)
    
    # 1. Verificar modelo YOLO
    print("\n1. Verificando modelo YOLO...")
    try:
        model = get_yolo_model()
        print(f"   ✓ Modelo carregado: {model.__class__.__name__}")
    except Exception as e:
        print(f"   ✗ Erro ao carregar modelo: {e}")
        return
    
    # 2. Buscar imagens para teste
    print("\n2. Buscando imagens para teste...")
    imagens = ImagemProdutoPendente.objects.filter(status='pendente')[:5]
    print(f"   ✓ Encontradas {imagens.count()} imagens pendentes")
    
    if imagens.count() == 0:
        print("   ⚠ Nenhuma imagem pendente para testar")
        return
    
    # 3. Testar detecção em cada imagem
    print("\n3. Testando detecção de múltiplos produtos...")
    for idx, imagem in enumerate(imagens, 1):
        print(f"\n   Imagem {idx}: {imagem.imagem.name}")
        
        # Criar request fake
        factory = RequestFactory()
        request = factory.post('/api/detectar-produtos/', 
                               json.dumps({'imagem_id': imagem.id}),
                               content_type='application/json')
        
        try:
            response = detectar_produtos_api(request)
            data = json.loads(response.content)
            
            if data.get('success'):
                bboxes = data.get('bboxes', [])
                print(f"   ✓ Detectados {len(bboxes)} produtos:")
                
                for i, bbox in enumerate(bboxes, 1):
                    print(f"\n      Produto {i}:")
                    print(f"      - Confiança YOLO: {bbox['confidence']:.2%}")
                    print(f"      - Forma: {bbox['forma']}")
                    print(f"      - OCR: {bbox['ocr_texto'][:5]}..." if bbox['ocr_texto'] else "      - OCR: []")
                    
                    if bbox['produto_sugerido_id']:
                        produto = ProdutoMae.objects.get(id=bbox['produto_sugerido_id'])
                        print(f"      - Sugestão: {produto.descricao_produto}")
                        print(f"      - Confiança: {bbox['confianca_sugestao']:.1f}%")
                        print(f"      - Razão: {bbox['razao_sugestao']}")
                    else:
                        print(f"      - Sugestão: Nenhuma")
            else:
                print(f"   ✗ Erro: {data.get('error')}")
                
        except Exception as e:
            print(f"   ✗ Erro ao processar: {e}")
    
    # 4. Estatísticas
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS DO BANCO DE DADOS")
    print("=" * 80)
    
    total = ImagemProdutoPendente.objects.count()
    pendentes = ImagemProdutoPendente.objects.filter(status='pendente').count()
    aprovadas = ImagemProdutoPendente.objects.filter(status='aprovada').count()
    rejeitadas = ImagemProdutoPendente.objects.filter(status='rejeitada').count()
    
    print(f"\nTotal de imagens: {total}")
    print(f"  - Pendentes: {pendentes}")
    print(f"  - Aprovadas: {aprovadas}")
    print(f"  - Rejeitadas: {rejeitadas}")
    
    desconhecidos = ImagemProdutoPendente.objects.filter(
        produto__descricao_produto__icontains='DESCONHECIDO'
    ).count()
    
    manuais = ImagemProdutoPendente.objects.filter(
        produto__descricao_produto__icontains='FAMILIA_HEINEKEN_MANUAL'
    ).count()
    
    print(f"\nProdutos problemáticos:")
    print(f"  - DESCONHECIDO: {desconhecidos}")
    print(f"  - FAMILIA_HEINEKEN_MANUAL: {manuais}")
    print(f"  - Total para revisar: {desconhecidos + manuais}")
    
    # 5. Instruções
    print("\n" + "=" * 80)
    print("COMO USAR O SISTEMA")
    print("=" * 80)
    print("""
1. Acesse: http://localhost:8000/verifik/coleta/revisar-desconhecidos/

2. Para cada imagem você verá:
   - Múltiplos bboxes detectados (verde=alta confiança, amarelo=média, vermelho=baixa)
   - Análise IA para cada produto (forma, OCR, sugestão)
   - Botões individuais: Aprovar, Manual, Rejeitar

3. Opções:
   - Aprovar: Salva o bbox no dataset com o produto sugerido
   - Manual: Selecione outro produto da lista
   - Rejeitar: Ignora este bbox
   - Aprovar Todos Alta Confiança: Aprova automaticamente bboxes ≥70%

4. Atalhos do teclado:
   - A: Aprovar bbox atual
   - R: Rejeitar bbox atual
   - M: Abrir seleção manual
   - Setas: Navegar entre bboxes
    """)

if __name__ == '__main__':
    main()
