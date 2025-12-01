import os
import django
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models_coleta import ImagemProdutoPendente, LoteFotos
from verifik.models import ProdutoMae
from collections import defaultdict

def analisar_anotacoes():
    """Analisa as anotações JSON e mapeia produtos detectados"""
    
    pasta_base = r"C:\Users\gabri\Downloads\OneDrive_2025-11-30\BRUNO SENA CASA CAIADA\FAMILIA HEINEKEN"
    pastas_exportacao = [d for d in Path(pasta_base).iterdir() if d.is_dir() and d.name.startswith('exportacao_')]
    
    # Mapear produto_id -> nome do produto
    produtos_detectados = defaultdict(lambda: {'nome': '', 'count': 0, 'imagens': []})
    
    print("="*70)
    print("🔍 ANALISANDO ANOTAÇÕES DAS EXPORTAÇÕES")
    print("="*70)
    
    for pasta_exp in pastas_exportacao:
        dados_json = pasta_exp / "dados_exportacao.json"
        produtos_json = pasta_exp / "produtos.json"
        
        if not dados_json.exists() or not produtos_json.exists():
            continue
        
        # Carregar produtos
        with open(produtos_json, 'r', encoding='utf-8') as f:
            produtos = json.load(f)
            # produtos é um dicionário {produto_id: {nome, marca, etc}}
            for prod_id, prod_info in produtos.items():
                produtos_detectados[prod_id]['nome'] = prod_info.get('nome', 'DESCONHECIDO')
        
        # Carregar dados de exportação
        with open(dados_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Contar detecções
        for imagem_info in dados.get('imagens', []):
            if imagem_info.get('tipo') == 'anotada':
                for anotacao in imagem_info.get('anotacoes', []):
                    prod_id = str(anotacao.get('produto_id'))
                    produtos_detectados[prod_id]['count'] += 1
                    produtos_detectados[prod_id]['imagens'].append(imagem_info.get('arquivo'))
    
    # Mostrar produtos detectados
    print(f"\n📊 Produtos detectados nas anotações:")
    print("-" * 70)
    
    for prod_id, info in sorted(produtos_detectados.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"ID {prod_id}: {info['nome']} - {info['count']} detecções")
    
    return produtos_detectados


def mapear_produtos_django():
    """Mapeia produtos do sistema de coleta para produtos do Django"""
    
    # Produtos HEINEKEN no Django
    produtos_heineken = ProdutoMae.objects.filter(descricao_produto__icontains='heineken')
    
    print("\n" + "="*70)
    print("🏷️ PRODUTOS HEINEKEN NO BANCO DE DADOS DJANGO")
    print("="*70)
    
    for p in produtos_heineken:
        print(f"{p.id:3d} - {p.descricao_produto}")
    
    # Mapeamento sugerido (baseado em análise)
    mapeamento = {
        # produto_id_coleta: produto_id_django
        '1': 1,    # BARRIL DE CHOPP HEINEKEN 5 LITROS
        '49': 49,  # CERVEJA HEINEKEN ZERO ALCOOL GARRAFA 330ML
        '50': 50,  # CERVEJA HEINEKEN ZERO ALCOOL LATA 350ML
        '51': 51,  # CERVEJA HEINEKEN 330ML
        '52': 52,  # CERVEJA HEINEKEN GF 600ML
        '53': 53,  # CERVEJA HEINEKEN LATA 269ML
        '54': 54,  # CERVEJA HEINEKEN LATA 350ML
    }
    
    return mapeamento, produtos_heineken


def reclassificar_imagens_importadas():
    """Reclassifica imagens que foram importadas com produto genérico"""
    
    print("\n" + "="*70)
    print("🔄 RECLASSIFICANDO IMAGENS")
    print("="*70)
    
    # Buscar imagens com produtos genéricos
    produtos_genericos = ['DESCONHECIDO', 'FAMILIA_HEINEKEN_MANUAL']
    
    for prod_nome in produtos_genericos:
        try:
            produto_generico = ProdutoMae.objects.get(descricao_produto=prod_nome)
            imagens = ImagemProdutoPendente.objects.filter(produto=produto_generico)
            
            print(f"\n📦 Produto: {prod_nome}")
            print(f"   {imagens.count()} imagens encontradas")
            
            if imagens.count() > 0:
                print(f"\n   ⚠️ Estas imagens precisam ser reclassificadas!")
                print(f"   Opções:")
                print(f"   1. Manter como '{prod_nome}' (nenhum produto específico detectado)")
                print(f"   2. Reclassificar para produtos HEINEKEN específicos (baseado em anotações)")
                print(f"   3. Deletar (se forem inválidas)")
                
        except ProdutoMae.DoesNotExist:
            print(f"\n❌ Produto '{prod_nome}' não encontrado no banco")
    
    return


def criar_produtos_faltantes_heineken(produtos_detectados, mapeamento):
    """Cria produtos HEINEKEN que estão nas anotações mas não no Django"""
    
    print("\n" + "="*70)
    print("➕ VERIFICANDO PRODUTOS FALTANTES")
    print("="*70)
    
    produtos_django_ids = set(mapeamento.values())
    
    for prod_id, info in produtos_detectados.items():
        if int(prod_id) not in produtos_django_ids:
            print(f"\n⚠️ Produto ID {prod_id} não mapeado: {info['nome']}")
            print(f"   Detectado {info['count']} vezes")
            print(f"   → Precisa ser criado ou mapeado manualmente")


def exibir_solucoes():
    """Exibe soluções para o problema"""
    
    print("\n" + "="*70)
    print("💡 SOLUÇÕES RECOMENDADAS")
    print("="*70)
    
    print("""
    PROBLEMA: Imagens importadas com produto genérico 'FAMILIA_HEINEKEN_MANUAL'
    
    SOLUÇÃO 1: USAR ANOTAÇÕES (Recomendado)
    ----------------------------------------
    ✅ As exportações JSON contêm bounding boxes com produto_id específico
    ✅ Cada bbox já sabe qual produto HEINEKEN foi detectado
    ✅ Podemos reclassificar automaticamente baseado nas anotações
    
    Ação: Executar script de reclassificação inteligente
    
    
    SOLUÇÃO 2: RECLASSIFICAÇÃO MANUAL
    ----------------------------------
    ⚙️ Acesse a página de lotes
    ⚙️ Veja cada imagem individualmente
    ⚙️ Aprove e associe ao produto correto manualmente
    
    Ação: Usar interface web para revisar e aprovar
    
    
    SOLUÇÃO 3: TREINAR COM CLASSE GENÉRICA
    ---------------------------------------
    📦 Manter como 'FAMILIA_HEINEKEN' (classe genérica)
    📦 Modelo detecta "qualquer Heineken" sem especificar qual
    📦 Depois refinamento pode separar os tipos
    
    Ação: Aprovar lote como está e treinar modelo genérico
    
    
    RECOMENDAÇÃO: SOLUÇÃO 1
    -----------------------
    Use as anotações JSON para reclassificar automaticamente.
    Cada imagem já tem informação de qual produto foi detectado.
    """)


def main():
    print("="*70)
    print("🔧 ANÁLISE E RECLASSIFICAÇÃO DE PRODUTOS HEINEKEN")
    print("="*70)
    
    # 1. Analisar anotações
    produtos_detectados = analisar_anotacoes()
    
    # 2. Mapear produtos Django
    mapeamento, produtos_django = mapear_produtos_django()
    
    # 3. Verificar produtos faltantes
    criar_produtos_faltantes_heineken(produtos_detectados, mapeamento)
    
    # 4. Verificar imagens importadas
    reclassificar_imagens_importadas()
    
    # 5. Exibir soluções
    exibir_solucoes()
    
    print("\n" + "="*70)
    print("📋 PRÓXIMAS AÇÕES")
    print("="*70)
    print("""
    1. Escolher solução (1, 2 ou 3)
    2. Se escolher Solução 1:
       - Executar script de reclassificação automática
       - Script lerá JSON e associará cada imagem ao produto correto
       
    3. Se escolher Solução 2:
       - Acesse: http://127.0.0.1:8000/verifik/coleta/lotes/
       - Revise cada imagem
       - Aprove associando ao produto correto
       
    4. Se escolher Solução 3:
       - Renomeie produto para 'HEINEKEN_GENERICA'
       - Aprove lote completo
       - Treine modelo com classe genérica
    """)


if __name__ == '__main__':
    main()
