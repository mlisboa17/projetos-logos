from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


# ==============================================
# 🧑 FUNCIONÁRIOS E USUÁRIOS
# ==============================================

class Funcionario(models.Model):
    """Operadores de caixa e outros funcionários"""
    # Integração com LOGOS
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, related_name='verifik_funcionarios', null=True, blank=True)
    
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
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
    
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    # Integração com LOGOS
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, related_name='verifik_produtos', null=True, blank=True)
    
    codigo_barras = models.CharField(max_length=50)
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
        unique_together = [['organization', 'codigo_barras']]  # Código único por empresa

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
    
    # Integração com LOGOS
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, related_name='verifik_vendas', null=True, blank=True)
    
    numero_venda = models.CharField(max_length=50)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True)
    data_hora = models.DateTimeField(default=timezone.now)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONCLUIDA')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Operação de Venda'
        verbose_name_plural = 'Operações de Vendas'
        ordering = ['-data_hora']
        unique_together = [['organization', 'numero_venda']]  # Número único por organização

    def __str__(self):
        return f"Venda #{self.numero_venda} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class ItemVenda(models.Model):
    """Itens de uma operação de venda"""
    operacao = models.ForeignKey(OperacaoVenda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item de Venda'
        verbose_name_plural = 'Itens de Venda'

    def __str__(self):
        return f"{self.produto.descricao_produto} x{self.quantidade}"


class DeteccaoProduto(models.Model):
    """Produtos detectados por vídeo ou OCR"""
    METODO_DETECCAO_CHOICES = [
        ('VIDEO', 'Vídeo/Visão Computacional'),
        ('OCR', 'OCR/Leitura de Texto'),
        ('MANUAL', 'Identificação Manual'),
    ]
    
    camera = models.ForeignKey('Camera', on_delete=models.SET_NULL, null=True)
    data_hora_deteccao = models.DateTimeField(default=timezone.now)
    metodo_deteccao = models.CharField(max_length=20, choices=METODO_DETECCAO_CHOICES)
    produto_identificado = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True)
    confianca = models.FloatField(help_text="Nível de confiança da IA (0-100%)")
    
    # Resultado da leitura
    marca_detectada = models.CharField(max_length=100, blank=True)
    tipo_detectado = models.CharField(max_length=100, blank=True)
    codigo_detectado = models.CharField(max_length=50, blank=True)
    
    # Evidências
    imagem_capturada = models.ImageField(upload_to='deteccoes/', null=True, blank=True)
    dados_raw = models.JSONField(null=True, blank=True, help_text="Dados brutos da IA")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Detecção de Produto'
        verbose_name_plural = 'Detecções de Produtos'
        ordering = ['-data_hora_deteccao']

    def __str__(self):
        produto = self.produto_identificado.descricao_produto if self.produto_identificado else "Não identificado"
        return f"{produto} - {self.data_hora_deteccao.strftime('%d/%m/%Y %H:%M')} ({self.confianca}%)"


# ==============================================
# 🚨 INCIDENTES E EVIDÊNCIAS
# ==============================================

class Incidente(models.Model):
    """Divergências entre entrega e registro"""
    TIPO_CHOICES = [
        ('PRODUTO_NAO_REGISTRADO', 'Produto Entregue Não Registrado'),
        ('QUANTIDADE_DIVERGENTE', 'Quantidade Divergente'),
        ('PRODUTO_DIFERENTE', 'Produto Diferente do Registrado'),
        ('OUTRO', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_INVESTIGACAO', 'Em Investigação'),
        ('CONFIRMADO', 'Confirmado'),
        ('FALSO_POSITIVO', 'Falso Positivo'),
        ('RESOLVIDO', 'Resolvido'),
    ]
    
    codigo_incidente = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    # Relações
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True)
    operacao_venda = models.ForeignKey(OperacaoVenda, on_delete=models.SET_NULL, null=True, blank=True)
    deteccao = models.ForeignKey(DeteccaoProduto, on_delete=models.SET_NULL, null=True)
    camera = models.ForeignKey('Camera', on_delete=models.SET_NULL, null=True)
    
    # Dados do incidente
    data_hora_ocorrencia = models.DateTimeField(default=timezone.now)
    descricao = models.TextField()
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Análise e decisão
    analisado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    data_analise = models.DateTimeField(null=True, blank=True)
    observacoes_analise = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Incidente'
        verbose_name_plural = 'Incidentes'
        ordering = ['-data_hora_ocorrencia']

    def __str__(self):
        return f"Incidente #{self.codigo_incidente} - {self.get_tipo_display()}"


