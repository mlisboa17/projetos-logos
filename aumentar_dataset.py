"""
Script de Data Augmentation para produtos de conveniência
Usa Albumentations para multiplicar o dataset mantendo anotações YOLO

De 100 imagens → 1000+ imagens com variações realistas
"""

import os
import cv2
import albumentations as A
from pathlib import Path
import shutil
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO DE TRANSFORMAÇÕES
# ============================================================

def criar_pipeline_augmentation():
    """
    Pipeline de transformações para simular condições reais de loja:
    - Diferentes iluminações
    - Produtos em ângulos variados
    - Câmera em movimento (blur)
    - Qualidade de imagem variada
    """
    
    transform = A.Compose([
        # Rotação leve (produto inclinado no balcão)
        A.Rotate(limit=15, p=0.5),
        
        # Flip horizontal (produto virado)
        A.HorizontalFlip(p=0.3),
        
        # Mudanças de iluminação (luz natural, artificial, sombra)
        A.RandomBrightnessContrast(
            brightness_limit=0.3,
            contrast_limit=0.3,
            p=0.7
        ),
        
        # Saturação (cores mais/menos vivas)
        A.HueSaturationValue(
            hue_shift_limit=10,
            sat_shift_limit=30,
            val_shift_limit=20,
            p=0.5
        ),
        
        # Blur (câmera em movimento, fora de foco)
        A.OneOf([
            A.MotionBlur(blur_limit=5, p=1.0),
            A.GaussianBlur(blur_limit=5, p=1.0),
        ], p=0.3),
        
        # Ruído (qualidade de câmera)
        A.GaussNoise(var_limit=(5.0, 30.0), p=0.2),
        
        # Mudança de perspectiva (ângulo da câmera)
        A.Perspective(scale=(0.02, 0.05), p=0.3),
        
        # Sombras
        A.RandomShadow(
            shadow_roi=(0, 0.5, 1, 1),
            num_shadows_lower=1,
            num_shadows_upper=2,
            shadow_dimension=5,
            p=0.2
        ),
        
        # Crop e resize (zoom in/out)
        A.RandomSizedBBoxSafeCrop(
            height=640,
            width=640,
            erosion_rate=0.2,
            p=0.3
        ),
        
    ], bbox_params=A.BboxParams(
        format='yolo',
        label_fields=['class_labels'],
        min_visibility=0.3  # Descarta bbox se <30% visível
    ))
    
    return transform


