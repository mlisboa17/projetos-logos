"""
VerifiK - Verificar foto e marcar produtos
Primeiro detecta automaticamente, depois permite correções manuais
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from ultralytics import YOLO
from verifik.models import ProdutoMae, ImagemProduto
import cv2
import numpy as np
from datetime import datetime


class VerificadorMarcador:
    def __init__(self):
        self.modelo = None
        self.imagem_path = None
        self.imagem_original = None
        self.deteccoes = []
        self.produtos_confirmados = []
        self.carregar_modelo()
    
    def carregar_modelo(self):
        """Carrega modelo YOLO"""
        modelo_path = BASE_DIR / 'verifik' / 'verifik_yolov8.pt'
        if modelo_path.exists():
            print("📦 Carregando modelo YOLO...")
            self.modelo = YOLO(str(modelo_path))
            print("✅ Modelo carregado!\n")
        else:
            print("⚠️  Modelo não encontrado!")
            print("   Apenas marcação manual disponível.\n")
    
    def detectar_produtos(self, imagem_path):
        """Detecta produtos automaticamente na imagem"""
        self.imagem_path = imagem_path
        self.imagem_original = cv2.imread(str(imagem_path))
        
        if self.imagem_original is None:
            print(f"❌ Não foi possível abrir: {imagem_path}")
            return False
        
        print("="*70)
        print("🔍 VERIFICANDO IMAGEM COM MODELO YOLO")
        print("="*70)
        print(f"📸 Arquivo: {Path(imagem_path).name}\n")
        
        if not self.modelo:
            print("⚠️  Modelo não disponível - indo direto para marcação manual...\n")
            return True  # Continua para marcação manual
        
        # Executar detecção
        print("⏳ Detectando produtos...")
        resultados = self.modelo.predict(
            source=str(imagem_path),
            conf=0.15,
            iou=0.45,
            verbose=False
        )
        
        resultado = resultados[0]
        boxes = resultado.boxes
        
        # Mapear classes para produtos
        produtos_bd = list(ProdutoMae.objects.filter(
            imagens_treino__isnull=False
        ).distinct().order_by('id'))
        
        # Processar detecções
        self.deteccoes = []
        for box in boxes:
            class_id = int(box.cls[0])
            confianca = float(box.conf[0])
            coords = box.xyxy[0].cpu().numpy()
            
            if class_id < len(produtos_bd):
                produto = produtos_bd[class_id]
                self.deteccoes.append({
                    'produto': produto,
                    'confianca': confianca,
                    'bbox': coords.tolist(),
                    'confirmado': False
                })
        
        # Mostrar resultados
        if self.deteccoes:
            print(f"\n✅ Detectados {len(self.deteccoes)} produto(s):\n")
            for i, det in enumerate(self.deteccoes, 1):
                marca = det['produto'].marca
                desc = det['produto'].descricao_produto
                conf = det['confianca']
                print(f"   {i}. {marca} - {desc}")
                print(f"      Confiança: {conf:.1%}")
        else:
            print("\n❌ Nenhum produto detectado automaticamente")
        
        return True
    
    def revisar_deteccoes(self):
        """Permite revisar e confirmar/corrigir detecções"""
        if not self.deteccoes:
            print("\n📝 Nenhum produto detectado. Indo para marcação manual...\n")
            return False
        
        print("\n" + "="*70)
        print("🔍 REVISAR DETECÇÕES")
        print("="*70)
        print("\nOpções:")
        print("  s - Aceitar TODAS as detecções")
        print("  r - Revisar UMA POR UMA (confirmar ou corrigir)")
        print("  m - Ignorar tudo e marcar MANUALMENTE")
        print("  n - Cancelar")
        
        escolha = input("\n▶️  Escolha: ").strip().lower()
        
        if escolha == 's':
            # Aceitar todas
            print("\n✅ Aceitando todas as detecções...")
            for det in self.deteccoes:
                det['confirmado'] = True
                self.produtos_confirmados.append(det)
            return True
        
        elif escolha == 'r':
            # Revisar uma por uma
            return self.revisar_uma_por_uma()
        
        elif escolha == 'm':
            # Marcação manual
            print("\n📝 Indo para marcação manual...")
            return False
        
        else:
            print("\n❌ Cancelado")
            return None
    
    def revisar_uma_por_uma(self):
        """Revisa cada detecção individualmente"""
        print("\n" + "="*70)
        print("📋 REVISÃO INDIVIDUAL")
        print("="*70)
        
        for i, det in enumerate(self.deteccoes, 1):
            print(f"\n🔍 Detecção {i}/{len(self.deteccoes)}:")
            print(f"   Produto: {det['produto'].marca} - {det['produto'].descricao_produto}")
            print(f"   Confiança: {det['confianca']:.1%}")
            
            print("\n   Opções:")
            print("   ✓ - Confirmar (produto correto)")
            print("   x - Ignorar (produto errado)")
            print("   c - Corrigir (escolher outro produto)")
            
            escolha = input("\n   ▶️  Escolha: ").strip().lower()
            
            if escolha == '✓' or escolha == 's':
                det['confirmado'] = True
                self.produtos_confirmados.append(det)
                print("   ✅ Confirmado!")
            
            elif escolha == 'c':
                # Corrigir produto
                produto_correto = self.buscar_produto()
                if produto_correto:
                    det['produto'] = produto_correto
                    det['confirmado'] = True
                    self.produtos_confirmados.append(det)
                    print("   ✅ Corrigido e confirmado!")
                else:
                    print("   ❌ Cancelado")
            
            else:
                print("   ❌ Ignorado")
        
        if self.produtos_confirmados:
            print(f"\n✅ {len(self.produtos_confirmados)} produto(s) confirmado(s)")
            return True
        else:
            print("\n⚠️  Nenhum produto confirmado")
            return False
    
    def buscar_produto(self):
        """Busca produto por nome"""
        while True:
            busca = input("\n   Digite parte do nome (ou '0' para cancelar): ").strip()
            
            if busca == '0':
                return None
            
            # Buscar
            produtos = ProdutoMae.objects.filter(
                descricao_produto__icontains=busca
            ).order_by('marca', 'descricao_produto') | ProdutoMae.objects.filter(
                marca__icontains=busca
            ).order_by('marca', 'descricao_produto')
            
            produtos = produtos.distinct()
            produtos_list = list(produtos)
            
            if not produtos_list:
                print(f"   ❌ Nenhum produto encontrado com '{busca}'")
                continue
            
            print(f"\n   🔍 Encontrado(s) {len(produtos_list)} produto(s):")
            for idx, produto in enumerate(produtos_list, 1):
                treinado = "✓" if produto.imagens_treino.exists() else "○"
                print(f"   {idx:2d}. [{treinado}] {produto.marca} - {produto.descricao_produto}")
            
            try:
                escolha = input("\n   Número (Enter=buscar novamente): ").strip()
                
                if not escolha:
                    continue
                
                idx = int(escolha) - 1
                if 0 <= idx < len(produtos_list):
                    produto_selecionado = produtos_list[idx]
                    
                    # Confirmação
                    print(f"\n   📦 {produto_selecionado.marca} - {produto_selecionado.descricao_produto}")
                    confirmacao = input("   ✅ Confirmar? (s/n): ").strip().lower()
                    
                    if confirmacao == 's':
                        return produto_selecionado
                    else:
                        print("   ❌ Cancelado")
                        continue
                else:
                    print("   ❌ Número inválido!")
            except ValueError:
                print("   ❌ Digite um número válido!")
    
    def salvar_produtos(self):
        """Salva produtos confirmados no banco"""
        if not self.produtos_confirmados:
            print("\n⚠️  Nenhum produto para salvar")
            return
        
        print("\n" + "="*70)
        print("💾 SALVANDO PRODUTOS")
        print("="*70)
        
        salvos = 0
        for det in self.produtos_confirmados:
            try:
                # Recortar imagem
                x1, y1, x2, y2 = map(int, det['bbox'])
                produto_img = self.imagem_original[y1:y2, x1:x2]
                
                # Criar nome do arquivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                marca_slug = det['produto'].marca.replace(' ', '_')
                filename = f"{marca_slug}_{timestamp}_{salvos}.jpg"
                
                # Criar diretório
                save_dir = BASE_DIR / 'media' / 'produtos' / marca_slug
                save_dir.mkdir(parents=True, exist_ok=True)
                
                # Salvar imagem
                save_path = save_dir / filename
                cv2.imwrite(str(save_path), produto_img)
                
                # Salvar no banco
                ImagemProduto.objects.create(
                    produto=det['produto'],
                    imagem=f'produtos/{marca_slug}/{filename}',
                    descricao=f'Verificação automática - conf: {det["confianca"]:.1%}'
                )
                
                salvos += 1
                print(f"   ✅ {det['produto'].marca} - {det['produto'].descricao_produto}")
                
            except Exception as e:
                print(f"   ❌ Erro ao salvar: {e}")
        
        print(f"\n✅ {salvos} produto(s) salvos com sucesso!")
    
    def marcar_manualmente(self):
        """Abre interface de marcação manual"""
        print("\n" + "="*70)
        print("📝 MARCAÇÃO MANUAL")
        print("="*70)
        print("Abrindo ferramenta de marcação manual...\n")
        
        # Importar e executar marcador manual
        from marcar_produtos_manual import MarcadorProdutos
        
        marcador = MarcadorProdutos()
        if marcador.carregar_imagem(str(self.imagem_path)):
            if marcador.marcar_produtos():
                marcador.salvar_marcacoes()


def main():
    """Função principal"""
    print("\n" + "="*70)
    print("🎯 VERIFIK - VERIFICAR E MARCAR PRODUTOS")
    print("="*70)
    
    # Solicitar imagem
    caminho = input("\n📸 Caminho da imagem: ").strip().strip('"')
    
    if not caminho or not Path(caminho).exists():
        print("❌ Arquivo não encontrado!")
        return
    
    # Criar verificador
    verificador = VerificadorMarcador()
    
    # 1. Detectar produtos
    if not verificador.detectar_produtos(caminho):
        return
    
    # 2. Revisar detecções
    if verificador.deteccoes:
        resultado = verificador.revisar_deteccoes()
        
        if resultado is None:
            # Cancelado
            return
        
        if resultado:
            # Produtos confirmados - salvar
            verificador.salvar_produtos()
            
            # Perguntar se quer marcar mais produtos manualmente
            mais = input("\n▶️  Marcar mais produtos manualmente? (s/n): ").strip().lower()
            if mais == 's':
                verificador.marcar_manualmente()
            return
    
    # 3. Marcação manual (se não detectou nada ou escolheu manual)
    verificador.marcar_manualmente()


if __name__ == '__main__':
    main()
