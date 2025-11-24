"""
Analisa acurácia dos produtos treinados no VerifiK
"""
import os
import sys
import django

# Configurar Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae

print("\n" + "="*80)
print("ANÁLISE DE PRODUTOS TREINADOS - VERIFIK")
print("="*80 + "\n")

# Buscar todos os produtos
total = ProdutoMae.objects.count()
print(f"📊 TOTAL DE PRODUTOS CADASTRADOS: {total}\n")

# Produtos com imagens de treino
com_treino = ProdutoMae.objects.filter(imagens_treino__isnull=False).distinct()
sem_treino = ProdutoMae.objects.filter(imagens_treino__isnull=True)

print(f"✅ PRODUTOS COM IMAGENS DE TREINO: {com_treino.count()}")
print(f"⚠️  PRODUTOS SEM IMAGENS DE TREINO: {sem_treino.count()}\n")

# Mostrar produtos treinados
if com_treino.exists():
    print("="*80)
    print("PRODUTOS COM IMAGENS DE TREINO")
    print("="*80)
    print(f"{'Produto':<50} {'Tipo':<15} {'Qtd Imagens'}")
    print("-"*80)
    
    for produto in com_treino.order_by('tipo', 'descricao_produto'):
        nome = produto.descricao_produto[:48] if produto.descricao_produto else 'Sem nome'
        tipo = produto.tipo[:13] if produto.tipo else 'N/A'
        
        # Contar imagens de treino
        num_imgs = produto.imagens_treino.count()
        
        # Status visual
        if num_imgs >= 20:
            status = "🟢 Ótimo"
        elif num_imgs >= 10:
            status = "🟡 Bom"
        else:
            status = "🟠 Pouco"
        
        print(f"{nome:<50} {tipo:<15} {num_imgs:3d} {status}")
    
    print("="*80)
else:
    print("❌ Nenhum produto possui imagens de treino!\n")

# Estatísticas por tipo
print("\n" + "="*80)
print("ESTATÍSTICAS POR TIPO")
print("="*80 + "\n")

todos_tipos = ProdutoMae.objects.values_list('tipo', flat=True).distinct().order_by('tipo')

for tipo in todos_tipos:
    if tipo:
        total_tipo = ProdutoMae.objects.filter(tipo=tipo).count()
        treinados_tipo = com_treino.filter(tipo=tipo).count()
        percentual = (treinados_tipo / total_tipo * 100) if total_tipo > 0 else 0
        
        # Barra de progresso
        barra_len = 30
        preenchido = int((treinados_tipo / total_tipo * barra_len)) if total_tipo > 0 else 0
        barra = "█" * preenchido + "░" * (barra_len - preenchido)
        
        print(f"{tipo:<20} [{barra}] {treinados_tipo:3d}/{total_tipo:3d} ({percentual:5.1f}%)")

# Produtos sem treino - Top 20
if sem_treino.exists():
    print("\n" + "="*80)
    print("PRODUTOS SEM IMAGENS DE TREINO (Top 20)")
    print("="*80)
    print(f"{'Produto':<50} {'Tipo':<15} {'Tem Foto Ref?'}")
    print("-"*80)
    
    for produto in sem_treino.order_by('tipo', 'descricao_produto')[:20]:
        nome = produto.descricao_produto[:48] if produto.descricao_produto else 'Sem nome'
        tipo = produto.tipo[:13] if produto.tipo else 'N/A'
        tem_ref = "✓ SIM" if produto.imagem_referencia else "✗ NÃO"
        
        print(f"{nome:<50} {tipo:<15} {tem_ref}")
    
    if sem_treino.count() > 20:
        print(f"\n... e mais {sem_treino.count() - 20} produtos sem treino")

# Resumo
print("\n" + "="*80)
print("📊 RESUMO FINAL")
print("="*80)

percentual_treinado = (com_treino.count() / total * 100) if total > 0 else 0

print(f"\n  Total de produtos: {total}")
print(f"  Produtos treinados: {com_treino.count()} ({percentual_treinado:.1f}%)")
print(f"  Produtos pendentes: {sem_treino.count()} ({100-percentual_treinado:.1f}%)")

# Total de imagens
total_imagens = sum([p.imagens_treino.count() for p in com_treino])
media_por_produto = total_imagens / com_treino.count() if com_treino.count() > 0 else 0

print(f"\n  Total de imagens de treino: {total_imagens}")
print(f"  Média por produto treinado: {media_por_produto:.1f} imagens")

# Avaliação
if percentual_treinado < 20:
    print("\n  🔴 CRÍTICO: Muito poucos produtos treinados!")
    print("     Ação: Iniciar processo de fotografia e treinamento urgente")
elif percentual_treinado < 50:
    print("\n  🟠 ATENÇÃO: Menos da metade dos produtos treinados")
    print("     Ação: Priorizar produtos mais vendidos")
elif percentual_treinado < 80:
    print("\n  🟡 BOM: Continue o processo de treinamento")
else:
    print("\n  🟢 EXCELENTE: Maioria dos produtos já treinada!")

print("\n" + "="*80 + "\n")
