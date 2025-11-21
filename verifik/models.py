"""
╔══════════════════════════════════════════════════════════════════╗
║                      MODELS - VERIFIK APP                        ║
║         Sistema de IA para Detecção de Produtos por Câmeras     ║
╚══════════════════════════════════════════════════════════════════╝

📚 O QUE É ESTE ARQUIVO:
------------------------
Define todos os modelos (estruturas de dados) do módulo VerifiK:

1. 👤 FUNCIONÁRIOS:
   - Funcionario: Operadores de caixa
   - PerfilGestor: Gestores que acessam o sistema

2. 📦 PRODUTOS:
   - ProdutoMae: Catálogo GLOBAL de produtos
   - CodigoBarrasProdutoMae: Múltiplos códigos de barras por produto
   - ImagemProduto: Fotos para treinar IA

3. 📷 CÂMERAS E DETECÇÕES:
   - Camera: Câmeras físicas instaladas
   - DeteccaoProduto: Quando IA detecta produto
   - OperacaoVenda: Vendas registradas no caixa

4. ⚠️ INCIDENTES:
   - Incidente: Divergências entre detecção e venda
   - StatusRespostaIncidente: Histórico de resoluções

🔧 CONCEITOS IMPORTANTES:
-------------------------
1. **ProdutoMae (Produto Global)**:
   - SEM FK para Organization
   - Compartilhado entre TODAS as empresas
   - Catálogo mestre único

2. **Multi-tenant**:
   - Funcionario, Camera, OperacaoVenda TÊM FK para Organization
   - Cada empresa vê apenas seus dados

3. **Relacionamentos**:
   - ForeignKey (N-para-1): Muitos funcionários para 1 organização
   - related_name: Nome da relação inversa
   - on_delete=CASCADE: Se organização deletada, deleta funcionários

4. **Índices (Performance)**:
   - Index em campos buscados frequentemente
   - Exemplo: codigo_barras (busca por código)

📖 DOCUMENTAÇÃO:
----------------
Django Models: https://docs.djangoproject.com/en/5.2/topics/db/models/
QuerySets: https://docs.djangoproject.com/en/5.2/ref/models/querysets/
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


# ============================================================
# 👤 SEÇÃO 1: FUNCIONÁRIOS E USUÁRIOS
# ============================================================

class Funcionario(models.Model):
    """
    Funcionário de uma organização (operador de caixa, vendedor, etc.)
    
    ╔══════════════════════════════════════════════════════════╗
    ║  RELACIONAMENTOS:                                        ║
    ║  - Pertence a 1 Organization (multi-tenant)              ║
    ║  - Pode ter 1 User associado (login no sistema)          ║
    ║                                                          ║
    ║  USO PRINCIPAL:                                          ║
    ║  - Rastrear quem fez vendas                             ║
    ║  - Associar incidentes a funcionários                    ║
    ║  - Controlar acesso ao sistema                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    Exemplo:
    --------
    Nome: Maria Silva
    CPF: 123.456.789-00
    Cargo: Operadora de Caixa
    Matricula: OP-001
    Organization: Posto Centro
    """
    
    # ──────────────────────────────────────────────────────────
    # 🔗 RELACIONAMENTOS (ForeignKeys)
    # ──────────────────────────────────────────────────────────
    
    organization = models.ForeignKey(
        'accounts.Organization',          # Modelo relacionado
        on_delete=models.CASCADE,         # Se org deletada, deleta funcionário
        related_name='verifik_funcionarios',  # org.verifik_funcionarios.all()
        null=True,
        blank=True,
        help_text='Organização à qual o funcionário pertence'
    )
    
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Aponta para User customizado
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Usuário do sistema (se tiver acesso ao painel)'
        # OneToOneField: 1 Funcionario = 1 User (máximo)
    )
    
    # ──────────────────────────────────────────────────────────
    # 📝 DADOS PESSOAIS
    # ──────────────────────────────────────────────────────────
    
    nome_completo = models.CharField(
        max_length=255,
        help_text='Nome completo do funcionário'
    )
    
    cpf = models.CharField(
        max_length=14,  # Formato: 000.000.000-00
        unique=True,    # CPF único no sistema todo
        help_text='CPF do funcionário'
    )
    
    # ──────────────────────────────────────────────────────────
    # 💼 DADOS PROFISSIONAIS
    # ──────────────────────────────────────────────────────────
    
    cargo = models.CharField(
        max_length=100,
        help_text='Cargo (ex: Operador de Caixa, Gerente)'
    )
    
    matricula = models.CharField(
        max_length=50,
        unique=True,
        help_text='Número de matrícula único'
    )
    
    ativo = models.BooleanField(
        default=True,
        help_text='Se False, funcionário foi desligado'
    )
    
    data_admissao = models.DateField(
        help_text='Data de contratação'
    )
    
    data_demissao = models.DateField(
        null=True,
        blank=True,
        help_text='Data de desligamento (se houver)'
    )
    
    foto = models.ImageField(
        upload_to='funcionarios/',
        null=True,
        blank=True,
        help_text='Foto do funcionário (opcional)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🗂️ METADATA
    # ──────────────────────────────────────────────────────────
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome_completo']  # Ordem alfabética

    def __str__(self):
        return f"{self.nome_completo} ({self.matricula})"


class PerfilGestor(models.Model):
    """
    Perfil de gestor/admin que acessa o painel VerifiK
    
    Diferença entre Funcionario e PerfilGestor:
    --------------------------------------------
    - Funcionario: Trabalha no posto (operador de caixa)
    - PerfilGestor: Acessa sistema web (supervisor, gerente)
    
    Níveis de acesso:
    -----------------
    - SUPERVISOR: Vê relatórios da sua loja
    - GERENTE: Vê relatórios de várias lojas
    - ADMINISTRADOR: Acesso total, configura sistema
    """
    
    NIVEL_CHOICES = [
        ('SUPERVISOR', 'Supervisor'),        # 👁️ Acesso limitado
        ('GERENTE', 'Gerente'),              # 👨‍💼 Acesso médio
        ('ADMINISTRADOR', 'Administrador'),  # 🔑 Acesso total
    ]
    
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text='User associado (1-para-1)'
    )
    
    nivel_acesso = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES,
        help_text='Nível de permissões no sistema'
    )
    
    telefone = models.CharField(
        max_length=20,
        help_text='Telefone para notificações'
    )
    
    receber_alertas_email = models.BooleanField(
        default=True,
        help_text='Enviar alertas por email'
    )
    
    receber_alertas_whatsapp = models.BooleanField(
        default=False,
        help_text='Enviar alertas por WhatsApp (futuro)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Gestor'
        verbose_name_plural = 'Perfis de Gestores'

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.nivel_acesso}"


# ============================================================
# 📦 SEÇÃO 2: PRODUTOS (CATÁLOGO GLOBAL)
# ============================================================

class ProdutoMae(models.Model):
    """
    Produto do catálogo MESTRE (compartilhado globalmente)
    
    ╔══════════════════════════════════════════════════════════╗
    ║  ⚠️ IMPORTANTE: SEM FK PARA ORGANIZATION!                ║
    ║                                                          ║
    ║  Por quê?                                                ║
    ║  - Catálogo global compartilhado entre todas empresas    ║
    ║  - Facilita treinamento da IA (imagens centralizadas)    ║
    ║  - Evita duplicação de produtos iguais                   ║
    ║                                                          ║
    ║  Exemplo:                                                ║
    ║  "Coca-Cola 350ml" é O MESMO produto em todos postos    ║
    ║  Mas cada posto pode ter códigos de barras diferentes    ║
    ╚══════════════════════════════════════════════════════════╝
    
    Relacionamentos:
    ----------------
    - ProdutoMae.codigos_barras → Lista de CodigoBarrasProdutoMae
    - ProdutoMae.imagens_treino → Lista de ImagemProduto
    
    Uso na IA:
    ----------
    1. Admin adiciona produto
    2. Admin adiciona 5-10 imagens do produto (vários ângulos)
    3. IA treina com essas imagens
    4. Câmeras detectam produto em tempo real
    """
    
    descricao_produto = models.CharField(
        max_length=255,
        help_text='Nome/descrição do produto (ex: Coca-Cola 350ml)'
    )
    
    marca = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Marca do produto (ex: Coca-Cola, Pepsi)'
    )
    
    tipo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Categoria (ex: Refrigerante, Chocolate, Cerveja)'
    )
    
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Preço de referência em reais (R$)'
        # Cada organização pode ter preço diferente
    )
    
    imagem_referencia = models.ImageField(
        upload_to='produtos_mae/',
        null=True,
        blank=True,
        help_text='Imagem principal do produto (thumb)'
    )
    
    ativo = models.BooleanField(
        default=True,
        help_text='Se False, produto descontinuado'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto Mãe'
        verbose_name_plural = 'Produtos Mãe'
        ordering = ['descricao_produto']

    def __str__(self):
        return f"{self.descricao_produto} - {self.marca or 'Sem marca'}"


class CodigoBarrasProdutoMae(models.Model):
    """
    Código de barras associado a um Produto Mãe
    
    ╔══════════════════════════════════════════════════════════╗
    ║  POR QUE MÚLTIPLOS CÓDIGOS?                              ║
    ║                                                          ║
    ║  Mesmo produto pode ter códigos diferentes:              ║
    ║  1. Embalagens diferentes (lata vs garrafa)              ║
    ║  2. Fornecedores diferentes                              ║
    ║  3. Promoções com código especial                        ║
    ║  4. Importação paralela                                  ║
    ║                                                          ║
    ║  REGRA: Código ÚNICO globalmente                         ║
    ║  Mesmo código não pode estar em 2 produtos diferentes    ║
    ╚══════════════════════════════════════════════════════════╝
    
    Exemplo:
    --------
    ProdutoMae: Coca-Cola 350ml
    Códigos:
    - 7894900011517 (lata) ← principal=True
    - 7894900532340 (garrafa)
    - 7894900530018 (pack 6un)
    """
    
    produto_mae = models.ForeignKey(
        ProdutoMae,
        on_delete=models.CASCADE,
        related_name='codigos_barras',
        help_text='Produto ao qual este código pertence'
        # produto.codigos_barras.all() retorna todos os códigos
    )
    
    codigo = models.CharField(
        max_length=50,
        unique=True,  # ⚠️ UNIQUE! Um código só pertence a UM produto
        db_index=True,  # Índice para busca rápida
        help_text='Código de barras (EAN-13, EAN-8, etc.)'
    )
    
    principal = models.BooleanField(
        default=False,
        help_text='Código principal do produto (mostrar primeiro)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Código de Barras (Produto Mãe)'
        verbose_name_plural = 'Códigos de Barras (Produto Mãe)'
        ordering = ['-principal', 'codigo']  # Principal primeiro
        
        # ──────────────────────────────────────────────────────
        # 🚀 ÍNDICES (PERFORMANCE)
        # ──────────────────────────────────────────────────────
        # Aceleram buscas no banco de dados
        indexes = [
            models.Index(fields=['codigo']),  # Busca por código
            models.Index(fields=['produto_mae', 'principal']),  # Busca principal de um produto
        ]
    
    def __str__(self):
        principal_str = " ⭐" if self.principal else ""
        return f"{self.codigo}{principal_str} → {self.produto_mae.descricao_produto}"


class ImagemProduto(models.Model):
    """Múltiplas imagens para treinamento da IA"""
    produto = models.ForeignKey(ProdutoMae, on_delete=models.CASCADE, related_name='imagens_treino')
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
    produto = models.ForeignKey(ProdutoMae, on_delete=models.SET_NULL, null=True)
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
    produto_identificado = models.ForeignKey(ProdutoMae, on_delete=models.SET_NULL, null=True, blank=True)
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
