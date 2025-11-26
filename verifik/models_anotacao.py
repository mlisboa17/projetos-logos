# Sistema de Anotação de Imagens com Bounding Boxes
# Permite funcionários anotarem múltiplos produtos em uma única foto

from django.db import models
from django.conf import settings
from verifik.models import ProdutoMae

class ImagemAnotada(models.Model):
    """Imagem que pode conter múltiplos produtos anotados"""
    
    STATUS_CHOICES = [
        ('anotando', 'Em Anotação'),
        ('concluida', 'Concluída'),
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
        verbose_name="Total de anotações",
        help_text="Quantos produtos foram anotados nesta imagem"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Comentários sobre a imagem"
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
        verbose_name="Data de aprovação"
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
        help_text="Produto identificado nesta região"
    )
    
    # Coordenadas do bounding box (valores normalizados 0-1)
    bbox_x = models.FloatField(
        verbose_name="X (centro)",
        help_text="Posição X do centro do box (0-1)"
    )
    
    bbox_y = models.FloatField(
        verbose_name="Y (centro)",
        help_text="Posição Y do centro do box (0-1)"
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
        verbose_name="Confiança",
        help_text="Confiança na anotação (0-1)"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Notas sobre esta anotação específica"
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criação"
    )
    
    class Meta:
        verbose_name = "Anotação de Produto"
        verbose_name_plural = "Anotações de Produtos"
        ordering = ['imagem_anotada', 'id']
    
    def __str__(self):
        return f"{self.produto.descricao_produto} na imagem #{self.imagem_anotada.id}"
    
    def get_yolo_format(self):
        """Retorna a anotação no formato YOLO"""
        return f"{self.produto.id} {self.bbox_x} {self.bbox_y} {self.bbox_width} {self.bbox_height}"
