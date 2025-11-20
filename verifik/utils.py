"""
Utilidades e helpers para o sistema VerifiK
"""
from django.db import models


def get_user_permissions(user):
    """
    Retorna as permissões do usuário
    
    Returns:
        dict: {
            'is_admin': bool,
            'is_manager': bool,
            'is_supervisor': bool,
            'nivel': str,
            'perfil': PerfilGestor or None
        }
    """
    is_admin = user.is_superuser
    is_manager = False
    is_supervisor = False
    nivel = 'SUPER_ADMIN' if user.is_superuser else None
    perfil = None
    
    if hasattr(user, 'perfilgestor'):
        perfil = user.perfilgestor
        nivel = perfil.nivel_acesso
        is_admin = perfil.nivel_acesso == 'ADMINISTRADOR'
        is_manager = perfil.nivel_acesso == 'GERENTE'
        is_supervisor = perfil.nivel_acesso == 'SUPERVISOR'
    
    return {
        'is_admin': is_admin,
        'is_manager': is_manager,
        'is_supervisor': is_supervisor,
        'nivel': nivel,
        'perfil': perfil
    }


def calcular_proxima_ordem(produto):
    """
    Calcula a próxima ordem disponível para imagens de um produto
    
    Args:
        produto: Instância do modelo Produto
        
    Returns:
        int: Próxima ordem disponível
    """
    from .models import ImagemProduto
    
    ultima_ordem = produto.imagens_treino.aggregate(
        max_ordem=models.Max('ordem')
    )['max_ordem']
    
    return (ultima_ordem or 0) + 1


def processar_upload_multiplo(produto, imagens, descricao_base=''):
    """
    Processa upload de múltiplas imagens para um produto
    
    Args:
        produto: Instância do modelo Produto
        imagens: Lista de arquivos de imagem
        descricao_base: Descrição base para as imagens
        
    Returns:
        tuple: (imagens_adicionadas: int, primeira_imagem: ImagemProduto or None, erros: list)
    """
    from .models import ImagemProduto
    
    ordem_inicial = calcular_proxima_ordem(produto)
    imagens_adicionadas = 0
    primeira_imagem = None
    erros = []
    
    for idx, imagem in enumerate(imagens):
        try:
            # Criar descrição única para cada imagem
            if descricao_base:
                descricao = f"{descricao_base} #{idx + 1}"
            else:
                descricao = f"Imagem {ordem_inicial + idx}"
            
            # Criar registro da imagem
            img_obj = ImagemProduto.objects.create(
                produto=produto,
                imagem=imagem,
                descricao=descricao,
                ordem=ordem_inicial + idx,
                ativa=True
            )
            
            if primeira_imagem is None:
                primeira_imagem = img_obj
            
            imagens_adicionadas += 1
            
        except Exception as e:
            erros.append(f"{imagem.name}: {str(e)}")
    
    return imagens_adicionadas, primeira_imagem, erros


def definir_imagem_referencia(produto, imagem):
    """
    Define a imagem de referência do produto se ainda não tiver uma
    
    Args:
        produto: Instância do modelo Produto
        imagem: Arquivo de imagem ou ImagemProduto
        
    Returns:
        bool: True se foi definida, False se já tinha referência
    """
    if not produto.imagem_referencia:
        if hasattr(imagem, 'imagem'):
            # É uma instância de ImagemProduto
            produto.imagem_referencia = imagem.imagem
        else:
            # É um arquivo direto
            produto.imagem_referencia = imagem
        
        produto.save()
        return True
    
    return False
