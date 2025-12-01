#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detector Simplificado - Método Híbrido YOLO + GRID + OCR
Fluxo: Detecta → Pergunta quantidade → Confirma produtos → Permite correção
"""

import os
import sys
import shutil
import cv2
import numpy as np
import django
import pytesseract
import tkinter as tk
from pathlib import Path
from ultralytics import YOLO
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox, simpledialog

# Configurar Django para acessar produtos_mae
sys.path.append(os.path.join(os.path.dirname(__file__), 'fuel_prices'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
try:
    django.setup()
    from verifik.models import ProdutoMae
    USAR_PRODUTOS_MAE = True
except:
    USAR_PRODUTOS_MAE = False
    print("⚠️  Não foi possível carregar produtos_mae, usando lista fixa")

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Produtos disponíveis (fallback caso Django não funcione)
PRODUTOS = [
    'HEINEKEN_CERVEJA_HEINEKEN_LATA_350ML',
    'BUDWEISER_CERVEJA_BUDWEISER_LATA_350ML',
    'AMSTEL_CERVEJA_AMSTEL_LATA_350ML',
    'STELLA_CERVEJA_STELLA_ARTOIS_LATA_350ML',
    'DEVASSA_CERVEJA_DEVASSA_LATA_350ML',
    'PETRA_CERVEJA_PETRA_LATA_350ML',
    'PILSEN_CERVEJA_PILSEN_LATA_350ML',
    'PEPSI_REFRIGERANTE_PEPSI_LATA_350ML',
    'COCA_REFRIGERANTE_COCA_COLA_LATA_350ML',
]


class DetectorSimples:
    def __init__(self, caminho_foto, caminho_modelo=None):
        self.caminho_foto = caminho_foto
        self.img_original = cv2.imread(caminho_foto)
        self.img_altura, self.img_largura = self.img_original.shape[:2]
        
        # Escala para display
        max_w, max_h = 1000, 700
        if self.img_largura > max_w or self.img_altura > max_h:
            escala_w = max_w / self.img_largura
            escala_h = max_h / self.img_altura
            self.escala = min(escala_w, escala_h)
        else:
            self.escala = 1.0
        
        self.display_w = int(self.img_largura * self.escala)
        self.display_h = int(self.img_altura * self.escala)
        
        # Carregar modelo
        if caminho_modelo is None:
            localizacoes = [
                r"C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\runs\treino_continuado\weights\best.pt",
                r"verifik\runs\treino_continuado\weights\best.pt",
            ]
            for loc in localizacoes:
                if os.path.exists(loc):
                    caminho_modelo = loc
                    break
        
        self.model = YOLO(caminho_modelo)
        
        # Detecções finais
        self.deteccoes_finais = []
        
        # Interface
        self.root = None
        self.canvas = None
        self.desenhando = False
        self.x_inicial = None
        self.y_inicial = None
        self.rect_id = None
    
    def ler_texto_bbox(self, x1, y1, x2, y2):
        """Lê texto na região usando OCR"""
        try:
            regiao = self.img_original[y1:y2, x1:x2]
            
            # Tentar múltiplos métodos de processamento
            metodos = [
                lambda img: img,  # Original
                lambda img: cv2.convertScaleAbs(img, alpha=1.5, beta=30),  # Brilho
                lambda img: cv2.cvtColor(cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)), cv2.COLOR_GRAY2BGR),  # Equalizar
            ]
            
            melhor_texto = ""
            for metodo in metodos:
                img_proc = metodo(regiao)
                texto = pytesseract.image_to_string(img_proc, lang='por+eng', config='--psm 6')
                texto_limpo = ''.join(c for c in texto if c.isalnum() or c.isspace()).strip()
                
                if len(texto_limpo) > len(melhor_texto):
                    melhor_texto = texto_limpo
            
            return melhor_texto if melhor_texto else None
        except:
            return None
    
    def detectar_hibrido(self):
        """Detecção híbrida YOLO + GRID"""
        print("\n" + "="*80)
        print("🔍 DETECÇÃO HÍBRIDA: YOLO + GRID")
        print("="*80 + "\n")
        
        results = self.model.predict(
            source=self.caminho_foto,
            conf=0.05,
            iou=0.3,
            max_det=100,
            save=False,
            verbose=False
        )
        
        boxes = results[0].boxes
        area_total = self.img_largura * self.img_altura
        usar_grid = False
        
        # Verificar se precisa usar grid
        if len(boxes) > 0:
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                bbox_area = (x2 - x1) * (y2 - y1)
                percentual = (bbox_area / area_total) * 100
                
                if percentual > 70:
                    usar_grid = True
                    print(f"⚠️  BBox genérica ({percentual:.1f}%) - usando GRID\n")
                    break
        
        if usar_grid or len(boxes) == 0:
            deteccoes = self._detectar_por_grid()
        else:
            deteccoes = self._processar_deteccoes_normais(boxes)
        
        # Remover duplicatas
        deteccoes = self._remover_duplicatas(deteccoes)
        
        print(f"✅ {len(deteccoes)} produto(s) detectado(s)\n")
        return deteccoes
    
    def _detectar_por_grid(self):
        """Detecção por grid 4x3"""
        grid_deteccoes = []
        
        posicoes_h = [
            ("Esquerda", 0, 0.5),
            ("Esq-Centro", 0.25, 0.75),
            ("Centro-Dir", 0.5, 1.0),
            ("Direita", 0.5, 1.0),
        ]
        
        posicoes_v = [
            ("Superior", 0, 0.4),
            ("Meio", 0.3, 0.7),
            ("Inferior", 0.6, 1.0),
        ]
        
        for nome_v, y_start, y_end in posicoes_v:
            for nome_h, x_start, x_end in posicoes_h:
                x1_reg = int(self.img_largura * x_start)
                x2_reg = int(self.img_largura * x_end)
                y1_reg = int(self.img_altura * y_start)
                y2_reg = int(self.img_altura * y_end)
                
                regiao = self.img_original[y1_reg:y2_reg, x1_reg:x2_reg]
                
                results_reg = self.model.predict(
                    source=regiao,
                    conf=0.025,
                    iou=0.24,
                    max_det=5,
                    save=False,
                    verbose=False
                )
                
                for box in results_reg[0].boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1_local, y1_local, x2_local, y2_local = map(int, xyxy)
                    
                    x1_global = x1_reg + x1_local
                    y1_global = y1_reg + y1_local
                    x2_global = x1_reg + x2_local
                    y2_global = y1_reg + y2_local
                    
                    bbox_w = x2_local - x1_local
                    bbox_h = y2_local - y1_local
                    regiao_w = x2_reg - x1_reg
                    regiao_h = y2_reg - y1_reg
                    
                    if bbox_w > regiao_w * 0.9 and bbox_h > regiao_h * 0.9:
                        continue
                    
                    aspect_ratio = bbox_h / bbox_w if bbox_w > 0 else 0
                    if aspect_ratio < 1.2:
                        continue
                    
                    bbox_area_local = bbox_w * bbox_h
                    regiao_area = regiao_w * regiao_h
                    if bbox_area_local < regiao_area * 0.05:
                        continue
                    
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Tentar OCR para validar/melhorar detecção
                    texto_ocr = self.ler_texto_bbox(x1_global, y1_global, x2_global, y2_global)
                    produto_nome = self.model.names[cls_id]
                    
                    if texto_ocr:
                        print(f"   OCR: {texto_ocr} (detectado como {produto_nome})")
                    
                    grid_deteccoes.append({
                        'bbox': (x1_global, y1_global, x2_global, y2_global),
                        'cls_id': cls_id,
                        'conf': conf,
                        'produto': produto_nome,
                        'ocr_texto': texto_ocr if texto_ocr else ""
                    })
        
        return grid_deteccoes
    
    def _processar_deteccoes_normais(self, boxes):
        """Processa detecções normais"""
        deteccoes = []
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            
            # Tentar OCR para validar
            texto_ocr = self.ler_texto_bbox(x1, y1, x2, y2)
            produto_nome = self.model.names[cls_id]
            
            if texto_ocr:
                print(f"   OCR: {texto_ocr} (detectado como {produto_nome})")
            
            deteccoes.append({
                'bbox': (x1, y1, x2, y2),
                'cls_id': cls_id,
                'conf': conf,
                'produto': produto_nome,
                'ocr_texto': texto_ocr if texto_ocr else ""
            })
        
        return deteccoes
    
    def _remover_duplicatas(self, deteccoes):
        """Remove duplicatas"""
        if not deteccoes:
            return []
        
        deteccoes_ordenadas = sorted(deteccoes, key=lambda x: x['conf'], reverse=True)
        unicas = []
        
        for det in deteccoes_ordenadas:
            x1, y1, x2, y2 = det['bbox']
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            area_det = (x2 - x1) * (y2 - y1)
            
            duplicata = False
            
            for unica in unicas:
                ux1, uy1, ux2, uy2 = unica['bbox']
                ucx = (ux1 + ux2) / 2
                ucy = (uy1 + uy2) / 2
                
                dist = np.sqrt((cx - ucx)**2 + (cy - ucy)**2)
                diagonal = np.sqrt(self.img_largura**2 + self.img_altura**2)
                
                if dist < diagonal * 0.10:
                    duplicata = True
                    break
                
                xi1 = max(x1, ux1)
                yi1 = max(y1, uy1)
                xi2 = min(x2, ux2)
                yi2 = min(y2, uy2)
                
                inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
                
                if inter_area > 0:
                    area_unica = (ux2 - ux1) * (uy2 - uy1)
                    union_area = area_det + area_unica - inter_area
                    iou = inter_area / union_area if union_area > 0 else 0
                    
                    if iou > 0.25:
                        duplicata = True
                        break
            
            if not duplicata:
                unicas.append(det)
        
        return unicas
    
    def perguntar_quantidade(self, deteccoes_auto):
        """Pergunta quantos produtos existem na foto"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update()
        
        qtd_detectada = len(deteccoes_auto)
        
        qtd = simpledialog.askinteger(
            "Quantidade de Produtos",
            f"🔍 Detecção automática encontrou: {qtd_detectada} produto(s)\n\n"
            f"Quantos produtos REALMENTE existem na foto?",
            initialvalue=qtd_detectada,
            minvalue=0,
            maxvalue=50,
            parent=root
        )
        
        root.destroy()
        return qtd
    
    def confirmar_produtos(self, deteccoes_auto):
        """Mostra produtos detectados para confirmação"""
        if not deteccoes_auto:
            return []
        
        confirmadas = []
        
        for i, det in enumerate(deteccoes_auto):
            # Mostrar imagem com bbox destacada
            self.mostrar_produto_para_confirmacao(det, i+1, len(deteccoes_auto))
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.update()
            
            nome_produto = det['produto']
            
            resposta = messagebox.askyesnocancel(
                f"Produto {i+1}/{len(deteccoes_auto)}",
                f"Este produto está correto?\n\n"
                f"🏷️  Produto: {nome_produto}\n"
                f"📊 Confiança: {det['conf']*100:.1f}%\n\n"
                f"✅ Sim = Confirmar produto\n"
                f"❌ Não = Rejeitar produto\n"
                f"🔄 Cancelar = Corrigir produto",
                parent=root
            )
            
            root.destroy()
            
            if resposta is True:  # Sim - confirma
                confirmadas.append(det)
                print(f"✅ Confirmado: {nome_produto}")
            elif resposta is None:  # Cancelar - corrigir
                produto_correto = self.selecionar_produto_dialog()
                if produto_correto:
                    # Se for OUTRO_PRODUTO, tentar OCR
                    if produto_correto.startswith("OUTRO_"):
                        x1, y1, x2, y2 = det['bbox']
                        texto_ocr = self.ler_texto_bbox(x1, y1, x2, y2)
                        if texto_ocr:
                            produto_correto = f"OUTRO_{texto_ocr.upper().replace(' ', '_')}"
                        cls_id = len(PRODUTOS)
                    else:
                        # Verificar se produto está na lista fixa
                        try:
                            cls_id = PRODUTOS.index(produto_correto)
                        except ValueError:
                            # Produto da base produtos_mae
                            cls_id = len(PRODUTOS) + hash(produto_correto) % 1000
                    
                    det['produto'] = produto_correto
                    det['classe_id'] = cls_id
                    confirmadas.append(det)
                    print(f"🔄 Corrigido para: {produto_correto}")
                else:
                    print(f"❌ Cancelado: {nome_produto}")
            else:  # Não - rejeita
                print(f"❌ Rejeitado: {nome_produto}")
        
        return confirmadas
    
    def mostrar_produto_para_confirmacao(self, det, num, total):
        """Mostra janela com produto destacado"""
        img = self.img_original.copy()
        x1, y1, x2, y2 = det['bbox']
        
        # Desenhar bbox em destaque
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 4)
        cv2.putText(img, f"{num}/{total}", (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
        
        # Redimensionar
        if self.escala < 1.0:
            img = cv2.resize(img, (self.display_w, self.display_h))
        
        cv2.imshow(f"Produto {num}/{total} - Pressione qualquer tecla", img)
        cv2.waitKey(500)  # Mostra por 500ms
        cv2.destroyAllWindows()
    
    def adicionar_produtos_manualmente(self, qtd_faltante):
        """Permite adicionar produtos manualmente"""
        print(f"\n📝 Adicione {qtd_faltante} produto(s) manualmente\n")
        
        adicionados = []
        
        for i in range(qtd_faltante):
            det = self.desenhar_bbox_manual(i+1, qtd_faltante)
            if det:
                adicionados.append(det)
        
        return adicionados
    
    def desenhar_bbox_manual(self, num, total):
        """Interface para desenhar bbox manualmente"""
        # Fechar qualquer janela anterior
        try:
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
        except:
            pass
        
        self.root = tk.Tk()
        self.root.title(f"➕ Adicionar Produto {num}/{total}")
        
        # Variáveis de desenho
        self.desenhando = False
        self.x_inicial = 0
        self.y_inicial = 0
        self.rect_id = None
        
        # Canvas
        self.canvas = tk.Canvas(self.root, width=self.display_w, height=self.display_h,
                               bg='black', cursor='cross')
        self.canvas.pack()
        
        # Mostrar imagem
        img = self.img_original.copy()
        if self.escala < 1.0:
            img = cv2.resize(img, (self.display_w, self.display_h))
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        self.photo = ImageTk.PhotoImage(img_pil)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Eventos
        self.canvas.bind('<ButtonPress-1>', self.mouse_press)
        self.canvas.bind('<B1-Motion>', self.mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.mouse_release)
        
        # Instruções
        tk.Label(self.root, text=f"🖱️  ARRASTE o mouse para desenhar a caixa ao redor do produto {num}/{total}",
                font=('Arial', 11, 'bold'), bg='#3498db', fg='white', pady=10).pack(fill=tk.X)
        
        self.bbox_selecionada = None
        self.root.mainloop()
        
        return self.bbox_selecionada
    
    def mouse_press(self, event):
        self.desenhando = True
        self.x_inicial = int(event.x / self.escala)
        self.y_inicial = int(event.y / self.escala)
    
    def mouse_drag(self, event):
        if self.desenhando:
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            
            x = event.x
            y = event.y
            self.rect_id = self.canvas.create_rectangle(
                self.x_inicial * self.escala, 
                self.y_inicial * self.escala,
                x, y, outline='yellow', width=3
            )
    
    def mouse_release(self, event):
        if self.desenhando:
            self.desenhando = False
            x_final = int(event.x / self.escala)
            y_final = int(event.y / self.escala)
            
            x1 = min(self.x_inicial, x_final)
            y1 = min(self.y_inicial, y_final)
            x2 = max(self.x_inicial, x_final)
            y2 = max(self.y_inicial, y_final)
            
            if abs(x2 - x1) > 20 and abs(y2 - y1) > 20:
                # Selecionar produto
                produto = self.selecionar_produto_dialog()
                
                if produto:
                    # Se for OUTRO_PRODUTO, tentar OCR na região
                    if produto.startswith("OUTRO_"):
                        texto_ocr = self.ler_texto_bbox(x1, y1, x2, y2)
                        if texto_ocr:
                            produto = f"OUTRO_{texto_ocr.upper().replace(' ', '_')}"
                        cls_id = len(PRODUTOS)  # Índice para produtos desconhecidos
                    else:
                        # Verificar se produto está na lista fixa, senão usar índice genérico
                        try:
                            cls_id = PRODUTOS.index(produto)
                        except ValueError:
                            # Produto da base produtos_mae que não está na lista fixa
                            cls_id = len(PRODUTOS) + hash(produto) % 1000
                    
                    self.bbox_selecionada = {
                        'bbox': (x1, y1, x2, y2),
                        'produto': produto,
                        'cls_id': cls_id,
                        'conf': 1.0,
                        'manual': True
                    }
                    try:
                        self.root.destroy()
                    except:
                        pass  # Janela já foi fechada
    
    def selecionar_produto_dialog(self):
        """Dialog para selecionar produto"""
        dialog = tk.Tk()
        dialog.title("Selecionar Produto")
        dialog.geometry("600x750")
        
        tk.Label(dialog, text="🏷️ Selecione o Produto:", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Campo de pesquisa
        search_frame = tk.Frame(dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 Buscar:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 12), width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        def limpar_busca():
            search_var.set("")
            search_entry.focus()
        
        def buscar_agora():
            filtrar_produtos()
            
        tk.Button(search_frame, text="🔍", command=buscar_agora, 
                 bg="#3498db", fg="white", font=("Arial", 11, "bold"), 
                 width=3).pack(side=tk.LEFT, padx=2)
        
        tk.Button(search_frame, text="✖", command=limpar_busca, 
                 bg="#95a5a6", fg="white", font=("Arial", 10, "bold"), 
                 width=3).pack(side=tk.LEFT, padx=2)
        
        # Dica de uso
        tk.Label(dialog, text="💡 Digite e pressione ENTER ou clique 🔍 para buscar", 
                font=("Arial", 9), fg="gray").pack(pady=(0, 5))
        
        # Frame principal com scroll
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas com scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Habilitar scroll com mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        produto_selecionado = [None]
        todos_widgets = []  # Armazena widgets para filtrar
        botao_selecionado = [None]  # Armazena botão atual selecionado
        
        def marcar_selecao(btn, produto_nome):
            """Marca visualmente o botão selecionado"""
            # Desmarcar botão anterior
            if botao_selecionado[0]:
                botao_selecionado[0].config(bg="#3498db", relief=tk.RAISED)
            
            # Marcar novo botão
            btn.config(bg="#27ae60", relief=tk.SUNKEN)
            botao_selecionado[0] = btn
            produto_selecionado[0] = produto_nome
        
        def selecionar_produto_mae(produto_obj, btn):
            """Seleciona produto do produtos_mae"""
            nome_produto = f"{produto_obj.marca}_{produto_obj.descricao_produto}".upper().replace(" ", "_")
            marcar_selecao(btn, nome_produto)
        
        def selecionar_marca_fixa(marca, btn):
            """Seleciona produto da lista fixa"""
            for prod in PRODUTOS:
                if prod.startswith(marca + "_"):
                    marcar_selecao(btn, prod)
                    return
        
        # Carregar produtos
        usar_db = USAR_PRODUTOS_MAE
        if usar_db:
            try:
                produtos_db = ProdutoMae.objects.all().order_by('marca', 'descricao_produto')
                
                # Agrupar por marca
                marcas_dict = {}
                for p in produtos_db:
                    if p.marca not in marcas_dict:
                        marcas_dict[p.marca] = []
                    marcas_dict[p.marca].append(p)
                
                # Mostrar por marca
                for marca in sorted(marcas_dict.keys()):
                    label = tk.Label(scrollable_frame, text=marca, font=("Arial", 11, "bold"),
                            bg="#34495e", fg="white")
                    label.pack(fill=tk.X, pady=(5, 0))
                    todos_widgets.append({'widget': label, 'texto': marca, 'pady': (5, 0)})
                    
                    for produto in marcas_dict[marca]:
                        desc_curta = produto.descricao_produto[:60]
                        btn = tk.Button(scrollable_frame, text=f"   {desc_curta}", font=("Arial", 10),
                                 bg="#3498db", fg="white", pady=8, anchor="w",
                                 command=lambda p=produto, b=None: None)
                        btn.pack(fill=tk.X, pady=1)
                        btn.config(command=lambda p=produto, b=btn: selecionar_produto_mae(p, b))
                        todos_widgets.append({'widget': btn, 'texto': f"{marca} {desc_curta}", 'pady': 1})
            except Exception as e:
                print(f"⚠️  Erro ao carregar produtos_mae: {e}")
                usar_db = False
        
        if not usar_db:
            # Lista fixa de produtos
            produtos_org = [
                ("CERVEJAS", [
                    ("HEINEKEN", "🟢 Heineken"),
                    ("BUDWEISER", "🔴 Budweiser"),
                    ("AMSTEL", "🟡 Amstel"),
                    ("STELLA", "⚪ Stella Artois"),
                    ("DEVASSA", "🟤 Devassa"),
                    ("PETRA", "🟠 Petra"),
                    ("PILSEN", "🔵 Pilsen"),
                ]),
                ("REFRIGERANTES", [
                    ("PEPSI", "🔵 Pepsi"),
                    ("COCA", "🔴 Coca-Cola"),
                ])
            ]
            
            for categoria, itens in produtos_org:
                label = tk.Label(scrollable_frame, text=categoria, font=("Arial", 11, "bold"),
                        bg="#34495e", fg="white")
                label.pack(fill=tk.X, pady=(5, 0))
                todos_widgets.append({'widget': label, 'texto': categoria, 'pady': (5, 0)})
                
                for marca, nome in itens:
                    btn = tk.Button(scrollable_frame, text=nome, font=("Arial", 12),
                             bg="#3498db", fg="white", pady=10,
                             command=lambda m=marca, b=None: None)
                    btn.pack(fill=tk.X, pady=2)
                    btn.config(command=lambda m=marca, b=btn: selecionar_marca_fixa(m, b))
                    todos_widgets.append({'widget': btn, 'texto': f"{categoria} {nome}", 'pady': 2})
        
        # Opção OUTRO PRODUTO
        label_outro = tk.Label(scrollable_frame, text="OUTRO PRODUTO", font=("Arial", 11, "bold"),
                bg="#9b59b6", fg="white")
        label_outro.pack(fill=tk.X, pady=(10, 0))
        todos_widgets.append({'widget': label_outro, 'texto': "OUTRO PRODUTO", 'pady': (10, 0)})
        
        # Definir filtro DEPOIS de carregar todos os widgets
        def filtrar_produtos(*args):
            """Filtra produtos baseado na busca"""
            termo = search_var.get().upper().strip()
            print(f"DEBUG: Filtrando por '{termo}', total widgets: {len(todos_widgets)}")
            
            # Se termo vazio, mostrar tudo
            if not termo:
                for widget_info in todos_widgets:
                    widget_info['widget'].pack(fill=tk.X, pady=widget_info['pady'])
                canvas.yview_moveto(0)
                return
            
            # Normalizar termos comuns
            termo_normalizado = termo
            if "REFRI" in termo or "REFRIG" in termo:
                termo_normalizado = "REFRIGERANTE"
            
            # Ocultar todos primeiro
            for widget_info in todos_widgets:
                widget_info['widget'].pack_forget()
            
            # Mostrar apenas os que correspondem
            encontrados = 0
            for widget_info in todos_widgets:
                texto = widget_info['texto'].upper()
                
                # Normalizar texto também
                texto_normalizado = texto
                if "REFRI" in texto or "REFRIG" in texto:
                    texto_normalizado = texto.replace("REFRI", "REFRIGERANTE").replace("REFRIG", "REFRIGERANTE")
                
                if termo_normalizado in texto_normalizado or termo in texto:
                    widget_info['widget'].pack(fill=tk.X, pady=widget_info['pady'])
                    encontrados += 1
            
            print(f"DEBUG: Encontrados {encontrados} itens")
            canvas.update_idletasks()
            canvas.yview_moveto(0)
        
        # Vincular busca em tempo real
        search_var.trace_add('write', filtrar_produtos)
        
        # Também permitir buscar com Enter
        def buscar_enter(event):
            filtrar_produtos()
        
        search_entry.bind('<Return>', buscar_enter)
        
        def outro_produto():
            nome = simpledialog.askstring("Outro Produto", 
                                         "Digite o nome do produto:")
            if nome:
                nome_limpo = nome.strip().upper().replace(" ", "_")
                produto_selecionado[0] = f"OUTRO_{nome_limpo}"
        
        btn_outro = tk.Button(scrollable_frame, text="🔍 Outro Produto (OCR)", font=("Arial", 12),
                 bg="#9b59b6", fg="white", pady=10,
                 command=outro_produto)
        btn_outro.pack(fill=tk.X, pady=2)
        todos_widgets.append({'widget': btn_outro, 'texto': "OUTRO PRODUTO OCR", 'pady': 2})
        
        # Frame de botões (fixo no rodapé)
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def confirmar():
            if produto_selecionado[0]:
                canvas.unbind_all("<MouseWheel>")
                dialog.destroy()
            else:
                messagebox.showwarning("Atenção", "⚠️ Selecione um produto da lista primeiro!\n\nClique em um produto para marcá-lo em verde,\ndepois clique em Confirmar.")
        
        def cancelar():
            produto_selecionado[0] = None
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
        
        # Label de status
        status_label = tk.Label(btn_frame, text="Nenhum produto selecionado", 
                               font=("Arial", 10), fg="#e74c3c", bg="#ecf0f1", pady=5)
        status_label.pack(fill=tk.X, pady=(0, 5))
        
        def atualizar_status(*args):
            if produto_selecionado[0]:
                # Pegar apenas nome curto
                nome_curto = produto_selecionado[0].split('_')[0]
                status_label.config(text=f"✓ Selecionado: {nome_curto}", fg="#27ae60")
            else:
                status_label.config(text="Nenhum produto selecionado", fg="#e74c3c")
        
        # Atualizar status quando selecionar
        original_marcar = marcar_selecao
        def marcar_selecao_com_status(btn, produto_nome):
            original_marcar(btn, produto_nome)
            atualizar_status()
        
        # Substituir função
        globals()['marcar_selecao'] = marcar_selecao_com_status
        
        tk.Button(btn_frame, text="✅ CONFIRMAR SELEÇÃO", command=confirmar,
                 bg="#27ae60", fg="white", font=("Arial", 12, "bold"),
                 pady=12).pack(fill=tk.X, pady=(0, 5))
        
        tk.Button(btn_frame, text="❌ Cancelar", command=cancelar,
                 bg="#e74c3c", fg="white", font=("Arial", 11),
                 pady=8).pack(fill=tk.X)
        
        dialog.mainloop()
        return produto_selecionado[0]
    
    def salvar_resultado(self):
        """Salvar dados de treino"""
        if len(self.deteccoes_finais) == 0:
            print("\n⚠️  Nenhuma detecção para salvar!")
            return
        
        output_dir = Path("dataset_corrigido")
        images_dir = output_dir / "images"
        labels_dir = output_dir / "labels"
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        nome_original = Path(self.caminho_foto).stem
        timestamp = Path(self.caminho_foto).stat().st_mtime
        nome_arquivo = f"{nome_original}_{int(timestamp)}"
        
        # Salvar imagem
        img_path = images_dir / f"{nome_arquivo}.jpg"
        shutil.copy(self.caminho_foto, img_path)
        
        # Salvar anotações
        label_path = labels_dir / f"{nome_arquivo}.txt"
        with open(label_path, 'w') as f:
            for det in self.deteccoes_finais:
                x1, y1, x2, y2 = det['bbox']
                x_center = ((x1 + x2) / 2) / self.img_largura
                y_center = ((y1 + y2) / 2) / self.img_altura
                width = (x2 - x1) / self.img_largura
                height = (y2 - y1) / self.img_altura
                class_id = det['cls_id']
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        # Salvar classes
        classes_path = output_dir / "classes.txt"
        with open(classes_path, 'w', encoding='utf-8') as f:
            for produto in PRODUTOS:
                f.write(f"{produto}\n")
        
        # Salvar preview
        img_preview = self.img_original.copy()
        for i, det in enumerate(self.deteccoes_finais):
            x1, y1, x2, y2 = det['bbox']
            cv2.rectangle(img_preview, (x1, y1), (x2, y2), (0, 255, 0), 3)
            texto = f"{i+1}. {det['produto'].split('_')[0]}"
            cv2.putText(img_preview, texto, (x1, y1-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        preview_path = output_dir / f"{nome_arquivo}_preview.jpg"
        cv2.imwrite(str(preview_path), img_preview)
        
        # Listar produtos salvos
        produtos_salvos = [det['produto'] for det in self.deteccoes_finais]
        
        print("\n" + "="*80)
        print("💾 DADOS DE TREINO SALVOS:")
        print("="*80)
        print(f"✅ Imagem: {img_path}")
        print(f"✅ Anotações: {label_path}")
        print(f"✅ Preview: {preview_path}")
        print(f"📊 Total: {len(self.deteccoes_finais)} produto(s)")
        print("\n📦 PRODUTOS SALVOS PARA TREINO:")
        print("-"*80)
        for i, produto in enumerate(produtos_salvos, 1):
            print(f"  {i}. {produto}")
        print("="*80 + "\n")
        
        # Criar mensagem resumida
        produtos_resumo = "\n".join([f"  • {p.split('_')[0]}" for p in produtos_salvos])
        
        messagebox.showinfo("Sucesso", 
                           f"✅ Salvamento concluído!\n\n"
                           f"📦 {len(self.deteccoes_finais)} produto(s) salvos:\n\n"
                           f"{produtos_resumo}\n\n"
                           f"📁 Local: {output_dir.absolute()}")
    
    def executar(self):
        """Fluxo principal"""
        # 1. Detectar automaticamente
        deteccoes_auto = self.detectar_hibrido()
        
        # 2. Perguntar quantidade
        qtd_real = self.perguntar_quantidade(deteccoes_auto)
        
        if qtd_real is None:
            print("❌ Cancelado pelo usuário")
            return
        
        # 3. Confirmar produtos detectados
        if len(deteccoes_auto) > 0:
            confirmadas = self.confirmar_produtos(deteccoes_auto[:qtd_real])
        else:
            confirmadas = []
        
        # 4. Adicionar produtos manualmente se necessário
        qtd_faltante = qtd_real - len(confirmadas)
        
        if qtd_faltante > 0:
            manuais = self.adicionar_produtos_manualmente(qtd_faltante)
            self.deteccoes_finais = confirmadas + manuais
        else:
            self.deteccoes_finais = confirmadas
        
        # 5. Perguntar se quer adicionar mais produtos (não detectados)
        if len(self.deteccoes_finais) > 0:
            resposta = messagebox.askyesno(
                "Adicionar mais produtos?",
                f"✅ {len(self.deteccoes_finais)} produto(s) confirmado(s)\n\n"
                f"Existe algum produto que o sistema NÃO detectou?\n\n"
                f"(Produtos novos que ele ainda não conhece)"
            )
            
            if resposta:
                qtd_extras = simpledialog.askinteger(
                    "Produtos Extras",
                    "Quantos produtos EXTRAS você quer adicionar?",
                    initialvalue=1,
                    minvalue=1,
                    maxvalue=20
                )
                
                if qtd_extras:
                    extras = self.adicionar_produtos_manualmente(qtd_extras)
                    self.deteccoes_finais.extend(extras)
        
        # 6. Salvar resultado
        if len(self.deteccoes_finais) > 0:
            self.salvar_resultado()
        else:
            print("\n⚠️  Nenhuma detecção final. Nada foi salvo.")


def main():
    print("📷 Selecione a foto...")
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    root.update()
    
    caminho_foto = filedialog.askopenfilename(
        title="Selecionar Foto",
        filetypes=[
            ("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp"),
            ("Todos os arquivos", "*.*")
        ],
        parent=root
    )
    
    root.destroy()
    
    if not caminho_foto:
        print("❌ Nenhuma foto selecionada.")
        return
    
    detector = DetectorSimples(caminho_foto)
    detector.executar()


if __name__ == "__main__":
    main()
