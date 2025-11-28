"""
VerifiK Mobile - Sistema de Coleta de Imagens Android
Versão otimizada para dispositivos móveis com interface Kivy
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.widget import Widget
from kivy.utils import platform

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
import shutil


class ImageAnnotationWidget(Widget):
    """Widget para desenhar anotações na imagem"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.annotations = []
        self.current_annotation = None
        self.bind(size=self.update_canvas)
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.current_annotation = {
                'start': touch.pos,
                'end': touch.pos,
                'color': (1, 0, 0, 1)  # Vermelho
            }
            return True
        return False
        
    def on_touch_move(self, touch):
        if self.current_annotation:
            self.current_annotation['end'] = touch.pos
            self.update_canvas()
            return True
        return False
        
    def on_touch_up(self, touch):
        if self.current_annotation:
            # Adicionar anotação finalizada
            self.annotations.append(self.current_annotation.copy())
            self.current_annotation = None
            self.update_canvas()
            return True
        return False
        
    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Desenhar anotações finalizadas
            for ann in self.annotations:
                Color(*ann['color'])
                Line(rectangle=(
                    min(ann['start'][0], ann['end'][0]),
                    min(ann['start'][1], ann['end'][1]),
                    abs(ann['end'][0] - ann['start'][0]),
                    abs(ann['end'][1] - ann['start'][1])
                ), width=2)
            
            # Desenhar anotação atual
            if self.current_annotation:
                Color(1, 1, 0, 1)  # Amarelo para anotação atual
                Line(rectangle=(
                    min(self.current_annotation['start'][0], self.current_annotation['end'][0]),
                    min(self.current_annotation['start'][1], self.current_annotation['end'][1]),
                    abs(self.current_annotation['end'][0] - self.current_annotation['start'][0]),
                    abs(self.current_annotation['end'][1] - self.current_annotation['start'][1])
                ), width=3)
    
    def clear_annotations(self):
        self.annotations = []
        self.update_canvas()


