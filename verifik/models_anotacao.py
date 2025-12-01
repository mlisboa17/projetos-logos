# -*- coding: utf-8 -*-
"""
Modelos de Anotacao e Imagem Unificada
Sistema consolidado para todas as imagens
"""

from django.db import models
from django.conf import settings
from verifik.models import ProdutoMae


class ImagemAnotada(models.Model):
    """Imagem que pode conter múltiplos produtos anotados com bounding boxes"""
    
    STATUS_CHOICES = [
        ('anotando', 'Em Anotacao'),
        ('concluida', 'Concluida'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]
    
    imagem = models.ImageField(
        upload_to='produtos/anotacoes/%Y/%m/%d/',
        verbose_name="Imagem Original",
        help_text="Foto contendo um ou mais produtos"
    )
    
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='imagens_anotadas',
        verbose_name="Enviado por"
    )
    
    data_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de envio"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='anotando',
        verbose_name="Status"
    )
    
    total_anotacoes = models.IntegerField(
        default=0,
        verbose_name="Total de anotacoes",
        help_text="Quantos produtos foram anotados nesta imagem"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observacoes",
        help_text="Comentarios sobre a imagem"
    )
    
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imagens_anotadas_aprovadas',
        verbose_name="Aprovado por"
    )
    
    data_aprovacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de aprovacao"
    )
    
    class Meta:
        verbose_name = "Imagem Anotada"
        verbose_name_plural = "Imagens Anotadas"
        ordering = ['-data_envio']
    
    def __str__(self):
        return f"Imagem #{self.id} - {self.total_anotacoes} produtos - {self.enviado_por}"


class AnotacaoProduto(models.Model):
    """Bounding box de um produto em uma imagem"""
    
    imagem_anotada = models.ForeignKey(
        ImagemAnotada,
        on_delete=models.CASCADE,
        related_name='anotacoes',
        verbose_name="Imagem"
    )
    
    produto = models.ForeignKey(
        ProdutoMae,
        on_delete=models.CASCADE,
        verbose_name="Produto",
        help_text="Produto identificado nesta regiao"
    )
    
    # Coordenadas do bounding box (valores normalizados 0-1)
    bbox_x = models.FloatField(
        verbose_name="X (centro)",
        help_text="Posicao X do centro do box (0-1)"
    )
    
    bbox_y = models.FloatField(
        verbose_name="Y (centro)",
        help_text="Posicao Y do centro do box (0-1)"
    )
    
    bbox_width = models.FloatField(
        verbose_name="Largura",
        help_text="Largura do box (0-1)"
    )
    
    bbox_height = models.FloatField(
        verbose_name="Altura",
        help_text="Altura do box (0-1)"
    )
    
    confianca = models.FloatField(
        default=1.0,
        verbose_name="Confianca",
        help_text="Confianca na anotacao (0-1)"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observacoes",
        help_text="Notas sobre esta anotacao especifica"
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criacao"
    )
    
    class Meta:
        verbose_name = "Anotacao de Produto"
        verbose_name_plural = "Anotacoes de Produtos"
        ordering = ['imagem_anotada', 'id']
    
    def __str__(self):
        return f"{self.produto.descricao_produto} na imagem #{self.imagem_anotada.id}"
    
    def get_yolo_format(self):
        """Retorna a anotacao no formato YOLO"""
        return f"{self.produto.id} {self.bbox_x} {self.bbox_y} {self.bbox_width} {self.bbox_height}"


class ImagemProcessada(models.Model):
    """Imagens processadas com fundo removido vinculadas as imagens originais"""
    from verifik.models import ImagemProduto
    
    imagem_original = models.ForeignKey(ImagemProduto, on_delete=models.CASCADE, related_name='imagens_processadas')
    imagem_processada = models.ImageField(upload_to='processadas_sem_fundo/')
    tipo_processamento = models.CharField(max_length=50, default='fundo_removido')
    descricao = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagem Processada'
        verbose_name_plural = 'Imagens Processadas'
        ordering = ['-data_criacao']

    def __str__(self):
        return f'{self.imagem_original.produto.descricao_produto} - {self.tipo_processamento}'


