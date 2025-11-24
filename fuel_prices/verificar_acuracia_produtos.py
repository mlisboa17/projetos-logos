"""
Verifica a acurácia de detecção de cada produto no modelo YOLO
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, DeteccaoProduto
from django.db.models import Count, Avg

print("\n" + "="*70)
print("ANÁLISE DE ACURÁCIA DE DETECÇÃO - VERIFIK")
print("="*70 + "\n")

# Estatísticas gerais
total_produtos = ProdutoMae.objects.count()
total_deteccoes = DeteccaoProduto.objects.count()

print(f"📊 ESTATÍSTICAS GERAIS:")
print(f"   Total de produtos cadastrados: {total_produtos}")
print(f"   Total de detecções registradas: {total_deteccoes}")

# Produtos com detecções
produtos_detectados = DeteccaoProduto.objects.values('produto').distinct().count()
print(f"   Produtos já detectados alguma vez: {produtos_detectados}")
print(f"   Produtos nunca detectados: {total_produtos - produtos_detectados}")

# Análise por produto
print("\n" + "="*70)
print("ACURÁCIA POR PRODUTO")
print("="*70 + "\n")

# Produtos ordenados por número de detecções
produtos_com_deteccao = DeteccaoProduto.objects.values(
    'produto__descricao_produto',
    'produto__tipo',
    'produto__marca'
).annotate(
    total_deteccoes=Count('id'),
    confianca_media=Avg('confianca')
).order_by('-total_deteccoes')

if produtos_com_deteccao.exists():
    print(f"{'Produto':<50} {'Tipo':<15} {'Detecções':<12} {'Confiança Média'}")
    print("-" * 100)
    
    for item in produtos_com_deteccao:
        produto = item['produto__descricao_produto'] or 'Sem nome'
        tipo = item['produto__tipo'] or 'N/A'
        deteccoes = item['total_deteccoes']
        confianca = item['confianca_media'] or 0
        
        # Indicador de qualidade baseado na confiança
        if confianca >= 0.9:
            indicador = "🟢 EXCELENTE"
        elif confianca >= 0.75:
            indicador = "🟡 BOA"
        elif confianca >= 0.5:
            indicador = "🟠 REGULAR"
        else:
            indicador = "🔴 BAIXA"
        
        print(f"{produto[:48]:<50} {tipo[:13]:<15} {deteccoes:<12} {confianca:.2%} {indicador}")
else:
    print("❌ Nenhuma detecção registrada ainda!")
    print("\nMotivos possíveis:")
    print("  1. Modelo YOLO não foi treinado")
    print("  2. API de detecção não foi utilizada")
    print("  3. Nenhuma imagem foi processada ainda")

# Produtos SEM detecção (nunca foram detectados)
print("\n" + "="*70)
print("PRODUTOS NUNCA DETECTADOS")
print("="*70 + "\n")

produtos_cadastrados_ids = set(ProdutoMae.objects.values_list('id', flat=True))
produtos_detectados_ids = set(DeteccaoProduto.objects.values_list('produto_id', flat=True))
produtos_nunca_detectados_ids = produtos_cadastrados_ids - produtos_detectados_ids

if produtos_nunca_detectados_ids:
    produtos_nunca = ProdutoMae.objects.filter(id__in=produtos_nunca_detectados_ids)
    print(f"Total: {produtos_nunca.count()} produtos\n")
    
    # Agrupar por tipo
    tipos = produtos_nunca.values_list('tipo', flat=True).distinct()
    for tipo in tipos:
        if tipo:
            prods_tipo = produtos_nunca.filter(tipo=tipo)
            print(f"\n{tipo}: {prods_tipo.count()} produto(s)")
            for p in prods_tipo[:10]:  # Mostrar apenas 10 primeiros de cada tipo
                tem_foto = "✓ Foto" if p.imagem_referencia else "✗ Sem foto"
                tem_treino = "✓ Treino" if p.imagens_treino else "✗ Sem treino"
                print(f"  - {p.descricao_produto} ({tem_foto}, {tem_treino})")
else:
    print("✅ Todos os produtos cadastrados já foram detectados pelo menos uma vez!")

# Resumo de treinamento
print("\n" + "="*70)
print("STATUS DE TREINAMENTO")
print("="*70 + "\n")

com_foto_ref = ProdutoMae.objects.filter(imagem_referencia__isnull=False).exclude(imagem_referencia='').count()
com_treino = ProdutoMae.objects.filter(imagens_treino__isnull=False).exclude(imagens_treino='').count()

print(f"Produtos com foto de referência: {com_foto_ref}/{total_produtos} ({com_foto_ref/total_produtos*100:.1f}%)")
print(f"Produtos com imagens de treino: {com_treino}/{total_produtos} ({com_treino/total_produtos*100:.1f}%)")
print(f"Produtos prontos para detecção: {produtos_detectados}/{total_produtos} ({produtos_detectados/total_produtos*100:.1f}%)")

print("\n" + "="*70)
print("💡 RECOMENDAÇÕES:")
print("="*70)
print("\n1. Fotografar e treinar produtos com 0 detecções")
print("2. Melhorar qualidade das fotos para produtos com confiança < 75%")
print("3. Adicionar mais imagens de treino para produtos com poucas detecções")
print("4. Testar API de detecção: /api/verifik/detectar/")
print("\n")
