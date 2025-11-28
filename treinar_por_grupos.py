"""
Sistema de Treinamento YOLO por Grupos de Produtos
Permite treinar o modelo em etapas, adicionando grupos de produtos gradualmente
"""

import os
import sys
import django
from pathlib import Path
import shutil
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from django.db.models import Count

def listar_grupos_disponiveis():
    """Lista todos os grupos/marcas disponíveis"""
    produtos_com_imgs = ProdutoMae.objects.filter(
        imagens_treino__isnull=False
    ).distinct()
    
    # Agrupar por marca
    marcas = {}
    for produto in produtos_com_imgs:
        marca = produto.marca or "SEM_MARCA"
        if marca not in marcas:
            marcas[marca] = {
                'produtos': [],
                'total_imagens': 0
            }
        marcas[marca]['produtos'].append(produto)
        marcas[marca]['total_imagens'] += produto.imagens_treino.count()
    
    return marcas

def mostrar_menu_grupos():
    """Mostra menu de seleção de grupos"""
    print("\n" + "="*70)
    print("🎯 TREINAMENTO YOLO POR GRUPOS - VERIFIK")
    print("="*70)
    
    marcas = listar_grupos_disponiveis()
    
    if not marcas:
        print("\n❌ Nenhum produto com imagens encontrado!")
        print("   Use 'marcar_produtos_manual.py' primeiro.\n")
        return None
    
    print(f"\n📦 GRUPOS DISPONÍVEIS PARA TREINO:")
    print("-" * 70)
    
    grupos_ordenados = sorted(marcas.items(), key=lambda x: x[1]['total_imagens'], reverse=True)
    
    for i, (marca, info) in enumerate(grupos_ordenados, 1):
        qtd_produtos = len(info['produtos'])
        qtd_imagens = info['total_imagens']
        print(f"   {i:2d}. {marca:20s} - {qtd_produtos:2d} produtos, {qtd_imagens:3d} imagens")
    
    print(f"\n   0. TREINAR TODOS OS GRUPOS DE UMA VEZ")
    print("-" * 70)
    
    return grupos_ordenados

def selecionar_grupos(grupos_ordenados):
    """Permite selecionar quais grupos treinar"""
    print("\n💡 OPÇÕES:")
    print("   - Digite números separados por vírgula (ex: 1,3,5)")
    print("   - Digite intervalo com hífen (ex: 1-4 para grupos 1,2,3,4)")
    print("   - Combine ambos (ex: 1-3,5,7 para grupos 1,2,3,5,7)")
    print("   - Digite '0' ou 'todos' para treinar TODOS DE UMA VEZ")
    print("   - Digite 'q' para sair")
    
    escolha = input("\n▶️  Escolha os grupos: ").strip().lower()
    
    if escolha == 'q':
        return None
    
    if escolha == '0' or escolha == 'todos':
        # Todos os grupos
        marcas = [marca for marca, _ in grupos_ordenados]
        print(f"\n✅ Selecionados TODOS os {len(marcas)} grupos")
        return marcas
    
    # Processar grupos específicos (com suporte a intervalos)
    try:
        indices = set()  # Usar set para evitar duplicatas
        
        # Dividir por vírgula
        partes = escolha.split(',')
        
        for parte in partes:
            parte = parte.strip()
            
            # Verificar se é intervalo (ex: 1-4)
            if '-' in parte:
                inicio, fim = parte.split('-')
                inicio = int(inicio.strip())
                fim = int(fim.strip())
                
                # Adicionar todos os números do intervalo
                for i in range(inicio, fim + 1):
                    if 1 <= i <= len(grupos_ordenados):
                        indices.add(i)
                    else:
                        print(f"   ⚠️  Número {i} fora do intervalo, ignorando...")
            else:
                # Número simples
                idx = int(parte)
                if 1 <= idx <= len(grupos_ordenados):
                    indices.add(idx)
                else:
                    print(f"   ⚠️  Número {idx} inválido, ignorando...")
        
        # Converter índices para marcas
        grupos_selecionados = []
        for idx in sorted(indices):
            marca, info = grupos_ordenados[idx - 1]
            grupos_selecionados.append(marca)
            qtd_imgs = info['total_imagens']
            print(f"   ✅ {marca} ({qtd_imgs} imagens)")
        
        if grupos_selecionados:
            print(f"\n📊 Total: {len(grupos_selecionados)} grupos selecionados")
            return grupos_selecionados
        else:
            print("   ❌ Nenhum grupo válido selecionado!")
            return None
    
    except ValueError:
        print("   ❌ Formato inválido! Use números, vírgulas e hífens (ex: 1-3,5,7)")
        return None