# ============================================================================
# MODELO UNIFICADO - CONSOLIDA TODAS AS IMAGENS
# ============================================================================

class ImagemUnificada(models.Model):
    """
    TABELA UNIFICADA para TODAS as imagens do sistema.
    
    Consolida: ImagemProduto, ImagemProcessada, ImagemAnotada, AnotacaoProduto
    
    TIPOS DE IMAGEM (extensivel):
    - original: Imagem original de treino
    - processada: Processada (fundo removido)
    - anotada: Anotada (multiplos produtos com bounding boxes)
    - augmentada: Augmentada (transformacoes: rotacao, flip, zoom, brightness, etc)
    - [... outros tipos podem ser adicionados no futuro]
    """
    
    # Deixar tipo_imagem aberto para extensoes futuras
    TIPO_IMAGEM_CHOICES = [
        ('original', 'Imagem Original de Treino'),
        ('processada', 'Processada (Fundo Removido)'),
        ('anotada', 'Anotada (Multiplos Produtos com BBox)'),
        ('augmentada', 'Augmentada (Transformacoes)'),
        # Espaco para novos tipos
    ]
    
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('inativa', 'Inativa'),
        ('anotando', 'Em Anotacao'),
        ('concluida', 'Concluida'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]
    
    # RELACIONAMENTOS PRINCIPAIS
    produto = models.ForeignKey(
        ProdutoMae, 
        on_delete=models.CASCADE, 
        related_name='imagens_unificadas',
        verbose_name="Produto"
    )
    
    # TIPO E ORIGEM
    tipo_imagem = models.CharField(
        max_length=50,  # Aumentar para permitir novos tipos
        choices=TIPO_IMAGEM_CHOICES,
        verbose_name="Tipo de Imagem",
        help_text="Tipo: original, processada, anotada, augmentada, etc"
    )
    
    imagem_original = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='derivadas',
        verbose_name="Imagem Original",
        help_text="Se processada/augmentada, referencia a imagem original"
    )
    
    # ARQUIVO
    arquivo = models.ImageField(
        upload_to='imagens_unificadas/%Y/%m/%d/',
        verbose_name="Arquivo de Imagem"
    )
    
    # METADADOS DE IMAGEM
    descricao = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Descricao"
    )
    
    ordem = models.IntegerField(
        default=0,
        verbose_name="Ordem"
    )
    
    width = models.IntegerField(
        default=0,
        verbose_name="Largura (px)"
    )
    
    height = models.IntegerField(
        default=0,
        verbose_name="Altura (px)"
    )
    
    tamanho_bytes = models.IntegerField(
        default=0,
        verbose_name="Tamanho (bytes)"
    )
    
    # STATUS E ATIVACAO
    ativa = models.BooleanField(
        default=True,
        verbose_name="Ativa"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativa',
        verbose_name="Status"
    )
    
    # PROCESSAMENTO (fundo removido, etc)
    tipo_processamento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='',
        verbose_name="Tipo de Processamento",
        help_text="Ex: fundo_removido"
    )
    
    # AUGMENTATION
    foi_augmentada = models.BooleanField(
        default=False,
        verbose_name="Foi Augmentada"
    )
    
    tipo_augmentacao = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Tipo de Augmentacao",
        help_text="Ex: rotacao_45, flip_horizontal, zoom_1.2, brightness_0.8"
    )
    
    # ANOTACAO (BOUNDING BOXES)
    total_anotacoes = models.IntegerField(
        default=0,
        verbose_name="Total de Anotacoes",
        help_text="Quantos produtos foram anotados (0 se nao anotada)"
    )
    
    bbox_x = models.FloatField(
        default=0.0,
        verbose_name="BBox Centro X (0-1)"
    )
    
    bbox_y = models.FloatField(
        default=0.0,
        verbose_name="BBox Centro Y (0-1)"
    )
    
    bbox_width = models.FloatField(
        default=0.0,
        verbose_name="BBox Largura (0-1)"
    )
    
    bbox_height = models.FloatField(
        default=0.0,
        verbose_name="BBox Altura (0-1)"
    )
    
    confianca = models.FloatField(
        default=0.0,
        verbose_name="Confianca (0-1)"
    )
    
    # RASTREAMENTO DE TREINO - IMPORTANTE!
    num_treinos = models.IntegerField(
        default=0,
        verbose_name="Vezes Treinada",
        help_text="Quantas vezes esta imagem foi usada em treino"
    )
    
    ultimo_treino = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ultimo Treino"
    )
    
    versao_modelo = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name="Versao do Modelo",
        help_text="Versao do modelo YOLO em que foi treinada"
    )
    
    # UPLOAD E RASTREAMENTO
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imagens_unificadas',
        verbose_name="Enviado por"
    )
    
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imagens_unificadas_aprovadas',
        verbose_name="Aprovado por"
    )
    
    observacoes = models.TextField(
        blank=True,
        default='',
        verbose_name="Observacoes"
    )
    
    # TIMESTAMPS
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criacao"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualizacao"
    )
    
    data_envio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Envio"
    )
    
    data_aprovacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Aprovacao"
    )
    
    class Meta:
        verbose_name = "Imagem Unificada"
        verbose_name_plural = "Imagens Unificadas"
        ordering = ['produto', 'tipo_imagem', 'created_at']
        indexes = [
            models.Index(fields=['produto', 'tipo_imagem']),
            models.Index(fields=['status']),
            models.Index(fields=['ativa']),
            models.Index(fields=['num_treinos']),
        ]
    
    def __str__(self):
        return f"{self.produto.descricao_produto} - {self.get_tipo_imagem_display()}"


