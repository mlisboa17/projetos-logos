"""
Script para corrigir associações erradas de imagens com produtos
Analisa e corrige baseado nos nomes dos arquivos
"""
import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto

def analisar():
    """Analisa todas as imagens e identifica erros"""
    print("=" * 70)
    print("ANÁLISE DE ASSOCIAÇÕES DE IMAGENS")
    print("=" * 70)
    print()
    
    # Correções com 100% de certeza baseadas em nomes de arquivos/pastas
    correcoes = [
        {
            'de_produto': 1,  # BARRIL DE CHOPP HEINEKEN 5 LITROS
            'para_produto': 51,  # CERVEJA HEINEKEN 330ML
            'filtro': 'heineken330ml',
            'descricao': 'Heineken330ml → CERVEJA HEINEKEN 330ML'
        },
        {
            'de_produto': 15,  # CERVEJA BLACK PRINCESS GOLD PILSEN 330ML
            'para_produto': 117,  # REFRIGERANTE BLACK PEPSI 350ML
            'filtro': 'pepsiblack',
            'descricao': 'pepsiblack350ml → REFRIGERANTE BLACK PEPSI 350ML'
        },
        {
            'de_produto': 24,  # CERVEJA BUDWEISER LATA 473 ML
            'para_produto': 25,  # CERVEJA BUDWEISER LN 330ML
            'filtro': 'bud_330ml_longneck',
            'descricao': 'bud_330ml_LongNeck → CERVEJA BUDWEISER LN 330ML'
        },
        {
            'de_produto': 94,  # CERVEJA STELLA ARTOIS 330ML
            'para_produto': 98,  # CERVEJA STELLA PURE GOLD S GLUTEN LONG 330ML
            'filtro': 'puregold',
            'descricao': 'Stella_PureGold → CERVEJA STELLA PURE GOLD'
        },
    ]
    
    total_erros = 0
    resultado = []
    
    for c in correcoes:
        imgs = ImagemProduto.objects.filter(produto_id=c['de_produto'])
        imgs_afetadas = [i for i in imgs if c['filtro'] in i.imagem.name.lower()]
        
        if not imgs_afetadas:
            continue
            
        prod_de = ProdutoMae.objects.get(id=c['de_produto'])
        prod_para = ProdutoMae.objects.get(id=c['para_produto'])
        
        print(f"🔴 ERRO ENCONTRADO: {c['descricao']}")
        print(f"   DE: ID {c['de_produto']} - {prod_de.descricao_produto}")
        print(f"   PARA: ID {c['para_produto']} - {prod_para.descricao_produto}")
        print(f"   IMAGENS AFETADAS: {len(imgs_afetadas)}")
        print(f"   Exemplo: {imgs_afetadas[0].imagem.name}")
        print()
        
        total_erros += len(imgs_afetadas)
        resultado.append({
            **c,
            'imagens': imgs_afetadas,
            'prod_de_nome': prod_de.descricao_produto,
            'prod_para_nome': prod_para.descricao_produto
        })
    
    print("=" * 70)
    print(f"TOTAL DE IMAGENS COM ERRO: {total_erros}")
    print("=" * 70)
    
    return resultado


def corrigir(resultado, aplicar=False):
    """Aplica as correções"""
    if not resultado:
        print("Nenhuma correção necessária!")
        return
    
    print()
    if aplicar:
        print("🔧 APLICANDO CORREÇÕES...")
    else:
        print("📋 SIMULAÇÃO (use --aplicar para executar)")
    print()
    
    for r in resultado:
        print(f"{'✅ Corrigindo' if aplicar else '📝 Corrigiria'}: {r['descricao']}")
        print(f"   {len(r['imagens'])} imagens: {r['de_produto']} → {r['para_produto']}")
        
        if aplicar:
            for img in r['imagens']:
                img.produto_id = r['para_produto']
                img.save()
            print(f"   ✅ {len(r['imagens'])} imagens corrigidas!")
        print()
    
    if aplicar:
        print("=" * 70)
        print("✅ TODAS AS CORREÇÕES FORAM APLICADAS!")
        print("=" * 70)


def verificar_imagens_invalidas():
    """Verifica imagens que podem não servir para treino"""
    print()
    print("=" * 70)
    print("VERIFICAÇÃO DE IMAGENS POTENCIALMENTE INVÁLIDAS")
    print("=" * 70)
    print()
    
    suspeitas = []
    
    # Verificar imagens com nomes genéricos
    for img in ImagemProduto.objects.all().select_related('produto'):
        nome = img.imagem.name.lower()
        motivo = None
        
        # Imagens sem identificação clara
        if 'whatsapp image' in nome and not any(x in nome for x in ['amstel', 'heineken', 'budweiser', 'devassa', 'pepsi']):
            motivo = "WhatsApp sem identificação do produto"
        
        # Arquivos muito genéricos
        elif nome.endswith('.jpg') and nome.split('/')[-1].startswith('20251') and len(nome.split('/')[-1]) < 20:
            motivo = "Nome genérico (só data)"
        
        if motivo:
            suspeitas.append({
                'id': img.id,
                'arquivo': img.imagem.name,
                'produto': img.produto.descricao_produto,
                'motivo': motivo
            })
    
    if suspeitas:
        print(f"⚠️ {len(suspeitas)} imagens suspeitas encontradas:")
        print()
        for s in suspeitas[:20]:
            print(f"  ID {s['id']}: {s['arquivo'][:60]}")
            print(f"     Produto: {s['produto']}")
            print(f"     Motivo: {s['motivo']}")
            print()
        if len(suspeitas) > 20:
            print(f"  ... e mais {len(suspeitas) - 20} imagens")
    else:
        print("✅ Nenhuma imagem suspeita encontrada!")


def mostrar_resumo_final():
    """Mostra resumo após correções"""
    print()
    print("=" * 70)
    print("RESUMO ATUAL DO BANCO DE DADOS")
    print("=" * 70)
    print()
    
    from django.db.models import Count
    produtos = ImagemProduto.objects.values(
        'produto_id', 
        'produto__descricao_produto'
    ).annotate(
        total=Count('id')
    ).order_by('-total')
    
    print("PRODUTOS COM IMAGENS:")
    for p in produtos:
        print(f"  ID {p['produto_id']}: {p['produto__descricao_produto']} = {p['total']} imgs")
    
    print()
    print(f"Total geral: {ImagemProduto.objects.count()} imagens")


if __name__ == "__main__":
    aplicar = '--aplicar' in sys.argv
    
    # Analisar erros
    resultado = analisar()
    
    # Corrigir (simulação ou real)
    corrigir(resultado, aplicar=aplicar)
    
    # Verificar imagens inválidas
    verificar_imagens_invalidas()
    
    # Mostrar resumo se aplicou
    if aplicar:
        mostrar_resumo_final()
    else:
        print()
        print("💡 Para aplicar as correções, execute:")
        print("   python corrigir_associacoes.py --aplicar")