class EvidenciaIncidente(models.Model):
    """Vídeo, imagem e dados que provam o incidente"""
    TIPO_EVIDENCIA_CHOICES = [
        ('VIDEO', 'Vídeo'),
        ('IMAGEM', 'Imagem'),
        ('AUDIO', 'Áudio'),
        ('DOCUMENTO', 'Documento'),
        ('LOG', 'Log do Sistema'),
    ]
    
    incidente = models.ForeignKey(Incidente, on_delete=models.CASCADE, related_name='evidencias')
    tipo = models.CharField(max_length=20, choices=TIPO_EVIDENCIA_CHOICES)
    arquivo = models.FileField(upload_to='evidencias/')
    descricao = models.TextField(blank=True)
    duracao_segundos = models.IntegerField(null=True, blank=True, help_text="Para vídeos/áudios")
    timestamp_relevante = models.CharField(max_length=20, blank=True, help_text="Momento relevante no vídeo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evidência de Incidente'
        verbose_name_plural = 'Evidências de Incidentes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} - Incidente #{self.incidente.codigo_incidente}"


# ==============================================
# 📢 ALERTAS
# ==============================================

class Alerta(models.Model):
    """Notificações enviadas ao gestor"""
    TIPO_CHOICES = [
        ('INCIDENTE', 'Incidente Detectado'),
        ('CAMERA_INATIVA', 'Câmera Inativa'),
        ('SISTEMA', 'Alerta do Sistema'),
        ('RELATORIO', 'Relatório Agendado'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]
    
    CANAL_CHOICES = [
        ('EMAIL', 'E-mail'),
        ('WHATSAPP', 'WhatsApp'),
        ('PAINEL', 'Painel Web'),
        ('SMS', 'SMS'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('ENVIADO', 'Enviado'),
        ('FALHOU', 'Falhou'),
        ('LIDO', 'Lido'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='MEDIA')
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    # Destinatário
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Conteúdo
    titulo = models.CharField(max_length=255)
    mensagem = models.TextField()
    incidente = models.ForeignKey(Incidente, on_delete=models.SET_NULL, null=True, blank=True)
    camera = models.ForeignKey('Camera', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Controle de envio
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_envio = models.DateTimeField(null=True, blank=True)
    data_leitura = models.DateTimeField(null=True, blank=True)
    tentativas_envio = models.IntegerField(default=0)
    erro_envio = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"


# ==============================================
# 📹 CÂMERAS E MONITORAMENTO
# ==============================================

class Camera(models.Model):
    """Informações das câmeras instaladas"""
    STATUS_CHOICES = [
        ('ATIVA', 'Ativa'),
        ('INATIVA', 'Inativa'),
        ('MANUTENCAO', 'Em Manutenção'),
        ('ERRO', 'Com Erro'),
    ]
    
    # Integração com LOGOS
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE, related_name='verifik_cameras', null=True, blank=True)
    
    nome = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=255, help_text="Ex: Caixa 1, Entrada, Setor A")
    ip_address = models.GenericIPAddressField()
    porta = models.IntegerField(default=554)
    usuario = models.CharField(max_length=100, blank=True)
    senha = models.CharField(max_length=100, blank=True)
    url_stream = models.CharField(max_length=500, help_text="URL completa do stream RTSP/HTTP")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVA')
    ativa = models.BooleanField(default=True)
    
    # Configurações
    resolucao = models.CharField(max_length=20, default="1920x1080")
    fps = models.IntegerField(default=30, help_text="Frames por segundo")
    gravar_continuamente = models.BooleanField(default=False)
    tempo_retencao_dias = models.IntegerField(default=30, help_text="Dias para manter gravações")
    
    # Monitoramento
    ultima_conexao = models.DateTimeField(null=True, blank=True)
    ultima_deteccao = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Câmera'
        verbose_name_plural = 'Câmeras'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.localizacao} ({self.status})"


class CameraStatus(models.Model):
    """Histórico de atividade/inatividade das câmeras"""
    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('ERRO_CONEXAO', 'Erro de Conexão'),
        ('ERRO_AUTENTICACAO', 'Erro de Autenticação'),
        ('BAIXA_QUALIDADE', 'Baixa Qualidade'),
    ]
    
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='historico_status')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    data_hora = models.DateTimeField(default=timezone.now)
    
    # Métricas
    qualidade_sinal = models.IntegerField(null=True, blank=True, help_text="0-100%")
    latencia_ms = models.IntegerField(null=True, blank=True, help_text="Latência em milissegundos")
    fps_atual = models.IntegerField(null=True, blank=True)
    
    # Informações de erro
    codigo_erro = models.CharField(max_length=50, blank=True)
    mensagem_erro = models.TextField(blank=True)
    
    # Duração do status
    duracao_minutos = models.IntegerField(null=True, blank=True, help_text="Quanto tempo ficou neste status")

    class Meta:
        verbose_name = 'Status de Câmera'
        verbose_name_plural = 'Histórico de Status das Câmeras'
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.camera.nome} - {self.get_status_display()} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