def ler_anotacao_yolo(txt_path):
    """
    Lê arquivo de anotação YOLO
    Retorna: (bboxes, class_labels)
    """
    bboxes = []
    class_labels = []
    
    if not os.path.exists(txt_path):
        return bboxes, class_labels
    
    with open(txt_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                bboxes.append([x_center, y_center, width, height])
                class_labels.append(class_id)
    
    return bboxes, class_labels


def salvar_anotacao_yolo(txt_path, bboxes, class_labels):
    """Salva anotações no formato YOLO"""
    with open(txt_path, 'w') as f:
        for bbox, class_id in zip(bboxes, class_labels):
            x_center, y_center, width, height = bbox
            f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")


def aumentar_dataset(
    pasta_origem,
    pasta_destino,
    num_augmentacoes=10,
    manter_originais=True
):
    """
    Aplica data augmentation no dataset
    
    Args:
        pasta_origem: Pasta com imagens e anotações YOLO
        pasta_destino: Onde salvar dataset aumentado
        num_augmentacoes: Quantas variações gerar por imagem
        manter_originais: Se True, copia originais também
    """
    
    print("="*70)
    print("🔄 DATA AUGMENTATION - PRODUTOS DE CONVENIÊNCIA")
    print("="*70)
    print(f"📁 Origem: {pasta_origem}")
    print(f"📁 Destino: {pasta_destino}")
    print(f"🔢 Augmentações por imagem: {num_augmentacoes}")
    print()
    
    # Criar pasta destino
    os.makedirs(pasta_destino, exist_ok=True)
    
    # Pipeline de transformações
    transform = criar_pipeline_augmentation()
    
    # Buscar todas as imagens
    extensoes = ['.jpg', '.jpeg', '.png']
    imagens = []
    
    for ext in extensoes:
        imagens.extend(Path(pasta_origem).rglob(f"*{ext}"))
    
    total_imagens = len(imagens)
    total_geradas = 0
    
    print(f"📸 Encontradas {total_imagens} imagens")
    print(f"📊 Serão geradas ~{total_imagens * num_augmentacoes} novas imagens")
    print()
    
    for idx, img_path in enumerate(imagens, 1):
        print(f"[{idx}/{total_imagens}] {img_path.name}")
        
        # Ler imagem
        image = cv2.imread(str(img_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Ler anotação YOLO
        txt_path = img_path.with_suffix('.txt')
        bboxes, class_labels = ler_anotacao_yolo(txt_path)
        
        if not bboxes:
            print(f"   ⚠️ Sem anotações, pulando...")
            continue
        
        # Copiar original se solicitado
        if manter_originais:
            shutil.copy(img_path, pasta_destino / img_path.name)
            if txt_path.exists():
                shutil.copy(txt_path, pasta_destino / txt_path.name)
            total_geradas += 1
        
        # Gerar augmentações
        for aug_idx in range(num_augmentacoes):
            try:
                # Aplicar transformações
                transformed = transform(
                    image=image,
                    bboxes=bboxes,
                    class_labels=class_labels
                )
                
                # Verificar se ainda tem bboxes válidos
                if not transformed['bboxes']:
                    continue
                
                # Salvar imagem aumentada
                nome_base = img_path.stem
                nome_aug = f"{nome_base}_aug_{aug_idx+1}{img_path.suffix}"
                
                img_aug = cv2.cvtColor(transformed['image'], cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(pasta_destino / nome_aug), img_aug)
                
                # Salvar anotações aumentadas
                txt_aug = pasta_destino / f"{nome_base}_aug_{aug_idx+1}.txt"
                salvar_anotacao_yolo(
                    txt_aug,
                    transformed['bboxes'],
                    transformed['class_labels']
                )
                
                total_geradas += 1
                
            except Exception as e:
                print(f"   ⚠️ Erro na augmentação {aug_idx+1}: {e}")
                continue
        
        print(f"   ✅ {num_augmentacoes} variações geradas")
    
    print()
    print("="*70)
    print("✅ AUGMENTATION CONCLUÍDO!")
    print("="*70)
    print(f"📊 Total de imagens geradas: {total_geradas}")
    print(f"📁 Dataset aumentado em: {pasta_destino}")
    print()


def aumentar_dataset_completo(
    pasta_dataset='assets/dataset/train',
    pasta_saida='assets/dataset_augmented',
    num_augmentacoes=10,
    apenas_categorias=None  # Lista de categorias específicas ou None para todas
):
    """
    Processa todas as categorias de produtos (ou apenas categorias específicas)
    
    Args:
        apenas_categorias: Lista de nomes de pastas ou None para processar todas
                          Ex: ['CERVEJA AMSTEL 473ML', 'REFRIGERANTE COCA 2L']
    """
    
    print("\n" + "="*70)
    print("🚀 AUMENTANDO DATASET COMPLETO")
    print("="*70)
    
    pasta_dataset = Path(pasta_dataset)
    pasta_saida = Path(pasta_saida)
    
    # Criar estrutura de pastas
    os.makedirs(pasta_saida, exist_ok=True)
    
    # Processar cada categoria de produto
    todas_categorias = [d for d in pasta_dataset.iterdir() if d.is_dir()]
    
    # Filtrar se especificado
    if apenas_categorias:
        categorias = [c for c in todas_categorias if c.name in apenas_categorias]
        print(f"\n⚡ Modo incremental: processando apenas {len(categorias)} categorias")
    else:
        categorias = todas_categorias
        print(f"\n📦 Modo completo: processando todas as {len(categorias)} categorias")
    
    print(f"\n📦 Categorias encontradas: {len(categorias)}")
    for cat in categorias:
        print(f"   - {cat.name}")
    print()
    
    for cat in categorias:
        print(f"\n{'='*70}")
        print(f"📦 Processando: {cat.name}")
        print(f"{'='*70}")
        
        # Criar pasta de saída para categoria
        pasta_cat_saida = pasta_saida / cat.name
        
        # Aumentar dataset
        aumentar_dataset(
            pasta_origem=cat,
            pasta_destino=pasta_cat_saida,
            num_augmentacoes=num_augmentacoes,
            manter_originais=True
        )
    
    print("\n" + "="*70)
    print("🎉 TODOS OS PRODUTOS PROCESSADOS!")
    print("="*70)
    print(f"📁 Dataset aumentado salvo em: {pasta_saida}")
    print()
    print("🎯 PRÓXIMOS PASSOS:")
    print("   1. Treinar modelo YOLO com dataset aumentado")
    print("   2. Validar performance com imagens reais")
    print("   3. Integrar modelo na câmera")
    print()


if __name__ == '__main__':
    # Verificar se Albumentations está instalado
    try:
        import albumentations as A
    except ImportError:
        print("❌ Albumentations não instalado!")
        print("   Execute: pip install albumentations")
        exit(1)
    
    # MODO 1 - Processar TUDO (primeira vez ou quando quiser reprocessar tudo)
    aumentar_dataset_completo(
        pasta_dataset='assets/dataset/train',
        pasta_saida='assets/dataset_augmented',
        num_augmentacoes=10  # 10 variações por imagem
    )
    
    # MODO 2 - Processar apenas novos produtos (quando adicionar mais produtos)
    # Descomente as linhas abaixo e especifique os produtos novos:
    
    # aumentar_dataset_completo(
    #     pasta_dataset='assets/dataset/train',
    #     pasta_saida='assets/dataset_augmented',
    #     num_augmentacoes=10,
    #     apenas_categorias=[
    #         'REFRIGERANTE COCA COLA 2L',  # Exemplo de novos produtos
    #         'CHOCOLATE LACTA 100G',
    #         'SALGADINHO RUFFLES 50G'
    #     ]
    # )