class VerifiKMobileApp(App):
    """Aplicativo principal VerifiK Mobile"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.produtos = []
        self.produto_selecionado = None
        self.imagem_atual = None
        self.annotations_widget = None
        self.init_database()
        
    def build(self):
        """Constrói a interface principal"""
        # Layout principal
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Cabeçalho
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        header.add_widget(Label(
            text='📱 VerifiK Mobile - Coleta de Imagens',
            font_size='18sp',
            bold=True,
            color=(0.2, 0.3, 0.8, 1)
        ))
        main_layout.add_widget(header)
        
        # Container principal com scroll
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Seção 1: Seleção de Produto
        produto_section = self.create_produto_section()
        content.add_widget(produto_section)
        
        # Seção 2: Captura/Carregamento de Imagem
        image_section = self.create_image_section()
        content.add_widget(image_section)
        
        # Seção 3: Anotações
        annotation_section = self.create_annotation_section()
        content.add_widget(annotation_section)
        
        # Seção 4: Ações
        actions_section = self.create_actions_section()
        content.add_widget(actions_section)
        
        scroll.add_widget(content)
        main_layout.add_widget(scroll)
        
        # Carregar produtos
        self.load_produtos()
        
        return main_layout
    
    def create_produto_section(self):
        """Cria seção de seleção de produto"""
        section = BoxLayout(orientation='vertical', size_hint_y=None, height=120, spacing=5)
        
        # Título
        section.add_widget(Label(
            text='🎯 1. Selecione o Produto',
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30,
            color=(0.1, 0.6, 0.1, 1)
        ))
        
        # Spinner para produtos
        self.produto_spinner = Spinner(
            text='Carregando produtos...',
            size_hint_y=None,
            height=40,
            font_size='14sp'
        )
        self.produto_spinner.bind(text=self.on_produto_selected)
        section.add_widget(self.produto_spinner)
        
        # Botão atualizar
        btn_refresh = Button(
            text='🔄 Atualizar Lista',
            size_hint_y=None,
            height=40,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        btn_refresh.bind(on_press=lambda x: self.load_produtos())
        section.add_widget(btn_refresh)
        
        return section
    
    def create_image_section(self):
        """Cria seção de captura/carregamento de imagem"""
        section = BoxLayout(orientation='vertical', size_hint_y=None, height=300, spacing=5)
        
        # Título
        section.add_widget(Label(
            text='📷 2. Capture ou Carregue Imagem',
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30,
            color=(0.6, 0.1, 0.6, 1)
        ))
        
        # Botões de ação
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        btn_camera = Button(
            text='📷 Câmera',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_camera.bind(on_press=self.open_camera)
        
        btn_gallery = Button(
            text='🖼️ Galeria',
            background_color=(0.2, 0.8, 0.2, 1)
        )
        btn_gallery.bind(on_press=self.open_gallery)
        
        btn_layout.add_widget(btn_camera)
        btn_layout.add_widget(btn_gallery)
        section.add_widget(btn_layout)
        
        # Área de preview da imagem
        self.image_preview = Image(
            source='',
            size_hint_y=None,
            height=200
        )
        section.add_widget(self.image_preview)
        
        return section
    
    def create_annotation_section(self):
        """Cria seção de anotações"""
        section = BoxLayout(orientation='vertical', size_hint_y=None, height=350, spacing=5)
        
        # Título
        section.add_widget(Label(
            text='✏️ 3. Marque o Produto na Imagem',
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30,
            color=(0.8, 0.4, 0.1, 1)
        ))
        
        # Instruções
        section.add_widget(Label(
            text='Toque e arraste na imagem para marcar onde está o produto',
            font_size='12sp',
            size_hint_y=None,
            height=25,
            color=(0.5, 0.5, 0.5, 1)
        ))
        
        # Widget de anotação
        self.annotations_widget = ImageAnnotationWidget(
            size_hint_y=None,
            height=250
        )
        section.add_widget(self.annotations_widget)
        
        # Botão limpar anotações
        btn_clear = Button(
            text='🧽 Limpar Marcações',
            size_hint_y=None,
            height=40,
            background_color=(0.7, 0.7, 0.7, 1)
        )
        btn_clear.bind(on_press=self.clear_annotations)
        section.add_widget(btn_clear)
        
        return section
    
    def create_actions_section(self):
        """Cria seção de ações finais"""
        section = BoxLayout(orientation='vertical', size_hint_y=None, height=200, spacing=5)
        
        # Título
        section.add_widget(Label(
            text='💾 4. Salvar e Exportar',
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30,
            color=(0.1, 0.1, 0.8, 1)
        ))
        
        # Campo observações
        section.add_widget(Label(
            text='Observações (opcional):',
            font_size='12sp',
            size_hint_y=None,
            height=25,
            halign='left'
        ))
        
        self.observacoes_input = TextInput(
            text='',
            multiline=True,
            size_hint_y=None,
            height=60
        )
        section.add_widget(self.observacoes_input)
        
        # Botões de ação
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        btn_save = Button(
            text='💾 Salvar Anotação',
            background_color=(0.1, 0.7, 0.1, 1)
        )
        btn_save.bind(on_press=self.save_annotation)
        
        btn_export = Button(
            text='📤 Exportar Dados',
            background_color=(0.8, 0.6, 0.1, 1)
        )
        btn_export.bind(on_press=self.export_data)
        
        btn_layout.add_widget(btn_save)
        btn_layout.add_widget(btn_export)
        section.add_widget(btn_layout)
        
        return section
    
    def init_database(self):
        """Inicializa o banco de dados SQLite"""
        # Definir caminho do banco baseado na plataforma
        if platform == 'android':
            from android.storage import primary_external_storage_path
            storage_path = primary_external_storage_path()
            self.db_path = os.path.join(storage_path, 'VerifiK', 'coleta_mobile.db')
        else:
            # Para desenvolvimento/teste
            self.db_path = 'coleta_mobile.db'
        
        # Criar diretório se necessário
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Criar tabelas
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao_produto TEXT NOT NULL,
                marca TEXT,
                ativo INTEGER DEFAULT 1,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de imagens coletadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imagens_coletadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER,
                caminho_imagem TEXT,
                anotacoes TEXT,
                observacoes TEXT,
                data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP,
                sincronizado INTEGER DEFAULT 0,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Adicionar alguns produtos padrão se não existirem
        self.add_default_produtos()
    
    def add_default_produtos(self):
        """Adiciona produtos padrão se o banco estiver vazio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM produtos')
        count = cursor.fetchone()[0]
        
        if count == 0:
            produtos_default = [
                ('Coca-Cola 350ml', 'Coca-Cola'),
                ('Guaraná Antarctica 350ml', 'Antarctica'),
                ('Água Crystal 500ml', 'Crystal'),
                ('Biscoito Passatempo', 'Nestlé'),
                ('Chocolate Bis', 'Lacta'),
            ]
            
            cursor.executemany(
                'INSERT INTO produtos (descricao_produto, marca) VALUES (?, ?)',
                produtos_default
            )
            conn.commit()
        
        conn.close()
    
    def load_produtos(self):
        """Carrega produtos do banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, descricao_produto, marca FROM produtos WHERE ativo = 1 ORDER BY descricao_produto')
        self.produtos = cursor.fetchall()
        conn.close()
        
        # Atualizar spinner
        produtos_text = ['Selecione um produto...']
        for produto in self.produtos:
            desc = produto[1]
            if produto[2]:  # Se tem marca
                desc += f' - {produto[2]}'
            produtos_text.append(desc)
        
        self.produto_spinner.values = produtos_text
        if len(produtos_text) > 1:
            self.produto_spinner.text = produtos_text[0]
    
    def on_produto_selected(self, spinner, text):
        """Callback quando produto é selecionado"""
        if text != 'Selecione um produto...':
            # Encontrar produto correspondente
            for produto in self.produtos:
                desc = produto[1]
                if produto[2]:
                    desc += f' - {produto[2]}'
                if desc == text:
                    self.produto_selecionado = produto
                    break
    
    def open_camera(self, instance):
        """Abre câmera para capturar foto"""
        if platform == 'android':
            # Usar camera Android
            from android import activity, mActivity
            from jnius import autoclass, cast
            
            # Intent para capturar foto
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')
            
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            mActivity.startActivityForResult(intent, 1001)
        else:
            # Para desenvolvimento - mostrar popup informativo
            self.show_popup('Câmera', 'Câmera não disponível no modo desenvolvimento')
    
    def open_gallery(self, instance):
        """Abre galeria para selecionar imagem"""
        # Criar popup com file chooser
        content = BoxLayout(orientation='vertical')
        
        file_chooser = FileChooserIconView(
            filters=['*.png', '*.jpg', '*.jpeg'],
            path='/'
        )
        content.add_widget(file_chooser)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        btn_select = Button(text='Selecionar')
        btn_cancel = Button(text='Cancelar')
        
        btn_layout.add_widget(btn_select)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='Selecionar Imagem',
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        def on_select(instance):
            if file_chooser.selection:
                self.load_image(file_chooser.selection[0])
            popup.dismiss()
        
        btn_select.bind(on_press=on_select)
        btn_cancel.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def load_image(self, image_path):
        """Carrega imagem selecionada"""
        self.imagem_atual = image_path
        self.image_preview.source = image_path
        
        # Limpar anotações anteriores
        if self.annotations_widget:
            self.annotations_widget.clear_annotations()
    
    def clear_annotations(self, instance):
        """Limpa todas as anotações"""
        if self.annotations_widget:
            self.annotations_widget.clear_annotations()
    
    def save_annotation(self, instance):
        """Salva anotação no banco de dados"""
        if not self.produto_selecionado:
            self.show_popup('Erro', 'Selecione um produto primeiro!')
            return
        
        if not self.imagem_atual:
            self.show_popup('Erro', 'Carregue uma imagem primeiro!')
            return
        
        if not self.annotations_widget.annotations:
            self.show_popup('Erro', 'Faça pelo menos uma marcação na imagem!')
            return
        
        # Salvar no banco
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Converter anotações para JSON
        anotacoes_json = json.dumps(self.annotations_widget.annotations)
        
        cursor.execute('''
            INSERT INTO imagens_coletadas 
            (produto_id, caminho_imagem, anotacoes, observacoes) 
            VALUES (?, ?, ?, ?)
        ''', (
            self.produto_selecionado[0],
            self.imagem_atual,
            anotacoes_json,
            self.observacoes_input.text
        ))
        
        conn.commit()
        conn.close()
        
        self.show_popup('Sucesso', 'Anotação salva com sucesso!')
        
        # Limpar para próxima anotação
        self.clear_annotations(None)
        self.observacoes_input.text = ''
    
    def export_data(self, instance):
        """Exporta dados coletados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM imagens_coletadas WHERE sincronizado = 0
        ''')
        count = cursor.fetchone()[0]
        
        if count == 0:
            self.show_popup('Info', 'Nenhum dado novo para exportar')
            conn.close()
            return
        
        # Preparar dados para exportação
        cursor.execute('''
            SELECT ic.*, p.descricao_produto, p.marca
            FROM imagens_coletadas ic
            JOIN produtos p ON ic.produto_id = p.id
            WHERE ic.sincronizado = 0
        ''')
        dados = cursor.fetchall()
        
        # Criar estrutura de exportação
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_imagens': len(dados),
            'imagens': []
        }
        
        for row in dados:
            export_data['imagens'].append({
                'id': row[0],
                'produto_id': row[1],
                'produto_nome': row[6],
                'produto_marca': row[7],
                'caminho_imagem': row[2],
                'anotacoes': json.loads(row[3]) if row[3] else [],
                'observacoes': row[4],
                'data_coleta': row[5]
            })
        
        # Salvar arquivo de exportação
        if platform == 'android':
            from android.storage import primary_external_storage_path
            storage_path = primary_external_storage_path()
            export_path = os.path.join(storage_path, 'VerifiK', 'Exports')
        else:
            export_path = 'exports'
        
        os.makedirs(export_path, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'verifik_export_{timestamp}.json'
        filepath = os.path.join(export_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Marcar como sincronizado
        cursor.execute('UPDATE imagens_coletadas SET sincronizado = 1 WHERE sincronizado = 0')
        conn.commit()
        conn.close()
        
        self.show_popup('Sucesso', f'Dados exportados para:\n{filepath}\n\n{count} imagens processadas')
    
    def show_popup(self, title, message):
        """Mostra popup informativo"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, text_size=(300, None)))
        
        btn_ok = Button(text='OK', size_hint_y=None, height=50)
        content.add_widget(btn_ok)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.6)
        )
        
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()


class VerifiKMobile(VerifiKMobileApp):
    """Classe principal do app"""
    pass


if __name__ == '__main__':
    VerifiKMobile().run()