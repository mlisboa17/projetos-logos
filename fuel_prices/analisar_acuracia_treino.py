"""
Analisa acurácia dos produtos treinados na tabela ProdutoMae
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae

print("\n" + "="*80)
print("ANÁLISE DE ACURÁCIA - PRODUTOS TREINADOS (ProdutoMae)")
print("="*80 + "\n")

# Buscar todos os produtos
total = ProdutoMae.objects.count()
print(f"📊 TOTAL DE PRODUTOS: {total}\n")

# Produtos com imagens de treino (considerados "treinados")
# imagens_treino é uma relação ManyToMany com ImagemProduto
com_treino = ProdutoMae.objects.filter(
    imagens_treino__isnull=False
).distinct()

print(f"✅ PRODUTOS COM IMAGENS DE TREINO: {com_treino.count()}\n")

if com_treino.exists():
    print("="*80)
    print(f"{'Produto':<45} {'Tipo':<15} {'Marca':<15} {'Qtd Imgs'}")
    print("="*80)
    
    for produto in com_treino:
        nome = produto.descricao_produto[:43] if produto.descricao_produto else 'Sem nome'
        tipo = produto.tipo[:13] if produto.tipo else 'N/A'
        marca = produto.marca[:13] if produto.marca else 'N/A'
        
        # Contar quantas imagens de treino este produto tem
        num_imagens = produto.imagens_treino.count()
        
        # Verificar se tem foto de referência também
        tem_ref = "✓ Ref" if produto.imagem_referencia else "✗ Sem Ref"
        
        print(f"{nome:<45} {tipo:<15} {marca:<15} {num_imagens} imgs | {tem_ref}")
    
    print("="*80)
else:
    print("❌ Nenhum produto tem imagens de treino cadastradas!\n")

# Produtos SEM treino
sem_treino = ProdutoMae.objects.filter(
    imagens_treino__isnull=True
)

print(f"\n⚠️  PRODUTOS SEM IMAGENS DE TREINO: {sem_treino.count()}\n")

if sem_treino.exists():
    # Agrupar por tipo
    print("Distribuição por tipo:")
    print("-" * 80)
    
    tipos = sem_treino.values_list('tipo', flat=True).distinct()
    for tipo in sorted(tipos):
        if tipo:
            count = sem_treino.filter(tipo=tipo).count()
            print(f"  {tipo}: {count} produto(s)")
    
    print("\n" + "="*80)
    print("PRIMEIROS 20 PRODUTOS SEM TREINO:")
    print("="*80)
    print(f"{'Produto':<45} {'Tipo':<15} {'Tem Foto Ref?'}")
    print("-"*80)
    
    for produto in sem_treino[:20]:
        nome = produto.descricao_produto[:43] if produto.descricao_produto else 'Sem nome'
        tipo = produto.tipo[:13] if produto.tipo else 'N/A'
        tem_ref = "✓ SIM" if produto.imagem_referencia else "✗ NÃO"
        
        print(f"{nome:<45} {tipo:<15} {tem_ref}")
    
    if sem_treino.count() > 20:
        print(f"\n... e mais {sem_treino.count() - 20} produtos")

# Estatísticas por tipo
print("\n" + "="*80)
print("ESTATÍSTICAS POR TIPO DE PRODUTO")
print("="*80 + "\n")

todos_tipos = ProdutoMae.objects.values_list('tipo', flat=True).distinct()
for tipo in sorted(todos_tipos):
    if tipo:
        total_tipo = ProdutoMae.objects.filter(tipo=tipo).count()
        treinados_tipo = com_treino.filter(tipo=tipo).count()
        percentual = (treinados_tipo / total_tipo * 100) if total_tipo > 0 else 0
        
        # Barra de progresso visual
        barra_total = 30
        barra_preenchida = int((treinados_tipo / total_tipo * barra_total)) if total_tipo > 0 else 0
        barra = "█" * barra_preenchida + "░" * (barra_total - barra_preenchida)
        
        print(f"{tipo:<20} [{barra}] {treinados_tipo}/{total_tipo} ({percentual:.1f}%)")

# Resumo final
print("\n" + "="*80)
print("📈 RESUMO GERAL")
print("="*80)
percentual_geral = (com_treino.count() / total * 100) if total > 0 else 0
print(f"\n  Total de produtos: {total}")
print(f"  Produtos treinados: {com_treino.count()} ({percentual_geral:.1f}%)")
print(f"  Produtos pendentes: {sem_treino.count()} ({100-percentual_geral:.1f}%)")

if percentual_geral < 50:
    print("\n  ⚠️  ATENÇÃO: Menos de 50% dos produtos estão treinados!")
    print("     Recomendação: Priorizar fotografar e treinar produtos mais vendidos")
elif percentual_geral < 80:
    print("\n  ⚡ BOM PROGRESSO: Continue treinando os produtos restantes")
else:
    print("\n  ✅ EXCELENTE: Maioria dos produtos já está treinada!")

print("\n" + "="*80 + "\n")
