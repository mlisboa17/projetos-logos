"""
Script de Treinamento do Modelo YOLO - VerifiK
Treina o modelo de detecção de produtos usando as imagens já cadastradas
"""
import os
import sys
import django
from pathlib import Path
import shutil

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from django.db.models import Count


def verificar_ultralytics():
    """Verifica se ultralytics está instalado"""
    try:
        from ultralytics import YOLO
        print("✅ Ultralytics instalado")
        return True
    except ImportError:
        print("❌ Ultralytics não encontrado")
        print("📦 Instalando ultralytics...")
        os.system("pip install ultralytics")
        return True


def preparar_dataset():
    """Prepara dataset no formato YOLO"""
    print("\n" + "="*60)
    print("📂 PREPARANDO DATASET YOLO")
    print("="*60)
    
    # Buscar produtos com imagens
    produtos = ProdutoMae.objects.annotate(
        num_imagens=Count('imagens_treino')
    ).filter(num_imagens__gt=0).order_by('tipo', 'marca', 'descricao_produto')
    
    if not produtos.exists():
        print("❌ Nenhum produto com imagens de treino encontrado")
        print("💡 Adicione imagens em /admin/verifik/produtomae/")
        return None
    
    print(f"\n✅ {produtos.count()} produtos com imagens encontradas:")
    for i, produto in enumerate(produtos):
        nome_produto = f"{produto.marca} {produto.descricao_produto}".strip()
        print(f"   {i}. {nome_produto} - {produto.num_imagens} imagens")
    
    # Criar estrutura de diretórios
    dataset_dir = BASE_DIR / 'verifik' / 'dataset_yolo'
    train_images_dir = dataset_dir / 'train' / 'images'
    train_labels_dir = dataset_dir / 'train' / 'labels'
    
    # Limpar e recriar
    if dataset_dir.exists():
        print(f"\n🗑️  Removendo dataset antigo...")
        shutil.rmtree(dataset_dir)
    
    train_images_dir.mkdir(parents=True, exist_ok=True)
    train_labels_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Diretórios criados em: {dataset_dir}")
    
    # Mapear produtos para IDs de classe
    produto_to_class = {produto.id: idx for idx, produto in enumerate(produtos)}
    class_names = [f"{p.marca} {p.descricao_produto}".strip() for p in produtos]
    
    print(f"\n📋 Mapeamento de Classes:")
    for produto_id, class_id in produto_to_class.items():
        produto = produtos.get(id=produto_id)
        nome_produto = f"{produto.marca} {produto.descricao_produto}".strip()
        print(f"   Classe {class_id}: {nome_produto}")
    
    # Copiar imagens e criar labels
    print(f"\n📸 Copiando imagens e gerando labels...")
    total_imagens = 0
    
    for produto in produtos:
        class_id = produto_to_class[produto.id]
        imagens = produto.imagens_treino.all()
        
        for img in imagens:
            if not img.imagem:
                continue
            
            # Caminho da imagem original
            src_path = Path(img.imagem.path)
            if not src_path.exists():
                print(f"   ⚠️  Imagem não encontrada: {src_path}")
                continue
            
            # Copiar imagem
            img_filename = f"{produto.id}_{img.id}.jpg"
            dst_image_path = train_images_dir / img_filename
            shutil.copy2(src_path, dst_image_path)
            
            # Criar label YOLO (formato: class x_center y_center width height)
            # Como as imagens são do produto inteiro, usamos bbox full
            label_filename = f"{produto.id}_{img.id}.txt"
            label_path = train_labels_dir / label_filename
            
            with open(label_path, 'w') as f:
                # Produto ocupa imagem toda: centro (0.5, 0.5), tamanho (1.0, 1.0)
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            total_imagens += 1
    
    print(f"✅ {total_imagens} imagens preparadas")
    
    # Criar data.yaml
    data_yaml_path = dataset_dir / 'data.yaml'
    yaml_content = f"""# VerifiK Dataset Configuration
path: {dataset_dir.absolute()}
train: train/images
val: train/images  # Usando mesmo conjunto para treino e validação (dataset pequeno)

# Classes
nc: {len(class_names)}
names: {class_names}
"""
    
    with open(data_yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"✅ Arquivo de configuração criado: {data_yaml_path}")
    
    return data_yaml_path, class_names


