from django.db import models

class ProcessadorImagens(models.Model):
    """Registro de processamentos realizados"""
    TIPOS_PROCESSAMENTO = [
        ('remover_fundo', 'Remover Fundo'),
        ('redimensionar', 'Redimensionar'),
        ('normalizar', 'Normalizar Cores'),
        ('aumentar_contraste', 'Aumentar Contraste'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPOS_PROCESSAMENTO)
    imagem_original = models.CharField(max_length=500, help_text="Caminho da imagem original")
    imagem_processada = models.CharField(max_length=500, help_text="Caminho da imagem processada")
    status = models.CharField(max_length=20, default='sucesso', choices=[
        ('sucesso', 'Sucesso'),
        ('erro', 'Erro'),
        ('processando', 'Processando'),
    ])
    mensagem_erro = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    parametros = models.JSONField(default=dict, help_text="Parâmetros usados no processamento")
    
    class Meta:
        ordering = ['-data_criacao']
        verbose_name = "Processador de Imagens"
        verbose_name_plural = "Processadores de Imagens"
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.status} - {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"
