from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from pathlib import Path
from verifik.models import ProdutoMae, ImagemProduto, Categoria, Marca
from verifik.models_anotacao import ImagemAnotada
from acessorios.processador import ProcessadorImagensGenerico
from acessorios.filtrador import FiltrorImagens
from acessorios.models import ProcessadorImagens as ProcessadorImagensLog
import json


def index_processador(request):
    """Página principal do processador"""
    categorias = Categoria.objects.all()
    marcas = Marca.objects.all()
    
    # Estatísticas
    total_imagens = ImagemProduto.objects.count()
    total_anotadas = ImagemAnotada.objects.count()
    total_nao_anotadas = total_imagens - total_anotadas
    
    processamentos_recentes = ProcessadorImagensLog.objects.all()[:10]
    
    context = {
        'categorias': categorias,
        'marcas': marcas,
        'total_imagens': total_imagens,
        'total_anotadas': total_anotadas,
        'total_nao_anotadas': total_nao_anotadas,
        'processamentos_recentes': processamentos_recentes,
    }
    
    return render(request, 'acessorios/index.html', context)


def listar_imagens_processadas(request):
    """Lista todas as imagens processadas"""
    processamentos = ProcessadorImagensLog.objects.all()
    
    # Filtros
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    
    if tipo:
        processamentos = processamentos.filter(tipo=tipo)
    if status:
        processamentos = processamentos.filter(status=status)
    
    context = {
        'processamentos': processamentos,
        'tipo': tipo,
        'status': status,
    }
    
    return render(request, 'acessorios/listar_processadas.html', context)


def galeria_processadas(request):
    """Galeria visual das imagens processadas"""
    processamentos = ProcessadorImagensLog.objects.filter(
        status='sucesso',
        imagem_processada__isnull=False
    ).exclude(imagem_processada='')
    
    # Verificar quais realmente existem
    imagens = []
    for p in processamentos[:100]:
        caminho = Path(f"media/{p.imagem_processada}")
        if caminho.exists():
            imagens.append({
                'id': p.id,
                'tipo': p.get_tipo_display(),
                'caminho': f"/media/{p.imagem_processada}",
                'data': p.data_criacao,
                'original': p.imagem_original,
            })
    
    context = {
        'imagens': imagens,
        'total': len(imagens),
    }
    
    return render(request, 'acessorios/galeria_processadas.html', context)


