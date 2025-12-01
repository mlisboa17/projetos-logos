# -*- coding: utf-8 -*-
"""
Modelo consolidado de imagens para o sistema
Define ImagemUnificada que consolida todas as imagens do sistema
"""

from django.db import models
from django.conf import settings
from verifik.models import ProdutoMae


class ImagemUnificada(models.Model):
    """
    Tabela UNIFICADA para TODAS as imagens do sistema
    Consolida: ImagemProduto, ImagemProcessada, ImagemAnotada, AnotacaoProduto
    
    TIPOS DE IMAGEM:
    - original: Imagem original de treino
    - processada: Processada (fundo removido)
    - anotada: Anotada (múltiplos produtos com bounding boxes)
    - augmentada: Augmentada (transformações: rotacao, flip, zoom, brightness, etc)
    """
    
    TIPO_IMAGEM_CHOICES = [
        ('original', 'Imagem Original de Treino'),
        ('processada', 'Processada (Fundo Removido)'),
        ('anotada', 'Anotada (Múltiplos Produtos com BBox)'),
        ('augmentada', 'Augmentada (Transformações)'),
    ]
    
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('inativa', 'Inativa'),
        ('anotando', 'Em Anotação'),
        ('concluida', 'Concluída'),
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
        max_length=20, 
        choices=TIPO_IMAGEM_CHOICES,
        verbose_name="Tipo de Imagem",
        help_text="original, processada, anotada ou augmentada"
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
    
    # PROCESSAMENTO (fundo removido)
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
