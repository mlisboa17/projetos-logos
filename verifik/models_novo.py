from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ==============================================
# 🧑 FUNCIONÁRIOS E USUÁRIOS
# ==============================================

class Funcionario(models.Model):
    """Operadores de caixa e outros funcionários"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome_completo = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    cargo = models.CharField(max_length=100)
    matricula = models.CharField(max_length=50, unique=True)
    ativo = models.BooleanField(default=True)
    data_admissao = models.DateField()
    data_demissao = models.DateField(null=True, blank=True)
    foto = models.ImageField(upload_to='funcionarios/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.matricula})"


class PerfilGestor(models.Model):
    """Usuários gestores que acessam o painel"""
    NIVEL_CHOICES = [
        ('SUPERVISOR', 'Supervisor'),
        ('GERENTE', 'Gerente'),
        ('ADMINISTRADOR', 'Administrador'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nivel_acesso = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    telefone = models.CharField(max_length=20)
    receber_alertas_email = models.BooleanField(default=True)
    receber_alertas_whatsapp = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Gestor'
        verbose_name_plural = 'Perfis de Gestores'

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.nivel_acesso}"


# ==============================================
# 🛒 OPERAÇÕES E PRODUTOS
# ==============================================

class Produto(models.Model):
    """Catálogo de produtos da loja"""
    codigo_barras = models.CharField(max_length=50, unique=True)
    descricao_produto = models.CharField(max_length=255)
    marca = models.CharField(max_length=100, blank=True, null=True)
    tipo = models.CharField(max_length=100, blank=True, null=True)  # Ex: Refrigerante, Chocolate, Salgadinho
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem_referencia = models.ImageField(upload_to='produtos/', null=True, blank=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['descricao_produto']

    def __str__(self):
        return f"{self.descricao_produto}"


class ImagemProduto(models.Model):
    """Múltiplas imagens para treinamento da IA"""
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='imagens_treino')
    imagem = models.ImageField(upload_to='produtos/treino/')
    descricao = models.CharField(max_length=255, blank=True, null=True)
    ordem = models.IntegerField(default=0)
    ativa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagem de Produto'
        verbose_name_plural = 'Imagens de Produtos'
        ordering = ['produto', 'ordem', 'id']

    def __str__(self):
        return f"{self.produto.descricao_produto} - Imagem {self.ordem}"


class OperacaoVenda(models.Model):
    """Operações registradas no sistema de vendas (PDV)"""
    STATUS_CHOICES = [
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
        ('PENDENTE', 'Pendente'),
    ]
    
    numero_venda = models.CharField(max_length=50, unique=True)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True)
    data_hora = models.DateTimeField(default=timezone.now)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONCLUIDA')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Operação de Venda'
        verbose_name_plural = 'Operações de Vendas'
        ordering = ['-data_hora']

    def __str__(self):
        return f"Venda {self.numero_venda} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class ItemVenda(models.Model):
    """Itens de cada operação de venda"""
    operacao = models.ForeignKey(OperacaoVenda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Item de Venda'
        verbose_name_plural = 'Itens de Venda'

    def __str__(self):
        return f"{self.produto.descricao_produto} x{self.quantidade}"


# ==============================================
# 🎥 CÂMERAS E DETECÇÕES
# ==============================================

class Camera(models.Model):
    """Câmeras de segurança monitoradas"""
    nome = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    url_stream = models.URLField(max_length=500, null=True, blank=True)
    ativa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Câmera'
        verbose_name_plural = 'Câmeras'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.localizacao}"


class CameraStatus(models.Model):
    """Status de operação das câmeras"""
    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('ERRO', 'Erro'),
    ]
    
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='status_historico')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    mensagem = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Status de Câmera'
        verbose_name_plural = 'Status de Câmeras'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.camera.nome} - {self.status}"


class DeteccaoProduto(models.Model):
    """Produtos detectados pela IA nas câmeras"""
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='deteccoes')
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField()
    confianca = models.FloatField()  # 0.0 a 1.0
    frame_imagem = models.ImageField(upload_to='deteccoes/', null=True, blank=True)
    bbox_x = models.IntegerField()  # Bounding box
    bbox_y = models.IntegerField()
    bbox_width = models.IntegerField()
    bbox_height = models.IntegerField()
    verificada = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Detecção de Produto'
        verbose_name_plural = 'Detecções de Produtos'
        ordering = ['-timestamp']

    def __str__(self):
        produto_nome = self.produto.descricao_produto if self.produto else "Desconhecido"
        return f"{produto_nome} - {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"


# ==============================================
# 🚨 INCIDENTES E ALERTAS
# ==============================================

class Incidente(models.Model):
    """Incidentes de fraude detectados"""
    TIPO_CHOICES = [
        ('PRODUTO_NAO_REGISTRADO', 'Produto não registrado no PDV'),
        ('DIVERGENCIA_QUANTIDADE', 'Divergência de quantidade'),
        ('DIVERGENCIA_PRODUTO', 'Produto diferente do registrado'),
        ('HORARIO_SUSPEITO', 'Movimentação em horário suspeito'),
    ]
    
    SEVERIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
    ]
    
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('EM_ANALISE', 'Em Análise'),
        ('RESOLVIDO', 'Resolvido'),
        ('FALSO_POSITIVO', 'Falso Positivo'),
    ]
    
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    severidade = models.CharField(max_length=20, choices=SEVERIDADE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')
    deteccao = models.ForeignKey(DeteccaoProduto, on_delete=models.CASCADE, related_name='incidentes')
    operacao_venda = models.ForeignKey(OperacaoVenda, on_delete=models.SET_NULL, null=True, blank=True)
    descricao = models.TextField()
    responsavel_analise = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)
    data_resolucao = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Incidente'
        verbose_name_plural = 'Incidentes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.created_at.strftime('%d/%m/%Y')}"


class EvidenciaIncidente(models.Model):
    """Evidências anexadas aos incidentes"""
    incidente = models.ForeignKey(Incidente, on_delete=models.CASCADE, related_name='evidencias')
    tipo_arquivo = models.CharField(max_length=50)  # Ex: imagem, vídeo
    arquivo = models.FileField(upload_to='evidencias/')
    descricao = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evidência de Incidente'
        verbose_name_plural = 'Evidências de Incidentes'

    def __str__(self):
        return f"Evidência - {self.incidente.id}"


class Alerta(models.Model):
    """Alertas enviados para gestores"""
    CANAL_CHOICES = [
        ('EMAIL', 'E-mail'),
        ('WHATSAPP', 'WhatsApp'),
        ('SISTEMA', 'Notificação no Sistema'),
    ]
    
    incidente = models.ForeignKey(Incidente, on_delete=models.CASCADE, related_name='alertas')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    mensagem = models.TextField()
    enviado = models.BooleanField(default=False)
    data_envio = models.DateTimeField(null=True, blank=True)
    lido = models.BooleanField(default=False)
    data_leitura = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']

    def __str__(self):
        return f"Alerta {self.canal} - {self.destinatario.username}"
