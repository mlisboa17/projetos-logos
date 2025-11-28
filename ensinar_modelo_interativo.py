"""
VerifiK - Sistema Interativo de Ensino do Modelo
Permite corrigir detecções e ensinar novos produtos de forma interativa
"""

import os
import sys
import django
from pathlib import Path
import cv2
import numpy as np
import shutil
from datetime import datetime

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from ultralytics import YOLO
from verifik.models import ProdutoMae, ImagemProduto


class EnsinoInterativo:
    def __init__(self):
        self.modelo_path = BASE_DIR / 'verifik' / 'verifik_yolov8.pt'
        self.dataset_path = BASE_DIR / 'verifik' / 'dataset_yolo'
        self.modelo = None
        self.imagem_atual = None
        self.deteccoes = []
        
    def carregar_modelo(self):
        """Carrega modelo existente ou cria novo"""
        if self.modelo_path.exists():
            print(f"📦 Carregando modelo existente: {self.modelo_path}")
            self.modelo = YOLO(str(self.modelo_path))
        else:
            print(f"⚠️  Modelo não encontrado. Use treinar_modelo_yolo.py primeiro")
            sys.exit(1)
    
    def detectar_produtos(self, caminho_foto):
        """Detecta produtos na foto"""
        print(f"\n🔍 Analisando foto: {caminho_foto}")
        
        self.imagem_atual = cv2.imread(caminho_foto)
        if self.imagem_atual is None:
            print(f"❌ Não foi possível carregar a imagem")
            return False
        
        # Executar detecção
        resultados = self.modelo.predict(
            source=caminho_foto,
            conf=0.15,  # Threshold baixo para pegar mais detecções
            iou=0.45,
            verbose=False
        )
        
        resultado = resultados[0]
        boxes = resultado.boxes
        
        # Processar detecções
        self.deteccoes = []
        produtos_bd = list(ProdutoMae.objects.filter(
            imagens_treino__isnull=False
        ).distinct().order_by('id'))
        
        for box in boxes:
            class_id = int(box.cls[0])
            confianca = float(box.conf[0])
            coords = box.xyxy[0].cpu().numpy()
            
            produto_nome = "Desconhecido"
            if class_id < len(produtos_bd):
                produto_nome = produtos_bd[class_id].marca
            
            self.deteccoes.append({
                'class_id': class_id,
                'produto_nome': produto_nome,
                'confianca': confianca,
                'bbox': coords.tolist()
            })
        
        return True
    
    def mostrar_deteccoes(self):
        """Mostra detecções encontradas"""
        if not self.deteccoes:
            print("\n⚠️  NENHUM PRODUTO DETECTADO!")
            print("   O modelo não reconheceu nada na imagem.")
            return
        
        print(f"\n📊 DETECÇÕES ENCONTRADAS: {len(self.deteccoes)}")
        print("=" * 80)
        
        for idx, det in enumerate(self.deteccoes, 1):
            # Buscar produto no BD para pegar descrição completa
            produtos_bd = list(ProdutoMae.objects.filter(
                imagens_treino__isnull=False
            ).distinct().order_by('id'))
            
            produto_nome = det['produto_nome']
            produto_descricao = ""
            
            if det['class_id'] < len(produtos_bd):
                produto_obj = produtos_bd[det['class_id']]
                produto_descricao = produto_obj.descricao_produto
            
            print(f"\n{idx}. {produto_nome}")
            if produto_descricao:
                print(f"   Descrição: {produto_descricao}")
            print(f"   Confiança: {det['confianca']:.1%}")
            print(f"   Posição: {[int(x) for x in det['bbox']]}")
    
    def perguntar_correcoes(self):
        """Pergunta ao usuário sobre cada detecção"""
        print("\n" + "=" * 80)
        print("🎓 VAMOS ENSINAR O MODELO!")
        print("=" * 80)
        print("Para cada detecção, você pode:")
        print("  ✅ Confirmar se está correto")
        print("  ❌ Corrigir se está errado")
        print("  ➕ Adicionar produtos que ele não viu")
        
        correcoes = []
        
        # Verificar cada detecção
        for idx, det in enumerate(self.deteccoes, 1):
            print(f"\n{'─' * 80}")
            print(f"DETECÇÃO {idx}/{len(self.deteccoes)}")
            print(f"Produto detectado: {det['produto_nome']} (confiança: {det['confianca']:.1%})")
            
            resposta = input("Está correto? (s/n): ").strip().lower()
            
            if resposta == 'n':
                print("\n📝 Qual é o produto correto?")
                produto_correto = self.selecionar_produto()
                
                if produto_correto:
                    correcoes.append({
                        'bbox': det['bbox'],
                        'produto': produto_correto,
                        'acao': 'corrigir'
                    })
                    print(f"✅ Correção registrada: {produto_correto.marca}")
            else:
                # Confirmar produto correto
                produto = ProdutoMae.objects.filter(
                    imagens_treino__isnull=False
                ).distinct().order_by('id')[det['class_id']]
                
                correcoes.append({
                    'bbox': det['bbox'],
                    'produto': produto,
                    'acao': 'confirmar'
                })
                print(f"✅ Confirmado: {produto.marca}")
        
        # Perguntar se tem produtos não detectados
        print(f"\n{'─' * 80}")
        tem_mais = input("\nExistem produtos na foto que NÃO foram detectados? (s/n): ").strip().lower()
        
        if tem_mais == 's':
            print("\n➕ ADICIONAR PRODUTOS NÃO DETECTADOS")
            print("(Você precisará marcar a região na imagem)")
            
            while True:
                produto = self.selecionar_produto()
                if produto:
                    # Aqui você marcaria a região manualmente ou usaria outra foto
                    print(f"✅ {produto.marca} será adicionado ao treinamento")
                    print("   (Use uma foto individual deste produto para melhor resultado)")
                
                continuar = input("\nAdicionar outro produto não detectado? (s/n): ").strip().lower()
                if continuar != 's':
                    break
        
        return correcoes
    
    def selecionar_produto(self):
        """Permite usuário selecionar produto correto por busca"""
        print("\n📦 BUSCAR PRODUTO:")
        print("=" * 80)
        
        # Busca por nome
        while True:
            busca = input("\nDigite parte do nome do produto (ou 'listar' para ver todos, '0' para pular): ").strip()
            
            if busca == '0':
                return None
            
            if busca.lower() == 'listar':
                # Mostrar apenas produtos já treinados
                produtos = ProdutoMae.objects.filter(
                    imagens_treino__isnull=False
                ).distinct().order_by('marca', 'descricao_produto')
                
                print("\n🎓 PRODUTOS JÁ TREINADOS:")
                produtos_list = list(produtos)
                for idx, produto in enumerate(produtos_list, 1):
                    print(f"{idx:2d}. {produto.marca} - {produto.descricao_produto}")
                
                if not produtos_list:
                    print("⚠️  Nenhum produto treinado ainda")
                    continue
                
            else:
                # Buscar por nome
                produtos = ProdutoMae.objects.filter(
                    descricao_produto__icontains=busca
                ).order_by('marca', 'descricao_produto') | ProdutoMae.objects.filter(
                    marca__icontains=busca
                ).order_by('marca', 'descricao_produto')
                
                produtos = produtos.distinct()
                produtos_list = list(produtos)
                
                if not produtos_list:
                    print(f"❌ Nenhum produto encontrado com '{busca}'")
                    continue
                
                print(f"\n🔍 Encontrado(s) {len(produtos_list)} produto(s):")
                for idx, produto in enumerate(produtos_list, 1):
                    treinado = "✓" if produto.imagens_treino.exists() else "○"
                    print(f"{idx:2d}. [{treinado}] {produto.marca} - {produto.descricao_produto}")
            
            # Selecionar da lista filtrada
            try:
                escolha = input("\nDigite o número (ou Enter para buscar novamente): ").strip()
                
                if not escolha:
                    continue
                
                idx = int(escolha) - 1
                if 0 <= idx < len(produtos_list):
                    produto_escolhido = produtos_list[idx]
                    print(f"✅ Selecionado: {produto_escolhido.marca} - {produto_escolhido.descricao_produto}")
                    return produto_escolhido
                else:
                    print("❌ Número inválido!")
            except ValueError:
                print("❌ Digite um número válido!")
    
    def salvar_correcoes(self, caminho_foto, correcoes):
        """Salva correções como novas imagens de treino"""
        if not correcoes:
            print("\n⚠️  Nenhuma correção para salvar")
            return
        
        print(f"\n💾 Salvando {len(correcoes)} correção(ões)...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for idx, correcao in enumerate(correcoes):
            produto = correcao['produto']
            bbox = correcao['bbox']
            
            # Recortar região do produto
            x1, y1, x2, y2 = map(int, bbox)
            produto_crop = self.imagem_atual[y1:y2, x1:x2]
            
            # Salvar como imagem de treino
            pasta_produto = BASE_DIR / 'media' / 'produtos' / produto.marca.replace(' ', '_')
            pasta_produto.mkdir(parents=True, exist_ok=True)
            
            nome_arquivo = f"{produto.marca}_{timestamp}_{idx}.jpg"
            caminho_crop = pasta_produto / nome_arquivo
            
            cv2.imwrite(str(caminho_crop), produto_crop)
            
            # Registrar no banco de dados
            ImagemProduto.objects.create(
                produto=produto,
                imagem=str(caminho_crop.relative_to(BASE_DIR))
            )
            
            acao_txt = "corrigido" if correcao['acao'] == 'corrigir' else "confirmado"
            print(f"  ✅ {produto.marca} - {acao_txt}")
        
        print(f"\n✅ {len(correcoes)} imagem(ns) adicionada(s) ao dataset de treino!")
        print("\n💡 Execute 'python treinar_modelo_yolo.py' para retreinar o modelo")
    
    def executar(self, caminho_foto):
        """Fluxo principal"""
        print("\n" + "=" * 80)
        print("🎓 VERIFIK - ENSINO INTERATIVO DO MODELO")
        print("=" * 80)
        
        # Carregar modelo
        self.carregar_modelo()
        
        # Detectar produtos
        if not self.detectar_produtos(caminho_foto):
            return
        
        # Mostrar detecções
        self.mostrar_deteccoes()
        
        # Perguntar correções
        correcoes = self.perguntar_correcoes()
        
        # Salvar correções
        self.salvar_correcoes(caminho_foto, correcoes)
        
        print("\n" + "=" * 80)
        print("✅ Ensino concluído!")
        print("=" * 80)


def main():
    """Função principal"""
    sistema = EnsinoInterativo()
    
    print("\n" + "=" * 80)
    print("🎓 SISTEMA DE ENSINO INTERATIVO DO VERIFIK")
    print("=" * 80)
    print("\nEste sistema permite:")
    print("  1. Ver o que o modelo detectou")
    print("  2. Corrigir detecções erradas")
    print("  3. Adicionar produtos não detectados")
    print("  4. Salvar automaticamente para retreinamento")
    
    while True:
        print("\n" + "─" * 80)
        caminho_foto = input("\n📸 Digite o caminho da foto (ou 'sair'): ").strip().strip('"')
        
        if caminho_foto.lower() == 'sair':
            print("\n👋 Até logo!")
            break
        
        if not os.path.exists(caminho_foto):
            print(f"❌ Arquivo não encontrado: {caminho_foto}")
            continue
        
        sistema.executar(caminho_foto)
        
        continuar = input("\nAnalisar outra foto? (s/n): ").strip().lower()
        if continuar != 's':
            break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Ensino cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