def treinar_modelo(data_yaml_path, class_names):
    """Treina o modelo YOLOv8"""
    from ultralytics import YOLO
    
    print("\n" + "="*60)
    print("🚀 INICIANDO TREINAMENTO DO MODELO")
    print("="*60)
    
    print(f"\n📊 Configuração:")
    print(f"   • Classes: {len(class_names)}")
    print(f"   • Épocas: 50")
    print(f"   • Batch size: 8")
    print(f"   • Tamanho imagem: 640px")
    print(f"   • Modelo base: YOLOv8n (nano)")
    
    # Verificar se existe checkpoint anterior
    checkpoint_path = BASE_DIR / 'verifik' / 'runs' / 'treino_verifik' / 'weights' / 'last.pt'
    
    if checkpoint_path.exists():
        print(f"\n🔄 Checkpoint encontrado!")
        print(f"   {checkpoint_path}")
        resposta = input("\n▶️  Deseja continuar de onde parou? (s/N): ").strip().lower()
        
        if resposta == 's':
            print(f"\n📥 Retomando treinamento do checkpoint...")
            model = YOLO(str(checkpoint_path))
            resume = True
        else:
            print(f"\n📥 Carregando modelo base YOLOv8n (novo treinamento)...")
            model = YOLO('yolov8n.pt')
            resume = False
    else:
        print(f"\n📥 Carregando modelo base YOLOv8n...")
        model = YOLO('yolov8n.pt')
        resume = False
    
    # Treinar
    if resume:
        print(f"\n🎯 Retomando treinamento...")
    else:
        print(f"\n🎯 Iniciando treinamento (pode levar 15-30 minutos)...")
    print(f"⏳ Aguarde... Pressione Ctrl+C para pausar\n")
    
    results = model.train(
        data=str(data_yaml_path),
        epochs=50,
        batch=8,
        imgsz=640,
        patience=10,
        project=str(BASE_DIR / 'verifik' / 'runs'),
        name='treino_verifik',
        exist_ok=True,
        resume=resume,
        verbose=True
    )
    
    print(f"\n✅ Treinamento concluído!")
    
    return model, results


def salvar_modelo(model):
    """Salva o modelo treinado"""
    print("\n" + "="*60)
    print("💾 SALVANDO MODELO TREINADO")
    print("="*60)
    
    # Caminho do melhor modelo
    best_model_path = BASE_DIR / 'verifik' / 'runs' / 'treino_verifik' / 'weights' / 'best.pt'
    
    if not best_model_path.exists():
        print(f"❌ Modelo best.pt não encontrado em: {best_model_path}")
        return None
    
    # Copiar para verifik/verifik_yolov8.pt
    final_model_path = BASE_DIR / 'verifik' / 'verifik_yolov8.pt'
    shutil.copy2(best_model_path, final_model_path)
    
    # Tamanho do arquivo
    size_mb = final_model_path.stat().st_size / (1024 * 1024)
    
    print(f"✅ Modelo salvo em: {final_model_path}")
    print(f"📦 Tamanho: {size_mb:.2f} MB")
    
    return final_model_path


