from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pathlib import Path
import json
from verifik.models import ProdutoMae

@login_required
def visualizar_anotacoes(request):
    """Visualiza imagens com bounding boxes das exportações"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Apenas administradores.')
        return redirect('home')
    
    # Caminho das exportações
    pasta_base = Path(r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\FAMILIA HEINEKEN")
    
    exportacoes = []
    
    if pasta_base.exists():
        pastas_exportacao = [d for d in pasta_base.iterdir() if d.is_dir() and d.name.startswith('exportacao_')]
        
        for pasta_exp in pastas_exportacao:
            dados_json = pasta_exp / "dados_exportacao.json"
            produtos_json = pasta_exp / "produtos.json"
            pasta_imagens = pasta_exp / "imagens"
            
            if not dados_json.exists() or not produtos_json.exists():
                continue
            
            # Carregar produtos da exportação
            with open(produtos_json, 'r', encoding='utf-8') as f:
                produtos_exp = json.load(f)
                produtos_dict = {p['id']: p for p in produtos_exp}
            
            # Carregar dados de exportação
            with open(dados_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Processar cada imagem
            for img_data in dados['imagens']:
                arquivo = img_data['arquivo']
                anotacoes = img_data.get('anotacoes', [])
                
                if not anotacoes:
                    continue
                
                caminho_img = pasta_imagens / arquivo
                
                if not caminho_img.exists():
                    continue
                
                # Processar anotações
                anotacoes_processadas = []
                for anotacao in anotacoes:
                    produto_exp_id = anotacao['produto_id']
                    produto_exp = produtos_dict.get(produto_exp_id, {})
                    produto_nome = produto_exp.get('nome', f'Produto {produto_exp_id}')
                    
                    # Tentar encontrar produto correspondente no Django
                    try:
                        produto_django = ProdutoMae.objects.filter(
                            descricao_produto__icontains=produto_nome
                        ).first()
                    except:
                        produto_django = None
                    
                    anotacoes_processadas.append({
                        'produto_exp_id': produto_exp_id,
                        'produto_nome': produto_nome,
                        'produto_django': produto_django,
                        'x': anotacao['x'],
                        'y': anotacao['y'],
                        'width': anotacao['width'],
                        'height': anotacao['height'],
                    })
                
                # Caminho relativo da imagem
                caminho_relativo = str(caminho_img).replace('\\', '/')
                
                exportacoes.append({
                    'pasta': pasta_exp.name,
                    'arquivo': arquivo,
                    'imagem_path': caminho_relativo,
                    'data': img_data.get('data', ''),
                    'anotacoes': anotacoes_processadas,
                    'total_anotacoes': len(anotacoes_processadas)
                })
    
    context = {
        'exportacoes': exportacoes,
        'total_imagens': len(exportacoes),
        'total_anotacoes': sum(e['total_anotacoes'] for e in exportacoes),
    }
    
    return render(request, 'verifik/visualizar_anotacoes.html', context)
