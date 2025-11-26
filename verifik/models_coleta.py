# Sistema de Coleta de Imagens
# Permite funcionários enviarem fotos de produtos para revisão

from django.db import models
from django.conf import settings
from verifik.models import ProdutoMae

class ImagemProdutoPendente(models.Model):
    """Imagens enviadas por funcionários aguardando aprovação"""
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]
    
    produto = models.ForeignKey(
        ProdutoMae,
        on_delete=models.CASCADE,
        verbose_name="Produto",
        help_text="Produto ao qual a imagem pertence"
    )
    
    imagem = models.ImageField(
        upload_to='produtos/pendentes/%Y/%m/%d/',
        verbose_name="Imagem",
        help_text="Foto do produto"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name="Status"
    )
    
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='imagens_enviadas',
        verbose_name="Enviado por"
    )
    
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imagens_aprovadas',
        verbose_name="Aprovado por"
    )
    
    data_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de envio"
    )
    
    data_aprovacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de aprovação"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Comentários sobre a foto"
    )
    
    motivo_rejeicao = models.TextField(
        blank=True,
        verbose_name="Motivo da rejeição",
        help_text="Razão pela qual a imagem foi rejeitada"
    )
    
    qualidade = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Qualidade (1-5)",
        help_text="Avaliação da qualidade da imagem"
    )
    
    lote = models.ForeignKey(
        'LoteFotos',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imagens',
        verbose_name="Lote"
    )
    
    class Meta:
        verbose_name = "Imagem Pendente"
        verbose_name_plural = "Imagens Pendentes"
        ordering = ['-data_envio']
    
    def __str__(self):
        return f"{self.produto.descricao_produto} - {self.enviado_por} - {self.status}"


class LoteFotos(models.Model):
    """Agrupa várias fotos enviadas de uma vez"""
    
    nome = models.CharField(
        max_length=200,
        verbose_name="Nome do lote",
        help_text="Ex: Coleta Loja Centro - 26/11/2025"
    )
    
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Enviado por"
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de criação"
    )
    
    total_imagens = models.IntegerField(
        default=0,
        verbose_name="Total de imagens"
    )
    
    imagens_aprovadas = models.IntegerField(
        default=0,
        verbose_name="Imagens aprovadas"
    )
    
    imagens_rejeitadas = models.IntegerField(
        default=0,
        verbose_name="Imagens rejeitadas"
    )
    
    class Meta:
        verbose_name = "Lote de Fotos"
        verbose_name_plural = "Lotes de Fotos"
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.nome} - {self.total_imagens} fotos"
