#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Novo modelo consolidado de imagens
Todas as imagens em uma tabela única com tipo_imagem
"""

novo_modelo = '''

class ImagemUnificada(models.Model):
    """
    Tabela unificada para TODAS as imagens do sistema
    Consolida: ImagemProduto, ImagemProcessada, ImagemAnotada, AnotacaoProduto
    """
    
    TIPO_IMAGEM_CHOICES = [
        ('original', 'Imagem Original de Treino'),
        ('processada', 'Processada (Fundo Removido)'),
        ('anotada', 'Anotada (Múltiplos Produtos)'),
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
        verbose_name="Tipo de Imagem"
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
        verbose_name="Descrição"
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
    
    # STATUS E ATIVAÇÃO
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
    
    # PROCESSAMENTO
    tipo_processamento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='',
        verbose_name="Tipo de Processamento",
        help_text="Ex: fundo_removido, rotacao_90, flip_horizontal"
    )
    
    # ANOTAÇÃO (BOUNDING BOXES)
    total_anotacoes = models.IntegerField(
        default=0,
        verbose_name="Total de Anotações",
        help_text="Quantos produtos foram anotados"
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
        verbose_name="Confiança (0-1)"
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
        verbose_name="Observações"
    )
    
    # TIMESTAMPS
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )
    
    data_envio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Envio"
    )
    
    data_aprovacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Aprovação"
    )
    
    class Meta:
        verbose_name = "Imagem Unificada"
        verbose_name_plural = "Imagens Unificadas"
        ordering = ['produto', 'tipo_imagem', 'created_at']
        indexes = [
            models.Index(fields=['produto', 'tipo_imagem']),
            models.Index(fields=['status']),
            models.Index(fields=['ativa']),
        ]
    
    def __str__(self):
        return f"{self.produto.descricao_produto} - {self.get_tipo_imagem_display()}"
    
    def salvar_dimensoes(self):
        """Atualiza width e height da imagem"""
        from PIL import Image
        try:
            img = Image.open(self.arquivo.path)
            self.width, self.height = img.size
            self.tamanho_bytes = self.arquivo.size
        except:
            pass
'''

print(novo_modelo)
