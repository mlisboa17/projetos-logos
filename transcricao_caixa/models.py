from django.db import models
from django.conf import settings
from django.utils import timezone


class Empresa(models.Model):
    """Empresas/estabelecimentos que fazem fechamento de caixa"""
    nome = models.CharField(max_length=200, verbose_name="Nome da Empresa")
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True, verbose_name="CNPJ")
    endereco = models.TextField(blank=True, verbose_name="Endereço")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class TipoDocumento(models.Model):
    """Tipos de documentos que podem ser transcritos (Nota Fiscal, Cupom, Recibo, etc.)"""
    nome = models.CharField(max_length=100, verbose_name="Tipo de Documento")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    padrao_ocr = models.TextField(blank=True, help_text="Padrão regex ou palavras-chave para identificação automática")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class FechamentoCaixa(models.Model):
    """Fechamento de caixa de uma empresa em uma data específica"""
    
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('em_processamento', 'Em Processamento'),
        ('aguardando_revisao', 'Aguardando Revisão'),
        ('revisado', 'Revisado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='fechamentos', verbose_name="Empresa")
    data_fechamento = models.DateField(verbose_name="Data do Fechamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho', verbose_name="Status")
    
    # Valores calculados
    total_vendas = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total de Vendas")
    total_despesas = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total de Despesas")
    total_liquido = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Líquido")
    
    # Contadores
    total_documentos = models.IntegerField(default=0, verbose_name="Total de Documentos")
    documentos_processados = models.IntegerField(default=0, verbose_name="Documentos Processados")
    documentos_revisados = models.IntegerField(default=0, verbose_name="Documentos Revisados")
    
    # Observações
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Auditoria
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='fechamentos_criados', verbose_name="Criado por")
    revisado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='fechamentos_revisados', verbose_name="Revisado por")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    concluido_em = models.DateTimeField(null=True, blank=True, verbose_name="Concluído em")
    
    class Meta:
        verbose_name = "Fechamento de Caixa"
        verbose_name_plural = "Fechamentos de Caixa"
        ordering = ['-data_fechamento', '-criado_em']
        unique_together = ['empresa', 'data_fechamento']
    
    def __str__(self):
        return f"{self.empresa.nome} - {self.data_fechamento.strftime('%d/%m/%Y')}"
    
    def calcular_totais(self):
        """Recalcula os totais baseado nos documentos transcritos"""
        documentos = self.documentos_transcritos.all()
        
        self.total_vendas = sum(d.valor_total for d in documentos if d.tipo_movimento == 'entrada')
        self.total_despesas = sum(d.valor_total for d in documentos if d.tipo_movimento == 'saida')
        self.total_liquido = self.total_vendas - self.total_despesas
        self.total_documentos = documentos.count()
        self.documentos_processados = documentos.filter(status='processado').count()
        self.documentos_revisados = documentos.filter(status='revisado').count()
        
        self.save()


class DocumentoTranscrito(models.Model):
    """Documento individual (nota, cupom, etc.) transcrito de uma imagem"""
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('processado', 'Processado'),
        ('erro', 'Erro'),
        ('revisado', 'Revisado'),
        ('rejeitado', 'Rejeitado'),
    ]
    
    TIPO_MOVIMENTO_CHOICES = [
        ('entrada', 'Entrada (Venda)'),
        ('saida', 'Saída (Despesa)'),
    ]
    
    fechamento = models.ForeignKey(FechamentoCaixa, on_delete=models.CASCADE, related_name='documentos_transcritos', verbose_name="Fechamento")
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tipo de Documento")
    tipo_movimento = models.CharField(max_length=10, choices=TIPO_MOVIMENTO_CHOICES, default='entrada', verbose_name="Tipo de Movimento")
    
    # Imagem original
    imagem = models.ImageField(upload_to='transcricao_caixa/documentos/%Y/%m/%d/', verbose_name="Imagem do Documento")
    imagem_processada = models.ImageField(upload_to='transcricao_caixa/processadas/%Y/%m/%d/', null=True, blank=True, verbose_name="Imagem Processada")
    
    # Dados transcritos
    texto_completo = models.TextField(blank=True, verbose_name="Texto Completo (OCR)")
    numero_documento = models.CharField(max_length=100, blank=True, verbose_name="Número do Documento")
    data_documento = models.DateField(null=True, blank=True, verbose_name="Data do Documento")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Total")
    
    # Campos extraídos (JSON para flexibilidade)
    dados_extraidos = models.JSONField(default=dict, blank=True, verbose_name="Dados Extraídos", help_text="Campos específicos extraídos do documento")
    
    # Status e confiança
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    confianca_ocr = models.FloatField(default=0, verbose_name="Confiança do OCR (%)", help_text="Percentual de confiança na transcrição")
    
    # Observações e correções
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    correcoes_manuais = models.TextField(blank=True, verbose_name="Correções Manuais")
    
    # Auditoria
    processado_em = models.DateTimeField(null=True, blank=True, verbose_name="Processado em")
    revisado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos_revisados', verbose_name="Revisado por")
    revisado_em = models.DateTimeField(null=True, blank=True, verbose_name="Revisado em")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Documento Transcrito"
        verbose_name_plural = "Documentos Transcritos"
        ordering = ['-criado_em']
    
    def __str__(self):
        tipo = self.tipo_documento.nome if self.tipo_documento else "Documento"
        return f"{tipo} - R$ {self.valor_total} - {self.status}"
    
    def marcar_como_processado(self):
        """Marca documento como processado e atualiza totais do fechamento"""
        self.status = 'processado'
        self.processado_em = timezone.now()
        self.save()
        
        # Atualizar totais do fechamento
        self.fechamento.calcular_totais()
    
    def marcar_como_revisado(self, usuario):
        """Marca documento como revisado por um usuário"""
        self.status = 'revisado'
        self.revisado_por = usuario
        self.revisado_em = timezone.now()
        self.save()
        
        # Atualizar totais do fechamento
        self.fechamento.calcular_totais()


class ItemDocumento(models.Model):
    """Itens individuais de um documento (produtos/serviços em uma nota)"""
    documento = models.ForeignKey(DocumentoTranscrito, on_delete=models.CASCADE, related_name='itens', verbose_name="Documento")
    
    descricao = models.CharField(max_length=500, verbose_name="Descrição")
    quantidade = models.DecimalField(max_digits=10, decimal_places=3, default=1, verbose_name="Quantidade")
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Unitário")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Total")
    
    # Dados adicionais
    codigo = models.CharField(max_length=100, blank=True, verbose_name="Código")
    unidade = models.CharField(max_length=10, blank=True, verbose_name="Unidade")
    
    # Ordem no documento
    ordem = models.IntegerField(default=0, verbose_name="Ordem")
    
    class Meta:
        verbose_name = "Item do Documento"
        verbose_name_plural = "Itens do Documento"
        ordering = ['documento', 'ordem']
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor_total}"
    
    def save(self, *args, **kwargs):
        # Calcular valor total automaticamente
        self.valor_total = self.quantidade * self.valor_unitario
        super().save(*args, **kwargs)