class HistoricoTreino(models.Model):
    """Rastreia cada sessao de treinamento e quais imagens foram usadas"""
    
    STATUS_TREINO = [
        ('iniciado', 'Iniciado'),
        ('processando', 'Processando'),
        ('concluido', 'Concluido'),
        ('erro', 'Erro'),
    ]
    
    versao_modelo = models.CharField(
        max_length=50,
        verbose_name="Versao do Modelo",
        help_text="Ex: yolov8n_v1, yolov8n_v2"
    )
    
    data_inicio = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Inicio"
    )
    
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Conclusao"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_TREINO,
        default='iniciado',
        verbose_name="Status"
    )
    
    total_imagens = models.IntegerField(
        default=0,
        verbose_name="Total de Imagens Usadas"
    )
    
    total_produtos = models.IntegerField(
        default=0,
        verbose_name="Total de Produtos"
    )
    
    epocas = models.IntegerField(
        default=50,
        verbose_name="Epocas de Treino"
    )
    
    acuracia = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Acuracia Final"
    )
    
    perda = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Perda Final"
    )
    
    parametros = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Parametros do Treino"
    )
    
    observacoes = models.TextField(
        blank=True,
        default='',
        verbose_name="Observacoes"
    )
    
    class Meta:
        verbose_name = "Historico de Treino"
        verbose_name_plural = "Historicos de Treino"
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f"Treino {self.versao_modelo} - {self.data_inicio.strftime('%d/%m/%Y %H:%M')}"


class ImagemTreino(models.Model):
    """Vincula imagens ao historico de treino (muitos-para-muitos com rastreamento)"""
    
    imagem = models.ForeignKey(
        ImagemUnificada,
        on_delete=models.CASCADE,
        related_name='treinos',
        verbose_name="Imagem"
    )
    
    historico_treino = models.ForeignKey(
        HistoricoTreino,
        on_delete=models.CASCADE,
        related_name='imagens',
        verbose_name="Treino"
    )
    
    foi_usada = models.BooleanField(
        default=True,
        verbose_name="Foi Usada no Treino"
    )
    
    data_adicao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Adicao"
    )
    
    class Meta:
        verbose_name = "Imagem em Treino"
        verbose_name_plural = "Imagens em Treino"
        unique_together = [['imagem', 'historico_treino']]
    
    def __str__(self):
        return f"{self.imagem} - {self.historico_treino.versao_modelo}"