@require_http_methods(["POST"])
def processar_categoria(request):
    """Processa imagens de uma categoria via AJAX"""
    categoria_id = request.POST.get('categoria_id')
    
    if not categoria_id or not categoria_id.isdigit():
        return JsonResponse({'erro': 'Categoria inválida'}, status=400)
    
    try:
        # Buscar imagens
        anotadas = set()
        for img in ImagemAnotada.objects.all():
            anotadas.add(img.imagem)
        
        queryset = ImagemProduto.objects.filter(
            produto__categoria_id=int(categoria_id),
            ativa=True
        ).exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        if not caminhos:
            return JsonResponse({
                'erro': 'Nenhuma imagem encontrada',
                'total': 0
            })
        
        # Processar
        processador = ProcessadorImagensGenerico()
        resultados, erros = processador.processar_lote(
            'remover_fundo',
            caminhos,
            prefixo=f"cat_{categoria_id}"
        )
        
        # Registrar no banco
        for resultado in resultados:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=resultado['original'],
                imagem_processada=resultado['processada'],
                status='sucesso',
                parametros={}
            )
        
        for erro in erros:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=erro['arquivo'],
                imagem_processada='',
                status='erro',
                mensagem_erro=erro['erro'],
                parametros={}
            )
        
        return JsonResponse({
            'sucesso': True,
            'total_processados': len(resultados),
            'total_erros': len(erros),
            'mensagem': f'{len(resultados)} imagens processadas com sucesso!'
        })
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@require_http_methods(["POST"])
def processar_marca(request):
    """Processa imagens de uma marca via AJAX"""
    marca_id = request.POST.get('marca_id')
    
    if not marca_id or not marca_id.isdigit():
        return JsonResponse({'erro': 'Marca inválida'}, status=400)
    
    try:
        # Buscar imagens
        anotadas = set()
        for img in ImagemAnotada.objects.all():
            anotadas.add(img.imagem)
        
        queryset = ImagemProduto.objects.filter(
            produto__marca_id=int(marca_id),
            ativa=True
        ).exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        if not caminhos:
            return JsonResponse({
                'erro': 'Nenhuma imagem encontrada',
                'total': 0
            })
        
        # Processar
        processador = ProcessadorImagensGenerico()
        resultados, erros = processador.processar_lote(
            'remover_fundo',
            caminhos,
            prefixo=f"marca_{marca_id}"
        )
        
        # Registrar no banco
        for resultado in resultados:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=resultado['original'],
                imagem_processada=resultado['processada'],
                status='sucesso',
                parametros={}
            )
        
        for erro in erros:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=erro['arquivo'],
                imagem_processada='',
                status='erro',
                mensagem_erro=erro['erro'],
                parametros={}
            )
        
        return JsonResponse({
            'sucesso': True,
            'total_processados': len(resultados),
            'total_erros': len(erros),
            'mensagem': f'{len(resultados)} imagens processadas com sucesso!'
        })
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@require_http_methods(["POST"])
def processar_produto(request):
    """Processa imagens de um produto via AJAX"""
    produto_id = request.POST.get('produto_id')
    
    if not produto_id or not produto_id.isdigit():
        return JsonResponse({'erro': 'Produto inválido'}, status=400)
    
    try:
        # Buscar imagens
        anotadas = set()
        for img in ImagemAnotada.objects.all():
            anotadas.add(img.imagem)
        
        queryset = ImagemProduto.objects.filter(
            produto_id=int(produto_id),
            ativa=True
        ).exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        if not caminhos:
            return JsonResponse({
                'erro': 'Nenhuma imagem encontrada',
                'total': 0
            })
        
        # Processar
        processador = ProcessadorImagensGenerico()
        resultados, erros = processador.processar_lote(
            'remover_fundo',
            caminhos,
            prefixo=f"prod_{produto_id}"
        )
        
        # Registrar no banco
        for resultado in resultados:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=resultado['original'],
                imagem_processada=resultado['processada'],
                status='sucesso',
                parametros={}
            )
        
        for erro in erros:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=erro['arquivo'],
                imagem_processada='',
                status='erro',
                mensagem_erro=erro['erro'],
                parametros={}
            )
        
        return JsonResponse({
            'sucesso': True,
            'total_processados': len(resultados),
            'total_erros': len(erros),
            'mensagem': f'{len(resultados)} imagens processadas com sucesso!'
        })
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@require_http_methods(["POST"])
def processar_todas_nao_anotadas(request):
    """Processa todas as imagens não anotadas via AJAX"""
    
    try:
        # Buscar imagens não anotadas
        anotadas = set()
        for img in ImagemAnotada.objects.all():
            anotadas.add(img.imagem)
        
        queryset = ImagemProduto.objects.filter(
            ativa=True
        ).exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        if not caminhos:
            return JsonResponse({
                'erro': 'Nenhuma imagem não anotada encontrada',
                'total': 0
            })
        
        # Limitar a 50 primeiro para não sobrecarregar
        caminhos_lote = caminhos[:50]
        
        # Processar
        processador = ProcessadorImagensGenerico()
        resultados, erros = processador.processar_lote(
            'remover_fundo',
            caminhos_lote,
            prefixo='todas'
        )
        
        # Registrar no banco
        for resultado in resultados:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=resultado['original'],
                imagem_processada=resultado['processada'],
                status='sucesso',
                parametros={}
            )
        
        for erro in erros:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=erro['arquivo'],
                imagem_processada='',
                status='erro',
                mensagem_erro=erro['erro'],
                parametros={}
            )
        
        return JsonResponse({
            'sucesso': True,
            'total_processados': len(resultados),
            'total_erros': len(erros),
            'restantes': len(caminhos) - len(caminhos_lote),
            'mensagem': f'{len(resultados)} imagens processadas! Faltam {len(caminhos) - len(caminhos_lote)}'
        })
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@require_http_methods(["POST"])
def processar_multiplos_produtos(request):
    """Processa imagens de múltiplos produtos via AJAX"""
    produtos_str = request.POST.get('produtos_ids', '')
    
    if not produtos_str:
        return JsonResponse({'erro': 'Nenhum produto selecionado'}, status=400)
    
    try:
        # Parse dos IDs de produtos
        produtos_ids = [int(pid.strip()) for pid in produtos_str.split(',') if pid.strip().isdigit()]
        
        if not produtos_ids:
            return JsonResponse({'erro': 'IDs de produtos inválidos'}, status=400)
        
        # Buscar imagens dos produtos selecionados
        anotadas = set()
        for img in ImagemAnotada.objects.all():
            anotadas.add(img.imagem)
        
        queryset = ImagemProduto.objects.filter(
            produto_id__in=produtos_ids,
            ativa=True
        ).exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        if not caminhos:
            return JsonResponse({
                'erro': 'Nenhuma imagem encontrada para os produtos selecionados',
                'total': 0
            })
        
        # Limitar a 100 imagens por vez
        caminhos_lote = caminhos[:100]
        
        # Processar
        processador = ProcessadorImagensGenerico()
        resultados, erros = processador.processar_lote(
            'remover_fundo',
            caminhos_lote,
            prefixo=f"multi_prod_{len(produtos_ids)}"
        )
        
        # Registrar no banco
        for resultado in resultados:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=resultado['original'],
                imagem_processada=resultado['processada'],
                status='sucesso',
                parametros=json.dumps({'produtos': produtos_ids})
            )
        
        for erro in erros:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=erro['arquivo'],
                imagem_processada='',
                status='erro',
                mensagem_erro=erro['erro'],
                parametros=json.dumps({'produtos': produtos_ids})
            )
        
        return JsonResponse({
            'sucesso': True,
            'total_processados': len(resultados),
            'total_erros': len(erros),
            'restantes': len(caminhos) - len(caminhos_lote),
            'mensagem': f'{len(resultados)} imagens de {len(produtos_ids)} produtos processadas! Faltam {len(caminhos) - len(caminhos_lote)}'
        })
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@require_http_methods(["POST"])
def processar_tudo_direto(request):
    """Processa TODAS as imagens de TODOS os produtos via AJAX"""
    
    try:
        # Buscar TODAS as imagens não anotadas
        anotadas = set()
        for img in ImagemAnotada.objects.all():
            anotadas.add(img.imagem)
        
        queryset = ImagemProduto.objects.filter(
            ativa=True
        ).exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        if not caminhos:
            return JsonResponse({
                'erro': 'Nenhuma imagem não processada encontrada',
                'total': 0
            })
        
        # Limitar a 200 imagens por vez para não sobrecarregar
        caminhos_lote = caminhos[:200]
        
        # Processar
        processador = ProcessadorImagensGenerico()
        resultados, erros = processador.processar_lote(
            'remover_fundo',
            caminhos_lote,
            prefixo='tudo_direto'
        )
        
        # Registrar no banco
        for resultado in resultados:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=resultado['original'],
                imagem_processada=resultado['processada'],
                status='sucesso',
                parametros=json.dumps({'processamento': 'tudo_direto'})
            )
        
        for erro in erros:
            ProcessadorImagensLog.objects.create(
                tipo='remover_fundo',
                imagem_original=erro['arquivo'],
                imagem_processada='',
                status='erro',
                mensagem_erro=erro['erro'],
                parametros=json.dumps({'processamento': 'tudo_direto'})
            )
        
        return JsonResponse({
            'sucesso': True,
            'total_processados': len(resultados),
            'total_erros': len(erros),
            'restantes': len(caminhos) - len(caminhos_lote),
            'mensagem': f'✅ {len(resultados)} imagens processadas com sucesso! Faltam {len(caminhos) - len(caminhos_lote)} imagens para processar.'
        })
    
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)
