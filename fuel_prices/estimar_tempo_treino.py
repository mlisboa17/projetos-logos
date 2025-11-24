"""
Script para verificar produtos com imagens e estimar tempo de treinamento
"""
import os
import sys
import django

# Adicionar diretório pai ao path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto

print("╔══════════════════════════════════════════════════════════════════╗")
print("║           ANÁLISE DE PRODUTOS PARA TREINAMENTO DE IA            ║")
print("╚══════════════════════════════════════════════════════════════════╝\n")

# Produtos com imagens
produtos_com_imagens = ProdutoMae.objects.filter(
    imagens_treino__isnull=False, 
    ativo=True
).distinct()

total_produtos = produtos_com_imagens.count()
total_imagens = ImagemProduto.objects.filter(ativa=True).count()

print("📊 ESTATÍSTICAS:")
print("=" * 70)
print(f"Total de produtos ativos: {ProdutoMae.objects.filter(ativo=True).count()}")
print(f"Produtos COM imagens: {total_produtos}")
print(f"Produtos SEM imagens: {ProdutoMae.objects.filter(ativo=True, imagens_treino__isnull=True).count()}")
print(f"Total de imagens de treino: {total_imagens}")

if total_produtos > 0:
    media_imagens = total_imagens / total_produtos
    print(f"Média de imagens por produto: {media_imagens:.1f}")
else:
    media_imagens = 0

print("\n📦 PRODUTOS COM IMAGENS:")
print("=" * 70)

if total_produtos > 0:
    for produto in produtos_com_imagens[:20]:  # Mostrar até 20 primeiros
        num_imagens = produto.imagens_treino.filter(ativa=True).count()
        print(f"  • {produto.descricao_produto[:50]:50} | {num_imagens:2} imagens")
    
    if total_produtos > 20:
        print(f"  ... e mais {total_produtos - 20} produtos")
else:
    print("  ⚠️ Nenhum produto com imagens encontrado!")

print("\n⏱️ ESTIMATIVA DE TEMPO DE TREINAMENTO:")
print("=" * 70)

if total_produtos == 0:
    print("❌ Não há produtos para treinar (sem imagens)")
elif total_imagens < 10:
    print("⚠️ DATASET MUITO PEQUENO!")
    print("   Mínimo recomendado: 10+ imagens por produto")
    print("   Você tem: {:.1f} imagens por produto em média".format(media_imagens))
else:
    print("\n🤖 MODELOS DISPONÍVEIS E TEMPOS ESTIMADOS:\n")
    
    # YOLOv8 Nano (mais rápido)
    tempo_yolo_nano = (total_imagens * 0.5) / 60  # ~0.5s por imagem
    print(f"1. YOLOv8 Nano (leve, rápido):")
    print(f"   • Precisão: ★★★☆☆ (Boa)")
    print(f"   • Velocidade detecção: ★★★★★ (Muito rápida)")
    print(f"   • Tempo treinamento: ~{tempo_yolo_nano:.1f} minutos")
    print(f"   • Hardware: CPU ok (GPU melhor)")
    
    # YOLOv8 Small
    tempo_yolo_small = (total_imagens * 1.2) / 60  # ~1.2s por imagem
    print(f"\n2. YOLOv8 Small (balanceado):")
    print(f"   • Precisão: ★★★★☆ (Muito boa)")
    print(f"   • Velocidade detecção: ★★★★☆ (Rápida)")
    print(f"   • Tempo treinamento: ~{tempo_yolo_small:.1f} minutos")
    print(f"   • Hardware: GPU recomendada")
    
    # YOLOv8 Medium
    tempo_yolo_medium = (total_imagens * 2.5) / 60  # ~2.5s por imagem
    print(f"\n3. YOLOv8 Medium (alta precisão):")
    print(f"   • Precisão: ★★★★★ (Excelente)")
    print(f"   • Velocidade detecção: ★★★☆☆ (Boa)")
    print(f"   • Tempo treinamento: ~{tempo_yolo_medium:.1f} minutos")
    print(f"   • Hardware: GPU necessária")
    
    # ResNet50 (Transfer Learning)
    tempo_resnet = (total_imagens * 3.0) / 60  # ~3s por imagem
    print(f"\n4. ResNet50 (Transfer Learning):")
    print(f"   • Precisão: ★★★★★ (Excelente)")
    print(f"   • Velocidade detecção: ★★★☆☆ (Boa)")
    print(f"   • Tempo treinamento: ~{tempo_resnet:.1f} minutos")
    print(f"   • Hardware: GPU necessária")
    
    print("\n📝 OBSERVAÇÕES:")
    print("   • Tempos são estimativas (variam com hardware)")
    print("   • Com GPU: 5-10x mais rápido")
    print("   • Épocas padrão: 50-100 (ajustável)")
    print("   • Dataset pequeno: menos épocas necessárias")

print("\n💡 RECOMENDAÇÃO:")
print("=" * 70)

if total_produtos == 0:
    print("❌ Adicione imagens aos produtos antes de treinar!")
    print("   1. Acesse: http://127.0.0.1:8000/verifik/produtos/")
    print("   2. Clique em um produto")
    print("   3. Adicione 5-10 imagens de diferentes ângulos")
elif total_imagens < 50:
    print("⚠️ Dataset muito pequeno para produção!")
    print(f"   • Você tem: {total_imagens} imagens")
    print("   • Mínimo para teste: 50+ imagens")
    print("   • Ideal produção: 500+ imagens (10+ por produto)")
    print("\n🚀 Para testes iniciais:")
    print(f"   • Modelo: YOLOv8 Nano")
    print(f"   • Tempo: ~{tempo_yolo_nano:.1f} minutos")
    print("   • Épocas: 20-30 (teste rápido)")
else:
    print("✅ Dataset adequado para treinamento!")
    print(f"   • {total_produtos} produtos")
    print(f"   • {total_imagens} imagens")
    print(f"   • {media_imagens:.1f} imagens/produto")
    print("\n🎯 Modelo recomendado: YOLOv8 Small")
    print(f"   • Tempo estimado: {tempo_yolo_small:.1f} minutos")
    print("   • Épocas recomendadas: 50-100")

print("\n" + "=" * 70)