def testar_modelo(model_path, class_names):
    """Testa o modelo treinado em todas as imagens de cada produto"""
    from ultralytics import YOLO
    
    print("\n" + "="*60)
    print("🧪 TESTANDO MODELO TREINADO - ANÁLISE COMPLETA")
    print("="*60)
    
    # Carregar modelo treinado
    model = YOLO(str(model_path))
    
    # Buscar todos os produtos com imagens
    produtos = ProdutoMae.objects.annotate(
        num_imagens=Count('imagens_treino')
    ).filter(num_imagens__gt=0).order_by('tipo', 'marca')
    
    print(f"\n🔍 Testando {produtos.count()} produtos:\n")
    
    resultados_finais = []
    
    for produto in produtos:
        nome_produto = f"{produto.marca} {produto.descricao_produto}".strip()
        imagens = produto.imagens_treino.all()
        
        total_imagens = 0
        deteccoes_corretas = 0
        confiancas = []
        
        for img in imagens:
            if not img.imagem:
                continue
            
            try:
                img_path = img.imagem.path
                total_imagens += 1
                
                # Predição
                results = model.predict(img_path, conf=0.3, verbose=False)
                
                # Processar resultado
                melhor_deteccao = None
                melhor_conf = 0
                
                for r in results:
                    for box in r.boxes:
                        class_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = class_names[class_id]
                        
                        if conf > melhor_conf:
                            melhor_conf = conf
                            melhor_deteccao = class_name
                
                # Verificar se detectou corretamente
                if melhor_deteccao == nome_produto:
                    deteccoes_corretas += 1
                    confiancas.append(melhor_conf)
                
            except Exception as e:
                continue
        
        # Calcular métricas
        if total_imagens > 0:
            taxa_acerto = (deteccoes_corretas / total_imagens) * 100
            confianca_media = sum(confiancas) / len(confiancas) if confiancas else 0
            
            # Status
            if taxa_acerto >= 80 and confianca_media >= 0.75:
                status = "🟢 EXCELENTE"
            elif taxa_acerto >= 60 and confianca_media >= 0.60:
                status = "🟡 BOM"
            else:
                status = "🔴 BAIXO"
            
            resultados_finais.append({
                'produto': nome_produto,
                'total_imagens': total_imagens,
                'acertos': deteccoes_corretas,
                'taxa_acerto': taxa_acerto,
                'confianca_media': confianca_media,
                'status': status
            })
    
    # Imprimir resumo por produto
    print("\n" + "="*60)
    print("📊 RESULTADOS POR PRODUTO")
    print("="*60 + "\n")
    
    for r in resultados_finais:
        print(f"{r['status']} {r['produto']}")
        print(f"   📸 Imagens testadas: {r['total_imagens']}")
        print(f"   ✅ Acertos: {r['acertos']}/{r['total_imagens']} ({r['taxa_acerto']:.1f}%)")
        print(f"   🎯 Confiança média: {r['confianca_media']:.1%}")
        print()
    
    # Estatísticas gerais
    print("="*60)
    print("📈 ESTATÍSTICAS GERAIS")
    print("="*60 + "\n")
    
    total_imgs = sum(r['total_imagens'] for r in resultados_finais)
    total_acertos = sum(r['acertos'] for r in resultados_finais)
    taxa_geral = (total_acertos / total_imgs * 100) if total_imgs > 0 else 0
    conf_geral = sum(r['confianca_media'] for r in resultados_finais) / len(resultados_finais) if resultados_finais else 0
    
    print(f"Total de produtos: {len(resultados_finais)}")
    print(f"Total de imagens: {total_imgs}")
    print(f"Taxa de acerto geral: {taxa_geral:.1f}%")
    print(f"Confiança média geral: {conf_geral:.1%}")
    
    excelentes = sum(1 for r in resultados_finais if '🟢' in r['status'])
    bons = sum(1 for r in resultados_finais if '🟡' in r['status'])
    baixos = sum(1 for r in resultados_finais if '🔴' in r['status'])
    
    print(f"\n🟢 Excelente: {excelentes} produtos")
    print(f"🟡 Bom: {bons} produtos")
    print(f"🔴 Baixo: {baixos} produtos")


def main():
    """Função principal"""
    print("\n" + "="*60)
    print("🎯 TREINAMENTO DO MODELO YOLO - VERIFIK")
    print("="*60)
    
    # 1. Verificar ultralytics
    if not verificar_ultralytics():
        return
    
    # 2. Preparar dataset
    resultado = preparar_dataset()
    if resultado is None:
        return
    
    data_yaml_path, class_names = resultado
    
    # 3. Iniciar treinamento automaticamente
    print("\n" + "="*60)
    print("🚀 INICIANDO TREINAMENTO (estimativa: 15-30 minutos)")
    print("="*60)
    
    # 4. Treinar modelo
    model, results = treinar_modelo(data_yaml_path, class_names)
    
    # 5. Salvar modelo
    model_path = salvar_modelo(model)
    if model_path is None:
        return
    
    # 6. Testar modelo
    testar_modelo(model_path, class_names)
    
    print("\n" + "="*60)
    print("✅ PROCESSO COMPLETO!")
    print("="*60)
    print(f"\n📁 Modelo salvo em: {model_path}")
    print(f"🔌 Use na API: YOLO('{model_path}')")
    print(f"📊 Resultados do treino: verifik/runs/treino_verifik/")
    print("\n🎉 O modelo está pronto para detecção de produtos!\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Treinamento interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
