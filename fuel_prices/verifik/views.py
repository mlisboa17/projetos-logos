from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from .models import ProdutoMae, ImagemProduto
import json
import os
from pathlib import Path
from PIL import Image
import io


def treino_interface(request):
    """Interface web para anotação e treinamento"""
    return render(request, 'verifik/treino_interface.html')


@csrf_exempt
@require_http_methods(["POST"])
def treinar_novas_imagens_api(request):
    """
    Treina apenas imagens que ainda não foram treinadas
    """
    try:
        from django.core.management import call_command
        import threading
        from django.utils import timezone
        
        # Contar imagens não treinadas
        imagens_nao_treinadas = ImagemProduto.objects.filter(
            treinada=False
        )
        
        total_nao_treinadas = imagens_nao_treinadas.count()
        
        if total_nao_treinadas == 0:
            return JsonResponse({
                'success': False,
                'error': 'Não há imagens novas para treinar'
            })
        
        # Contar por produto
        produtos_afetados = imagens_nao_treinadas.values('produto__marca', 'produto__descricao_produto').distinct().count()
        
        def run_training():
            try:
                # Executar treinamento incremental
                call_command('treinar_incremental', only_new=True)
                
                # Marcar imagens como treinadas
                ImagemProduto.objects.filter(treinada=False).update(
                    treinada=True,
                    data_treinamento=timezone.now()
                )
            except Exception as e:
                print(f"Erro durante treinamento: {e}")
        
        # Iniciar thread de treinamento
        training_thread = threading.Thread(target=run_training)
        training_thread.daemon = True
        training_thread.start()
        
        return JsonResponse({
            'success': True,
            'total_imagens': total_nao_treinadas,
            'produtos_afetados': produtos_afetados,
            'message': f'Treinamento iniciado com {total_nao_treinadas} imagens novas de {produtos_afetados} produtos'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def api_produtos(request):
    """API para listar produtos"""
    produtos = ProdutoMae.objects.all().order_by('marca', 'descricao_produto')
    data = [{
        'id': p.id,
        'marca': p.marca,
        'descricao_produto': p.descricao_produto
    } for p in produtos]
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def treinar_incremental_api(request):
    """
    Recebe imagens anotadas e inicia treinamento incremental
    """
    try:
        images = request.FILES.getlist('images')
        
        if not images:
            return JsonResponse({'success': False, 'error': 'Nenhuma imagem enviada'})
        
        # Processar cada imagem e suas anotações
        processed_images = []
        total_products = 0
        
        for index, image_file in enumerate(images):
            # Obter anotações
            annotations_key = f'annotations_{index}'
            annotations_json = request.POST.get(annotations_key, '[]')
            annotations = json.loads(annotations_json)
            
            if not annotations:
                continue
            
            # Salvar imagem temporariamente
            img = Image.open(image_file)
            img_width, img_height = img.size
            
            # Para cada bbox na imagem
            for ann in annotations:
                produto_id = ann['product_id']
                
                try:
                    produto = ProdutoMae.objects.get(id=produto_id)
                    
                    # Extrair crop da bbox
                    x = int(ann['x'])
                    y = int(ann['y'])
                    width = int(ann['width'])
                    height = int(ann['height'])
                    
                    # Crop da imagem
                    crop = img.crop((x, y, x + width, y + height))
                    
                    # Salvar crop
                    marca_dir = Path('media/produtos') / produto.marca
                    marca_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Encontrar próximo número
                    numero = 1
                    while True:
                        filename = f"{numero}_{image_file.name}"
                        filepath = marca_dir / filename
                        if not filepath.exists():
                            break
                        numero += 1
                    
                    # Salvar arquivo
                    crop_rgb = crop.convert('RGB')
                    crop_rgb.save(filepath, 'JPEG', quality=95)
                    
                    # Salvar no banco
                    img_treino = ImagemProduto(
                        produto=produto,
                        imagem=f"produtos/{produto.marca}/{filename}"
                    )
                    img_treino.save()
                    
                    total_products += 1
                    
                except ProdutoMae.DoesNotExist:
                    continue
            
            processed_images.append(image_file.name)
        
        # Iniciar treinamento em background
        from django.core.management import call_command
        import threading
        
        def run_training():
            call_command('treinar_incremental')
        
        # Iniciar thread de treinamento
        training_thread = threading.Thread(target=run_training)
        training_thread.daemon = True
        training_thread.start()
        
        return JsonResponse({
            'success': True,
            'images_processed': len(processed_images),
            'total_products': total_products,
            'message': 'Treinamento iniciado em background'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def produtos_lista_treino(request):
    """
    Lista produtos com informações sobre imagens treinadas e não treinadas
    """
    # Buscar produtos com anotações de imagens
    produtos = ProdutoMae.objects.all().annotate(
        total_imagens=Count('imagens_treino'),
        imagens_treinadas=Count('imagens_treino', filter=Q(imagens_treino__treinada=True)),
        imagens_nao_treinadas=Count('imagens_treino', filter=Q(imagens_treino__treinada=False))
    ).order_by('-imagens_nao_treinadas', 'marca', 'descricao_produto')
    
    # Totais gerais
    total_imagens_treinadas = ImagemProduto.objects.filter(treinada=True).count()
    total_imagens_nao_treinadas = ImagemProduto.objects.filter(treinada=False).count()
    
    context = {
        'produtos': produtos,
        'total_imagens_treinadas': total_imagens_treinadas,
        'total_imagens_nao_treinadas': total_imagens_nao_treinadas,
    }
    
    return render(request, 'verifik/produtos_lista_treino.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def treinar_produto_api(request):
    """
    Treina apenas as imagens não treinadas de um produto específico
    """
    try:
        import json
        from django.utils import timezone
        
        data = json.loads(request.body)
        produto_id = data.get('produto_id')
        
        if not produto_id:
            return JsonResponse({'success': False, 'error': 'produto_id não fornecido'})
        
        # Buscar produto
        try:
            produto = ProdutoMae.objects.get(id=produto_id)
        except ProdutoMae.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produto não encontrado'})
        
        # Contar imagens não treinadas deste produto
        imagens_nao_treinadas = ImagemProduto.objects.filter(
            produto=produto,
            treinada=False
        )
        
        total_nao_treinadas = imagens_nao_treinadas.count()
        
        if total_nao_treinadas == 0:
            return JsonResponse({
                'success': False,
                'error': 'Não há imagens novas para treinar neste produto'
            })
        
        def run_training():
            try:
                from django.core.management import call_command
                
                # Executar treinamento incremental apenas deste produto
                call_command('treinar_incremental', only_new=True, produto_id=produto_id)
                
                # Marcar imagens deste produto como treinadas
                ImagemProduto.objects.filter(
                    produto=produto,
                    treinada=False
                ).update(
                    treinada=True,
                    data_treinamento=timezone.now()
                )
            except Exception as e:
                print(f"Erro durante treinamento: {e}")
        
        # Iniciar thread de treinamento
        import threading
        training_thread = threading.Thread(target=run_training)
        training_thread.daemon = True
        training_thread.start()
        
        return JsonResponse({
            'success': True,
            'total_imagens': total_nao_treinadas,
            'produto': f"{produto.marca} {produto.descricao_produto}",
            'message': f'Treinamento iniciado: {total_nao_treinadas} imagens novas (total com augmentation: {total_nao_treinadas * 8})'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

