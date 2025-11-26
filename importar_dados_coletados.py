"""
Script para importar dados coletados pelos funcionários
Sincroniza as imagens e anotações com o banco de dados Django
"""

import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime
import shutil

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae
from verifik.models_anotacao import ImagemAnotada, AnotacaoProduto
from django.contrib.auth import get_user_model

User = get_user_model()


def importar_dados_exportados(pasta_exportacao):
    """
    Importa dados de uma pasta exportada pelo sistema standalone
    
    Args:
        pasta_exportacao: Caminho para a pasta com dados_exportacao.json
    """
    
    pasta = Path(pasta_exportacao)
    
    if not pasta.exists():
        print(f"❌ Pasta não encontrada: {pasta}")
        return
        
    arquivo_json = pasta / 'dados_exportacao.json'
    
    if not arquivo_json.exists():
        print(f"❌ Arquivo dados_exportacao.json não encontrado em: {pasta}")
        return
        
    print("📥 Importando dados coletados...")
    print("=" * 60)
    
    # Ler dados
    with open(arquivo_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        
    usuario_nome = dados.get('usuario', 'Funcionário')
    data_exportacao = dados.get('data_exportacao')
    imagens = dados.get('imagens', [])
    
    print(f"📊 Dados da exportação:")
    print(f"   Usuário: {usuario_nome}")
    print(f"   Data: {data_exportacao}")
    print(f"   Total de imagens: {len(imagens)}")
    print()
    
    # Buscar ou criar usuário
    usuario, created = User.objects.get_or_create(
        username=usuario_nome.lower().replace(' ', '_'),
        defaults={
            'first_name': usuario_nome,
            'is_active': True
        }
    )
    
    if created:
        print(f"✓ Usuário '{usuario_nome}' criado")
    
    # Diretório de destino
    media_dir = Path('media/produtos/anotacoes')
    media_dir.mkdir(parents=True, exist_ok=True)
    
    importadas = 0
    erros = []
    
    for img_data in imagens:
        try:
            arquivo_origem = pasta / 'imagens' / img_data['arquivo']
            
            if not arquivo_origem.exists():
                erros.append(f"Arquivo não encontrado: {img_data['arquivo']}")
                continue
                
            # Criar subpasta por data
            data_pasta = datetime.now().strftime('%Y/%m/%d')
            destino_dir = media_dir / data_pasta
            destino_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar imagem
            arquivo_destino = destino_dir / img_data['arquivo']
            shutil.copy2(arquivo_origem, arquivo_destino)
            
            # Caminho relativo para o Django
            caminho_relativo = f"produtos/anotacoes/{data_pasta}/{img_data['arquivo']}"
            
            # Criar registro de imagem
            imagem_anotada = ImagemAnotada.objects.create(
                imagem=caminho_relativo,
                enviado_por=usuario,
                observacoes=img_data.get('observacoes', ''),
                status='concluida',
                total_anotacoes=len(img_data.get('anotacoes', []))
            )
            
            # Criar anotações
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
                    
                except ProdutoMae.DoesNotExist:
                    erros.append(f"Produto ID {produto_id} não encontrado")
                    
            importadas += 1
            print(f"✓ Importada: {img_data['arquivo']} ({len(img_data.get('anotacoes', []))} anotações)")
            
        except Exception as e:
            erros.append(f"Erro em {img_data.get('arquivo', 'desconhecido')}: {str(e)}")
            
    print()
    print("=" * 60)
    print(f"✅ Importação concluída!")
    print(f"   Total importadas: {importadas}")
    print(f"   Erros: {len(erros)}")
    
    if erros:
        print("\n⚠️ Erros encontrados:")
        for erro in erros[:10]:  # Mostrar apenas os 10 primeiros
            print(f"   - {erro}")
        if len(erros) > 10:
            print(f"   ... e mais {len(erros) - 10} erros")


def importar_produtos(pasta_exportacao):
    """
    Importa produtos novos do arquivo produtos.json
    """
    
    pasta = Path(pasta_exportacao)
    arquivo_produtos = pasta / 'produtos.json'
    
    if not arquivo_produtos.exists():
        print("ℹ️ Nenhum arquivo de produtos para importar")
        return
        
    with open(arquivo_produtos, 'r', encoding='utf-8') as f:
        produtos = json.load(f)
        
    print(f"\n📦 Importando produtos...")
    
    criados = 0
    existentes = 0
    
    for prod_data in produtos:
        descricao = prod_data['descricao_produto']
        marca = prod_data.get('marca')
        
        # Verificar se já existe
        produto_existente = ProdutoMae.objects.filter(
            descricao_produto=descricao,
            marca=marca
        ).first()
        
        if produto_existente:
            existentes += 1
        else:
            ProdutoMae.objects.create(
                descricao_produto=descricao,
                marca=marca,
                preco=0.00,
                ativo=True
            )
            criados += 1
            print(f"   ✓ Criado: {descricao}")
            
    print(f"\n   Total criados: {criados}")
    print(f"   Já existentes: {existentes}")


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       IMPORTAÇÃO DE DADOS COLETADOS - VerifiK             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    if len(sys.argv) < 2:
        print("📁 Uso: python importar_dados_coletados.py <pasta_exportacao>")
        print()
        print("Exemplo:")
        print("   python importar_dados_coletados.py C:/Users/Usuario/Desktop/exportacao_20251126_143052")
        print()
        return
        
    pasta_exportacao = sys.argv[1]
    
    # Importar produtos primeiro
    importar_produtos(pasta_exportacao)
    
    # Importar imagens e anotações
    importar_dados_exportados(pasta_exportacao)
    
    print("\n🎉 Processo concluído!")
    print("\n💡 Próximos passos:")
    print("   1. Acesse http://127.0.0.1:8000/coleta/importar-dataset/")
    print("   2. Use 'Importar Anotadas' para adicionar ao dataset de treino")
    print("   3. As imagens estarão prontas para treinar o modelo YOLO!")


if __name__ == '__main__':
    main()