def preparar_dataset_grupos(grupos_selecionados):
    """Prepara dataset YOLO apenas com produtos dos grupos selecionados"""
    from treinar_modelo_yolo import preparar_dataset
    
    print("\n" + "="*70)
    print("📂 PREPARANDO DATASET COM GRUPOS SELECIONADOS")
    print("="*70)
    
    # Filtrar produtos apenas dos grupos selecionados
    produtos = ProdutoMae.objects.filter(
        marca__in=grupos_selecionados,
        imagens_treino__isnull=False
    ).distinct().prefetch_related('imagens_treino')
    
    if not produtos.exists():
        print("\n❌ Nenhum produto encontrado nos grupos selecionados!")
        return None
    
    print(f"\n✅ Grupos selecionados: {', '.join(grupos_selecionados)}")
    print(f"✅ {produtos.count()} produtos encontrados")
    
    # Mostrar produtos
    for i, produto in enumerate(produtos):
        qtd_imgs = produto.imagens_treino.count()
        print(f"   {i}. {produto.marca} {produto.descricao_produto} - {qtd_imgs} imagens")
    
    # Confirmar
    confirma = input(f"\n▶️  Continuar com estes produtos? (s/N): ").strip().lower()
    if confirma != 's':
        print("❌ Treinamento cancelado pelo usuário")
        return None
    
    # Preparar dataset (usando a função do treinar_modelo_yolo.py)
    # Mas filtrando apenas os produtos selecionados
    dataset_dir = Path(__file__).parent / 'verifik' / 'dataset_yolo'
    train_images_dir = dataset_dir / 'train' / 'images'
    train_labels_dir = dataset_dir / 'train' / 'labels'
    
    # Remover dataset antigo com tratamento de erro
    if dataset_dir.exists():
        print(f"\n🗑️  Removendo dataset antigo...")
        import time
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                shutil.rmtree(dataset_dir)
                break
            except PermissionError as e:
                if tentativa < max_tentativas - 1:
                    print(f"⚠️  Tentativa {tentativa + 1} falhou, aguardando...")
                    time.sleep(1)
                else:
                    print(f"❌ Não foi possível remover o dataset antigo.")
                    print(f"   Feche todos os programas que possam estar usando os arquivos.")
                    print(f"   Execute: Remove-Item -Path '{dataset_dir}' -Recurse -Force")
                    return None
    
    # Criar diretórios
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
            
            # Criar label YOLO
            label_filename = f"{produto.id}_{img.id}.txt"
            label_path = train_labels_dir / label_filename
            
            with open(label_path, 'w') as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            
            total_imagens += 1
    
    print(f"✅ {total_imagens} imagens preparadas")
    
    # Criar data.yaml
    data_yaml_path = dataset_dir / 'data.yaml'
    yaml_content = f"""# VerifiK Dataset Configuration - GRUPOS: {', '.join(grupos_selecionados)}
path: {dataset_dir.absolute()}
train: train/images
val: train/images

# Classes
nc: {len(class_names)}
names: {class_names}
"""
    
    with open(data_yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"✅ Arquivo de configuração criado: {data_yaml_path}")
    
    return data_yaml_path, class_names, total_imagens

def treinar_grupos(grupos_selecionados):
    """Executa treinamento com os grupos selecionados"""
    
    # Preparar dataset
    resultado = preparar_dataset_grupos(grupos_selecionados)
    if resultado is None:
        return
    
    data_yaml_path, class_names, total_imagens = resultado
    
    # Importar função de treino
    from treinar_modelo_yolo import treinar_modelo, salvar_modelo
    
    print("\n" + "="*70)
    print("🚀 INICIANDO TREINAMENTO")
    print("="*70)
    print(f"   • Grupos: {', '.join(grupos_selecionados)}")
    print(f"   • Classes: {len(class_names)}")
    print(f"   • Imagens: {total_imagens}")
    print(f"   • Épocas: 50")
    print(f"   • Batch size: 8")
    print(f"   • Estimativa: 15-30 minutos")
    print("="*70)
    
    # Treinar
    try:
        model, results = treinar_modelo(data_yaml_path, class_names)
        
        # Salvar modelo
        model_path = salvar_modelo(model)
        
        print("\n" + "="*70)
        print("✅ TREINAMENTO CONCLUÍDO COM SUCESSO!")
        print("="*70)
        print(f"   📁 Modelo salvo em: {model_path}")
        print(f"   📊 Grupos treinados: {', '.join(grupos_selecionados)}")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Treinamento interrompido pelo usuário")
        print("   O checkpoint foi salvo em: verifik/runs/treino_verifik/weights/last.pt")
        print("   Execute novamente para continuar de onde parou.")
    except Exception as e:
        print(f"\n❌ Erro durante treinamento: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Função principal"""
    
    # Mostrar menu
    grupos_ordenados = mostrar_menu_grupos()
    if grupos_ordenados is None:
        return
    
    # Selecionar grupos
    grupos_selecionados = selecionar_grupos(grupos_ordenados)
    if grupos_selecionados is None:
        print("\n❌ Operação cancelada")
        return
    
    # Treinar
    treinar_grupos(grupos_selecionados)

if __name__ == '__main__':
    main()
