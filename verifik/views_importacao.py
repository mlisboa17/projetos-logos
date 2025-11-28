# Views para importação de pastas do sistema standalone

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from pathlib import Path
import json
import os
import shutil
from datetime import datetime

from verifik.models import ProdutoMae
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def importar_pasta_standalone(request):
    """Interface para importar pastas do sistema standalone"""
    
    if not request.user.is_staff:
        messages.error(request, 'Apenas gestores podem acessar esta área.')
        return redirect('verifik_home')
    
    context = {
        'titulo': 'Importar Pasta do Sistema Standalone',
    }
    
    return render(request, 'verifik/importar_pasta_standalone.html', context)


@login_required
@require_http_methods(["POST"])
def executar_importacao_pasta(request):
    """Executa a importação de uma pasta do sistema standalone"""
    
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    
    try:
        caminho_pasta = request.POST.get('caminho_pasta', '').strip()
        
        if not caminho_pasta:
            return JsonResponse({
                'success': False, 
                'error': 'Caminho da pasta é obrigatório'
            })
        
        pasta = Path(caminho_pasta)
        
        if not pasta.exists():
            return JsonResponse({
                'success': False,
                'error': f'Pasta não encontrada: {caminho_pasta}'
            })
        
        if not pasta.is_dir():
            return JsonResponse({
                'success': False,
                'error': 'Caminho deve ser uma pasta, não um arquivo'
            })
        
        # Verificar se é uma pasta de exportação válida
        arquivo_json = pasta / 'dados_exportacao.json'
        
        if not arquivo_json.exists():
            return JsonResponse({
                'success': False,
                'error': 'Pasta inválida - não contém dados_exportacao.json'
            })
        
        pasta_imagens = pasta / 'imagens'
        
        if not pasta_imagens.exists():
            return JsonResponse({
                'success': False,
                'error': 'Pasta inválida - não contém subpasta "imagens"'
            })
        
        # Ler dados da exportação
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        usuario_nome = dados.get('usuario', 'Funcionário')
        data_exportacao = dados.get('data_exportacao')
        imagens = dados.get('imagens', [])
        
        if not imagens:
            return JsonResponse({
                'success': False,
                'error': 'Nenhuma imagem encontrada nos dados de exportação'
            })
        
        # Importar produtos primeiro (se houver arquivo produtos.json)
        produtos_importados = importar_produtos_da_pasta(pasta)
        
        # Buscar ou criar usuário
        usuario, created = User.objects.get_or_create(
            username=usuario_nome.lower().replace(' ', '_'),
            defaults={
                'first_name': usuario_nome,
                'is_active': True
            }
        )
        
        # Diretório de destino no Django
        media_dir = Path(settings.MEDIA_ROOT) / 'produtos' / 'anotacoes'
        media_dir.mkdir(parents=True, exist_ok=True)
        
        importadas = 0
        erros = []
        
        for img_data in imagens:
            try:
                arquivo_origem = pasta_imagens / img_data['arquivo']
                
                if not arquivo_origem.exists():
                    erros.append(f"Arquivo não encontrado: {img_data['arquivo']}")
                    continue
                
                # Criar subpasta por data
                data_pasta = datetime.now().strftime('%Y/%m/%d')
                destino_dir = media_dir / data_pasta
                destino_dir.mkdir(parents=True, exist_ok=True)
                
                # Gerar nome único para evitar conflitos
                timestamp = datetime.now().strftime('%H%M%S_%f')
                nome_arquivo = f"{Path(img_data['arquivo']).stem}_{timestamp}{Path(img_data['arquivo']).suffix}"
                arquivo_destino = destino_dir / nome_arquivo
                
                # Copiar imagem
                shutil.copy2(arquivo_origem, arquivo_destino)
                
                # Caminho relativo para o Django
                caminho_relativo = f"produtos/anotacoes/{data_pasta}/{nome_arquivo}"
                
                # Criar registro de imagem
                imagem_anotada = ImagemAnotada.objects.create(
                    imagem=caminho_relativo,
                    enviado_por=usuario,
                    observacoes=img_data.get('observacoes', ''),
                    status='aprovada',
                    total_anotacoes=len(img_data.get('anotacoes', []))
                )
                
                # Criar anotações
                anotacoes_criadas = 0
                for anotacao_data in img_data.get('anotacoes', []):
                    produto_id = anotacao_data['produto_id']
                    
                    try:
                        produto = ProdutoMae.objects.get(id=produto_id)
                        
                        AnotacaoProduto.objects.create(
                            imagem_anotada=imagem_anotada,
                            produto=produto,
                            bbox_x=anotacao_data['x'],
                            bbox_y=anotacao_data['y'],
                            bbox_width=anotacao_data['width'],
                            bbox_height=anotacao_data['height']
                        )
                        
                        anotacoes_criadas += 1
                        
                    except ProdutoMae.DoesNotExist:
                        erros.append(f"Produto ID {produto_id} não encontrado para {img_data['arquivo']}")
                
                importadas += 1
                
            except Exception as e:
                erros.append(f"Erro em {img_data.get('arquivo', 'desconhecido')}: {str(e)}")
        
        # Preparar resposta
        resultado = {
            'success': True,
            'mensagem': f'Importação concluída com sucesso!',
            'detalhes': {
                'pasta': str(pasta.name),
                'usuario': usuario_nome,
                'data_exportacao': data_exportacao,
                'imagens_importadas': importadas,
                'produtos_importados': produtos_importados,
                'total_erros': len(erros),
                'erros': erros[:10] if erros else []  # Limitar a 10 erros na resposta
            }
        }
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro durante a importação: {str(e)}'
        })


def importar_produtos_da_pasta(pasta):
    """Importa produtos novos do arquivo produtos.json (se existir)"""
    
    arquivo_produtos = pasta / 'produtos.json'
    
    if not arquivo_produtos.exists():
        return 0
    
    try:
        with open(arquivo_produtos, 'r', encoding='utf-8') as f:
            produtos = json.load(f)
        
        criados = 0
        
        for prod_data in produtos:
            descricao = prod_data['descricao_produto']
            marca = prod_data.get('marca', '')
            
            # Verificar se já existe
            produto_existente = ProdutoMae.objects.filter(
                descricao_produto=descricao,
                marca=marca
            ).first()
            
            if not produto_existente:
                ProdutoMae.objects.create(
                    descricao_produto=descricao,
                    marca=marca,
                    preco=0.00,
                    ativo=True
                )
                criados += 1
        
        return criados
        
    except Exception:
        return 0