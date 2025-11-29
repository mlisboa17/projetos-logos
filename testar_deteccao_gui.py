#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interface gráfica para testar detecção de produtos
Permite selecionar foto e ajustar parâmetros visualmente
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
from pathlib import Path

# Adicionar ao path para importar módulos Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ultralytics import YOLO


class AplicativoTesteDeteccao:
    def __init__(self, root):
        self.root = root
        self.root.title("VerifiK - Teste de Detecção de Produtos")
        self.root.geometry("1200x800")
        
        self.modelo = None
        self.foto_path = None
        self.foto_original = None
        self.resultado_img = None
        
        self.criar_interface()
        self.carregar_modelo()
    
    def criar_interface(self):
        # Frame superior - Controles
        frame_controles = ttk.Frame(self.root, padding="10")
        frame_controles.pack(side=tk.TOP, fill=tk.X)
        
        # Botão selecionar foto
        self.btn_foto = ttk.Button(
            frame_controles, 
            text="📷 Selecionar Foto",
            command=self.selecionar_foto
        )
        self.btn_foto.pack(side=tk.LEFT, padx=5)
        
        # Label foto selecionada
        self.lbl_foto = ttk.Label(frame_controles, text="Nenhuma foto selecionada")
        self.lbl_foto.pack(side=tk.LEFT, padx=10)
        
        # Slider confiança
        ttk.Label(frame_controles, text="Confiança:").pack(side=tk.LEFT, padx=(20, 5))
        self.confianca_var = tk.DoubleVar(value=0.05)
        self.slider_confianca = ttk.Scale(
            frame_controles,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.confianca_var,
            length=200
        )
        self.slider_confianca.pack(side=tk.LEFT, padx=5)
        self.lbl_confianca = ttk.Label(frame_controles, text="5%")
        self.lbl_confianca.pack(side=tk.LEFT, padx=5)
        
        # Slider IoU
        ttk.Label(frame_controles, text="IoU:").pack(side=tk.LEFT, padx=(20, 5))
        self.iou_var = tk.DoubleVar(value=0.45)
        self.slider_iou = ttk.Scale(
            frame_controles,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.iou_var,
            length=150
        )
        self.slider_iou.pack(side=tk.LEFT, padx=5)
        self.lbl_iou = ttk.Label(frame_controles, text="45%")
        self.lbl_iou.pack(side=tk.LEFT, padx=5)
        
        # Atualizar labels
        def atualizar_confianca(*args):
            valor = self.confianca_var.get()
            self.lbl_confianca.config(text=f"{valor*100:.0f}%")
        self.confianca_var.trace('w', atualizar_confianca)
        
        def atualizar_iou(*args):
            valor = self.iou_var.get()
            self.lbl_iou.config(text=f"{valor*100:.0f}%")
        self.iou_var.trace('w', atualizar_iou)
        
        # Botão detectar
        self.btn_detectar = ttk.Button(
            frame_controles,
            text="🔍 Detectar Produtos",
            command=self.detectar,
            state=tk.DISABLED
        )
        self.btn_detectar.pack(side=tk.LEFT, padx=20)
        
        # Frame central - Imagens
        frame_imagens = ttk.Frame(self.root)
        frame_imagens.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas para imagem original
        frame_original = ttk.LabelFrame(frame_imagens, text="Foto Original", padding="5")
        frame_original.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.canvas_original = tk.Canvas(frame_original, bg="gray")
        self.canvas_original.pack(fill=tk.BOTH, expand=True)
        
        # Canvas para resultado
        frame_resultado = ttk.LabelFrame(frame_imagens, text="Detecções", padding="5")
        frame_resultado.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.canvas_resultado = tk.Canvas(frame_resultado, bg="gray")
        self.canvas_resultado.pack(fill=tk.BOTH, expand=True)
        
        # Frame inferior - Resultados
        frame_resultados = ttk.LabelFrame(self.root, text="Resultados", padding="10")
        frame_resultados.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=10, pady=10)
        
        # Text widget para resultados
        self.text_resultados = tk.Text(frame_resultados, height=8, font=("Consolas", 9))
        self.text_resultados.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.text_resultados, command=self.text_resultados.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_resultados.config(yscrollcommand=scrollbar.set)
    
    def carregar_modelo(self):
        """Carrega o modelo YOLO"""
        self.log("🤖 Carregando modelo YOLO...")
        
        # Procurar modelo
        localizacoes = [
            r"C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\runs\treino_continuado\weights\best.pt",
            r"verifik\runs\treino_continuado\weights\best.pt",
            r"fuel_prices\runs\detect\heineken_330ml\weights\best.pt",
        ]
        
        modelo_path = None
        for loc in localizacoes:
            if os.path.exists(loc):
                modelo_path = loc
                break
        
        if modelo_path is None:
            self.log("❌ ERRO: Modelo não encontrado!")
            return
        
        try:
            self.modelo = YOLO(modelo_path)
            self.log(f"✓ Modelo carregado: {modelo_path}")
            self.log(f"  └─ {len(self.modelo.names)} classes treinadas")
        except Exception as e:
            self.log(f"❌ ERRO ao carregar modelo: {e}")
    
    def selecionar_foto(self):
        """Abre dialog para selecionar foto"""
        filepath = filedialog.askopenfilename(
            title="Selecionar Foto",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        if filepath:
            self.foto_path = filepath
            self.lbl_foto.config(text=os.path.basename(filepath))
            self.btn_detectar.config(state=tk.NORMAL)
            
            # Carregar e mostrar imagem original
            try:
                img = Image.open(filepath)
                self.foto_original = img.copy()
                self.mostrar_imagem(self.canvas_original, img)
                self.log(f"📷 Foto carregada: {os.path.basename(filepath)} ({img.size[0]}x{img.size[1]})")
            except Exception as e:
                self.log(f"❌ ERRO ao carregar foto: {e}")
    
    def mostrar_imagem(self, canvas, img):
        """Mostra imagem no canvas, ajustando tamanho"""
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas.update()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
        
        # Calcular escala
        img_width, img_height = img.size
        scale = min(canvas_width / img_width, canvas_height / img_height) * 0.95
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Redimensionar
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Converter para PhotoImage
        photo = ImageTk.PhotoImage(img_resized)
        
        # Mostrar no canvas
        canvas.delete("all")
        canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=photo,
            anchor=tk.CENTER
        )
        canvas.image = photo  # Manter referência
    
    def detectar(self):
        """Executa detecção na foto selecionada"""
        if self.modelo is None:
            self.log("❌ Modelo não carregado!")
            return
        
        if self.foto_path is None:
            self.log("❌ Nenhuma foto selecionada!")
            return
        
        confianca = self.confianca_var.get()
        iou = self.iou_var.get()
        self.log(f"🔍 Detectando produtos (conf: {confianca*100:.0f}%, IoU: {iou*100:.0f}%)...")
        
        try:
            # Fazer predição
            results = self.modelo.predict(
                source=self.foto_path,
                conf=confianca,
                iou=iou,
                max_det=1000,
                save=False,
                verbose=False
            )
            
            result = results[0]
            boxes = result.boxes
            
            if len(boxes) == 0:
                self.log("⚠️  Nenhum produto detectado!")
                self.log("💡 Tente reduzir a confiança mínima")
                return
            
            # Mostrar imagem com detecções
            img_resultado = result.plot()
            img_resultado = Image.fromarray(img_resultado[..., ::-1])  # BGR -> RGB
            self.mostrar_imagem(self.canvas_resultado, img_resultado)
            
            # Analisar resultados
            self.log(f"✅ {len(boxes)} produto(s) detectado(s)!")
            self.log("-" * 70)
            
            deteccoes = {}
            for i, box in enumerate(boxes):
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                nome_classe = self.modelo.names[cls_id]
                
                if nome_classe not in deteccoes:
                    deteccoes[nome_classe] = []
                deteccoes[nome_classe].append(conf)
                
                self.log(f"  {i+1}. {nome_classe} - {conf*100:.1f}%")
            
            self.log("-" * 70)
            self.log("📊 Resumo:")
            for produto, confidencias in sorted(deteccoes.items()):
                qtd = len(confidencias)
                conf_media = sum(confidencias) / qtd
                self.log(f"  • {produto}: {qtd}x (conf. média: {conf_media*100:.1f}%)")
            
        except Exception as e:
            self.log(f"❌ ERRO na detecção: {e}")
            import traceback
            traceback.print_exc()
    
    def log(self, mensagem):
        """Adiciona mensagem ao log"""
        self.text_resultados.insert(tk.END, mensagem + "\n")
        self.text_resultados.see(tk.END)
        self.root.update()


def main():
    root = tk.Tk()
    app = AplicativoTesteDeteccao(root)
    root.mainloop()


if __name__ == "__main__":
    main()
