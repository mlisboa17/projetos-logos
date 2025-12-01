"""
Importa imagens das pastas de coleta diretamente para o sistema Django
Versão automática (sem confirmação)
"""

import os
import sys
import django
from pathlib import Path
from datetime import datetime
import shutil

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae
from verifik.models_coleta import ImagemProdutoPendente, LoteFotos
from django.contrib.auth import get_user_model

User = get_user_model()


def criar_ou_buscar_produto(nome_produto):
    """
    Cria ou busca um produto baseado no nome da pasta
    """
    # Tentar encontrar produto existente
    produto = ProdutoMae.objects.filter(
        descricao_produto__icontains=nome_produto
    ).first()
    
    if produto:
        return produto
    
    # Se não encontrar, criar novo
    produto = ProdutoMae.objects.create(
        descricao_produto=nome_produto.upper().replace('_', ' '),
        marca='A definir',
        preco=0.00,
        ativo=True
    )
    
    print(f"   ✓ Produto criado: {produto.descricao_produto}")
    return produto


def importar_pasta_coleta():
    """
    Importa imagens das pastas de coleta para o sistema Django
    """
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   IMPORTAR PASTAS DE COLETA PARA DJANGO - VerifiK         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Pastas onde podem estar imagens coletadas
    pastas_busca = [
        Path('dados_coleta'),
        Path('media/produtos'),
        Path('media/coleta'),
    ]
    
    # Buscar todas as pastas de produtos
    produtos_imagens = {}
    
    print("🔍 Procurando imagens nas pastas de coleta...\n")
    
    for base_dir in pastas_busca:
        if not base_dir.exists():
            continue
            
        # Procurar subpastas (cada subpasta = um produto)
        for pasta_produto in base_dir.iterdir():
            if not pasta_produto.is_dir():
                continue
                
            nome_produto = pasta_produto.name
            
            # Ignorar pastas especiais
            if nome_produto.startswith('.') or nome_produto in ['anotacoes', 'treino', 'teste', 'pendentes']:
                continue
            
            # Buscar imagens nesta pasta
            imagens = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                imagens.extend(list(pasta_produto.glob(ext)))
            
            if imagens:
                if nome_produto not in produtos_imagens:
                    produtos_imagens[nome_produto] = []
                produtos_imagens[nome_produto].extend(imagens)
    
    if not produtos_imagens:
        print("❌ Nenhuma imagem encontrada nas pastas de coleta!")
        print("\nPastas verificadas:")
        for pasta in pastas_busca:
            print(f"   - {pasta}")
        return
    
    # Mostrar resumo
    print(f"✓ Encontradas {len(produtos_imagens)} pastas de produtos:\n")
    for produto, imagens in sorted(produtos_imagens.items()):
        print(f"   📦 {produto}: {len(imagens)} imagens")
    
    print()
    print("🚀 Iniciando importação automática...\n")
    
    # Buscar ou criar usuário padrão
    usuario, created = User.objects.get_or_create(
        username='coletor',
        defaults={
            'first_name': 'Sistema de Coleta',
            'is_active': True
        }
    )
    
    # Criar lote de fotos
    lote = LoteFotos.objects.create(
        enviado_por=usuario,
        nome=f"Importação de pastas de coleta - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        total_imagens=sum(len(imgs) for imgs in produtos_imagens.values())
    )
    
    print(f"📦 Lote criado: #{lote.id}\n")
    
    # Diretório de destino
    media_dir = Path('media/produtos/pendentes')
    media_dir.mkdir(parents=True, exist_ok=True)
    
    total_importadas = 0
    total_erros = 0
    
    for nome_produto, imagens in produtos_imagens.items():
        print(f"📦 Importando: {nome_produto}")
        
        # Criar ou buscar produto
        produto = criar_ou_buscar_produto(nome_produto)
        
        for idx, img_path in enumerate(imagens, 1):
            try:
                # Criar nome único
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                novo_nome = f"{nome_produto}_{timestamp}_{idx}{img_path.suffix}"
                
                # Copiar imagem
                destino = media_dir / novo_nome
                shutil.copy2(img_path, destino)
                
                # Caminho relativo para Django
                caminho_relativo = f"produtos/pendentes/{novo_nome}"
                
                # Criar registro
                ImagemProdutoPendente.objects.create(
                    lote=lote,
                    produto=produto,
                    imagem=caminho_relativo,
                    status='pendente',
                    enviado_por=usuario
                )
                
                total_importadas += 1
                
                if idx % 20 == 0:
                    print(f"   ✓ {idx}/{len(imagens)} imagens")
                    
            except Exception as e:
                print(f"   ✗ Erro em {img_path.name}: {e}")
                total_erros += 1
        
        print(f"   ✅ {len(imagens)} imagens de {nome_produto} importadas")
    
    # Atualizar lote
    lote.imagens_aprovadas = 0
    lote.imagens_rejeitadas = 0
    lote.save()
    
    print()
    print("=" * 64)
    print("✅ IMPORTAÇÃO CONCLUÍDA!")
    print()
    print(f"📊 Estatísticas:")
    print(f"   Total importadas: {total_importadas}")
    print(f"   Erros: {total_erros}")
    print(f"   Produtos: {len(produtos_imagens)}")
    print()
    print("💡 Próximos passos:")
    print("   1. Acesse: http://127.0.0.1:8000/coleta/lotes/")
    print(f"   2. Abra o lote #{lote.id}")
    print("   3. Revise e confirme os produtos sugeridos")
    print("   4. Anote as bounding boxes nas imagens")
    print("   5. Exporte para o dataset de treinamento!")


if __name__ == '__main__':
    importar_pasta_coleta()
