"""
Sistema de Treinamento com Validação de Quantidade
Autor: Sistema Verifik
Data: 2025-11-24

Fluxo:
1. Usuário informa quantos produtos existem na foto
2. Sistema detecta e mostra os produtos encontrados
3. Usuário valida se está correto ou corrige manualmente
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProduto
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image


class TreinadorComValidacao:
    def __init__(self, modelo_path='verifik/verifik_yolov8.pt'):
        self.modelo_path = modelo_path
        self.modelo = None
        self.imagem = None
        self.imagem_original = None
        self.deteccoes = []
        self.produtos_marcados = []
        self.escala = 1.0
        
    def carregar_modelo(self):
        """Carrega o modelo YOLO"""
        print("\n📦 Carregando modelo YOLO...")
        self.modelo = YOLO(self.modelo_path)
        print("✅ Modelo carregado!\n")
        
    def carregar_imagem(self, caminho_imagem):
        """Carrega a imagem"""
        if not os.path.exists(caminho_imagem):
            print(f"❌ Arquivo não encontrado: {caminho_imagem}")
            return False
            
        self.imagem_original = cv2.imread(caminho_imagem)
        if self.imagem_original is None:
            print(f"❌ Erro ao carregar imagem: {caminho_imagem}")
            return False
            
        altura, largura = self.imagem_original.shape[:2]
        print(f"✅ Imagem carregada: {largura}x{altura}px")
        
        # Calcular escala para exibição
        max_display = 800
        if max(largura, altura) > max_display:
            self.escala = max_display / max(largura, altura)
            print(f"   Exibindo em escala: {self.escala:.2f}x\n")
        
        return True
        
    def detectar_produtos(self, qtd_esperada=None):
        """Detecta produtos na imagem usando YOLO com múltiplos níveis de confiança"""
        print("🔍 Detectando produtos automaticamente...")
        
        # Níveis de confiança progressivos
        niveis_conf = [0.25, 0.20, 0.15, 0.10, 0.05]
        
        self.deteccoes = []
        
        for conf_threshold in niveis_conf:
            results = self.modelo.predict(
                source=self.imagem_original,
                conf=conf_threshold,
                verbose=False
            )
            
            deteccoes_temp = []
            
            if len(results) > 0 and len(results[0].boxes) > 0:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confianca = float(box.conf[0])
                    classe_id = int(box.cls[0])
                    classe_nome = results[0].names[classe_id]
                    
                    deteccoes_temp.append({
                        'bbox': (x1, y1, x2, y2),
                        'confianca': confianca,
                        'classe': classe_nome
                    })
            
            # Remover duplicatas (mesma região)
            self.deteccoes = self._remover_duplicatas(deteccoes_temp)
            
            print(f"   Tentativa com confiança {conf_threshold*100:.0f}%: {len(self.deteccoes)} produto(s)")
            
            # Se encontrou a quantidade esperada, parar
            if qtd_esperada and len(self.deteccoes) >= qtd_esperada:
                print(f"   ✅ Encontrou {len(self.deteccoes)} produto(s)!")
                break
                
            # Se não há quantidade esperada, usar primeira tentativa com resultados
            if not qtd_esperada and len(self.deteccoes) > 0:
                break
        
        print(f"\n✅ Total detectado: {len(self.deteccoes)} produto(s)\n")
        return len(self.deteccoes)
    
    def _remover_duplicatas(self, deteccoes):
        """Remove detecções duplicadas (mesma região)"""
        if not deteccoes:
            return []
        
        # Ordenar por confiança (maior primeiro)
        deteccoes_ordenadas = sorted(deteccoes, key=lambda x: x['confianca'], reverse=True)
        
        deteccoes_unicas = []
        
        for det in deteccoes_ordenadas:
            x1, y1, x2, y2 = det['bbox']
            duplicata = False
            
            # Verificar se já existe uma detecção na mesma região
            for det_existente in deteccoes_unicas:
                ex1, ey1, ex2, ey2 = det_existente['bbox']
                
                # Calcular IoU (Intersection over Union)
                inter_x1 = max(x1, ex1)
                inter_y1 = max(y1, ey1)
                inter_x2 = min(x2, ex2)
                inter_y2 = min(y2, ey2)
                
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                    area1 = (x2 - x1) * (y2 - y1)
                    area2 = (ex2 - ex1) * (ey2 - ey1)
                    union_area = area1 + area2 - inter_area
                    iou = inter_area / union_area if union_area > 0 else 0
                    
                    # Se IoU > 50%, considerar duplicata
                    if iou > 0.5:
                        duplicata = True
                        break
            
            if not duplicata:
                deteccoes_unicas.append(det)
        
        return deteccoes_unicas
        
    def mostrar_deteccoes(self):
        """Mostra as detecções encontradas"""
        if not self.deteccoes:
            print("⚠️  Nenhum produto detectado")
            return
            
        print("📋 PRODUTOS DETECTADOS:")
        print("=" * 80)
        for i, det in enumerate(self.deteccoes, 1):
            classe_partes = det['classe'].split(' ', 1)
            marca = classe_partes[0]
            descricao = classe_partes[1] if len(classe_partes) > 1 else ''
            
            print(f"\n   {i}. {marca} - {descricao}")
            print(f"      Confiança: {det['confianca']*100:.1f}%")
            
        print("\n" + "=" * 80)
        
    def visualizar_deteccoes(self):
        """Mostra a imagem com as detecções marcadas"""
        if not self.deteccoes:
            return
            
        # Criar cópia da imagem
        img_display = self.imagem_original.copy()
        
        # Desenhar retângulos
        for i, det in enumerate(self.deteccoes, 1):
            x1, y1, x2, y2 = det['bbox']
            cor = (0, 255, 0)  # Verde
            
            # Retângulo
            cv2.rectangle(img_display, (x1, y1), (x2, y2), cor, 2)
            
            # Número
            cv2.putText(img_display, str(i), (x1+5, y1+25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
            
        # Redimensionar se necessário
        if self.escala < 1.0:
            altura, largura = img_display.shape[:2]
            nova_largura = int(largura * self.escala)
            nova_altura = int(altura * self.escala)
            img_display = cv2.resize(img_display, (nova_largura, nova_altura))
            
        # Mostrar
        cv2.imshow('Detecções - Pressione ESC para fechar', img_display)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    def buscar_produto(self, termo_busca=''):
        """Busca produtos no banco de dados"""
        if termo_busca:
            produtos = ProdutoMae.objects.filter(
                descricao_produto__icontains=termo_busca
            ) | ProdutoMae.objects.filter(
                marca__icontains=termo_busca
            )
        else:
            produtos = ProdutoMae.objects.all()
            
        return produtos.order_by('marca', 'descricao_produto')
        
    def selecionar_produto_manual(self):
        """Interface para seleção manual de produto"""
        print("\n" + "─" * 80)
        print("📦 BUSCAR PRODUTO:")
        
        termo = input("Digite parte do nome (ou '0' para cancelar): ").strip()
        
        if termo == '0':
            return None
            
        produtos = self.buscar_produto(termo)
        
        if not produtos.exists():
            print("❌ Nenhum produto encontrado")
            return self.selecionar_produto_manual()
            
        # Mostrar opções
        print(f"\n🔍 Encontrado(s) {produtos.count()} produto(s):")
        produtos_list = list(produtos[:20])  # Limitar a 20
        
        for i, prod in enumerate(produtos_list, 1):
            # Verificar se tem imagens de treino
            num_imgs = ImagemProduto.objects.filter(produto=prod).count()
            indicador = "[✓]" if num_imgs > 0 else "[○]"
            print(f" {i:2}. {indicador} {prod.marca} - {prod.descricao_produto}")
            
        # Selecionar
        try:
            escolha = input("\nNúmero (Enter=buscar novamente): ").strip()
            
            if not escolha:
                return self.selecionar_produto_manual()
                
            idx = int(escolha) - 1
            if 0 <= idx < len(produtos_list):
                produto = produtos_list[idx]
                
                # Mostrar informações
                num_imgs = ImagemProduto.objects.filter(produto=produto).count()
                print("\n" + "─" * 80)
                print("📦 PRODUTO SELECIONADO:")
                print(f"   Marca: {produto.marca}")
                print(f"   Descrição: {produto.descricao_produto}")
                print(f"   Imagens de treino: {num_imgs}")
                print("─" * 80)
                
                confirmar = input("✅ Confirmar este produto? (s/n): ").strip().lower()
                if confirmar == 's':
                    return produto
                    
        except (ValueError, IndexError):
            print("❌ Opção inválida")
            
        return self.selecionar_produto_manual()
        
    def marcar_manual_com_bbox(self, qtd_esperada):
        """Interface para marcação manual com desenho de bbox"""
        print("\n" + "=" * 80)
        print("📝 MARCAÇÃO MANUAL COM REGIÕES")
        print("=" * 80)
        print(f"Você precisa marcar {qtd_esperada} região(ões) na imagem")
        print()
        print("🖱️  INSTRUÇÕES:")
        print("   1. Clique e arraste para desenhar um retângulo em cada produto")
        print("   2. Pressione ENTER para salvar a marcação")
        print("   3. Repita até marcar todos os produtos")
        print("   4. Pressione ESC para cancelar")
        print("=" * 80)
        
        self.produtos_marcados = []
        bboxes_manuais = []
        
        # Preparar imagem para desenho
        img_trabalho = self.imagem_original.copy()
        if self.escala < 1.0:
            altura, largura = img_trabalho.shape[:2]
            nova_largura = int(largura * self.escala)
            nova_altura = int(altura * self.escala)
            img_display = cv2.resize(img_trabalho, (nova_largura, nova_altura))
        else:
            img_display = img_trabalho.copy()
        
        # Variáveis para desenho
        desenho = {'inicio': None, 'fim': None, 'desenhando': False}
        bboxes_temp = []
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal desenho, bboxes_temp, img_display
            
            # Ajustar coordenadas pela escala
            x_real = int(x / self.escala) if self.escala < 1.0 else x
            y_real = int(y / self.escala) if self.escala < 1.0 else y
            
            if event == cv2.EVENT_LBUTTONDOWN:
                desenho['inicio'] = (x_real, y_real)
                desenho['desenhando'] = True
                
            elif event == cv2.EVENT_MOUSEMOVE and desenho['desenhando']:
                desenho['fim'] = (x_real, y_real)
                
            elif event == cv2.EVENT_LBUTTONUP:
                desenho['fim'] = (x_real, y_real)
                desenho['desenhando'] = False
                
                if desenho['inicio'] and desenho['fim']:
                    x1 = min(desenho['inicio'][0], desenho['fim'][0])
                    y1 = min(desenho['inicio'][1], desenho['fim'][1])
                    x2 = max(desenho['inicio'][0], desenho['fim'][0])
                    y2 = max(desenho['inicio'][1], desenho['fim'][1])
                    
                    # Validar tamanho mínimo
                    if (x2 - x1) > 20 and (y2 - y1) > 20:
                        bboxes_temp.append((x1, y1, x2, y2))
                        print(f"   ✅ Região {len(bboxes_temp)} marcada")
                        
                desenho['inicio'] = None
                desenho['fim'] = None
        
        window_name = f'Marque {qtd_esperada} produto(s) - ENTER=salvar, ESC=cancelar'
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, mouse_callback)
        
        while True:
            # Criar cópia para exibição
            img_temp = img_trabalho.copy()
            
            # Desenhar bboxes já salvas
            for i, bbox in enumerate(bboxes_temp):
                x1, y1, x2, y2 = bbox
                cv2.rectangle(img_temp, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img_temp, str(i+1), (x1+5, y1+25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Desenhar bbox sendo criada
            if desenho['desenhando'] and desenho['inicio'] and desenho['fim']:
                x1, y1 = desenho['inicio']
                x2, y2 = desenho['fim']
                cv2.rectangle(img_temp, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Adicionar contador
            texto = f"Marcadas: {len(bboxes_temp)}/{qtd_esperada}"
            cv2.putText(img_temp, texto, (10, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            
            # Redimensionar se necessário
            if self.escala < 1.0:
                altura, largura = img_temp.shape[:2]
                nova_largura = int(largura * self.escala)
                nova_altura = int(altura * self.escala)
                img_show = cv2.resize(img_temp, (nova_largura, nova_altura))
            else:
                img_show = img_temp
            
            cv2.imshow(window_name, img_show)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 13:  # ENTER
                if len(bboxes_temp) == qtd_esperada:
                    break
                else:
                    print(f"   ⚠️  Você marcou {len(bboxes_temp)} região(ões), precisa marcar {qtd_esperada}")
                    
            elif key == 27:  # ESC
                print("\n❌ Cancelado")
                cv2.destroyAllWindows()
                return
        
        cv2.destroyAllWindows()
        
        # Para cada bbox, pedir qual produto é
        print(f"\n✅ {len(bboxes_temp)} região(ões) marcada(s)!")
        print("\nAgora identifique cada produto:\n")
        
        for i, bbox in enumerate(bboxes_temp):
            print(f"\n{'='*80}")
            print(f"🔍 REGIÃO {i+1}/{len(bboxes_temp)}")
            print(f"{'='*80}")
            
            produto = self.selecionar_produto_manual()
            
            if produto is None:
                print("   ❌ Região ignorada")
                continue
            
            self.produtos_marcados.append(produto)
            
            # Criar detecção manual
            det = {
                'bbox': bbox,
                'confianca': 1.0,  # Marcação manual = 100%
                'classe': f"{produto.marca} {produto.descricao_produto}",
                'produto': produto,
                'indice': i
            }
            self.deteccoes.append(det)
            
            print(f"   ✅ Região {i+1} = {produto.marca} - {produto.descricao_produto}")
        
        print(f"\n✅ Total marcado: {len(self.produtos_marcados)} produto(s)")
        
    def mostrar_bbox_especifica(self, indice_deteccao):
        """Mostra apenas uma bbox específica na imagem"""
        if indice_deteccao >= len(self.deteccoes):
            return
            
        # Criar cópia da imagem
        img_display = self.imagem_original.copy()
        
        # Desenhar TODAS as detecções em cinza claro
        for j, det_other in enumerate(self.deteccoes):
            x1, y1, x2, y2 = det_other['bbox']
            cv2.rectangle(img_display, (x1, y1), (x2, y2), (200, 200, 200), 1)
            cv2.putText(img_display, str(j+1), (x1+5, y1+25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Destacar a detecção atual em VERDE BRILHANTE
        det = self.deteccoes[indice_deteccao]
        x1, y1, x2, y2 = det['bbox']
        cor = (0, 255, 0)  # Verde
        
        # Retângulo grosso
        cv2.rectangle(img_display, (x1, y1), (x2, y2), cor, 4)
        
        # Número grande
        cv2.putText(img_display, str(indice_deteccao+1), (x1+5, y1+35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, cor, 3)
        
        # Adicionar texto "ESTA DETECÇÃO" no topo
        cv2.putText(img_display, f"DETECCAO #{indice_deteccao+1}", (10, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # Redimensionar se necessário
        if self.escala < 1.0:
            altura, largura = img_display.shape[:2]
            nova_largura = int(largura * self.escala)
            nova_altura = int(altura * self.escala)
            img_display = cv2.resize(img_display, (nova_largura, nova_altura))
            
        # Mostrar
        window_name = f'Detecção #{indice_deteccao+1} - Pressione qualquer tecla para fechar'
        cv2.imshow(window_name, img_display)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def corrigir_deteccoes(self):
        """Permite corrigir as detecções manualmente"""
        print("\n" + "=" * 80)
        print("🔧 CORRIGIR DETECÇÕES")
        print("=" * 80)
        print()
        
        self.produtos_marcados = []
        
        for i, det in enumerate(self.deteccoes, 1):
            classe_partes = det['classe'].split(' ', 1)
            marca = classe_partes[0]
            descricao = classe_partes[1] if len(classe_partes) > 1 else ''
            
            print(f"\n🔍 Detecção {i}/{len(self.deteccoes)}:")
            print(f"   Detectado: {marca} - {descricao}")
            print(f"   Confiança: {det['confianca']*100:.1f}%")
            print()
            print("   Opções:")
            print("   ✓ - Confirmar (está correto)")
            print("   x - Ignorar (está errado)")
            print("   v - VER (mostrar esta detecção na imagem)")
            print("   c - Corrigir (escolher outro produto)")
            print()
            
            escolha = input("   ▶️  Escolha: ").strip().lower()
            
            if escolha == 'v':
                # Mostrar esta detecção específica
                self.mostrar_bbox_especifica(i-1)
                # Repetir a pergunta
                i -= 1
                continue
            
            elif escolha == '✓':
                # Buscar produto no banco
                try:
                    produto = ProdutoMae.objects.get(
                        marca=marca,
                        descricao_produto__icontains=descricao.replace(marca, '').strip()
                    )
                    self.produtos_marcados.append(produto)
                    det['produto'] = produto
                    det['indice'] = i - 1  # Salvar índice para vincular bbox
                    print(f"   ✅ Confirmado: {produto.marca} - {produto.descricao_produto}\n")
                except ProdutoMae.DoesNotExist:
                    print(f"   ❌ Produto não encontrado no banco. Use 'c' para corrigir.\n")
                    
            elif escolha == 'x':
                print(f"   ❌ Ignorado\n")
                
            elif escolha == 'c':
                print(f"\n   📦 Produto detectado: {marca} - {descricao}")
                print(f"   🔄 Escolha o produto CORRETO:\n")
                produto = self.selecionar_produto_manual()
                if produto:
                    self.produtos_marcados.append(produto)
                    det['produto'] = produto
                    det['indice'] = i - 1  # Salvar índice para vincular bbox
                    print(f"   ✅ Corrigido para: {produto.marca} - {produto.descricao_produto}\n")
                    
        print(f"\n✅ Total confirmado: {len(self.produtos_marcados)} produto(s)")
        
    def salvar_marcacoes(self, caminho_imagem):
        """Salva as marcações no banco de dados"""
        if not self.produtos_marcados:
            print("\n⚠️  Nenhum produto para salvar")
            return
            
        print(f"\n💾 Salvando {len(self.produtos_marcados)} marcação(ões)...")
        
        # Abrir imagem original
        img_pil = Image.open(caminho_imagem)
        nome_arquivo = Path(caminho_imagem).stem
        
        salvos = 0
        
        for i, produto in enumerate(self.produtos_marcados):
            # Buscar bbox correspondente se existir
            bbox = None
            for det in self.deteccoes:
                if 'produto' in det and det['produto'] == produto and 'indice' in det:
                    # Verificar se é o mesmo índice (para não pegar bbox errada)
                    if i == det.get('indice', -1):
                        bbox = det['bbox']
                        break
            
            # Se ainda não achou, tentar pela correspondência de produto
            if bbox is None:
                for det in self.deteccoes:
                    if 'produto' in det and det['produto'] == produto:
                        bbox = det['bbox']
                        break
                    
            # Se não tem bbox, usar imagem completa
            if bbox is None:
                crop = img_pil
                print(f"  ⚠️  {produto.marca} - Usando imagem completa (sem bbox)")
            else:
                x1, y1, x2, y2 = bbox
                crop = img_pil.crop((x1, y1, x2, y2))
                
            # Salvar crop
            marca_dir = Path('media/produtos') / produto.marca
            marca_dir.mkdir(parents=True, exist_ok=True)
            
            # Encontrar próximo número disponível
            numero = 1
            while True:
                crop_filename = f"{numero}_{nome_arquivo}.jpg"
                crop_path = marca_dir / crop_filename
                if not crop_path.exists():
                    break
                numero += 1
                
            # Salvar arquivo
            crop_rgb = crop.convert('RGB')
            crop_rgb.save(crop_path, 'JPEG', quality=95)
            
            # Salvar no banco
            img_treino = ImagemProduto(
                produto=produto,
                imagem=f"produtos/{produto.marca}/{crop_filename}"
            )
            img_treino.save()
            
            print(f"  ✅ {produto.marca} - {produto.descricao_produto}")
            salvos += 1
            
        print(f"\n✅ {salvos} imagem(ns) adicionada(s) ao dataset!")
        print("💡 Execute 'python treinar_modelo_yolo.py' para retreinar")


def main():
    print("\n" + "=" * 80)
    print("🎯 TREINAMENTO COM VALIDAÇÃO DE QUANTIDADE")
    print("=" * 80)
    print()
    
    # Pedir caminho da imagem
    caminho_imagem = input('📸 Caminho da imagem: ').strip().strip('"')
    
    if not caminho_imagem:
        print("❌ Nenhum caminho fornecido")
        return
        
    # Criar treinador
    treinador = TreinadorComValidacao()
    
    # Carregar modelo
    treinador.carregar_modelo()
    
    # Carregar imagem
    if not treinador.carregar_imagem(caminho_imagem):
        return
        
    # ETAPA 1: Perguntar quantos produtos existem
    print("=" * 80)
    print("❓ VALIDAÇÃO DE QUANTIDADE")
    print("=" * 80)
    
    try:
        qtd_esperada = int(input("\n📊 Quantos produtos existem nesta foto? ").strip())
    except ValueError:
        print("❌ Valor inválido")
        return
        
    # ETAPA 2: Detectar automaticamente
    qtd_detectada = treinador.detectar_produtos(qtd_esperada=qtd_esperada)
    
    # ETAPA 3: Comparar quantidades
    print("=" * 80)
    print("📊 RESULTADO DA DETECÇÃO")
    print("=" * 80)
    print(f"\n   Esperado:  {qtd_esperada} produto(s)")
    print(f"   Detectado: {qtd_detectada} produto(s)")
    
    if qtd_detectada == qtd_esperada:
        print("\n   ✅ QUANTIDADE CORRETA!")
    else:
        print(f"\n   ⚠️  DIFERENÇA: {abs(qtd_detectada - qtd_esperada)} produto(s)")
        
    # ETAPA 4: Mostrar detecções
    if qtd_detectada > 0:
        print()
        treinador.mostrar_deteccoes()
        
        # Perguntar se quer visualizar
        visualizar = input("\n👁️  Visualizar detecções na imagem? (s/n): ").strip().lower()
        if visualizar == 's':
            treinador.visualizar_deteccoes()
            
    # ETAPA 5: Validar ou corrigir
    print("\n" + "=" * 80)
    print("✅ VALIDAÇÃO")
    print("=" * 80)
    print()
    print("Opções:")
    print("  ✓ - ACEITAR (detecções estão corretas)")
    print("  c - CORRIGIR (revisar uma por uma)")
    print("  m - MANUAL (ignorar detecções e marcar do zero)")
    print("  n - CANCELAR")
    print()
    
    escolha = input("▶️  Escolha: ").strip().lower()
    
    if escolha == '✓' or escolha == 'v':
        # Validar quantidade antes de aceitar
        if len(treinador.deteccoes) != qtd_esperada:
            print(f"\n❌ ERRO: Você informou {qtd_esperada} produto(s), mas o sistema detectou {len(treinador.deteccoes)}!")
            print("   Use 'c' para corrigir ou 'm' para marcar manualmente as regiões corretas.\n")
            # Não salvar, voltar ao menu
        else:
            # Aceitar todas as detecções
            print("\n✅ Aceitando todas as detecções...")
            for det in treinador.deteccoes:
                classe_partes = det['classe'].split(' ', 1)
                marca = classe_partes[0]
                descricao = classe_partes[1] if len(classe_partes) > 1 else ''
                
                try:
                    produto = ProdutoMae.objects.get(
                        marca=marca,
                        descricao_produto__icontains=descricao.replace(marca, '').strip()
                    )
                    treinador.produtos_marcados.append(produto)
                    det['produto'] = produto
                except ProdutoMae.DoesNotExist:
                    print(f"⚠️  Produto não encontrado: {det['classe']}")
                
    elif escolha == 'c':
        # Corrigir detecções
        treinador.corrigir_deteccoes()
        
    elif escolha == 'm':
        # Marcação manual COM bbox obrigatória
        treinador.marcar_manual_com_bbox(qtd_esperada)
        
    elif escolha == 'n':
        print("\n❌ Cancelado")
        return
        
    else:
        print("\n❌ Opção inválida")
        return
        
    # ETAPA 6: Salvar
    if treinador.produtos_marcados:
        treinador.salvar_marcacoes(caminho_imagem)
    else:
        print("\n⚠️  Nenhum produto para salvar")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
