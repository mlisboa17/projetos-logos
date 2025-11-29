"""
Sistema de Coleta de Imagens - Versão Mobile (Android)
Desenvolvido com Kivy para rodar em smartphones
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image as KivyImage
from kivy.uix.camera import Camera
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform

import sqlite3
import requests
import json
import os
from datetime import datetime
from pathlib import Path
import tempfile

# Link do Google Drive para sincronização
LINK_GOOGLE_DRIVE_BANCO = "https://drive.google.com/uc?export=download&id=1N_eU1mQUJGX-G-RrenApfUM6Nfs0eA8V"


class TelaInicial(Screen):
    """Tela inicial com sincronização"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Logo/Título
        titulo = Label(
            text='[b]VerifiK[/b]\nSistema de Coleta Mobile',
            markup=True,
            font_size='24sp',
            size_hint=(1, 0.3)
        )
        layout.add_widget(titulo)
        
        # Botão sincronizar
        btn_sync = Button(
            text='🔄 Sincronizar Produtos',
            size_hint=(1, 0.2),
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_sync.bind(on_press=self.sincronizar)
        layout.add_widget(btn_sync)
        
        # Botão iniciar coleta
        btn_iniciar = Button(
            text='📸 Iniciar Coleta',
            size_hint=(1, 0.2),
            background_color=(0.15, 0.68, 0.38, 1)
        )
        btn_iniciar.bind(on_press=self.ir_para_coleta)
        layout.add_widget(btn_iniciar)
        
        # Botão exportar
        btn_exportar = Button(
            text='📤 Exportar Dados',
            size_hint=(1, 0.2),
            background_color=(0.95, 0.61, 0.07, 1)
        )
        btn_exportar.bind(on_press=self.exportar_dados)
        layout.add_widget(btn_exportar)
        
        self.add_widget(layout)
    
    def sincronizar(self, instance):
        """Sincroniza produtos do Google Drive"""
        try:
            # Mostrar progresso
            popup = Popup(
                title='Sincronizando...',
                content=Label(text='Baixando produtos da nuvem...'),
                size_hint=(0.8, 0.3)
            )
            popup.open()
            
            # Download
            response = requests.get(LINK_GOOGLE_DRIVE_BANCO, timeout=30)
            
            if response.status_code == 200:
                # Salvar temporariamente
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
                temp_file.write(response.content)
                temp_file.close()
                
                # Importar produtos
                app = App.get_running_app()
                app.importar_produtos(temp_file.name)
                
                os.unlink(temp_file.name)
                
                popup.dismiss()
                self.mostrar_mensagem('Sucesso!', '✅ Produtos sincronizados!')
            else:
                popup.dismiss()
                self.mostrar_mensagem('Erro', 'Falha ao baixar dados')
                
        except Exception as e:
            popup.dismiss()
            self.mostrar_mensagem('Erro', f'Erro: {str(e)}')
    
    def ir_para_coleta(self, instance):
        self.manager.current = 'coleta'
    
    def exportar_dados(self, instance):
        self.manager.current = 'exportar'
    
    def mostrar_mensagem(self, titulo, mensagem):
        popup = Popup(
            title=titulo,
            content=Label(text=mensagem),
            size_hint=(0.8, 0.4)
        )
        popup.open()


class TelaColeta(Screen):
    """Tela principal de coleta com câmera"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.produto_selecionado = None
        self.bboxes = []
        self.foto_path = None
        
        layout = BoxLayout(orientation='vertical', spacing=5)
        
        # Barra superior - Produto selecionado
        self.label_produto = Label(
            text='Selecione um produto',
            size_hint=(1, 0.08),
            color=(1, 0.84, 0, 1)
        )
        layout.add_widget(self.label_produto)
        
        # Contador de produtos na foto
        self.label_contador = Label(
            text='Nenhuma foto capturada',
            size_hint=(1, 0.06),
            color=(0.5, 1, 0.5, 1),
            font_size='14sp'
        )
        layout.add_widget(self.label_contador)
        
        # Câmera
        self.camera = Camera(
            resolution=(1280, 720),
            size_hint=(1, 0.6),
            play=True
        )
        layout.add_widget(self.camera)
        
        # Botões de ação
        btn_layout = GridLayout(cols=3, size_hint=(1, 0.12), spacing=5)
        
        btn_produtos = Button(text='📦 Produtos', background_color=(0.2, 0.6, 1, 1))
        btn_produtos.bind(on_press=self.selecionar_produto)
        btn_layout.add_widget(btn_produtos)
        
        btn_foto = Button(text='📸 Capturar', background_color=(0.15, 0.68, 0.38, 1))
        btn_foto.bind(on_press=self.capturar_foto)
        btn_layout.add_widget(btn_foto)
        
        btn_salvar = Button(text='💾 Salvar', background_color=(0.95, 0.61, 0.07, 1))
        btn_salvar.bind(on_press=self.salvar_anotacao)
        btn_layout.add_widget(btn_salvar)
        
        layout.add_widget(btn_layout)
        
        # Observações
        self.obs_input = TextInput(
            hint_text='Observações (opcional)',
            size_hint=(1, 0.12),
            multiline=False
        )
        layout.add_widget(self.obs_input)
        
        # Botão voltar
        btn_voltar = Button(
            text='⬅️ Voltar',
            size_hint=(1, 0.08),
            background_color=(0.59, 0.65, 0.69, 1)
        )
        btn_voltar.bind(on_press=self.voltar)
        layout.add_widget(btn_voltar)
        
        self.add_widget(layout)
    
    def selecionar_produto(self, instance):
        """Abre lista de produtos"""
        app = App.get_running_app()
        produtos = app.carregar_produtos()
        
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)
        scroll = ScrollView(size_hint=(1, 0.9))
        lista = GridLayout(cols=1, spacing=5, size_hint_y=None)
        lista.bind(minimum_height=lista.setter('height'))
        
        for prod in produtos:
            btn = Button(
                text=f"{prod[1]} - {prod[2] or ''}",
                size_hint_y=None,
                height=60
            )
            btn.produto_id = prod[0]
            btn.produto_nome = prod[1]
            btn.bind(on_press=self.produto_selecionado_callback)
            lista.add_widget(btn)
        
        scroll.add_widget(lista)
        content.add_widget(scroll)
        
        btn_fechar = Button(text='Fechar', size_hint=(1, 0.1))
        content.add_widget(btn_fechar)
        
        self.popup_produtos = Popup(
            title='Selecione o Produto',
            content=content,
            size_hint=(0.9, 0.9)
        )
        btn_fechar.bind(on_press=self.popup_produtos.dismiss)
        self.popup_produtos.open()
    
    def produto_selecionado_callback(self, instance):
        self.produto_selecionado = (instance.produto_id, instance.produto_nome)
        self.label_produto.text = f'✓ {instance.produto_nome}'
        self.popup_produtos.dismiss()
    
    def capturar_foto(self, instance):
        """Captura foto da câmera"""
        if not self.produto_selecionado:
            self.mostrar_mensagem('Atenção', 'Selecione um produto primeiro!')
            return
        
        # Se já tem foto, apenas adiciona produto
        if self.foto_path:
            self.bboxes.append({
                'produto_id': self.produto_selecionado[0],
                'produto_nome': self.produto_selecionado[1]
            })
            
            # Atualizar contador
            self.label_contador.text = f'✅ {len(self.bboxes)} produto(s) nesta foto'
            
            self.mostrar_mensagem(
                'Produto Adicionado!', 
                f'✅ {self.produto_selecionado[1]} adicionado!\n\n'
                f'Total: {len(self.bboxes)} produto(s) nesta foto\n\n'
                f'💡 Selecione outro produto e clique novamente\n'
                f'ou clique em SALVAR para finalizar.'
            )
            return
        
        # Primeira vez - captura foto
        app = App.get_running_app()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.foto_path = os.path.join(app.img_dir, f"foto_{timestamp}.jpg")
        self.camera.export_to_png(self.foto_path)
        
        # Adicionar primeiro produto
        self.bboxes.append({
            'produto_id': self.produto_selecionado[0],
            'produto_nome': self.produto_selecionado[1]
        })
        
        # Atualizar contador
        self.label_contador.text = f'✅ 1 produto nesta foto'
        
        self.mostrar_mensagem(
            'Foto Capturada!', 
            f'✅ Foto salva com {self.produto_selecionado[1]}!\n\n'
            f'💡 DICA: Tem mais produtos nesta foto?\n'
            f'Selecione outro produto e clique em\n'
            f'📸 CAPTURAR novamente (sem tirar outra foto)!\n\n'
            f'Quando terminar, clique em SALVAR.'
        )
    
    def salvar_anotacao(self, instance):
        """Salva anotações no banco"""
        if not self.foto_path or not self.bboxes:
            self.mostrar_mensagem('Atenção', 'Capture uma foto primeiro!')
            return
        
        app = App.get_running_app()
        observacoes = self.obs_input.text
        
        try:
            conn = sqlite3.connect(app.db_path)
            cursor = conn.cursor()
            
            # Salvar imagem
            cursor.execute('''
                INSERT INTO imagens_coletadas 
                (caminho_imagem, tipo, total_anotacoes, observacoes, usuario)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.foto_path, 'mobile', len(self.bboxes), observacoes, 'mobile_user'))
            
            imagem_id = cursor.lastrowid
            
            # Salvar anotações (sem bbox pois é mobile)
            for bbox in self.bboxes:
                cursor.execute('''
                    INSERT INTO anotacoes
                    (imagem_id, produto_id, bbox_x, bbox_y, bbox_width, bbox_height)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (imagem_id, bbox['produto_id'], 0.5, 0.5, 0.8, 0.8))
            
            conn.commit()
            conn.close()
            
            # Limpar
            self.bboxes = []
            self.foto_path = None
            self.obs_input.text = ''
            self.label_produto.text = 'Selecione um produto'
            self.label_contador.text = 'Nenhuma foto capturada'
            self.produto_selecionado = None
            
            self.mostrar_mensagem('Sucesso!', '✅ Anotação salva!')
            
        except Exception as e:
            self.mostrar_mensagem('Erro', f'Erro ao salvar: {str(e)}')
    
    def voltar(self, instance):
        self.manager.current = 'inicial'
    
    def mostrar_mensagem(self, titulo, mensagem):
        popup = Popup(
            title=titulo,
            content=Label(text=mensagem),
            size_hint=(0.8, 0.4)
        )
        popup.open()


class TelaExportar(Screen):
    """Tela de exportação de dados"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        titulo = Label(
            text='📤 Exportar Dados',
            font_size='20sp',
            size_hint=(1, 0.2)
        )
        layout.add_widget(titulo)
        
        self.label_info = Label(
            text='Carregando...',
            size_hint=(1, 0.4)
        )
        layout.add_widget(self.label_info)
        
        btn_exportar = Button(
            text='💾 Gerar Arquivo de Exportação',
            size_hint=(1, 0.2),
            background_color=(0.15, 0.68, 0.38, 1)
        )
        btn_exportar.bind(on_press=self.exportar)
        layout.add_widget(btn_exportar)
        
        btn_voltar = Button(
            text='⬅️ Voltar',
            size_hint=(1, 0.2),
            background_color=(0.59, 0.65, 0.69, 1)
        )
        btn_voltar.bind(on_press=self.voltar)
        layout.add_widget(btn_voltar)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """Atualizar informações ao entrar"""
        app = App.get_running_app()
        conn = sqlite3.connect(app.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM imagens_coletadas WHERE sincronizado = 0')
        total = cursor.fetchone()[0]
        conn.close()
        
        self.label_info.text = f'📊 Dados Coletados:\n\n{total} imagem(ns) para exportar'
    
    def exportar(self, instance):
        app = App.get_running_app()
        try:
            export_path = os.path.join(app.data_dir, f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            
            conn = sqlite3.connect(app.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM imagens_coletadas WHERE sincronizado = 0')
            imagens = cursor.fetchall()
            
            dados = []
            for img in imagens:
                img_id = img[0]
                cursor.execute('SELECT produto_id FROM anotacoes WHERE imagem_id = ?', (img_id,))
                produtos = [p[0] for p in cursor.fetchall()]
                
                dados.append({
                    'imagem': img[1],
                    'produtos': produtos,
                    'observacoes': img[6],
                    'data': img[4]
                })
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            conn.close()
            
            self.mostrar_mensagem('Sucesso!', f'✅ Exportado!\n\n{export_path}')
            
        except Exception as e:
            self.mostrar_mensagem('Erro', f'Erro: {str(e)}')
    
    def voltar(self, instance):
        self.manager.current = 'inicial'
    
    def mostrar_mensagem(self, titulo, mensagem):
        popup = Popup(
            title=titulo,
            content=Label(text=mensagem),
            size_hint=(0.8, 0.4)
        )
        popup.open()


class VerifiKMobileApp(App):
    """Aplicativo principal"""
    
    def build(self):
        # Configurar diretórios
        if platform == 'android':
            from android.storage import primary_external_storage_path
            self.data_dir = os.path.join(primary_external_storage_path(), 'VerifiK')
        else:
            self.data_dir = os.path.join(os.path.expanduser('~'), 'VerifiK')
        
        os.makedirs(self.data_dir, exist_ok=True)
        self.img_dir = os.path.join(self.data_dir, 'imagens')
        os.makedirs(self.img_dir, exist_ok=True)
        
        self.db_path = os.path.join(self.data_dir, 'verifik_mobile.db')
        
        # Inicializar banco
        self.init_database()
        
        # Criar telas
        sm = ScreenManager()
        sm.add_widget(TelaInicial(name='inicial'))
        sm.add_widget(TelaColeta(name='coleta'))
        sm.add_widget(TelaExportar(name='exportar'))
        
        return sm
    
    def init_database(self):
        """Inicializar banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao_produto TEXT NOT NULL,
                marca TEXT,
                ativo INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imagens_coletadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caminho_imagem TEXT NOT NULL,
                tipo TEXT,
                usuario TEXT,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_anotacoes INTEGER,
                observacoes TEXT,
                sincronizado INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anotacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imagem_id INTEGER,
                produto_id INTEGER,
                bbox_x REAL,
                bbox_y REAL,
                bbox_width REAL,
                bbox_height REAL,
                FOREIGN KEY (imagem_id) REFERENCES imagens_coletadas(id),
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def importar_produtos(self, db_temp_path):
        """Importar produtos do banco temporário"""
        try:
            conn_temp = sqlite3.connect(db_temp_path)
            cursor_temp = conn_temp.cursor()
            
            cursor_temp.execute('SELECT descricao_produto, marca FROM verifik_produtomae WHERE ativo = 1')
            produtos = cursor_temp.fetchall()
            conn_temp.close()
            
            # Limpar produtos locais
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM produtos')
            
            # Inserir novos
            for prod in produtos:
                cursor.execute('INSERT INTO produtos (descricao_produto, marca, ativo) VALUES (?, ?, 1)', prod)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Erro ao importar: {e}")
    
    def carregar_produtos(self):
        """Carregar produtos do banco local"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, descricao_produto, marca FROM produtos WHERE ativo = 1 ORDER BY descricao_produto')
        produtos = cursor.fetchall()
        conn.close()
        return produtos


if __name__ == '__main__':
    VerifiKMobileApp().run()
