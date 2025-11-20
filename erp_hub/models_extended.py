"""
Models estendidos para empresas do Grupo Lisboa
"""
from django.db import models
from django.core.validators import RegexValidator
from accounts.models import Organization


class TipoLogradouro(models.TextChoices):
    """Tipos de logradouro"""
    RUA = 'rua', 'Rua'
    AVENIDA = 'avenida', 'Avenida'
    PRACA = 'praca', 'Praça'
    RODOVIA = 'rodovia', 'Rodovia'
    ESTRADA = 'estrada', 'Estrada'
    TRAVESSA = 'travessa', 'Travessa'


class RegimeTributario(models.TextChoices):
    """Regime tributário"""
    SIMPLES = 'simples', 'Simples Nacional'
    REAL = 'real', 'Lucro Real'
    PRESUMIDO = 'presumido', 'Lucro Presumido'
    MEI = 'mei', 'MEI'


class Empresa(models.Model):
    """
    Modelo base para empresas do grupo
    Representa dados cadastrais completos (CNPJ, endereço, etc)
    """
    # Relacionamento
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='empresas',
        verbose_name='Organização'
    )
    
    # Identificação
    razao_social = models.CharField('Razão Social', max_length=200)
    nome_fantasia = models.CharField('Nome Fantasia', max_length=200)
    cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
                message='CNPJ inválido. Use formato: 00.000.000/0000-00'
            )
        ]
    )
    
    # Inscrições
    inscricao_municipal = models.CharField('Inscrição Municipal', max_length=50, blank=True)
    inscricao_estadual = models.CharField('Inscrição Estadual', max_length=50, blank=True)
    
    # Endereço
    cep = models.CharField(
        'CEP',
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{2}\.\d{3}-\d{3}$',
                message='CEP inválido. Use formato: 00.000-000'
            )
        ]
    )
    tipo_logradouro = models.CharField(
        'Tipo Logradouro',
        max_length=20,
        choices=TipoLogradouro.choices,
        default=TipoLogradouro.AVENIDA
    )
    logradouro = models.CharField('Logradouro', max_length=200)
    numero = models.CharField('Número', max_length=10)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100)
    cidade = models.CharField('Cidade', max_length=100)
    estado = models.CharField('Estado', max_length=2)
    
    # Contato
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    celular = models.CharField('Celular', max_length=20, blank=True)
    fax = models.CharField('Fax', max_length=20, blank=True)
    email_contato = models.EmailField('E-mail de Contato', blank=True)
    
    # Gestão
    proprietario = models.CharField('Proprietário', max_length=200)
    gerente = models.CharField('Gerente', max_length=200, blank=True)
    nome_declarante = models.CharField('Nome do Declarante', max_length=200, blank=True)
    cpf_declarante = models.CharField('CPF do Declarante', max_length=14, blank=True)
    
    # Tributação
    regime_tributario = models.CharField(
        'Regime Tributário',
        max_length=20,
        choices=RegimeTributario.choices,
        default=RegimeTributario.REAL
    )
    
    # Códigos e identificadores externos
    codigo_receita = models.CharField('Código de Receita', max_length=20, blank=True)
    codigo_externo = models.CharField('Código Externo', max_length=50, blank=True)
    logomarca = models.ImageField('Logomarca', upload_to='empresas/logos/', null=True, blank=True)
    
    # Controle
    ativa = models.BooleanField('Ativa', default=True)
    data_abertura = models.DateField('Data de Abertura', null=True, blank=True)
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    
    # Observações
    observacoes = models.TextField('Observações', blank=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['razao_social']
        indexes = [
            models.Index(fields=['cnpj']),
            models.Index(fields=['organization', 'ativa']),
        ]
    
    def __str__(self):
        return f"{self.nome_fantasia} ({self.cnpj})"
    
    @property
    def endereco_completo(self):
        """Retorna endereço formatado"""
        partes = [
            f"{self.get_tipo_logradouro_display()} {self.logradouro}",
            f"nº {self.numero}",
        ]
        if self.complemento:
            partes.append(self.complemento)
        partes.extend([
            self.bairro,
            f"{self.cidade}/{self.estado}",
            f"CEP {self.cep}"
        ])
        return ", ".join(partes)


class Bandeira(models.TextChoices):
    """Bandeiras de combustível"""
    VIBRA = 'vibra', 'Vibra (BR/Petrobras)'
    SHELL = 'shell', 'Shell'
    IPIRANGA = 'ipiranga', 'Ipiranga'
    RAIZEN = 'raizen', 'Raízen (Shell)'
    ALE = 'ale', 'Ale'
    BRANCA = 'branca', 'Bandeira Branca'
    OUTRO = 'outro', 'Outro'


class TipoServico(models.TextChoices):
    """Tipos de serviço oferecidos no posto"""
    COMBUSTIVEL = 'combustivel', 'Combustível'
    CONVENIENCIA = 'conveniencia', 'Loja de Conveniência'
    TROCA_OLEO = 'troca_oleo', 'Troca de Óleo'
    LAVAGEM = 'lavagem', 'Lavagem'
    BORRACHARIA = 'borracharia', 'Borracharia'
    RESTAURANTE = 'restaurante', 'Restaurante'
    GNV = 'gnv', 'GNV'


class PostoCombustivel(Empresa):
    """
    Posto de combustível
    Herda todos os dados cadastrais de Empresa
    """
    # Identificação específica
    bandeira = models.CharField(
        'Bandeira',
        max_length=20,
        choices=Bandeira.choices,
        default=Bandeira.VIBRA
    )
    codigo_anp = models.CharField('Código ANP', max_length=50, blank=True)
    
    # Serviços
    servicos = models.JSONField(
        'Serviços Oferecidos',
        default=list,
        help_text='Lista de serviços oferecidos no posto'
    )
    tem_conveniencia = models.BooleanField('Tem Loja de Conveniência', default=False)
    
    # Estrutura
    numero_bombas = models.IntegerField('Número de Bombas', default=0)
    numero_tanques = models.IntegerField('Número de Tanques', default=0)
    numero_pistas = models.IntegerField('Número de Pistas', default=1)
    
    # Capacidade dos tanques (em litros)
    capacidade_gasolina_comum = models.DecimalField(
        'Capacidade Gasolina Comum (L)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    capacidade_gasolina_aditivada = models.DecimalField(
        'Capacidade Gasolina Aditivada (L)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    capacidade_diesel_s10 = models.DecimalField(
        'Capacidade Diesel S10 (L)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    capacidade_diesel_comum = models.DecimalField(
        'Capacidade Diesel Comum (L)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    capacidade_etanol = models.DecimalField(
        'Capacidade Etanol (L)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Horário de funcionamento
    horario_abertura = models.TimeField('Horário de Abertura', null=True, blank=True)
    horario_fechamento = models.TimeField('Horário de Fechamento', null=True, blank=True)
    funciona_24h = models.BooleanField('Funciona 24h', default=False)
    
    # Integrações
    usa_webpostos = models.BooleanField('Usa WebPostos', default=False)
    codigo_webpostos = models.CharField('Código WebPostos', max_length=50, blank=True)
    
    class Meta:
        verbose_name = 'Posto de Combustível'
        verbose_name_plural = 'Postos de Combustível'
        ordering = ['nome_fantasia']
    
    def __str__(self):
        return f"{self.nome_fantasia} - {self.get_bandeira_display()}"
    
    @property
    def capacidade_total(self):
        """Capacidade total de armazenamento em litros"""
        return (
            self.capacidade_gasolina_comum +
            self.capacidade_gasolina_aditivada +
            self.capacidade_diesel_s10 +
            self.capacidade_diesel_comum +
            self.capacidade_etanol
        )


class TipoRestaurante(models.TextChoices):
    """Tipos de restaurante"""
    FAST_FOOD = 'fast_food', 'Fast Food'
    RESTAURANTE = 'restaurante', 'Restaurante'
    LANCHONETE = 'lanchonete', 'Lanchonete'
    CAFETERIA = 'cafeteria', 'Cafeteria'
    FRANQUIA = 'franquia', 'Franquia'


class Restaurante(Empresa):
    """
    Restaurante/Lanchonete
    Herda todos os dados cadastrais de Empresa
    """
    tipo = models.CharField(
        'Tipo',
        max_length=20,
        choices=TipoRestaurante.choices,
        default=TipoRestaurante.FAST_FOOD
    )
    
    # Franquia
    e_franquia = models.BooleanField('É Franquia', default=False)
    nome_franquia = models.CharField('Nome da Franquia', max_length=100, blank=True)
    codigo_franquia = models.CharField('Código Franquia', max_length=50, blank=True)
    
    # Capacidade
    numero_mesas = models.IntegerField('Número de Mesas', default=0)
    capacidade_pessoas = models.IntegerField('Capacidade (pessoas)', default=0)
    
    # Delivery
    aceita_delivery = models.BooleanField('Aceita Delivery', default=True)
    tem_ifood = models.BooleanField('Tem iFood', default=False)
    tem_uber_eats = models.BooleanField('Tem Uber Eats', default=False)
    tem_rappi = models.BooleanField('Tem Rappi', default=False)
    
    # Horário
    horario_abertura = models.TimeField('Horário de Abertura', null=True, blank=True)
    horario_fechamento = models.TimeField('Horário de Fechamento', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Restaurante'
        verbose_name_plural = 'Restaurantes'
        ordering = ['nome_fantasia']
    
    def __str__(self):
        return f"{self.nome_fantasia} - {self.get_tipo_display()}"


class SistemaEnergiaSolar(Empresa):
    """
    Sistema de Energia Solar
    Herda todos os dados cadastrais de Empresa
    """
    # Especificações técnicas
    potencia_instalada_kwp = models.DecimalField(
        'Potência Instalada (kWp)',
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Potência total instalada em kilowatt-pico'
    )
    numero_paineis = models.IntegerField('Número de Painéis', default=0)
    marca_paineis = models.CharField('Marca dos Painéis', max_length=100, blank=True)
    marca_inversor = models.CharField('Marca do Inversor', max_length=100, blank=True)
    
    # Geração
    geracao_media_mensal_kwh = models.DecimalField(
        'Geração Média Mensal (kWh)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    economia_media_mensal = models.DecimalField(
        'Economia Média Mensal (R$)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Datas
    data_instalacao = models.DateField('Data de Instalação', null=True, blank=True)
    data_ativacao = models.DateField('Data de Ativação', null=True, blank=True)
    
    # Sistema de monitoramento
    tem_sistema_monitoramento = models.BooleanField('Tem Sistema de Monitoramento', default=False)
    url_monitoramento = models.URLField('URL do Sistema de Monitoramento', blank=True)
    api_monitoramento = models.CharField('API de Monitoramento', max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Sistema de Energia Solar'
        verbose_name_plural = 'Sistemas de Energia Solar'
        ordering = ['nome_fantasia']
    
    def __str__(self):
        return f"{self.nome_fantasia} - {self.potencia_instalada_kwp} kWp"


class LojaConveniencia(Empresa):
    """
    Loja de Conveniência
    Pode ser independente ou dentro de um posto
    """
    # Relacionamento com posto
    posto = models.ForeignKey(
        PostoCombustivel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lojas_conveniencia',
        verbose_name='Posto',
        help_text='Posto onde a conveniência está localizada (se aplicável)'
    )
    
    # Características
    area_m2 = models.DecimalField('Área (m²)', max_digits=8, decimal_places=2, default=0)
    numero_checkouts = models.IntegerField('Número de Checkouts', default=1)
    tem_padaria = models.BooleanField('Tem Padaria', default=False)
    tem_cafe = models.BooleanField('Tem Café', default=False)
    tem_freezer = models.BooleanField('Tem Área de Freezer', default=True)
    
    # Serviços
    aceita_vale_refeicao = models.BooleanField('Aceita Vale Refeição', default=False)
    aceita_cartao_combustivel = models.BooleanField('Aceita Cartão de Combustível', default=False)
    
    # Categorias de produtos
    vende_bebidas = models.BooleanField('Vende Bebidas', default=True)
    vende_alimentos = models.BooleanField('Vende Alimentos', default=True)
    vende_higiene = models.BooleanField('Vende Higiene', default=True)
    vende_automotivos = models.BooleanField('Vende Produtos Automotivos', default=True)
    
    # Horário
    horario_abertura = models.TimeField('Horário de Abertura', null=True, blank=True)
    horario_fechamento = models.TimeField('Horário de Fechamento', null=True, blank=True)
    funciona_24h = models.BooleanField('Funciona 24h', default=False)
    
    # Integrações
    usa_sistema_pdv = models.BooleanField('Usa Sistema PDV', default=False)
    nome_sistema_pdv = models.CharField('Nome do Sistema PDV', max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'Loja de Conveniência'
        verbose_name_plural = 'Lojas de Conveniência'
        ordering = ['nome_fantasia']
    
    def __str__(self):
        if self.posto:
            return f"{self.nome_fantasia} - {self.posto.nome_fantasia}"
        return self.nome_fantasia


class TipoLubrificante(models.TextChoices):
    """Tipos de lubrificante"""
    OLEO_MOTOR = 'oleo_motor', 'Óleo de Motor'
    OLEO_CAMBIO = 'oleo_cambio', 'Óleo de Câmbio'
    OLEO_HIDRAULICO = 'oleo_hidraulico', 'Óleo Hidráulico'
    FLUIDO_FREIO = 'fluido_freio', 'Fluido de Freio'
    ADITIVO = 'aditivo', 'Aditivo'
    GRAXAS = 'graxas', 'Graxas'
    ARLA32 = 'arla32', 'Arla 32'
    OUTRO = 'outro', 'Outro'


class CentroLubrificacao(Empresa):
    """
    Centro de Lubrificação/Troca de Óleo
    Pode ser independente ou dentro de um posto
    """
    # Relacionamento com posto
    posto = models.ForeignKey(
        PostoCombustivel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='centros_lubrificacao',
        verbose_name='Posto',
        help_text='Posto onde o centro está localizado (se aplicável)'
    )
    
    # Estrutura
    numero_boxes = models.IntegerField('Número de Boxes', default=1)
    tem_elevador = models.BooleanField('Tem Elevador', default=False)
    tem_rampa = models.BooleanField('Tem Rampa', default=False)
    
    # Serviços oferecidos
    faz_troca_oleo = models.BooleanField('Faz Troca de Óleo', default=True)
    faz_troca_filtros = models.BooleanField('Faz Troca de Filtros', default=True)
    faz_alinhamento = models.BooleanField('Faz Alinhamento', default=False)
    faz_balanceamento = models.BooleanField('Faz Balanceamento', default=False)
    faz_lavagem_motor = models.BooleanField('Faz Lavagem de Motor', default=False)
    
    # Tipos de veículos atendidos
    atende_passeio = models.BooleanField('Atende Veículos de Passeio', default=True)
    atende_moto = models.BooleanField('Atende Motos', default=False)
    atende_caminhao = models.BooleanField('Atende Caminhões', default=False)
    atende_onibus = models.BooleanField('Atende Ônibus', default=False)
    
    # Marcas de lubrificantes trabalhadas
    marcas_lubrificantes = models.JSONField(
        'Marcas de Lubrificantes',
        default=list,
        help_text='Lista de marcas de lubrificantes comercializadas'
    )
    
    # Horário
    horario_abertura = models.TimeField('Horário de Abertura', null=True, blank=True)
    horario_fechamento = models.TimeField('Horário de Fechamento', null=True, blank=True)
    
    # Capacidade
    atendimentos_dia = models.IntegerField('Atendimentos por Dia (média)', default=0)
    tempo_medio_atendimento = models.IntegerField('Tempo Médio de Atendimento (min)', default=30)
    
    class Meta:
        verbose_name = 'Centro de Lubrificação'
        verbose_name_plural = 'Centros de Lubrificação'
        ordering = ['nome_fantasia']
    
    def __str__(self):
        if self.posto:
            return f"{self.nome_fantasia} - {self.posto.nome_fantasia}"
        return self.nome_fantasia
