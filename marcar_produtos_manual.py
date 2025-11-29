"""
VerifiK - Sistema de Marcação Manual de Produtos
Permite marcar produtos na foto clicando e arrastando
"""

import os
import sys
import django
from pathlib import Path
import cv2
import numpy as np

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from datetime import datetime
from ultralytics import YOLO


class MarcadorProdutos:
    def __init__(self):
        self.imagem_original = None
        self.imagem_exibida = None
        self.imagem_path = None
        self.produtos_marcados = []
        self.ponto_inicial = None
        self.ponto_final = None
        self.desenhando = False
        self.escala = 1.0
        self.modelo = None
        self.carregar_modelo()
    
    def carregar_modelo(self):
        """Carrega modelo YOLO para detecção automática"""
        modelo_path = BASE_DIR / 'verifik' / 'verifik_yolov8.pt'
        if modelo_path.exists():
            print("📦 Carregando modelo YOLO...")
            self.modelo = YOLO(str(modelo_path))
            print("✅ Modelo carregado!")
        else:
            print("⚠️  Modelo não encontrado - apenas marcação manual disponível")
    
    def detectar_automatico(self):
        """Tenta detectar produtos automaticamente"""
        if not self.modelo:
            return
        
        print("\n🔍 Detectando produtos automaticamente...")
        
        # Executar detecção
        resultados = self.modelo.predict(
            source=self.imagem_path,
            conf=0.15,
            iou=0.45,
            verbose=False
        )
        
        resultado = resultados[0]
        boxes = resultado.boxes
        
        # Processar detecções
        produtos_bd = list(ProdutoMae.objects.filter(
            imagens_treino__isnull=False
        ).distinct().order_by('id'))
        
        deteccoes = []
        for box in boxes:
            class_id = int(box.cls[0])
            confianca = float(box.conf[0])
            coords = box.xyxy[0].cpu().numpy()
            
            if class_id < len(produtos_bd):
                produto = produtos_bd[class_id]
                deteccoes.append({
                    'produto': produto,
                    'confianca': confianca,
                    'bbox': coords.tolist()
                })
        
        if deteccoes:
            print(f"✅ Detectados {len(deteccoes)} produto(s) automaticamente:")
            for det in deteccoes:
                print(f"   - {det['produto'].marca} ({det['confianca']:.1%})")
            
            # Perguntar se quer usar detecções automáticas
            resposta = input("\nUsar estas detecções? (s=sim, n=marcar manual, c=corrigir): ").strip().lower()
            
            if resposta == 's':
                # Adicionar todas as detecções
                for det in deteccoes:
                    x1, y1, x2, y2 = map(int, det['bbox'])
                    
                    # Converter para display
                    x1_display = int(x1 * self.escala)
                    y1_display = int(y1 * self.escala)
                    x2_display = int(x2 * self.escala)
                    y2_display = int(y2 * self.escala)
                    
                    self.produtos_marcados.append({
                        'produto': det['produto'],
                        'bbox': [x1, y1, x2, y2],
                        'bbox_display': [x1_display, y1_display, x2_display, y2_display]
                    })
                
                print(f"✅ {len(deteccoes)} produtos adicionados!")
                self.atualizar_visualizacao()
                
            elif resposta == 'c':
                # Modo correção - mostrar cada detecção
                for idx, det in enumerate(deteccoes, 1):
                    print(f"\n─── Detecção {idx}/{len(deteccoes)} ───")
                    print(f"Produto: {det['produto'].marca} - {det['produto'].descricao_produto}")
                    print(f"Confiança: {det['confianca']:.1%}")
                    
                    confirma = input("Correto? (s=sim, n=escolher outro, p=pular): ").strip().lower()
                    
                    if confirma == 's':
                        produto = det['produto']
                    elif confirma == 'n':
                        produto = self.selecionar_produto()
                        if not produto:
                            continue
                    else:
                        continue
                    
                    x1, y1, x2, y2 = map(int, det['bbox'])
                    x1_display = int(x1 * self.escala)
                    y1_display = int(y1 * self.escala)
                    x2_display = int(x2 * self.escala)
                    y2_display = int(y2 * self.escala)
                    
                    self.produtos_marcados.append({
                        'produto': produto,
                        'bbox': [x1, y1, x2, y2],
                        'bbox_display': [x1_display, y1_display, x2_display, y2_display]
                    })
                
                print(f"✅ {len(self.produtos_marcados)} produtos confirmados!")
                self.atualizar_visualizacao()
        else:
            print("⚠️  Nenhum produto detectado automaticamente")
            print("   Você pode marcar manualmente")
        
    def mouse_callback(self, event, x, y, flags, param):
        """Callback para eventos do mouse"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Início do arrasto
            self.ponto_inicial = (x, y)
            self.desenhando = True
            
        elif event == cv2.EVENT_MOUSEMOVE:
            # Durante o arrasto
            if self.desenhando:
                self.ponto_final = (x, y)
                # Redesenhar imagem com retângulo temporário
                self.atualizar_visualizacao()
                
        elif event == cv2.EVENT_LBUTTONUP:
            # Fim do arrasto
            self.ponto_final = (x, y)
            self.desenhando = False
            
            if self.ponto_inicial and self.ponto_final:
                # Garantir que x1 < x2 e y1 < y2
                x1 = min(self.ponto_inicial[0], self.ponto_final[0])
                y1 = min(self.ponto_inicial[1], self.ponto_final[1])
                x2 = max(self.ponto_inicial[0], self.ponto_final[0])
                y2 = max(self.ponto_inicial[1], self.ponto_final[1])
                
                # Verificar se não é muito pequeno
                if (x2 - x1) > 20 and (y2 - y1) > 20:
                    # Converter para coordenadas da imagem original
                    x1_orig = int(x1 / self.escala)
                    y1_orig = int(y1 / self.escala)
                    x2_orig = int(x2 / self.escala)
                    y2_orig = int(y2 / self.escala)
                    
                    # Selecionar produto
                    produto = self.selecionar_produto()
                    
                    if produto:
                        self.produtos_marcados.append({
                            'produto': produto,
                            'bbox': [x1_orig, y1_orig, x2_orig, y2_orig],
                            'bbox_display': [x1, y1, x2, y2]
                        })
                        print(f"✅ Marcado: {produto.marca} - {produto.descricao_produto}")
                    
                self.ponto_inicial = None
                self.ponto_final = None
                self.atualizar_visualizacao()
    
    def atualizar_visualizacao(self):
        """Atualiza a imagem exibida com marcações"""
        self.imagem_exibida = self.imagem_display.copy()
        
        # Desenhar produtos já marcados
        for idx, marcacao in enumerate(self.produtos_marcados, 1):
            x1, y1, x2, y2 = marcacao['bbox_display']
            cv2.rectangle(self.imagem_exibida, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Label com número
            label = f"{idx}. {marcacao['produto'].marca}"
            cv2.putText(self.imagem_exibida, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Desenhar retângulo temporário durante arrasto
        if self.desenhando and self.ponto_inicial and self.ponto_final:
            cv2.rectangle(self.imagem_exibida, self.ponto_inicial, self.ponto_final,
                         (255, 0, 0), 2)
        
        cv2.imshow('Marcar Produtos - ESC: Sair | ENTER: Salvar', self.imagem_exibida)
    
    def selecionar_produto(self):
        """Permite usuário selecionar produto por busca"""
        print("\n" + "─" * 80)
        print("📦 BUSCAR PRODUTO:")
        
        while True:
            busca = input("Digite parte do nome (ou '0' para cancelar): ").strip()
            
            if busca == '0':
                return None
            
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
            
            # Selecionar da lista
            try:
                escolha = input("\nNúmero (Enter=buscar novamente): ").strip()
                
                if not escolha:
                    continue
                
                idx = int(escolha) - 1
                if 0 <= idx < len(produtos_list):
                    produto_selecionado = produtos_list[idx]
                    
                    # CONFIRMAÇÃO - mostrar produto escolhido
                    print("\n" + "─" * 80)
                    print(f"📦 PRODUTO SELECIONADO:")
                    print(f"   Marca: {produto_selecionado.marca}")
                    print(f"   Descrição: {produto_selecionado.descricao_produto}")
                    treinado = produto_selecionado.imagens_treino.count()
                    print(f"   Imagens de treino: {treinado}")
                    print("─" * 80)
                    
                    confirmacao = input("✅ Confirmar este produto? (s/n): ").strip().lower()
                    
                    if confirmacao == 's':
                        return produto_selecionado
                    else:
                        print("❌ Cancelado. Busque novamente.")
                        continue
                else:
                    print("❌ Número inválido!")
            except ValueError:
                print("❌ Digite um número válido!")
    
    def carregar_imagem(self, caminho):
        """Carrega e prepara imagem para marcação"""
        self.imagem_path = caminho
        self.imagem_original = cv2.imread(caminho)
        
        if self.imagem_original is None:
            print(f"❌ Não foi possível carregar: {caminho}")
            return False
        
        # Redimensionar se muito grande (para caber na tela)
        height, width = self.imagem_original.shape[:2]
        max_height = 800
        
        if height > max_height:
            self.escala = max_height / height
            new_width = int(width * self.escala)
            new_height = max_height
            self.imagem_display = cv2.resize(self.imagem_original, (new_width, new_height))
        else:
            self.escala = 1.0
            self.imagem_display = self.imagem_original.copy()
        
        self.imagem_exibida = self.imagem_display.copy()
        
        print(f"\n✅ Imagem carregada: {width}x{height}px")
        if self.escala != 1.0:
            print(f"   Exibindo em escala: {self.escala:.2f}x")
        
        return True
    
    def marcar_produtos(self):
        """Interface principal para marcação"""
        # Tentar detecção automática primeiro
        if self.modelo:
            self.detectar_automatico()
        
        print("\n" + "=" * 80)
        print("🎯 MARCAÇÃO MANUAL (se necessário):")
        print("=" * 80)
        print("1. Clique e arraste para adicionar produtos não detectados")
        print("2. Selecione o produto da lista")
        print("3. Repita para todos os produtos faltantes")
        print("4. Pressione ENTER para salvar")
        print("5. Pressione ESC para cancelar")
        print("=" * 80)
        
        cv2.namedWindow('Marcar Produtos - ESC: Sair | ENTER: Salvar')
        cv2.setMouseCallback('Marcar Produtos - ESC: Sair | ENTER: Salvar', self.mouse_callback)
        
        self.atualizar_visualizacao()
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print("\n❌ Marcação cancelada")
                cv2.destroyAllWindows()
                return False
            
            elif key == 13:  # ENTER
                if self.produtos_marcados:
                    cv2.destroyAllWindows()
                    return True
                else:
                    print("\n⚠️  Marque pelo menos um produto antes de salvar!")
        
        cv2.destroyAllWindows()
        return False
    
    def salvar_marcacoes(self):
        """Salva produtos marcados como imagens de treino"""
        if not self.produtos_marcados:
            print("\n⚠️  Nenhuma marcação para salvar")
            return
        
        print(f"\n💾 Salvando {len(self.produtos_marcados)} marcação(ões)...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for idx, marcacao in enumerate(self.produtos_marcados):
            produto = marcacao['produto']
            x1, y1, x2, y2 = marcacao['bbox']
            
            # Recortar produto da imagem original
            produto_crop = self.imagem_original[y1:y2, x1:x2]
            
            # Salvar
            pasta_produto = BASE_DIR / 'media' / 'produtos' / produto.marca.replace(' ', '_')
            pasta_produto.mkdir(parents=True, exist_ok=True)
            
            nome_arquivo = f"{produto.marca}_{timestamp}_{idx}.jpg"
            caminho_crop = pasta_produto / nome_arquivo
            
            cv2.imwrite(str(caminho_crop), produto_crop)
            
            # Registrar no banco
            ImagemProduto.objects.create(
                produto=produto,
                imagem=str(caminho_crop.relative_to(BASE_DIR)),
                descricao=f"Marcação manual - {timestamp}"
            )
            
            print(f"  ✅ {produto.marca} - {produto.descricao_produto}")
        
        print(f"\n✅ {len(self.produtos_marcados)} imagem(ns) adicionada(s) ao dataset!")
        print("💡 Execute 'python treinar_modelo_yolo.py' para retreinar")


def main():
    """Função principal"""
    print("\n" + "=" * 80)
    print("🎯 VERIFIK - MARCAÇÃO MANUAL DE PRODUTOS")
    print("=" * 80)
    
    marcador = MarcadorProdutos()
    
    while True:
        print("\n" + "─" * 80)
        caminho = input("📸 Caminho da foto (ou 'sair'): ").strip().strip('"')
        
        if caminho.lower() == 'sair':
            print("\n👋 Até logo!")
            break
        
        if not os.path.exists(caminho):
            print(f"❌ Arquivo não encontrado: {caminho}")
            continue
        
        if not marcador.carregar_imagem(caminho):
            continue
        
        if marcador.marcar_produtos():
            marcador.salvar_marcacoes()
        
        # Resetar para próxima foto
        marcador.produtos_marcados = []
        
        continuar = input("\nMarcar outra foto? (s/n): ").strip().lower()
        if continuar != 's':
            break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Marcação cancelada pelo usuário")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        cv2.destroyAllWindows()
